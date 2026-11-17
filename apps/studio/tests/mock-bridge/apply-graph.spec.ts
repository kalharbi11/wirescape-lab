// SPDX-License-Identifier: GPL-3.0-only
import { test, expect, type Page } from '@playwright/test';
import { boot, settle, state } from '../helpers';
import { mockBridge } from './bridge';

type Wire = { type: string; patch?: any };
const patch = (modules: any[]) => ({
  format: 'wirescape.native.patch' as const, version: 2 as const, modules,
  connections: [], ui: { positions: Object.fromEntries(modules.map((m, i) => [m.id, [70 + i * 600, 50]])),
    view: { x: 0, y: 0, zoom: 1 }, labels: {} },
});
const wires = (page: Page) => page.evaluate(() =>
  ((window as any).__mockBridge.sent as Wire[]).filter(m => m.type === 'loadGraph' || m.type === 'applyGraph'));
async function setup(page: Page, capability: boolean, modules: any[]) {
  await mockBridge(page, { applyGraph: capability });
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'E1b'), patch(modules));
  await expect.poll(async () => (await page.evaluate(() => (window as any).__mockBridge.getGraph())).modules.length)
    .toBe(modules.length);
  await page.evaluate(() => { (window as any).__mockBridge.sent.length = 0; });
  await settle(page);
}
async function expectGraphCommands(page: Page, expected: string[]) {
  await expect.poll(async () => (await wires(page)).map(m => m.type)).toEqual(expected);
}

for (const capability of [true, false]) {
  const wire = capability ? 'applyGraph' : 'loadGraph';
  test.describe('E1b real bridge ' + (capability ? 'applyGraph capability' : 'legacy fallback'), () => {
    test('config edit, undo, redo and explicit snapshot restore all use the negotiated command', async ({ page }) => {
      await setup(page, capability, [{ id: 1, module: 'osc.in' }]);
      await page.evaluate(async () => {
        await window.__wirescapeTest.commitOscConfig(1,
          { port: 9005, lan: false, rows: [] }, 'osc.in');
      });
      await expectGraphCommands(page, [wire]);
      await page.evaluate(() => window.__wirescapeTest.undo());
      await expectGraphCommands(page, [wire, wire]);
      await page.evaluate(() => window.__wirescapeTest.redo());
      await expectGraphCommands(page, [wire, wire, wire]);
      await page.evaluate(() => window.__wirescapeTest.restoreSnapshot({
        format: 'wirescape.native.patch', version: 2,
        modules: [{ id: 1, module: 'osc.in', config: { port: 9010, rows: [] } }],
        connections: [],
      }));
      await expectGraphCommands(page, [wire, wire, wire, wire]);
      const graph = await page.evaluate(() => (window as any).__mockBridge.getGraph());
      expect(graph.modules[0].config.port).toBe(9010);
    });

    test('OSC In row edit and MIDI endpoint config edit use the negotiated command', async ({ page }) => {
      await setup(page, capability, [{ id: 1, module: 'osc.in' }, { id: 2, module: 'midi.in' }]);
      await page.getByTestId('osc-edit-1').click();
      await page.getByTestId('osc-row1-pattern').fill('/e1b/row');
      await page.getByTestId('osc-editor-save').click();
      await expectGraphCommands(page, [wire]);
      await page.evaluate(() => window.__wirescapeTest.setMidiEndpoint(2, 'M8 MIDI 1', 'M8:M8 MIDI 1'));
      await expectGraphCommands(page, [wire, wire]);
    });

    test('CC Learn commits one complete graph using the negotiated command', async ({ page }) => {
      await setup(page, capability, [{ id: 2, module: 'essentials.vcf' }]);
      await page.getByTestId('knob-2-cutoff').click({ button: 'right' });
      await page.getByTestId('context-midi').click();
      await expect(page.getByTestId('learn-bar')).toBeVisible();
      await expect(async () => {
        await page.evaluate(() => (window as any).__mockBridge.captureCc(
          'M8 MIDI 1|M8:M8 MIDI 1', 3, 74, 64));
        await expect(page.getByTestId('learn-message')).toContainText('CC 74', { timeout: 600 });
      }).toPass({ timeout: 10_000 });
      await page.getByTestId('learn-confirm').click();
      await expectGraphCommands(page, [wire]);
      const graph = await page.evaluate(() => (window as any).__mockBridge.getGraph());
      expect(graph.modules.some((m: any) => m.module === 'midi.cc_to_cv')).toBe(true);
      expect(graph.connections.some((c: any) => c.kind === 'modulation' && c.to.port === 'cutoff')).toBe(true);
    });
  });
}

