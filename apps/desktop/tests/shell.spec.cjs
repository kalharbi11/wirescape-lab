// SPDX-License-Identifier: GPL-3.0-only
const { test, expect } = require('../../studio/node_modules/@playwright/test');
const { _electron: electron } = require('../../studio/node_modules/playwright');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const electronExecutable = require('electron');
const appMain = path.resolve(__dirname, '../build/main.js');
const stub = path.resolve(__dirname, 'stub-engine.cjs');

test('explicit LAN consent is forwarded verbatim to a socket-free engine stub', async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-osc-consent-'));
  const recorded = path.join(directory, 'args.json');
  const app = await electron.launch({
    executablePath: electronExecutable,
    args: ['--no-sandbox', appMain, '--engine', stub, '--null-audio', '--confirm-lan'],
    env: { ...process.env, WIRESCAPE_TEST_STUB: '1', STUB_FLAGS_FILE: recorded }
  });
  try {
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    await expect.poll(() => fs.existsSync(recorded)).toBe(true);
    expect(JSON.parse(fs.readFileSync(recorded, 'utf8'))).toEqual(['--null-audio', '--confirm-lan']);
  } finally {
    await app.close();
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

async function launch(extraEnv = {}) {
  return electron.launch({
    executablePath: electronExecutable,
    args: ['--no-sandbox', appMain, '--engine', stub, '--null-audio'],
    env: { ...process.env, WIRESCAPE_TEST_STUB: '1', ...extraEnv }
  });
}
test('native window loads the real built UI with the isolated five-member bridge', async () => {
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    expect(await page.evaluate(() => Object.keys(window.wirescape).sort()))
      .toEqual(['onMessage', 'openPatch', 'platform', 'savePatch', 'send']);
    const flags = await app.evaluate(({ BrowserWindow }) => {
      const w = BrowserWindow.getAllWindows()[0];
      return [w.isMinimizable(), w.isClosable()];
    });
    expect(flags).toEqual([true, true]);
    expect(await page.evaluate(() => typeof require)).toBe('undefined');
    expect(await page.evaluate(() => typeof process)).toBe('undefined');
  } finally { await app.close(); }
});
test('NDJSON replies, unexpected crash notification and bounded automatic restart', async () => {
  const app = await launch({ STUB_CRASH_ON_PANIC: '1' });
  try {
    const page = await app.firstWindow();
    const messages = await page.evaluate(async () => {
      return new Promise((resolve, reject) => {
        const seen = [];
        const timer = setTimeout(() => reject(new Error('Missing restart sequence')), 15000);
        const off = window.wirescape.onMessage(msg => {
          seen.push(msg);
          const hellos = seen.filter(v => v.type === 'hello');
          if (hellos.length >= 1 && !seen.some(v => v.re === 'p1')) {
            window.wirescape.send({ v: 0, id: 'p1', type: 'listAudioDevices' });
          }
          if (seen.some(v => v.re === 'p1') && !seen.some(v => v.type === 'app.engineExited')) {
            window.wirescape.send({ v: 0, id: 'crash1', type: 'panic' });
          }
          if (hellos.length >= 2 && seen.some(v => v.type === 'app.engineExited')) {
            clearTimeout(timer); off(); resolve(seen);
          }
        });
      });
    });
    expect(messages.some(m => m.re === 'p1' && m.ok === true)).toBe(true);
    expect(messages.some(m => m.type === 'app.engineExited' && m.expected === false)).toBe(true);
    const hellos = messages.filter(m => m.type === 'hello');
    expect(hellos[0].session).not.toBe(hellos[1].session);
    expect(new Set(hellos.map(h => h.session)).size).toBe(hellos.length);
  } finally { await app.close(); }
});
// RS: the old stop-at-four assertion is intentionally replaced by the
// planner's opposite contract. Use real supervisor timers and a socket-free
// stub; the cap is observed twice, including a restart after reaching it.
test('RS retries indefinitely with 250ms doubling capped at 30s, non-modal banner and graph replay', async () => {
  test.setTimeout(150000);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-crash-loop-'));
  const countFile = path.join(dir, 'spawns');
  const loadsFile = path.join(dir, 'loads.jsonl');
  const app = await launch({ STUB_CRASH_COUNT_FILE: countFile, STUB_LOAD_LOG: loadsFile });
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ dialog }) => {
      globalThis.__failureDialogCount = 0;
      dialog.showMessageBox = async () => {
        globalThis.__failureDialogCount++;
        return new Promise(() => {});
      };
    });
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    await page.evaluate(() => {
      window.__restartDelays = [];
      window.__restartHellos = [];
      window.wirescape.onMessage(message => {
        if (message.type === 'app.engineRestartPolicy' && message.phase === 'waiting')
          window.__restartDelays.push(message.delayMs);
        if (message.type === 'hello') window.__restartHellos.push(message.session);
      });
      // A valid snapshot exercises the existing Studio crash-recovery modal path.
      localStorage.setItem('wirescape.autosave.v2', JSON.stringify({
        name: 'RS snapshot', patch: { format: 'wirescape.native.patch', version: 2, modules: [], connections: [] }
      }));
    });
    await expect.poll(() => page.evaluate(() => window.__restartDelays.slice(0, 3)), { timeout: 12000 })
      .toEqual([250, 500, 1000]);
    await expect(page.getByTestId('engine-restart-banner')).toBeVisible();
    await expect(page.getByTestId('recovery-modal')).toBeHidden();
    await expect(page.getByTestId('open-settings')).toBeEnabled();
    await expect.poll(() => page.evaluate(() => window.__restartDelays.slice(0, 9)), { timeout: 115000 })
      .toEqual([250, 500, 1000, 2000, 4000, 8000, 16000, 30000, 30000]);
    expect(Number(fs.readFileSync(countFile, 'utf8'))).toBeGreaterThanOrEqual(9);
    expect(await app.evaluate(() => globalThis.__failureDialogCount)).toBe(0);
    const loads = fs.readFileSync(loadsFile, 'utf8').trim().split('\n').map(line => JSON.parse(line));
    expect(new Set(loads.map(entry => entry.session)).size).toBeGreaterThanOrEqual(2);
    expect(loads[1].graph).toEqual(loads[0].graph);
    const sessions = await page.evaluate(() => window.__restartHellos);
    expect(new Set(sessions).size).toBeGreaterThanOrEqual(8);
  } finally {
    await app.close().catch(() => {});
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
test('RS stable status resets retry delay and clears the banner', async () => {
  test.setTimeout(60000);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-stable-restart-'));
  const countFile = path.join(dir, 'spawns');
  const app = await launch({ STUB_CRASH_COUNT_FILE: countFile, STUB_STABLE_SPAWN: '4' });
  try {
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    await page.evaluate(() => {
      window.__restartDelays = [];
      window.wirescape.onMessage(message => {
        if (message.type === 'app.engineRestartPolicy' && message.phase === 'waiting')
          window.__restartDelays.push(message.delayMs);
      });
    });
    await expect.poll(() => page.evaluate(() => window.__restartDelays.slice(0, 3)), { timeout: 15000 })
      .toEqual([250, 500, 1000]);
    await expect(page.getByTestId('engine-restart-banner')).toBeVisible();
    // The fourth engine has a continuous status heartbeat for >30s, then crashes.
    // It must recover from the prior crash loop without restarting the UI.
    await expect(page.getByTestId('engine-restart-banner')).toBeHidden({ timeout: 40000 });
    await expect.poll(() => page.evaluate(() => window.__restartDelays.slice(0, 4)), { timeout: 5000 })
      .toEqual([250, 500, 1000, 250]);
    expect(Number(fs.readFileSync(countFile, 'utf8'))).toBeGreaterThanOrEqual(4);
  } finally {
    await app.close().catch(() => {});
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
test('native File intents and open/save round-trip never expose a filesystem path', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-shell-'));
  const file = path.join(dir, 'patch.json');
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ dialog }, filepath) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filepath });
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [filepath] });
    }, file);
    const saved = await page.evaluate(() => window.wirescape.savePatch('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":true}\n', { saveAs: true }));
    expect(saved).toEqual({ name: 'patch.json' });
    expect(fs.readFileSync(file, 'utf8')).toBe('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":true}\n');
    expect(await page.evaluate(() => window.wirescape.openPatch()))
      .toEqual({ text: '{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":true}\n', name: 'patch.json' });
    await page.evaluate(() => {
      window.__intents = [];
      window.wirescape.onMessage(message => window.__intents.push(message));
    });
    await app.evaluate(({ Menu }) => {
      Menu.getApplicationMenu().getMenuItemById('open-patch').click();
      Menu.getApplicationMenu().getMenuItemById('save-patch').click();
      Menu.getApplicationMenu().getMenuItemById('save-as').click();
    });
    await expect.poll(() => page.evaluate(() => window.__intents.filter(v => typeof v.type === 'string' && v.type.startsWith('app.menu'))))
      .toEqual([
        { v: 0, type: 'app.menuOpenPatch' },
        { v: 0, type: 'app.menuSavePatch', saveAs: false },
        { v: 0, type: 'app.menuSavePatch', saveAs: true }
      ]);
  } finally {
    await app.close();
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
test('patch dialogs create the user patch folder lazily and retain the selected path', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-patches-'));
  const folder = path.join(dir, 'patches');
  const selected = path.join(dir, 'selected.json');
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    await app.evaluate(({ app, dialog }, directory) => {
      app.setPath('userData', directory);
      globalThis.__patchDefaults = [];
      dialog.showOpenDialog = async (_window, options) => {
        globalThis.__patchDefaults.push(options.defaultPath);
        return { canceled: true, filePaths: [] };
      };
      dialog.showSaveDialog = async (_window, options) => {
        globalThis.__patchDefaults.push(options.defaultPath);
        return { canceled: true };
      };
    }, dir);
    expect(fs.existsSync(folder)).toBe(false);
    expect(await page.evaluate(() => window.wirescape.openPatch())).toBeNull();
    expect(fs.statSync(folder).isDirectory()).toBe(true);
    const preserved = path.join(folder, 'existing.json');
    fs.writeFileSync(preserved, '{"unknown":"keep me"}\n');
    expect(await page.evaluate(() => window.wirescape.savePatch('{}', { saveAs: true }))).toBeNull();
    expect(await app.evaluate(() => globalThis.__patchDefaults))
      .toEqual([folder, path.join(folder, 'Untitled.json')]);
    expect(fs.readdirSync(folder)).toEqual(['existing.json']);

    await app.evaluate(({ dialog }, filename) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filename });
    }, selected);
    expect(await page.evaluate(() => window.wirescape.savePatch('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":42}\n', { saveAs: true })))
      .toEqual({ name: 'selected.json' });
    expect(fs.readFileSync(selected, 'utf8')).toBe('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":42}\n');
    await app.evaluate(({ dialog }) => {
      dialog.showSaveDialog = async (_window, options) => {
        globalThis.__patchDefaults.push(options.defaultPath);
        return { canceled: true };
      };
    });
    expect(await page.evaluate(() => window.wirescape.openPatch())).toBeNull();
    expect(await page.evaluate(() => window.wirescape.savePatch('{}', { saveAs: true }))).toBeNull();
    expect(await app.evaluate(() => globalThis.__patchDefaults.slice(-2))).toEqual([selected, selected]);
    // Cancelled Open/Save As must not redirect a subsequent plain Save.
    await page.evaluate(() => window.wirescape.savePatch('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":43}\n'));
    expect(fs.readFileSync(selected, 'utf8')).toBe('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"unknown":43}\n');
    expect(fs.readFileSync(preserved, 'utf8')).toBe('{"unknown":"keep me"}\n');
  } finally {
    await app.close();
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
test('an unavailable patch folder rejects file operations while the window remains usable', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-patch-error-'));
  fs.writeFileSync(path.join(dir, 'patches'), 'existing file');
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    await app.evaluate(({ app, dialog }, directory) => {
      app.setPath('userData', directory);
      dialog.showOpenDialog = dialog.showSaveDialog = async () => {
        throw new Error('Dialog must not open without a patch folder');
      };
    }, dir);
    await expect(page.evaluate(() => window.wirescape.openPatch())).rejects.toThrow('Could not create patch folder');
    await expect(page.evaluate(() => window.wirescape.savePatch('{}'))).rejects.toThrow('Could not create patch folder');
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    expect(await page.evaluate(() => Object.keys(window.wirescape).sort()))
      .toEqual(['onMessage', 'openPatch', 'platform', 'savePatch', 'send']);
    expect(fs.readFileSync(path.join(dir, 'patches'), 'utf8')).toBe('existing file');
  } finally {
    await app.close();
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
test('Escape exits F11 fullscreen and Quit closes engine stdin', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-eof-'));
  const marker = path.join(dir, 'shutdown');
  const app = await launch({ STUB_EXIT_MARKER: marker });
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].setFullScreen(true));
    await expect.poll(() => app.evaluate(({ BrowserWindow }) =>
      BrowserWindow.getAllWindows()[0].isFullScreen())).toBe(true);
    await page.keyboard.press('Escape');
    await expect.poll(() => app.evaluate(({ BrowserWindow }) =>
      BrowserWindow.getAllWindows()[0].isFullScreen())).toBe(false);
    await app.evaluate(({ app }) => app.quit());
    await expect.poll(() => fs.existsSync(marker)).toBe(true);
  } finally {
    await app.close().catch(() => {});
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('patch library keeps paths private, bounds reads and detaches bundled save targets', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-library-'));
  const patches = path.join(root, 'patches');
  fs.mkdirSync(patches);
  fs.writeFileSync(path.join(patches, 'Song.json'), '{"format":"wirescape.native.patch","version":2,"future":42}');
  fs.writeFileSync(path.join(patches, 'Huge.json'), 'x'.repeat(2097153));
  fs.writeFileSync(path.join(patches, 'Bad.json'), Buffer.from([255]));
  fs.writeFileSync(path.join(patches, 'Future.json'), '{"format":"wirescape.native.patch","version":99}');
  let app;
  try {
    app = await launch();
    // Playwright's Electron main-process evaluate runs without CommonJS require.
    // Create fixtures in this Node test process and pass only serializable paths.
    await app.evaluate(({ app }, directory) => app.setPath('userData', directory), root);
    const page = await app.firstWindow();
    await page.waitForFunction(() => document.body.dataset.ready === 'true');
    const listed = await page.evaluate(() => window.wirescape.openPatch({ library: 'list' }));
    expect(JSON.parse(listed.text)).toContain('Song.json');
    expect(listed.text).not.toContain(root);
    expect(await page.evaluate(() => window.wirescape.openPatch({ library: 'read', name: 'Song.json' })))
      .toEqual({ name: 'Song.json', text: '{"format":"wirescape.native.patch","version":2,"future":42}' });
    for (const name of ['../Song.json', 'Huge.json', 'Bad.json', 'Future.json']) {
      expect(await page.evaluate(async name => {
        try { await window.wirescape.openPatch({ library: 'read', name }); return false; } catch { return true; }
      }, name)).toBe(true);
    }
    if (process.platform !== 'win32') {
      fs.writeFileSync(path.join(root, 'Outside.json'), '{}');
      fs.symlinkSync(path.join(root, 'Outside.json'), path.join(patches, 'Escape.json'));
      expect(await page.evaluate(async () => {
        try { await window.wirescape.openPatch({ library: 'read', name: 'Escape.json' }); return false; } catch { return true; }
      })).toBe(true);
    }
    await page.evaluate(() => window.wirescape.openPatch({ library: 'reset' }));
    const output = path.join(patches, 'Copy.json');
    const expectedDefault = path.join(patches, 'Untitled.json');
    await app.evaluate(({ dialog }, paths) => {
      dialog.showSaveDialog = async (_window, options) => {
        if (options.defaultPath !== paths.expectedDefault) throw new Error('Wrong default folder');
        return { canceled: false, filePath: paths.output };
      };
    }, { output, expectedDefault });
    await page.evaluate(() => window.wirescape.savePatch('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"copy":true}', { saveAs: true }));
    expect(fs.readFileSync(output, 'utf8')).toBe('{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[],"copy":true}');
    expect(fs.readFileSync(path.join(patches, 'Song.json'), 'utf8')).toBe('{"format":"wirescape.native.patch","version":2,"future":42}');
  } finally {
    if (app) await app.close().catch(() => {});
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('unsupported opens never rebind Save and unsupported targets are never overwritten', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-refused-file-'));
  const good = path.join(dir, 'good.json'), rejected = path.join(dir, 'rejected.json');
  const native = unknown => JSON.stringify({ format: 'wirescape.native.patch', version: 2,
    modules: [], connections: [], unknown }) + '\n';
  fs.writeFileSync(good, native('original'));
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ dialog }, filename) => {
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [filename] });
    }, good);
    await page.evaluate(() => window.wirescape.openPatch());
    const fixture = path.resolve(__dirname, '../../../tests/native/compat/fixtures/legacy_documents');
    const invalid = fs.readdirSync(fixture).map(name => fs.readFileSync(path.join(fixture, name), 'utf8'));
    invalid.push('{broken', '[]', native(false).replace('"version":2', '"version":99'),
      native(false).replace('"unknown":false', '"unknown":1,"\\u0075nknown":2'),
      native(false).replace('"unknown":false', '"unknown":[{"a":1,"a":2}]'), ' '.repeat(2097153));
    const base = JSON.parse(native(false));
    const malformed = [{ modules: [{ id: 'bad', module: 'vendor.x' }] },
      { modules: [{ id: 1, module: 'x' }, { id: 1, module: 'y' }] }, { modules: [null] },
      { modules: [{ id: 1, module: null }] }, { connections: [null] },
    { ui: 4 }, { ui: { positions: 'bad' } }, { ui: { view: [] } }, { ui: { labels: false } },
    { ui: { cableColors: null } },
      { connections: [{ kind: 'future', from: { module: 1, port: 'a' }, to: { module: 99, port: 'b' } }] },
      { connections: [{ kind: 'signal', from: { module: 'bad', port: 'a' }, to: { module: 99, port: 'b' } }] },
      { version: 1, modules: undefined }, { version: 1, connections: undefined },
      { version: 1, modules: [{ id: 1, type: null }] },
    { version: 1, modules: [{ id: 1, type: 'essentials.vco', values: 4 }] },
      { version: 1, connections: [{ kind: 'audio', fromNode: 1, fromPort: 'a', toNode: 99 }] }];
    invalid.push(...malformed.map(change => JSON.stringify({ ...base, ...change })));
    for (const bytes of invalid) {
      fs.writeFileSync(rejected, bytes);
      await app.evaluate(({ dialog }, filename) => {
        dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [filename] });
        dialog.showSaveDialog = async () => ({ canceled: false, filePath: filename });
      }, rejected);
      await expect(page.evaluate(() => window.wirescape.openPatch())).rejects.toThrow('Could not read');
      await page.evaluate(text => window.wirescape.savePatch(text), native('still on good'));
      expect(fs.readFileSync(good, 'utf8')).toBe(native('still on good'));
      await expect(page.evaluate(text => window.wirescape.savePatch(text, { saveAs: true }), native('new')))
        .rejects.toThrow('Refusing to overwrite');
      expect(fs.readFileSync(rejected, 'utf8')).toBe(bytes);
    }
    const opaque = JSON.stringify({ ...base, modules: [{ id: 1, module: 'vendor.future', opaque: true }],
      connections: [{ kind: 'signal', from: { module: 1, port: 'future' }, to: { module: 99, port: 'missing' }, vendor: 42 }] });
    fs.writeFileSync(rejected, opaque);
    expect((await page.evaluate(() => window.wirescape.openPatch())).text).toBe(opaque);
    await page.evaluate(text => window.wirescape.savePatch(text), opaque);
    expect(fs.readFileSync(rejected, 'utf8')).toBe(opaque);
    expect(fs.readdirSync(dir).some(name => name.endsWith('.tmp') || name.includes('.bak-v1'))).toBe(false);
  } finally { await app.close(); fs.rmSync(dir, { recursive: true, force: true }); }
});


