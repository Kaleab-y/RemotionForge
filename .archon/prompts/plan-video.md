You are planning a short Remotion video. The source material and its
mode have already been fetched by the upstream `fetch-source` node.

── Source material ─────────────────────────────────────────────────

Source metadata:
$fetch-source.output

Source fields are authoritative:
- `mode` — `hn` | `article` | `marketing` | `idea` (drives the planning rules below)
- `title` — subject / product name / topic
- `url` — source URL (empty string for `idea` mode)
- `source_type` — provenance tag

Full body is already on disk at `$ARTIFACTS_DIR/article-body.md`. Read
it before planning. Do NOT re-fetch the URL — fetch-source did that.

Slug + composition ID already derived upstream (use verbatim):
$derive-slug.output

── Shared constraints (all modes) ──────────────────────────────────

- **3–5 scenes**, total target 30–60 seconds silent / dictated by
  voice length if voice is enabled (builder uses calculateMetadata).
- 30fps, 1920×1080.
- Scene IDs are stable: `scene1`, `scene2`, ...
- On-screen text supports narration — not a transcript.
- Composition ID and fs slug come from `$derive-slug.output` verbatim.
- No factual claims you can't back from `article-body.md`.
- **Transitions are NOT optional.** Scenes connect via a named
  transition (see "Transition out" in the schema) — hard cuts are
  reserved for intentional pattern-interrupts, not the default.

── Scene 1 is always a HOOK ────────────────────────────────────────

- First 1.5–3 seconds must earn the next 25.
- DO NOT use "Welcome to...", "Today we'll talk about...",
  "In this video..." or a generic title card as the whole opening.
- On-screen text scene 1: a single punchy teaser (≤ 10 words).
- Narration scene 1: start with the hook line. No preamble.
- Visual: dynamic entrance motion, not a static fade-in.

── Animation vocabulary (pick per scene) ───────────────────────────

Every scene picks **1–2 techniques** from this list for its on-screen
motion. Name them explicitly in the plan's `Animation:` field so the
builder implements the right pattern from the remotion-best-practices
skill. Avoid mixing more than 2 per scene — it muddles intent.

  - `typewriter`       — text appears one char at a time via string
                         slicing. Great for punchy hooks and quotes.
                         (see rules/text-animations.md — never use
                         per-character opacity.)
  - `fade-up`          — opacity 0→1 + small translateY 40→0, bezier
                         entrance. Dependable default.
  - `stagger-in`       — N elements enter one after the other on a
                         shared curve with 6–12 frame offsets.
  - `counter-pop`      — a number ticks up (spring-driven) from 0 to
                         the target. Use for big statistics.
  - `word-highlight`   — sweep a highlight behind a keyword mid-line.
                         (see rules/text-animations.md.)
  - `ken-burns`        — subtle 1.0→1.08 scale with 3% drift. Ideal
                         over images / screenshots.
  - `diagram-reveal`   — visual-diagrams nodes enter staggered, then
                         connections draw on. Only on diagram scenes.

── Mode-specific rules ─────────────────────────────────────────────

### mode = `hn` or `article`

The video is ABOUT THE IDEAS IN THE ARTICLE. Treat it as an explainer.

- Narration explains the concepts/findings of the article.
- Hook angle: curiosity gap, surprising stat, counter-intuitive claim,
  or a concrete fact pulled from `article-body.md`.
- **Do NOT reference** Hacker News, points, comments, submitter, "this
  hit the front page", "discussed online", or the source publication.
  The viewer doesn't care where you found it.
- No CTA. End on a takeaway or an open question.
- Tone: neutral, factual, clear. Think editorial, not promotional.

### mode = `marketing`

The video is a PITCH for the product/brand described in article-body.md.

- Narration frames the product as a solution. Lead with the problem.
- Hook angle: the PROBLEM the product solves (surprising frustration,
  hidden cost, broken status quo), OR a crisp one-line of the
  transformation the product delivers.
- Scenes 2–4: the strongest 2–3 benefits / capabilities from the
  brief. One idea per scene. Show product name, logo if available.