test('capability-on graph refusal leaves running document, graph and generation untouched', async ({ page }) => {
  await setup(page, true, [{ id: 1, module: 'osc.in' }]);
  const before = await page.evaluate(() => ({
    graph: (window as any).__mockBridge.getGraph(),
    gen: (window as any).__mockBridge.generation(),
  }));
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('applyGraph', 'refused'));
  await page.evaluate(() => window.__wirescapeTest.commitOscConfig(1,
    { port: 9012, lan: false, rows: [] }, 'osc.in'));
  await expectGraphCommands(page, ['applyGraph']);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph())).toEqual(before.graph);
  await expect.poll(async () => (await state(page)).modules[0].config).toBeUndefined();
  expect(await page.evaluate(() => (window as any).__mockBridge.generation())).toBe(before.gen);
});

test('successful applyGraph with unapplied values reconciles engine and visible authored document', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]));
  await page.evaluate(() => window.__wirescapeTest.restoreSnapshot({
    format: 'wirescape.native.patch', version: 2,
    modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }],
    connections: [],
  }));
  await expectGraphCommands(page, ['applyGraph']);
  await expect.poll(async () => (await state(page)).modules[0].parameters.frequency).toBe(220);
  expect(await page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].parameters.frequency)).toBe(220);
});


test('refused undo restores history position and authored document without a compensating reload', async ({ page }) => {
  await setup(page, true, [{ id: 1, module: 'osc.in' }]);
  await page.evaluate(() => window.__wirescapeTest.commitOscConfig(1,
    { port: 9021, lan: false, rows: [] }, 'osc.in'));
  await expectGraphCommands(page, ['applyGraph']);
  const depth = await page.evaluate(() => window.__wirescapeTest.historyDepth());
  const before = await state(page);
  const gen = await page.evaluate(() => (window as any).__mockBridge.generation());
  await page.evaluate(() => (window as any).__mockBridge.refuseNext('applyGraph', 'refused'));
  await page.evaluate(() => window.__wirescapeTest.undo());
  await expectGraphCommands(page, ['applyGraph', 'applyGraph']);
  await expect.poll(async () => (await state(page)).modules[0].config.port).toBe(9021);
  expect(await page.evaluate(() => window.__wirescapeTest.historyDepth())).toEqual(depth);
  expect(await page.evaluate(() => (window as any).__mockBridge.generation())).toBe(gen);
  expect(await page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].config.port)).toBe(9021);
  expect((await state(page)).modules[0]).toEqual(before.modules[0]);
});

test('opening a different patch remains loadGraph even when applyGraph is supported', async ({ page }) => {
  await setup(page, true, [{ id: 1, module: 'osc.in' }]);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'Opened patch'), patch([{ id: 8, module: 'essentials.vco' }]));
  await expectGraphCommands(page, ['loadGraph']);
});


test('generation-only push cannot confirm applyGraph until delayed ACK reports unapplied parameters', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => {
    (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]);
    (window as any).__mockBridge.holdNext('applyGraph');
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }],
      connections: [],
    });
  });
  await expectGraphCommands(page, ['applyGraph']);
  await page.evaluate(() => (window as any).__mockBridge.loseHeldWithPush(true));
  const afterPush = await page.evaluate(() => {
    const real = window.__wirescapeTest.engine as any;
    return { settled: real.settleUnansweredLoad(true),
      confirmed: real.confirmed.modules[0].parameters.frequency,
      visible: window.__wirescapeTest.state().modules[0].parameters.frequency };
  });
  expect(afterPush).toEqual({ settled: false, confirmed: 220, visible: 440 });
  await page.evaluate(() => (window as any).__mockBridge.replyHeldLate());
  await expect.poll(async () => (await state(page)).modules[0].parameters.frequency).toBe(220);
  expect(await page.evaluate(() => (window.__wirescapeTest.engine as any).confirmed.modules[0].parameters.frequency))
    .toBe(220);
  expect(await page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].parameters.frequency))
    .toBe(220);
});

