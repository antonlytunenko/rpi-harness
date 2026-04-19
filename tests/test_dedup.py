"""Tests for harness.dedup (PLAN step 3.3)."""
import pytest

from harness.dedup import load_state, needs_processing, save_state


def test_needs_processing_returns_true_when_key_absent():
    assert needs_processing({}, "repo:issue:1", "2026-01-01T00:00:00Z") is True


def test_needs_processing_returns_false_when_timestamp_equal():
    state = {"repo:issue:1": "2026-01-01T00:00:00Z"}
    assert needs_processing(state, "repo:issue:1", "2026-01-01T00:00:00Z") is False


def test_needs_processing_returns_true_when_item_is_newer():
    state = {"repo:issue:1": "2026-01-01T00:00:00Z"}
    assert needs_processing(state, "repo:issue:1", "2026-01-02T00:00:00Z") is True


def test_load_state_returns_empty_dict_when_file_missing(tmp_path):
    result = load_state(str(tmp_path / "nonexistent.json"))
    assert result == {}


def test_save_and_load_state_round_trip(tmp_path):
    path = str(tmp_path / "state.json")
    original = {"key": "value", "nested": {"a": 1}}
    save_state(path, original)
    assert load_state(path) == original
