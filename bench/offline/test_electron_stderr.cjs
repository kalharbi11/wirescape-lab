// SPDX-License-Identifier: GPL-3.0-only
// Early-stderr collection regression: synthetic Node executable; no app/device launch.
'use strict';
const assert = require('node:assert/strict');
const { mkdtempSync, readFileSync, rmSync } = require('node:fs');
const { spawnSync } = require('node:child_process');
const os = require('node:os');
const path = require('node:path');
const { quoteShell, createStderrWrapper, parseBootHello } = require('./electron_stderr.cjs');

assert.equal(parseBootHello('inspector\nboot-to-first-hello-ms=12.375\n'), 12.375);
assert.equal(parseBootHello('no hello received'), null);
assert.equal(parseBootHello('boot-to-first-hello-ms=0\n'), 0);
assert.equal(quoteShell("a'b"), "'a'\\''b'");
assert.throws(() => quoteShell('\0'));

if (process.platform === 'linux') {
  const directory=mkdtempSync(path.join(os.tmpdir(), 'wirescape-l4-stderr-test-'));
  try {
    const { executablePath, logPath }=createStderrWrapper(process.execPath,directory);
    const child=spawnSync(executablePath,[
      '-e', "process.stderr.write('Debugger listening on ws://example\\nboot-to-first-hello-ms=8.25\\n')"
    ],{encoding:'utf8',timeout:10000});
    assert.equal(child.status,0,child.stderr);
    assert.match(child.stderr,/Debugger listening on ws:\/\/example/);
    assert.match(child.stderr,/boot-to-first-hello-ms=8.25/);
    assert.equal(parseBootHello(readFileSync(logPath,'utf8')),8.25);
  } finally { rmSync(directory,{recursive:true,force:true}); }
}
console.log('Electron stderr capture regression passed');
