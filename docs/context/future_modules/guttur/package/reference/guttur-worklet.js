// SPDX-License-Identifier: GPL-3.0-only
/* GUTTUR engine core.
   One file, no DOM: runs in the offline harness (Node), in an AudioWorklet, and on the main thread.
   Source: band-limited LF pulses decided per cycle at closure. Throat: tube-derived resonances
   played through a ramped zero-delay SVF cascade. Group: leader, followers, one looseness axis. */
(function (G) {
'use strict';

const VERSION = '1.0.0';
const TAU = Math.PI * 2;
const LN2 = Math.LN2;

/* ------------------------------------------------------------------ utilities */
function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
function lerp(a, b, t) { return a + (b - a) * t; }
function smooth(a, b, x) { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
function dbToGain(db) { return Math.pow(10, db / 20); }
function hash(a, b, c, d) {
  let h = 2166136261 ^ (a | 0);
  h = Math.imul(h ^ (b | 0), 16777619);
  h = Math.imul(h ^ (c | 0), 2246822519);
  h = Math.imul(h ^ (d | 0), 3266489917);
  h ^= h >>> 15; h = Math.imul(h, 2246822519); h ^= h >>> 13; h = Math.imul(h, 3266489917); h ^= h >>> 16;
  return h >>> 0;
}
function h01(a, b, c, d) { return hash(a, b, c, d) / 4294967296; }
function h11(a, b, c, d) { return h01(a, b, c, d) * 2 - 1; }

/* ------------------------------------------------------------------ FFT */
function fft(re, im, inverse) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (inverse ? TAU : -TAU) / len;
    const wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const a = i + k, b = a + len / 2;
        const tr = re[b] * cr - im[b] * ci, ti = re[b] * ci + im[b] * cr;
        re[b] = re[a] - tr; im[b] = im[a] - ti; re[a] += tr; im[a] += ti;
        const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr;
      }
    }
  }
  if (inverse) for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
}

/* ------------------------------------------------------------------ LF glottal pulse tables
   Rd runs from pressed (0.3) to breathy (2.7). Each Rd has 8 levels of detail; level l holds
   harmonics up to 512>>l with a raised-cosine taper over the top 30%, so a table never
   contains a harmonic above the pitch it serves. */
const RD_MIN = 0.3, RD_MAX = 2.7, N_RD = 17, RD_STEP = (RD_MAX - RD_MIN) / (N_RD - 1);
const N_LEV = 8, H0 = 512, S0 = 16384, FLOW_N = 256;

function lfParams(Rd) {
  const Ra = -0.01 + 0.048 * Rd, Rk = 0.224 + 0.118 * Rd;
  const Rg = (Rk / 4) * (0.5 + 1.2 * Rk) / (0.11 * Rd - Ra * (0.5 + 1.2 * Rk));
  const Ta = Ra, Tp = 1 / (2 * Rg), Te = Tp + Tp * Rk;
  const eps = 1 / Ta, shift = Math.exp(-eps * (1 - Te)), Delta = 1 - shift;
  let rhs = (1 / eps) * (shift - 1) + (1 - Te) * shift; rhs /= Delta;
  const lower = -(Te - Tp) / 2 + rhs, upper = -lower;
  const omega = Math.PI / Tp, s = Math.sin(omega * Te);
  const y = -Math.PI * s * upper / (Tp * 2), z = Math.log(y), alpha = z / (Tp / 2 - Te);
  const E0 = -1 / (s * Math.exp(alpha * Te));
  return { Tp, Te, Ta, eps, shift, Delta, omega, alpha, E0 };
}
function lfSample(p, t) {
  if (t > p.Te) return (-Math.exp(-p.eps * (t - p.Te)) + p.shift) / p.Delta;
  return p.E0 * Math.exp(p.alpha * t) * Math.sin(p.omega * t);
}

function buildPulseTables() {
  const M = 32768;
  const sizes = [], hmax = [], base = [];
  let total = 0;
  for (let l = 0; l < N_LEV; l++) {
    hmax.push(Math.max(2, H0 >> l)); sizes.push(l === 0 ? S0 : Math.min(S0, 64 * hmax[l]));
    base.push(total); total += (sizes[l] + 1) * N_RD;
  }
  const data = new Float32Array(total);
  const flow = new Float32Array(N_RD * (FLOW_N + 1));
  const te = new Float32Array(N_RD);
  const NH = 160, harm = new Float32Array(N_RD * NH);
  const re = new Float64Array(M), im = new Float64Array(M);
  for (let r = 0; r < N_RD; r++) {
    const Rd = RD_MIN + r * RD_STEP;
    const p = lfParams(Rd);
    te[r] = p.Te;
    let mean = 0;
    for (let i = 0; i < M; i++) { re[i] = lfSample(p, i / M); im[i] = 0; mean += re[i]; }
    mean /= M;
    // flow (integral) for noise gating, normalised 0..1
    let acc = 0, fmax = 1e-9; const fl = new Float64Array(M);
    for (let i = 0; i < M; i++) { acc += re[i] - mean; fl[i] = acc; }
    let fmin = Infinity; for (let i = 0; i < M; i++) { if (fl[i] < fmin) fmin = fl[i]; }
    for (let i = 0; i < M; i++) { fl[i] -= fmin; if (fl[i] > fmax) fmax = fl[i]; }
    for (let k = 0; k <= FLOW_N; k++) flow[r * (FLOW_N + 1) + k] = fl[Math.min(M - 1, Math.round(k / FLOW_N * (M - 1)))] / fmax;
    fft(re, im, false);
    for (let h = 1; h <= NH; h++) harm[r * NH + h - 1] = Math.hypot(re[h], im[h]) / M * 2;
    for (let l = 0; l < N_LEV; l++) {
      const S = sizes[l], H = hmax[l];
      const xr = new Float64Array(S), xi = new Float64Array(S);
      for (let h = 1; h <= H && h < S / 2; h++) {
        const x = h / H;
        const tap = x < 0.7 ? 1 : 0.5 * (1 + Math.cos(Math.PI * (x - 0.7) / 0.3));
        const g = tap * S / M;
        xr[h] = re[h] * g; xi[h] = im[h] * g;
        xr[S - h] = re[h] * g; xi[S - h] = -im[h] * g;
      }
      fft(xr, xi, true);
      const o = base[l] + r * (S + 1);
      for (let i = 0; i < S; i++) data[o + i] = xr[i];
      data[o + S] = xr[0];
    }
  }
  return { data, flow, te, sizes, hmax, base, harm, NH };
}

/* ------------------------------------------------------------------ tube model
   A 34-section area function from glottis (x=0) to lips (x=1) at a reference length of
   17.5 cm. Controls: vowel path (u o a e i), pharynx narrowing (the ع squeeze), mouth
   opening, ring (epilarynx narrowing). Resonances come from the zeros of the chain-matrix
   element M22 (closed glottis, open lips with end correction). They are solved once on a
   grid; length scales every resonance by 17.5/L exactly. */
const TUBE_NS = 34, L_REF = 17.5, C_SOUND = 35000, N_RES = 10;
const VOWEL_ANCHORS = [
  /* u */ [[0, 0.6], [0.06, 1.2], [0.12, 3.0], [0.32, 5.5], [0.45, 3.0], [0.53, 0.6], [0.58, 0.45], [0.68, 3.0], [0.82, 6.5], [0.9, 2.0], [0.93, 0.25], [1, 0.2]],
  /* o */ [[0, 0.6], [0.06, 1.2], [0.12, 1.8], [0.3, 1.5], [0.42, 1.2], [0.52, 1.6], [0.66, 4.5], [0.84, 6.0], [0.9, 2.0], [0.93, 0.6], [1, 0.5]],
  /* a */ [[0, 0.6], [0.06, 1.2], [0.12, 0.9], [0.25, 0.55], [0.42, 0.7], [0.55, 2.2], [0.68, 4.6], [0.82, 6.0], [0.92, 5.2], [1, 3.8]],
  /* e */ [[0, 0.6], [0.06, 1.2], [0.12, 2.6], [0.3, 4.5], [0.5, 3.2], [0.65, 1.6], [0.78, 1.1], [0.88, 1.6], [0.95, 2.4], [1, 2.6]],
  /* i */ [[0, 0.6], [0.06, 1.2], [0.12, 3.2], [0.3, 7.0], [0.48, 6.0], [0.62, 2.2], [0.72, 0.5], [0.82, 0.32], [0.9, 0.7], [0.96, 1.6], [1, 2.0]]
];
const VOWEL_NAMES = ['u', 'o', 'a', 'e', 'i'];
function profileAt(cp, x) {
  for (let i = 1; i < cp.length; i++) if (x <= cp[i][0]) {
    const x0 = cp[i - 1][0], a0 = cp[i - 1][1], x1 = cp[i][0], a1 = cp[i][1];
    const t = (x - x0) / (x1 - x0); const d = (1 - t) * Math.sqrt(a0) + t * Math.sqrt(a1); return d * d;
  }
  return cp[cp.length - 1][1];
}
function areaFunction(vowel, pharynx, mouth, ring, out) {
  out = out || new Float64Array(TUBE_NS);
  const pos = clamp(vowel, 0, 1) * 4; const i0 = Math.min(3, Math.floor(pos)); const t = pos - i0;
  const mk = Math.pow(2, (clamp(mouth, 0, 1) - 0.5) * 4.4);
  for (let i = 0; i < TUBE_NS; i++) {
    const x = (i + 0.5) / TUBE_NS;
    const d = (1 - t) * Math.sqrt(profileAt(VOWEL_ANCHORS[i0], x)) + t * Math.sqrt(profileAt(VOWEL_ANCHORS[i0 + 1], x));
    let A = d * d;
    const wp = Math.exp(-Math.pow((x - 0.27) / 0.09, 2)) * clamp(pharynx, 0, 1);      // pharyngeal squeeze
    A = Math.pow(A, 1 - wp) * Math.pow(0.3, wp);
    const wr = (1 - smooth(0.08, 0.16, x)) * clamp(ring, 0, 1) * 0.85;                 // epilarynx narrowing
    A = Math.pow(A, 1 - wr) * Math.pow(0.22, wr);
    const wm = smooth(0.76, 0.92, x);                                                   // lips and front cavity
    A *= Math.pow(mk, wm);
    out[i] = Math.max(0.05, A);
  }
  return out;
}
function tubeM22(A, L, f, ns) {
  const l = L / ns;
  const k = TAU * f * l / C_SOUND, cs = Math.cos(k), sn = Math.sin(k);
  let a = 1, b = 0, c = 0, d = 1;
  for (let i = 0; i < ns; i++) {
    const Z = 1 / A[i], b2 = Z * sn, c2 = sn / Z;
    const na = a * cs - b * c2, nb = a * b2 + b * cs, nc = c * cs + d * c2, nd = -c * b2 + d * cs;
    a = na; b = nb; c = nc; d = nd;
  }
  const r = Math.sqrt(A[ns - 1] / Math.PI), ke = TAU * f * 0.8 * r / C_SOUND, ce = Math.cos(ke), se = Math.sin(ke);
  const Z = 1 / A[ns - 1];
  return -c * Z * se + d * ce;
}
function tubeResonances(A, L, n, out, amp) {
  out = out || new Float64Array(n);
  let found = 0, df = 25, f0 = 40, v0 = tubeM22(A, L, f0, TUBE_NS);
  for (let f = f0 + df; f < 16000 && found < n; f += df) {
    const v = tubeM22(A, L, f, TUBE_NS);
    if (v0 * v < 0) {
      let lo = f - df, hi = f, vl = v0;
      for (let it = 0; it < 22; it++) { const m = 0.5 * (lo + hi), vm = tubeM22(A, L, m, TUBE_NS); if (vl * vm <= 0) hi = m; else { lo = m; vl = vm; } }
      const fk = 0.5 * (lo + hi);
      if (amp) { const dl = 0.25, dd = (tubeM22(A, L, fk + dl, TUBE_NS) - tubeM22(A, L, fk - dl, TUBE_NS)) / (2 * dl); amp[found] = -2 / (fk * dd); }
      out[found++] = fk;
    }
    v0 = v;
  }
  for (; found < n; found++) { out[found] = found ? out[found - 1] * 1.15 : 500; if (amp) amp[found] = 0; }
  return out;
}
const GRID = { nv: 9, np: 5, nm: 5, nr: 4 };
function buildTubeGrid() {
  const { nv, np, nm, nr } = GRID;
  const count = nv * np * nm * nr;
  const F = new Float32Array(count * N_RES), Am = new Float32Array(count * N_RES), minA = new Float32Array(count);
  const A = new Float64Array(TUBE_NS), R = new Float64Array(N_RES), RA = new Float64Array(N_RES);
  let idx = 0;
  for (let iv = 0; iv < nv; iv++) for (let ip = 0; ip < np; ip++) for (let im = 0; im < nm; im++) for (let ir = 0; ir < nr; ir++) {
    areaFunction(iv / (nv - 1), ip / (np - 1), im / (nm - 1), ir / (nr - 1), A);
    tubeResonances(A, L_REF, N_RES, R, RA);
    let mn = 99; for (let i = 0; i < TUBE_NS; i++) if (A[i] < mn) mn = A[i];
    for (let k = 0; k < N_RES; k++) { F[idx * N_RES + k] = R[k]; Am[idx * N_RES + k] = RA[k]; }
    minA[idx] = mn; idx++;
  }
  return { F, Am, minA };
}
// 4-D multilinear lookup of resonances at the reference length.
function gridLookup(grid, vowel, pharynx, mouth, ring, outF, outA) {
  const { nv, np, nm, nr } = GRID;
  const fv = clamp(vowel, 0, 1) * (nv - 1), fp = clamp(pharynx, 0, 1) * (np - 1), fm = clamp(mouth, 0, 1) * (nm - 1), fr = clamp(ring, 0, 1) * (nr - 1);
  const iv = Math.min(nv - 2, fv | 0), ip = Math.min(np - 2, fp | 0), im = Math.min(nm - 2, fm | 0), ir = Math.min(nr - 2, fr | 0);
  const tv = fv - iv, tp = fp - ip, tm = fm - im, tr = fr - ir;
  for (let k = 0; k < N_RES; k++) { outF[k] = 0; if (outA) outA[k] = 0; }
  let mA = 0;
  for (let c = 0; c < 16; c++) {
    const dv = c & 1, dp = (c >> 1) & 1, dm = (c >> 2) & 1, dr = (c >> 3) & 1;
    const w = (dv ? tv : 1 - tv) * (dp ? tp : 1 - tp) * (dm ? tm : 1 - tm) * (dr ? tr : 1 - tr);
    if (w === 0) continue;
    const idx = (((iv + dv) * np + (ip + dp)) * nm + (im + dm)) * nr + (ir + dr);
    const o = idx * N_RES;
    for (let k = 0; k < N_RES; k++) { outF[k] += w * grid.F[o + k]; if (outA) outA[k] += w * grid.Am[o + k]; }
    mA += w * grid.minA[idx];
  }
  return mA;
}
// Bandwidths from losses: wall and viscous losses (Hawks & Miller fit below 5 kHz),
// radiation growth above it, glottal loss that widens the low resonances for breathy
// pulses, and a floor that keeps the high resonances soft so they never ping.
function bandwidth(F, n, rd, minA) {
  let B;
  if (F < 500) B = 165.327516 + F * (-0.673636734 + F * (1.80874446e-3 + F * (-4.52201682e-6 + F * (7.495140e-9 - F * 4.70219241e-12))));
  else if (F < 5000) B = 15.8146139 + F * (8.10159009e-2 + F * (-9.79728215e-5 + F * (5.28725064e-8 + F * (-1.07099364e-11 + F * 7.91528509e-16))));
  else B = 360 * Math.pow(F / 5000, 1.6);
  B = Math.max(B, 40);
  if (n === 0) B += 28 * rd; else if (n === 1) B += 14 * rd; else if (n === 2) B += 6 * rd;
  const narrow = clamp((0.9 - minA) / 0.75, 0, 1);
  if (n < 3) B *= 1 + narrow * (n === 0 ? 0.9 : n === 1 ? 0.6 : 0.3);
  if (F > 3000) B = Math.max(B, 0.075 * F);
  return B;
}

