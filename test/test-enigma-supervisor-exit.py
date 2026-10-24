"""Offline subprocess regression on the actual transformed supervisor tail.

Executes the unchanged historical stop() against fake OS child/group interfaces;
never launches its guest/watchdog recipes. All receipt and shell-AND I/O is real.
"""
import gzip
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

repo = pathlib.Path(__file__).resolve().parents[1]
evidence = repo / 'docs/re-notes/enigma-supervisor-exit-repair-20261024'
adapter = repo / 'tools/enigma-terminal-capture-guard.cjs'
original = gzip.decompress((evidence / 'original-supervise.py.gz').read_bytes()).decode()
assert hashlib.sha256(original.encode()).hexdigest() == '73be15954cedc19340779ff6bda2397cb94927ca702d2baebdccd5e763cf7b73'
receipt = dict(version=1, terminal=True, reason='capture-byte-limit', artifactAccepted=False,
               runnerSHA256='4d7b9587676db38fcf3314807acb2b2a42b5f09d2c98fcf3dccb8a6cde9e1809',
               captureSHA256='6d64a146f2daf8b598dbf13e3c13f890dbc783d8f5286aacba6d343758d22079',
               name='AssertionError', code='ERR_ASSERTION', message='capture byte limit')

def body(source):
    start = source.index(' while p.poll() is None:\n', source.index("why='natural'"))
    # No reconstruction of the finalization: include the actual try/finally EOF.
    return 'try:\n' + source[start:]

