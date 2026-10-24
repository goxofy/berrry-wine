'use strict';
// Preload BEFORE enigma-quiet-filesystem.cjs, then the original capture.cjs.
// No guest, renderer, filesystem, or guard-limit changes. Disabled is inert.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const assert = require('node:assert/strict');
const pins = Object.freeze({
  runner: '4d7b9587676db38fcf3314807acb2b2a42b5f09d2c98fcf3dccb8a6cde9e1809',
  quietRunner: '343f7572511b0de8bf79f3a9415d68e4bc6577490cc3bf71f1e8c066623477fb',
  capture: '6d64a146f2daf8b598dbf13e3c13f890dbc783d8f5286aacba6d343758d22079',
  supervisor: '73be15954cedc19340779ff6bda2397cb94927ca702d2baebdccd5e763cf7b73',
});
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
const call = `require(${JSON.stringify(__filename)})`;
const anchors = Object.freeze({
  png: '        } catch (e) {\n          logs.push(`[input] png FAILED',
  batch: '    } catch (e) {\n      flushLogs();\n      console.log(`\\n*** CRASH at batch',
  capture: "  assert(result.length<=131072,'capture byte limit');",
  supervisorHelper: 'H=pathlib.Path(__file__).parent',
  supervisorLoop: " while p.poll() is None:\n  if time.monotonic()-start>60:",
  supervisorFinal: " log.close();(E/'terminal.json')",
});
function once(source, anchor, replacement) {
  assert.equal(source.split(anchor).length - 1, 1, 'terminal capture anchor missing/ambiguous');
  return source.replace(anchor, replacement);
}
function transformRunner(source) {
  assert([pins.runner, pins.quietRunner].includes(sha256(source)), 'terminal capture runner hash');
  source = once(source, anchors.png, anchors.png.replace('          logs.push', `          ${call}.rethrow();\n          logs.push`));
  return once(source, anchors.batch, anchors.batch.replace('      flushLogs();', `      ${call}.rethrow();\n      flushLogs();`));
}
function transformCapture(source) {
  assert.equal(sha256(source), pins.capture, 'terminal capture preload hash');
  return once(source, anchors.capture,
    `  try { ${anchors.capture.trim()} } catch (error) { ${call}.reject(error); }`);
}
function transformSupervisor(source) {
  assert.equal(sha256(source), pins.supervisor, 'terminal capture supervisor hash');
  const helper = `def terminal_capture():
 name=os.environ.get('ENIGMA_TERMINAL_RECEIPT')
 if not name or not os.path.exists(name):return None
 with open(name,'rb') as f:data=f.read(1025)
 assert len(data)<=1024,'terminal capture receipt size'
 record=json.loads(data)
 assert record.get('version')==1 and record.get('terminal') is True
 assert record.get('reason')=='capture-byte-limit' and record.get('artifactAccepted') is False
 assert record.get('runnerSHA256')=='${pins.runner}'
 assert record.get('captureSHA256')=='${pins.capture}'
 assert record.get('code')=='ERR_ASSERTION' and record.get('message')=='capture byte limit'
 return record
`;
  source = once(source, anchors.supervisorHelper, helper + anchors.supervisorHelper);
  source = once(source, anchors.supervisorLoop,
    " while p.poll() is None:\n  if terminal_capture() is not None:why='capture-byte-limit';break\n  if time.monotonic()-start>60:");
  // Also inspect after natural child exit: a fast rejection can beat the poll.
  return once(source, anchors.supervisorFinal,
    " capture_terminal=terminal_capture()\n if capture_terminal is not None:receipt.update(reason='capture-byte-limit',captureTerminal=capture_terminal)\n log.close();(E/'terminal.json')");
}
let terminal = null;
let receiptPath = null;
// Capture the receipt primitives before capture.cjs installs its PNG writer.
const io = Object.fromEntries(['openSync', 'writeSync', 'fsyncSync', 'closeSync', 'linkSync', 'unlinkSync'].map(k => [k, fs[k].bind(fs)]));
function reject(error) {
  if (!terminal) {
    terminal = error; // identity, not message/regex classification
    try {
      assert(receiptPath, 'terminal capture receipt is not configured');
      const record = JSON.stringify({ version: 1, terminal: true, reason: 'capture-byte-limit',
        runnerSHA256: pins.runner, captureSHA256: pins.capture,
        name: String(error.name).slice(0, 80), code: String(error.code).slice(0, 80),
        message: String(error.message).slice(0, 256), artifactAccepted: false }) + '\n';
      const pending = receiptPath + '.pending';
      const fd = io.openSync(pending, 'wx', 0o600);
      try {
        const bytes = Buffer.from(record);
        let offset = 0;
        while (offset < bytes.length) {
          const n = io.writeSync(fd, bytes, offset, bytes.length - offset);
          assert(n > 0, 'terminal receipt short write');
          offset += n;
        }
        io.fsyncSync(fd);
      } finally { io.closeSync(fd); }
      // Publish the complete, fsynced inode without replacing any prior receipt.
      io.linkSync(pending, receiptPath);
      io.unlinkSync(pending);
      const dir = io.openSync(path.dirname(receiptPath), 'r');
      try { io.fsyncSync(dir); } finally { io.closeSync(dir); }
    } catch (receiptError) {
      // A failed receipt is still fatal; never resume or replace the denial.
      Object.defineProperty(error, 'terminalReceiptError', { value: receiptError });
    }
  }
  throw terminal;
}
function rethrow() { if (terminal) throw terminal; }
function install(root, capture, receipt) {
  for (const value of [root, capture, receipt]) assert(value && path.isAbsolute(value), 'terminal capture absolute paths required');
  root = fs.realpathSync(root);
  capture = fs.realpathSync(capture);
  const runner = path.join(root, 'test/run.js');
  assert.equal(sha256(fs.readFileSync(runner)), pins.runner, 'terminal capture original runner hash');
  assert.equal(sha256(fs.readFileSync(capture)), pins.capture, 'terminal capture original preload hash');
  assert(!require.cache[runner] && !require.cache[capture], 'terminal capture must precede runner and capture loading');
  assert(!fs.existsSync(receipt), 'terminal capture receipt must be fresh');
  assert(!fs.existsSync(receipt + '.pending'), 'terminal capture pending receipt must be fresh');
  fs.realpathSync(path.dirname(receipt));
  receiptPath = receipt;
  const original = Module.prototype._compile;
  Module.prototype._compile = function(source, file) {
    if (file === runner) source = transformRunner(source);
    if (file === capture) source = transformCapture(source);
    return original.call(this, source, file);
  };
}
module.exports = { pins, sha256, anchors, once, transformRunner, transformCapture, transformSupervisor, reject, rethrow, install };
if (process.env.ENIGMA_TERMINAL_CAPTURE_INSTALL === '1') {
  install(process.env.ENIGMA_RUNNER_ROOT, process.env.ENIGMA_CAPTURE_PATH, process.env.ENIGMA_TERMINAL_RECEIPT);
}