test('v1 Open is read-only and first Save writes the exact sibling backup', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-v1-backup-'));
  const file = path.join(dir, 'source.json'), fresh = path.join(dir, 'fresh.json');
  const original = ' ' + String.fromCharCode(10) +
    JSON.stringify({ format: 'wirescape.native.patch', version: 1,
      modules: [], connections: [], outputNode: 0, vendor: { untouched: true } }) + String.fromCharCode(10);
  const migrated = JSON.stringify({ format: 'wirescape.native.patch', version: 2,
    modules: [], connections: [], preserved: JSON.parse(original), vendor: { untouched: true } });
  fs.writeFileSync(file, original);
  const app = await launch();
  try {
    const page = await app.firstWindow();
    const before = fs.statSync(file).mtimeMs;
    await app.evaluate(({ dialog }, filename) => {
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [filename] });
    }, file);
    await page.evaluate(() => window.wirescape.openPatch());
    expect(fs.readFileSync(file, 'utf8')).toBe(original);
    expect(fs.statSync(file).mtimeMs).toBe(before);
    expect(fs.existsSync(file + '.bak-v1')).toBe(false);
    const backup = file + '.bak-v1';
    fs.mkdirSync(backup);
    await expect(page.evaluate(text => window.wirescape.savePatch(text), migrated))
      .rejects.toThrow('Could not create original patch backup; target was kept');
    expect(fs.readFileSync(file, 'utf8')).toBe(original);
    fs.rmdirSync(backup);
    await page.evaluate(text => window.wirescape.savePatch(text), migrated);
    expect(fs.readFileSync(backup, 'utf8')).toBe(original);
    expect(fs.readFileSync(file, 'utf8')).toBe(migrated);
    await page.evaluate(text => window.wirescape.savePatch(text), migrated);
    expect(fs.existsSync(backup + '.2')).toBe(false);
    await app.evaluate(({ dialog }, filename) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filename });
    }, file);
    await page.evaluate(text => window.wirescape.savePatch(text, { saveAs: true }), migrated);
    expect(fs.readFileSync(file, 'utf8')).toBe(migrated); // v2 destination, no second backup
    expect(fs.existsSync(backup + '.2')).toBe(false);
    await app.evaluate(({ dialog }, filename) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filename });
    }, fresh);
    await page.evaluate(text => window.wirescape.savePatch(text, { saveAs: true }), migrated);
    expect(fs.readFileSync(fresh, 'utf8')).toBe(migrated);
    expect(fs.existsSync(fresh + '.bak-v1')).toBe(false);
    expect(fs.readFileSync(file, 'utf8')).toBe(migrated);
    expect(fs.readdirSync(dir).filter(name => name.endsWith('.tmp'))).toEqual([]);
  } finally { await app.close(); fs.rmSync(dir, { recursive: true, force: true }); }
});

