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
- Special modules shouldn't carry the `essentials` tag. GUTTR's ID is `guttr`. CHAOS is currently
  `essentials.chaos_lite`, which it shouldn't be. Low priority: only rename it if that area gets rewritten anyway (it needs a
  lossless patch migration, since saved and bundled patches use the old ID). Macro is `ports.macro_oscillator`.
- The point of the complex modules isn't those modules themselves: it's to work out their **categories**, so
  that when similar new modules are added, most of the infrastructure is already there.

## GUTTUR (module in the works)
- I've made a headless C++17 version of GUTTUR with a Wirescape ABI 2 adapter: the full throat voice
  (LF glottal source, 34-section tract, throat groups, room), no chant sequencer, no UI. It still needs
  more testing by me; treat it as a module in the works: `docs/context/future_modules/guttur/STATUS.md`.
  (Everything earlier about GUTTR/GUTTUR is replaced by this.)
- I want a multi-voice synth where I can modulate the voices independently, based on the throat instrument.
- The point isn't GUTTUR itself: I want the infrastructure for its kind of module (model-based voices with
  large tables, voices inside voices, groups, shared space, many per-voice controls) to be there, so similar
  modules are easy later. GUTTUR is a good test of that.

## Stock modules that add capabilities
- That's how the app has been growing: many stock modules brought a new capability with them (Chord →
  polyphony, sequencers → timed events and sequencing, OSC and MIDI → communication, and so on).
- Alongside the special modules, I want to look at which stock modules would add more capabilities to
  Wirescape at the core level. Fable could lay the ground and protocols for them so we build them after,
  or develop basic versions quickly. It's a way to expand what the app can support.

## Custom UIs for modules
- I want to start designing my own interfaces for modules (for example GUTTUR and CHAOS), the way VCV Rack
  developers design their own panels.
- I want the UI capabilities expanded so people can design module interfaces within Wirescape, and I want it
  to be easy, or similar to existing UI-building systems, especially the ones used in module and plugin
  environments.
- Worth considering: support for JUCE's HTML/WebView UI approach.

## Process notes for the brief (not for Fable to act on)
- Facts and opinions stay separate. The research packs and measurements are neutral; opinions only in proposals.
- Big decisions come back to me before they're built.
- The final brief to Fable says what I need and what's important to me, in my voice, without telling it how.
