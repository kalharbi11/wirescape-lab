// SPDX-License-Identifier: GPL-3.0-only
// OB-c pre-S6: actual RealEngine query/command path with an injected fake
// Windows audio backend. Does not pretend an ASIO driver is installed.
const { test, expect } = require('@playwright/test');
const { RealEngine } = require('../src/engine/RealEngine');
const { ModuleRegistry } = require('../src/modules/registry');

test('OB-c: while running, a new ASIO enumeration replaces stale devices without graph reload', async () => {
  const sent = [];
  const asio = {
    id: 'ASIO|FlexASIO', hostApi: 'ASIO', backend: 'asio',
    name: 'FlexASIO', kind: 'audio', supported: true,
    outputChannels: 2, sampleRates: [48000],
  };
  const wasapi = {
    id: 'Windows WASAPI|Speakers', hostApi: 'Windows WASAPI',
    name: 'Speakers', kind: 'audio', supported: true,
  };
  const old = {
    id: 'Windows WASAPI|Old', hostApi: 'Windows WASAPI',
    name: 'Old', kind: 'audio', supported: true,
  };
  let receive;
  let graphLoads = 0;
  let currentGen = '0';
  const emit = value => {
    if (!receive) throw new Error('no RealEngine listener');
    receive(value);
  };
  const bridge = {
    platform: 'win32',
    onMessage(callback) { receive = callback; return () => { receive = null; }; },
    send(message) {
      sent.push(message);
      if (message.type === 'loadGraph') {
        ++graphLoads;
        currentGen = String(Number(currentGen) + 1);
        queueMicrotask(() => emit({ v: 0, re: message.id, session: 'obc',
          gen: currentGen, ok: true }));
      } else if (message.type === 'listAudioDevices') {
        // The backend publishes a new ASIO driver after hello, while the
        // already loaded graph and its generation remain in service.
        queueMicrotask(() => emit({ v: 0, re: message.id, session: 'obc',
          gen: currentGen, ok: true,
          result: { devices: [wasapi, asio],
            audio: { unavailableDrivers: [
              { hostApi: 'ASIO', name: 'Uninitialized ASIO', reason: 'init failed' },
            ] } } }));
      } else if (message.type === 'selectAudioDevice') {
        queueMicrotask(() => emit({ v: 0, re: message.id, session: 'obc',
          gen: currentGen, ok: true }));
      } else throw new Error('unexpected command ' + message.type);
    },
  };
  const patch = { format: 'wirescape.native.patch', version: 2,
    modules: [{ id: 1, module: 'essentials.output' }], connections: [] };
  const engine = new RealEngine(bridge, () => patch, new ModuleRegistry([]));
  engine.start();
  let status;
  const unsubscribe = engine.onStatus(value => { status = value; });
  emit({ v: 0, type: 'hello', protocol: 0, session: 'obc', gen: '0',
    capabilities: [], catalogue: { modules: [] },
    audio: { state: 'running', deviceId: old.id, deviceName: old.name,
      sampleRate: 48000, bufferFrames: 256, latencyMs: 10.67,
      cpuPercent: 3, dropouts: 0 },
    midi: { devices: [], activity: {} } });
  await engine.loadGraph(patch);
  const generation = engine.generation();
  expect(graphLoads).toBe(1);
  const discovered = await engine.listAudioDevices();
  expect(discovered).toEqual([wasapi, asio]);
  expect(status.audio.state).toBe('running');
  expect(status.audio.unavailableDrivers).toEqual([
    { hostApi: 'ASIO', name: 'Uninitialized ASIO', reason: 'init failed' },
  ]);
  expect(discovered).not.toContainEqual(expect.objectContaining({ name: 'Uninitialized ASIO' }));
  expect(engine.generation()).toBe(generation);
  expect(graphLoads).toBe(1);
  engine.selectAudioDevice(asio.id);
  expect(sent.at(-1)).toMatchObject({ type: 'selectAudioDevice', deviceId: asio.id });
  expect(graphLoads).toBe(1);
  unsubscribe();
  engine.stop();
});