test('Save As to the opened v1 path backs up original bytes and writes the chosen destination', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-v1-same-path-'));
  const filename = path.join(dir, 'legacy.json');
  const original = ' ' + JSON.stringify({ format: 'wirescape.native.patch', version: 1,
    modules: [], connections: [], outputNode: 0 }) + '\n';
  const updated = JSON.stringify({ format: 'wirescape.native.patch', version: 2,
    modules: [], connections: [], preserved: JSON.parse(original) });
  fs.writeFileSync(filename, original);
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ dialog }, filepath) => {
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [filepath] });
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filepath });
    }, filename);
    const opened = await page.evaluate(() => window.wirescape.openPatch());
    expect(opened.text).toBe(original);
    expect(fs.readFileSync(filename, 'utf8')).toBe(original);
    expect(fs.existsSync(filename + '.bak-v1')).toBe(false);
    await page.evaluate(text => window.wirescape.savePatch(text, { saveAs: true }), updated);
    expect(fs.readFileSync(filename + '.bak-v1', 'utf8')).toBe(original);
    expect(fs.readFileSync(filename, 'utf8')).toBe(updated);
    expect(fs.existsSync(filename + '.bak-v1.2')).toBe(false);
  } finally { await app.close(); fs.rmSync(dir, { recursive: true, force: true }); }
});

