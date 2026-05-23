"""Integration tests: filter interacting with real UpdateInfo objects."""
from __future__ import annotations

from depwatch.checker import UpdateInfo
from depwatch.filter import FilterConfig, apply_filter


def _u(pkg: str, cur: str, lat: str) -> UpdateInfo:
    return UpdateInfo(package=pkg, current_version=cur, latest_version=lat)


def test_default_config_passes_all_updates():
    updates = [
        _u("requests", "2.27.0", "2.27.1"),
        _u("django", "4.1.0", "4.2.0"),
        _u("flask", "2.0.0", "3.0.0"),
    ]
    result = apply_filter(updates, FilterConfig())
    assert result == updates


def test_combined_ignore_and_min_bump():
    """Ignore 'internal-*' and require at least a minor bump."""
    updates = [
        _u("internal-auth", "1.0.0", "2.0.0"),   # ignored by pattern
        _u("requests", "2.27.0", "2.27.1"),        # patch → below minor threshold
        _u("django", "4.1.0", "4.2.0"),            # minor → passes
        _u("flask", "2.0.0", "3.0.0"),             # major → passes
    ]
    cfg = FilterConfig(ignore_packages=["internal-*"], min_bump="minor")
    result = apply_filter(updates, cfg)
    names = [u.package for u in result]
    assert "internal-auth" not in names
    assert "requests" not in names
    assert "django" in names
    assert "flask" in names


def test_all_suppressed_returns_empty():
    updates = [
        _u("boto3", "1.0.0", "1.0.1"),
        _u("botocore", "1.0.0", "1.0.1"),
    ]
    cfg = FilterConfig(ignore_packages=["boto*"])
    assert apply_filter(updates, cfg) == []


def test_major_only_filters_minor_and_patch():
    updates = [
        _u("a", "1.0.0", "1.0.1"),  # patch
        _u("b", "1.0.0", "1.1.0"),  # minor
        _u("c", "1.0.0", "2.0.0"),  # major
    ]
    cfg = FilterConfig(min_bump="major")
    result = apply_filter(updates, cfg)
    assert len(result) == 1
    assert result[0].package == "c"
