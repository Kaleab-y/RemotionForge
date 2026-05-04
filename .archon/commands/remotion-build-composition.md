---
description: Implement a Remotion composition for RemotionForge (workflow: `remotion-idea-to-video`). Writes a self-contained `src/<CompId>/` folder into the repo root, wires audio from `public/`, picks up `visual-diagrams` only on flagged scenes, applies optional brand overlay from `.archon/brand.yaml`. Never edits `src/Root.tsx` — a downstream node regenerates `src/compositions.gen.ts` to pick up every composition's `index.ts`.
argument-hint: (no direct arguments — consumes artifacts at $ARTIFACTS_DIR/ and the repo's public/ audio assets)
---

# Remotion — Build Composition

**Workflow ID**: $WORKFLOW_ID
**Artifacts dir**: $ARTIFACTS_DIR

You are the Remotion builder node for RemotionForge (workflow: `remotion-idea-to-video`). The
plan, narration, diagram decision, and (opt-in) audio assets are already on
disk. Your job: implement a **new composition** inside the repo's persistent
Remotion project so it joins the library of all past videos. You have two
skills loaded:

- `remotion-best-practices` — always consult
- `visual-diagrams` — consult ONLY if the plan flagged diagrams

---

## Phase 1: LOAD

The **repo root is your project root**. Archon runs you from there, so `cwd`,
`package.json`, `src/`, `public/` are all the repo's.

Read these in order:

1. `$ARTIFACTS_DIR/slug.json` — authoritative `composition_id` and `fs_slug`.
   **The composition ID MUST be the exact `composition_id` string.** Don't
   invent one.
2. `$ARTIFACTS_DIR/video-plan.md` — scene structure.
3. `$ARTIFACTS_DIR/narration.json` — spoken script per scene.
4. `$ARTIFACTS_DIR/article.json` + `$ARTIFACTS_DIR/article-body.md` — source.
5. `$ARTIFACTS_DIR/diagram-flag.json` — `{uses_diagrams, scenes[]}`.
6. **Probe which audio assets exist** — read each manifest if present:
   - `$ARTIFACTS_DIR/audio/voice-manifest.json`
   - `$ARTIFACTS_DIR/audio/music-manifest.json`
   - `$ARTIFACTS_DIR/audio/sfx-manifest.json`

   The corresponding MP3s have already been written under the repo's
   `public/voiceover/<CompId>/`, `public/music/<CompId>.mp3`, and
   `public/sfx/<CompId>/` respectively. You do NOT write audio files —
   you only wire them.
7. `.archon/brand.yaml` (repo-local, optional) — if present, apply the
   `colors`, `font_family`, `logo_url`, `watermark_position` /
   `watermark_opacity`. If absent, use neutral defaults:

       bg: #0B1120
       primary: #7C3AED
       secondary: #06B6D4
       accent: #F59E0B
       text_primary: #FFFFFF
       text_muted: #94A3B8
       font: Inter (via @remotion/google-fonts)
       no watermark

8. `package.json` — confirm Remotion version. If `@remotion/transitions`,
   `@remotion/google-fonts`, or `lucide-react` are missing and the plan
   requires them, install them now via
   `pnpm add @remotion/transitions @remotion/google-fonts lucide-react`.
9. `src/Root.tsx` and `src/compositions.gen.ts` — **DO NOT EDIT EITHER
   FILE.** The root reads from `src/compositions.gen.ts`, which a
   downstream workflow node regenerates by scanning `src/<name>/index.ts`
   files. All you need to do is drop a valid `index.ts` inside your
   composition's folder.

Then from the skills, always read:
- `rules/compositions.md`
- `rules/timing.md`
- `rules/sequencing.md`
- `rules/text-animations.md`
- `rules/animations.md`
- `rules/fonts.md`
- `rules/transitions.md`   ← scene boundary transitions are first-class

If **voice-manifest exists**, additionally read:
- `rules/voiceover.md`
- `rules/calculate-metadata.md`
- `rules/get-audio-duration.md`
- `rules/audio.md`

If **diagram-flag.uses_diagrams == true**, additionally read:
- `visual-diagrams` SKILL.md
- `references/component-patterns.md`
- `references/animation-choreography.md`

### PHASE_1_CHECKPOINT
- [ ] `composition_id` + `fs_slug` captured from slug.json (will use verbatim)
- [ ] Plan + narration + diagram-flag read
- [ ] Each audio manifest probed; modes noted (voiced / music / sfx)
- [ ] Brand config loaded OR defaults selected
- [ ] Relevant rule files consulted

## Phase 2: IMPLEMENT

Create a single self-contained directory: **`src/<CompositionId>/`** in the
repo root.

    src/<COMPOSITION_ID>/
      index.ts                 — default-exports composition meta (REQUIRED)
      <COMPOSITION_ID>.tsx     — top-level composition, <Sequence>s, audio
      calculateMetadata.ts     — only when voice-manifest exists
      constants.ts             — fps, palette, typography, layout
      scenes/Scene1.tsx        — per-scene component
      scenes/SceneN.tsx

### `src/<CompId>/index.ts` — the registration contract

This file is the only thing `src/Root.tsx` looks at. It must export a default
object with this shape:

```tsx
// src/<CompId>/index.ts
import { <CompId> } from './<CompId>';
import { calculateMetadata } from './calculateMetadata'; // voiced mode only

export default {
  id: '<CompId>',
  component: <CompId>,
  width: 1920,
  height: 1080,
  fps: 30,
  durationInFrames: 1800,   // placeholder; calculateMetadata overrides
  calculateMetadata,         // omit when silent mode
};
```

**If you skip or mis-type this file, `Root.tsx` will not register the
composition** — that's a CRITICAL failure.

### Shared rules (always)

- Composition ID = exact `composition_id` from slug.json.
- 1920×1080 @ 30fps.
- Scene IDs stable: `scene1`, `scene2`, …
- **No TailwindCSS.** Inline styles or style objects.
- All `interpolate()` calls set `extrapolateLeft: "clamp"` and
  `extrapolateRight: "clamp"`.
- Text ≥ 48px body / ≥ 96px headlines.
- **Durations in seconds × fps**, not raw frame counts. `const FADE_IN = 0.6 * fps;`
  not `const FADE_IN = 18;`. Only measured audio frame counts (from the
  manifest) appear as raw numbers.
- **Premount every `<Sequence>`.** `<Sequence premountFor={fps} ...>` — the
  skill's `rules/sequencing.md` mandates this for smooth Studio scrubbing.
  Exception: sequences shorter than 1 second can use a smaller premount.
- **Never per-character opacity** for text animation. Typewriter uses
  string slicing (see `rules/text-animations.md`). Per-character opacity
  is a HIGH-severity finding for QA.
- **No CSS transitions / animations. No Tailwind animation classes.**
  All motion goes through `interpolate()` + `useCurrentFrame()`.
- **Hook (scene1)**: narration and on-screen text must NOT echo the article
  title, must NOT reference HN/points/comments, must NOT open with
  "Welcome" / "Today" / "In this video". On-screen ≤ 10 words. Entrance
  motion is dynamic.
- **Content**: nothing anywhere may reference Hacker News or its metadata.
- **Isolation**: do NOT edit files outside `src/<CompId>/`. Do not touch
  other compositions. Do not edit `src/Root.tsx` or `src/compositions.gen.ts`.
  It's fine to create `src/shared/` helpers if your code genuinely reuses
  them, but don't refactor other compositions' code to use your helpers.

### Easing palette (pick intentionally per motion)

From `rules/timing.md`. **Never use `Easing.linear` for anything but loops.**

```ts
import { interpolate, Easing } from "remotion";

// UI entrance — crisp, no overshoot. Default for enter animations.
const enter = Easing.bezier(0.16, 1, 0.3, 1);

// Editorial fade — symmetric ease-in-out. Use for cross-scene fades.
const editorial = Easing.bezier(0.45, 0, 0.55, 1);

// Playful overshoot — y > 1 control point. Use sparingly for emphasis.
const pop = Easing.bezier(0.34, 1.56, 0.64, 1);
```

Rule of thumb: `enter` bezier (or `Easing.out(...)`) for things COMING IN,
`Easing.in(...)` for things LEAVING. Elements arrive with momentum and
leave with gravity.

### Composed-progress pattern (the right way to animate multiple props)

From `rules/timing.md`. Separate **timing** (when and how fast) from
**mapping** (what values). When a scene animates multiple properties on
the same beat, derive them from ONE normalized 0→1 progress variable:

```tsx
const progress = interpolate(frame, [0, 0.8 * fps], [0, 1], {
  easing: Easing.bezier(0.16, 1, 0.3, 1),
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});

const y       = interpolate(progress, [0, 1], [40, 0]);
const scale   = interpolate(progress, [0, 1], [0.96, 1]);
const opacity = interpolate(progress, [0, 1], [0, 1]);
```

This prevents the no-op interpolation bug (`[1.0, 1.0]`) QA has caught in
the past — you can see at a glance that every derived value has a real
range.

### Scene boundaries — use `<TransitionSeries>` (mandatory when plan requests one)

The plan's `Transition out:` field is NOT decorative. If ANY scene specifies
a transition other than `hard-cut`, the composition MUST arrange scenes
under `<TransitionSeries>` from `@remotion/transitions` with the matching
preset — hand-animating opacity on the boundary is forbidden.

```tsx
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { fade }      from "@remotion/transitions/fade";
import { slide }     from "@remotion/transitions/slide";
import { wipe }      from "@remotion/transitions/wipe";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { flip }      from "@remotion/transitions/flip";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={scene1Frames}>
    <Scene1 />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={slide({ direction: "from-right" })}
    timing={linearTiming({ durationInFrames: Math.round(0.35 * fps) })}
  />
  <TransitionSeries.Sequence durationInFrames={scene2Frames}>
    <Scene2 />
  </TransitionSeries.Sequence>
  ...
</TransitionSeries>
```

Plan → preset mapping (apply each scene's `Transition out:` to the
transition AFTER that scene):
- `fade`        → `fade()`
- `slide-left`  → `slide({ direction: "from-right" })`   (new scene enters from right)
- `slide-right` → `slide({ direction: "from-left" })`
- `slide-up`    → `slide({ direction: "from-bottom" })`
- `slide-down`  → `slide({ direction: "from-top" })`
- `wipe`        → `wipe()`
- `clock-wipe`  → `clockWipe({ width, height })`
- `flip`        → `flip()`
- `hard-cut`    → no `<TransitionSeries.Transition>` between those two
  sequences — adjacent `<TransitionSeries.Sequence>`s produce a hard cut.

Transitions **shorten** the timeline (two scenes play simultaneously during
the crossfade). When computing `durationInFrames` for `calculateMetadata`
you MUST subtract transition durations from the total (see
`rules/transitions.md#calculating-total-composition-duration`).

When SFX has a `transition_N` cue, align the SFX's Sequence offset to the
visual transition's cut point (not to either scene's full boundary).

