// SPDX-License-Identifier: GPL-3.0-only
// A10 OB-c Echo: measure ACTUAL Studio knob pointermove -> setParam cadence.
// This is a capture/gesture fact, NOT a native sidecar click/sound pass.
// The native PCM oracle will replay this exact trace after the lead authorizes
// artifact transfer and a CTest/native-binary writer slot.
import { test, expect } from '@playwright/test';
import patch from '../patches/basics-03-echo-and-reverb.json' with { type: 'json' };
import { boot } from './helpers';

type ParamEvent = { t_ms: number; moduleId: number; paramId: string; value: number };

test('OB-c A10 Echo: actual 100 ms / 1 s knob gestures emit measured setParam trace', async ({ page }, testInfo) => {
  await boot(page);
  await page.evaluate(p => window.__wirescapeTest.load(p, 'A10 Echo trace'), patch);
  await page.evaluate(() => {
    // Move the real Studio canvas view to the Echo card before pointer input.
    const vp = window.__wirescapeTest.canvas.viewport;
    vp.setView(vp.view.x, vp.view.y, 1);
    const card = document.querySelector<HTMLElement>('[data-testid="module-6"]');
    if (!card) throw new Error('INFRA_A10_ECHO: no real delay card');
    const rect = card.getBoundingClientRect(), bounds = vp.rect();
    vp.setView(vp.view.x - (rect.left - bounds.left) + 50,
               vp.view.y - (rect.top - bounds.top) + 70, 1);
    const api = window.__wirescapeTest;
    const engine = api.engine as any;
    const events: ParamEvent[] = [];
    (window as any).__obCA10ParamEvents = events;
    const original = engine.setParam.bind(engine);
    engine.setParam = (moduleId: number, paramId: string, value: number): void => {
      events.push({ t_ms: performance.now(), moduleId, paramId, value });
      original(moduleId, paramId, value);
    };
  });

  // Knob.ts:303–332: one setValue(..., false) for each REAL pointermove and
  // setValue(..., true) on pointerup. The Studio implementation does not set
  // a fixed 60-Hz command timer. Drive real DOM gestures; never substitute a
  // guessed cadence for the captured timestamps.
  const data: Array<{
    knob: string; duration_nominal_ms: number;
    gesture_start_ms: number; gesture_end_ms: number;
    events: ParamEvent[];
  }> = [];
  for (const duration of [100, 1000]) {
    for (const knob of ['time', 'feedback', 'tone', 'mix']) {
      const slider = page.getByTestId('knob-6-' + knob).getByRole('slider');
      await slider.scrollIntoViewIfNeeded();
      const box = await slider.boundingBox();
      expect(box, 'the real Echo knob must render').not.toBeNull();
      const startX = box!.x + box!.width / 2;
      const startY = box!.y + box!.height / 2;
      await page.mouse.move(startX, startY);
      const start = await page.evaluate(() => performance.now());
      await page.mouse.down();
      const steps = duration === 100 ? 6 : 60;
      for (let i = 1; i <= steps; i++) {
        await page.mouse.move(startX, startY - 36 * i / steps);
        await page.waitForTimeout(duration / steps);
      }
      await page.mouse.up();
      const end = await page.evaluate(() => performance.now());
      // The observer is deliberately not emptied between gestures until after
      // asserting its full per-drag product trace.
      const all = await page.evaluate(() => (window as any).__obCA10ParamEvents as ParamEvent[]);
      const within = all.filter(e =>
        e.moduleId === 6 && e.paramId === knob && e.t_ms >= start && e.t_ms <= end + 1);
      expect(within.length, 'real Knob pointermove/setParam, not FakeEngine rendering').toBeGreaterThan(2);
      expect(within.every(e => Number.isFinite(e.value))).toBe(true);
      expect(within.every((e, i) => i === 0 || e.t_ms >= within[i - 1].t_ms)).toBe(true);
      data.push({ knob, duration_nominal_ms: duration,
        gesture_start_ms: start, gesture_end_ms: end,
        events: within.map(e => ({ ...e, t_ms: e.t_ms - start })) });
    }
  }
  // Mode/division are STEP switches. A10 says report-only; no sound/click
  // threshold is asserted for them (separate 0011 row 8 fix).
  const switches = await page.evaluate(() => {
    const api = window.__wirescapeTest, e = api.engine as any;
    const prior = (window as any).__obCA10ParamEvents.length;
    e.setParam(6, 'mode', 0);
    e.setParam(6, 'division', 3);
    return ((window as any).__obCA10ParamEvents as ParamEvent[]).slice(prior);
  });
  const evidence = {
    kind: 'OB-c A10 actual Studio knob pointer events to FakeEngine setParam',
    source: 'apps/studio/src/panels/widgets/Knob.ts:303-332',
    real_sidecar_or_audio: false,
    device_used: false,
    delay_module_id: 6,
    gestures: data,
    mode_division_record_only: switches,
  };
  await testInfo.attach('ob-c-a10-studio-setparam-cadence', {
    body: JSON.stringify(evidence, null, 2), contentType: 'application/json',
  });
  console.log('OB-C-A10-CADENCE-FACT ' + JSON.stringify(evidence));
  expect(data).toHaveLength(8);
});