test('Save As to an existing v1 destination uses lowest free backup; equal bytes are reused', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-v1-collision-'));
  const original = JSON.stringify({ format: 'wirescape.native.patch', version: 1,
    modules: [], connections: [], outputNode: 0 });
  const output = JSON.stringify({ format: 'wirescape.native.patch', version: 2,
    modules: [], connections: [] });
  const target = path.join(dir, 'target.json'), equal = path.join(dir, 'equal.json');
  const backup = target + '.bak-v1';
  fs.writeFileSync(target, original);
  fs.writeFileSync(backup, 'different first backup');
  fs.writeFileSync(backup + '.2', 'different second backup');
  fs.writeFileSync(equal, original);
  fs.writeFileSync(equal + '.bak-v1', original);
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ dialog }, filename) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filename });
    }, target);
    await page.evaluate(text => window.wirescape.savePatch(text, { saveAs: true }), output);
    expect(fs.readFileSync(target, 'utf8')).toBe(output);
    expect(fs.readFileSync(backup, 'utf8')).toBe('different first backup');
    expect(fs.readFileSync(backup + '.2', 'utf8')).toBe('different second backup');
    expect(fs.readFileSync(backup + '.3', 'utf8')).toBe(original);
    await app.evaluate(({ dialog }, filename) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: filename });
    }, equal);
    const before = fs.statSync(equal + '.bak-v1').mtimeMs;
    await page.evaluate(text => window.wirescape.savePatch(text, { saveAs: true }), output);
    expect(fs.readFileSync(equal, 'utf8')).toBe(output);
    expect(fs.statSync(equal + '.bak-v1').mtimeMs).toBe(before);
    expect(fs.existsSync(equal + '.bak-v1.2')).toBe(false);
    expect(fs.readdirSync(dir).filter(name => name.endsWith('.tmp'))).toEqual([]);
  } finally { await app.close(); fs.rmSync(dir, { recursive: true, force: true }); }
});