### Font loading (via `@remotion/google-fonts`)

From `rules/fonts.md`. If the package isn't installed:
`pnpm add @remotion/google-fonts`. Load once at the top of a module
imported early (typically `constants.ts`), with weights + subsets
declared to keep bundle size down:

```tsx
// src/<CompId>/constants.ts
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "600", "800"],
  subsets: ["latin"],
});

export const FONT_FAMILY = fontFamily;
```

Then consume `FONT_FAMILY` in scene components. If brand.yaml sets
`font_family`, swap the import path (e.g. `@remotion/google-fonts/Manrope`).
If the requested family isn't on Google Fonts, fall back to `Inter` and
note it in your final report.

### Brand overlay

If `.archon/brand.yaml` exists, apply its `colors`, `font_family`, and
watermark settings to `constants.ts` and (if logo_url present) a composition-
level `<Img>` at `watermark_position` with `watermark_opacity`. Clamp logo
width to 120px. If `logo_url` is a URL, download it to
`public/brand/logo.<ext>` as part of your build. If it's a path under
`.archon/brand/`, copy it into `public/brand/`. Absent file ⇒ neutral
defaults (see Phase 1).

### Silent mode (no voice-manifest)

- `durationInFrames` on the composition meta is static, derived from plan
  scene durations MINUS transition durations.
