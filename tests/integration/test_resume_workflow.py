"""
Integration tests for resume workflow functionality.

Tests the complete checkpoint → status → resume → history workflow.
Verifies metadata persistence, phase skip logic, and command integration.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from acpctl.core.checkpoint import (
    get_checkpoint_by_feature_id,
    get_latest_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)
from acpctl.core.state import create_test_state


class TestCheckpointMetadata:
    """Test CLI metadata structure and persistence."""

    def test_save_checkpoint_with_enhanced_metadata(self, tmp_path):
        """Test saving checkpoint with all metadata fields."""
        # Create test state
        state = create_test_state(
            phase="specify",
            constitution="Test constitution",
            governance_passes=True,
            feature_description="Add OAuth2 authentication",
            spec="# Test Spec\n\nOAuth2 authentication specification.",
        )

        # Save checkpoint with enhanced metadata
        checkpoint_path = tmp_path / "001-oauth2.json"
        save_checkpoint(
            state=state,
            filepath=str(checkpoint_path),
            feature_id="001-oauth2-authentication",
            thread_id="thread_001",
            status="in_progress",
            phases_completed=["init", "specify"],
            feature_name="oauth2-authentication",
            spec_path="specs/001-oauth2-authentication",
        )

        # Verify file exists
        assert checkpoint_path.exists()

        # Load and verify metadata
        loaded_state, metadata = load_checkpoint(str(checkpoint_path))

        assert metadata.feature_id == "001-oauth2-authentication"
        assert metadata.feature_name == "oauth2-authentication"
        assert metadata.thread_id == "thread_001"
        assert metadata.status == "in_progress"
        assert metadata.phases_completed == ["init", "specify"]
        assert metadata.current_phase == "specify"
        assert metadata.spec_path == "specs/001-oauth2-authentication"
        assert metadata.started_at != ""
        assert metadata.updated_at != ""
        assert metadata.checkpoint_version == "1.0.0"
        assert metadata.acpctl_version == "1.0.0"

    def test_save_checkpoint_preserves_started_at(self, tmp_path):
        """Test that started_at is preserved across checkpoint updates."""
        state = create_test_state(
            phase="specify",
            constitution="Test constitution",
            governance_passes=True,
            feature_description="Test feature",
            spec="# Test Spec",
        )

        checkpoint_path = tmp_path / "001-test.json"

        # First save
        save_checkpoint(
            state=state,
            filepath=str(checkpoint_path),
            feature_id="001-test",
            thread_id="thread_001",
            status="in_progress",
            phases_completed=["init", "specify"],
        )

        _, first_metadata = load_checkpoint(str(checkpoint_path))
        first_started_at = first_metadata.started_at

        # Second save (simulating update to plan phase)
        import time
        time.sleep(0.1)  # Ensure different timestamp

        state["phase"] = "plan"
        state["plan"] = "# Test Plan"
        state["data_model"] = "# Test Data Model"
        save_checkpoint(
            state=state,
            filepath=str(checkpoint_path),
            feature_id="001-test",
            thread_id="thread_001",
            status="in_progress",
            phases_completed=["init", "specify", "plan"],
        )

        _, second_metadata = load_checkpoint(str(checkpoint_path))

        # started_at should be preserved
        assert second_metadata.started_at == first_started_at
        # updated_at should be different
        assert second_metadata.updated_at != first_started_at


class TestListCheckpoints:
    """Test checkpoint listing functionality."""

    def test_list_checkpoints_empty_directory(self, tmp_path):
        """Test listing when no checkpoints exist."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        checkpoints = list_checkpoints(state_dir=str(state_dir))
        assert checkpoints == []

    def test_list_checkpoints_multiple_workflows(self, tmp_path):
        """Test listing multiple workflows sorted by most recent."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create multiple checkpoints with different timestamps
        for i, (feature_id, status) in enumerate([
            ("001-oauth2", "completed"),
            ("002-user-auth", "in_progress"),
            ("003-api-versioning", "in_progress"),
        ]):
            state = create_test_state(
                phase="specify",
                constitution="Test",
                governance_passes=True,
            )

            checkpoint_path = state_dir / f"{feature_id}.json"
            save_checkpoint(
                state=state,
                filepath=str(checkpoint_path),
                feature_id=feature_id,
                thread_id=f"thread_{i:03d}",
                status=status,
                phases_completed=["init", "specify"],
                feature_name=feature_id,
            )

            # Add small delay to ensure different timestamps
            import time
            time.sleep(0.1)

        # List checkpoints
        checkpoints = list_checkpoints(state_dir=str(state_dir))

        assert len(checkpoints) == 3
        # Should be sorted by most recent first
        assert checkpoints[0]["feature_id"] == "003-api-versioning"
        assert checkpoints[1]["feature_id"] == "002-user-auth"
        assert checkpoints[2]["feature_id"] == "001-oauth2"

    def test_list_checkpoints_includes_all_metadata(self, tmp_path):
        """Test that list_checkpoints includes all metadata fields."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        state = create_test_state(
            phase="specify",
            constitution="Test",
            governance_passes=True,
        )

        checkpoint_path = state_dir / "001-test.json"
        save_checkpoint(
            state=state,
            filepath=str(checkpoint_path),
            feature_id="001-test",
            thread_id="thread_001",
            status="in_progress",
            phases_completed=["init", "specify"],
            feature_name="test-feature",
            spec_path="specs/001-test",
        )

        checkpoints = list_checkpoints(state_dir=str(state_dir))

        assert len(checkpoints) == 1
        checkpoint = checkpoints[0]

        # Verify all required fields
        assert "filepath" in checkpoint
        assert "feature_id" in checkpoint
        assert "feature_name" in checkpoint
        assert "thread_id" in checkpoint
        assert "status" in checkpoint
        assert "current_phase" in checkpoint
        assert "phases_completed" in checkpoint
        assert "started_at" in checkpoint
        assert "updated_at" in checkpoint
        assert "spec_path" in checkpoint

        assert checkpoint["feature_id"] == "001-test"
        assert checkpoint["feature_name"] == "test-feature"
        assert checkpoint["status"] == "in_progress"


