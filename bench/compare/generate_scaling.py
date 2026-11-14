# SPDX-License-Identifier: GPL-3.0-only
"""Generate native scaling patches; purely file-based, never opens devices."""
import argparse
import json
from pathlib import Path


def scaling_patch(n):
    if not isinstance(n, int) or n < 1:
        raise ValueError("N must be a positive integer")
    # Five per voice, N-1 stereo summing mixers, one shared output.
    if 6 * n > 64:
        raise ValueError(f"N={n} exceeds Wirescape 64-module graph limit (6*N modules)")
    modules = []
    cables = []
    ids = iter(range(1, 65))
    voices = []

    def module(kind, params):
        node = next(ids)
        modules.append({"id": node, "module": kind, "version": 2, "parameters": params})
        return node

    def connect(fr, port, to, target):
        cables.append({"kind": "signal", "from": {"module": fr, "port": port},
                       "to": {"module": to, "port": target}})

    for _ in range(n):
        lfo = module("essentials.lfo", {"rate": .5, "depth": 1})
        vco = module("essentials.vco", {"frequency": 220})
        vcf = module("essentials.vcf", {"cutoff": 1800, "resonance": .15})
        adsr = module("essentials.adsr",
                      {"attack": .015, "decay": .14, "sustain": .65, "release": .2})
        vca = module("essentials.vca", {"gain": .02})
        connect(lfo, "control", adsr, "gate")
        connect(vco, "audio", vcf, "audio")
        connect(vcf, "low24", vca, "audio")
        connect(adsr, "envelope", vca, "gain_cv")
        voices.append(vca)

    while len(voices) > 1:
        next_level = []
        for i in range(0, len(voices), 2):
            if i + 1 >= len(voices):
                next_level.append(voices[i])
                continue
            mixer = module("essentials.mixer", {"level_a": 1, "level_b": 1})
            connect(voices[i], "audio", mixer, "a")
            connect(voices[i + 1], "audio", mixer, "b")
            next_level.append(mixer)
        voices = next_level
    output = module("essentials.output", {})
    connect(voices[0], "audio", output, "audio")
    return {
        "SPDX-License-Identifier": "GPL-3.0-only",
        "name": f"Compare D scaling {n} mono voices",
        "description": f"{n} identical LFO-gated oscillator-filter-envelope voices",
        "format": "wirescape.native.patch", "version": 2,
        "settings": {"sample_rate": 48000, "max_block_frames": 256,
                     "max_channels": 16, "feedback_block": 32,
                     "seed": 147, "timing_mode": "immediate"},
        "modules": modules, "connections": cables,
        "outputs": [{"module": output, "port": "audio", "bus_channel": i} for i in (0, 1)],
        "ui": {}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    patch = scaling_patch(args.n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
