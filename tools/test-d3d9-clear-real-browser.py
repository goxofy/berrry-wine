#!/usr/bin/env python3
"""Single bounded installed-Chrome tree. No install, sandbox bypass or retries.

Usage: python3 tools/test-d3d9-clear-real-browser.py OUTPUT ACCOUNTING_JSON
Accounting names the task allocation, external session/event paths, and initial
SQLite sizes. Admission denial is exit 2, never a passing skip. OUTPUT is fresh.
"""
import ctypes
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time

MIB = 1048576


def processes():
    table = {}
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                f = (p / 'stat').read_text().rsplit(')', 1)[1].split()
                table[int(p.name)] = (int(f[1]), int(f[11]) + int(f[12]))
            except (FileNotFoundError, ProcessLookupError):
                pass
    return table


def descendants(table):
    owned = {os.getpid()}
    while True:
        new = {pid for pid, (ppid, _) in table.items() if ppid in owned}
        if new <= owned:
            return owned - {os.getpid()}
        owned |= new


def usage(config):
    paths = set()
    for name in [config['allocation'], *config['external']]:
        p = Path(name)
        if p.exists():
            paths.add(p)
            if p.is_dir():
                paths.update(p.rglob('*'))
    total = largest = 0
    for p in paths:
        try:
            s = p.lstat()
            # Chromium creates SingletonLock/Socket symlinks. Charge their
            # own inode bytes without traversing them or charging targets.
            total += max(s.st_size, s.st_blocks * 512)
            if stat.S_ISREG(s.st_mode):
                largest = max(largest, s.st_size)
        except FileNotFoundError:
            pass  # Chrome may remove its own transient files.
    baseline = json.loads(Path(config['sqliteBaseline']).read_text())
    growth = 0
    for p in Path(config['sqliteDirectory']).glob('*sqlite*'):
        try:
            if p.is_file():
                growth += max(0, p.stat().st_size - baseline.get(str(p), 0))
        except FileNotFoundError:
            pass
    return total + growth, largest, growth


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (24 * MIB, 24 * MIB))


def main():
    output = Path(sys.argv[1]).resolve()
    config = json.loads(Path(sys.argv[2]).read_text())
    assert output.parent == Path(config['allocation']).resolve()
    assert len(os.fsencode(str(output))) <= 58, 'Chrome Unix socket path bound'
    assert not output.exists(), 'Fresh OUTPUT required; retain all prior receipts'
    output.mkdir()
    receipt = {'wallLimit': 60, 'aggregateCpuLimit': 60, 'reserve': 8 * MIB,
               'future': config['future'], 'sandboxDisabled': False,
               'startedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    proc = None
    try:
        memory = int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines()
                          if s.startswith('MemAvailable:'))) * 1024
        used, largest, growth = usage(config)
        free = shutil.disk_usage(output).free
        projection = used + 12 * MIB + config['future'] + 8 * MIB
        receipt.update(memoryBefore=memory, ownedBefore=used, sqliteGrowthBefore=growth,
                       freeBefore=free, projectedTotal=projection)
        assert memory >= 2684354560, f'MemAvailable {memory} < 2684354560; no browser launched'
        assert projection <= 64 * MIB, f'Task projection {projection} > 64 MiB'
        assert free - (projection - used) >= 2982150144, 'Host free floor'
        assert largest <= 24 * MIB, 'Per-file limit'
        assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0, 'Subreaper required'
        receipt['admission'] = 'pass'
        command = ['node', '--max-old-space-size=256',
                   str(Path(__file__).with_name('d3d9-clear-real-cdp.js')), str(output)]
        receipt['command'] = command
        start = time.monotonic()
        seen, cpu_seen, security = set(), {}, {}
        peak = used
        with (output / 'harness.log').open('wb') as log:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                    preexec_fn=limits, start_new_session=True)
            try:
                while proc.poll() is None:
                    table = processes()
                    owned = descendants(table)
                    seen |= owned
                    for pid in owned:
                        cpu_seen[pid] = max(cpu_seen.get(pid, 0), table[pid][1])
                        try:
                            args = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
                            assert b'--no-sandbox' not in args
                            if b'--type=renderer' in args:
                                status = dict(s.split(':', 1) for s in Path(f'/proc/{pid}/status').read_text().splitlines() if ':' in s)
                                security[pid] = {k: status[k].strip() for k in ['NoNewPrivs', 'Seccomp']}
                        except (FileNotFoundError, ProcessLookupError):
                            pass
                    used, largest, growth = usage(config)
                    peak = max(peak, used)
                    cpu = sum(cpu_seen.values()) / os.sysconf('SC_CLK_TCK')
                    if time.monotonic() - start >= 60 or cpu >= 60:
                        raise RuntimeError('Browser tree wall/aggregate CPU limit')
                    if used + config['future'] + 8 * MIB > 64 * MIB or largest > 24 * MIB:
                        raise RuntimeError('Task allocation/per-file limit')
                    time.sleep(.2)
            finally:
                # Entire original process group, plus detached/adopted helpers.
                for sig, grace in [(signal.SIGTERM, 5), (signal.SIGKILL, 2)]:
                    end = time.monotonic() + grace
                    try:
                        os.killpg(proc.pid, sig)
                    except ProcessLookupError:
                        pass
                    while True:
                        owned = descendants(processes())
                        seen |= owned
                        for pid in owned:
                            try:
                                os.kill(pid, sig)
                            except ProcessLookupError:
                                pass
                        proc.poll()
                        for pid in owned - {proc.pid}:
                            try:
                                os.waitpid(pid, os.WNOHANG)
                            except ChildProcessError:
                                pass
                        if not descendants(processes()) or time.monotonic() >= end:
                            break
                        time.sleep(.05)
                    if not descendants(processes()):
                        break
                proc.wait(timeout=1)
                remaining = sorted(descendants(processes()))
                receipt.update(exit=proc.returncode, wallSeconds=round(time.monotonic()-start, 3),
                               peakOwnedBytes=peak, descendantsSeen=sorted(seen),
                               descendantsRemaining=remaining, rendererSecurity=security,
                               aggregateCpuSeconds=sum(cpu_seen.values()) / os.sysconf('SC_CLK_TCK'))
                assert not remaining, 'Unreaped browser descendants'
        return proc.returncode
    except Exception as e:
        receipt.update(failure=str(e), admission=receipt.get('admission', 'denied'),
                       browserLaunched=proc is not None)
        print(json.dumps(receipt))
        return 2
    finally:
        receipt['finalOwnedBytes'], receipt['largestFile'], receipt['sqliteGrowthFinal'] = usage(config)
        (output / 'cleanup-resource.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    sys.exit(main())
