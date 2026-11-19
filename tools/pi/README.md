# Pi / owner patch round-trip (OB-a2)

This runner checks **temporary copies** of an owner's native v2 JSON patches with
the production Studio PatchDoc codec and compiled native wirescape_render.
No audio, MIDI or LAN devices are used. The input directory is read-only.

From the repository root, build the device-free renderer and install Studio
dependencies:

```sh
python tools/dev.py build --headless
npm ci --prefix apps/studio
```

Then place copies (not the owner's real files) in a temporary folder and run:

```sh
python tools/patch_roundtrip.py --renderer build/native/wirescape_render --dir /path/to/temporary/patch-copies
```

The --dir mode scans *.json recursively and fails for an empty/missing folder.
For each valid native v2 input it runs Studio load/save/reload and three
production native loads/renders, checking normalized document equality,
deterministic stereo WAV SHA-256 and zero fault metrics. Existing negative
document/render sensitivity controls also run. Invalid documents produce
individual case failures; source SHA-256 values are checked before/after,
including files that fail validation. The JSON file inventory is rechecked.

Manifests, saved documents, audio renders and event scripts live only in a
separate temporary folder, never in the owner input folder. The default JSON
report is bench/results/patch_roundtrip_owner.json. --report is permitted
only for paths under bench/results/. A missing local .gitignore there is
created with *; existing ignore configurations are never overwritten. The
runner verifies git check-ignore before writing the report. Neither owner
files nor this private report should be uploaded to CI or committed.

Exit 0: every discovered file, original negative controls, input hashes
and directory inventory pass. Exit 1: missing/empty directory, invalid file,
unexplained document/audio change, setup failure, or modified input.
Exit 2: invalid CLI arguments or an unsafe/non-ignored report destination.
Inspect cases[].status/reason and input_sha256_before/after for details.
A later owner-only acceptance run on the real private folder is separate.

Without --dir, the existing OB-a1 positive bundled/config-shape cases and
negative controls remain in force:

```sh
python tools/patch_roundtrip.py --renderer build/native/wirescape_render
```
