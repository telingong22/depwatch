"""Tests for depwatch.fetcher module."""

from unittest.mock import MagicMock, patch

import pytest

from depwatch.fetcher import ReleaseInfo, fetch_latest, fetch_latest_go, fetch_latest_python


PYPI_RESPONSE = {
    "info": {
        "version": "2.1.0",
        "project_url": "https://pypi.org/project/requests/",
    }
}

GO_RESPONSE = {
    "Version": "v1.21.0",
    "Time": "2023-08-01T00:00:00Z",
}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_python_success(mock_get):
    mock_get.return_value = _mock_response(PYPI_RESPONSE)
    result = fetch_latest_python("requests")
    assert result is not None
    assert result.name == "requests"
    assert result.version == "2.1.0"
    assert result.language == "python"
    assert "pypi.org" in result.url


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_python_network_error(mock_get):
    import requests as req
    mock_get.side_effect = req.RequestException("timeout")
    result = fetch_latest_python("requests")
    assert result is None


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_python_bad_json(mock_get):
    mock_get.return_value = _mock_response({"unexpected": True})
    result = fetch_latest_python("requests")
    assert result is None


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_go_success(mock_get):
    mock_get.return_value = _mock_response(GO_RESPONSE)
    result = fetch_latest_go("golang.org/x/net")
    assert result is not None
    assert result.name == "golang.org/x/net"
    assert result.version == "v1.21.0"
    assert result.language == "go"
    assert "pkg.go.dev" in result.url


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_go_missing_version(mock_get):
    mock_get.return_value = _mock_response({"Time": "2023-08-01T00:00:00Z"})
    result = fetch_latest_go("golang.org/x/net")
    assert result is None


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_dispatch_python(mock_get):
    mock_get.return_value = _mock_response(PYPI_RESPONSE)
    result = fetch_latest("requests", "python")
    assert isinstance(result, ReleaseInfo)
    assert result.language == "python"


@patch("depwatch.fetcher.requests.get")
def test_fetch_latest_dispatch_go(mock_get):
    mock_get.return_value = _mock_response(GO_RESPONSE)
    result = fetch_latest("golang.org/x/net", "go")
    assert isinstance(result, ReleaseInfo)
    assert result.language == "go"


def test_fetch_latest_unsupported_language():
    with pytest.raises(ValueError, match="Unsupported language"):
        fetch_latest("some-pkg", "ruby")
