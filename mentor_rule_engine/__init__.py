"""Deterministic mentor-rule reproduction engine.

The runtime package intentionally has no dependency on the reverse-engineered
casebook. Reference cases are loaded only by the regression runner.
"""

from .engine import (
    EngineConfig,
    MentorRuleEngine,
    RuleCandidate,
    RuleEngineResult,
)

__all__ = [
    "EngineConfig",
    "MentorRuleEngine",
    "RuleCandidate",
    "RuleEngineResult",
]
