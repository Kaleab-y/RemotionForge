# /// script
# requires-python = ">=3.11"
# ///
"""
Shared helpers for the audio-generation scripts
(generate_voiceover.py, generate_music.py, generate_sfx.py).

Intentionally stdlib-only so the helper doesn't force uv to solve an env
just to source it. Each script declares its own PEP 723 deps.
"""
from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Callable, Any
import subprocess
import json
import shutil
import hashlib


def load_project_env(root: Path) -> None:
    """Load .archon/.env into process env if present.

    Archon loads `~/.archon/.env` automatically and (as of recent versions)
    project-level `.archon/.env`, but we keep this as a safety net so the
    scripts are runnable outside Archon too (e.g. for local debugging).
    Never overrides an already-set env var.
    """
    env_file = root / ".archon" / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_brand_yaml(root: Path) -> dict:
    """Return the brand config as a dict, or an empty dict if absent/invalid.

    We avoid a hard YAML dep — the file is tiny and only needs a handful of
    string keys. If a user writes a malformed file we silently fall back to
    defaults rather than failing the whole workflow on an optional feature.
    """
    path = root / ".archon" / "brand.yaml"
    if not path.exists():
        return {}
    try:
        import yaml  # Optional — PyYAML ships with most Pythons, but not all
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def slug_from_composition_id(composition_id: str) -> str:
    """Defensive — return the composition_id unchanged. We treat the planner's
    chosen composition_id as authoritative; callers pass it through."""
    return composition_id


def retry_call(func: Callable[[], Any], attempts: int = 3, base_delay: float = 1.0) -> Any:
    """Retry a no-arg callable with exponential backoff.

    func: callable that takes no arguments. Raises any exception on failure.
    attempts: total attempts (default 3).
    base_delay: initial backoff in seconds; backoff doubles each retry.
    Returns the callable's result or raises the last exception.
    """
    last_exc = None
    for i in range(attempts):
        try:
            return func()
        except Exception as e:
            last_exc = e
            if i + 1 >= attempts:
                break
            sleep_for = base_delay * (2 ** i)
            try:
                time.sleep(sleep_for)
            except KeyboardInterrupt:
                raise
    raise last_exc


def make_idempotency_key(*parts: object) -> str:
    """Create a stable idempotency key from the given parts.

    The key is a deterministic SHA256 hex digest of the joined parts.
    """
    key = "|".join(str(p) for p in parts)
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    # Truncate to 48 chars to be conservative for header length limits.
    return h[:48]


def probe_audio(path: Path) -> dict:
    """Return audio metadata for `path`.

    Attempts to use `ffprobe` for robust metadata. Falls back to mutagen
    if ffprobe is unavailable or fails. Returns dict with keys:
      - duration: float seconds (0.0 if unknown)
      - sample_rate: int or None
      - channels: int or None
    """
    if not path.exists():
        return {"duration": 0.0, "sample_rate": None, "channels": None}

    # Prefer ffprobe when available
    if shutil.which("ffprobe"):
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=sample_rate,channels",
                "-of",
                "json",
                str(path),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(proc.stdout or "{}")
            duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)
            streams = data.get("streams", []) or []
            sample_rate = None
            channels = None
            if streams:
                sr = streams[0].get("sample_rate")
                ch = streams[0].get("channels")
                try:
                    sample_rate = int(sr) if sr is not None else None
                except Exception:
                    sample_rate = None
                try:
                    channels = int(ch) if ch is not None else None
                except Exception:
                    channels = None
            return {"duration": duration, "sample_rate": sample_rate, "channels": channels}
        except Exception:
            # Fall through to mutagen fallback
            pass

    # Fallback: try mutagen (MP3 info)
    try:
        from mutagen.mp3 import MP3  # type: ignore

        audio = MP3(str(path))
        duration = float(getattr(audio.info, "length", 0.0) or 0.0)
        sample_rate = getattr(audio.info, "sample_rate", None)
        channels = getattr(audio.info, "channels", None)
        return {"duration": duration, "sample_rate": sample_rate, "channels": channels}
    except Exception:
        return {"duration": 0.0, "sample_rate": None, "channels": None}
