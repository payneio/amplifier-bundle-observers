"""Tests for the hooks-observations module."""

import json

import pytest

from amplifier_bundle_observers.hooks_observations import ObservationHooks
from amplifier_bundle_observers.models import (
    ExecutionConfig,
    HookConfig,
    ObservationsModuleConfig,
    ObserverConfig,
    WatchConfig,
    WatchType,
)


class MockCoordinator:
    """Mock coordinator for testing hooks."""

    def __init__(self):
        self.registered_hooks = []
        self.tools = {}

    def get(self, mount_type: str, name: str):
        """Get a mounted tool."""
        if mount_type == "tools":
            return self.tools.get(name)
        return None

    def get_capability(self, name: str):
        """Mock capability getter."""
        return None  # No spawn capability in tests


@pytest.fixture
def config():
    """Create a test configuration."""
    return ObservationsModuleConfig(
        hooks=[HookConfig(trigger="orchestrator:complete", priority=5)],
        execution=ExecutionConfig(
            max_concurrent=2,
            timeout_per_observer=30,
            on_timeout="skip",
        ),
        observers=[
            ObserverConfig(
                name="Test Scanner",
                role="Test role",
                focus="Test focus",
                model="test-model",
                timeout=15,
                watch=[
                    WatchConfig(type=WatchType.FILES, paths=["src/**/*.py"]),
                ],
            ),
        ],
    )


@pytest.fixture
def coordinator():
    """Create a mock coordinator."""
    return MockCoordinator()


@pytest.fixture
def hooks(config, coordinator):
    """Create hooks instance."""
    return ObservationHooks(config, coordinator)


class TestObserverResultParsing:
    """Tests for parsing observer results."""

    def test_parse_valid_json_response(self, hooks):
        """Test parsing a valid JSON response."""
        result = json.dumps({
            "observations": [
                {
                    "content": "Found an issue",
                    "severity": "high",
                    "source_ref": "test.py:10",
                    "metadata": {"category": "quality"},
                }
            ]
        })

        parsed = hooks._parse_observer_result(result, "Test Observer")

        assert len(parsed["observations"]) == 1
        assert parsed["observations"][0]["content"] == "Found an issue"
        assert parsed["observations"][0]["observer"] == "Test Observer"
        assert parsed["observations"][0]["status"] == "open"

    def test_parse_json_in_code_block(self, hooks):
        """Test parsing JSON wrapped in markdown code block."""
        result = """Here are my observations:

```json
{
  "observations": [
    {
      "content": "Missing type hint",
      "severity": "medium"
    }
  ]
}
```

That's all I found."""

        parsed = hooks._parse_observer_result(result, "Test Observer")

        assert len(parsed["observations"]) == 1
        assert parsed["observations"][0]["content"] == "Missing type hint"

    def test_parse_json_in_plain_code_block(self, hooks):
        """Test parsing JSON in code block without json marker."""
        result = """
```
{
  "observations": [
    {"content": "Issue found", "severity": "low"}
  ]
}
```
"""

        parsed = hooks._parse_observer_result(result, "Test Observer")

        assert len(parsed["observations"]) == 1

    def test_parse_empty_observations(self, hooks):
        """Test parsing response with no issues."""
        result = json.dumps({"observations": []})

        parsed = hooks._parse_observer_result(result, "Test Observer")

        assert parsed["observations"] == []

    def test_parse_plain_text_fallback(self, hooks):
        """Test fallback for plain text response."""
        result = "I found a significant security vulnerability in the authentication module that could allow unauthorized access."

        parsed = hooks._parse_observer_result(result, "Test Observer")

        # Should create a single info-level observation
        assert len(parsed["observations"]) == 1
        assert parsed["observations"][0]["severity"] == "info"
        assert parsed["observations"][0]["metadata"].get("parse_error") is True

    def test_parse_no_issues_text(self, hooks):
        """Test that 'no issues' text doesn't create observation."""
        result = "No issues found. Everything looks good."

        parsed = hooks._parse_observer_result(result, "Test Observer")

        # Should not create observation for "no issues" responses
        assert parsed["observations"] == []

    def test_parse_dict_result(self, hooks):
        """Test parsing dict result (from spawn_capability)."""
        result = {
            "output": json.dumps({
                "observations": [
                    {"content": "Test issue", "severity": "high"}
                ]
            })
        }

        parsed = hooks._parse_observer_result(result, "Test Observer")

        assert len(parsed["observations"]) == 1
        assert parsed["observations"][0]["content"] == "Test issue"

    def test_parse_adds_defaults(self, hooks):
        """Test that parsing adds default values."""
        result = json.dumps({
            "observations": [
                {"content": "Issue", "severity": "high"}
            ]
        })

        parsed = hooks._parse_observer_result(result, "Observer")

        obs = parsed["observations"][0]
        assert obs["observer"] == "Observer"
        assert obs["status"] == "open"
        assert obs["source_type"] == "mixed"
        assert "metadata" in obs


