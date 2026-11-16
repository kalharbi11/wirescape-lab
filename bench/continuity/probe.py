# SPDX-License-Identifier: GPL-3.0-only
"""The probe patch and the edit list of proposals/0005 section 4 (T0.13b, #100).

Bus channels (one witness each; see DESIGN.md):
  0 tone 1 kHz      VCO 1 -> Output 2                          never edited
  1 slip tone 10 Hz VCO 3 -> Output 4                          never edited
  2 tail            clock 8 -> function env 7 -> VCA 6 (noise 5) -> delay 9 -> Output 10
  3 held note       keyboard 11 -> VCO 12 / ADSR 13 -> VCA 14 -> Output 15 (noteOn before the edit)
  4 clock           clock 16 -> function env 17 -> VCA 18 (VCO 19, 2 kHz) -> Output 20
  5 subject         VCO 50 (330 Hz, modulated by VCO 52 at 0.05) -> Output 51
  6 subject 2       VCO 54 (550 Hz) -> Output 55
  7 groove voice    clock 16 -> Groove 60 t1_notes -> VCO 61 -> Output 62
  8 spare output    Output 56, unfed
Unrouted spares: VCO 90; midi.cc_to_cv 71; osc.in 70 (loopback, port PORT).
"""
from __future__ import annotations

import copy

OSC_PORT = 47913  # loopback only; a busy port leaves the route inactive, not the patch refused


def sig(a, ap, b, bp):
    return {'kind': 'signal', 'from': {'module': a, 'port': ap}, 'to': {'module': b, 'port': bp}}


def ev(a, ap, b, bp):
    return {'kind': 'event', 'from': {'module': a, 'port': ap}, 'to': {'module': b, 'port': bp}}


def mod(a, ap, b, param, amount):
    return {'kind': 'modulation', 'from': {'module': a, 'port': ap}, 'to': {'module': b, 'port': param},
            'amount': amount}


GROOVE = {'version': 2, 'bpm': 120, 'tracks': [{'length': 16, 'div': 1, 'armed': True, 'steps': [
    {'kind': 'note', 'key': 60, 'velocity': 0.9, 'gate': 0.5}, {'kind': 'rest'},
    {'kind': 'note', 'key': 67, 'velocity': 0.9, 'gate': 0.5}, {'kind': 'rest'}]}]}


def base() -> dict:
    m = lambda i, t, **p: {'id': i, 'module': t, **({'parameters': p} if p else {})}
    modules = [
        m(1, 'essentials.vco', frequency=1000), m(2, 'essentials.output'),
        m(3, 'essentials.vco', frequency=10), m(4, 'essentials.output'),
        m(5, 'essentials.noise', level=0.5), m(6, 'essentials.vca', gain=1),
        m(7, 'essentials.function_envelope', rise=0.0001, fall=0.01),
        m(8, 'essentials.clock', bpm=20, duty=0.05),
        m(9, 'fx.delay', time=0.25, feedback=0.9, mix=1.0), m(10, 'essentials.output'),
        m(11, 'host.keyboard'), m(12, 'essentials.vco'),
        m(13, 'essentials.adsr', attack=0.005, decay=0.05, sustain=0.7, release=0.2),
        m(14, 'essentials.vca', gain=1), m(15, 'essentials.output'),
        m(16, 'essentials.clock', bpm=240, duty=0.1),
        m(17, 'essentials.function_envelope', rise=0.0001, fall=0.02),
        m(18, 'essentials.vca', gain=1), m(19, 'essentials.vco', frequency=2000), m(20, 'essentials.output'),
        m(50, 'essentials.vco', frequency=330), m(51, 'essentials.output'),
        m(52, 'essentials.vco', frequency=2), m(54, 'essentials.vco', frequency=550),
        m(55, 'essentials.output'), m(56, 'essentials.output'),
        {**m(60, 'sequencing.groove', run=1), 'config': copy.deepcopy(GROOVE)},
        m(61, 'essentials.vco'), m(62, 'essentials.output'),
        {'id': 70, 'module': 'osc.in', 'config': {'version': 1, 'port': OSC_PORT,
                                                  'rows': [{'pattern': '/probe/a', 'kind': 'cv'}]}},
        {'id': 71, 'module': 'midi.cc_to_cv', 'config': {'rows': [{'channel': 0, 'controller': 21}]}},
        m(90, 'essentials.vco', frequency=777),
    ]
    connections = [
        sig(1, 'audio', 2, 'audio'), sig(3, 'audio', 4, 'audio'),
        sig(5, 'audio', 6, 'audio'), sig(8, 'clock', 7, 'gate'), sig(7, 'envelope', 6, 'gain_cv'),
        sig(6, 'audio', 9, 'left'), sig(9, 'left', 10, 'audio'),
        sig(11, 'pitch', 12, 'pitch'), sig(11, 'gate', 13, 'gate'), sig(12, 'audio', 14, 'audio'),
        sig(13, 'envelope', 14, 'gain_cv'), sig(14, 'audio', 15, 'audio'),
        sig(16, 'clock', 17, 'gate'), sig(17, 'envelope', 18, 'gain_cv'), sig(19, 'audio', 18, 'audio'),
        sig(18, 'audio', 20, 'audio'),
        sig(50, 'audio', 51, 'audio'), mod(52, 'audio', 50, 'frequency', 0.05),
        sig(54, 'audio', 55, 'audio'),
        sig(16, 'clock', 60, 'clock'), ev(60, 't1_notes', 61, 'notes'), sig(61, 'audio', 62, 'audio'),
    ]
    out = lambda mod_id, ch: {'module': mod_id, 'port': 'audio', 'bus_channel': ch}
    outputs = [out(2, 0), out(4, 1), out(10, 2), out(15, 3), out(20, 4), out(51, 5), out(55, 6),
               out(62, 7), out(56, 8)]
    return {'format': 'wirescape.native.patch', 'version': 2, 'modules': modules,
            'connections': connections, 'outputs': outputs}


