# SPDX-License-Identifier: GPL-3.0-only
"""Generative patch driver: Euclidean drums, a random-walk melody, a Markov chord pad
and two slow CVs, sent as OSC to a Wirescape OSC In module (stdlib only, no installs).

Addresses use the planned "Script (/ws/...)" preset (proposal 0022, OB-h5):
  /ws/pitch/<voice>  MIDI note number 0-127 (cv row maps it to 1 V/oct, C4 = 0)
  /ws/gate/<voice>   1 / 0
  /ws/vel/<voice>    0-1
  /ws/trig/<n>       message alone fires a trigger
  /ws/cv/1 ... 4     0-1
A wildcard row with a numeric last segment (/ws/pitch/*) becomes poly channels, so voice
<n> is channel <n> on that row. Pair pitch/<n> with gate/<n> for the same voice.
"""
import math, random, socket, struct, time

HOST, PORT = "127.0.0.1", 9000
BPM, STEPS = 112, 16                     # 16th-note grid
SCALE = [0, 2, 3, 5, 7, 8, 10]           # natural minor
ROOT = 57                                # A3
MELODY, PAD = 1, (2, 3, 4)               # voice numbers

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def _pad(b: bytes) -> bytes:
    return b + b"\0" * (4 - len(b) % 4)

def send(address: str, *values: float) -> None:
    tags = "," + "f" * len(values)
    packet = _pad(address.encode()) + _pad(tags.encode())
    packet += b"".join(struct.pack(">f", float(v)) for v in values)
    sock.sendto(packet, (HOST, PORT))

def euclid(hits: int, steps: int, rotate: int = 0) -> list[bool]:
    return [((i + rotate) * hits) % steps < hits for i in range(steps)]

KICK, HAT = euclid(5, STEPS), euclid(7, STEPS, rotate=2)
CHORDS = {0: [3, 5], 3: [5, 0], 5: [0, 3, 4], 4: [0]}  # scale degree -> next degrees

def note(degree: int, octave: int = 0) -> int:
    return ROOT + 12 * (octave + degree // len(SCALE)) + SCALE[degree % len(SCALE)]

def voice_on(v: int, n: int, vel: float) -> None:
    send(f"/ws/pitch/{v}", n)            # pitch first, so the gate starts at the right note
    send(f"/ws/vel/{v}", vel)
    send(f"/ws/gate/{v}", 1)

def voice_off(v: int) -> None:
    send(f"/ws/gate/{v}", 0)

def init() -> None:
    # Send every channel once, in index order, so poly channel numbers stay stable.
    for v in (MELODY, *PAD):
        send(f"/ws/pitch/{v}", ROOT); send(f"/ws/vel/{v}", 0); send(f"/ws/gate/{v}", 0)
    for c in (1, 2, 3, 4):
        send(f"/ws/cv/{c}", 0.5)

def run(bars: int | None = None) -> None:
    init()
    step_s = 60 / BPM / 4
    start = time.perf_counter()
    walk, chord_root, cv_walk, step = 7, 0, 0.5, 0
    while bars is None or step < bars * STEPS:
        s = step % STEPS
        if KICK[s]: send("/ws/trig/1")
        if HAT[s] and random.random() < 0.85: send("/ws/trig/2")

        if s % 2 == 0:                                   # melody on 8ths
            voice_off(MELODY)
            if random.random() < 0.75:                   # 25 % rests
                walk = max(0, min(14, walk + random.choice([-2, -1, -1, 1, 1, 2])))
                voice_on(MELODY, note(walk), 0.9 if s % 8 == 0 else 0.6)

        if s == 0:                                       # new chord each bar (Markov)
            chord_root = random.choice(CHORDS[chord_root])
            for v, offset in zip(PAD, (0, 2, 4)):
                voice_on(v, note(chord_root + offset, -1), 0.5)
        elif s % 4 == 0:                                 # keep held gates alive: the preset
            for v in PAD:                                # gate row times out after 2 s
                send(f"/ws/gate/{v}", 1)

        cv_walk = max(0.0, min(1.0, cv_walk + random.uniform(-0.03, 0.03)))
        send("/ws/cv/1", cv_walk)                                    # e.g. filter cutoff
        send("/ws/cv/2", 0.5 + 0.5 * math.sin(step * 2 * math.pi / 64))  # 4-bar sweep

        step += 1
        time.sleep(max(0.0, start + step * step_s - time.perf_counter()))  # no drift

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        for v in (MELODY, *PAD):
            voice_off(v)                                 # never leave a note hanging