results = []
with tempfile.TemporaryDirectory(prefix='enigma-supervisor-exit-') as tmp:
    root = pathlib.Path(tmp)
    sourcefile = root / 'original.py'
    sourcefile.write_text(original)
    transformed = subprocess.run(['node', '--max-old-space-size=256', '-e',
        'process.stdout.write(require(process.argv[1]).transformSupervisor(require("fs").readFileSync(process.argv[2],"utf8")))',
        str(adapter), str(sourcefile)], capture_output=True, timeout=10, check=True).stdout.decode()
    helper = transformed[transformed.index('def terminal_capture():'):transformed.index('H=pathlib.Path')]
    original_stop = original[original.index('def stop(p):'):original.index('def limits():')]
    assert original_stop in transformed, 'all watchdog cleanup source must remain byte-exact'
    exit_guard = 'if capture_terminal is not None:raise SystemExit(1)\n'
    assert transformed.count(exit_guard) == 1
    reverted = transformed.replace(exit_guard, '')
    # The meaningful mutant is the exact previously rejected transformation.
    old_adapter = root / 'old.cjs'
    old_adapter.write_bytes(gzip.decompress((repo / 'docs/re-notes/enigma-runner-repairs-independent-20261024/candidate-terminal.cjs.gz').read_bytes()))
    old = subprocess.run(['node', '--max-old-space-size=256', '-e',
        'process.stdout.write(require(process.argv[1]).transformSupervisor(require("fs").readFileSync(process.argv[2],"utf8")))',
        str(old_adapter), str(sourcefile)], capture_output=True, timeout=10, check=True).stdout.decode()
    assert reverted == old

    def run(name, source, raw, poll='running', failure='', configured=True, output=b''):
        case = root / name
        case.mkdir()
        (case / 'output.log').write_bytes(output)
        if raw is not None:
            (case / 'raw.json').write_text(raw)
        env = dict(os.environ)
        env.pop('ENIGMA_TERMINAL_RECEIPT', None)
        if configured:
            env['ENIGMA_TERMINAL_RECEIPT'] = str(case / 'raw.json')
        script = case / 'supervisor.py'
        prelude = '''import os,json,pathlib,signal,types
E=pathlib.Path(CASE)
trace=[]
def save():
 (E/'trace.json').write_text(json.dumps(trace))
def killpg(pid,sig):
 trace.append(['killpg',pid,sig]);save();raise ProcessLookupError()
def waitpid(pid,flag):
 trace.append(['waitpid',pid,flag]);save();raise ChildProcessError()
os=types.SimpleNamespace(environ=os.environ,path=os.path,killpg=killpg,waitpid=waitpid,WNOHANG=os.WNOHANG)
class Child:
 pid=12345
 returncode=CHILDCODE
 def poll(self):
  if FAILURE=='poll' and not getattr(self,'polled',False):
   self.polled=True;raise RuntimeError('original poll failure')
  return None if POLL=='running' else self.returncode
 def wait(self):
  trace.append(['wait']);save()
  if FAILURE=='cleanup':raise RuntimeError('original cleanup failure')
class Clock:
 def monotonic(self):return 61
 def sleep(self,n):raise AssertionError('unexpected sleep')
class Log:
 def close(self):
  trace.append(['log.close']);save()
  if FAILURE=='publication':(E/'terminal.json').mkdir()
p=Child();time=Clock();start=0;why='natural';offset=0;tail=b'';log=Log()
'''.replace('CASE', repr(str(case))).replace('CHILDCODE', '1' if poll == 'failed' else '0').replace('POLL', repr(poll)).replace('FAILURE', repr(failure))
        # Actual stop() runs here using only fake OS interfaces above.
        script.write_text(prelude + helper + original_stop + body(source))
        dependent = case / 'dependent.py'
        dependent.write_text('import pathlib\npathlib.Path(' + repr(str(case / 'dependent')) + ').touch()\n')
        process = subprocess.run(['bash', '-c', '"$1" "$2" && "$1" "$3"',
            'probe', sys.executable, str(script), str(dependent)], env=env, capture_output=True, timeout=10)
        assert len(process.stdout) + len(process.stderr) < 8192
        recordfile = case / 'terminal.json'
        record = json.loads(recordfile.read_text()) if recordfile.is_file() else None
        trace = json.loads((case / 'trace.json').read_text())
        result = dict(name=name, exit=process.returncode, dependentRan=(case / 'dependent').exists(),
                      receipt=record, cleanupTrace=trace, stderr=process.stderr.decode())
        results.append(result)
        return result

    def denial(result):
        assert result['exit'] == 1 and not result['dependentRan']
        assert result['receipt']['reason'] == 'capture-byte-limit'
        assert result['receipt']['captureTerminal'] == receipt
        assert result['cleanupTrace'] == [['killpg',12345,15],['killpg',12345,0],
            ['killpg',12345,9],['wait'],['waitpid',-1,1],['killpg',12345,0],['log.close']]
        assert result['receipt']['remainingGroup'] is False

    for poll in ['running', 'success', 'failed']:
        denial(run('denial-' + poll, transformed, json.dumps(receipt), poll=poll))
    mutant = run('revert-exit-guard', reverted, json.dumps(receipt))
    try:
        denial(mutant)
    except AssertionError:
        assert mutant['exit'] == 0 and mutant['dependentRan']
    else:
        raise AssertionError('reverting mutation accepted')
    # Disabled/missing receipt and unrelated child outcomes retain historical
    # semantics, including its historical exit0 for an unrelated child exit1.
    for name, raw, configured, poll in [
        ('natural-success', None, True, 'success'),
        ('missing-receipt', None, True, 'running'),
        ('disabled-with-denial-file', json.dumps(receipt), False, 'success'),
        ('unrelated-child-failure', None, True, 'failed')]:
        result = run(name, transformed, raw, poll=poll, configured=configured)
        baseline = run(name + '-original', original, raw, poll=poll, configured=configured)
        assert result == dict(baseline, name=name), (result, baseline)
        assert result['exit'] == 0 and result['dependentRan']
    for failure in ['poll', 'cleanup', 'publication']:
        result = run('exception-' + failure, transformed, json.dumps(receipt), failure=failure)
        assert result['exit'] == 1 and not result['dependentRan']
        assert ('original ' + failure + ' failure' in result['stderr']) if failure != 'publication' else 'IsADirectoryError' in result['stderr']
        assert 'SystemExit' not in result['stderr']
        if failure == 'poll':
            assert result['receipt']['captureTerminal'] == receipt
            assert result['cleanupTrace'][-1] == ['log.close']
    # Malformed/oversized receipts remain rejecting failures through full EOF.
    for name, raw in [('malformed','{}'), ('oversized','x'*1025)]:
        result = run(name, transformed, raw)
        assert result['exit'] != 0 and not result['dependentRan']
        assert 'AssertionError' in result['stderr']
    print(json.dumps(dict(passTests=True, actualTransformedSource=True, originalStopUnchanged=True,
        revertingMutationRejected=True, historicalUnrelatedSemanticsPreserved=True, results=results), indent=2))