let SHARED = null;
function buildShared() {
  if (!SHARED) SHARED = { pulses: buildPulseTables(), grid: buildTubeGrid() };
  return SHARED;
}
function adoptShared(s) { SHARED = s; return s; }

/* ------------------------------------------------------------------ parameters */
const PARAM_DEFS = {
  // folds
  pressure: [0.5, 0, 1], breath: [0.12, 0, 1], whisper: [0, 0, 1], jitter: [0.3, 0, 5], shimmer: [2.5, 0, 20],
  tremor: [6, 0, 60], wander: [4, 0, 40], vibrato: [0, 0, 80],
  // roughness
  growl: [0, 0, 1], creak: [0, 0, 1], tailFry: [0, 0, 1], flutter: [0, 0, 1], rasp: [0, 0, 1], breaks: [0, 0, 1],
  // throat
  size: [17.5, 13, 20.5], pharynx: [0, 0, 1], mouth: [0.5, 0, 1], ring: [0.3, 0, 1], vowel: [0.5, 0, 1],
  // onset
  style: [0.45, 0, 1], attack: [60, 3, 1200], release: [220, 20, 2500], glide: [60, 0, 600],
  // group (play)
  throats: [3, 1, 8], looseness: [0.35, 0, 1], spread: [0.5, 0, 1], sizeSpread: [0.4, 0, 1],
  // space
  distance: [0.15, 0, 1], azimuth: [0, -180, 180], room: [0.5, 0, 1], decay: [1.8, 0.3, 7], wet: [0.28, 0, 1],
  // tone
  drive: [0, 0, 1], body: [0, -12, 6], air: [0, -6, 9], level: [0, -24, 6],
  // proof
  gritAfter: [0, 0, 1],
  // chant transport
  tempo: [96, 40, 180], swing: [0, 0, 0.6], chantLevel: [0, -24, 6]
};
function defaultParams() { const p = {}; for (const k in PARAM_DEFS) p[k] = PARAM_DEFS[k][0]; return p; }

/* Texture presets ("specimens"). Values sit inside measured human ranges unless named extreme. */
const PRESETS = [
  { id: 'clean', name: 'Clean voice', note: 'Healthy closure, small irregularity', p: { pressure: 0.5, breath: 0.1, jitter: 0.35, shimmer: 2.5, tremor: 5, wander: 4, growl: 0, creak: 0, flutter: 0, rasp: 0, size: 17.5, vowel: 0.5, mouth: 0.55, ring: 0.35, pharynx: 0, style: 0.45, drive: 0, tailFry: 0, breaks: 0 } },
  { id: 'weathered', name: 'Weathered baritone', note: 'Late-Cash bundle: breath, tremor, fry at phrase ends', p: { pressure: 0.42, breath: 0.38, jitter: 2.3, shimmer: 6.5, tremor: 26, wander: 12, growl: 0.04, creak: 0.03, tailFry: 0.75, flutter: 0.15, rasp: 0.12, size: 18.9, vowel: 0.4, mouth: 0.42, ring: 0.2, pharynx: 0.05, style: 0.35, attack: 90, release: 520, breaks: 0.15 } },
  { id: 'raspy', name: 'Raspy belt', note: 'Pressed, open, irregular, rasp in the open phase', p: { pressure: 0.74, breath: 0.1, jitter: 1.1, shimmer: 9.2, tremor: 10, wander: 6, growl: 0.1, creak: 0, flutter: 0.22, rasp: 0.34, size: 17.2, vowel: 0.56, mouth: 0.78, ring: 0.62, pharynx: 0.08, style: 0.7, drive: 0.05, breaks: 0.1 } },
  { id: 'chant', name: 'Chant voice', note: 'Rough, low, made for rows', p: { pressure: 0.6, breath: 0.26, jitter: 1.7, shimmer: 8.0, tremor: 8, wander: 8, growl: 0.07, creak: 0, flutter: 0.2, rasp: 0.28, size: 18.2, vowel: 0.38, mouth: 0.5, ring: 0.25, pharynx: 0.12, style: 0.6 } },
  { id: 'growl', name: 'Chest growl', note: 'False folds join: period doubling below 200 Hz', p: { pressure: 0.7, breath: 0.2, jitter: 2.2, shimmer: 6, tremor: 6, wander: 6, growl: 0.85, creak: 0, flutter: 0.35, rasp: 0.5, size: 18.6, vowel: 0.35, mouth: 0.5, ring: 0.3, pharynx: 0.2, style: 0.75, drive: 0.1 } },
  { id: 'fry', name: 'Vocal fry', note: 'Pressed pulses with silence between them', p: { pressure: 0.78, breath: 0.05, jitter: 1.0, shimmer: 5, tremor: 0, wander: 3, growl: 0, creak: 0.9, flutter: 0, rasp: 0.05, size: 17.8, vowel: 0.45, mouth: 0.45, ring: 0.2, pharynx: 0, style: 0.5 } },
  { id: 'ayn', name: 'ع Pharynx', note: 'Low throat squeeze: F1 up, F2 down, wet', p: { pressure: 0.62, breath: 0.24, jitter: 1.0, shimmer: 5, tremor: 6, wander: 5, growl: 0.06, creak: 0, flutter: 0.25, rasp: 0.2, size: 17.6, vowel: 0.5, mouth: 0.52, ring: 0.3, pharynx: 0.92, style: 0.55 } },
  { id: 'ring', name: 'Ring', note: 'Narrow epilarynx gathers energy near 3 kHz', p: { pressure: 0.62, breath: 0.08, jitter: 0.4, shimmer: 2.8, tremor: 6, wander: 3, vibrato: 22, growl: 0, creak: 0, flutter: 0, rasp: 0, size: 17.3, vowel: 0.62, mouth: 0.62, ring: 0.95, pharynx: 0, style: 0.6 } },
  { id: 'whisper', name: 'Whisper', note: 'Folds apart; turbulence shaped by the tube', p: { pressure: 0.4, breath: 0.7, whisper: 0.92, jitter: 0.5, shimmer: 3, tremor: 0, wander: 2, growl: 0, creak: 0, flutter: 0, rasp: 0.05, size: 17.5, vowel: 0.5, mouth: 0.6, ring: 0.2, pharynx: 0, style: 0.3 } },
  { id: 'small', name: 'Small throat', note: 'Short tube, high register, light fold mass', p: { pressure: 0.5, breath: 0.2, jitter: 0.5, shimmer: 3.2, tremor: 7, wander: 5, growl: 0, creak: 0, flutter: 0, rasp: 0.03, size: 13.6, vowel: 0.6, mouth: 0.6, ring: 0.4, pharynx: 0, style: 0.4 } },
  { id: 'kargyraa', name: 'Deep kargyraa', note: 'Long tube, full false-fold doubling, low only', p: { pressure: 0.72, breath: 0.18, jitter: 2.0, shimmer: 6, tremor: 4, wander: 4, growl: 1, creak: 0.08, flutter: 0.3, rasp: 0.35, size: 19.8, vowel: 0.28, mouth: 0.4, ring: 0.55, pharynx: 0.15, style: 0.7 } }
];

/* ------------------------------------------------------------------ gestures for chant
   keys: [u, amp, semis, vowel(-1 base), mouth(-1 base), pressure delta, growl add, breath add] */
const GESTURES = {
  hum:    { style: 0.12, keys: [[0, 0, 0, 0.1, 0.2, 0, 0, 0], [0.2, 0.75, 0, 0.1, 0.2, 0, 0, 0], [0.82, 0.7, 0, 0.12, 0.22, 0, 0, 0], [1, 0, 0, 0.1, 0.2, 0, 0, 0]] },
  daha:   { style: 0.62, keys: [[0, 0, 0, 0.42, 0.55, 0.1, 0, 0], [0.06, 0.82, 0, 0.45, 0.62, 0.12, 0, 0], [0.26, 0.6, -1, 0.45, 0.55, 0, 0, 0], [0.34, 0.06, -1, 0.4, 0.4, 0, 0, 0.35], [0.42, 1.0, 1, 0.5, 0.85, 0.22, 0.25, 0.5], [0.72, 0.62, -1, 0.5, 0.7, 0.1, 0.1, 0.25], [1, 0, -4, 0.45, 0.5, 0, 0, 0.35]] },
  grunt:  { style: 0.95, keys: [[0, 0, 0, 0.3, 0.5, 0.3, 0.5, 0], [0.07, 1, 0, 0.3, 0.5, 0.35, 0.6, 0], [0.5, 0.6, -2, 0.2, 0.42, 0.2, 0.6, 0.1], [1, 0, -5, 0.12, 0.3, 0, 0.4, 0.25]] },
  shout:  { style: 0.85, keys: [[0, 0, 0, 0.5, 0.9, 0.4, 0.1, 0], [0.07, 1.05, 2, 0.52, 1, 0.45, 0.15, 0], [0.5, 0.9, 1, 0.5, 0.95, 0.35, 0.1, 0], [0.82, 0.5, -3, 0.5, 0.8, 0.1, 0.1, 0.2], [1, 0, -6, 0.45, 0.6, 0, 0, 0.3]] },
  wow:    { style: 0.3, keys: [[0, 0, 0, 0.0, 0.1, 0, 0, 0], [0.12, 0.7, 0, 0.02, 0.14, 0, 0, 0], [0.5, 1, 0.5, 0.5, 0.95, 0.1, 0, 0], [0.84, 0.7, 0, 0.1, 0.3, 0, 0, 0], [1, 0, -0.5, 0.0, 0.1, 0, 0, 0]] },
  swell:  { style: 0.2, keys: [[0, 0, 0, 0.3, 0.4, -0.1, 0, 0.1], [0.5, 1, 0, 0.5, 0.7, 0.1, 0, 0], [1, 0, 0, 0.35, 0.45, -0.1, 0, 0.1]] },
  pulse:  { style: 0.7, keys: [[0, 0, 0, -1, -1, 0.1, 0, 0], [0.08, 1, 0, 0.55, 0.7, 0.15, 0, 0], [0.55, 0.5, 0, 0.55, 0.6, 0, 0, 0], [1, 0, -1, 0.5, 0.5, 0, 0, 0]] },
  call:   { style: 0.5, who: 'leader', keys: [[0, 0, 0, 0.55, 0.7, 0.1, 0, 0], [0.06, 1, 0, 0.55, 0.75, 0.15, 0, 0], [0.3, 1, 3, 0.62, 0.8, 0.2, 0, 0], [0.55, 0.9, 5, 0.55, 0.8, 0.2, 0, 0], [0.78, 0.8, 3, 0.45, 0.65, 0.1, 0, 0], [1, 0, 0, 0.4, 0.5, 0, 0, 0.2]] },
  answer: { style: 0.55, who: 'followers', keys: [[0, 0, 0, 0.45, 0.6, 0.1, 0, 0], [0.08, 1, 3, 0.5, 0.7, 0.15, 0.1, 0], [0.6, 0.9, 0, 0.45, 0.65, 0.1, 0.1, 0], [1, 0, -2, 0.35, 0.45, 0, 0, 0.2]] },
  split:  { style: 0.3, keys: [[0, 0, 0, 0.05, 0.3, 0.1, 0.6, 0], [0.1, 0.9, 0, 0.05, 0.3, 0.15, 0.8, 0], [0.5, 0.9, 0, 0.95, 0.3, 0.15, 0.8, 0], [0.9, 0.85, 0, 0.1, 0.3, 0.1, 0.8, 0], [1, 0, 0, 0.05, 0.3, 0, 0.6, 0]] },
  phrase: { style: 0.45, keys: [[0, 0, 0, 0.5, 0.6, 0, 0, 0], [0.05, 0.9, 0, 0.5, 0.65, 0.1, 0, 0], [0.22, 0.95, 3, 0.6, 0.75, 0.15, 0, 0], [0.4, 0.9, 5, 0.5, 0.8, 0.15, 0, 0], [0.58, 0.85, 3, 0.4, 0.6, 0.1, 0, 0], [0.76, 0.8, 0, 0.45, 0.6, 0.05, 0, 0], [0.9, 0.6, -2, 0.4, 0.5, 0, 0, 0.1], [1, 0, -2, 0.35, 0.45, 0, 0, 0.2]] },
  breath: { style: 0.3, voiced: false, keys: [[0, 0, 0, 0.4, 0.6, 0, 0, 0], [0.6, 0.6, 0, 0.4, 0.6, 0, 0, 0], [1, 0, 0, 0.4, 0.6, 0, 0, 0]] },
  clap:   { kind: 'clap' },
  stamp:  { kind: 'stamp' }
};
const GESTURE_ORDER = ['daha', 'grunt', 'shout', 'pulse', 'wow', 'hum', 'swell', 'call', 'answer', 'phrase', 'split', 'breath', 'clap', 'stamp'];

