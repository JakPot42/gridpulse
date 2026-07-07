"""Tests for brief.py -- Claude Haiku stress-driver narrative brief.

Regression coverage for a real gap: generate_brief()'s live-mode path had
no try/except at all around client.messages.create() -- a live-mode
Claude failure propagated as a raw, unhandled provider exception. Its own
twin, water_monitor/brief.py, already wrapped the identical call in
try/except -> RuntimeError; gridpulse's copy had drifted. Fixed to match.

Phase 6, Cluster 5 consistency pass: generate_brief() now delegates its
live-mode call to the shared claude_brief.call_claude(), which constructs
its own anthropic.Anthropic client internally -- the mock patch target
moved from brief.anthropic.Anthropic to claude_brief.anthropic.Anthropic,
and the raised exception is claude_brief.ClaudeCallError instead of a
locally-defined RuntimeError. Same guarantee either way: a live-mode
Claude failure surfaces as a clear, raised error, never silent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch

import pytest

from brief import generate_brief
from claude_brief import ClaudeCallError
from stress_engine import build_snapshot


def _snap():
    return build_snapshot(
        region="CAL",
        hour="2026-07-07T14:00",
        demand_mwh=60000,
        solar_mwh=5000,
        wind_mwh=3000,
        firm_mwh=52000,
    )


class TestGenerateBriefDemoMode:
    def test_demo_mode_returns_seeded_brief(self):
        text = generate_brief(_snap(), demo_mode=True)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_demo_mode_falls_back_to_default_for_unknown_region(self):
        snap = _snap()
        snap.region = "ZZ"
        text = generate_brief(snap, demo_mode=True)
        assert isinstance(text, str)
        assert len(text) > 0


class TestGenerateBriefLiveMode:
    @patch("claude_brief.anthropic.Anthropic")
    def test_live_mode_returns_stripped_text(self, mock_anthropic_cls, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="  Grid stress is elevated due to low wind.  ")]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        text = generate_brief(_snap(), demo_mode=False)
        assert text == "Grid stress is elevated due to low wind."

    @patch("claude_brief.anthropic.Anthropic")
    def test_live_mode_wraps_api_failure_in_claude_call_error(self, mock_anthropic_cls, monkeypatch):
        """
        Regression test for the fix: a genuine Claude API failure (network
        error, rate limit, etc.) must surface as ClaudeCallError, not
        propagate as a raw, unhandled exception from the anthropic SDK.
        """
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("simulated API failure")
        mock_anthropic_cls.return_value = mock_client

        with pytest.raises(ClaudeCallError, match="Claude API error"):
            generate_brief(_snap(), demo_mode=False)

    @patch("claude_brief.anthropic.Anthropic")
    def test_live_mode_wraps_non_runtime_exceptions_too(self, mock_anthropic_cls, monkeypatch):
        """The bug this fixes: the original code caught nothing at all, so
        even a bare Exception subclass (not just RuntimeError) would have
        propagated raw. Confirm any Exception is wrapped, matching the
        portfolio-wide 'catch Exception, not a specific SDK type' doctrine
        (the Anthropic SDK raises a bare TypeError on a missing/malformed
        key, not anthropic.APIError)."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = TypeError("bad api key")
        mock_anthropic_cls.return_value = mock_client

        with pytest.raises(ClaudeCallError, match="Claude API error"):
            generate_brief(_snap(), demo_mode=False)

    def test_live_mode_missing_api_key_raises_claude_call_error(self, monkeypatch):
        """New behavior from the shared claude_brief.call_claude(): a missing
        key is checked before any network attempt, rather than surfacing as
        whatever error the SDK happens to raise on empty credentials."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ClaudeCallError, match="ANTHROPIC_API_KEY not set"):
            generate_brief(_snap(), demo_mode=False)
