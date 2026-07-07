"""
claude_brief.py — shared Claude call wrapper for the Installation
Resilience cluster (Phase 6, Cluster 5).

Every consuming project should call `call_claude()` instead of
constructing its own anthropic.Anthropic client and its own try/except
around messages.create(). Built because the cluster's 3 source projects
had drifted into two genuinely different, both-intentional failure
behaviors for a live-mode Claude call failing:

  - water_monitor/brief.py and (after Step 0's standalone fix)
    gridpulse/brief.py: raise, loudly. A `brief` command that can't get a
    real brief should fail, not silently succeed with the wrong content.
  - joule/brief.py: catch and fall back to the already-computed
    deterministic template. A screening tool (`joule smr`, `joule ally`)
    should still show real physics/citation-backed numbers even if the
    narrative-writing step fails -- the score and tier are the substance,
    the brief is prose on top of it.

Neither behavior is a bug -- they're genuinely different, deliberate UX
choices for genuinely different command types (a dedicated "generate me a
brief" command vs. a screening command that includes a brief as one
section of a larger report). `on_error` makes that choice explicit and
required at the call site instead of leaving it implicit in which
try/except style a given file happened to use.

The Anthropic SDK raises a bare TypeError (not anthropic.APIError) when
api_key is empty or malformed -- catching Exception broadly, not
anthropic.APIError specifically, is deliberate and matches the
portfolio-wide fix already applied elsewhere.
"""
from __future__ import annotations

import os

import anthropic

CLAUDE_MODEL = "claude-haiku-4-5-20251001"


class ClaudeCallError(Exception):
    """Raised for any Claude API failure -- missing key, network error,
    rate limit, malformed response, etc. Wraps the original exception.
    Only ever raised when on_error="raise" (the default)."""


def call_claude(
    messages: list[dict],
    *,
    system: str | None = None,
    max_tokens: int = 400,
    model: str = CLAUDE_MODEL,
    api_key: str | None = None,
    on_error: str = "raise",
    fallback: str | None = None,
) -> str:
    """
    Call Claude and return the response text (content[0].text, stripped).

    on_error="raise" (default): any failure raises ClaudeCallError --
    matches water_monitor's and gridpulse's own brief.py behavior.

    on_error="fallback": any failure returns `fallback` instead of
    raising -- matches joule's brief.py behavior. `fallback` is required
    in this mode (raises ValueError at call time if omitted, not silently
    treated as None).
    """
    if on_error not in ("raise", "fallback"):
        raise ValueError(f'on_error must be "raise" or "fallback", got {on_error!r}')
    if on_error == "fallback" and fallback is None:
        raise ValueError('fallback text is required when on_error="fallback"')

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        if on_error == "fallback":
            return fallback
        raise ClaudeCallError(
            "ANTHROPIC_API_KEY not set. Set it in the environment or pass api_key= explicitly."
        )

    try:
        client = anthropic.Anthropic(api_key=key)
        kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system is not None:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text.strip()
    except Exception as exc:
        if on_error == "fallback":
            return fallback
        raise ClaudeCallError(f"Claude API error: {exc}") from exc
