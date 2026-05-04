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
