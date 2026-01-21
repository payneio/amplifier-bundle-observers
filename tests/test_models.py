"""Tests for the observer bundle models."""

from datetime import datetime

import pytest

from amplifier_bundle_observers.models import (
    ExecutionConfig,
    HookConfig,
    Observation,
    ObservationsModuleConfig,
    ObserverConfig,
    Severity,
    SourceType,
    Status,
    WatchConfig,
    WatchType,
)


class TestObservation:
    """Tests for the Observation model."""

    def test_create_observation(self):
        """Test creating a new observation."""
        obs = Observation.create(
            observer="Test Observer",
            content="Found an issue",
            severity="high",
            source_type="file",
            source_ref="test.py:10",
            metadata={"category": "security"},
        )

        assert obs.observer == "Test Observer"
        assert obs.content == "Found an issue"
        assert obs.severity == Severity.HIGH
        assert obs.status == Status.OPEN
        assert obs.source_type == SourceType.FILE
        assert obs.source_ref == "test.py:10"
        assert obs.metadata == {"category": "security"}
        assert obs.id is not None
        assert obs.created_at is not None

    def test_create_with_enum_severity(self):
        """Test creating observation with enum severity."""
        obs = Observation.create(
            observer="Test",
            content="Test content",
            severity=Severity.CRITICAL,
        )
        assert obs.severity == Severity.CRITICAL

    def test_acknowledge_observation(self):
        """Test acknowledging an observation."""
        obs = Observation.create(
            observer="Test",
            content="Test",
            severity="medium",
        )
        assert obs.status == Status.OPEN
        assert obs.acknowledged_at is None

        obs.acknowledge()

        assert obs.status == Status.ACKNOWLEDGED
        assert obs.acknowledged_at is not None

    def test_resolve_observation(self):
        """Test resolving an observation."""
        obs = Observation.create(
            observer="Test",
            content="Test",
            severity="low",
        )

        obs.resolve(note="Fixed in commit abc123")

        assert obs.status == Status.RESOLVED
        assert obs.resolved_at is not None
        assert obs.resolution_note == "Fixed in commit abc123"

    def test_resolve_without_note(self):
        """Test resolving without a note."""
        obs = Observation.create(
            observer="Test",
            content="Test",
            severity="info",
        )

        obs.resolve()

        assert obs.status == Status.RESOLVED
        assert obs.resolution_note is None

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        obs = Observation.create(
            observer="Test Observer",
            content="Test content",
            severity="high",
            source_type="file",
            source_ref="test.py:42",
            metadata={"key": "value"},
        )
        obs.acknowledge()

        # Serialize
        data = obs.to_dict()

        # Deserialize
        restored = Observation.from_dict(data)

        assert restored.id == obs.id
        assert restored.observer == obs.observer
        assert restored.content == obs.content
        assert restored.severity == obs.severity
        assert restored.status == obs.status
        assert restored.source_type == obs.source_type
        assert restored.source_ref == obs.source_ref
        assert restored.metadata == obs.metadata


class TestWatchConfig:
    """Tests for WatchConfig."""

    def test_files_watch_config(self):
        """Test creating files watch config."""
        config = WatchConfig.from_dict({
            "type": "files",
            "paths": ["src/**/*.py", "tests/**/*.py"],
        })

        assert config.type == WatchType.FILES
        assert config.paths == ["src/**/*.py", "tests/**/*.py"]

    def test_conversation_watch_config(self):
        """Test creating conversation watch config."""
        config = WatchConfig.from_dict({
            "type": "conversation",
            "include_tool_calls": True,
            "include_reasoning": False,
        })

        assert config.type == WatchType.CONVERSATION
        assert config.include_tool_calls is True
        assert config.include_reasoning is False

    def test_to_dict(self):
        """Test serializing watch config."""
        config = WatchConfig(
            type=WatchType.FILES,
            paths=["**/*.py"],
        )

        data = config.to_dict()

        assert data["type"] == "files"
        assert data["paths"] == ["**/*.py"]


