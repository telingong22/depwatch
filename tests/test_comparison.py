"""Tests for depwatch.comparison."""
import pytest

from depwatch.checker import UpdateInfo
from depwatch.comparison import ComparisonResult, compare_updates


def _make_update(
    package: str = "requests",
    current: str = "2.0.0",
    latest: str = "2.1.0",
    project: str = "myapp",
    language: str = "python",
) -> UpdateInfo:
    return UpdateInfo(
        project=project,
        package=package,
        current_version=current,
        latest_version=latest,
        language=language,
    )


# ---------------------------------------------------------------------------
# ComparisonResult helpers
# ---------------------------------------------------------------------------

def test_comparison_result_is_empty_when_no_lists():
    result = ComparisonResult()
    assert result.is_empty()


def test_comparison_result_not_empty_with_added():
    result = ComparisonResult(added=[_make_update()])
    assert not result.is_empty()


def test_comparison_result_not_empty_with_removed():
    result = ComparisonResult(removed=[_make_update()])
    assert not result.is_empty()


def test_comparison_result_not_empty_with_changed():
    result = ComparisonResult(changed=[_make_update()])
    assert not result.is_empty()


def test_to_dict_keys():
    result = ComparisonResult(added=[_make_update()])
    d = result.to_dict()
    assert set(d.keys()) == {"added", "removed", "changed", "summary"}


def test_to_dict_summary_counts():
    result = ComparisonResult(
        added=[_make_update()],
        removed=[_make_update(package="flask")],
        changed=[_make_update(package="boto3")],
    )
    summary = result.to_dict()["summary"]
    assert summary == {"added": 1, "removed": 1, "changed": 1}


# ---------------------------------------------------------------------------
# compare_updates logic
# ---------------------------------------------------------------------------

def test_compare_all_new_when_previous_empty():
    current = [_make_update("requests"), _make_update("flask")]
    result = compare_updates(previous=[], current=current)
    assert len(result.added) == 2
    assert result.removed == []
    assert result.changed == []


def test_compare_all_removed_when_current_empty():
    previous = [_make_update("requests"), _make_update("flask")]
    result = compare_updates(previous=previous, current=[])
    assert result.added == []
    assert len(result.removed) == 2
    assert result.changed == []


def test_compare_identical_sets_is_empty():
    updates = [_make_update("requests"), _make_update("flask")]
    result = compare_updates(previous=updates, current=updates)
    assert result.is_empty()


def test_compare_detects_changed_latest_version():
    prev = [_make_update("requests", latest="2.1.0")]
    curr = [_make_update("requests", latest="2.2.0")]
    result = compare_updates(previous=prev, current=curr)
    assert len(result.changed) == 1
    assert result.changed[0].latest_version == "2.2.0"
    assert result.added == []
    assert result.removed == []


def test_compare_same_latest_not_in_changed():
    prev = [_make_update("requests", current="2.0.0", latest="2.1.0")]
    curr = [_make_update("requests", current="2.0.5", latest="2.1.0")]
    result = compare_updates(previous=prev, current=curr)
    # current_version changed but latest_version same -> not in changed
    assert result.is_empty()


def test_compare_mixed_scenario():
    prev = [
        _make_update("requests", latest="2.1.0"),
        _make_update("flask", latest="3.0.0"),
    ]
    curr = [
        _make_update("requests", latest="2.2.0"),  # changed
        _make_update("boto3", latest="1.0.0"),      # added
    ]  # flask removed
    result = compare_updates(previous=prev, current=curr)
    assert len(result.added) == 1 and result.added[0].package == "boto3"
    assert len(result.removed) == 1 and result.removed[0].package == "flask"
    assert len(result.changed) == 1 and result.changed[0].package == "requests"
