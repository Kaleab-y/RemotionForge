# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27",
#   "mutagen>=1.47",
# ]
# ///
"""
TTS voiceover generator for the `remotion-idea-to-video` workflow.

Invoked by the `generate-audio` node. Reads narration JSON produced by
`plan-video`, calls the configured TTS provider (Cartesia or ElevenLabs),
writes per-scene MP3 files under the Remotion project's `public/voiceover/`
directory, and emits a manifest with per-scene durations in seconds and frames.

Opt-in: if no provider is configured via env, exits 0 without writing a
manifest — downstream nodes then build a silent composition.

Usage:
    uv run .archon/scripts/generate_voiceover.py <artifacts-dir>

Environment:
    VOICE_PROVIDER        optional: 'cartesia' | 'elevenlabs' | 'none'
                          default: auto-detect from present API keys
    CARTESIA_API_KEY      required when provider resolves to cartesia
    CARTESIA_VOICE_ID     optional override (default: Skylar - Friendly Guide)
    CARTESIA_MODEL        optional override (default: sonic-3)
    ELEVENLABS_API_KEY    required when provider resolves to elevenlabs
    ELEVENLABS_VOICE_ID   optional override (default: Rachel)
    ELEVENLABS_MODEL      optional override (default: eleven_multilingual_v2)
    COMPOSITION_ID        optional override (default: HnStory)
    FPS                   optional override (default: 30)

Output:
    $ARTIFACTS_DIR/project/public/voiceover/<composition_id>/<sceneN>.mp3
    $ARTIFACTS_DIR/audio/voice-manifest.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from mutagen.mp3 import MP3

# Force UTF-8 stdout/stderr so non-ASCII chars (e.g. "→") don't crash on Windows cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from _audio_common import load_project_env, retry_call, make_idempotency_key, probe_audio  # noqa: E402


# Defaults — override via env vars documented in the module docstring.
DEFAULT_CARTESIA_VOICE = "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4"  # Skylar - Friendly Guide
DEFAULT_CARTESIA_MODEL = "sonic-3"
DEFAULT_CARTESIA_VERSION = "2026-03-01"

DEFAULT_ELEVENLABS_VOICE = "hpp4J3VqNfWAUOO0d1Us"  # Bella — premade (free-tier safe), warm, informative
DEFAULT_ELEVENLABS_MODEL = "eleven_multilingual_v2"

DEFAULT_COMPOSITION_ID = "HnStory"
DEFAULT_FPS = 30


def resolve_provider() -> str:
    """Return 'cartesia' | 'elevenlabs' | 'none' based on env."""
    explicit = (os.environ.get("VOICE_PROVIDER") or "").strip().lower()
    if explicit in {"cartesia", "elevenlabs", "none"}:
        if explicit == "cartesia" and not os.environ.get("CARTESIA_API_KEY"):
            sys.exit("FATAL: VOICE_PROVIDER=cartesia but CARTESIA_API_KEY is not set")
        if explicit == "elevenlabs" and not os.environ.get("ELEVENLABS_API_KEY"):
            sys.exit("FATAL: VOICE_PROVIDER=elevenlabs but ELEVENLABS_API_KEY is not set")
        return explicit
    if explicit:
        sys.exit(f"FATAL: unknown VOICE_PROVIDER={explicit!r} (expected cartesia|elevenlabs|none)")

    if os.environ.get("CARTESIA_API_KEY"):
        return "cartesia"
    if os.environ.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    return "none"


def synthesize_cartesia(text: str, out_path: Path, idempotency_key: str | None = None) -> None:
    api_key = os.environ["CARTESIA_API_KEY"]
    voice_id = os.environ.get("CARTESIA_VOICE_ID", DEFAULT_CARTESIA_VOICE)
    model_id = os.environ.get("CARTESIA_MODEL", DEFAULT_CARTESIA_MODEL)
    version = os.environ.get("CARTESIA_VERSION", DEFAULT_CARTESIA_VERSION)

    body = {
        "model_id": model_id,
        "transcript": text,
        "voice": {"mode": "id", "id": voice_id},
        "output_format": {
            "container": "mp3",
            "sample_rate": 44100,
            "bit_rate": 128000,
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Cartesia-Version": version,
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            "https://api.cartesia.ai/tts/bytes",
            headers=headers,
            json=body,
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Cartesia TTS returned {resp.status_code}: {resp.text[:500]}"
        )
    out_path.write_bytes(resp.content)


def synthesize_elevenlabs(text: str, out_path: Path, idempotency_key: str | None = None) -> None:
    api_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE)
    model_id = os.environ.get("ELEVENLABS_MODEL", DEFAULT_ELEVENLABS_MODEL)

    body = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": float(os.environ.get("ELEVENLABS_STABILITY", "0.5")),
            "similarity_boost": float(os.environ.get("ELEVENLABS_SIMILARITY", "0.8")),
            "style": float(os.environ.get("ELEVENLABS_STYLE", "0.25")),
            "speed": float(os.environ.get("ELEVENLABS_SPEED", "1.0")),
        },
    }

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=body,
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS returned {resp.status_code}: {resp.text[:500]}"
        )
    out_path.write_bytes(resp.content)


def measure_duration_seconds(path: Path) -> float:
    return float(MP3(path).info.length)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: generate_voiceover.py <artifacts-dir>")

    artifacts_dir = Path(sys.argv[1]).resolve()
    if not artifacts_dir.is_dir():
        sys.exit(f"FATAL: artifacts dir not found: {artifacts_dir}")

    # Load project-level .archon/.env from the invoking cwd (archon cwd = repo root)
    load_project_env(Path.cwd())

    provider = resolve_provider()
    if provider == "none":
        print("Voice: not configured — skipping voiceover generation (silent video).")
        print("To enable: set CARTESIA_API_KEY or ELEVENLABS_API_KEY in .archon/.env")
        return

    narration_path = artifacts_dir / "narration.json"
    if not narration_path.exists():
        sys.exit(f"FATAL: narration.json missing — expected at {narration_path}")

    narration = json.loads(narration_path.read_text())
    composition_id = narration.get("composition_id") or os.environ.get(
        "COMPOSITION_ID", DEFAULT_COMPOSITION_ID
    )
    fps = int(narration.get("fps") or os.environ.get("FPS", DEFAULT_FPS))
    scenes = narration.get("scenes") or []
    if not scenes:
        sys.exit("FATAL: narration.json has no scenes[]")

    # Audio lives under the repo's own public/voiceover/<compositionId>/ so
    # staticFile() resolves directly. Archon runs this script with cwd =
    # repo root (same place as .archon/), so Path.cwd() is the project root.
    project_root = Path.cwd()
    out_dir = project_root / "public" / "voiceover" / composition_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Voice: provider={provider}, composition={composition_id}, scenes={len(scenes)}")

    manifest_scenes = []
    total_seconds = 0.0

    for scene in scenes:
        scene_id = scene["id"]
        text = scene["text"].strip()
        if not text:
            sys.exit(f"FATAL: scene {scene_id!r} has empty narration text")

        out_path = out_dir / f"{scene_id}.mp3"
        print(f"  → {scene_id}: synthesizing ({len(text)} chars)")

        try:
            # Retry the TTS call with exponential backoff on transient failures.
            id_key = make_idempotency_key(provider, composition_id, scene_id, text[:400])
            if provider == "cartesia":
                retry_call(lambda: synthesize_cartesia(text, out_path, idempotency_key=id_key), attempts=3, base_delay=1.0)
            else:
                retry_call(lambda: synthesize_elevenlabs(text, out_path, idempotency_key=id_key), attempts=3, base_delay=1.0)
        except Exception as e:
            sys.exit(f"FATAL: TTS failed after retries: {e}")

        info = probe_audio(out_path)
        duration_s = float(info.get("duration") or 0.0)
        duration_frames = round(duration_s * fps)
        total_seconds += duration_s

        # Path is relative to public/ so staticFile(path) works in Remotion.
        rel_path = f"voiceover/{composition_id}/{scene_id}.mp3"
        manifest_scenes.append(
            {
                "id": scene_id,
                "path": rel_path,
                "duration_s": round(duration_s, 4),
                "duration_frames": duration_frames,
                "sample_rate": info.get("sample_rate"),
                "channels": info.get("channels"),
            }
        )
        print(f"    wrote {out_path.name} — {duration_s:.2f}s ({duration_frames}f) — sr={info.get('sample_rate')} ch={info.get('channels')}")

    manifest = {
        "provider": provider,
        "model_id": (
            os.environ.get("CARTESIA_MODEL", DEFAULT_CARTESIA_MODEL)
            if provider == "cartesia"
            else os.environ.get("ELEVENLABS_MODEL", DEFAULT_ELEVENLABS_MODEL)
        ),
        "voice_id": (
            os.environ.get("CARTESIA_VOICE_ID", DEFAULT_CARTESIA_VOICE)
            if provider == "cartesia"
            else os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE)
        ),
        "composition_id": composition_id,
        "fps": fps,
        "scenes": manifest_scenes,
        "total_duration_s": round(total_seconds, 4),
        "total_duration_frames": sum(s["duration_frames"] for s in manifest_scenes),
    }

    manifest_path = artifacts_dir / "audio" / "voice-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(
        f"Voice: {len(scenes)} files, total "
        f"{total_seconds:.2f}s / {manifest['total_duration_frames']} frames"
    )
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
