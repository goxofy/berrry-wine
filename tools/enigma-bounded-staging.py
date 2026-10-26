#!/usr/bin/env python3
"""Stream pinned inputs into a NEW tree; share only immutable font copies.

No donor hard links, symlinks, full-file buffers, or persistent transfer payloads.
The destination and its parent must be coordinator-owned and not concurrently
modified. Published fonts are read-only; consumers must not chmod/write them.
"""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile

CHUNK = 8192


def font(target):
    return target.startswith(('runner/fonts/', 'runtime/fonts/'))


def validate(rows):
    seen = set()
    for row in rows:
        target = row['target']
        p = PurePosixPath(target)
        if (not target or target == '.' or p.is_absolute() or '..' in p.parts or
                str(p) != target or target in seen):
            raise ValueError('unsafe/duplicate target: ' + target)
        if type(row['bytes']) is not int or row['bytes'] < 0:
            raise ValueError('invalid size')
        if not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('invalid hash')
        seen.add(target)
    for target in seen:
        if any(str(p) in seen for p in PurePosixPath(target).parents if str(p) != '.'):
            raise ValueError('file/directory collision')


@contextlib.contextmanager
def source(row):
    """Read exact Git blobs or standing files without writing donor state."""
    if row['kind'] == 'git':
        revision = row['revision']
        if not re.fullmatch('[0-9a-f]{40}', revision):
            raise ValueError('full Git revision required')
        proc = subprocess.Popen(['git', '-C', row['donor'], 'show',
                                 revision + ':' + row['path']], stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
        try:
            yield proc.stdout
            if proc.wait() != 0:
                raise ValueError('missing Git input: ' + row['path'])
        finally:
            proc.stdout.close()
            if proc.poll() is None:
                proc.terminate()
            proc.wait()
    elif row['kind'] == 'file':
        with open(row['path'], 'rb') as stream:
            yield stream
    else:
        raise ValueError('unsupported input kind')


def consume(row, stream, output=None):
    digest = hashlib.sha256()
    size = 0
    while True:
        block = stream.read(CHUNK)
        if not block:
            break
        size += len(block)
        if size > row['bytes']:
            raise ValueError('input exceeds pinned size: ' + row['target'])
        digest.update(block)
        if output is not None:
            output.write(block)
    if size != row['bytes'] or digest.hexdigest() != row['sha256']:
        raise ValueError('input identity changed: ' + row['target'])


def inventory(root):
    """Logical paths versus allocated inodes, including all owned directories.

    Distinct filesystems/inodes are distinct charges. Hard links inside this
    owned tree count once physically; no standing donor bytes are hidden here.
    """
    seen = set()
    allocated = logical = path_allocated = 0
    files = 0
    for path in [root, *root.rglob('*')]:
        s = path.lstat()
        if stat.S_ISLNK(s.st_mode):
            raise ValueError('unexpected symlink')
        path_allocated += s.st_blocks * 512
        key = s.st_dev, s.st_ino
        if key not in seen:
            allocated += s.st_blocks * 512
            seen.add(key)
        if stat.S_ISREG(s.st_mode):
            files += 1
            logical += s.st_size
    return dict(logicalBytes=logical, physicalOwnedBytes=allocated,
                pathSummedAllocatedBytes=path_allocated, files=files,
                uniqueInodes=len(seen))


def stage(rows, destination, opener=source, share_fonts=True):
    """Fail atomically; cleanup only the fresh invocation-owned temporary tree.

    Reverify EVERY required donor, even a duplicate whose output will be linked.
    Failure or KeyboardInterrupt leaves destination absent and donors untouched.
    Existing destinations are rejected, never replaced or cleaned up.
    """
    validate(rows)
    destination = Path(destination)
    if os.path.lexists(destination):
        raise FileExistsError(destination)
    temp = Path(tempfile.mkdtemp(prefix='.enigma-stage-', dir=destination.parent))
    canonical = {}
    try:
        for row in rows:
            target = temp / row['target']
            target.parent.mkdir(parents=True, exist_ok=True)
            key = row['bytes'], row['sha256']
            shared = canonical.get(key) if share_fonts and font(row['target']) else None
            with opener(row) as stream:
                if shared is None:
                    with target.open('xb') as output:
                        consume(row, stream, output)
                else:
                    consume(row, stream)
            if shared is not None:
                os.link(shared, target)  # no fallback that silently exceeds budget
            elif font(row['target']):
                target.chmod(0o444)
                canonical[key] = target
        receipt = inventory(temp)
        # Parent is exclusively owned; do not run concurrent publishers here.
        if os.path.lexists(destination):
            raise FileExistsError(destination)
        temp.rename(destination)
        return receipt
    except BaseException:
        shutil.rmtree(temp)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('destination')
    args = parser.parse_args()
    print(json.dumps(stage(json.loads(Path(args.manifest).read_text()), args.destination)))


if __name__ == '__main__':
    main()
