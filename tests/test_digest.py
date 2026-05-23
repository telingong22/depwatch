"""Tests for depwatch.digest."""

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest, build_all_digests, build_digest
from depwatch.state import get_last_seen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(name="myproject"):
    from depwatch.config import ProjectConfig
    return ProjectConfig(name=name, language="python", path="requirements.txt")


def _make_update(package="requests", current="2.27.0", latest="2.28.0"):
    return UpdateInfo(package=package, current_version=current, latest_version=latest)


# ---------------------------------------------------------------------------
# ProjectDigest
# ---------------------------------------------------------------------------

def test_project_digest_is_empty():
    d = ProjectDigest(project_name="p")
    assert d.is_empty


def test_project_digest_not_empty():
    d = ProjectDigest(project_name="p", updates=[_make_update()])
    assert not d.is_empty


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_build_digest_all_new():
    project = _make_project()
    updates = [_make_update("requests"), _make_update("flask", "2.0", "3.0")]
    state = {}
    digest = build_digest(project, updates, state)
    assert len(digest.updates) == 2
    assert get_last_seen(state, "myproject", "requests") == "2.28.0"
    assert get_last_seen(state, "myproject", "flask") == "3.0"


def test_build_digest_skips_already_seen():
    project = _make_project()
    updates = [_make_update("requests", "2.27.0", "2.28.0")]
    state = {"myproject/requests": "2.28.0"}
    digest = build_digest(project, updates, state)
    assert digest.is_empty


def test_build_digest_partial_new():
    project = _make_project()
    updates = [
        _make_update("requests", "2.27.0", "2.28.0"),
        _make_update("flask", "2.0", "3.0"),
    ]
    state = {"myproject/requests": "2.28.0"}
    digest = build_digest(project, updates, state)
    assert len(digest.updates) == 1
    assert digest.updates[0].package == "flask"


def test_build_digest_updates_state():
    project = _make_project()
    updates = [_make_update("requests", "2.27.0", "2.28.0")]
    state = {}
    build_digest(project, updates, state)
    assert get_last_seen(state, "myproject", "requests") == "2.28.0"


def test_build_digest_empty_updates():
    project = _make_project()
    digest = build_digest(project, [], {})
    assert digest.is_empty


# ---------------------------------------------------------------------------
# build_all_digests
# ---------------------------------------------------------------------------

def test_build_all_digests_multiple_projects():
    proj_a = _make_project("proj_a")
    proj_b = _make_project("proj_b")
    updates_map = {
        proj_a: [_make_update("requests")],
        proj_b: [_make_update("gin", "1.8", "1.9")],
    }
    state = {}
    digests = build_all_digests(updates_map, state)
    assert len(digests) == 2
    names = {d.project_name for d in digests}
    assert names == {"proj_a", "proj_b"}


def test_build_all_digests_deduplicates_across_runs():
    proj = _make_project()
    updates = [_make_update()]
    state = {}
    first = build_all_digests({proj: updates}, state)
    second = build_all_digests({proj: updates}, state)
    assert not first[0].is_empty
    assert second[0].is_empty
