"""Tests for depwatch.notifier module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import UpdateInfo
from depwatch.config import AlertConfig
from depwatch.notifier import DigestPayload, notify, send_email_digest


def _make_alert_config(**kwargs) -> AlertConfig:
    defaults = dict(
        target="ops@example.com",
        interval="24h",
        method="email",
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender="depwatch@example.com",
    )
    defaults.update(kwargs)
    return AlertConfig(**defaults)


def _make_update(name="requests", current="2.28.0", latest="2.31.0") -> UpdateInfo:
    return UpdateInfo(package=name, current_version=current, latest_version=latest)


# --- DigestPayload ---

def test_digest_payload_is_empty():
    payload = DigestPayload(updates=[])
    assert payload.is_empty() is True


def test_digest_payload_not_empty():
    payload = DigestPayload(updates=[_make_update()])
    assert payload.is_empty() is False


def test_digest_format_text_empty():
    payload = DigestPayload(updates=[])
    assert "No dependency updates" in payload.format_text()


def test_digest_format_text_with_updates():
    payload = DigestPayload(updates=[_make_update("flask", "2.0.0", "3.0.0")])
    text = payload.format_text()
    assert "flask" in text
    assert "3.0.0" in text
    assert "Dependency Update Digest" in text


# --- send_email_digest ---

def test_send_email_digest_skips_empty():
    config = _make_alert_config()
    payload = DigestPayload(updates=[])
    result = send_email_digest(payload, config)
    assert result is False


def test_send_email_digest_success():
    config = _make_alert_config()
    payload = DigestPayload(updates=[_make_update()])

    with patch("depwatch.notifier.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        result = send_email_digest(payload, config)

    assert result is True
    mock_server.sendmail.assert_called_once()


def test_send_email_digest_smtp_error():
    import smtplib
    config = _make_alert_config()
    payload = DigestPayload(updates=[_make_update()])

    with patch("depwatch.notifier.smtplib.SMTP", side_effect=smtplib.SMTPException("conn refused")):
        result = send_email_digest(payload, config)

    assert result is False


# --- notify ---

def test_notify_dispatches_email():
    config = _make_alert_config(method="email")
    payload = DigestPayload(updates=[_make_update()])

    with patch("depwatch.notifier.send_email_digest", return_value=True) as mock_send:
        result = notify(payload, config)

    assert result is True
    mock_send.assert_called_once_with(payload, config)


def test_notify_unknown_method_returns_false():
    config = _make_alert_config(method="slack")
    payload = DigestPayload(updates=[_make_update()])
    result = notify(payload, config)
    assert result is False