- No `calculateMetadata.ts`.
- No `<Audio>` for voice. (Music/SFX still layer if their manifests exist.)
- Scenes still arranged inside `<TransitionSeries>` unless every scene in
  the plan uses `hard-cut` (rare).

### Voiced mode (voice-manifest exists)

Canonical pattern from `rules/voiceover.md` + `rules/transitions.md`:

1. Write `src/<CompId>/calculateMetadata.ts` that:
   - Uses `getAudioDuration(staticFile(scene.path))` per scene — **dynamic**,
     not hardcoded frame constants.
   - Subtracts transition durations from the total (transitions overlap).
   - Passes `sceneDurations` as composition props.

2. `<CompId>.tsx` arranges scenes inside `<TransitionSeries>` (per the
   Scene boundaries section). Each `<TransitionSeries.Sequence>` contains
   the scene component PLUS its `<Audio src={staticFile(scene.path)} />`:

   ```tsx
   <TransitionSeries.Sequence durationInFrames={scene1Frames}>
     <Audio src={staticFile(voice.scenes[0].path)} />
     <Scene1 />
   </TransitionSeries.Sequence>
   <TransitionSeries.Transition
     presentation={fade()}
     timing={linearTiming({ durationInFrames: Math.round(0.35 * fps) })}
   />
   <TransitionSeries.Sequence durationInFrames={scene2Frames}>
     <Audio src={staticFile(voice.scenes[1].path)} />
     <Scene2 />
   </TransitionSeries.Sequence>
   ```