class TestObserverConfig:
    """Tests for ObserverConfig."""

    def test_from_dict(self):
        """Test creating observer config from dict."""
        config = ObserverConfig.from_dict({
            "name": "Security Reviewer",
            "role": "Security analysis",
            "focus": "Look for vulnerabilities",
            "model": "claude-sonnet-4-20250514",
            "timeout": 45,
            "watch": [
                {"type": "files", "paths": ["src/**/*.py"]},
                {"type": "conversation", "include_tool_calls": True},
            ],
            "metadata": {"category": "security"},
        })

        assert config.name == "Security Reviewer"
        assert config.role == "Security analysis"
        assert config.focus == "Look for vulnerabilities"
        assert config.model == "claude-sonnet-4-20250514"
        assert config.timeout == 45
        assert len(config.watch) == 2
        assert config.watch[0].type == WatchType.FILES
        assert config.watch[1].type == WatchType.CONVERSATION
        assert config.metadata == {"category": "security"}
        assert config.enabled is True  # Default

    def test_disabled_observer(self):
        """Test disabled observer."""
        config = ObserverConfig.from_dict({
            "name": "Test",
            "role": "Test",
            "focus": "Test",
            "model": "test-model",
            "enabled": False,
            "watch": [],
        })

        assert config.enabled is False


class TestExecutionConfig:
    """Tests for ExecutionConfig."""

    def test_defaults(self):
        """Test default values."""
        config = ExecutionConfig.from_dict({})

        assert config.mode == "parallel_sync"
        assert config.max_concurrent == 10
        assert config.timeout_per_observer == 30
        assert config.on_timeout == "skip"

    def test_custom_values(self):
        """Test custom values."""
        config = ExecutionConfig.from_dict({
            "mode": "parallel_sync",
            "max_concurrent": 5,
            "timeout_per_observer": 60,
            "on_timeout": "fail",
        })

        assert config.max_concurrent == 5
        assert config.timeout_per_observer == 60
        assert config.on_timeout == "fail"


class TestHookConfig:
    """Tests for HookConfig."""

    def test_from_dict(self):
        """Test creating hook config."""
        config = HookConfig.from_dict({
            "trigger": "orchestrator:complete",
            "priority": 10,
        })

        assert config.trigger == "orchestrator:complete"
        assert config.priority == 10

    def test_default_priority(self):
        """Test default priority."""
        config = HookConfig.from_dict({"trigger": "message:received"})

        assert config.priority == 5


class TestObservationsModuleConfig:
    """Tests for ObservationsModuleConfig."""

    def test_full_config(self):
        """Test parsing full module config."""
        config = ObservationsModuleConfig.from_dict({
            "hooks": [
                {"trigger": "orchestrator:complete", "priority": 5},
            ],
            "execution": {
                "max_concurrent": 2,
                "timeout_per_observer": 30,
            },
            "observers": [
                {
                    "name": "Quick Scanner",
                    "role": "Fast scan",
                    "focus": "Obvious errors",
                    "model": "claude-3-5-haiku-latest",
                    "timeout": 15,
                    "watch": [{"type": "files", "paths": ["**/*.py"]}],
                },
                {
                    "name": "Deep Reviewer",
                    "role": "Thorough analysis",
                    "focus": "Architecture and security",
                    "model": "claude-sonnet-4-20250514",
                    "timeout": 60,
                    "watch": [
                        {"type": "files", "paths": ["src/**/*.py"]},
                        {"type": "conversation"},
                    ],
                },
            ],
        })

        assert len(config.hooks) == 1
        assert config.hooks[0].trigger == "orchestrator:complete"
        assert config.execution.max_concurrent == 2
        assert len(config.observers) == 2
        assert config.observers[0].name == "Quick Scanner"
        assert config.observers[1].name == "Deep Reviewer"

    def test_default_hook(self):
        """Test default hook when none specified."""
        config = ObservationsModuleConfig.from_dict({
            "observers": [],
        })

        assert len(config.hooks) == 1
        assert config.hooks[0].trigger == "orchestrator:complete"

    def test_empty_config(self):
        """Test empty config."""
        config = ObservationsModuleConfig.from_dict({})

        assert len(config.hooks) == 1  # Default hook
        assert len(config.observers) == 0