test('CC Learn generation push after delayed ACK threshold is not false success', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vcf' }]);
  await page.getByTestId('knob-2-cutoff').click({ button: 'right' });
  await page.getByTestId('context-midi').click();
  await expect(async () => {
    await page.evaluate(() => (window as any).__mockBridge.captureCc(
      'M8 MIDI 1|M8:M8 MIDI 1', 3, 74, 64));
    await expect(page.getByTestId('learn-message')).toContainText('CC 74', { timeout: 600 });
  }).toPass({ timeout: 10_000 });
  await page.evaluate(() => (window as any).__mockBridge.holdNext('applyGraph'));
  await page.getByTestId('learn-confirm').click();
  await expectGraphCommands(page, ['applyGraph']);
  await page.evaluate(() => (window as any).__mockBridge.loseHeldWithPush(true));
  // App's legacy-load recovery timer checks the gen after 3 seconds. A
  // generation push must not release the Learn busy gate without applyGraph ACK.
  await page.waitForTimeout(3150);
  await page.evaluate(() => (window as any).__mockBridge.status());
  await expect(page.getByTestId('midi-learn-applying')).toBeVisible();
  await page.evaluate(() => (window as any).__mockBridge.replyHeldLate());
  await expect(page.getByTestId('midi-learn-applying')).toBeHidden();
  expect((await state(page)).modules.some((m: any) => m.module === 'midi.cc_to_cv')).toBe(true);
});

test('two overlapping snapshot replans serialize as applyGraph; stale ACK cannot alter doc or gen', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => {
    (window as any).__mockBridge.holdNext('applyGraph');
    for (const frequency of [440, 660]) {
      window.__wirescapeTest.restoreSnapshot({
        format: 'wirescape.native.patch', version: 2,
        modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency } }],
        connections: [],
      });
    }
  });
  await expectGraphCommands(page, ['applyGraph']); // second queued, not demoted to loadGraph
  const first = (await wires(page))[0] as any;
  await page.evaluate(() => (window as any).__mockBridge.acceptHeld());
  await expectGraphCommands(page, ['applyGraph', 'applyGraph']);
  await expect.poll(() => page.evaluate(() => (window as any).__mockBridge.getGraph().modules[0].parameters.frequency))
    .toBe(660);
  const beforeLate = await page.evaluate(() => ({
    gen: (window.__wirescapeTest.engine as any).generation(),
    committed: (window.__wirescapeTest.engine as any).confirmed.modules[0].parameters.frequency,
    authored: window.__wirescapeTest.state().modules[0].parameters.frequency,
  }));
  expect(beforeLate.committed).toBe(660);
  expect(beforeLate.authored).toBe(660);
  await page.evaluate(id => (window as any).__mockBridge.lateReply(id, '999'), first.id);
  const afterLate = await page.evaluate(() => ({
    gen: (window.__wirescapeTest.engine as any).generation(),
    committed: (window.__wirescapeTest.engine as any).confirmed.modules[0].parameters.frequency,
    authored: window.__wirescapeTest.state().modules[0].parameters.frequency,
  }));
  expect(afterLate).toEqual(beforeLate);
});

test('reordered equivalent config and native-ignored config fields allow valid unapplied ACK', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco',
    config: { first: 1, second: 2 }, parameters: { frequency: 220 } }]);
  await page.evaluate(() => {
    (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]);
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco',
        config: { second: 2, first: 1 }, parameters: { frequency: 440 } }],
      connections: [],
    });
  });
  await expectGraphCommands(page, ['applyGraph']);
  await expect.poll(async () => (await state(page)).modules[0].parameters.frequency).toBe(220);
  expect((await page.evaluate(() => (window.__wirescapeTest.engine as any).confirmed.modules[0].parameters.frequency)))
    .toBe(220);
  // Native canonical config may ignore a source-authored key. The native
  // replaced list (not JSON.stringify of authoring config) is authoritative.
  await page.evaluate(() => {
    (window as any).__mockBridge.setNativeReplaced([]);
    (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]);
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco',
        config: { first: 1, second: 2, ignoredDefault: 0 }, parameters: { frequency: 880 } }],
      connections: [],
    });
  });
  await expectGraphCommands(page, ['applyGraph', 'applyGraph']);
  await expect.poll(async () => (await state(page)).modules[0].parameters.frequency).toBe(220);
});

test('native replaced ID in unapplied list still fails closed', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => {
    (window as any).__mockBridge.setNativeReplaced([2]);
    (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]);
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco',
        config: { newMode: 1 }, parameters: { frequency: 440 } }],
      connections: [],
    });
  });
  await expectGraphCommands(page, ['applyGraph']);
  await expect.poll(() => page.evaluate(() => (window.__wirescapeTest.engine as any).ready)).toBe(false);
  const confirmed = await page.evaluate(() => (window.__wirescapeTest.engine as any).confirmed.modules[0].parameters.frequency);
  expect(confirmed).toBe(220);
});


