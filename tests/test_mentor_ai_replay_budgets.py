from __future__ import annotations

import unittest

from scripts.mentor_ai_replay import provider_budget_limits


class ProviderBudgetLimitsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "replayStartUtc": "2025-10-27T00:00:00Z",
            "replayEndUtc": "2025-10-27T01:00:00Z",
            "maximumMapScoutPromptBytes": 10000,
            "maximumMapReviewPromptBytes": 8000,
            "maximumRefinementPromptBytes": 12000,
            "maximumTriggerPromptBytes": 16000,
            "maximumPendingPromptBytes": 12000,
            "scoutMaxOutputTokens": 1600,
            "reviewerMaxOutputTokens": 4096,
            "estimatedImageTokensPerCall": 2048,
        }

    def test_manual_default_covers_two_requests_per_replay_minute(self) -> None:
        run_calls, total_calls, run_tokens, total_tokens = provider_budget_limits(
            self.config, "manual-codex"
        )

        self.assertEqual(run_calls, 122)
        self.assertEqual(total_calls, 122)
        self.assertGreater(run_tokens, 0)
        self.assertEqual(total_tokens, run_tokens)

    def test_manual_explicit_limits_override_duration_defaults(self) -> None:
        config = {
            **self.config,
            "maximumManualCallsPerRun": 300,
            "maximumManualCalls": 500,
            "maximumManualTokensPerRun": 700000,
            "maximumManualTotalTokens": 900000,
        }

        self.assertEqual(
            provider_budget_limits(config, "manual-codex"),
            (300, 500, 700000, 900000),
        )

    def test_codex_cli_keeps_cost_guard_defaults(self) -> None:
        self.assertEqual(
            provider_budget_limits(self.config, "codex-cli"),
            (220, 500, 2_000_000, 4_000_000),
        )


if __name__ == "__main__":
    unittest.main()
