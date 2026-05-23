"""Unit tests for depwatch.webhook."""

from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import UpdateInfo
from depwatch.notifier import DigestPayload
from depwatch.webhook import WebhookConfig, _build_body, send_webhook


def _make_update(project: str = "myapp", pkg: str = "requests") -> UpdateInfo:
    return UpdateInfo(project=project, package=pkg, current_version="1.0.0", latest_version="2.0.0")


def _make_payload(*updates: UpdateInfo) -> DigestPayload:
    return DigestPayload(updates=list(updates))


# --- WebhookConfig validation ---

def test_webhook_config_valid():
    cfg = WebhookConfig(url="https://example.com/hook")
    assert cfg.timeout == 10


def test_webhook_config_invalid_url():
    with pytest.raises(ValueError, match="http"):
        WebhookConfig(url="ftp://bad.url")


def test_webhook_config_invalid_timeout():
    with pytest.raises(ValueError, match="timeout"):
        WebhookConfig(url="https://example.com", timeout=0)


# --- _build_body ---

def test_build_body_structure():
    payload = _make_payload(_make_update())
    raw = _build_body(payload)
    data = json.loads(raw)
    assert "projects" in data
    assert data["projects"][0]["package"] == "requests"
    assert data["projects"][0]["latest_version"] == "2.0.0"


def test_build_body_empty_payload():
    payload = _make_payload()
    raw = _build_body(payload)
    data = json.loads(raw)
    assert data["projects"] == []


# --- send_webhook ---

def _mock_urlopen(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_webhook_success():
    cfg = WebhookConfig(url="https://example.com/hook")
    payload = _make_payload(_make_update())
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(200)):
        result = send_webhook(cfg, payload)
    assert result is True


def test_send_webhook_empty_payload_skips():
    cfg = WebhookConfig(url="https://example.com/hook")
    payload = _make_payload()
    with patch("urllib.request.urlopen") as mock_open:
        result = send_webhook(cfg, payload)
    mock_open.assert_not_called()
    assert result is True


def test_send_webhook_http_error():
    cfg = WebhookConfig(url="https://example.com/hook")
    payload = _make_payload(_make_update())
    err = urllib.error.HTTPError(url="", code=500, msg="Server Error", hdrs=None, fp=None)  # type: ignore
    with patch("urllib.request.urlopen", side_effect=err):
        result = send_webhook(cfg, payload)
    assert result is False


def test_send_webhook_network_error():
    cfg = WebhookConfig(url="https://example.com/hook")
    payload = _make_payload(_make_update())
    err = urllib.error.URLError(reason="connection refused")
    with patch("urllib.request.urlopen", side_effect=err):
        result = send_webhook(cfg, payload)
    assert result is False


def test_send_webhook_includes_secret_header():
    cfg = WebhookConfig(url="https://example.com/hook", secret="topsecret")
    payload = _make_payload(_make_update())
    captured: dict = {}

    def fake_urlopen(req, timeout):
        captured["headers"] = dict(req.headers)
        return _mock_urlopen(200)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        send_webhook(cfg, payload)

    assert captured["headers"].get("X-depwatch-secret") == "topsecret"