test('v1 library read and listing preserve disk bytes and exclude backup files', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-v1-library-'));
  const folder = path.join(dir, 'patches'), file = path.join(folder, 'Legacy.json');
  fs.mkdirSync(folder);
  const original = JSON.stringify({ format: 'wirescape.native.patch', version: 1,
    modules: [], connections: [], outputNode: 0 });
  fs.writeFileSync(file, original);
  const app = await launch();
  try {
    await app.evaluate(({ app }, directory) => app.setPath('userData', directory), dir);
    const page = await app.firstWindow();
    const before = fs.statSync(file).mtimeMs;
    const listed = await page.evaluate(() => window.wirescape.openPatch({ library: 'list' }));
    expect(JSON.parse(listed.text)).toContain('Legacy.json');
    const opened = await page.evaluate(() => window.wirescape.openPatch({ library: 'read', name: 'Legacy.json' }));
    expect(opened.text).toBe(original);
    expect(fs.readFileSync(file, 'utf8')).toBe(original);
    expect(fs.statSync(file).mtimeMs).toBe(before);
    expect(fs.existsSync(file + '.bak-v1')).toBe(false);
    fs.writeFileSync(file + '.bak-v1', original);
    const again = await page.evaluate(() => window.wirescape.openPatch({ library: 'list' }));
    expect(JSON.parse(again.text)).toEqual(['Legacy.json']);
  } finally { await app.close(); fs.rmSync(dir, { recursive: true, force: true }); }
});