class TestGetLatestCheckpoint:
    """Test latest checkpoint detection."""

    def test_get_latest_checkpoint_no_checkpoints(self, tmp_path):
        """Test when no checkpoints exist."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        result = get_latest_checkpoint(state_dir=str(state_dir))
        assert result is None

    def test_get_latest_checkpoint_returns_most_recent(self, tmp_path):
        """Test that latest checkpoint is correctly identified."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create multiple checkpoints
        for feature_id in ["001-old", "002-middle", "003-latest"]:
            state = create_test_state(
                phase="specify",
                constitution="Test",
                governance_passes=True,
            )

            checkpoint_path = state_dir / f"{feature_id}.json"
            save_checkpoint(
                state=state,
                filepath=str(checkpoint_path),
                feature_id=feature_id,
                thread_id=f"thread_{feature_id}",
                status="in_progress",
            )

            import time
            time.sleep(0.1)

        latest = get_latest_checkpoint(state_dir=str(state_dir))
        assert latest is not None
        assert "003-latest" in latest


class TestGetCheckpointByFeatureId:
    """Test checkpoint lookup by feature ID."""

    def test_get_checkpoint_by_feature_id_found(self, tmp_path):
        """Test finding checkpoint by feature ID."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        state = create_test_state(
            phase="specify",
            constitution="Test",
            governance_passes=True,
        )

        checkpoint_path = state_dir / "001-oauth2.json"
        save_checkpoint(
            state=state,
            filepath=str(checkpoint_path),
            feature_id="001-oauth2-authentication",
            thread_id="thread_001",
            status="in_progress",
        )

        result = get_checkpoint_by_feature_id(
            "001-oauth2-authentication",
            state_dir=str(state_dir),
        )

        assert result is not None
        assert "001-oauth2" in result

    def test_get_checkpoint_by_feature_id_not_found(self, tmp_path):
        """Test when feature ID doesn't exist."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        result = get_checkpoint_by_feature_id(
            "999-nonexistent",
            state_dir=str(state_dir),
        )

        assert result is None


class TestResumeWorkflowLogic:
    """Test resume command logic without CLI integration."""

    def test_determine_next_phase_after_init(self):
        """Test phase determination after init."""
        from acpctl.cli.commands.resume import determine_next_phase

        next_phase = determine_next_phase(["init"], "init")
        assert next_phase == "specify"

    def test_determine_next_phase_after_specify(self):
        """Test phase determination after specify."""
        from acpctl.cli.commands.resume import determine_next_phase

        next_phase = determine_next_phase(["init", "specify"], "specify")
        assert next_phase == "plan"

    def test_determine_next_phase_after_plan(self):
        """Test phase determination after plan."""
        from acpctl.cli.commands.resume import determine_next_phase

        next_phase = determine_next_phase(["init", "specify", "plan"], "plan")
        assert next_phase == "implement"

    def test_determine_next_phase_complete(self):
        """Test phase determination when complete."""
        from acpctl.cli.commands.resume import determine_next_phase

        next_phase = determine_next_phase(
            ["init", "specify", "plan", "implement"],
            "complete",
        )
        assert next_phase is None


class TestHistoryFormatting:
    """Test history command formatting logic."""

    def test_format_timestamp_valid(self):
        """Test formatting valid ISO timestamp."""
        from acpctl.cli.commands.history import format_timestamp

        timestamp = "2025-11-05T10:30:00"
        result = format_timestamp(timestamp, short=False)
        assert result == "2025-11-05 10:30:00"

    def test_format_timestamp_short(self):
        """Test formatting timestamp in short mode."""
        from acpctl.cli.commands.history import format_timestamp

        timestamp = "2025-11-05T10:30:00"
        result = format_timestamp(timestamp, short=True)
        assert result == "2025-11-05"

    def test_format_timestamp_empty(self):
        """Test formatting empty timestamp."""
        from acpctl.cli.commands.history import format_timestamp

        result = format_timestamp("", short=False)
        assert "—" in result or result == ""

    def test_format_timestamp_invalid(self):
        """Test formatting invalid timestamp."""
        from acpctl.cli.commands.history import format_timestamp

        result = format_timestamp("invalid", short=False)
        assert result == "invalid"  # Should return as-is