3. On-screen text complements — does not duplicate — the narration.

### Music layer (music-manifest exists)

Single composition-level `<Audio>` at root (not inside any Sequence):

```tsx
<Audio src={staticFile(musicManifest.path)} volume={musicManifest.volume} />
```

Default volume ~0.2 (ducked beneath voice). Manifest is authoritative.
If music is shorter than the composition, accept silence at the tail —
looping BGM under narration is distracting. If longer, Remotion trims.

### SFX layer (sfx-manifest exists)

For each cue in `sfx-manifest.cues`:
- `intro_whoosh` → `<Sequence from={0} durationInFrames={cue.duration_frames}>` with audio.
- `outro_stinger` → at `compositionDuration - cue.duration_frames`.
- `transition_N` → at each scene boundary (offset = end-frame of `from_scene`
  minus ~3 frames to lead the cut).

Don't place SFX mid-scene unless the plan explicitly requested it.

### Diagram scenes (diagram-flag.uses_diagrams == true)

For each scene in `diagram-flag.scenes`, use the matching `visual-diagrams`
component:

- `flow` → `FlowDiagram`
- `hub-and-spoke` → `HubAndSpoke`
- `layered` → `LayeredArchitecture`
- `comparison` → `ComparisonDiagram`
- `infographic` → `InfographicFlow`

Follow the skill's rules: gradient fills, 2-layer shadows, ≥2.5px connection
strokes, Lucide icons (`lucide-react`) or downloaded brand logos, never
Unicode emoji as icons. Background atmosphere (ProceduralNoise + radial
gradient) encouraged for diagram scenes.

If the `visual-diagrams` components aren't importable from the project
(i.e. there's no shared components directory under `src/shared/`), vendor
what you need into `src/shared/components/` following the skill's design
rules. Keep your vendored components visual-diagrams-compliant.

### PHASE_2_CHECKPOINT
- [ ] `src/<CompId>/` populated, including `index.ts` default-export
- [ ] `src/Root.tsx` AND `src/compositions.gen.ts` UNTOUCHED
- [ ] Scenes wrapped in `<TransitionSeries>` with the plan's transitions
      applied as `<TransitionSeries.Transition>` (unless all `hard-cut`)
- [ ] Every `<Sequence>` / `<TransitionSeries.Sequence>` uses `premountFor`
- [ ] All durations expressed as `seconds * fps`, not raw frame numbers
      (audio-manifest frame counts are the only exception)
- [ ] All `interpolate()` calls use a named `Easing.bezier` curve (not linear)
- [ ] Multi-property animations derive from a single normalized progress
- [ ] Fonts loaded via `@remotion/google-fonts` with weights + subsets
- [ ] Typewriter effects use string slicing, never per-character opacity
- [ ] If voiced: `calculateMetadata.ts` uses dynamic `getAudioDuration`
      AND subtracts transition durations from the total
- [ ] If music: single composition-level `<Audio volume>` set from manifest
- [ ] If SFX: cues wired at correct offsets from the manifest
- [ ] If diagrams: flagged scenes use the correct component, fully styled
- [ ] Brand overlay applied where relevant
- [ ] No Tailwind, no CSS transitions/animations, no HN references

## Phase 3: SELF-CHECK

```bash
npx --yes tsc --noEmit
```

Fix errors. Retry up to two times. If still failing, stop and report.

### PHASE_3_CHECKPOINT
- [ ] `tsc --noEmit` exits 0
- [ ] `src/<CompId>/index.ts` and `src/<CompId>/<CompId>.tsx` present
- [ ] `src/Root.tsx` unchanged from what you read in Phase 1

## Phase 4: REPORT

Final message (plain text, no code fences, no file dumps):

- Composition ID
- Modes: voiced=<bool> music=<bool> sfx=<bool> diagrams=<bool>
- Duration source (plan | audio-dynamic)
- Scenes implemented (one line each: `sceneN — name — start..end frames`)
- Files written (paths relative to repo root)
- `tsc --noEmit` result (PASS or error summary)

No other text.
