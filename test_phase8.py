#!/usr/bin/env python3
"""
Quick validation test for Phase 8 implementations.

Tests basic functionality of new utilities without requiring full test suite.
"""

import sys
from pathlib import Path

# Add acpctl to path
sys.path.insert(0, str(Path(__file__).parent))


def test_validation():
    """Test validation utilities."""
    print("Testing validation utilities...")
    from acpctl.utils.validation import (
        get_schema_version,
        validate_state_schema,
        sanitize_state_for_checkpoint,
    )

    # Test get_schema_version
    version = get_schema_version()
    assert version == "1.0.0", f"Expected 1.0.0, got {version}"
    print(f"  ✓ Schema version: {version}")

    # Test validate_state_schema with minimal valid state
    from acpctl.core.state import create_test_state

    state = create_test_state(phase="init")
    valid, error = validate_state_schema(state)
    assert valid, f"State validation failed: {error}"
    print(f"  ✓ State validation works")

    # Test sanitize
    sanitized = sanitize_state_for_checkpoint(state)
    assert isinstance(sanitized, dict), "Sanitization should return dict"
    print(f"  ✓ State sanitization works")


def test_errors():
    """Test error message utilities."""
    print("Testing error message utilities...")
    from acpctl.utils.errors import ErrorMessages, ACPError

    # Test error message generation
    msg = ErrorMessages.constitution_not_found()
    assert "constitution.md" in msg, "Error message should mention constitution file"
    print(f"  ✓ Error message generation works")

    # Test custom exception
    try:
        raise ACPError("Test error", "Test fix")
    except ACPError as e:
        assert e.message == "Test error"
        assert e.suggested_fix == "Test fix"
        print(f"  ✓ Custom exceptions work")


def test_performance():
    """Test performance utilities."""
    print("Testing performance utilities...")
    from acpctl.utils.performance import (
        timed_operation,
        PerformanceTracker,
        LazyLoader,
    )
    import time

    # Test timed_operation
    with timed_operation("test_op", log_result=False) as timer:
        time.sleep(0.01)  # Small delay
    elapsed = timer.elapsed()
    assert elapsed >= 0.01, f"Timer should track at least 0.01s, got {elapsed}"
    print(f"  ✓ Timed operation works (elapsed: {elapsed:.3f}s)")

    # Test PerformanceTracker
    tracker = PerformanceTracker()
    tracker.start("test")
    time.sleep(0.01)
    duration = tracker.end("test")
    assert duration >= 0.01, "Tracker should measure at least 0.01s"
    stats = tracker.get_stats("test")
    assert stats["count"] == 1, "Should have 1 tracked operation"
    print(f"  ✓ Performance tracker works")

    # Test LazyLoader
    loaded = False

    def load_func():
        nonlocal loaded
        loaded = True
        return "loaded_value"

    loader = LazyLoader(load_func)
    assert not loaded, "Should not load until get() called"
    value = loader.get()
    assert loaded, "Should be loaded after get()"
    assert value == "loaded_value", "Should return loaded value"
    print(f"  ✓ Lazy loader works")


def test_checkpoint_migration():
    """Test checkpoint migration utilities."""
    print("Testing checkpoint migration...")
    from acpctl.core.checkpoint import migrate_checkpoint

    # Test no-op migration (same version)
    test_checkpoint = {
        "state": {"schema_version": "1.0.0", "phase": "init"},
        "metadata": {"feature_id": "test"},
    }
    result = migrate_checkpoint(test_checkpoint, "1.0.0", "1.0.0")
    assert result == test_checkpoint, "Same-version migration should be no-op"
    print(f"  ✓ Same-version migration works")

    # Test unsupported migration raises error
    try:
        migrate_checkpoint(test_checkpoint, "1.0.0", "999.0.0")
        assert False, "Should raise error for unsupported migration"
    except ValueError as e:
        assert "not supported" in str(e)
        print(f"  ✓ Unsupported migration raises error")


def test_workflow_retry():
    """Test workflow retry logic."""
    print("Testing workflow retry logic...")
    from acpctl.core.workflow import route_governance
    from acpctl.core.state import create_test_state

    # Test passing governance (use init phase to avoid validation issues)
    state = create_test_state(
        phase="init",
        constitution="Test constitution",
        governance_passes=True,
        error_count=2,
    )
    result = route_governance(state)
    assert result == "passed", f"Expected 'passed', got {result}"
    assert state["error_count"] == 0, "Error count should be reset on success"
    print(f"  ✓ Governance pass route works")

    # Test retry logic
    state = create_test_state(phase="init", governance_passes=False, error_count=0)
    result = route_governance(state)
    assert result == "retry", f"Expected 'retry', got {result}"
    assert state["error_count"] == 1, "Error count should increment"
    print(f"  ✓ Governance retry route works")

    # Test max retries
    state = create_test_state(phase="init", governance_passes=False, error_count=3)
    result = route_governance(state)
    assert result == "failed", f"Expected 'failed', got {result}"
    print(f"  ✓ Governance max retry route works")


def test_agent_streaming():
    """Test agent streaming display."""
    print("Testing agent streaming display...")
    from acpctl.agents.base import BaseAgent
    from acpctl.core.state import create_test_state

    class TestAgent(BaseAgent):
        def execute(self, state):
            self.update_streaming_display("Test message")
            return state

    agent = TestAgent("Test Agent", "test")
    state = create_test_state()

    # Test without streaming (verbose=False)
    result = agent.execute_with_streaming(state, verbose=False)
    assert result["phase"] == "init", "Should execute normally"
    print(f"  ✓ Non-streaming execution works")

    # Test with streaming (verbose=True)
    # Just verify it doesn't crash - actual display won't show in test
    result = agent.execute_with_streaming(state, verbose=True)
    assert result["phase"] == "init", "Should execute with streaming"
    print(f"  ✓ Streaming execution works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 8 Implementation Validation")
    print("=" * 60)
    print()

    tests = [
        test_validation,
        test_errors,
        test_performance,
        test_checkpoint_migration,
        test_workflow_retry,
        test_agent_streaming,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            print()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All Phase 8 implementations validated successfully!")


if __name__ == "__main__":
    main()