/* Chant scenes. Steps are sixteenths; each event: [step, gesture, lengthSteps, accent, semitones]. */
const SCENES = [
  { id: 'daha', trim: 3.0, name: 'Daha line', note: 'Two lines answer a reciter; guttural "da-HA" and claps', tempo: 100, bars: 2, layers: [
    { name: 'Line I', singers: 7, midi: 45, preset: 'chant', sizeLo: 17.6, sizeHi: 19.6, looseness: 0.32, distance: 0.25, azimuth: -40, spread: 0.45, timing: 'grid', gain: 0, events: [[0, 'daha', 3, 1, 0], [8, 'daha', 3, 0.85, 0], [16, 'daha', 3, 1, 0], [24, 'grunt', 2, 0.9, -2]] },
    { name: 'Line II', singers: 7, midi: 45, preset: 'chant', sizeLo: 17.4, sizeHi: 19.4, looseness: 0.36, distance: 0.3, azimuth: 40, spread: 0.45, timing: 'grid', gain: -1, events: [[4, 'daha', 3, 0.9, 0], [12, 'daha', 3, 0.85, 0], [20, 'daha', 3, 0.9, 0], [28, 'grunt', 2, 1, -2]] },
    { name: 'Hands', singers: 6, midi: 45, preset: 'chant', sizeLo: 17, sizeHi: 19, looseness: 0.25, distance: 0.3, azimuth: 0, spread: 0.7, timing: 'grid', gain: -4, events: [[2, 'clap', 1, 0.8, 0], [6, 'clap', 1, 1, 0], [10, 'clap', 1, 0.8, 0], [14, 'clap', 1, 1, 0], [18, 'clap', 1, 0.8, 0], [22, 'clap', 1, 1, 0], [26, 'clap', 1, 0.8, 0], [30, 'clap', 1, 1, 0]] },
    { name: 'Reciter', singers: 1, midi: 52, preset: 'weathered', sizeLo: 18.2, sizeHi: 18.2, looseness: 0.2, distance: 0.05, azimuth: 0, spread: 0, timing: 'grid', gain: -2, events: [[0, 'phrase', 14, 0.9, 0]] }
  ] },
  { id: 'haka', trim: 2.1, name: 'Drilled shout', note: 'Tight unit, hard onsets, stamps on the beat', tempo: 92, bars: 1, layers: [
    { name: 'Leader', singers: 1, midi: 50, preset: 'raspy', sizeLo: 17.8, sizeHi: 17.8, looseness: 0.1, distance: 0.05, azimuth: 0, spread: 0, timing: 'grid', gain: -1, events: [[0, 'shout', 3, 1, 0]] },
    { name: 'Unit', singers: 10, midi: 45, preset: 'raspy', sizeLo: 17.4, sizeHi: 19.6, looseness: 0.12, distance: 0.22, azimuth: 0, spread: 0.6, timing: 'grid', gain: 0, events: [[4, 'shout', 2, 1, 0], [7, 'grunt', 2, 0.9, -2], [10, 'shout', 2, 1, 2], [13, 'grunt', 2, 1, -3]] },
    { name: 'Feet', singers: 6, midi: 45, preset: 'chant', sizeLo: 17, sizeHi: 19, looseness: 0.1, distance: 0.22, azimuth: 0, spread: 0.6, timing: 'grid', gain: -3, events: [[0, 'stamp', 1, 1, 0], [4, 'stamp', 1, 0.9, 0], [8, 'stamp', 1, 1, 0], [12, 'stamp', 1, 0.9, 0]] }
  ] },
  { id: 'grunts', trim: 2.9, name: 'Low grunt ostinato', note: 'Doubled-pulse grunts under a high solo line', tempo: 112, bars: 2, layers: [
    { name: 'Bass row', singers: 6, midi: 40, preset: 'growl', sizeLo: 18.4, sizeHi: 20.2, looseness: 0.3, distance: 0.25, azimuth: -20, spread: 0.5, timing: 'grid', gain: 0, events: [[0, 'grunt', 2, 1, 0], [3, 'grunt', 2, 0.8, 0], [6, 'grunt', 2, 0.9, 0], [8, 'grunt', 2, 1, 0], [11, 'grunt', 2, 0.8, 0], [14, 'grunt', 2, 0.9, 0], [16, 'grunt', 2, 1, 0], [19, 'grunt', 2, 0.8, 0], [22, 'grunt', 2, 0.9, 0], [24, 'grunt', 2, 1, 0], [27, 'grunt', 2, 0.8, 0], [30, 'grunt', 2, 0.9, 0]] },
    { name: 'Mid row', singers: 5, midi: 47, preset: 'chant', sizeLo: 17.4, sizeHi: 18.8, looseness: 0.35, distance: 0.3, azimuth: 30, spread: 0.5, timing: 'grid', gain: -3, events: [[2, 'pulse', 1, 0.7, 0], [10, 'pulse', 1, 0.7, 0], [18, 'pulse', 1, 0.7, 0], [26, 'pulse', 1, 0.7, 0]] },
    { name: 'Solo', singers: 1, midi: 59, preset: 'ring', sizeLo: 16.6, sizeHi: 16.6, looseness: 0.2, distance: 0.12, azimuth: 10, spread: 0, timing: 'grid', gain: -4, events: [[4, 'call', 10, 0.9, 0], [20, 'call', 8, 0.85, -2]] }
  ] },
  { id: 'split', trim: 3.5, name: 'Split tone', note: 'Low doubled fundamental, slow vowel sweeps lift overtones', tempo: 60, bars: 2, layers: [
    { name: 'Splitters', singers: 3, midi: 41, preset: 'kargyraa', sizeLo: 18.6, sizeHi: 19.8, looseness: 0.45, distance: 0.15, azimuth: 0, spread: 0.5, timing: 'free', gain: 0, events: [[0, 'split', 16, 1, 0], [16, 'split', 16, 0.9, 0]] },
    { name: 'Drone', singers: 2, midi: 41, preset: 'chant', sizeLo: 18, sizeHi: 19, looseness: 0.5, distance: 0.35, azimuth: 0, spread: 0.8, timing: 'free', gain: -6, events: [[0, 'hum', 30, 0.8, 0]] }
  ] },
  { id: 'faint', trim: 13.2, name: 'Faint chant', note: 'Distant, breathing, untimed; some voices behind you', tempo: 70, bars: 4, layers: [
    { name: 'Far row', singers: 8, midi: 45, preset: 'weathered', sizeLo: 17.4, sizeHi: 19.6, looseness: 0.65, distance: 0.82, azimuth: 160, spread: 0.6, timing: 'free', gain: -3, events: [[0, 'hum', 14, 0.7, 0], [16, 'swell', 14, 0.8, 0], [32, 'hum', 12, 0.7, -2], [48, 'swell', 14, 0.75, 0]] },
    { name: 'Breathers', singers: 5, midi: 45, preset: 'whisper', sizeLo: 17, sizeHi: 19, looseness: 0.8, distance: 0.7, azimuth: -150, spread: 0.7, timing: 'free', gain: -6, events: [[6, 'breath', 4, 0.8, 0], [22, 'breath', 4, 0.7, 0], [38, 'breath', 4, 0.8, 0], [54, 'breath', 4, 0.7, 0]] },
    { name: 'Low call', singers: 3, midi: 40, preset: 'chant', sizeLo: 18.6, sizeHi: 19.8, looseness: 0.55, distance: 0.9, azimuth: 180, spread: 0.3, timing: 'free', gain: -5, events: [[8, 'wow', 6, 0.7, 0], [40, 'wow', 6, 0.7, 0]] }
  ] },
  { id: 'field', trim: 20.7, name: 'Field', note: 'Steady statistics, soft onsets, no direction', tempo: 54, bars: 4, layers: [
    { name: 'Wash A', singers: 6, midi: 48, preset: 'clean', sizeLo: 16, sizeHi: 19, looseness: 0.75, distance: 0.55, azimuth: 0, spread: 1, timing: 'free', gain: -2, events: [[0, 'hum', 30, 0.6, 0], [32, 'hum', 30, 0.6, 0]] },
    { name: 'Wash B', singers: 6, midi: 55, preset: 'clean', sizeLo: 14.5, sizeHi: 17.5, looseness: 0.75, distance: 0.6, azimuth: 180, spread: 1, timing: 'free', gain: -5, events: [[16, 'swell', 30, 0.55, 0], [48, 'swell', 30, 0.55, 0]] }
  ] },
  { id: 'swarm', trim: 9.6, name: 'Approaching swarm', note: 'Irregular onsets, a body that comes closer from behind', tempo: 84, bars: 2, layers: [
    { name: 'Swarm', singers: 12, midi: 43, preset: 'chant', sizeLo: 16.8, sizeHi: 20, looseness: 0.85, distance: 0.95, azimuth: 170, spread: 0.5, timing: 'free', gain: 0, approach: 0.5, events: [[0, 'wow', 3, 0.8, 0], [5, 'grunt', 2, 0.7, 0], [9, 'wow', 3, 0.8, 2], [14, 'grunt', 2, 0.8, 0], [18, 'wow', 4, 0.8, 0], [24, 'grunt', 2, 0.9, -2], [28, 'daha', 3, 0.8, 0]] }
  ] }
];

/* ------------------------------------------------------------------ small DSP blocks */
function onePoleCoef(fc, sr) { return 1 - Math.exp(-TAU * fc / sr); }