test('atomic rename failure preserves disk contents and the Studio dirty marker until retry', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-commit-failure-'));
  const filename = path.join(dir, 'edited.json');
  const before = '{"format":"wirescape.native.patch","version":2,"modules":[],"connections":[]}\n';
  fs.writeFileSync(filename, before);
  const app = await launch();
  try {
    const page = await app.firstWindow();
    await expect(page.locator('body')).toHaveAttribute('data-ready', 'true');
    await page.evaluate(() => window.__wirescapeTest.doc.addModule('essentials.noise', {}, 30, 40));
    await expect(page.getByTestId('dirty-dot')).toHaveClass(/on/);
    await app.evaluate(({ dialog }, selected) => {
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: selected });
      const fsm = process.getBuiltinModule('node:fs');
      globalThis.__wsOriginalRename = fsm.promises.rename;
      fsm.promises.rename = async () => { throw new Error('injected commit refusal'); };
    }, filename);
    const recovery = page.getByTestId('recovery-modal');
    if (await recovery.isVisible()) await recovery.getByRole('button', { name: /dismiss|close|continue|ok/i }).click();
    await page.getByTestId('save-patch').click();
    await expect(page.getByText('Could not save patch')).toBeVisible();
    await expect(page.getByTestId('dirty-dot')).toHaveClass(/on/);
    expect(fs.readFileSync(filename, 'utf8')).toBe(before);
    expect(fs.readdirSync(dir).filter(name => name.endsWith('.tmp'))).toEqual([]);
    await app.evaluate(() => {
      const fsm = process.getBuiltinModule('node:fs');
      fsm.promises.rename = globalThis.__wsOriginalRename;
    });
    await page.getByTestId('save-patch').click();
    await expect(page.getByTestId('dirty-dot')).not.toHaveClass(/on/);
    expect(fs.readFileSync(filename, 'utf8')).not.toBe(before);
  } finally {
    try {
      await app.evaluate(() => {
        if (globalThis.__wsOriginalRename) {
          process.getBuiltinModule('node:fs').promises.rename = globalThis.__wsOriginalRename;
          delete globalThis.__wsOriginalRename;
        }
      });
    } finally {
      await app.close();
      fs.rmSync(dir, { recursive: true, force: true });
    }
  }
});

