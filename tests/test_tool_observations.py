"""Tests for the observations tool module."""

import pytest

from amplifier_bundle_observers.models import Severity, Status
from amplifier_bundle_observers.tool_observations import ObservationsTool


@pytest.fixture
def tool():
    """Create a fresh tool instance for each test."""
    return ObservationsTool()


class TestObservationsTool:
    """Tests for ObservationsTool."""

    @pytest.mark.asyncio
    async def test_create_single_observation(self, tool):
        """Test creating a single observation."""
        result = await tool.execute({
            "operation": "create",
            "observer": "Test Observer",
            "content": "Found a bug",
            "severity": "high",
            "source_type": "file",
            "source_ref": "test.py:10",
        })

        assert result.success is True
        assert result.output["status"] == "created"
        assert result.output["observation"]["observer"] == "Test Observer"
        assert result.output["observation"]["content"] == "Found a bug"
        assert result.output["observation"]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_create_batch_observations(self, tool):
        """Test creating multiple observations at once."""
        result = await tool.execute({
            "operation": "create_batch",
            "observations": [
                {
                    "observer": "Scanner",
                    "content": "Issue 1",
                    "severity": "high",
                },
                {
                    "observer": "Scanner",
                    "content": "Issue 2",
                    "severity": "medium",
                },
                {
                    "observer": "Reviewer",
                    "content": "Issue 3",
                    "severity": "low",
                },
            ],
        })

        assert result.success is True
        assert result.output["status"] == "created"
        assert result.output["count"] == 3
        assert result.output["by_severity"]["high"] == 1
        assert result.output["by_severity"]["medium"] == 1
        assert result.output["by_severity"]["low"] == 1

    @pytest.mark.asyncio
    async def test_list_observations(self, tool):
        """Test listing observations."""
        # Create some observations
        await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "A", "content": "Issue 1", "severity": "critical"},
                {"observer": "A", "content": "Issue 2", "severity": "high"},
                {"observer": "B", "content": "Issue 3", "severity": "medium"},
            ],
        })

        # List all
        result = await tool.execute({"operation": "list"})

        assert result.success is True
        assert result.output["count"] == 3
        assert result.output["total"] == 3

    @pytest.mark.asyncio
    async def test_list_with_status_filter(self, tool):
        """Test filtering observations by status."""
        # Create observations
        create_result = await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "A", "content": "Issue 1", "severity": "high"},
                {"observer": "A", "content": "Issue 2", "severity": "high"},
            ],
        })

        # Acknowledge one
        obs_id = create_result.output["observations"][0]["id"]
        await tool.execute({
            "operation": "acknowledge",
            "observation_id": obs_id,
        })

        # List only open
        result = await tool.execute({
            "operation": "list",
            "filters": {"status": "open"},
        })

        assert result.output["count"] == 1

        # List only acknowledged
        result = await tool.execute({
            "operation": "list",
            "filters": {"status": "acknowledged"},
        })

        assert result.output["count"] == 1

    @pytest.mark.asyncio
    async def test_list_with_severity_filter(self, tool):
        """Test filtering by severity."""
        await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "A", "content": "Critical", "severity": "critical"},
                {"observer": "A", "content": "High", "severity": "high"},
                {"observer": "A", "content": "Medium", "severity": "medium"},
                {"observer": "A", "content": "Low", "severity": "low"},
            ],
        })

        # Filter critical and high
        result = await tool.execute({
            "operation": "list",
            "filters": {"severity": ["critical", "high"]},
        })

        assert result.output["count"] == 2

    @pytest.mark.asyncio
    async def test_list_with_observer_filter(self, tool):
        """Test filtering by observer."""
        await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "Scanner", "content": "Issue 1", "severity": "high"},
                {"observer": "Scanner", "content": "Issue 2", "severity": "high"},
                {"observer": "Reviewer", "content": "Issue 3", "severity": "high"},
            ],
        })

        result = await tool.execute({
            "operation": "list",
            "filters": {"observer": "Scanner"},
        })

        assert result.output["count"] == 2

    @pytest.mark.asyncio
    async def test_list_sorted_by_severity(self, tool):
        """Test sorting by severity."""
        await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "A", "content": "Low", "severity": "low"},
                {"observer": "A", "content": "Critical", "severity": "critical"},
                {"observer": "A", "content": "Medium", "severity": "medium"},
            ],
        })

        result = await tool.execute({
            "operation": "list",
            "sort_by": "severity",
        })

        observations = result.output["observations"]
        assert observations[0]["severity"] == "critical"
        assert observations[1]["severity"] == "medium"
        assert observations[2]["severity"] == "low"

    @pytest.mark.asyncio
    async def test_get_observation(self, tool):
        """Test getting a specific observation."""
        create_result = await tool.execute({
            "operation": "create",
            "observer": "Test",
            "content": "Test issue",
            "severity": "high",
        })

        obs_id = create_result.output["observation"]["id"]

        result = await tool.execute({
            "operation": "get",
            "observation_id": obs_id,
        })

        assert result.success is True
        assert result.output["observation"]["id"] == obs_id
        assert result.output["observation"]["content"] == "Test issue"

    @pytest.mark.asyncio
    async def test_get_nonexistent_observation(self, tool):
        """Test getting observation that doesn't exist."""
        result = await tool.execute({
            "operation": "get",
            "observation_id": "nonexistent-id",
        })

        assert result.success is True  # Operation succeeded
        assert result.output["status"] == "error"
        assert "not found" in result.output["error"].lower()

    @pytest.mark.asyncio
    async def test_acknowledge_observation(self, tool):
        """Test acknowledging an observation."""
        create_result = await tool.execute({
            "operation": "create",
            "observer": "Test",
            "content": "Test",
            "severity": "high",
        })

        obs_id = create_result.output["observation"]["id"]

        result = await tool.execute({
            "operation": "acknowledge",
            "observation_id": obs_id,
        })

        assert result.success is True
        assert result.output["status"] == "acknowledged"
        assert result.output["observation"]["status"] == "acknowledged"
        assert result.output["observation"]["acknowledged_at"] is not None

    @pytest.mark.asyncio
    async def test_resolve_observation(self, tool):
        """Test resolving an observation."""
        create_result = await tool.execute({
            "operation": "create",
            "observer": "Test",
            "content": "Test",
            "severity": "high",
        })

        obs_id = create_result.output["observation"]["id"]

        result = await tool.execute({
            "operation": "resolve",
            "observation_id": obs_id,
            "resolution_note": "Fixed in commit abc123",
        })

        assert result.success is True
        assert result.output["status"] == "resolved"
        assert result.output["observation"]["status"] == "resolved"
        assert result.output["observation"]["resolution_note"] == "Fixed in commit abc123"

    @pytest.mark.asyncio
    async def test_clear_resolved(self, tool):
        """Test clearing resolved observations."""
        # Create observations
        create_result = await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "A", "content": "Issue 1", "severity": "high"},
                {"observer": "A", "content": "Issue 2", "severity": "high"},
                {"observer": "A", "content": "Issue 3", "severity": "high"},
            ],
        })

        # Resolve two of them
        for obs in create_result.output["observations"][:2]:
            await tool.execute({
                "operation": "resolve",
                "observation_id": obs["id"],
            })

        # Clear resolved
        result = await tool.execute({"operation": "clear_resolved"})

        assert result.success is True
        assert result.output["count"] == 2

        # Verify only one remains
        list_result = await tool.execute({"operation": "list"})
        assert list_result.output["total"] == 1

    @pytest.mark.asyncio
    async def test_unknown_operation(self, tool):
        """Test handling unknown operation."""
        result = await tool.execute({"operation": "invalid_op"})

        assert result.success is False
        assert "unknown operation" in result.error["message"].lower()

    @pytest.mark.asyncio
    async def test_list_with_limit(self, tool):
        """Test limiting list results."""
        await tool.execute({
            "operation": "create_batch",
            "observations": [
                {"observer": "A", "content": f"Issue {i}", "severity": "high"}
                for i in range(10)
            ],
        })

        result = await tool.execute({
            "operation": "list",
            "limit": 3,
        })

        assert result.output["count"] == 3
        assert result.output["total"] == 10
