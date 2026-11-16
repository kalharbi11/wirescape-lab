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
  type ProtocolApplyGraphResult,
} from '../../apps/studio/src/engine/generated/protocol_v0';

// Test-only Node reader, no new dependency or runtime import.
declare const require: (id: string) => {
  readFileSync: (path: string, encoding: string) => string
};

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
const applyGraph: ProtocolCommand = { v: 0, id: 'apply1', type: 'applyGraph', patch: editable };
const applyResult: ProtocolApplyGraphResult = { path: 'live', replaced: [], unapplied: [] };
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
const union: ProtocolV0[] = [note, panic, loaded, connected, applyGraph, identity, accepted, refused, event, statusPush];
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
type RequestIdCase = { name: string; id: string; valid: boolean };
const idCases = JSON.parse(
  require('node:fs').readFileSync('tools/protocol/request_id_cases.json', 'utf8')
) as RequestIdCase[];
check(idCases.length >= 10, 'missing shared Q8 corpus');
for (const example of idCases) {
  check(validateProtocolV0({ v: 0, id: example.id, type: 'panic' }) === example.valid,
    'Q8 TS request-ID disagreement: ' + example.name);
}
type BusChannelCase = { name: string; value: number; valid: boolean };
const busCases = JSON.parse(
  require('node:fs').readFileSync('tools/protocol/bus_channel_cases.json', 'utf8')
) as BusChannelCase[];
check(busCases.length === 6, 'missing Q13 bus-channel corpus');
for (const sample of busCases) {
  const patch = { ...editable, outputs: [{ module: 7, port: 'audio', bus_channel: sample.value }] };
  for (const type of ['loadGraph', 'applyGraph']) {
    check(validateProtocolV0({ v: 0, id: 'bus', type, patch }) === sample.valid,
      'Q13 TS output-channel mismatch: ' + sample.name + '/' + type);
  }
}
check(validateProtocolV0({ v: 0, re: 'apply1', ok: true, gen: '1', result: applyResult }),
  'applyGraph result envelope rejected');
check(!validateProtocolV0({ v: 0, re: 'apply1', ok: true, gen: '1',
  result: { path: 'other', replaced: [], unapplied: [] } }), 'invalid applyGraph path accepted');
// @ts-expect-error applyGraph always requires a PatchV2
const incompleteApply: ProtocolCommand = { v: 0, id: 'bad', type: 'applyGraph' };
void incompleteApply;

// The Q8 pattern applies ONLY to request IDs. Generic JSON Schema strings
// still use Unicode-codepoint minLength/maxLength, never byte length.
for (const scalar of ['é', '🙂']) {
  const other = { v: 0, id: 'ascii', type: 'selectAudioDevice',
    deviceId: scalar.repeat(129) };
  check(new TextEncoder().encode(other.deviceId).length > 256,
    'generic Unicode fixture does not exceed 256 UTF-8 bytes');
  check(validateProtocolV0(other), 'generic Unicode string must count codepoints');
  check(!validateProtocolV0({ ...other, deviceId: scalar.repeat(257) }),
    'generic Unicode 257 codepoints must exceed maxLength 256');
}
console.log('generated TS discriminated types, Q8 ASCII and Unicode regressions passed');

