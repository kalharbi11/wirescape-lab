<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0008 — One transport: tempo and play/stop from the app to modules (design for T1.7)

Fable, 2026-11-16 (ET), against `main` at `c692c7a`. Not yet contracted: TR1 touches the engine
and the sidecar, so it starts after M1 stage S5b.

## Today (observed)
- The engine has a transport: `cfg.bpm` 120, `cfg.playing` true, a running `beat`
  (`engine2.h` Config; `engine2.cpp:647-649, 929`). Every module receives it in `ws2_process`.
- `Engine::transport()` (`engine2.cpp:989`) writes those three values directly. Render reads them
  at the same time, so calling it while audio runs is a data race. Nothing in the sidecar,
  facade or document loader calls it. The host tempo is therefore always 120 and always playing.
- Only the LFO reads the host transport, for its sync option (`modules2/lfo/dsp.h:28-29`).
- Clock has its own `bpm` parameter and integrates its own phase (`modules2/clock/dsp.h:8-12`).
- Groove has its own `bpm` in config (`modules2/groove/config.h:35`), so changing it replaces the
  instance.
- Studio's status bar shows the Clock module's tempo, not the host's (`StatusBar.ts:133`,
  `App.ts:1008`). The protocol has no transport command.

So a patch can hold three unrelated tempos, and the one the engine distributes cannot be set.

## Decisions
1. **The patch has one transport.** Document: `settings.transport = {bpm, playing}`, default
   `{120, true}` when absent, which is today's behaviour. It is saved with the patch.
2. **Protocol (additive to v0):** capability `transport`; command
   `setTransport {bpm?: 20..300, playing?: boolean, beat?: number ≥ 0}`, apply class `live`;
   `status` gains `transport {bpm, playing, beat}`. `beat` in the command is a locate.
3. **Engine: transport changes travel as a packet.** The control side sends one host packet
   (event type `WS2_TRANSPORT_EVENT`, addressed to the host, not to a node) through the existing
   critical ingress ring. Render applies it in `collect()` at the start of a block. bpm, playing
   and beat change together; `beat` stays continuous unless the packet locates. The direct writes
   in `Engine::transport()` are removed for a prepared engine; before `prepare` it may still set
   the initial values.
4. **Stop means the beat stops, not the audio.** `playing=false` freezes `beat` and clears
   `WS2_PLAYING`. Modules keep processing; tails ring; a keyboard note still sounds.
5. **Transport survives edits.** It lives in the engine's persistent state, so replan and
   `applyGraph` keep bpm, playing and beat. `loadGraph` takes them from the new document and
   starts at beat 0.
6. **Followers derive phase from the beat; they do not integrate it.** A module following the
   host computes its position from `transport.beat` (as the LFO does). Followers therefore agree
   with each other and a locate works.
7. **Following is opt-in per module, default off for existing documents.** Sound of saved patches
   does not change (Fixed constraint).
   - Clock: new parameter `sync` (stepped, 0 = internal, 1 = host), added at the end of the
     parameter table; default 0. With `sync` on, tick phase is `frac(beat × ticks_per_beat)`, the
     `bpm` parameter is ignored, and the clock outputs nothing while the host is stopped.
   - Groove: new config field `tempo_source` (`internal` | `host`), default `internal`. With
     `host`, step position comes from the beat and the module runs only while both the host and
     its own run state are on. When module data lands (`0005` E3) this field moves there.
   - LFO: unchanged.
8. **Studio default for newly created Clock and Groove modules is `host`.** Existing documents are
   not migrated. This is a product default and the owner may overrule it; it is one constant.
9. **Studio gets one transport control:** tempo field and play/stop in the status bar, bound to
   `setTransport`; the status bar shows the host tempo. The Clock-derived display goes.

## Stages
| Stage | What | Class | Merge |
|---|---|---|---|
| TR1 | Engine packet path (3), sidecar command, status field, document setting, protocol spec, tests | C | lead after contract-review |
| TR2 | Clock `sync`, Groove `tempo_source`, module tests, patch designer guide | B (module DSP) | lead |
| TR3 | Studio transport control, `FakeEngine`, Playwright; default of decision 8 | B | lead |

## Invariants and evidence
- **K1** With no `settings.transport` and no `setTransport`, output is bit-identical: golden 24
  identical on three platforms on every stage.
- **K2** Nothing but the render thread writes bpm, playing or beat on a prepared engine.
  `Engine::transport` on a prepared engine allocates nothing and takes no lock.
- **K3** No existing parameter, port or module ID changes; Clock's new parameter is appended.
- **K4** A sent `setTransport` is applied at a block boundary within two blocks; a full ring is
  reported as `busy`, never dropped silently.
- Tests: over the protocol on the null sink, set 90 BPM and show a synced LFO and a synced Clock
  at the new rate (the `0004` criterion); stop and show the beat frozen while a held note still
  sounds; locate and show two followers aligned; `applyGraph` keeps the beat.
- T0.13 gains a row: `setTransport` bpm change with the witness tone untouched.

## Open, not blocking
Time signature and loop points exist in `ws2_transport` and stay at 4/4 and off. External MIDI
clock as a tempo source is a later step that feeds the same packet path.

Signed: Fable, 2026-11-16
