"""Integration tests: pinning advisor end-to-end with real digest structures."""
from __future__ import annotations

from depwatch.checker import UpdateInfo
from depwatch.digest import ProjectDigest
from depwatch.pinning import build_pin_suggestions, suggestions_to_text


def _u(pkg: str, cur: str, lat: str, lang: str = "python") -> UpdateInfo:
    return UpdateInfo(
        project="integration", package=pkg, language=lang,
        current_version=cur, latest_version=lat,
    )


def _d(name: str, updates: list) -> ProjectDigest:
    return ProjectDigest(project_name=name, updates=updates)


def test_full_pipeline_produces_pins_for_all_updates():
    digests = [
        _d("web", [_u("flask", "2.2.0", "3.0.3"), _u("gunicorn", "20.0.0", "21.2.0")]),
        _d("data", [_u("pandas", "1.5.0", "2.2.1")]),
    ]
    suggestions = build_pin_suggestions(digests)
    assert len(suggestions) == 3
    pins = {s.suggested_pin for s in suggestions}
    assert "flask==3.0.3" in pins
    assert "gunicorn==21.2.0" in pins
    assert "pandas==2.2.1" in pins


def test_go_pins_formatted_correctly():
    digests = [
        _d("svc", [
            _u("github.com/gin-gonic/gin", "1.8.0", "1.9.1", lang="go"),
        ]),
    ]
    suggestions = build_pin_suggestions(digests)
    assert suggestions[0].suggested_pin == "github.com/gin-gonic/gin v1.9.1"


def test_empty_digests_produce_no_suggestions():
    assert build_pin_suggestions([]) == []
    assert build_pin_suggestions([_d("empty", [])]) == []


def test_text_output_contains_all_pins():
    digests = [
        _d("app", [
            _u("requests", "2.28.0", "2.31.0"),
            _u("httpx", "0.23.0", "0.27.0"),
        ]),
    ]
    suggestions = build_pin_suggestions(digests)
    text = suggestions_to_text(suggestions)
    assert "requests==2.31.0" in text
    assert "httpx==0.27.0" in text
    assert "Pin suggestions" in text
