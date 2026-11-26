<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OSC presets (A92, OB-h5)

OSC presets are reusable editor mappings, not patches. Choose a built-in or load a JSON file,
then use **Save and apply** to commit ordinary module config through the existing engine
acceptance path. Cancel leaves the patch unchanged. **Save preset…** exports the editor
draft without committing it to the patch.

## Script (/ws/…)

The OSC In built-in maps these eight rows, leaving the current UDP port and LAN request
unchanged. New OSC In modules still default to Pico knobs.

| Row | Pattern | Kind | Mapping |
|---|---|---|---|
| 1 | `/ws/pitch/*` | CV | MIDI note 0–127, 1 V/oct, MIDI 60 = 0; output (note − 60)/12; no smoothing |
| 2 | `/ws/trig/*` | trigger | a message fires |
| 3 | `/ws/gate/*` | gate | 0/1; stale zero after 2000 ms |
| 4 | `/ws/vel/*` | CV | 0–1 |
| 5–8 | `/ws/cv/1` … `/ws/cv/4` | CV | 0–1, 5 ms smoothing |

Send concrete OSC addresses, e.g. `/ws/pitch/1` with numeric argument 60. OSC In already
maps numeric final wildcard segments to densely sorted poly channels (up to 16); it does not
allocate MIDI voices. Send initial values for every intended index before playing to stabilize
channel ordering. See [OSC In](../../modules/osc_in/README.md). The configured UDP port and
network permission still govern routing.

## Version 1 file envelope

```json
{
  "format": "wirescape.osc.preset",
  "version": 1,
  "module": "osc.in",
  "name": "My script",
  "config": {
    "port": 9000,
    "rows": []
  }
}
```

The example shows the envelope only: an actual file must have exactly eight fully specified
rows. Names are 1–120 characters, with no control characters; the UTF-8 JSON limit is 256 KiB.
`module` must be `osc.in` or `osc.out`; the wrong module or unsupported version is refused.
Config contains only the following:
- OSC In: `port` (1024–65535), `rows` with `pattern`, `argument`, `kind`, `input_min`,
  `input_max`, `output_min`, `output_max`, `smoothing_ms`, `timeout_ms`, `stale`, optional `enabled`.
- OSC Out: `port` (1–65535), `rate_hz` (1–500), `rows` with `address`, `kind`,
  `deadband`, optional `enabled`, and `notes` with `address` and optional `enabled`.
  Rows default enabled; notes default disabled. Existing module range and address rules apply.

Export uses explicit field allowlists. Import ignores `lan`, `host`, and other fields outside
the preset schema; it never changes a patch's network permission or destination. The
file's port is applied. No patch-format version changes. Python scripts can read the JSON
and extract the patterns/addresses and argument indexes without changing Wirescape.

## Storage

Desktop Save/Load uses file dialogs, initially in `<userData>/presets/osc/`. The editor
lists matching module presets from that directory as buttons and provides **Open presets
folder**. Selected files can also be elsewhere. The file-only IPC accepts leaf names only
for library reads and never supplies filesystem paths to the renderer. It refuses oversized
and symlinked files and non-preset overwrite targets. The web editor downloads/uploads JSON
without desktop file access.
