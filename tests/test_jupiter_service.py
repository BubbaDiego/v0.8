
"""Simple self contained tests for :mod:`wallets.jupiter_service`."""

from unittest import TestCase, main
import os
import sys

# Allow running this file directly by adding project root to ``sys.path``
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Provide a minimal ``requests`` stub when the package isn't installed.
if 'requests' not in sys.modules:
    import types

    requests_stub = types.ModuleType('requests')

    def _dummy_post(*_a, **_k):  # pragma: no cover - sanity safeguard
        raise RuntimeError('requests.post called unexpectedly')

    requests_stub.post = _dummy_post
    sys.modules['requests'] = requests_stub


def load_service(mock_post):
    """Import :class:`JupiterService` with dependencies stubbed."""
    import importlib
    import types

    requests_stub = types.SimpleNamespace(post=mock_post)
    log_stub = types.SimpleNamespace(debug=lambda *a, **k: None, error=lambda *a, **k: None)
    logging_stub = types.SimpleNamespace(log=log_stub)
    constants_stub = types.SimpleNamespace(JUPITER_API_BASE='http://stub')

    sys.modules['requests'] = requests_stub
    sys.modules['core.logging'] = logging_stub
    sys.modules['core.constants'] = constants_stub

    import wallets.jupiter_service as js
    importlib.reload(js)
    return js.JupiterService



class DummyResponse:
    """Minimal stand-in for :class:`requests.Response`."""

=======
import sys
import importlib
from types import SimpleNamespace
import pytest


class DummyResponse:
  def __init__(self, data=None, status=200):
        self._data = data or {}
        self.status_code = status

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("error")


class JupiterServiceTests(TestCase):
    """Unit tests for :class:`JupiterService`."""

    def test_increase_position_success(self):
        calls = {}

        def mock_post(url, json=None, timeout=None):
            calls['url'] = url
            calls['json'] = json
            return DummyResponse({'ok': True})

        JupiterService = load_service(mock_post)
        svc = JupiterService(api_base='http://test')
        result = svc.increase_position('wallet1', 'BTC', 5.0)

        self.assertEqual(result, {'ok': True})
        self.assertEqual(calls['url'], 'http://test/v1/increase_position')
        self.assertEqual(calls['json'], {
            'wallet': 'wallet1',
            'market': 'BTC',
            'collateral_delta': 5.0,
            'size_usd_delta': 0,
        })

    def test_decrease_position_success(self):
        def mock_post(url, json=None, timeout=None):
            return DummyResponse({'ok': True})

        JupiterService = load_service(mock_post)
        svc = JupiterService(api_base='http://test')
        result = svc.decrease_position('w', 'ETH', 1.2)

        self.assertEqual(result, {'ok': True})

    def test_increase_position_error(self):
        def mock_post(url, json=None, timeout=None):
            return DummyResponse(status=500)

        JupiterService = load_service(mock_post)
        svc = JupiterService(api_base='http://test')
        with self.assertRaises(Exception):
            svc.increase_position('w', 'BTC', 1.0)


if __name__ == '__main__':
    main()

def load_service(monkeypatch, mock_post):
    requests_stub = SimpleNamespace(post=mock_post)
    monkeypatch.setitem(sys.modules, 'requests', requests_stub)
    import wallets.jupiter_service as js
    importlib.reload(js)
    return js, js.JupiterService


def test_increase_position_success(monkeypatch):
    calls = {}

    def mock_post(url, json=None, timeout=None):
        calls['url'] = url
        calls['json'] = json
        return DummyResponse({'ok': True})

    js, JupiterService = load_service(monkeypatch, mock_post)
    svc = JupiterService(api_base='http://test')
    result = svc.increase_position('wallet1', 'BTC', 5.0)

    assert result == {'ok': True}
    assert calls['url'] == 'http://test/v1/increase_position'
    assert calls['json'] == {
        'wallet': 'wallet1',
        'market': 'BTC',
        'collateral_delta': 5.0,
        'size_usd_delta': 0,
    }


def test_decrease_position_success(monkeypatch):
    def mock_post(url, json=None, timeout=None):
        return DummyResponse({'ok': True})

    js, JupiterService = load_service(monkeypatch, mock_post)
    svc = JupiterService(api_base='http://test')
    result = svc.decrease_position('w', 'ETH', 1.2)

    assert result == {'ok': True}


def test_increase_position_error(monkeypatch):
    def mock_post(url, json=None, timeout=None):
        return DummyResponse(status=500)

    js, JupiterService = load_service(monkeypatch, mock_post)
    svc = JupiterService(api_base='http://test')
    with pytest.raises(Exception):
        svc.increase_position('w', 'BTC', 1.0)

