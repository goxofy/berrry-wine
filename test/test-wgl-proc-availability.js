#!/usr/bin/env node
'use strict';
const assert = require('assert');
const { bootRenderHarness } = require('./render-helper');

async function main() {
  const extraWat = `
    (func (export "lookup_regs") (result i32) (global.get $reg_base))
    (func (export "lookup_thunks") (result i32) (i32.atomic.load (global.get $THUNK_NEXT_SHARED)))
    (func (export "lookup_error") (result i32) (global.get $last_error))
    (func (export "lookup_library") (param $name i32) (result i32)
      (local $esp i32)
      (local.set $esp (i32.load offset=16 (global.get $reg_base)))
      (call $handle_LoadLibraryA (local.get $name) (i32.const 0) (i32.const 0) (i32.const 0) (i32.const 0) (i32.const 0))
      (i32.store offset=16 (global.get $reg_base) (local.get $esp))
      (i32.load (global.get $reg_base)))
    (func (export "lookup_static_gl_test") (param $module i32) (param $name i32) (result i32)
      (global.set $last_error (i32.const 0))
      (call $handle_GetProcAddress (local.get $module) (local.get $name)
        (i32.const 0) (i32.const 0) (i32.const 0) (i32.const 0))
      (i32.load (global.get $reg_base)))
    (func (export "lookup_gl_test") (param $name i32) (result i32)
      (local $esp i32) (local $answer i32)
      (local.set $esp (i32.load offset=16 (global.get $reg_base)))
      (call $handle_gpu_api (i32.const 50) (i32.const 1)
        (local.get $name) (i32.const 0) (i32.const 0)
        (i32.const 0) (i32.const 0) (i32.const 0))
      (local.set $answer (i32.load (global.get $reg_base)))
      (if (i32.ne (i32.load offset=16 (global.get $reg_base))
          (i32.add (local.get $esp) (i32.const 8))) (then (unreachable)))
      (i32.store offset=16 (global.get $reg_base) (local.get $esp))
      (local.get $answer))`;
  const mutation = process.env.GL_LOOKUP_MUTATION;
  let prebuiltModule = null;
  if (mutation) {
    const { compileSrcWasm } = require('./compile-src');
    let changed = false;
    const bytes = compileSrcWasm((file, source) => {
      if (file === '13-exports.wat') return source + extraWat;
      if (file !== '09a0-handlers-base.wat') return source;
      const from = mutation === 'cleanup'
        ? '(global.set $last_error (i32.const 127)) ;; ERROR_PROC_NOT_FOUND\n        (br $gpa)'
        : '(call $gl_dynamic_api_unsupported (local.get $i))';
      const to = mutation === 'cleanup'
        ? '(global.set $last_error (i32.const 127)) ;; ERROR_PROC_NOT_FOUND\n        (return)'
        : mutation === 'all' ? '(i32.const 1)' : '(i32.const 0)';
      assert(source.includes(from), 'mutation anchor'); changed = true;
      return source.replace(from, to);
    });
    assert(changed); prebuiltModule = new WebAssembly.Module(bytes);
  }
  const { exports: e, memory } = await bootRenderHarness(prebuiltModule ? { prebuiltModule } : { extraWat });
  const toWasm = p => p - e.get_image_base() + e.get_guest_base();
  const table = require('../src/api_table.json');
  function string(name) {
    const bytes = Buffer.from(name + '\0');
    const p = e.guest_alloc(bytes.length);
    new Uint8Array(memory.buffer, toWasm(p), bytes.length).set(bytes);
    return p;
  }
  const lookup = name => e.lookup_gl_test(string(name)) >>> 0;
  for (const name of ['wglSwapIntervalEXT', 'glTexParameteriv',
    'glLockArraysEXT', 'glUnlockArraysEXT',
    'GetTickCount', 'gluPerspective', 'glNotARealFunction', 'glactivetextureARB']) {
    assert.strictEqual(lookup(name), 0, `${name} must not be advertised`);
  }
  for (const name of ['glActiveTextureARB', 'glClientActiveTextureARB',
    'glMultiTexCoord2fARB', 'glTexParameterfv', 'glGetTexParameterfv',
    'glTexCoord2d', 'glTexCoord2dv',
    'glColor3dv', 'glColor4dv', 'glRectf', 'glMultMatrixd',
    'wglSwapLayerBuffers', 'wglGetCurrentContext', 'wglGetCurrentDC']) {
    const thunk = lookup(name);
    assert.notStrictEqual(thunk, 0, `${name} remains available`);
    assert.strictEqual(new DataView(memory.buffer).getUint32(toWasm(thunk) + 4, true),
      table.findIndex(api => api.name === name), `${name} dispatches to its real API`);
  }
  assert.strictEqual(e.lookup_gl_test(0), 0);
  const module = e.lookup_library(string('opengl32.dll')) >>> 0;
  assert.strictEqual(module,e.get_image_base() >>> 0,'legacy OpenGL library alias (zero-base harness)');
  const v = new DataView(memory.buffer), regs = e.lookup_regs(), stack = e.guest_alloc(128);
  function staticLookup(name) {
    const p = string(name);
    for (let i=0;i<8;i++) v.setUint32(regs+i*4, 0x55660000+i, true);
    v.setUint32(regs+16, stack, true);
    new Uint8Array(memory.buffer,toWasm(stack),128).fill(0xa5);
    const result = e.lookup_static_gl_test(module,p) >>> 0;
    assert.strictEqual(v.getUint32(regs+16,true),stack+12,'GetProcAddress stdcall ABI');
    for (let i=1;i<8;i++) if(i!==4) assert.strictEqual(v.getUint32(regs+i*4,true),0x55660000+i,'GPR preserved');
    assert(new Uint8Array(memory.buffer,toWasm(stack),128).every(x=>x===0xa5),'guest stack preserved');
    return result;
  }
  for (const name of ['glLockArraysEXT','glUnlockArraysEXT','glTexParameteriv','wglSwapIntervalEXT']) {
    const before=e.lookup_thunks();
    assert.strictEqual(staticLookup(name),0,`${name}: SDL fallback must also reject unsupported GL`);
    assert.strictEqual(e.lookup_error(),127,'ERROR_PROC_NOT_FOUND');
    assert.strictEqual(e.lookup_thunks(),before,'rejection allocates no thunk');
  }
  for (const name of ['glDrawElements','glDrawArrays','glMultMatrixd','wglGetProcAddress']) {
    const thunk=staticLookup(name);
    assert(thunk,`${name} remains available through SDL fallback`);
    assert.strictEqual(v.getUint32(toWasm(thunk)+4,true),table.findIndex(a=>a.name===name));
  }
  assert(staticLookup('GetTickCount'),'non-GL compatibility lookup preserved');
  assert.strictEqual(staticLookup('glNotARealFunction'),0);
  if (!mutation) {
    const { spawnSync } = require('child_process');
    for (const variant of ['missing','all','cleanup']) {
      const r=spawnSync(process.execPath,[__filename],{env:{...process.env,GL_LOOKUP_MUTATION:variant},encoding:'utf8',timeout:120000});
      assert.strictEqual(r.status,1,`${variant} must fail acceptance: ${r.stderr}`);
      assert(/AssertionError/.test(r.stderr),`${variant} must fail an assertion: ${r.stderr}`);
      console.log(`Rejected broken ${variant} lookup variant`);
    }
  }
  console.log('WGL procedure availability and thunk identities pass');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
