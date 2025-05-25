import sys

import os
import importlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

# Ensure repository root is on sys.path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



class DummyResponse:
    def __init__(self, data=None, status=200):
        self._data = data or {}
        self.status_code = status

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("error")

def load_service(mock_post):
    """Import JupiterService with stubbed dependencies."""
    dummy_log = SimpleNamespace(debug=lambda *a, **k: None,
                               error=lambda *a, **k: None)
    class DummyRichLogger:
        def __getattr__(self, _):
            return lambda *a, **k: None
    rich_logger_stub = SimpleNamespace(RichLogger=DummyRichLogger, ModuleFilter=object)
    modules = {
        'requests': SimpleNamespace(post=mock_post),
        'core.logging': SimpleNamespace(log=dummy_log, configure_console_log=lambda: None),
        'utils.rich_logger': rich_logger_stub,
    }
    with patch.dict(sys.modules, modules):
        import wallets.jupiter_service as js
        importlib.reload(js)
    return js.JupiterService


class JupiterServiceTests(unittest.TestCase):
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

    def test_decrease_position_error(self):
        def mock_post(url, json=None, timeout=None):
            return DummyResponse(status=404)

        JupiterService = load_service(mock_post)
        svc = JupiterService(api_base='http://test')
        with self.assertRaises(Exception):
            svc.decrease_position('w', 'SOL', 2.0)


if __name__ == "__main__":
    unittest.main()



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


