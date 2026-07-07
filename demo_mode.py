"""
demo_mode.py — canonical DEMO_MODE boolean-parsing convention for the
Installation Resilience cluster (Phase 6, Cluster 5).

Two different conventions were found across the 3 source projects:
GridPulse and Water Security Stress Monitor both use a default-true,
permissive-negative read (`os.getenv("DEMO_MODE", "True").lower() not in
("false", "0", "no")` -- anything not an explicit "off" string counts as
demo mode); joule uses a strict positive-equality read
(`os.environ.get("DEMO_MODE", "True") == "True"` -- only the literal
string "True" is truthy, "true"/"1"/"yes" would all silently read as
DEMO_MODE=False). Same class of drift found and reconciled in every prior
Phase 6 cluster's own demo_mode.py.

is_demo_mode() doesn't force a UX change on any tool -- it only
centralizes the parsing convention (permissive, env var, default True) so
the strict-vs-permissive drift stops here.
"""
import os


def is_demo_mode(default: bool = True) -> bool:
    """Read DEMO_MODE from the environment, defaulting to `default` if unset."""
    return os.getenv("DEMO_MODE", str(default)).lower() in ("1", "true", "yes")
