# remotion-idea-to-video

Archon workflow that turns any URL into a short voiced Remotion video — voiced, with optional SFX/music, rendered to mp4, archived in-repo.

## What it does

Pass a mode + (URL or prompt) via `$ARGUMENTS`:

- `""` / `"hn"` — auto-pick today's top Hacker News story
- `"article <url>"` — explainer video from an article
- `"marketing <url>"` — pitch video for a product site
- `"idea <free-form prompt>"` — describe a topic in plain English, no URL needed

Each run drops a new composition under `src/<CompId>/` and renders an mp4 into `./videos/<date>-<slug>/`. Studio opened against the repo shows every past video in one sidebar.

---

## Quick start — let your coding agent set this up

**Easiest path: have your coding agent do the setup for you.** This README is written so any agent can read it end-to-end and bring the repo to a runnable state without you running install commands by hand.

1. Open your coding agent inside this repo.
2. Tell it: **"Read `README.md` and set up this repo so I can run the Remotion video workflow."**
3. When it asks about your TTS provider (Cartesia or ElevenLabs), answer with whichever you have a key for. The agent will create `.archon/.env` and fill in the right variables.
4. When the agent reports everything verified, run the workflow (see [Run](#run)).

### Which coding agent?

**We've tested with [Claude Code](https://claude.ai/code), and that's the recommended starting point.** Archon also supports **Codex** and **Pi** — set `DEFAULT_AI_ASSISTANT=claude|codex|pi` in `.archon/.env`. The setup steps below assume Claude Code; swap the `claude` install command for the equivalent assistant CLI if you're using something else.

> **Note for the coding agent reading this**: this README is the single source of truth for setup. Walk through [Prerequisites checklist](#prerequisites-checklist) → [Verify what's already installed](#verify-whats-already-installed) → [Install (per requirement)](#install-per-requirement) → [Run](#run) in order. **Do not guess the TTS provider** — ask the user which key they have (Cartesia or ElevenLabs) before writing `.archon/.env`. Do not skip steps. Do not invent commands not in this file.

---

## Prerequisites checklist

Six things must be present. None of them are optional.

| # | Requirement                              | Why                                                                |
|---|------------------------------------------|--------------------------------------------------------------------|
| 1 | **Archon CLI** (`archon` on PATH)        | Runs the workflow DAG                                              |
| 2 | **Claude Code CLI** (`claude` on PATH)   | Drives `command`/`prompt` nodes (planner, builder, QA, summarizer) |
| 3 | **Remotion skill** at `.claude/skills/remotion-best-practices/SKILL.md` | First node (`check-skill`) hard-fails without it |
| 4 | **System tooling**: Node 20+, pnpm, Python 3.11+, uv, jq, ffmpeg | Used by scripts, scaffolding, audio gen, rendering              |
| 5 | **`.archon/.env`** (you create it)       | Holds assistant auth + API keys; not committed; copy from `.env.example` |
| 6 | **At least one TTS API key** (Cartesia or ElevenLabs) | Voice is required for a non-silent output                |

### Verify what's already installed

Run these in order. If any check fails, jump to the matching install section below.

```bash
# 1. archon
archon --version

# 2. claude code
claude --version

# 3. remotion skill (workflow looks in any of these paths)
ls .claude/skills/remotion-best-practices/SKILL.md \
   .agents/skills/remotion-best-practices/SKILL.md \
   "$HOME/.claude/skills/remotion-best-practices/SKILL.md" 2>/dev/null

# 4. system tooling
node --version           # >= v20
pnpm --version
python --version         # >= 3.11
uv --version
jq --version
ffmpeg -version

# 5. env file present
test -f .archon/.env && echo "ok" || echo "missing"

# 6. at least one TTS key set
grep -E '^(CARTESIA|ELEVENLABS)_API_KEY=' .archon/.env
```

PowerShell equivalents (Windows): replace `ls ... 2>/dev/null` with `Get-ChildItem ...`, `test -f` with `Test-Path`, and `grep` with `Select-String`.

---

## Install (per requirement)

### 1. Archon CLI

```bash
# macOS / Linux
curl -fsSL https://archon.diy/install | bash

# Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex
```

Docs: https://archon.diy/docs. After install, run `archon --version` to confirm it's on PATH.

### 2. Claude Code CLI

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash

# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```

Then **`claude /login`** once. The workflow uses `CLAUDE_USE_GLOBAL_AUTH=true` (see `.env.example`) which reuses this session — you don't need `ANTHROPIC_API_KEY`.

### 3. Remotion skill

From this repo root:

```bash
npx skills add remotion-dev/skills --yes
```

This installs both `remotion-best-practices` (animation/voiceover rules) and `visual-diagrams` (hub-and-spoke / flow / comparison components) under `.claude/skills/` and `.agents/skills/`. The `archon` skill is bundled too.

### 4. System tooling

| Tool        | Install                                                                 |
|-------------|-------------------------------------------------------------------------|
| **Node 20+** | nvm: `nvm install 20 && nvm use 20`. Or via your platform's installer. |
| **pnpm**    | `npm install -g pnpm`                                                   |
| **Python 3.11+** | macOS: `brew install python@3.11`. Linux: distro package. Windows: https://www.python.org/downloads/ |
| **uv**      | macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh`. Windows: `irm https://astral.sh/uv/install.ps1 \| iex` |
| **jq**      | macOS: `brew install jq`. Linux: `apt install jq`. Windows: `winget install jqlang.jq` |
| **ffmpeg**  | macOS: `brew install ffmpeg`. Linux: `apt install ffmpeg`. Windows: `winget install Gyan.FFmpeg` |

### 5. Create `.archon/.env`

**You must create this file — it does not exist by default.** Start from the template:

```bash
# macOS / Linux
cp .env.example .archon/.env

# Windows (PowerShell)
Copy-Item .env.example .archon/.env
```

The defaults in `.env.example` are correct for most users:

```env
CLAUDE_USE_GLOBAL_AUTH=true     # use `claude /login` session (recommended)
DEFAULT_AI_ASSISTANT=claude     # claude | codex | pi
```

- If you logged in with `claude /login`, leave these as-is — no `ANTHROPIC_API_KEY` needed.
- If you'd rather use a raw API key, set `ANTHROPIC_API_KEY=sk-ant-...` and flip `CLAUDE_USE_GLOBAL_AUTH=false`.
- If you're using Codex or Pi instead of Claude, set `DEFAULT_AI_ASSISTANT=codex` (or `pi`) and follow that assistant's auth instructions.

### 6. Configure your voice (TTS) provider

The workflow needs **at least one** TTS provider configured to produce a non-silent video. **Pick one of the two options below** based on which key you have, and append the matching block to `.archon/.env`.

**Option A — Cartesia (recommended, free tier works):**

1. Sign up at https://cartesia.ai and grab an API key from the dashboard.
2. Append to `.archon/.env`:
   ```env
   CARTESIA_API_KEY=sk_car_...
   ```

**Option B — ElevenLabs (also unlocks SFX and music):**

1. Sign up at https://elevenlabs.io and grab an API key from your profile.
2. Append to `.archon/.env`:
   ```env
   ELEVENLABS_API_KEY=sk_...
   ```
3. Optional add-ons (only on a paid plan for music):
   ```env
   SFX_PROVIDER=elevenlabs       # opt-in sound effects
   MUSIC_PROVIDER=elevenlabs     # opt-in background music (paid tier required)
   ```

You can set both keys if you have them — the workflow auto-detects. Force a specific one with `VOICE_PROVIDER=cartesia` or `VOICE_PROVIDER=elevenlabs`.

**If neither key is set**, voice generation exits silently and you get a video with no audio (fail-safe by design — `generate-audio` exits 0 with no manifest, and `build-composition` builds a silent version).

---

## Run

```bash
archon workflow run remotion-idea-to-video --no-worktree ""
archon workflow run remotion-idea-to-video --no-worktree "marketing https://your-site.com"
archon workflow run remotion-idea-to-video --no-worktree "article https://some-blog.com/post"
archon workflow run remotion-idea-to-video --no-worktree "idea How vector databases work, in 40 seconds, for backend engineers"
```

First run scaffolds the Remotion project (`package.json`, `src/`, `remotion.config.ts`, etc.) into the repo root automatically. Subsequent runs detect the existing project and skip scaffolding — **don't scaffold manually.**

---

## Optional env (in `.archon/.env`)

| Variable | Purpose |
|---|---|
| `VOICE_PROVIDER=cartesia\|elevenlabs\|none` | Force TTS provider (default: auto-detect) |
| `SFX_PROVIDER=elevenlabs` | Opt in to sound effects |
| `MUSIC_PROVIDER=elevenlabs` | Opt in to background music (paid ElevenLabs tier) |
| `RENDER_ENABLED=false` | Skip mp4 render + archive |
| `CLAUDE_BIN_PATH=/path/to/claude` | If Archon can't find the `claude` binary |
| `ELEVENLABS_VOICE_ID=...` | Override default voice (Bella, free-tier-safe) |
| `ELEVENLABS_STABILITY=0.5` | Voice stability (0–1) |
| `ELEVENLABS_SIMILARITY=0.8` | Voice similarity boost (0–1) |
| `ELEVENLABS_STYLE=0.25` | Voice style strength (0–1) |
| `ELEVENLABS_SPEED=1.0` | Voice speed multiplier |
| `FORCE_FRESH_RUN=true\|false` | When `true`, the `validate-artifacts` node will attempt to regenerate missing or zero-length audio artifacts (voice/music/sfx) by re-running the respective generation scripts. Useful when resuming a run but artifacts were deleted; intended for development/debugging. |

---

## Output

- **mp4 archive**: `./videos/<YYYY-MM-DD>-<slug>/<slug>.mp4` (gitignored)
- **Composition source**: `./src/<CompositionId>/` (committable — grows over time)
- **Audio assets**: `./public/{voiceover,music,sfx}/...` (gitignored)
- **Preview every video together**: `npx remotion studio`

---

## Optional: brand overlay

```bash
cp .archon/brand.example.yaml .archon/brand.yaml
```

Edit palette, font, logo watermark, voice tone, music mood. Missing file ⇒ neutral defaults.

---

## Troubleshooting

These are the failure modes that hit the original development sessions, with fixes.

### `FATAL: the remotion-best-practices skill is not installed`
The first node (`check-skill`) couldn't find `SKILL.md`. Run `npx skills add remotion-dev/skills --yes` from the repo root.

### `command not found: claude` (during a `command` node)
Either `claude` isn't on PATH, or Archon couldn't auto-discover it. Set `CLAUDE_BIN_PATH=/full/path/to/claude` in `.archon/.env`.

### ElevenLabs returns HTTP 402
Default voice was a paid-tier-only "library" voice. Workflow now defaults to **Bella** (`hpp4J3VqNfWAUOO0d1Us`), a "premade" voice every account has. If you customized `ELEVENLABS_VOICE_ID`, switch back to a premade voice or upgrade your plan.

### Rendered video is silent even though voice succeeded earlier
Archon caches by `workflow_run_id` + `node_id`. If you `rm -rf`'d artifacts mid-development, the next run will skip "completed" audio nodes but find no audio files. Fix: start a fresh run (new run ID), or delete the stale row from `archon.db`.

### `import.meta.glob is not a function` in Studio
This was patched — the registry is now generated statically by the `regenerate-registry` node into `src/compositions.gen.ts`. If you see this, you're on a stale checkout; pull the latest.

### Scaffold step wiped out `.git/`
Patched — the workflow now strips the scaffold's `.git/`, `.gitignore`, and `README.md` before merging. If your local history is gone, your branch on origin is fine — re-clone or use `git init && remote add && fetch`.

### Workflow says "Skipped (prior_success)" on a fresh run
You're resuming a prior run, not starting fresh. Use a new workflow run ID, or clear the matching row in `archon.db`.

### `archon validate` errors before running
Run `archon validate workflows` and `archon validate commands` after any edits to `.archon/workflows/*.yaml` or `.archon/commands/*.md`. Cheaper than a real run.

---

## Anatomy (for agents reading this to debug deeper)

```
.archon/
├── workflows/remotion-idea-to-video.yaml   # 15-node DAG, 3 modes, opt-in audio
├── commands/
│   ├── remotion-build-composition.md    # builder contract + animation rules
│   └── remotion-iterate.md              # fixer contract (scoped)
├── scripts/
│   ├── _audio_common.py                 # env loader + brand yaml reader
│   ├── generate_voiceover.py            # Cartesia or ElevenLabs TTS
│   ├── generate_music.py                # ElevenLabs music (opt-in)
│   └── generate_sfx.py                  # ElevenLabs SFX (opt-in)
├── brand.example.yaml                   # optional palette/font/watermark/tone
├── config.yaml                          # repo-level archon config
└── .env                                 # API keys (gitignored)

.claude/skills/
├── remotion-best-practices/             # symlink to .agents/skills/...
├── visual-diagrams/                     # hub-and-spoke / flow / comparison
└── archon/                              # workflow-authoring docs
```

The DAG: `check-skill → fetch-source → derive-slug + plan-video → (generate-audio + generate-sfx + generate-music) → build-composition → regenerate-registry → qa-review →? iterate → verify → archive-render → summarize`. See `WORKSHOP.md` for the full mermaid diagram and design notes.
