// SPDX-License-Identifier: GPL-3.0-only
// Capture Electron's early stderr without hiding inspector output from Playwright.
'use strict';
const fs = require('node:fs');
const path = require('node:path');

function quoteShell(value) {
  if (typeof value !== 'string' || !value.length || value.includes('\0'))
    throw new Error('Invalid executable or temporary path');
  return "'" + value.replace(/'/g, "'\\''") + "'";
}

function createStderrWrapper(executable, directory) {
  // Linux-only wrapper: tee preserves stderr for Playwright's inspector handshake.
  const logPath = path.join(directory, 'electron-stderr.log');
  const executablePath = path.join(directory, 'electron-wrapper.sh');
  fs.writeFileSync(executablePath,
    '#!/bin/bash\nset -e\nexec ' + quoteShell(executable) +
    ' "$@" 2> >(tee -a ' + quoteShell(logPath) + ' >&2)\n', {mode: 0o700});
  fs.chmodSync(executablePath, 0o700);
  return {executablePath, logPath};
}

function parseBootHello(text) {
  const match = /boot-to-first-hello-ms=([0-9]+(?:\.[0-9]+)?)/.exec(text);
  return match ? Number(match[1]) : null;
}

module.exports = {quoteShell, createStderrWrapper, parseBootHello};
