#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-free ABI2 performance and DSP fact pack.

Build Release first: python tools/dev.py build --headless
Install: python -m pip install -r bench/offline/requirements.txt
Run: python bench/offline/run_all.py --quick
No audio/MIDI device or network service is accessed by this harness.
"""
import argparse
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from metrics import (basic, direct_envelope_metrics, envelope_metrics, filter_metrics,
                     oscillator_metrics, patch_metrics, read_audio, step_metrics)
from sidecar_probe import check_loads

ROOT = Path(__file__).resolve().parents[2]
RATE = 48000
BLOCKS = (64, 128, 256)
MODULE_FIXTURE = ROOT / "tools/foundation/fixtures/known_module_ids.txt"
PATCHES = ROOT / "apps/studio/patches"
COST_HELPER = ROOT / "tools/bench/abi2_cost.py"
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?f?"
PARAM = re.compile(r'(?:ws::param|stepped)\(\s*"([^"]+)"\s*,\s*"[^"]+"\s*,\s*(' +
                   NUMBER + r')\s*,\s*(' + NUMBER + r')\s*,\s*(' + NUMBER + r')')
PORT = re.compile(r'ws::port\(\s*"([^"]+)"\s*,\s*"[^"]+"\s*,\s*(WS2_[A-Z0-9_]+)')


def num(text):
    return float(text.rstrip("fF"))


def modules():
    return [line.strip() for line in MODULE_FIXTURE.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def descriptors():
    result = {}
    for path in sorted((ROOT / "native").rglob("*.h")):
        if path.stat().st_size > 100000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        found = re.search(r'\binfo\s*\{\s*"([^"]+)"\s*,\s*"[^"]+"\s*,\s*(\d+)', text)
        if not found:
            continue
        params = re.search(r'\bparams\s*\{(.*?)\};', text, re.S)
        if not params:
            params = re.search(r'\bparams\s*=\s*\[\]\s*\{(.*?)\};', text, re.S)
        inputs = re.search(r'\binputs\s*\{(.*?)\};', text, re.S)
        outputs = re.search(r'\boutputs\s*\{(.*?)\};', text, re.S)
        result[found.group(1)] = {
            "version": int(found.group(2)), "source": path.relative_to(ROOT).as_posix(),
            "parameters": {m.group(1): {"min": num(m.group(2)), "max": num(m.group(3)),
                                            "initial": num(m.group(4))}
                           for m in PARAM.finditer(params.group(1) if params else "")},
            "inputs": [dict(port=a, type=b) for a, b in
                       PORT.findall(inputs.group(1) if inputs else "")],
            "outputs": [dict(port=a, type=b) for a, b in
                        PORT.findall(outputs.group(1) if outputs else "")]
        }
    return result


def cpu_model():
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith(("model name", "hardware", "processor")) and ":" in line:
                value = line.partition(":")[2].strip()
                if value and not value.isdigit():
                    return value
    except OSError:
        pass
    return platform.processor() or platform.machine()


def provenance(build):
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                         text=True, timeout=10, check=False).stdout.strip()
    cache = build / "CMakeCache.txt"
    compiler = None
    config = None
    if cache.exists():
        for line in cache.read_text(errors="replace").splitlines():
            if line.startswith("CMAKE_CXX_COMPILER:FILEPATH="):
                compiler = Path(line.partition("=")[2]).name
            if line.startswith("CMAKE_BUILD_TYPE:STRING="):
                config = line.partition("=")[2]
    return {
        "commit": sha or None, "date_et": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine": {"cpu": cpu_model(), "architecture": platform.machine(),
                    "os": platform.platform(), "compiler": compiler or "unavailable",
                    "configuration": config or "multi-config/unavailable"},
        "sample_rate_hz": RATE, "block_sizes_frames": list(BLOCKS),
        "method": "python bench/offline/run_all.py"
    }


def executable(build, name):
    filename = name + (".exe" if os.name == "nt" else "")
    for candidate in (build / filename, build / "Release" / filename,
                      build / "native" / filename, build / "native" / "Release" / filename):
        if candidate.is_file():
            return candidate.resolve()
    return None


def call(command, timeout=120):
    try:
        completed = subprocess.run([str(s) for s in command], cwd=ROOT,
                                   capture_output=True, text=True, timeout=timeout, check=False,
                                   stdin=subprocess.DEVNULL)
        return {"exit_code": completed.returncode, "stdout": completed.stdout[-1800:],
                "stderr": completed.stderr[-1200:]}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"exit_code": None, "error": str(e)[:500]}


def parsed_command(command, prefix=None, timeout=120):
    result = call(command, timeout)
    raw = result.get("stdout", "")
    try:
        if result["exit_code"] != 0:
            detail = " ".join((result.get("stderr") or result.get("error") or "").split())
            raise ValueError("exit code %s: %s" % (result.get("exit_code"),
                                                   detail[:360] or "no stderr supplied"))
        if prefix:
            lines = [line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)]
            if len(lines) != 1:
                raise ValueError("expected one prefixed JSON line")
            return dict(status="measured", **json.loads(lines[0]))
        return dict(status="measured", **json.loads(raw))
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        diagnostic = " ".join((result.get("stderr") or result.get("error") or "").split())[:360]
        return {"status": "unavailable", "exit_code": result.get("exit_code"),
                "reason": str(e), "stderr": result.get("stderr", result.get("error", "")),
                "error_text": diagnostic or str(e)}


def markdown_rows(rows):
    def flatten(row):
        out = {}
        for k, v in row.items():
            if isinstance(v, dict):
                for n, nested in v.items():
                    if isinstance(nested, (int, float)) or nested is None:
                        out[k + "_" + n] = nested
            elif k in ("module", "patch", "parameter", "metric", "model", "status",
                       "reason", "stderr", "error_text", "sidecar_result", "sidecar_code",
                       "sidecar_message", "sidecar_error", "input_mode") or isinstance(v, (int, float)) or v is None:
                out[k] = v
        return out
    observed = [flatten(x) for x in rows]
    available = list(dict.fromkeys(k for record in observed for k in record))
    identities = ("module", "patch", "parameter", "metric", "model", "status", "reason")
    columns = ([key for key in identities if key in available] +
               [key for key in available if key not in identities])[:24]
    if not columns:
        columns = ["sample_count"]
        observed = [{"sample_count": 0}]
    def cell(value):
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.8g}" if math.isfinite(value) else "—"
        return str(value).replace("|", "\\|").replace("\r", "").replace("\n", "\\n")
    lines = ["| Index | " + " | ".join(columns) + " |",
             "|---:|" + "|".join("---:" for _ in columns) + "|"]
    for index, values in enumerate(observed, 1):
        lines.append("| " + str(index) + " | " +
                     " | ".join(cell(values.get(name)) for name in columns) + " |")
    return lines


def save(out, section, name, meta, rows, notes=None):
    folder = out / section
    folder.mkdir(parents=True, exist_ok=True)
    document = {"SPDX-License-Identifier": "GPL-3.0-only", "provenance": meta, "section": name, "rows": rows}
    if notes:
        document["method_details"] = notes
    (folder / (name + ".json")).write_text(json.dumps(document, indent=2, sort_keys=True,
                                                       allow_nan=False) + "\n", encoding="utf-8")
    machine = meta["machine"]
    lines = ["<!-- SPDX-License-Identifier: GPL-3.0-only -->", f"# {name}", "",
             f"Commit: {meta['commit']}; date ET: {meta['date_et']}",
             f"Machine: {machine['cpu']}; OS: {machine['os']}; compiler: {machine['compiler']}; configuration: {machine['configuration']}",
             f"Sample rate: {RATE} Hz; block frames: {', '.join(map(str, BLOCKS))}",
             f"Row count: {len(rows)}", ""]
    lines.extend(markdown_rows(rows))
    (folder / (name + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{section}/{name}: {len(rows)} rows", flush=True)


def patch_doc(name, mods, connections, output_node, output_port, seed=7):
    return {"format": "wirescape.native.patch", "version": 2, "name": name,
            "settings": {"seed": seed},
            "modules": mods, "connections": connections,
            "outputs": [{"module": output_node, "port": output_port, "bus_channel": c}
                        for c in (0, 1)]}


def mod(node, module, version=2, parameters=None):
    return {"id": node, "module": module, "version": version,
            "parameters": parameters or {}}


def edge(a, port_a, b, port_b):
    return {"kind": "signal", "from": {"module": a, "port": port_a},
            "to": {"module": b, "port": port_b}}


def direct_source(module, version, parameters, output_port, input_port=None,
                  input_module="essentials.vco", input_output="audio"):
    parts = [mod(1, module, version, parameters), mod(2, "essentials.output")]
    edges = [edge(1, output_port, 2, "audio")]
    if input_port:
        parts.append(mod(3, input_module))
        edges.insert(0, edge(3, input_output, 1, input_port))
    return patch_doc(module, parts, edges, 2, "audio")


def wav_run(renderer, patch, events, seconds, block, folder, seed=7):
    patch_file, script_file, wav_file = (folder / n for n in ("patch.json", "script.json", "audio.wav"))
    patch_file.write_text(json.dumps(patch), encoding="utf-8")
    script_file.write_text(json.dumps(sorted(events, key=lambda x: x["frame"])), encoding="utf-8")
    result = call([renderer, "--patch", patch_file, "--script", script_file,
                   "--out", wav_file, "--rate", RATE, "--block", block,
                   "--seconds", seconds, "--seed", seed], timeout=90)
    try:
        if result["exit_code"] != 0:
            raise ValueError("renderer exit nonzero")
        metrics = [json.loads(line[len("render_metrics "):])
                   for line in result.get("stdout", "").splitlines()
                   if line.startswith("render_metrics ")]
        if len(metrics) != 1:
            raise ValueError("renderer metrics missing")
        audio = read_audio(wav_file)
        return audio, {"status": "measured", "counters": metrics[0]}
    except (ValueError, OSError, TypeError, KeyError) as e:
        return None, {"status": "unavailable", "reason": str(e),
                      "stderr": result.get("stderr", result.get("error", ""))}


def run_wav(renderer, patch, events, seconds, block=128, seed=7):
    with tempfile.TemporaryDirectory(prefix="ws-offline-") as folder:
        return wav_run(renderer, patch, events, seconds, block, Path(folder), seed)


def build_module_patch(module_id, descriptor, override=None):
    if not descriptor:
        return None, "descriptor not found"
    outputs = descriptor["outputs"]
    audio = next((p["port"] for p in outputs if p["type"] == "WS2_AUDIO"), None)
    cv = next((p["port"] for p in outputs if p["type"] in ("WS2_CV_UNI", "WS2_CV_BI", "WS2_PITCH", "WS2_GATE")), None)
    if audio:
        input_port = next((p["port"] for p in descriptor["inputs"]
                           if p["type"] == "WS2_AUDIO"), None)
        return direct_source(module_id, descriptor["version"], override or {}, audio,
                             input_port), None
    if cv:
        return direct_source(module_id, descriptor["version"], override or {}, cv), None
    return None, "no audio or CV output available for renderer"


def scripted_keyboard_patch(document):
    """Produce a *derived* clocked-note fixture; never overwrite the bundled patch.

    The native paced soak accepts a patch, but has no event-script argument.
    StepSequencer has the same pitch/gate/velocity/notes output port names as
    host.keyboard. A Clock drives its note events entirely inside the engine.
    The input_mode field distinguishes these measurements from source patches.
    """
    keyboard = [m for m in document.get("modules", [])
                if m.get("module") == "host.keyboard"]
    if not keyboard:
        return None, 0
    derived = json.loads(json.dumps(document))
    next_id = max(m["id"] for m in derived["modules"])
    for node in derived["modules"]:
        if node.get("module") != "host.keyboard":
            continue
        node["module"] = "example.step_sequencer"
        node["version"] = 2
        node["parameters"] = {"run": 1, "length": 8}
        node.pop("config", None)
        next_id += 1
        derived["modules"].append({
            "id": next_id, "module": "essentials.clock", "version": 2,
            "parameters": {"bpm": 120, "ticks_per_beat": 1, "duty": 0.5, "run": 1}})
        derived["connections"].append({
            "kind": "signal",
            "from": {"module": next_id, "port": "clock"},
            "to": {"module": node["id"], "port": "clock"}})
    return derived, len(keyboard)


def soak_seconds_for(quick, requested):
    seconds = requested if requested is not None else (.05 if quick else 30.)
    if not math.isfinite(seconds) or seconds < .001 or seconds > 3600:
        raise ValueError("soak seconds must be finite and within .001..3600")
    return seconds


def soak_patches(soak, patches, meta, out, seconds, engine):
    """Paced document measurements, preserving raw vs substituted input provenance."""
    rows = []
    with tempfile.TemporaryDirectory(prefix="ws-soak-sources-") as temporary:
        folder = Path(temporary)
        for path in patches:
            try:
                original = json.loads(path.read_text(encoding="utf-8"))
                derived, keyboard_count = scripted_keyboard_patch(original)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                for block in BLOCKS:
                    rows.append({"patch": path.name, "block_frames": block, "seconds": seconds,
                                 "status": "unavailable",
                                 "reason": "fixture parse: %s: %s" % (type(exc).__name__, exc)})
                continue
            derived_path = folder / path.name
            if derived is not None:
                derived_path.write_text(json.dumps(derived), encoding="utf-8")
            for block in BLOCKS:
                def measure(patch_path, duration):
                    return parsed_command(
                        [soak, "--patch", patch_path, "--rate", RATE, "--block", block,
                         "--seconds", duration],
                        timeout=max(45, math.ceil(duration) + 40))
                input_mode = "original"
                source_probe = None
                scripted_probe = None
                chosen = path
                if derived is not None:
                    source_probe = measure(path, .05)
                    if source_probe["status"] != "measured":
                        scripted_probe = measure(derived_path, .05)
                        if scripted_probe["status"] == "measured":
                            input_mode = "clocked_step_sequencer_for_host_keyboard"
                            chosen = derived_path
                result = measure(chosen, seconds)
                row = {"patch": path.name, "block_frames": block, "seconds": seconds,
                       "input_mode": input_mode}
                if input_mode != "original":
                    row.update(source_patch_status=source_probe["status"],
                               source_patch_exit_code=source_probe.get("exit_code"),
                               source_patch_error=source_probe.get("error_text"),
                               keyboard_sources_replaced=keyboard_count,
                               derived_modules_added=keyboard_count,
                               scripted_source="essentials.clock -> example.step_sequencer")
                if source_probe and source_probe["status"] != "measured" and input_mode == "original":
                    row["source_patch_error"] = source_probe.get("error_text")
                    if scripted_probe and scripted_probe["status"] != "measured":
                        row["scripted_source_error"] = scripted_probe.get("error_text")
                row.update(result)
                if row["status"] == "unavailable":
                    row["error_text"] = result.get("error_text", result.get("reason", ""))
                    if scripted_probe and scripted_probe["status"] != "measured":
                        row["reason"] += "; scripted keyboard source also failed: " + (
                            scripted_probe.get("error_text") or scripted_probe.get("reason", ""))
                rows.append(row)
    failures = [dict(patch=row["patch"], block_frames=row["block_frames"],
                     status=row["status"], reason=row.get("reason"),
                     stderr=row.get("stderr"), exit_code=row.get("exit_code"),
                     error_text=row.get("error_text") or row.get("reason") or "",
                     source_patch_error=row.get("source_patch_error"),
                     scripted_source_error=row.get("scripted_source_error"))
                for row in rows if row["status"] != "measured"]
    if failures:
        failures = check_loads(engine, failures, PATCHES, RATE)
    save(out, "perf", "soak_failures", meta, failures,
         {"source": "wirescape_soak", "sidecar": "wirescape-engine --null-audio",
          "note": "A derived clocked source is reported in input_mode, not as the original patch."})
    save(out, "perf", "patch_soak", meta, rows,
         {"mode": "paced device-free document soak", "warmup_blocks": 256,
          "soak_seconds": seconds, "scripted_keyboard": "Clock and StepSequencer substitution",
          "note": "Soak reports max, median and percentiles; arithmetic mean unavailable."})
    return len(patches)


def cpu_sections(probes, mods, meta, out, quick, soak_seconds=None):
    probe, bench, cost, soak = probes["abi2_module_cpu_probe"], probes["abi2_benchmark"], probes["abi2_cost_probe"], probes["wirescape_soak"]
    rows = []
    for ident in mods:
        for block in BLOCKS:
            for channels in (1, 8):
                entry = {"module": ident, "block_frames": block, "channels": channels}
                args = [probe, "--module", ident, "--rate", RATE, "--block", block,
                        "--channels", channels, "--instances", 1, "--seconds", .1 if quick else 2]
                result = parsed_command(args, prefix="module_cpu_probe ", timeout=45)
                if ident == "essentials.chord" and result["status"] != "measured":
                    # The standalone probe passes a zero-byte ws2_config. Chord
                    # requires the document adapter's four-byte instance tag.
                    result["reason"] += (
                        "; direct probe passes zero config bytes; Chord needs four"
                        " (native/modules2/chord/dsp.h:54-56,"
                        " native/document/runtime_module_config.h:35-38)")
                    result["input_mode"] = "direct_descriptor_without_chord_instance_tag"
                ns = result.get("render_ns", {}).get("p99") if result.get("status") == "measured" else None
                entry.update(result)
                entry["p99_ns_per_sample"] = ns / (block * channels) if ns is not None else None
                rows.append(entry)
    failures = [dict(module=row["module"], block_frames=row["block_frames"],
                     channels=row["channels"], sample_rate_hz=RATE,
                     instances=1, seconds=.1 if quick else 2,
                     input_mode=row.get("input_mode", "normal"), status=row["status"],
                     reason=row.get("reason"), stderr=row.get("stderr"),
                     exit_code=row.get("exit_code"))
                for row in rows if row["status"] != "measured"]
    save(out, "perf", "probe_failures", meta, failures,
         {"source": "module_cpu_probe", "scope": "nonzero or invalid JSON responses"})
    denorm = []
    for ident in mods:
        for block in BLOCKS:
            args = [probe, "--module", ident, "--rate", RATE, "--block", block,
                    "--channels", 1, "--instances", 1, "--seconds", .1 if quick else 2]
            normal = parsed_command(args + ["--input-mode", "normal"],
                                    prefix="module_cpu_probe ", timeout=45)
            tiny = parsed_command(args + ["--input-mode", "denormal"],
                                  prefix="module_cpu_probe ", timeout=45)
            row = {"module": ident, "block_frames": block,
                   "input_value": 1e-30, "normal": normal, "denormal": tiny}
            if normal.get("status") == "measured" and tiny.get("status") == "measured":
                base = normal["render_ns"]["p99"]
                test = tiny["render_ns"]["p99"]
                row.update(status="measured", normal_p99_ns=base,
                           denormal_p99_ns=test, p99_ratio=test / base if base else None)
            else:
                row["status"] = "unavailable"
                row["reason"] = "normal or denormal probe failed"
                if ident == "essentials.chord":
                    row["reason"] += (
                        "; Chord requires four config bytes, but the direct probe"
                        " passes zero (native/modules2/chord/dsp.h:54-56)")
            denorm.append(row)
    save(out, "perf", "denormal_spikes", meta, denorm,
         {"input": "1e-30 constant on first and second signal inputs",
          "note": "1e-30f is normal binary32, not a subnormal input",
          "metric": "tiny-input/normal-input p99 render duration ratio"})
    save(out, "perf", "module_cpu", meta, rows,
         {"input": "110-Hz saw first input; seeded noise second input; probe-defined inputs"})
    engine_rows = []
    with tempfile.TemporaryDirectory(prefix="ws-engine-bench-") as temp:
        for block in BLOCKS:
            artifact = Path(temp) / ("benchmark_%d.json" % block)
            result = call([bench, probes["modules_dir"], artifact,
                           "--block", block], timeout=180)
            if result["exit_code"] == 0 and artifact.is_file():
                try:
                    data = json.loads(artifact.read_text())
                    if data["frames"] != block:
                        raise ValueError("benchmark frame count does not match request")
                    engine_rows.extend(dict(status="measured", block_frames=block, **row)
                                       for row in data["rows"])
                except (ValueError, KeyError, TypeError) as e:
                    engine_rows.append({"status": "unavailable", "block_frames": block,
                                        "reason": str(e)})
            else:
                engine_rows.append({"status": "unavailable", "block_frames": block,
                                    "stderr": result.get("stderr", ""),
                                    "exit_code": result.get("exit_code")})
    save(out, "perf", "engine_cpu", meta, engine_rows,
         {"block_frames": list(BLOCKS), "rate_hz": RATE,
          "method": "one benchmark process per block size"})
    if shutil.which("valgrind") and cost:
        with tempfile.TemporaryDirectory(prefix="ws-callgrind-") as temp:
            artifact = Path(temp) / "ir.json"
            result = call([sys.executable, COST_HELPER, "--build-dir", probes["build_dir"],
                           "--modules-dir", probes["modules_dir"],
                           "--blocks", *(["5", "15"] if quick else ["50", "150"]),
                           "--output", artifact], timeout=900)
            if result["exit_code"] == 0 and artifact.is_file():
                try:
                    cost_rows = [dict(status="measured", **r) for r in
                                 json.loads(artifact.read_text())["rows"]]
                except (ValueError, KeyError) as e:
                    cost_rows = [{"status": "unavailable", "reason": str(e)}]
            else:
                cost_rows = [{"status": "unavailable", "stderr": result.get("stderr", ""),
                              "exit_code": result.get("exit_code")}]
    else:
        cost_rows = [{"status": "unavailable", "reason": "valgrind or cost probe unavailable"}]
    save(out, "perf", "instruction_cost", meta, cost_rows,
         {"unit": "Ir per 256-frame block", "method": "subtract 2 callgrind run summaries"})
    return soak_patches(soak, sorted(PATCHES.glob("*.json")), meta, out,
                        soak_seconds_for(quick, soak_seconds), probes["wirescape-engine"])


def oscillator_sections(renderer, desc, meta, out, quick):
    rows = []
    seconds = .5 if quick else 2
    for ident, models in (("essentials.vco", [None]),
                          ("ports.macro_oscillator", list(range(24)))):
        d = desc.get(ident)
        if not d:
            rows.append({"module": ident, "status": "unavailable", "reason": "descriptor missing"})
            continue
        output = "audio" if models == [None] else "main"
        for model in models:
            for hz in (110, 440, 1760, 5000):
                params = {"frequency": hz} if model is None else {
                    "model": model, "coarse": 12 * math.log2(hz / 261.6255653005986)}
                entry = {"module": ident, "model": model, "target_hz": hz}
                if model is not None:
                    # Plaits coarse is +/-48 semitones. Supply the residual via
                    # a bounded constant CV connected to the pitch input.
                    coarse = float(np.clip(params["coarse"], -48, 48))
                    residual_cv = (params["coarse"] - coarse) / 12
                    params["coarse"] = coarse
                    patch = direct_source(ident, d["version"], params, output)
                    if abs(residual_cv) > 1e-9:
                        patch["modules"].append(mod(3, "essentials.scale_offset", parameters={
                            "scale": 0, "offset": residual_cv}))
                        patch["connections"].append(edge(3, "control", 1, "pitch"))
                else:
                    patch = direct_source(ident, d["version"], params, output)
                audio, result = run_wav(renderer, patch, [], seconds)
                if audio is not None:
                    result.update(oscillator_metrics(audio, hz))
                rows.append(dict(entry, **result))
    save(out, "dsp", "oscillators", meta, rows,
         {"alias_floor_unit": "dBFS non-harmonic FFT energy", "thd_unit": "dB",
          "pitch_unit": "cents", "vco_waveform": "sine",
          "macro_models": "0..23", "FFT": "Hann window, harmonic exclusion +/-4 bins"})


def filter_sections(renderer, desc, meta, out, quick):
    rows = []
    seconds = .5 if quick else 2
    for ident, port in (("essentials.vcf", "low12"), ("essentials.ladder", "audio")):
        d = desc.get(ident)
        if not d:
            rows.append({"module": ident, "status": "unavailable"})
            continue
        for cutoff in (100, 1000, 5000):
            for resonance in (0, .5, .9):
                feed = mod(1, "essentials.noise", parameters={"level": .2})
                outmod = mod(3, "essentials.output")
                dry = patch_doc("filter reference", [feed, outmod],
                                [edge(1, "audio", 3, "audio")], 3, "audio")
                wet = patch_doc(ident, [feed, mod(2, ident, d["version"],
                                                  {"cutoff": cutoff, "resonance": resonance}), outmod],
                                [edge(1, "audio", 2, "audio"), edge(2, port, 3, "audio")],
                                3, "audio")
                reference, ref_status = run_wav(renderer, dry, [], seconds)
                filtered, fil_status = run_wav(renderer, wet, [], seconds)
                record = {"module": ident, "cutoff_hz": cutoff, "resonance": resonance}
                if reference is not None and filtered is not None:
                    record.update(status="measured", **filter_metrics(reference, filtered))
                else:
                    record.update(status="unavailable", reference=ref_status, filtered=fil_status)
                rows.append(record)
        rows.append({"module": ident, "status": "unavailable", "metric": "self_oscillation_hz",
                     "reason": "no automated unexcited self-oscillation setup"})
    save(out, "dsp", "filters", meta, rows,
         {"method": "Welch PSD ratio; identical deterministic noise input and seed",
          "spectral_nperseg": 4096})


def module_sections(renderer, desc, all_modules, meta, out, quick):
    module_rows, param_rows = [], []
    seconds = .5 if quick else 1.5
    for ident in all_modules:
        descriptor = desc.get(ident)
        patch, reason = build_module_patch(ident, descriptor)
        base_row = {"module": ident}
        if patch is None:
            module_rows.append(dict(base_row, status="unavailable", reason=reason))
        else:
            audio, status = run_wav(renderer, patch, [], seconds)
            if audio is not None:
                module_rows.append(dict(base_row, status="measured", **basic(audio),
                                        counters=status["counters"]))
            else:
                module_rows.append(dict(base_row, **status))
        params = descriptor["parameters"] if descriptor else {}
        if not params:
            param_rows.append(dict(base_row, status="not_applicable", reason="no parameter metadata"))
        else:
            key, bounds = next(iter(params.items()))
            changed, why = build_module_patch(ident, descriptor, {key: bounds["min"]})
            entry = dict(base_row, parameter=key, min=bounds["min"], max=bounds["max"])
            if changed is None:
                param_rows.append(dict(entry, status="unavailable", reason=why))
            else:
                frame = round(seconds * RATE / 2)
                audio, status = run_wav(renderer, changed, [
                    {"frame": frame, "type": "setParam", "node": 1,
                     "parameter": key, "value": bounds["max"]}], seconds)
                param_rows.append(dict(entry, status="measured",
                                       **step_metrics(audio, frame)) if audio is not None
                                  else dict(entry, **status))
    save(out, "dsp", "module_outputs", meta, module_rows,
         {"measure": "direct output bus; VCO input feed only for audio-input modules"})
    save(out, "dsp", "parameter_steps", meta, param_rows,
         {"step": "first parameter min to max halfway through render",
          "highpass": "2nd order Butterworth 2kHz"})


def envelope_sections(renderer, meta, out, quick):
    seconds = 1 if quick else 2
    attack, release = .05, .1
    on, off = round(RATE * .1), round(RATE * .7)
    patch = patch_doc("envelope", [
        mod(1, "essentials.vco", parameters={"frequency": 440}),
        mod(2, "essentials.adsr", parameters={"attack": attack, "decay": .0001,
                                            "sustain": 1, "release": release}),
        mod(3, "essentials.vca", parameters={"gain": 1}),
        mod(4, "essentials.output")],
        [edge(1, "audio", 3, "audio"), edge(2, "envelope", 3, "gain_cv"),
         edge(3, "audio", 4, "audio")], 4, "audio")
    events = [{"frame": on, "type": "noteOn", "node": 2, "key": 60},
              {"frame": off, "type": "noteOff", "node": 2, "key": 60}]
    audio, status = run_wav(renderer, patch, events, seconds)
    rows = [dict(module="essentials.adsr", status="measured",
                 **envelope_metrics(audio, on, off, attack, release))] if audio is not None else [
                     dict(module="essentials.adsr", **status)]
    rise, fall = .05, .1
    function_patch = patch_doc("function envelope", [
        mod(1, "essentials.clock", parameters={"bpm": 60, "ticks_per_beat": 1,
                                              "duty": .5, "run": 1}),
        mod(2, "essentials.function_envelope", parameters={
            "rise": rise, "fall": fall, "curve": 0}),
        mod(3, "essentials.output")],
        [edge(1, "clock", 2, "gate"), edge(2, "envelope", 3, "audio")],
        3, "audio")
    function_audio, function_status = run_wav(renderer, function_patch, [], seconds)
    function_row = {"module": "essentials.function_envelope"}
    if function_audio is not None:
        function_row.update(status="measured", **direct_envelope_metrics(
            function_audio, 0, round(RATE * .5), rise, fall))
    else:
        function_row.update(function_status)
    rows.append(function_row)
    save(out, "dsp", "envelopes", meta, rows,
         {"ADSR_method": "analytic-signal amplitude smoothed over 128 samples",
          "function_method": "direct CV; 60 BPM clock drives 0.5-second gate",
          "target_attack_s": attack, "target_release_s": release})


def bundled_section(renderer, meta, out, quick):
    rows = []
    seconds = 1 if quick else 10
    for path in sorted(PATCHES.glob("*.json")):
        try:
            patch = json.loads(path.read_text())
            keyboard = [m["id"] for m in patch.get("modules", [])
                        if m.get("module") == "host.keyboard"]
            events = []
            for node in keyboard:
                events.extend([{"frame": 0, "type": "noteOn", "node": node, "key": 60},
                               {"frame": round(RATE * seconds / 2), "type": "noteOff",
                                "node": node, "key": 60}])
            seed = patch.get("settings", {}).get("seed", 42)
            audio, status = run_wav(renderer, patch, events, seconds, seed=seed)
            row = {"patch": path.name, "seconds": seconds}
            row.update(dict(status="measured", **patch_metrics(audio),
                            counters=status["counters"]) if audio is not None else status)
            rows.append(row)
        except (ValueError, OSError, KeyError, TypeError) as e:
            rows.append({"patch": path.name, "status": "unavailable", "reason": str(e)})
    save(out, "dsp", "bundled_patches", meta, rows,
         {"clicks": "sample difference > median + 10 median absolute deviations",
          "silence": "contiguous 20ms windows with RMS under 1e-5 FS"})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="short measurement windows")
    ap.add_argument("--soak-seconds", type=float, default=None,
                    help="duration per patch and block; default 30 s (0.05 s in --quick)")
    ap.add_argument("--build-dir", type=Path, default=ROOT / "build/native")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "facts")
    args = ap.parse_args(argv)
    try:
        soak_seconds_for(args.quick, args.soak_seconds)
    except ValueError as exc:
        ap.error(str(exc))
    build = args.build_dir.resolve()
    required = ("abi2_module_cpu_probe", "abi2_benchmark", "wirescape_soak",
                "wirescape_render", "wirescape-engine")
    binaries = {name: executable(build, name) for name in required + ("abi2_cost_probe",)}
    missing = [name for name in required if binaries[name] is None]
    if missing:
        ap.error("Release headless binaries not found: " + ", ".join(missing) +
                 "; run python tools/dev.py build --headless")
    meta = provenance(build)
    mods = modules()
    desc = descriptors()
    out = args.out_dir.resolve()
    probes = dict(binaries)
    probes["build_dir"] = build
    probes["modules_dir"] = binaries["abi2_benchmark"].parent
    cpu_sections(probes, mods, meta, out, args.quick, args.soak_seconds)
    oscillator_sections(binaries["wirescape_render"], desc, meta, out, args.quick)
    filter_sections(binaries["wirescape_render"], desc, meta, out, args.quick)
    module_sections(binaries["wirescape_render"], desc, mods, meta, out, args.quick)
    envelope_sections(binaries["wirescape_render"], meta, out, args.quick)
    bundled_section(binaries["wirescape_render"], meta, out, args.quick)
    print("Device-free fact pack complete: " + str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
