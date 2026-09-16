#!/usr/bin/env python3
"""Tests for model and effort discovery across supported harnesses."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
DISCOVERY_SCRIPT = SCRIPTS / "discovery.py"

sys.path.insert(0, str(SCRIPTS))
import discovery  # noqa: E402


class ModelDiscoveryTests(unittest.TestCase):
    def test_antigravity_discovery_parses_agy_models_output(self) -> None:
        raw_output = """gemini-3.8-flash-high     Gemini 3.8 Flash (High)
gemini-3.8-flash-medium   Gemini 3.8 Flash (Medium)
gemini-3.8-flash-low      Gemini 3.8 Flash (Low)
gemini-3.1-pro-high       Gemini 3.1 Pro (High)
claude-sonnet-4-6         Claude Sonnet 4.6 (Thinking)
"""
        models = discovery.parse_agy_models_output(raw_output)
        model_ids = [m["id"] for m in models]
        self.assertIn("gemini-3.8-flash-high", model_ids)
        self.assertIn("gemini-3.1-pro-high", model_ids)
        self.assertIn("claude-sonnet-4-6", model_ids)

        # Check supported effort extraction
        flash_high = next(m for m in models if m["id"] == "gemini-3.8-flash-high")
        self.assertEqual("high", flash_high.get("effort"))

    def test_paginated_discovery_retrieves_all_pages(self) -> None:
        # Simulate paginated fetcher
        pages = [
            {"models": [{"id": "model-p1-1"}, {"id": "model-p1-2"}], "next_page_token": "token2"},
            {"models": [{"id": "model-p2-1"}], "next_page_token": None},
        ]
        def mock_fetcher(page_token=None):
            if page_token is None:
                return pages[0]
            elif page_token == "token2":
                return pages[1]
            raise ValueError("Unknown token")

        results = discovery.fetch_paginated_catalog(mock_fetcher)
        self.assertEqual(["model-p1-1", "model-p1-2", "model-p2-1"], [m["id"] for m in results])

    def test_missing_discovery_produces_blocking_diagnostic(self) -> None:
        with self.assertRaises(discovery.DiscoveryError) as ctx:
            discovery.discover_models("unknown-harness")
        self.assertIn("missing discovery", str(ctx.exception).lower())

        with patch("shutil.which", return_value=None):
            with self.assertRaises(discovery.DiscoveryError) as ctx:
                discovery.discover_antigravity_models()
            self.assertIn("agy", str(ctx.exception).lower())

    def test_catalog_provenance_and_freshness_exposed_without_credentials(self) -> None:
        catalog = discovery.create_catalog_entry(
            harness="antigravity",
            models=[{"id": "gemini-2.5-pro", "contextWindow": 1000000, "supportedEfforts": ["low", "medium", "high"]}],
            provider="google",
            account="user@example.com",
            source_command="agy models",
        )
        self.assertEqual("antigravity", catalog["harness"])
        self.assertIn("provenance", catalog)
        self.assertEqual("agy models", catalog["provenance"]["source"])
        self.assertIn("discovered_at", catalog["provenance"])
        # Ensure no credential keys exist
        raw_json = json.dumps(catalog)
        self.assertNotIn("api_key", raw_json.lower())
        self.assertNotIn("password", raw_json.lower())
        self.assertNotIn("token", raw_json.lower())
        self.assertNotIn("secret", raw_json.lower())

    def test_changing_account_or_provider_invalidates_cache(self) -> None:
        catalog = discovery.create_catalog_entry(
            harness="antigravity",
            models=[{"id": "gemini-2.5-pro", "contextWindow": 1000000}],
            provider="google-work",
            account="alice@work.com",
            source_command="agy models",
        )
        # Valid when provider and account match
        self.assertTrue(discovery.is_catalog_valid(catalog, current_provider="google-work", current_account="alice@work.com"))
        # Invalid when provider changes
        self.assertFalse(discovery.is_catalog_valid(catalog, current_provider="google-personal", current_account="alice@work.com"))
        # Invalid when account changes
        self.assertFalse(discovery.is_catalog_valid(catalog, current_provider="google-work", current_account="bob@work.com"))

    def test_supported_effort_values_rejected_if_unsupported(self) -> None:
        # Only supported effort values
        efforts = discovery.validate_effort("gemini-2.5-pro", "ultra_high", supported_efforts=["low", "medium", "high"])
        self.assertFalse(efforts["valid"])
        self.assertIn("unsupported effort", efforts["error"].lower())

        valid_check = discovery.validate_effort("gemini-2.5-pro", "high", supported_efforts=["low", "medium", "high"])
        self.assertTrue(valid_check["valid"])


if __name__ == "__main__":
    unittest.main()
