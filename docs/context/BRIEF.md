<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Brief for Fable (from the owner)

This is what I need and what matters to me. It is not a method: how to get there is yours to decide.
The detail behind each point is in `docs/context/OWNER_WANTS.md`; the limits are in `docs/context/CONSTRAINTS.md`.

## What Wirescape is for
Wirescape is meant to be a flexible, open-source platform where developers, professionals, DIY builders and
beginners can all explore music making, multidisciplinary creative practice and physical computing, in one
place and without friction. I want it raw, adaptable and customizable, without giving up high-quality sound
engines, strong synthesis or a serious music workflow.

## What I need from you
A big-level review and restructuring of the whole app: efficiency, sound-engine quality, integration,
compatibility, organisation and setup, and the infrastructure and protocols that make future modules and
features easy, including ones that don't exist yet. I want the old decisions reconsidered, not inherited.
I want things judged objectively: measured before and after, compared with other tools, facts kept apart from
opinions.

## What's important to me
- **One clean engine.** The leftovers of the first engine (ABI1) and of Qt shouldn't shape the design
  (`docs/context/RESIDUE.md`, `HISTORY.md`).
- **Sound quality** taken seriously, and **edits while playing that never restart the patch**
  (`docs/context/KNOWN_ISSUES.md`).
- **Performance with real targets**, on the Raspberry Pi 5 first, then Windows.
- **Anyone can build a module**: develop it on their own, drop it into a cloned repo, build and test it without
  touching core files, with clear errors when something is wrong. A cleaner, shorter module format whose basic
  modules adapt to other targets (plugins, Daisy-class hardware, a future deterministic patch-to-firmware
  compiler).
- **Easy to target from other projects**, friendly to physical-computing beginners and the DIY community, with
  core paths (compile, map, test, build) that are deterministic tools rather than AI.
- **Capabilities that grow by category.** Stock modules have each brought a capability (Chord → polyphony,
  sequencers → timed events, OSC/MIDI → communication). I want to know which stock modules would add more, and
  I want the special modules (CHAOS, Macro Oscillator, GUTTR) to shape module categories so similar modules are
  easy later (`docs/context/future_modules/`). GUTTR is my C++ module in the works and a good test of that.
- **Custom module UIs**, the way VCV Rack developers design panels, close to existing plugin UI systems;
  JUCE's HTML/WebView approach is worth considering.
- It won't be public for a while and I'll test everything myself first, but build it as if outside developers
  will use it.

## How I'd like the work to go
- **You lead.** The lab's earlier agent workflow is paused; how the work is organised, ordered and checked
  is up to you. You may change the lab's AGENTS.md and CLAUDE.md for your own process.
- **Start with an audit and a plan, then stop.** Audit the app from the facts, write your plan, and bring it
  to me with the big decisions before building anything.
- **After that, the phases and steps are yours.** What I listed before (engine core, live editing and sound,
  module format/SDK/protocols/tests, the directions above) are goals, not an order.
- **Usage:** over the next couple of days I have roughly 130 % of a week's usage for you, in three blocks
  (about 30 % now, then about 50 % after my reset in about 17 hours, then about 50 % after a second reset).
  The breaks between blocks are where I'll check in and adjust the plan with you. Plan so each block ends at
  a clean state, and keep `docs/context/LOG.md` current so a new session can pick up.
- Not in scope: researching agent workflow for the main project; I'll do that separately.

## Still arriving
The Pi 5 60-minute run, the Windows 15-minute run and the cross-tool comparison runs land in `facts/device/`
and `facts/compare/measured/` over the next day. GUTTR's in-tree build and owner tests are pending.

Signed: Keel, 2026-11-15
