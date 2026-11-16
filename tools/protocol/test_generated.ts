// SPDX-License-Identifier: GPL-3.0-only
// Unwired TS compiler AND runtime tests: this file is not imported by the app.
import {
  validateProtocolV0,
  type ProtocolCommand,
  type ProtocolReply,
  type ProtocolPush,
  type ProtocolV0,
  type ProtocolPatch,
  type ProtocolConnection,
} from '../../apps/studio/src/engine/generated/protocol_v0';

function check(observed: boolean, message: string): void {
  if (!observed) throw new Error(message);
}

// Required payload fields and discriminated command type are now emitted
// from the schema rather than using Record<string, unknown>.
const note: ProtocolCommand = { v: 0, id: 'note1', type: 'noteOn', note: 60, velocity: 0.75 };
const panic: ProtocolCommand = { v: 0, id: 'panic1', type: 'panic', additionalWireField: 42 };
const connection: ProtocolConnection = {
  kind: 'signal', from: { module: 9, port: 'audio' }, to: { module: 7, port: 'audio' },
};
const editable: ProtocolPatch = {
  format: 'wirescape.native.patch', version: 2,
  modules: [{ id: 7, module: 'essentials.output', customConfig: { keep: [1, null, 'opaque'] } }],
  connections: [], futureDocument: { text: 'retained' }, ui: { unknownUI: true },
};
const loaded: ProtocolCommand = { v: 0, id: 'load1', type: 'loadGraph', patch: editable };
const connected: ProtocolCommand = { v: 0, id: 'connect1', type: 'connect', connection };
const identity: ProtocolCommand = {
  v: 0, id: 'mod1', type: 'setModAmount',
  connection: { kind: 'modulation', from: { module: 10, port: 'control' },
    to: { module: 9, port: 'frequency' }, amount: 'ignored' },
  amount: -0.5,
};
const accepted: ProtocolReply = { v: 0, re: 'load1', ok: true, gen: '1' };
const refused: ProtocolReply = {
  v: 0, re: 'load1', ok: false, gen: '0', code: 'invalid', message: 'Invalid',
};
const event: ProtocolPush = {
  v: 0, type: 'app.engineExited', exitCode: 0, signal: null, expected: true,
};
const statusPush: ProtocolPush = {
  v: 0, session: 's1', type: 'status', gen: '1',
  status: {
    audio: { state: 'no-device', deviceId: null, deviceName: null,
      sampleRate: 48000, bufferFrames: 256, latencyMs: 10.67,
      cpuPercent: 0, dropouts: 0 },
    midi: { devices: [], activity: {}, futureMidi: { unknown: true } },
    futureStatus: { unknown: 'preserved' },
  },
};
const union: ProtocolV0[] = [note, panic, loaded, connected, identity, accepted, refused, event, statusPush];
for (const wire of union) check(validateProtocolV0(wire), 'valid generated payload rejected');

// Compile-time negative cases MUST produce TS errors; removing required
// command fields or assigning wrong scalar types must not typecheck.
// @ts-expect-error noteOn requires both note and velocity
const missingNoteAndVelocity: ProtocolCommand = { v: 0, id: 'bad', type: 'noteOn' };
// @ts-expect-error literal envelope version is zero, not a boolean
const invalidVersion: ProtocolCommand = { v: false, id: 'bad', type: 'panic' };
// @ts-expect-error successful/failed replies have literal boolean ok
const numericOk: ProtocolReply = { v: 0, re: 'bad', ok: 1, gen: '0' };
// @ts-expect-error patch requires connections, not merely modules
const incompletePatch: ProtocolPatch = { format: 'wirescape.native.patch', version: 2, modules: [] };
// @ts-expect-error ProtocolV0 union cannot accept an incomplete noteOn command
const missingUnionCommand: ProtocolV0 = { v: 0, id: 'bad', type: 'noteOn' };
// @ts-expect-error status push requires a typed status payload
const missingPushStatus: ProtocolPush = { v: 0, session: 's', type: 'status', gen: '1' };
// @ts-expect-error a real connection endpoint must reference numeric module id
const invalidConnection: ProtocolConnection = { kind: 'signal', from: { module: 'str', port: 'audio' }, to: { module: 7, port: 'audio' } };
void missingNoteAndVelocity;
void invalidVersion;
void numericOk;
void incompletePatch;
void invalidConnection;
void missingUnionCommand;
void missingPushStatus;

check(!validateProtocolV0({ v: false, id: 'x', type: 'panic' }), 'Boolean false must not equal JSON zero');
check(!validateProtocolV0({ v: 0, re: 'x', ok: 1, gen: '0' }), 'Number 1 must not equal Boolean true');
check(validateProtocolV0({ v: 0, re: 'x', ok: true, gen: '0' }), 'Boolean reply expected');
check(!validateProtocolV0({ v: 0, id: 'x', type: 'noteOn' }), 'Absent note/velocity accepted');
check(!validateProtocolV0({ v: 0, id: 'x', type: 'connect',
  connection: { ...connection, amount: 'ignored' } }), 'Connect typed amount improperly relaxed');
check(validateProtocolV0(identity), 'Identity nested amount must be ignored by schema');
for (const scalar of ['é', '🙂']) {
  for (const count of [33, 64]) {
    const id = scalar.repeat(count);
    check(new TextEncoder().encode(id).length > 64, 'Non-ASCII test lacks byte overflow');
    check(validateProtocolV0({ v: 0, id, type: 'panic' }),
      'JSON Schema maxLength counts Unicode codepoints, not UTF-8 bytes');
  }
  check(!validateProtocolV0({ v: 0, id: scalar.repeat(65), type: 'panic' }),
    '65 Unicode codepoints must exceed schema maxLength 64');
}
check(!validateProtocolV0({ v: 0, id: 'a'.repeat(65), type: 'panic' }),
  '65 ASCII characters must exceed maxLength');
check(validateProtocolV0({ v: 0, id: 'a'.repeat(64), type: 'panic' }),
  '64 ASCII characters must pass shape validation');
// The production native sidecar separately rejects non-ASCII request IDs.
// PV1 schema validation does not authorize sending Unicode IDs on the wire.
console.log('generated TS discriminated types and runtime JSON/Unicode regressions passed');
