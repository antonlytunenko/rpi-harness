"""Deduplication module: track processed items by timestamp."""
from __future__ import annotations

import json
import os


def load_state(path: str) -> dict:
    """Load dedup state from *path*; return ``{}`` if the file does not exist."""
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


def save_state(path: str, state: dict) -> None:
    """Persist *state* to *path* as JSON."""
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2)


def needs_processing(state: dict, item_key: str, updated_at_iso: str) -> bool:
    """Return ``True`` when *updated_at_iso* is later than the stored timestamp.

    Also returns ``True`` when *item_key* is absent from *state*.
    """
    stored = state.get(item_key)
    if stored is None:
        return True
    return updated_at_iso > stored
