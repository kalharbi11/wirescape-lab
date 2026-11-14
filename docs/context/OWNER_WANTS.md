<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Owner wants and direction (working notes)

**Status:** raw notes, collected by Keel from the owner's messages. Not formatted, not consolidated, not a plan.
Before Fable starts, these get reorganised into the brief. They say what I want and what matters to me,
never how to build it: the infrastructure decisions are Fable's to make, and they may differ from how
things are done today.

---

## Why this lab exists
- I want a big-level review, restructuring and infrastructure pass over the whole app: efficiency, sound
  engine quality, integration, compatibility, organisation and setup.
- I want infrastructure and protocols that make future modules and features easy, including ones that
  don't exist yet.
- I want the old decisions reconsidered, not inherited. The context docs explain why things are the way
  they are so they can be judged, not so they're kept.
- I want things tested objectively: measured before and after, compared with other tools, with facts kept
  separate from opinions.
- I don't want Fable working on agent workflows or process; I'll research that separately later.
- This app won't be public for a while. It will go through a lot of testing by me first. But it should be
  built as if outside developers will use it.

## The engine and the core
- I want one clean engine. The leftovers of the first engine (ABI1) and of Qt shouldn't shape the design.
- I want the sound engine's quality looked at seriously: aliasing, clicks, zipper noise, smoothing, stability,
  denormals, CPU per voice.
- I want edits while playing to never restart the patch (today any config edit, undo or Groove edit reloads
  everything and resets phases, tails, envelopes, held notes, sequencer position).
- I want performance measured and new targets set with real numbers, on the Pi 5 first, then Windows.
- Pi 5 is the first target. Windows second. Module DSP stays portable (plugins, Daisy-class hardware).

## Modules: anyone can build one
- I want someone to be able to develop a module on their own, add it to their cloned repo by following
  simple instructions, and build and test it **without changing core files**.
- If a module has to be registered in a list somewhere, that's fine as long as a guide explains it. Better
  still might be a script that finds new modules and adds them automatically.
- I want a script that checks whether a module someone built passes the tests, where each error says what's
  wrong and what needs adjusting.
- I want the module format cleaner and shorter, especially for the basic modules, so they adapt easily to
  other targets (plugins, Daisy-class hardware, a future compiler). The plan already says module DSP should
  move unchanged into plugins and Daisy; I want the format to actually make that true and easy.
- I want someone (a person or an agent) to be able to read this repo, design a module outside it and build,
  test and use it locally, with no hidden repo-only steps.
- None of this has to be built now. It has to be considered while the engine and protocols are rebuilt.

## Ecosystem and portability
- I want Wirescape to be easy to target for other open-source projects and developers. If someone is making
  a synth and wants it on several platforms, Wirescape should be an easy place to implement it.
- **Auto-compiler (future, no AI):** someone builds a patch in Wirescape, maybe limited to basic or restricted
  modules, and a deterministic compiler turns it into firmware or code for another platform, starting with
  the Daisy Seed.
- **Build page (future):** load a patch, drop in buttons, knobs, sliders and trigs, wire each floating control
  to a parameter and number it, to map out an instrument's physical interface. Example: a synth voice with
  6 knobs → pick "Daisy Seed" → compile → each knob gets a pin number, plus a breadboarding/wiring guide.
- It can be very strict and simple at first. What matters now is that the module format and the basic modules
  don't block it.
- I want this platform to be very friendly to physical computing beginners and the DIY community, and to make
  their processes simpler.
- I want core paths (compile, map, test, build) to be deterministic tools anyone can run, relying less on AI.
- OSC Out to a microcontroller (ESP32) already exists for the Pi; physical-computing integration matters to me.

## Special modules and module categories
- **CHAOS and Macro Oscillator (Plaits port) are special modules, not standard ones.** They're ports of
  other projects' designs (Macro from Mutable Instruments Plaits; CHAOS, see `docs/design/ports/`). They're
  important for studying what the app can host, because I want many different open-source projects, and
  anyone developing for this app, to find it easy to bring their work in.
- The point of the complex modules isn't those modules themselves: it's to work out their **categories**, so
  that when similar new modules are added, most of the infrastructure is already there.

## GUTTR / GUTTUR (planned module; plan for compatibility now)
- Soon I want to build a version of my GUTTR synth into Wirescape. It will be more stripped down, but I want
  the **full throat voice** in it (the original GUTTUR engine, not the five-formant "lite" singer).
- No chant sequencer, not many parts or sections. A multi-voice synth where I can modulate the voices
  independently, based on the throat instrument.
- It's a sketch and not fully developed, so it can be built completely differently if that's better and more
  compatible. If it helps, I can get a sketch of it rewritten to fit Wirescape so Fable doesn't have to work
  on it much.
- What it is today (facts from the beta 0.4 source, for reference):
  - GUTTR: a Python instrument on Surge XT through `surgepy`, Dear PyGui UI, voices A/B (Surge) and singer C,
    a host DSP chain (roughness AM, looper, limiter), live MERGE effects between voices (vocoder, ring/AM/FM,
    envelope gate/duck, waveset braid, throat-follow), a fry gate, a self-modulating LFO and a randomizer.
    Controls map to the study guide *How Music Learned to Be Scary*. GPL-3 (because of Surge).
  - GUTTUR full throat (`guttur/core.js`, ~82 KB, one file, no DOM; runs in Node, an AudioWorklet or the main
    thread): band-limited LF glottal pulses decided per pitch cycle; tube-derived resonances from a vocal-tract
    area function (vowel, pharynx, mouth, ring), precomputed into a shared tube grid; played through a ramped
    zero-delay SVF cascade; a singer group with a leader, followers and one "looseness" axis; a room.
  - Per-voice parameters include vowel, size/length, jitter, shimmer, growl, breath, creak, number of throats,
    looseness, vibrato.
  - In beta 0.4 the full throat runs through a synchronous Node bridge, which the build notes say may underrun
    audio callbacks.
- Things this kind of module seems to need from a host (as I understand it, for Fable to check): large
  precomputed tables shared between instances and built off the audio thread; many voices with per-voice
  parameters and independent modulation; decisions at pitch-cycle boundaries; groups of voices that follow a
  leader; cross-voice effects (one voice shaping another); stereo output.

## Process notes for the brief (not for Fable to act on)
- Facts and opinions stay separate. The research packs and measurements are neutral; opinions only in proposals.
- Big decisions come back to me before they're built.
- The final brief to Fable says what I need and what's important to me, in my voice, without telling it how.