function Biquad() { this.b0 = 1; this.b1 = 0; this.b2 = 0; this.a1 = 0; this.a2 = 0; this.z1 = 0; this.z2 = 0; }
Biquad.prototype.set = function (type, f, q, db, sr) {
  const A = Math.pow(10, db / 40), w = TAU * f / sr, cs = Math.cos(w), sn = Math.sin(w), al = sn / (2 * q);
  let b0, b1, b2, a0, a1, a2;
  if (type === 'lowshelf' || type === 'highshelf') {
    const s = 2 * Math.sqrt(A) * al, sg = type === 'lowshelf' ? 1 : -1;
    b0 = A * ((A + 1) - sg * (A - 1) * cs + s); b1 = sg * 2 * A * ((A - 1) - sg * (A + 1) * cs); b2 = A * ((A + 1) - sg * (A - 1) * cs - s);
    a0 = (A + 1) + sg * (A - 1) * cs + s; a1 = -sg * 2 * ((A - 1) + sg * (A + 1) * cs); a2 = (A + 1) + sg * (A - 1) * cs - s;
  } else if (type === 'peak') { b0 = 1 + al * A; b1 = -2 * cs; b2 = 1 - al * A; a0 = 1 + al / A; a1 = -2 * cs; a2 = 1 - al / A; }
  else if (type === 'bandpass') { b0 = al; b1 = 0; b2 = -al; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else if (type === 'highpass') { b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = (1 + cs) / 2; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else { b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = (1 - cs) / 2; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  this.b0 = b0 / a0; this.b1 = b1 / a0; this.b2 = b2 / a0; this.a1 = a1 / a0; this.a2 = a2 / a0;
  return this;
};
Biquad.prototype.tick = function (x) {
  const y = this.b0 * x + this.z1; this.z1 = this.b1 * x - this.a1 * y + this.z2; this.z2 = this.b2 * x - this.a2 * y; return y;
};

/* ------------------------------------------------------------------ syllable / gesture state */
function evalKeys(keys, u, out) {
  if (u <= keys[0][0]) { for (let j = 1; j < 8; j++) out[j] = keys[0][j]; return out; }
  for (let i = 1; i < keys.length; i++) if (u <= keys[i][0]) {
    const a = keys[i - 1], b = keys[i], t = (u - a[0]) / (b[0] - a[0] || 1);
    for (let j = 1; j < 8; j++) {
      const va = a[j], vb = b[j];
      if ((j === 3 || j === 4) && (va < 0 || vb < 0)) out[j] = va < 0 && vb < 0 ? -1 : (va < 0 ? vb : va);
      else out[j] = va + (vb - va) * t;
    }
    return out;
  }
  const z = keys[keys.length - 1]; for (let j = 1; j < 8; j++) out[j] = z[j]; return out;
}

const SINGER_KEYS = ['pressure', 'breath', 'whisper', 'jitter', 'shimmer', 'tremor', 'wander', 'vibrato', 'growl', 'creak', 'tailFry', 'flutter', 'rasp', 'breaks', 'pharynx', 'ring', 'drive', 'style'];
/* ------------------------------------------------------------------ Singer
   One throat: source, resonator bank, high-pass, drive, space. Rendered block-wise. */
function Singer(eng, slot) {
  this.e = eng; this.slot = slot; this.sr = eng.sr;
  this.active = false; this.voicing = false;
  this.rng = (hash(slot, 991, 7, 3) | 1) >>> 0;
  this.ic1 = new Float64Array(N_RES); this.ic2 = new Float64Array(N_RES);
  this.ca1 = new Float64Array(N_RES); this.ca2 = new Float64Array(N_RES); this.ca3 = new Float64Array(N_RES);
  this.F = new Float64Array(N_RES); this.B = new Float64Array(N_RES); this.Fbuf = new Float64Array(N_RES);
  this.Abuf = new Float64Array(N_RES); this.ca = new Float64Array(N_RES); this.ta = new Float64Array(N_RES); this.src = new Float64Array(512);
  this.itd = new Float32Array(128); this.itdW = 0;
  this.kv = new Float64Array(8);
  this.cyc = new Float32Array(64 * 3); this.cycN = 0; // period(ms), amp, kind
  this.reset();
}
Singer.prototype.reset = function () {
  this.active = false; this.voicing = false; this.ph = 0; this.inc = 0; this.gap = 0; this.parity = 0;
  this.amp = 0; this.ampT = 0; this.rdA = 0; this.rdW = 0; this.lev = 0; this.tabRd = 0;
  this.ic1.fill(0); this.ic2.fill(0); this.hp1 = 0; this.hp2 = 0;
  this.p = 0; this.pT = 0; this.gate = false; this.V = 0; this.noiseA = 0; this.noiseB = 0;
  this.raspC = 0; this.first = 0; this.breakN = 0; this.breakR = 1;
  this.dlp = 0; this.flp = 0; this.asp1 = 0; this.fl1 = 0; this.fl2 = 0; this.xPrev = 0; this.driveOn = false;
  this.itd.fill(0); this.silentBlocks = 0; this.coefInit = false; this.outLev = 0;
  this.syl = null; this.sylT = 0; this.sylDur = 1; this.perc = null; this.percT = 0;
  this.wanderS = 0; this.wanderV = 0; this.fNow = 110; this.fCur = 110; this.gLvl = 0; this.gainCur = 0;
  this.revS = 0; this.pdel = 0; this.gL = null; this.gR = null; this.hpInit = false; this.killFade = 0;
};
Singer.prototype.sleep = function () {
  const own = this.owner, ev = this.events; this.reset();
  if (own && own.kind === 'layer') { this.owner = own; this.events = ev; } else { this.owner = null; this.events = null; }
};
// Expected loudness of this throat's voiced sound at a neutral shape, from the pulse's own
// harmonic spectrum and the tube's response (K-weighted power). Pitch, throat size and pressure
// are normalised by it; vowel, mouth and ring are left alone so gestures keep their dynamics.
const REF_SHAPE = { vowel: 0.5, pharynx: 0, mouth: 0.5, ring: 0.3 };
function expectedPower(e, f0, L, rd) {
  const pt = e.pulses, NH = pt.NH, sr = e.sr;
  const F = e._lnF || (e._lnF = new Float64Array(N_RES)), A = e._lnA || (e._lnA = new Float64Array(N_RES));
  const minA = gridLookup(e.grid, REF_SHAPE.vowel, REF_SHAPE.pharynx, REF_SHAPE.mouth, REF_SHAPE.ring, F, A);
  const sc = L_REF / L, rf = clamp((rd - RD_MIN) / RD_STEP, 0, N_RD - 1.001), r0 = rf | 0, rw = rf - r0;
  const B = e._lnB || (e._lnB = new Float64Array(N_RES));
  for (let k = 0; k < N_RES; k++) { F[k] *= sc; B[k] = bandwidth(F[k], k, rd, minA); }
  let P = 0;
  for (let h = 1; h <= NH; h++) {
    const f = h * f0; if (f > 7000 || f > 0.45 * sr) break;
    const c = (1 - rw) * pt.harm[r0 * NH + h - 1] + rw * pt.harm[(r0 + 1) * NH + h - 1];
    let hr = 0, hi = 0;
    for (let k = 0; k < N_RES; k++) {
      const wk = F[k], q = B[k];
      const dr = wk * wk - f * f, di = f * q;            // s-plane LP2 at jω, in Hz units
      const den = dr * dr + di * di, g = A[k] * wk * wk / den;
      hr += g * dr; hi -= g * di;
    }
    const f2 = f * f, kw = (1 + 1.5119 * f2 / (f2 + 2.25e6)) * (f2 * f2 / (f2 * f2 + 2.1e6));
    P += c * c * (hr * hr + hi * hi) * kw;
  }
  return P;
}
Singer.prototype.loudNorm = function () {
  const e = this.e, f = this.fCur, rd = this.rdNow || 1.2;
  if (this.lnF && Math.abs(f / this.lnF - 1) < 0.02 && Math.abs(rd - this.lnRd) < 0.06 && this.lnL === this.L) return;
  this.lnF = f; this.lnRd = rd; this.lnL = this.L;
  const P = expectedPower(e, clamp(f, 30, 1500), this.L, rd);
  if (!e.lnRef) e.lnRef = expectedPower(e, 160, L_REF, 1.2);
  // measured residual: pressed pulses grow louder with pitch faster than the model predicts
  const corr = Math.pow(10, -3.6 * Math.max(0, 1.5 - rd) * Math.max(0, Math.log2(f / 110)) / 20);
  this.normT = clamp(Math.sqrt(e.lnRef / (P + 1e-12)) * corr, 0.08, 12);
  if (!this.norm) this.norm = this.normT;
};
Singer.prototype.rand = function () { let x = this.rng; x ^= x << 13; x ^= x >>> 17; x ^= x << 5; this.rng = x >>> 0; return this.rng / 4294967296; };
Singer.prototype.gauss = function () { return (this.rand() + this.rand() + this.rand() + this.rand() - 2) * 1.7320508; };

// Assign a person: traits stay with the slot, so each singer keeps the same throat and habits.
Singer.prototype.assign = function (o) {
  this.owner = o.owner; this.layer = o.layer; this.role = o.role; this.index = o.index;
  this.P = o.params; this.seed = o.seed;
  this.L = o.size; this.az = o.azimuth; this.dist = o.distance; this.lagMs = o.lagMs || 0;
  this.detune = o.detune || 0; this.levelDb = o.levelDb || 0; this.vowelOff = o.vowelOff || 0;
  this.coupling = o.coupling == null ? 0.5 : o.coupling; this.looseWander = o.looseWander || 0;
  this.lod = o.lod || N_RES; this.carrier = o.carrier !== false; this.midi = o.midi; this.baseHz = 440 * Math.pow(2, (o.midi - 69) / 12);
  this.fLow = 92 * Math.pow(L_REF / this.L, 1.6);
  this.fNow = this.fCur = this.baseHz; this.scoop = 0; this.scoopTau = 0.1;
  this.gainExtra = o.gain || 1;
  this.trem = [h01(this.seed, 1, 0, 0) * TAU, h01(this.seed, 2, 0, 0) * TAU, h01(this.seed, 3, 0, 0) * TAU];
  this.tremR = [4.1 + h01(this.seed, 4, 0, 0) * 0.8, 5.0 + h01(this.seed, 5, 0, 0) * 0.7, 5.9 + h01(this.seed, 6, 0, 0) * 0.9];
  this.vibPh = h01(this.seed, 7, 0, 0) * TAU;
  this.active = true;
};

// Start voicing or a syllable. gate on with target pressure.
Singer.prototype.start = function (o) {
  const P = this.P;
  this.gate = true; this.pT = o.level == null ? 1 : o.level; this.style = o.style == null ? P.style : o.style;
  this.syl = o.gesture || null; this.sylT = 0; this.sylDur = Math.max(1, o.dur || 1); this.sylSemis = o.semis || 0; this.sylAcc = o.accent == null ? 1 : o.accent;
  this.unvoiced = !!(o.gesture && o.gesture.voiced === false);
  if (o.midi != null) { this.midi = o.midi; this.baseHz = 440 * Math.pow(2, (o.midi - 69) / 12); }
  // pitch scoop: start below, settle
  const sc = o.scoop || 0; this.scoop = -sc; this.scoopTau = Math.max(0.02, (o.settle || 0.1) / 2.3);
  if (!this.voicing && !this.wasSounding) { this.fCur = this.baseHz * Math.pow(2, (this.detune - sc) / 1200); }
  this.first = this.voicing ? 0 : 2;
  this.active = true; this.silentBlocks = 0;
};
Singer.prototype.stop = function () { this.gate = false; this.pT = 0; };
Singer.prototype.startPerc = function (kind, accent) {
  this.perc = kind; this.percT = 0; this.percAcc = accent; this.active = true; this.silentBlocks = 0;
  this.pc1 = 0; this.pc2 = 0; this.pcPh = 0;
  const f = kind === 'clap' ? 1050 + h01(this.seed, 31, 0, 0) * 900 : 140;
  this.percBq = this.percBq || new Biquad(); this.percBq.z1 = this.percBq.z2 = 0;
  this.percBq.set(kind === 'clap' ? 'bandpass' : 'lowpass', f, kind === 'clap' ? 1.4 : 0.8, 0, this.sr);
  this.flams = kind === 'clap' ? [0, 0.004 + this.rand() * 0.004, 0.009 + this.rand() * 0.006] : [0];
};

/* Closure: decide everything about the next cycle at the moment the folds meet. */
Singer.prototype.closure = function () {
  const e = this.e, P = this.Peff, sr = this.sr;
  const f = this.fCur;
  const reg = clamp(Math.log2(f / this.fLow) / 2.5, 0, 1);
  this.reg = reg;
  this.parity ^= 1;
  const grit = e.gritAfter ? 0 : 1;
  // growl: period doubling in the low register, rasp and shimmer carry the grit above it
  const growl = P.growl * grit;
  const lowG = 1 - smooth(0.2, 0.48, reg);
  const dbl = growl * lowG, gHi = growl * (1 - lowG);
  // creak: crisp separated pulses at the bottom; occasional cracks higher up
  const releaseFry = (1 - this.V) * (this.gate ? 0.15 : 1) * P.tailFry;
  const creak = clamp(P.creak + releaseFry, 0, 1) * grit;
  const lowC = 1 - smooth(0.1, 0.38, reg);
  const cr = creak * lowC, crackP = creak * (1 - lowC) * 0.05;
  // jitter (partly shared between singers) and shimmer, in Praat-calibrated units
  const c = this.coupling;
  const sj = (P.jitter * grit) * 0.01 * e.cal.jitter;
  let jit = sj * (c * e.sharedJit + Math.sqrt(1 - c * c) * this.gauss());
  jit += gHi * 0.012 * this.gauss();
  let per = sr / f * (1 + clamp(jit, -0.25, 0.25));
  const ss = (P.shimmer * grit) * 0.01 * e.cal.shimmer + gHi * 0.06;
  let a = 1 + ss * this.gauss();
  if (dbl > 0) {
    if (this.parity) { a *= 1 - 0.62 * dbl; per *= 1 + 0.09 * dbl; } else { per *= 1 - 0.09 * dbl; }
  }
  let pulse = per, gap = 0;
  if (cr > 0) {
    pulse = per / (1 + 1.3 * cr);
    gap = per - pulse;
    if (this.parity) { gap += 0.9 * cr * per * (0.45 + 0.55 * this.rand()); a *= 1 - 0.55 * cr * (0.4 + 0.6 * this.rand()); }
    if (this.rand() < 0.08 * cr) a *= 0.08;
  }
  if (crackP > 0 && this.rand() < crackP) { if (this.rand() < 0.5) gap += per * (0.3 + 0.6 * this.rand()); else a *= 0.3; jit += 0.02 * this.gauss(); }
  // breaks: rare register flips, likelier near the passaggio
  if (this.breakN > 0) { this.breakN--; pulse /= this.breakR; gap /= this.breakR; a *= 0.55; }
  else if (P.breaks > 0 && grit) {
    const near = 0.25 + Math.exp(-Math.pow((reg - 0.55) / 0.12, 2));
    if (this.rand() < P.breaks * 0.004 * near) { this.breakN = 2 + ((this.rand() * 6) | 0); this.breakR = this.rand() < 0.6 ? 1.5 : 2; }
  }
  // voicing strength from the onset gesture, decided per cycle
  const V = this.V * (1 - P.whisper);
  let boost = 1;
  if (this.first > 0) { boost = 1 + 0.5 * smooth(0.6, 1, this.style); this.first--; }
  this.ampT = Math.max(0, a) * V * this.pLevel * boost * (this.norm || 1) * (1 + cr);
  // pulse shape
  let rd = lerp(2.3, 0.62, P.pressure) + P.breath * 0.7 - cr * 0.55 - dbl * 0.25 - (boost - 1) * 0.8;
  if (this.breakN > 0) rd += 0.6;
  rd = clamp(rd + 0.05 * Math.min(1, ss * 12) * this.gauss(), RD_MIN, RD_MAX - 1e-6);
  const rf = (rd - RD_MIN) / RD_STEP; this.rdA = rf | 0; this.rdW = rf - this.rdA;
  this.tabRd = this.rdW < 0.5 ? this.rdA : this.rdA + 1;
  this.rdNow = rd;
  // table level by the pulse's own rate (never alias)
  const fp = sr / pulse, lim = 0.475 * sr / fp;
  const pt = e.pulses; let lev = 0; while (lev < N_LEV - 1 && pt.hmax[lev] > lim) lev++;
  this.lev = lev;
  this.inc = 1 / pulse; this.gap = Math.round(gap);
  // rasp: noise strength for this cycle's open phase
  this.raspC = (P.rasp * grit + gHi * 0.5 + dbl * 0.25) * (0.5 + this.rand());
  // statistics for readouts and checks
  const k = (this.cycN % 64) * 3; this.cyc[k] = (pulse + gap) / sr * 1000; this.cyc[k + 1] = this.ampT; this.cyc[k + 2] = cr > 0.3 ? 2 : dbl > 0.3 ? 1 : (gap > 0 ? 3 : 0); this.cycN++;
  if (V <= 0.002 && !this.gate) this.voicing = false;
};

// Control-rate update: pitch, envelopes, throat, coefficient targets.
Singer.prototype.control = function (n) {
  const e = this.e, sr = this.sr, dt = n / sr;
  const base = this.P;
  // merge gesture curves
  const Pe = this.Peff || (this.Peff = {});
  for (let i = 0; i < SINGER_KEYS.length; i++) { const k = SINGER_KEYS[i]; Pe[k] = base[k]; }
  let semis = 0, vowel = base.vowel + this.vowelOff, mouth = base.mouth, gestAmp = 1;
  if (this.syl && this.syl.keys) {
    const u = this.sylT / this.sylDur;
    const kv = evalKeys(this.syl.keys, u, this.kv);
    gestAmp = kv[1] * this.sylAcc; semis = kv[2] + this.sylSemis;
    if (kv[3] >= 0) vowel = lerp(base.vowel, kv[3], 0.85) + this.vowelOff;
    if (kv[4] >= 0) mouth = lerp(base.mouth, kv[4], 0.85);
    Pe.pressure = clamp(base.pressure + kv[5], 0, 1); Pe.growl = clamp(base.growl + kv[6], 0, 1); Pe.breath = clamp(base.breath + kv[7], 0, 1);
    this.pT = this.gate ? gestAmp : 0;
    this.sylT += n;
    if (u >= 1 && this.gate) { this.gate = false; this.pT = 0; }
  } else if (this.syl === null && this.gate) { semis = this.sylSemis || 0; }
  this.vowelNow = vowel; this.mouthNow = mouth;
  // onset gesture: pressure follows target; style sets threshold and breath lead
  const st = this.style == null ? base.style : this.style;
  const att = Math.max(st > 0.85 ? 0.004 : 0.012, (this.syl ? 0.035 : base.attack / 1000) * (1.2 - st));
  const rel = this.syl ? 0.06 : base.release / 1000;
  const tc = this.pT > this.p ? att : rel;
  this.p += (this.pT - this.p) * (1 - Math.exp(-dt / tc));
  if (this.p < 1e-5 && this.pT === 0) this.p = 0;
  const th = st < 0.33 ? lerp(0.12, 0.5, st / 0.33) : st < 0.67 ? lerp(0.5, 0.08, (st - 0.33) / 0.34) : lerp(0.08, 0.0, (st - 0.67) / 0.33);
  const lead = st < 0.33 ? lerp(0.25, 0.9, st / 0.33) : st < 0.67 ? lerp(0.9, 0.1, (st - 0.33) / 0.34) : lerp(0.1, 0, (st - 0.67) / 0.33);
  const V = this.unvoiced ? 0 : smooth(th, th + 0.22, this.p);
  this.V = V; this.pLevel = Math.pow(this.p, 0.7);
  if (!this.voicing && V > 0.002 && !this.unvoiced) { this.voicing = true; this.ph = 0; this.gap = 0; this.parity = 0; this.closureFirst = true; }
  // noise: breath through the glottis, pre-voicing air, whisper, release tail
  const asp = Pe.breath * 0.55 * (1 + 0.5 * (this.reg || 0));
  const pre = lead * this.p * (1 - V) * 0.9;
  const unv = this.unvoiced ? this.p * 1.1 : 0;
  this.noiseAT = (asp * V + pre + Pe.whisper * this.p * 0.95 + unv) * (e.gritAfter && !this.unvoiced ? 0.6 : 1);
  this.breathFloor = 0.12 + 0.5 * Pe.breath;
  // pitch: base, detune, scoop, tremor, wander, vibrato, gesture
  this.scoop *= Math.exp(-dt / this.scoopTau);
  const t = e.time;
  const tr = this.trem, trr = this.tremR;
  const tremAmp = Pe.tremor * (0.55 + 0.45 * Math.sin(t * 0.37 + tr[0]));
  const trem = tremAmp * (0.5 * Math.sin(TAU * trr[0] * t + tr[0]) + 0.3 * Math.sin(TAU * trr[1] * t + tr[1]) + 0.2 * Math.sin(TAU * trr[2] * t + tr[2]));
  this.wanderV += (this.gauss() * 0.9 - this.wanderV) * (1 - Math.exp(-dt / 0.6));
  this.wanderS += (this.wanderV - this.wanderS) * (1 - Math.exp(-dt / 1.4));
  const wand = (Pe.wander + (this.index > 0 ? this.looseWander : 0)) * this.wanderS * 1.6;
  this.vibPh += TAU * 5.4 * dt;
  const vib = Pe.vibrato * Math.sin(this.vibPh) * smooth(0.25, 0.9, this.p);
  const cents = this.detune + this.scoop + trem + wand + vib + semis * 100 + (this.bend || 0);
  const target = this.baseHz * Math.pow(2, cents / 1200);
  const gl = this.syl ? 0.012 : Math.max(0.002, base.glide / 1000);
  this.fCur += (target - this.fCur) * (1 - Math.exp(-dt / gl));
  // throat: tube-derived resonances
  const gridF = this.Fbuf;
  const minA = gridLookup(e.grid, vowel, Pe.pharynx, mouth, Pe.ring, gridF, this.Abuf);
  const scale = L_REF / this.L;
  const nr = this.lod, ny = 0.42 * sr;
  const rd = this.rdNow || lerp(2.3, 0.62, Pe.pressure);
  for (let k = 0; k < nr; k++) {
    let F = gridF[k] * scale; if (F > ny) F = ny;
    let B = bandwidth(F, k, rd, minA);
    const g = Math.tan(Math.PI * F / sr), kk = Math.min(1.9, B / F);
    const a1 = 1 / (1 + g * (g + kk)), a2 = g * a1, a3 = g * a2;
    this.F[k] = F; this.B[k] = B;
    if (!this.coefInit) { this.ca1[k] = a1; this.ca2[k] = a2; this.ca3[k] = a3; this.ca[k] = this.Abuf[k]; }
    this.ta[k] = this.Abuf[k];
    this.ta1 = this.ta1 || new Float64Array(N_RES); this.ta2 = this.ta2 || new Float64Array(N_RES); this.ta3 = this.ta3 || new Float64Array(N_RES);
    this.ta1[k] = a1; this.ta2[k] = a2; this.ta3[k] = a3;
  }
  this.coefInit = true;
  // high-pass: just below the lowest partial this singer intends
  const fLowest = this.fCur * (Pe.growl > 0.1 ? 0.5 : 1) * (1 - 0.5 * clamp(Pe.creak, 0, 1));
  let hpf = 0.6 * fLowest;
  if (!this.carrier) hpf = Math.max(hpf, 0.9 * this.fCur);
  hpf *= 1 + 1.2 * this.dist;
  hpf = clamp(hpf, 25, 900);
  { const g = Math.tan(Math.PI * hpf / sr), k = 1.41421356, a1 = 1 / (1 + g * (g + k)); this.hpT1 = a1; this.hpT2 = g * a1; this.hpT3 = g * g * a1; if (!this.hpInit) { this.hp_1 = this.hpT1; this.hp_2 = this.hpT2; this.hp_3 = this.hpT3; this.hpInit = true; } }
  // flutter: narrowband roughness modulator, tied loosely to pitch
  const ffc = clamp(30 + 0.3 * this.fCur, 30, 150), fq = 1.6;
  this.flg = Math.tan(Math.PI * ffc / sr); this.flk = 1 / fq;
  this.flNorm = 1 / Math.sqrt((1 / 3) * Math.PI * (ffc / fq) / sr) * 0.5;
  this.flDepth = (e.gritAfter ? 0 : Pe.flutter) * 0.32 * (0.75 + 0.5 * (1 - (this.reg || 0)));
  // drive
  this.driveT = Pe.drive;
  // gain: level and group law; loudness model normalises the voiced part
  this.loudNorm(); this.norm += (this.normT - this.norm) * (1 - Math.exp(-dt / 0.12));
  this.noiseAT *= Math.pow(this.norm, 0.6 * (1 - Pe.whisper));
  const comp = 1;
  this.gainT = this.killFade ? 0 : dbToGain(this.levelDb) * comp * this.gainExtra * e.cal.voice / e.cal.preDrive;
  // space
  const d = this.dist;
  const dirG = 1 / (1 + 4.5 * d * d + 1.5 * d);
  const azr = this.az * Math.PI / 180, lat = Math.sin(azr), back = smooth(95, 160, Math.abs(this.az));
  const pan = (lat + 1) * Math.PI / 4;
  this.gLT = Math.cos(pan) * dirG * (1 - 0.18 * back); this.gRT = Math.sin(pan) * dirG * (1 - 0.18 * back);
  this.sendT = (0.32 + 0.5 * d) * (0.85 + 0.3 * back);
  const lpf = clamp(17000 * Math.exp(-1.9 * d) * (1 - 0.45 * back), 1800, 18000);
  this.dlpC = onePoleCoef(lpf, sr);
  this.itdT = Math.min(60, Math.abs(lat) * 0.00062 * sr);
  this.farR = lat < 0; // far ear is right when source is left
  this.shadowC = onePoleCoef(clamp(18000 - 13500 * Math.abs(lat), 2500, 18000), sr);
};

Singer.prototype.render = function (n, outL, outR, send, buf) {
  const e = this.e, pt = e.pulses, sr = this.sr;
  if (this.voicing && this.closureFirst) { this.closureFirst = false; this.closure(); }
  // ---- source
  let ph = this.ph, inc = this.inc, amp = this.amp;
  const ampK = 1 - Math.exp(-1 / (0.0015 * sr));
  let nA = this.noiseA; const nAT = this.noiseAT, nAd = (nAT - nA) / n;
  const fbase = pt.data, flow = pt.flow;
  let x = this.rng;
  let a1 = this.asp1; const aspC = 0.974; // gentle high-pass on aspiration
  let f1 = this.fl1, f2 = this.fl2; const flg = this.flg, flk = this.flk, fd = this.flDepth * this.flNorm;
  const fa1 = 1 / (1 + flg * (flg + flk)), fa2 = flg * fa1, fa3 = flg * fa2;
  const floor = this.breathFloor;
  for (let i = 0; i < n; i++) {
    x ^= x << 13; x ^= x >>> 17; x ^= x << 5; x >>>= 0;
    const w1 = x / 2147483648 - 1;
    x ^= x << 13; x ^= x >>> 17; x ^= x << 5; x >>>= 0;
    const w2 = x / 2147483648 - 1;
    // flutter modulator
    const fv3 = w2 - f2, fv1 = fa1 * f1 + fa2 * fv3, fv2 = f2 + fa2 * f1 + fa3 * fv3;
    f1 = 2 * fv1 - f1; f2 = 2 * fv2 - f2;
    const fm = 1 + fd * fv1 * flk;
    let s = 0, gateFlow = 0;
    if (this.voicing) {
      if (this.gap > 0) { this.gap--; }
      else {
        ph += inc;
        if (ph >= 1) { ph -= 1; this.ph = ph; this.closure(); inc = this.inc; if (this.gap > 0) { ph = 0; this.gap--; } }
        if (this.voicing && this.gap === 0) {
          const lev = this.lev, S = pt.sizes[lev], o = pt.base[lev];
          const fi = ph * S, i0 = fi | 0, fr = fi - i0;
          const oa = o + this.rdA * (S + 1) + i0, ob = oa + (S + 1);
          const va = fbase[oa] + fr * (fbase[oa + 1] - fbase[oa]);
          const vb = this.rdA + 1 < N_RD ? fbase[ob] + fr * (fbase[ob + 1] - fbase[ob]) : va;
          s = va + this.rdW * (vb - va);
          gateFlow = flow[this.tabRd * (FLOW_N + 1) + ((ph * FLOW_N) | 0)];
        }
      }
      amp += (this.ampT - amp) * ampK;
      s *= amp * fm;
    }
    // noise rides the flow when voiced, flows freely when the folds are apart
    nA += nAd;
    const hp = w1 - a1; a1 = w1 * (1 - aspC) + a1 * aspC;
    const g = this.voicing ? (floor + (1 - floor) * gateFlow) : 1;
    const noise = hp * nA * g * 0.35 + w2 * this.raspC * gateFlow * gateFlow * amp * 0.28;
    buf[i] = s + noise;
  }
  this.rng = x; this.ph = ph; this.amp = amp; this.noiseA = nAT; this.asp1 = a1; this.fl1 = f1; this.fl2 = f2;
  // ---- throat: parallel bank of ramped zero-delay SVFs. Each resonance is weighted by the
  // tube's own residue at that root (-2 / (f dM22/df)), so the sum converges to the full tube
  // response and the top end belongs to this throat; no correction patch.
  const nr = this.lod, inv = 1 / n, src = this.src;
  for (let i = 0; i < n; i++) { src[i] = buf[i]; buf[i] = 0; }
  for (let k = 0; k < nr; k++) {
    let c1 = this.ca1[k], c2 = this.ca2[k], c3 = this.ca3[k], ak = this.ca[k];
    const d1 = (this.ta1[k] - c1) * inv, d2 = (this.ta2[k] - c2) * inv, d3 = (this.ta3[k] - c3) * inv, da = (this.ta[k] - ak) * inv;
    let s1 = this.ic1[k], s2 = this.ic2[k];
    for (let i = 0; i < n; i++) {
      c1 += d1; c2 += d2; c3 += d3; ak += da;
      const v3 = src[i] - s2, v1 = c1 * s1 + c2 * v3, v2 = s2 + c2 * s1 + c3 * v3;
      s1 = 2 * v1 - s1; s2 = 2 * v2 - s2; buf[i] += ak * v2;
    }
    this.ic1[k] = s1 + 1e-25; this.ic2[k] = s2; this.ca1[k] = c1; this.ca2[k] = c2; this.ca3[k] = c3; this.ca[k] = ak;
  }
  // ---- high-pass (SVF, Q 0.707), ramped
  {
    let c1 = this.hp_1, c2 = this.hp_2, c3 = this.hp_3; const k = 1.41421356;
    const d1 = (this.hpT1 - c1) * inv, d2 = (this.hpT2 - c2) * inv, d3 = (this.hpT3 - c3) * inv;
    let s1 = this.hp1, s2 = this.hp2;
    for (let i = 0; i < n; i++) {
      c1 += d1; c2 += d2; c3 += d3;
      const v0 = buf[i] + 1e-18, v3 = v0 - s2, v1 = c1 * s1 + c2 * v3, v2 = s2 + c2 * s1 + c3 * v3;
      s1 = 2 * v1 - s1; s2 = 2 * v2 - s2; buf[i] = v0 - k * v1 - v2;
    }
    this.hp1 = s1; this.hp2 = s2; this.hp_1 = c1; this.hp_2 = c2; this.hp_3 = c3;
  }
  // ---- percussion (hands, feet): bypasses the throat
  if (this.perc) {
    const isClap = this.perc === 'clap', bq = this.percBq, acc = this.percAcc;
    for (let i = 0; i < n; i++) {
      const t = (this.percT + i) / sr;
      let env = 0;
      if (isClap) { for (let f = 0; f < this.flams.length; f++) { const tt = t - this.flams[f]; if (tt >= 0) env += (f === this.flams.length - 1 ? Math.exp(-tt / 0.045) : Math.exp(-tt / 0.004)) * (f === this.flams.length - 1 ? 1 : 0.6) * Math.min(1, tt / 0.0006); } }
      else env = t < 0.25 ? Math.exp(-t / 0.05) * Math.min(1, t / 0.002) : 0;
      x ^= x << 13; x ^= x >>> 17; x ^= x << 5; x >>>= 0;
      const w = x / 2147483648 - 1;
      let v = bq.tick(w * env);
      if (!isClap) { this.pcPh += TAU * (52 + 30 * Math.exp(-t / 0.03)) / sr; v = v * 2.2 + Math.sin(this.pcPh) * env * 0.9; }
      buf[i] += v * acc * (isClap ? 3.2 : 1.6);
    }
    this.rng = x;
    this.percT += n; if (this.percT > 0.4 * sr) this.perc = null;
  }
  // ---- internal level: bring the throat to a known level before the drive
  const pg = e.cal.preDrive;
  let pk = 0;
  for (let i = 0; i < n; i++) { const v = buf[i] * pg; buf[i] = v; const av = v < 0 ? -v : v; if (av > pk) pk = av; }
  if (pk > (e.pkMax || 0)) e.pkMax = pk;
  // ---- drive (antiderivative anti-aliased tanh)
  const dr = this.driveT;
  if (dr > 0.002 || this.driveOn) {
    const pre = 1 + 14 * dr * dr, post = 1 / Math.sqrt(pre);
    let xp = this.xPrev;
    const lc = (v) => { const a = Math.abs(v); return a + Math.log1p(Math.exp(-2 * a)) - LN2; };
    let lp = lc(xp);
    const fadeIn = !this.driveOn;
    for (let i = 0; i < n; i++) {
      const xi = buf[i] * pre, d = xi - xp;
      const lx = lc(xi);
      const y = Math.abs(d) < 1e-6 ? Math.tanh(0.5 * (xi + xp)) : (lx - lp) / d;
      xp = xi; lp = lx;
      buf[i] = fadeIn ? lerp(buf[i], y * post, i / n) : y * post;
    }
    this.xPrev = xp; this.driveOn = dr > 0.002;
  }
  // ---- gain and space
  let gn = this.gainCur; const gd = (this.gainT - gn) * inv;
  let gL = this.gL == null ? this.gLT : this.gL, gR = this.gR == null ? this.gRT : this.gR;
  const gLd = (this.gLT - gL) * inv, gRd = (this.gRT - gR) * inv;
  let sd = this.revS; const sdd = (this.sendT - sd) * inv;
  let lp = this.dlp, sh = this.flp; const lpc = this.dlpC, shc = this.shadowC;
  const itd = this.itd, mask = 127; let w = this.itdW;
  let dl = this.pdel; const dld = (this.itdT - dl) * inv;
  const farR = this.farR;
  let ss = 0;
  for (let i = 0; i < n; i++) {
    gn += gd; gL += gLd; gR += gRd; sd += sdd; dl += dld;
    const v = buf[i] * gn; ss += v * v;
    lp += (v + 1e-18 - lp) * lpc;
    // far ear: delayed and shadowed
    itd[w] = lp; const rp = w - dl; const ri = Math.floor(rp), rf = rp - ri;
    const dv = itd[ri & mask] * (1 - rf) + itd[(ri + 1) & mask] * rf; w = (w + 1) & mask;
    sh += (dv - sh) * shc;
    if (farR) { outL[i] += lp * gL; outR[i] += sh * gR; } else { outL[i] += sh * gL; outR[i] += lp * gR; }
    send[i] += v * sd;
  }
  this.gainCur = gn; this.gL = gL; this.gR = gR; this.revS = sd; this.dlp = lp; this.flp = sh; this.itdW = w; this.pdel = dl;
  this.outLev = Math.sqrt(ss / n);
  // ---- lifecycle: ring out, then free
  if (!this.voicing && this.p < 1e-4 && this.noiseA < 1e-5 && !this.perc && !this.gate) {
    if (this.outLev < 1e-5) this.silentBlocks++; else this.silentBlocks = 0;
    if (this.silentBlocks > 6) this.sleep();
  } else this.silentBlocks = 0;
};

/* ------------------------------------------------------------------ Room: early reflections + 8-line FDN
   Filtered input, low frequencies decay faster than mids, highs faster still, gently modulated lines. */
function Room(sr) {
  this.sr = sr;
  const base = [1153, 1327, 1559, 1801, 2063, 2297, 2539, 2861];
  this.base = base.map(v => v * sr / 48000);
  this.size = 1; this.N = 8;
  this.lines = []; for (let i = 0; i < 8; i++) this.lines.push(new Float32Array(8192));
  this.w = 0; this.lo = new Float64Array(8); this.hi = new Float64Array(8);
  this.mph = new Float64Array(8); for (let i = 0; i < 8; i++) this.mph[i] = i * 0.77;
  this.pre = new Float32Array(8192); this.pw = 0; this.idle = 0;
  this.hpIn = new Biquad(); this.hpIn2 = new Biquad();
  this.v = new Float64Array(8);
  this.set(0.5, 1.8);
}
Room.prototype.set = function (size, rt) {
  const sr = this.sr;
  this.size = 0.55 + 1.05 * size; this.rt = rt;
  this.d = this.base.map(b => Math.min(8000, b * this.size));
  this.gL = []; this.gM = []; this.gH = [];
  for (let i = 0; i < 8; i++) {
    const D = this.d[i];
    this.gL.push(Math.pow(10, -3 * D / (sr * rt * 0.45)));
    this.gM.push(Math.pow(10, -3 * D / (sr * rt)));
    this.gH.push(Math.pow(10, -3 * D / (sr * rt * 0.32)));
  }
  this.cLo = onePoleCoef(320, sr); this.cHi = onePoleCoef(3800, sr);
  this.hpIn.set('highpass', 240, 0.7, 0, sr); this.hpIn2.set('highpass', 240, 0.7, 0, sr);
  this.taps = [[0.011, 0.5, -0.2], [0.019, -0.25, 0.45], [0.027, 0.32, 0.22], [0.034, -0.18, -0.3], [0.043, 0.2, -0.16], [0.052, -0.14, 0.18]].map(t => [Math.round(t[0] * sr * this.size), t[1], t[2]]);
  this.preD = Math.round(0.012 * sr);
};
Room.prototype.process = function (inp, outL, outR, n, wet) {
  const L = this.lines, d = this.d, lo = this.lo, hi = this.hi, sr = this.sr;
  const cLo = this.cLo, cHi = this.cHi, gL = this.gL, gM = this.gM, gH = this.gH, pre = this.pre, taps = this.taps;
  if (wet < 1e-4 && this.idle > 2) return;
  // per-block modulation of the line lengths (slow, a few samples deep)
  const dStart = this.dS || (this.dS = new Float64Array(8)), dInc = this.dI || (this.dI = new Float64Array(8));
  for (let k = 0; k < 8; k++) {
    const a = d[k] + 5 * Math.sin(this.mph[k]);
    this.mph[k] += (0.11 + 0.05 * k) * TAU * n / sr;
    const b = d[k] + 5 * Math.sin(this.mph[k]);
    dStart[k] = a; dInc[k] = (b - a) / n;
  }
  const t0 = taps[0], t1 = taps[1], t2 = taps[2], t3 = taps[3], t4 = taps[4], t5 = taps[5];
  const L0 = L[0], L1 = L[1], L2 = L[2], L3 = L[3], L4 = L[4], L5 = L[5], L6 = L[6], L7 = L[7];
  const s8 = 0.35355339059327373;
  let w = this.w, pw = this.pw, energy = 0;
  const v = this.v;
  for (let i = 0; i < n; i++) {
    const x = this.hpIn2.tick(this.hpIn.tick(inp[i]));
    pre[pw] = x;
    const eL = pre[(pw - t0[0]) & 8191] * t0[1] + pre[(pw - t1[0]) & 8191] * t1[1] + pre[(pw - t2[0]) & 8191] * t2[1] + pre[(pw - t3[0]) & 8191] * t3[1] + pre[(pw - t4[0]) & 8191] * t4[1] + pre[(pw - t5[0]) & 8191] * t5[1];
    const eR = pre[(pw - t0[0]) & 8191] * t0[2] + pre[(pw - t1[0]) & 8191] * t1[2] + pre[(pw - t2[0]) & 8191] * t2[2] + pre[(pw - t3[0]) & 8191] * t3[2] + pre[(pw - t4[0]) & 8191] * t4[2] + pre[(pw - t5[0]) & 8191] * t5[2];
    const xin = pre[(pw - this.preD) & 8191];
    pw = (pw + 1) & 8191;
    for (let k = 0; k < 8; k++) {
      const rp = w - (dStart[k] + dInc[k] * i), ri = Math.floor(rp), fr = rp - ri, line = L[k];
      const a = line[ri & 8191];
      const y = a + (line[(ri + 1) & 8191] - a) * fr;
      const l = lo[k] + (y - lo[k]) * cLo; lo[k] = l;
      const rest = y - l;
      const h = hi[k] + (rest - hi[k]) * cHi; hi[k] = h;
      v[k] = l * gL[k] + h * gM[k] + (rest - h) * gH[k];
    }
    // 8-point Hadamard, unrolled
    const a0 = v[0] + v[1], a1 = v[0] - v[1], a2 = v[2] + v[3], a3 = v[2] - v[3], a4 = v[4] + v[5], a5 = v[4] - v[5], a6 = v[6] + v[7], a7 = v[6] - v[7];
    const b0 = a0 + a2, b2 = a0 - a2, b1 = a1 + a3, b3 = a1 - a3, b4 = a4 + a6, b6 = a4 - a6, b5 = a5 + a7, b7 = a5 - a7;
    const y0 = (b0 + b4) * s8, y4 = (b0 - b4) * s8, y1 = (b1 + b5) * s8, y5 = (b1 - b5) * s8, y2 = (b2 + b6) * s8, y6 = (b2 - b6) * s8, y3 = (b3 + b7) * s8, y7 = (b3 - b7) * s8;
    const xi = xin * 0.35;
    L0[w] = y0 + xi; L1[w] = y1 + xi; L2[w] = y2 + xi; L3[w] = y3 + xi; L4[w] = y4 + xi; L5[w] = y5 + xi; L6[w] = y6 + xi; L7[w] = y7 + xi;
    w = (w + 1) & 8191;
    const oL = (y0 + y2 + y4 + y6) * 0.5 + eL * 0.6, oR = (y1 + y3 + y5 + y7) * 0.5 + eR * 0.6;
    outL[i] += oL * wet; outR[i] += oR * wet;
    energy += oL * oL + x * x;
  }
  this.w = w; this.pw = pw;
  this.idle = energy < 1e-14 ? (this.idle || 0) + 1 : 0;
};

/* ------------------------------------------------------------------ Engine */
function Engine(opts) {
  opts = opts || {};
  const sr = this.sr = opts.sampleRate || 48000;
  const sh = opts.shared ? adoptShared(opts.shared) : buildShared();
  this.pulses = sh.pulses; this.grid = sh.grid;
  this.maxSingers = opts.maxSingers || 24;
  this.P = defaultParams();
  this.cal = Object.assign({ jitter: 0.87, shimmer: 0.95, pitchExp: 0, voice: 0.1743, trim: {"clean": -1.0, "weathered": -2.1, "raspy": 1.0, "chant": 0.4, "growl": 1.0, "fry": -2.4, "ayn": -0.4, "ring": 2.6, "whisper": -0.5, "small": 0.5, "kargyraa": 1.5}, lowMidTarget: 14.0, afterTrim: -6.5, preDrive: 0.25 }, opts.cal || {});
  this.ctlBlock = opts.ctlBlock || 128;
  this.singers = []; for (let i = 0; i < this.maxSingers; i++) this.singers.push(new Singer(this, i));
  this.buf = new Float64Array(512); this.dryL = new Float64Array(512); this.dryR = new Float64Array(512); this.send = new Float64Array(512);
  this.wetL = new Float64Array(512); this.wetR = new Float64Array(512);
  this.room = new Room(sr);
  this.lowSh = [new Biquad(), new Biquad()]; this.highSh = [new Biquad(), new Biquad()];
  this.lmEq = [new Biquad(), new Biquad()]; this.scLM = new Biquad(); this.scPR = new Biquad();
  this.scLM.set('bandpass', 280, 0.6, 0, sr); this.scPR.set('bandpass', 2000, 0.55, 0, sr);
  this.lmEq[0].set('bandpass', 310, 0.8, 0, sr); this.lmEq[1].set('bandpass', 310, 0.8, 0, sr);
  this.eLM = 1e-9; this.ePR = 1e-9; this.lmCut = 0; this.lmRatio = 0; this.lmActive = 0;
  this.dc = [0, 0, 0, 0];
  this.limLook = Math.round(0.0025 * sr); this.limBuf = [new Float64Array(1024), new Float64Array(1024)]; this.limW = 0;
  this.limQ = new Int32Array(1024); this.limQv = new Float64Array(1024); this.limQh = 0; this.limQt = 0; this.limG = 1; this.limGR = 0; this.limIdx = 0;
  this.time = 0; this.sharedJit = 0; this.sjT = 0; this.sjA = 0; this.sjB = 0;
  this.notes = []; this.noteSeq = 0;
  this.scene = null; this.playing = false; this.stepPos = 0; this.rep = 0;
  this.loose = { wander: 0 }; this.jitCoupling = 0.5;
  this.gritAfter = 0; this.gaPrev = [0, 0];
  this.tele = { peak: 0, rms: 0 }; this.blockCount = 0; this.focus = -1;
  this.seed = opts.seed || 17;
  this.setParams({});
}
Engine.prototype.setParams = function (o) {
  for (const k in o) if (k in this.P) this.P[k] = o[k];
  const P = this.P, sr = this.sr;
  this.lowSh[0].set('lowshelf', 240, 0.7, P.body, sr); this.lowSh[1].set('lowshelf', 240, 0.7, P.body, sr);
  this.highSh[0].set('highshelf', 2400, 0.7, P.air, sr); this.highSh[1].set('highshelf', 2400, 0.7, P.air, sr);
  this.room.set(P.room, P.decay);
  this.gritAfter = P.gritAfter > 0.5 ? 1 : 0;
  this.applyLoose(P.looseness);
  // play-mode singers follow the live parameters; their personal traits stay
  for (const s of this.singers) if (s.active && s.owner && s.owner.kind === 'note') { s.P = this.P; this.placeNoteSinger(s, s.index, s.owner.size); }
  for (const n of this.notes) n.size = n.singers.length;
};
Engine.prototype.applyLoose = function (L) {
  this.jitCoupling = 0.5 * (1 - L);
};
function looseTable(L) {
  return {
    lag: lerp(6, 116, L), slip: lerp(2, 47, L), scoop: lerp(6, 76, L), settle: lerp(0.06, 0.28, L),
    detune: lerp(2, 22, L), skip: lerp(0, 0.12, L), coupling: lerp(0.5, 0, L), vowel: lerp(0.02, 0.12, L), level: lerp(0.5, 3.5, L)
  };
}

/* ---- play mode: each key wakes a group of throats, a leader and followers */
Engine.prototype.allocate = function (count) {
  const free = [];
  for (const s of this.singers) if (!s.active && !s.owner && !s.killFade && !s.deferred) { free.push(s); if (free.length === count) return free; }
  // steal from the oldest notes, released ones first; stolen throats fade for one block first
  const order = this.notes.filter(n => n.released).concat(this.notes.filter(n => !n.released));
  for (const n of order) {
    for (const s of n.singers) { if (free.length >= count) break; if (s.owner === n && !s.killFade) { s.killFade = 1; s.owner = null; free.push(s); } }
    if (free.length >= count) break;
  }
  this.notes = this.notes.filter(n => n.singers.some(s => s.owner === n));
  return free;
};
Engine.prototype.placeNoteSinger = function (s, i, G) {
  const P = this.P, lt = looseTable(P.looseness), seed = this.seed * 131 + i * 7;
  s.L = clamp(P.size + (i === 0 ? 0 : h11(seed, 11, 0, 0) * 1.6 * P.sizeSpread), 13, 20.5);
  s.fLow = 92 * Math.pow(L_REF / s.L, 1.6);
  s.detune = i === 0 ? 0 : h11(seed, 12, 0, 0) * lt.detune;
  s.levelDb = i === 0 ? 0 : -h01(seed, 13, 0, 0) * lt.level;
  s.vowelOff = i === 0 ? 0 : h11(seed, 14, 0, 0) * lt.vowel;
  const spreadDeg = P.spread * 70;
  s.az = clamp(P.azimuth + (G > 1 ? (i / (G - 1) - 0.5) * 2 * spreadDeg : 0) + h11(seed, 15, 0, 0) * 6 * P.spread, -180, 180);
  s.dist = clamp(P.distance + h01(seed, 16, 0, 0) * 0.12 * P.spread, 0, 1);
  s.lagMs = i === 0 ? 0 : lt.lag * (0.35 + 0.65 * h01(seed, 17, 0, 0));
  s.carrier = i < 3 || G <= 3;
  s.lod = s.dist > 0.55 && i > 0 ? 6 : N_RES;
  const groupLaw = Math.pow(G, -(0.44 + 0.08 * (1 - P.looseness)));
  s.gainExtra = groupLaw * dbToGain(this.cal.trim[this.presetId] || 0);
  s.coupling = lt.coupling; s.looseWander = lt.detune * 0.3;
};
Engine.prototype.noteOn = function (midi, vel) {
  const P = this.P, G = Math.round(P.throats);
  const note = { kind: 'note', id: ++this.noteSeq, midi, singers: [], size: G, vel: vel == null ? 1 : vel };
  const ss = this.allocate(G);
  const lt = looseTable(P.looseness);
  // legato: if a single note is held, glide instead of re-attacking
  this.notes.push(note);
  ss.forEach((s, i) => {
    if (s.killFade) { s.deferred = { note, i, G, midi }; note.singers.push(s); return; }
    s.assign({ owner: note, layer: -1, role: i === 0 ? 'leader' : 'follower', index: i, params: P, seed: this.seed * 131 + i * 7, size: P.size, azimuth: P.azimuth, distance: P.distance, midi });
    this.placeNoteSinger(s, i, G);
    note.singers.push(s);
    const slip = i === 0 ? 0 : h11(this.noteSeq, i, 21, 0) * lt.slip;
    const delay = Math.max(0, (s.lagMs + slip) / 1000);
    s.pending = { at: this.time + delay, start: { level: note.vel, scoop: i === 0 ? lt.scoop * 0.3 : lt.scoop * (0.4 + 0.6 * h01(this.noteSeq, i, 22, 0)), settle: lt.settle } };
  });
  note.lt = lt; note.seq = this.noteSeq;
  this.focus = ss.length ? ss[0].slot : this.focus;
  return note.id;
};
Engine.prototype.finishSteal = function (s) {
  const d = s.deferred; const sl = s.slot; s.reset(); s.slot = sl; s.owner = null; s.events = null; s.pending = null; s.pendingStop = 0; s.deferred = null;
  if (!d) return;
  const note = d.note, P = this.P, lt = note.lt || looseTable(P.looseness), i = d.i;
  s.assign({ owner: note, layer: -1, role: i === 0 ? 'leader' : 'follower', index: i, params: P, seed: this.seed * 131 + i * 7, size: P.size, azimuth: P.azimuth, distance: P.distance, midi: d.midi });
  this.placeNoteSinger(s, i, d.G);
  const slip = i === 0 ? 0 : h11(note.seq || 0, i, 21, 0) * lt.slip;
  s.pending = { at: this.time + Math.max(0, (s.lagMs + slip) / 1000), start: { level: note.vel, scoop: lt.scoop * 0.5, settle: lt.settle } };
  if (note.released) s.pending.stopAt = s.pending.at + 0.05;
};
Engine.prototype.noteOff = function (midi) {
  for (const n of this.notes) if (n.midi === midi && !n.released) {
    n.released = true;
    for (const s of n.singers) if (s.owner === n) {
      const lag = s.index === 0 ? 0 : s.lagMs * 0.6 / 1000;
      if (s.pending) { s.pending.stopAt = this.time + lag + 0.03; } else s.pendingStop = this.time + lag;
    }
  }
};
Engine.prototype.allOff = function () { for (const n of this.notes) this.noteOff(n.midi); };
Engine.prototype.panic = function () { for (const s of this.singers) { const sl = s.slot; s.reset(); s.slot = sl; s.owner = null; s.pending = null; s.pendingStop = 0; s.events = null; } this.notes = []; };

/* ---- chant: layers of singers playing gesture patterns */
Engine.prototype.setScene = function (scene) {
  // free chant singers
  for (const s of this.singers) if (s.owner && s.owner.kind === 'layer') { const sl = s.slot; s.reset(); s.slot = sl; s.owner = null; s.events = null; }
  this.scene = scene ? JSON.parse(JSON.stringify(scene)) : null;
  this.layers = [];
  if (!this.scene) return;
  if (this.scene.tempo) this.P.tempo = this.scene.tempo;
  this.scene.layers.forEach((L, li) => this.buildLayer(li));
  this.stepPos = 0; this.rep = 0; this.stepIndex = 0; this.approachT = 0;
  this.nextStep = this.time + 0.05; this.stepQ = []; this.curStep = null;
};
Engine.prototype.buildLayer = function (li) {
  const L = this.scene.layers[li];
  const old = this.layers[li];
  if (old) for (const s of old.singers) if (s.owner === old) { const sl = s.slot; s.reset(); s.slot = sl; s.owner = null; s.events = null; }
  const preset = PRESETS.find(p => p.id === L.preset) || PRESETS[0];
  const params = Object.assign(defaultParams(), preset.p, L.override || {});
  const layer = { kind: 'layer', li, def: L, singers: [], params, preset: preset.id };
  this.layers[li] = layer;
  const lt = looseTable(L.looseness);
  const count = Math.max(0, L.mute ? 0 : L.singers);
  let used = 0; for (const s of this.singers) if (s.active || s.owner) used++;
  const ss = [];
  for (const s of this.singers) { if (ss.length >= count) break; if (!s.active && !s.owner) ss.push(s); }
  ss.forEach((s, i) => {
    const seed = hash(this.seed, li, i, 77);
    const size = lerp(L.sizeLo, L.sizeHi, count > 1 ? (h01(seed, 1, 0, 0) * 0.6 + (i / (count - 1)) * 0.4) : 0.5);
    s.assign({ owner: layer, layer: li, role: i === 0 ? 'leader' : 'follower', index: i, params, seed, size, azimuth: 0, distance: L.distance, midi: L.midi });
    s.active = false; // sleeps until its first syllable
    s.detune = i === 0 ? 0 : h11(seed, 2, 0, 0) * lt.detune;
    s.levelDb = (i === 0 ? 0 : -h01(seed, 3, 0, 0) * lt.level) + (L.gain || 0);
    s.vowelOff = i === 0 ? 0 : h11(seed, 4, 0, 0) * lt.vowel;
    s.lagMs = i === 0 ? 0 : lt.lag * (0.35 + 0.65 * h01(seed, 5, 0, 0));
    const spreadDeg = (L.spread || 0) * 80;
    s.azBase = (count > 1 ? (i / (count - 1) - 0.5) * 2 * spreadDeg : 0) + h11(seed, 6, 0, 0) * 8 * (L.spread || 0);
    s.az = this.wrapAz(L.azimuth + s.azBase);
    s.distOff = h01(seed, 7, 0, 0) * 0.1 * (L.spread || 0);
    s.dist = clamp(L.distance + s.distOff, 0, 1);
    s.carrier = i < 3 || count <= 3;
    s.lod = (s.dist > 0.55 && i > 0) || i >= 8 ? 6 : N_RES;
    s.gainExtra = Math.pow(Math.max(1, count), -(0.44 + 0.08 * (1 - L.looseness))) * dbToGain(this.cal.trim[preset.id] || 0) * dbToGain(this.scene.trim || 0);
    s.coupling = lt.coupling; s.looseWander = lt.detune * 0.3;
    s.events = []; s.lastGain = L.gain || 0;
    layer.singers.push(s);
  });
};
Engine.prototype.wrapAz = function (a) { a = ((a + 180) % 360 + 360) % 360 - 180; return a; };
Engine.prototype.setLayer = function (li, patch) {
  if (!this.scene || !this.scene.layers[li]) return;
  const L = this.scene.layers[li];
  const rebuild = ('singers' in patch) || ('preset' in patch) || ('mute' in patch) || ('sizeLo' in patch) || ('sizeHi' in patch) || ('looseness' in patch);
  Object.assign(L, patch);
  if (rebuild) this.buildLayer(li);
  else {
    const layer = this.layers[li];
    for (const s of layer.singers) {
      s.dist = clamp(L.distance + (s.distOff || 0), 0, 1); s.az = this.wrapAz(L.azimuth + (s.azBase || 0));
      s.levelDb = (s.index === 0 ? 0 : s.levelDb - (s.lastGain || 0)) + (L.gain || 0); s.lastGain = L.gain || 0;
      if ('midi' in patch) { s.midi = L.midi; s.baseHz = 440 * Math.pow(2, (L.midi - 69) / 12); }
    }
  }
};
Engine.prototype.setEvents = function (li, events) { if (this.scene && this.scene.layers[li]) this.scene.layers[li].events = events; };
Engine.prototype.transport = function (on) {
  if (on && !this.playing) { this.playing = true; this.stepIndex = 0; this.nextStep = this.time + 0.05; this.rep = 0; this.approachT = 0; }
  if (!on && this.playing) { this.playing = false; this.stepQ = []; this.curStep = null; for (const l of this.layers || []) for (const s of l.singers) { s.events = []; if (s.gate) s.stop(); } }
};
Engine.prototype.schedule = function () {
  if (!this.playing || !this.scene) return;
  const stepDur = 60 / this.P.tempo / 4;
  const look = 0.16;
  const totalSteps = 16 * (this.scene.bars || 1);
  while (this.nextStep < this.time + look) {
    const st = this.stepIndex % totalSteps;
    const rep = Math.floor(this.stepIndex / totalSteps);
    const swing = (st % 2 === 1) ? this.P.swing * stepDur * 0.5 : 0;
    const t0 = this.nextStep + swing;
    this.scene.layers.forEach((L, li) => {
      const layer = this.layers[li]; if (!layer || L.mute) return;
      const lt = looseTable(L.looseness);
      for (const ev of L.events) {
        if (ev[0] !== st) continue;
        const g = GESTURES[ev[1]]; if (!g) continue;
        layer.singers.forEach((s, i) => {
          if (g.who === 'leader' && i !== 0) return;
          if (g.who === 'followers' && i === 0 && layer.singers.length > 1) return;
          const hs = hash(this.seed, li * 997 + i, rep, st);
          let off = s.lagMs / 1000 + (i === 0 ? 0.3 : 1) * h11(hs, 1, 0, 0) * lt.slip / 1000;
          if (L.timing === 'free') off += h11(hs, 2, 0, 0) * stepDur * (1.2 + 2 * L.looseness) + (i === 0 ? 0 : h01(hs, 3, 0, 0) * stepDur);
          const at = Math.max(this.time, t0 + Math.max(0, off));
          const skip = i > 0 && !g.kind && h01(hs, 4, 0, 0) < lt.skip;
          s.events.push({ at, g: skip ? GESTURES.breath : g, gname: skip ? 'breath' : ev[1], dur: (skip ? 1.5 : ev[2]) * stepDur, acc: skip ? 0.35 : ev[3] * (1 - 0.15 * h01(hs, 5, 0, 0) * L.looseness), semis: ev[4], scoop: (i === 0 ? 0.4 : 1) * lt.scoop * h01(hs, 6, 0, 0), settle: lt.settle });
        });
      }
    });
    (this.stepQ || (this.stepQ = [])).push([t0, st]);
    this.stepIndex++; this.nextStep += stepDur;
  }
};

Engine.prototype.process = function (outL, outR, nTotal) {
  let off = 0;
  while (off < nTotal) {
    const n = Math.min(this.ctlBlock, nTotal - off);
    this.block(outL, outR, off, n);
    off += n;
  }
};
Engine.prototype.block = function (outL, outR, off, n) {
  const sr = this.sr, P = this.P;
  const dt = n / sr;
  this.schedule();
  // shared jitter source (piecewise-linear noise near cycle rate)
  this.sjT += dt; if (this.sjT > 0.008) { this.sjT = 0; this.sjA = this.sjB; this.sjN = hash(this.sjN || 1, 5, 9, 1); this.sjB = (h01(this.sjN, 1, 0, 0) + h01(this.sjN, 2, 0, 0) + h01(this.sjN, 3, 0, 0) + h01(this.sjN, 4, 0, 0) - 2) * 1.732; }
  this.sharedJit = lerp(this.sjA, this.sjB, this.sjT / 0.008);
  // approach (layers that come closer)
  if (this.playing && this.scene) {
    this.approachT += dt;
    this.scene.layers.forEach((L, li) => {
      if (!L.approach || !this.layers[li]) return;
      const k = clamp(this.approachT / (40 * (1.05 - L.approach)), 0, 1);
      for (const s of this.layers[li].singers) s.dist = clamp((L.distance + (s.distOff || 0)) * (1 - 0.85 * k), 0, 1);
    });
  }
  const dryL = this.dryL, dryR = this.dryR, send = this.send, buf = this.buf;
  for (let i = 0; i < n; i++) { dryL[i] = 0; dryR[i] = 0; send[i] = 0; }
  let activeCount = 0;
  for (const s of this.singers) {
    // pending starts and stops (play mode)
    if (s.pending && this.time >= s.pending.at) { const st = s.pending; s.pending = null; s.start(st.start); if (st.stopAt) s.pendingStop = st.stopAt; }
    if (s.pendingStop && this.time >= s.pendingStop) { s.pendingStop = 0; s.stop(); }
    // chant events
    if (s.events && s.events.length) {
      for (let j = 0; j < s.events.length; j++) {
        const ev = s.events[j];
        if (ev.at <= this.time + dt) {
          if (ev.g.kind) s.startPerc(ev.g.kind, ev.acc);
          else s.start({ gesture: ev.g, dur: ev.dur * sr, accent: ev.acc, semis: ev.semis, style: ev.g.style, scoop: ev.scoop, settle: ev.settle, level: 1 });
          s.events.splice(j, 1); j--;
        }
      }
    }
    if (!s.active) { if (s.deferred) this.finishSteal(s); continue; }
    activeCount++;
    s.control(n);
    s.render(n, dryL, dryR, send, buf);
    if (s.killFade) this.finishSteal(s);
  }
  this.activeCount = activeCount;
  // room
  const wL = this.wetL, wR = this.wetR;
  for (let i = 0; i < n; i++) { wL[i] = 0; wR[i] = 0; }
  this.room.process(send, wL, wR, n, P.wet * 1.4);
  // bus: tone, anti-mud safety net, DC block, level, limiter
  const master = dbToGain(P.level) * (this.scene && this.playing ? dbToGain(P.chantLevel) : 1);
  const lmA = 1 - Math.exp(-1 / (0.35 * sr));
  let eLM = this.eLM, ePR = this.ePR;
  const lsh = this.lowSh, hsh = this.highSh, lmq = this.lmEq;
  let lmc = this.lmC || 0; const lmcT = 1 - Math.pow(10, -this.lmCut / 20), lmcD = (lmcT - lmc) / n;
  const gaTrim = dbToGain(this.cal.afterTrim);
  const ga = this.gritAfter, gaPre = 2.2 + 6 * (P.growl + P.rasp + P.shimmer / 12 + P.jitter / 3 + P.creak) / 3;
  for (let i = 0; i < n; i++) {
    let l = dryL[i] + wL[i], r = dryR[i] + wR[i];
    if (ga) { l = Math.tanh(l * gaPre) / Math.sqrt(gaPre) * gaTrim; r = Math.tanh(r * gaPre) / Math.sqrt(gaPre) * gaTrim; }
    l = hsh[0].tick(lsh[0].tick(l)); r = hsh[1].tick(lsh[1].tick(r));
    const m = 0.5 * (l + r);
    const a = this.scLM.tick(m), b = this.scPR.tick(m);
    eLM += (a * a - eLM) * lmA; ePR += (b * b - ePR) * lmA;
    lmc += lmcD; l -= lmc * lmq[0].tick(l); r -= lmc * lmq[1].tick(r);
    // DC blocker
    const dl = l - this.dc[0] + 0.9995 * this.dc[1]; this.dc[0] = l; this.dc[1] = dl;
    const dr = r - this.dc[2] + 0.9995 * this.dc[3]; this.dc[2] = r; this.dc[3] = dr;
    dryL[i] = dl * master; dryR[i] = dr * master;
  }
  this.eLM = eLM; this.ePR = ePR; this.lmC = lmc;
  const ratio = 10 * Math.log10((this.eLM + 1e-12) / (this.ePR + 1e-12));
  this.lmRatio = ratio;
  const over = ratio - this.cal.lowMidTarget;
  const cutT = over > 0 && this.eLM > 1e-8 ? Math.min(6, over * 0.6) : 0;
  this.lmCut += (cutT - this.lmCut) * (1 - Math.exp(-dt / 0.4));
  this.lmActive = this.lmCut > 0.5 ? 1 : 0;
  if (cutT === 0 && this.lmCut < 0.02) this.lmCut = 0;
  // look-ahead limiter at -1 dBFS
  const ceil = 0.891, La = this.limLook, BL = this.limBuf[0], BR = this.limBuf[1];
  const rel = 1 - Math.exp(-1 / (0.08 * sr)), att = 1 - Math.exp(-1 / (La * 0.25));
  let peak = 0, ss = 0, gr = 1;
  for (let i = 0; i < n; i++) {
    const l = dryL[i], r = dryR[i];
    const need = Math.min(1, ceil / (Math.max(Math.abs(l), Math.abs(r)) + 1e-12));
    // monotonic queue of minimum gain over the look-ahead window
    const idx = this.limIdx++;
    while (this.limQt > this.limQh && this.limQv[(this.limQt - 1) & 1023] >= need) this.limQt--;
    this.limQ[this.limQt & 1023] = idx; this.limQv[this.limQt & 1023] = need; this.limQt++;
    while (this.limQ[this.limQh & 1023] <= idx - La) this.limQh++;
    const target = this.limQv[this.limQh & 1023];
    this.limG += (target - this.limG) * (target < this.limG ? att : rel);
    const w = this.limW, rd = (w - La + 1024) & 1023;
    BL[w] = l; BR[w] = r; this.limW = (w + 1) & 1023;
    let ol = BL[rd] * this.limG, or = BR[rd] * this.limG;
    if (ol > ceil) ol = ceil; else if (ol < -ceil) ol = -ceil;
    if (or > ceil) or = ceil; else if (or < -ceil) or = -ceil;
    outL[off + i] = ol; outR[off + i] = or;
    const pk = Math.max(Math.abs(ol), Math.abs(or)); if (pk > peak) peak = pk; ss += ol * ol + or * or;
    if (this.limG < gr) gr = this.limG;
  }
  this.limGR = 20 * Math.log10(gr);
  this.tele.peak = Math.max(this.tele.peak * 0.9, peak); this.tele.rms = Math.sqrt(ss / (2 * n));
  if (this.stepQ) while (this.stepQ.length && this.stepQ[0][0] <= this.time) this.curStep = this.stepQ.shift()[1];
  this.time += dt; this.blockCount++;
};

// Summary for the interface, about 30 times a second.
Engine.prototype.telemetry = function () {
  const ss = [];
  let focus = null;
  for (const s of this.singers) {
    if (!s.owner && !s.active) continue;
    ss.push({ slot: s.slot, a: s.active ? 1 : 0, layer: s.layer, role: s.role === 'leader' ? 1 : 0, idx: s.index, lev: +(s.outLev || 0).toFixed(5), f: +s.fCur.toFixed(2), L: +s.L.toFixed(2), az: +s.az.toFixed(1), d: +s.dist.toFixed(3), lag: +(s.lagMs || 0).toFixed(1), det: +(s.detune || 0).toFixed(1), V: +(s.V || 0).toFixed(3), ph: +(s.ph || 0).toFixed(3), lod: s.lod });
  }
  let fs = this.singers[this.focus];
  if (!fs || !fs.active) fs = this.singers.find(s => s.active && s.role === 'leader') || this.singers.find(s => s.active) || null;
  if (fs) {
    // source statistics from the cycles actually generated
    const N = Math.min(fs.cycN, 64); let jsum = 0, ssum = 0, tsum = 0, asum = 0, cnt = 0;
    const cyc = fs.cyc, kinds = [];
    for (let j = 1; j < N; j++) {
      const k0 = ((fs.cycN - j) % 64) * 3, k1 = ((fs.cycN - j - 1) % 64) * 3;
      if (cyc[k0 + 1] <= 0 || cyc[k1 + 1] <= 0) continue;
      jsum += Math.abs(cyc[k0] - cyc[k1]); tsum += cyc[k0];
      ssum += Math.abs(cyc[k0 + 1] - cyc[k1 + 1]); asum += cyc[k0 + 1]; cnt++;
    }
    for (let j = 1; j <= Math.min(N, 40); j++) { const k = ((fs.cycN - j) % 64) * 3; kinds.push([+cyc[k].toFixed(2), +cyc[k + 1].toFixed(3), cyc[k + 2]]); }
    focus = { slot: fs.slot, F: Array.from(fs.F).slice(0, fs.lod).map(v => Math.round(v)), B: Array.from(fs.B).slice(0, fs.lod).map(v => Math.round(v)), rd: +(fs.rdNow || 0).toFixed(3), f: +fs.fCur.toFixed(2), L: fs.L, vowel: fs.vowelNow, mouth: fs.mouthNow, pharynx: fs.Peff ? fs.Peff.pharynx : 0, ring: fs.Peff ? fs.Peff.ring : 0, jit: cnt ? jsum / cnt / (tsum / cnt) * 100 : 0, shim: cnt ? ssum / cnt / (asum / cnt) * 100 : 0, cycles: kinds, V: fs.V, reg: fs.reg || 0 };
  }
  return { t: this.time, singers: ss, focus, bus: { lm: +this.lmRatio.toFixed(2), cut: +this.lmCut.toFixed(2), gr: +this.limGR.toFixed(2), peak: +this.tele.peak.toFixed(4), rms: +this.tele.rms.toFixed(5) }, active: this.activeCount, step: this.playing && this.scene ? (this.curStep == null ? -1 : this.curStep) : -1, playing: this.playing };
};

// Message interface for the worklet port.
Engine.prototype.message = function (m) {
  switch (m.type) {
    case 'params': if (m.presetId !== undefined) this.presetId = m.presetId; this.setParams(m.params || {}); break;
    case 'noteOn': this.noteOn(m.midi, m.vel); break;
    case 'noteOff': this.noteOff(m.midi); break;
    case 'allOff': this.allOff(); break;
    case 'panic': this.panic(); break;
    case 'scene': this.setScene(m.scene); break;
    case 'layer': this.setLayer(m.li, m.patch); break;
    case 'events': this.setEvents(m.li, m.events); break;
    case 'transport': this.transport(m.on); break;
    case 'focus': this.focus = m.slot; break;
    case 'focusLayer': { const l = this.layers && this.layers[m.li]; if (l && l.singers[0]) this.focus = l.singers[0].slot; break; }
    case 'cal': Object.assign(this.cal, m.cal); break;
  }
};

const Core = {
  VERSION, Engine, buildShared, adoptShared, buildPulseTables, buildTubeGrid, areaFunction, tubeResonances, gridLookup, bandwidth,
  lfParams, lfSample, PRESETS, SCENES, GESTURES, GESTURE_ORDER, PARAM_DEFS, defaultParams, looseTable, VOWEL_NAMES,
  consts: { RD_MIN, RD_MAX, N_RD, N_LEV, N_RES, TUBE_NS, L_REF, GRID }, util: { clamp, lerp, smooth, hash, h01, fft }
};
if (typeof module !== 'undefined' && module.exports) module.exports = Core;
G.GutturCore = Core;
})(typeof globalThis !== 'undefined' ? globalThis : this);

class GutturProcessor extends AudioWorkletProcessor {
  constructor(o) { super(); const po = (o && o.processorOptions) || {};
    this.eng = new GutturCore.Engine({ sampleRate: sampleRate, shared: po.shared }); this.k = 0;
    this.port.onmessage = e => { try { this.eng.message(e.data); } catch (err) { this.port.postMessage({ type: 'err', msg: String(err && err.message || err) }); } }; }
  process(inp, out) { const o = out[0]; const L = o[0], R = o[1] || o[0];
    try { this.eng.process(L, R, L.length); } catch (err) { if (!this.errSent) { this.errSent = 1; this.port.postMessage({ type: 'err', msg: String(err && err.message || err) }); } }
    if (++this.k % 10 === 0) this.port.postMessage({ type: 'tele', t: this.eng.telemetry() });
    return true; }
}
registerProcessor('guttur', GutturProcessor);