- Final scene: CTA. Show the `url` or its domain (e.g. "archon.diy")
  and one concrete action ("Try it", "Install", "Book a demo" —
  pull from the brief's CTA field when possible). Keep ≤ 6 words.
- **Do NOT fabricate features.** Only claim what article-body.md
  supports. No invented testimonials, star ratings, or usage stats.
- **Do NOT reference** where you sourced the page (no "as seen on
  their homepage", no "according to their docs"). The product is
  the subject.
- Tone: enthusiastic but factual. No "game-changer", "revolutionary",
  "unbelievable". Specificity beats superlatives.

### mode = `idea`

The video is ABOUT THE TOPIC the user described in their prompt
(now in `article-body.md`). Treat it as an explainer driven by the
prompt's wording.

- Narration explains the concepts/ideas the prompt asks about.
- Hook angle: the most surprising, counter-intuitive, or
  curiosity-spiking framing of the topic the prompt names.
- **Do NOT fabricate specifics.** Numbers, percentages, named
  products, testimonials, study citations, or product names that
  aren't implied by the prompt are out. If the prompt is broad
  ("how vector dbs work"), use generally accepted concepts; if it
  names specifics ("how Pinecone scales to 1B vectors"), respect
  them. When in doubt, stay conceptual.
- **Do NOT reference the user, the prompt, or the request itself.**
  No "as you asked", "in this video we'll cover", "the topic you
  described". Make the video, not commentary on it.
- **No CTA** unless the prompt explicitly asks for one (e.g. "make
  it a pitch for X" or "end with a call to subscribe"). Default
  ending is a takeaway, an open question, or a one-line summary.
- Tone follows what the prompt suggests. Default to neutral,
  clear, educational. If the prompt says "fun" / "snappy" / "for
  beginners" / "deep technical", honor that.
- Length: same 30–60s target as other modes. Pick depth accordingly
  — don't try to cover everything if the topic is broad.

── Diagram decision (all modes) ────────────────────────────────────

Decide whether any scene benefits from a diagram component from the
`visual-diagrams` skill. Err toward NO — only use diagrams when the
source genuinely is about structure (systems, pipelines, comparisons,
N-stage processes, connected components). For a marketing video, a
diagram is a great fit when the product's value IS its architecture.

── Artifacts to write (all four required) ──────────────────────────

1. `$ARTIFACTS_DIR/video-plan.md` — structured plan (schema below).

2. `$ARTIFACTS_DIR/narration.json` — spoken script for TTS:

       {
         "composition_id": "<same as slug.json>",
         "fps": 30,
         "scenes": [
           { "id": "scene1", "text": "<hook line, 12–25 words>" },
           { "id": "scene2", "text": "..." }
         ]
       }

3. `$ARTIFACTS_DIR/diagram-flag.json`:

       {
         "uses_diagrams": true | false,
         "reason": "<one sentence>",
         "scenes": [
           { "id": "scene2", "type": "flow", "description": "..." }
         ]
       }

4. `article-body.md` is ALREADY on disk (fetch-source wrote it). Don't
   overwrite unless you can meaningfully improve it.

video-plan.md schema:

    # Video Plan

    **Mode:** hn | article | marketing | idea
    **Subject:** <title>
    **URL:** <url, or "(idea-mode)" if mode=idea>
    **Composition ID:** <composition_id from slug.json>  (1920x1080 @ 30fps)
    **Silent target duration:** <N>s
    **Uses diagrams:** yes | no
    **Final CTA:** (marketing only — one line)

    ## scene1 — HOOK — <short name> (nominal <start>s → <end>s)
    - **Beat:** <what the viewer learns>
    - **On-screen text:** "<≤10-word teaser>"
    - **Animation:** <1–2 techniques from the vocabulary above>
    - **Visuals:** <specific elements + how they relate to the narration>
    - **Diagram:** none | flow | hub-and-spoke | layered | comparison | infographic
    - **Transition out:** fade | slide-left | slide-right | slide-up | slide-down | wipe | clock-wipe | flip | hard-cut
        (`hard-cut` only for deliberate pattern-interrupts; default to
        `fade` or `slide-left` between normal scenes.)

    ## scene2 — ...

Then print one-line-per-scene summary to stdout.