/** Q14/Q16: three views of the same graph plus the editor's dirty/history cursor. */
async function graphCheckpoint(page: Page) {
  return page.evaluate(() => {
    const t = window.__wirescapeTest, e = t.engine as any;
    const pick = (p: any) => p.modules.find((m: any) => m.id === 2)?.parameters ?? {};
    const undo = document.querySelector('[data-testid="undo"]') as HTMLButtonElement;
    const redo = document.querySelector('[data-testid="redo"]') as HTMLButtonElement;
    return { authored: pick(t.state()), confirmed: pick(e.confirmed),
      native: pick((window as any).__mockBridge.getGraph()),
      dirty: t.doc.dirty, history: t.historyDepth(),
      canUndo: !undo.disabled, canRedo: !redo.disabled };
  });
}
const frequencySnapshot = (frequency: number, amplitude?: number) => ({
  format: 'wirescape.native.patch' as const, version: 2 as const,
  modules: [{ id: 2, module: 'essentials.vco',
    parameters: { frequency, ...(amplitude === undefined ? {} : { amplitude }) } }],
  connections: [],
});
async function equalConfirmed(page: Page, frequency: number, amplitude?: number) {
  await expect.poll(async () => {
    const s = await graphCheckpoint(page);
    return s.authored.frequency === frequency && s.confirmed.frequency === frequency &&
      s.native.frequency === frequency && JSON.stringify(s.authored) === JSON.stringify(s.confirmed) &&
      JSON.stringify(s.confirmed) === JSON.stringify(s.native) &&
      (amplitude === undefined || s.authored.amplitude === amplitude);
  }).toBe(true);
}

test('Q14 A+B refused: one anchor restores 220, dirty and history position', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  const before = await graphCheckpoint(page);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.holdNext('applyGraph');
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }], connections: [],
    });
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 660 } }], connections: [],
    });
  });
  await expectGraphCommands(page, ['applyGraph']);
  await page.evaluate(() => (window as any).__mockBridge.refuseHeld());
  await equalConfirmed(page, 220);
  const after = await graphCheckpoint(page);
  expect(after).toEqual(before);
});

test('Q14 A confirmed/B refused: anchor advances to 440 with correct undo cursor', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.holdNext('applyGraph');
    for (const frequency of [440, 660]) window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency } }], connections: [],
    });
    b.refuseNext('applyGraph', 'refused');
    b.acceptHeld();
  });
  await expectGraphCommands(page, ['applyGraph', 'applyGraph']);
  await equalConfirmed(page, 440);
  const after = await graphCheckpoint(page);
  expect(after.dirty).toBe(true);
  expect(after.canUndo).toBe(true);
  expect(after.canRedo).toBe(false);
  expect(after.history.past).toBeGreaterThan(0);
});

test('Q14 partial A confirmed/B refused: unapplied side value never enters rollback anchor', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco',
    parameters: { frequency: 220, amplitude: 0.5 } }]);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.setUnapplied([{ moduleId: 2, paramId: 'amplitude' }]);
    b.holdNext('applyGraph');
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco',
        parameters: { frequency: 440, amplitude: 0.7 } }], connections: [],
    });
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco',
        parameters: { frequency: 660, amplitude: 0.7 } }], connections: [],
    });
    b.refuseNext('applyGraph');
    b.acceptHeld();
  });
  await expectGraphCommands(page, ['applyGraph', 'applyGraph']);
  await equalConfirmed(page, 440, 0.5);
  const after = await graphCheckpoint(page);
  expect(after.dirty).toBe(true);
  expect(after.canUndo).toBe(true);
  expect(after.canRedo).toBe(false);
});

test('Q14 partial earlier checkpoint then two refused: restored anchor is 220', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco',
    parameters: { frequency: 220, amplitude: 0.5 } }]);
  await page.evaluate(() => {
    (window as any).__mockBridge.setUnapplied([{ moduleId: 2, paramId: 'frequency' }]);
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco',
        parameters: { frequency: 440, amplitude: 0.5 } }], connections: [],
    });
  });
  await equalConfirmed(page, 220, 0.5);
  const prior = await graphCheckpoint(page);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.holdNext('applyGraph');
    for (const frequency of [440, 660]) window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency, amplitude: 0.5 } }],
      connections: [],
    });
    b.refuseHeld();
  });
  await equalConfirmed(page, 220, 0.5);
  const after = await graphCheckpoint(page);
  expect(after.dirty).toBe(prior.dirty);
  expect(after.history).toEqual(prior.history);
  expect(after.canUndo).toBe(prior.canUndo);
  expect(after.canRedo).toBe(prior.canRedo);
});