WITNESS = {0: 'tone', 1: 'slip_tone', 2: 'tail', 3: 'held_note', 4: 'clock'}
TONE_HZ, SLIP_HZ = 1000.0, 10.0
# Which earlier mark each witness's no-edit reference is aligned on (R7: shared earlier commands).
# All use `load`: every oscillator's phase runs from the load, and by the steady region the held
# note is at its constant sustain, so its samples match exactly on the load mark; on the `note` mark
# they would differ whenever load-to-note spacing differs between runs (a measured 0.21 residual).
ALIGN_ON = {c: 'load' for c in range(16)}


def _without(patch, module_id):
    p = copy.deepcopy(patch)
    p['modules'] = [m for m in p['modules'] if m['id'] != module_id]
    p['connections'] = [c for c in p['connections']
                        if module_id not in (c['from']['module'], c['to']['module'])]
    return p


def _module(patch, module_id):
    return next(m for m in patch['modules'] if m['id'] == module_id)


def _variant(change):
    p = base()
    change(p)
    return p


def edits() -> list[dict]:
    """Each edit: name, command (method, payload), subject bus channel or None, optional setup patch."""
    B = base()
    groove_steps = lambda p: _module(p, 60)['config']['tracks'][0]['steps'].__setitem__(
        1, {'kind': 'note', 'key': 64, 'velocity': 0.9, 'gate': 0.5})
    groove_length = lambda p: _module(p, 60)['config']['tracks'][0].__setitem__('length', 8)
    voices = lambda p: _module(p, 11).setdefault('parameters', {}).__setitem__('voices', 4)
    osc_row = lambda p: _module(p, 70)['config']['rows'][0].__setitem__('pattern', '/probe/b')
    param = lambda p: _module(p, 50)['parameters'].__setitem__('frequency', 440)
    return [
        dict(name='addModule unconnected', cmd=('addModule', dict(moduleId=91, moduleType='essentials.vco')),
             subject=None),
        dict(name='removeModule unconnected', cmd=('removeModule', dict(moduleId=90)), subject=None),
        dict(name='removeModule connected', cmd=('removeModule', dict(moduleId=50)), subject=5),
        dict(name='connect signal', cmd=('connect', dict(connection=sig(90, 'audio', 56, 'audio'))), subject=8),
        dict(name='disconnect signal', cmd=('disconnect', dict(connection=sig(50, 'audio', 51, 'audio'))),
             subject=5),
        dict(name='connect event', cmd=('connect', dict(connection=ev(11, 'notes', 54, 'notes'))), subject=6),
        dict(name='disconnect event', cmd=('disconnect', dict(connection=ev(60, 't1_notes', 61, 'notes'))),
             subject=7),
        dict(name='connect modulation', cmd=('connect', dict(connection=mod(52, 'audio', 54, 'frequency', 0.1))),
             subject=6),
        dict(name='disconnect modulation',
             cmd=('disconnect', dict(connection=mod(52, 'audio', 50, 'frequency', 0.05))), subject=5),
        dict(name='setModAmount', cmd=('setModAmount', dict(connection=mod(52, 'audio', 50, 'frequency', 0.05),
                                                            amount=0.2)), subject=5),
        dict(name='ccMap.set', cmd=('ccMap.set', dict(moduleId=71, row=0,
                                                      mapping=dict(channel=0, controller=22))), subject=None),
        dict(name='loadGraph identical', cmd=('loadGraph', dict(patch=B)), subject=5),
        dict(name='loadGraph Groove steps', cmd=('loadGraph', dict(patch=_variant(groove_steps))), subject=7),
        dict(name='loadGraph Groove length', cmd=('loadGraph', dict(patch=_variant(groove_length))), subject=7),
        dict(name='loadGraph voice count', cmd=('loadGraph', dict(patch=_variant(voices))), subject=3),
        dict(name='loadGraph OSC In row', cmd=('loadGraph', dict(patch=_variant(osc_row))), subject=None),
        dict(name='loadGraph one parameter', cmd=('loadGraph', dict(patch=_variant(param))), subject=5),
        dict(name='loadGraph deleted module', cmd=('loadGraph', dict(patch=_without(B, 90))), subject=None),
        dict(name='loadGraph restored module', cmd=('loadGraph', dict(patch=B)), subject=None,
             setup=_without(B, 90)),
        dict(name='setBufferFrames', cmd=('setBufferFrames', dict(frames=128)), subject=None),
        dict(name='panic', cmd=('panic', {}), subject=3),
    ]


# Rows listed so their absence is explicit, not silent (applyGraph lands with M2 E1).
UNSUPPORTED = [dict(name=f'applyGraph {k}', reason='applyGraph is not implemented before M2 E1')
               for k in ('identical', 'Groove steps', 'Groove length', 'voice count', 'OSC In row',
                         'one parameter', 'deleted module', 'restored module')]