test('OB-h5 preset IPC lists typed files, bounds reads and never exposes paths', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'wirescape-presets-'));
  const folder = path.join(root, 'presets', 'osc');
  const file = path.join(folder, 'Custom.json');
  const app = await launch();
  const preset = JSON.stringify({ format: 'wirescape.osc.preset', version: 1, module: 'osc.in',
    name: 'Custom', config: { port: 9000, rows: Array.from({ length: 8 }, (_, i) => ({
      pattern: '/test/' + (i + 1), kind: 'cv', argument: 0, input_min: 0, input_max: 1,
      output_min: 0, output_max: 1, smoothing_ms: 5, timeout_ms: 1000, stale: 'hold',
    })) } });
  try {
    const page = await app.firstWindow();
    await app.evaluate(({ app, dialog, shell }, args) => {
      app.setPath('userData', args.root);
      dialog.showSaveDialog = async () => ({ canceled: false, filePath: args.file });
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [args.file] });
      shell.openPath = async value => { globalThis.__presetOpened = value; return ''; };
    }, { root, file });
    expect(await page.evaluate(() => window.wirescapeOscPresets.list('osc.in'))).toEqual([]);
    expect(fs.existsSync(folder)).toBe(true);
    await page.evaluate(text => window.wirescapeOscPresets.save(text, 'Custom'), preset);
    expect(fs.readFileSync(file, 'utf8')).toBe(preset);
    await expect(page.evaluate(text => {
      const p = JSON.parse(text); p.config.lan = true;
      return window.wirescapeOscPresets.save(JSON.stringify(p), 'Custom');
    }, preset)).rejects.toThrow('portable mapping fields');
    await expect(page.evaluate(text => {
      const p = JSON.parse(text); p.config.rows[0].host = '192.0.2.1';
      return window.wirescapeOscPresets.save(JSON.stringify(p), 'Custom');
    }, preset)).rejects.toThrow('portable mapping fields');
    expect(fs.readFileSync(file, 'utf8')).toBe(preset);
    fs.writeFileSync(path.join(folder, 'Invalid.json'), '{}');
    fs.writeFileSync(path.join(folder, 'Out.json'), preset.replace('osc.in', 'osc.out'));
    fs.writeFileSync(path.join(folder, 'Large.json'), ' '.repeat(262145));
    expect(await page.evaluate(() => window.wirescapeOscPresets.list('osc.in')))
      .toEqual([{ file: 'Custom.json', name: 'Custom' }]);
    expect(await page.evaluate(() => window.wirescapeOscPresets.read('Custom.json'))).toBe(preset);
    expect(await page.evaluate(() => window.wirescapeOscPresets.choose())).toBe(preset);
    await expect(page.evaluate(() => window.wirescapeOscPresets.read('../Custom.json'))).rejects.toThrow();
    await expect(page.evaluate(() => window.wirescapeOscPresets.read('Large.json'))).rejects.toThrow();
    await page.evaluate(() => window.wirescapeOscPresets.openFolder());
    expect(await app.evaluate(() => globalThis.__presetOpened)).toBe(folder);
  } finally { await app.close(); fs.rmSync(root, { recursive: true, force: true }); }
});