test('Q16 e: 330 setParam ACK precedes held 440 snapshot, then graph refusal restores 330', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.holdNext('setParam');
    window.__wirescapeTest.commitParam(2, 'frequency', 330);
    b.holdNext('applyGraph');
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }], connections: [],
    });
  });
  await expect.poll(async () => (await wires(page)).length).toBe(0);
  expect(await graphCheckpoint(page)).toMatchObject({ authored: { frequency: 330 }, native: { frequency: 220 } });
  await page.evaluate(() => (window as any).__mockBridge.acceptHeld());
  await expectGraphCommands(page, ['applyGraph']);
  await page.evaluate(() => (window as any).__mockBridge.refuseHeld());
  await equalConfirmed(page, 330);
  const after = await graphCheckpoint(page);
  expect(after.dirty).toBe(true);
  expect(after.canUndo).toBe(true);
  expect(after.canRedo).toBe(false);
});

test('Q16 f: rejected pending 330 edit rolls back before 440 snapshot is authored', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  const baseline = await graphCheckpoint(page);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.holdNext('setParam');
    window.__wirescapeTest.commitParam(2, 'frequency', 330);
    b.holdNext('applyGraph');
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }], connections: [],
    });
  });
  await expect.poll(async () => (await wires(page)).length).toBe(0);
  await page.evaluate(() => (window as any).__mockBridge.refuseHeld());
  await expectGraphCommands(page, ['applyGraph']);
  await page.evaluate(() => (window as any).__mockBridge.refuseHeld());
  await equalConfirmed(page, 220);
  const after = await graphCheckpoint(page);
  expect(after.dirty).toBe(baseline.dirty);
  expect(after.history).toEqual(baseline.history);
  expect(after.canUndo).toBe(baseline.canUndo);
  expect(after.canRedo).toBe(baseline.canRedo);
});

test('Q16 g: edit authored behind pending chain is never sent after refusal', async ({ page }) => {
  await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
  const baseline = await graphCheckpoint(page);
  await page.evaluate(() => {
    const b = (window as any).__mockBridge;
    b.holdNext('applyGraph');
    window.__wirescapeTest.restoreSnapshot({
      format: 'wirescape.native.patch', version: 2,
      modules: [{ id: 2, module: 'essentials.vco', parameters: { frequency: 440 } }], connections: [],
    });
    window.__wirescapeTest.commitParam(2, 'frequency', 660);
  });
  await expectGraphCommands(page, ['applyGraph']);
  await page.evaluate(() => (window as any).__mockBridge.refuseHeld());
  await equalConfirmed(page, 220);
  const commands = await page.evaluate(() => (window as any).__mockBridge.sent.map((x: any) => x.type));
  expect(commands).not.toContain('setParam');
  const after = await graphCheckpoint(page);
  expect(after.dirty).toBe(baseline.dirty);
  expect(after.history).toEqual(baseline.history);
  expect(after.canUndo).toBe(baseline.canUndo);
  expect(after.canRedo).toBe(baseline.canRedo);
});

/** Q20(h): a 350 ms debounced edit must settle before the snapshot's anchor. */
for (const editConfirmed of [true, false]) {
  test(`Q20 h: debounced 330 ${editConfirmed ? 'confirmed' : 'refused'} before refused snapshot keeps anchor undo/redo`, async ({ page }) => {
    await setup(page, true, [{ id: 2, module: 'essentials.vco', parameters: { frequency: 220 } }]);
    const baseline = await graphCheckpoint(page);
    await page.evaluate(target => {
      const b = (window as any).__mockBridge;
      b.holdNext('setParam');
      // commitParam schedules History's 350 ms timer, but its ACK is held.
      window.__wirescapeTest.commitParam(2, 'frequency', 330);
      b.holdNext('applyGraph');
      // The snapshot must remain un-authored while the incremental ACK is held.
      window.__wirescapeTest.restoreSnapshot(target);
    }, frequencySnapshot(440));
    await expect.poll(async () => (await wires(page)).length).toBe(0);
    expect(await graphCheckpoint(page)).toMatchObject({
      authored: { frequency: 330 }, confirmed: { frequency: 220 },
    });
    await page.evaluate(confirm => {
      const b = (window as any).__mockBridge;
      if (confirm) b.acceptHeld();
      else b.refuseHeld();
    }, editConfirmed);
    await expectGraphCommands(page, ['applyGraph']);
    await page.evaluate(() => (window as any).__mockBridge.refuseHeld());
    await equalConfirmed(page, editConfirmed ? 330 : 220);
    const after = await graphCheckpoint(page);
    expect(after.dirty).toBe(editConfirmed ? true : baseline.dirty);
    expect(after.canUndo).toBe(editConfirmed ? true : baseline.canUndo);
    expect(after.canRedo).toBe(baseline.canRedo);
    expect(after.history.past).toBe(baseline.history.past + (editConfirmed ? 1 : 0));
    expect(after.history.future).toBe(baseline.history.future);
  });
}