class TestResultAggregation:
    """Tests for aggregating results from multiple observers."""

    def test_aggregate_multiple_results(self, hooks):
        """Test aggregating results from multiple observers."""
        results = [
            {
                "observations": [
                    {"content": "Issue 1", "severity": "high", "observer": "A"},
                    {"content": "Issue 2", "severity": "medium", "observer": "A"},
                ]
            },
            {
                "observations": [
                    {"content": "Issue 3", "severity": "critical", "observer": "B"},
                ]
            },
        ]

        aggregated = hooks._aggregate_results(results)

        assert len(aggregated) == 3

    def test_aggregate_with_empty_results(self, hooks):
        """Test aggregating when some observers found nothing."""
        results = [
            {"observations": [{"content": "Issue", "severity": "high", "observer": "A"}]},
            {"observations": []},
            {"observations": []},
        ]

        aggregated = hooks._aggregate_results(results)

        assert len(aggregated) == 1

    def test_aggregate_handles_errors(self, hooks):
        """Test aggregating results with errors."""
        results = [
            {"observations": [{"content": "Issue", "severity": "high", "observer": "A"}]},
            {"error": "timeout"},  # No observations key
            "invalid result",  # Not a dict
        ]

        aggregated = hooks._aggregate_results(results)

        assert len(aggregated) == 1


class TestObservationSummaryFormatting:
    """Tests for formatting observation summaries."""

    def test_format_summary(self, hooks):
        """Test formatting observation summary for context injection."""
        observations = [
            {
                "observer": "Scanner",
                "content": "Missing type hints on public function",
                "severity": "medium",
            },
            {
                "observer": "Scanner",
                "content": "Unused import detected",
                "severity": "low",
            },
            {
                "observer": "Security",
                "content": "Potential SQL injection vulnerability",
                "severity": "critical",
            },
        ]

        summary = hooks._format_observations_summary(observations)

        assert "3 open" in summary
        assert "critical" in summary
        assert "Scanner" in summary
        assert "Security" in summary
        assert "Missing type hints" in summary

    def test_format_summary_truncates_long_content(self, hooks):
        """Test that long observation content is truncated."""
        observations = [
            {
                "observer": "Test",
                "content": "A" * 200,  # Very long content
                "severity": "high",
            },
        ]

        summary = hooks._format_observations_summary(observations)

        # Should truncate to first 100 chars
        assert len(summary) < 250

    def test_format_summary_limits_per_observer(self, hooks):
        """Test that summary limits observations per observer."""
        observations = [
            {"observer": "Scanner", "content": f"Issue {i}", "severity": "low"}
            for i in range(10)
        ]

        summary = hooks._format_observations_summary(observations)

        # Should show top 3 + "and X more"
        assert "and 7 more" in summary


class TestChangeDetection:
    """Tests for change detection logic."""

    def test_file_state_hash_changes_with_content(self, hooks, tmp_path):
        """Test that file state hash changes when files change."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        # Get initial hash
        hash1 = hooks._get_file_state([str(tmp_path / "*.py")])

        # Modify file
        test_file.write_text("modified content")

        # Get new hash
        hash2 = hooks._get_file_state([str(tmp_path / "*.py")])

        assert hash1 != hash2

    def test_file_state_hash_stable(self, hooks, tmp_path):
        """Test that file state hash is stable without changes."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        hash1 = hooks._get_file_state([str(tmp_path / "*.py")])
        hash2 = hooks._get_file_state([str(tmp_path / "*.py")])

        assert hash1 == hash2

    def test_conversation_state_hash(self, hooks):
        """Test conversation state hashing."""
        event1 = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ]
        }

        event2 = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "New message"},
            ]
        }

        hash1 = hooks._get_conversation_state(event1)
        hash2 = hooks._get_conversation_state(event2)

        assert hash1 != hash2

    def test_conversation_state_filters_roles(self, hooks):
        """Test that conversation state filters relevant roles."""
        event = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "system", "content": "System message"},  # Should be filtered
                {"role": "assistant", "content": "Response"},
            ]
        }

        hash1 = hooks._get_conversation_state(event)

        # System message removal shouldn't affect hash since we only include
        # user, assistant, tool
        event_without_system = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Response"},
            ]
        }

        hash2 = hooks._get_conversation_state(event_without_system)

        assert hash1 == hash2
