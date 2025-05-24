import pytest

from unittest.mock import MagicMock

pytest.importorskip("solana")

from wallets.wallet_core import WalletCore
from wallets.wallet import Wallet


class DummyClient:
    def __init__(self):
        self.balance_calls = []
        self.tx_calls = []

    def get_balance(self, address):
        self.balance_calls.append(address)
        return 2.5

    def send_tx(self, kp, tx):
        self.tx_calls.append((kp, tx))
        return "sig123"


def test_fetch_balance(monkeypatch):
    core = WalletCore()
    dummy = DummyClient()
    monkeypatch.setattr(core, "client", dummy)
    wallet = Wallet(name="w1", public_address="A"*32)
    bal = core.fetch_balance(wallet)
    assert bal == 2.5
    assert dummy.balance_calls == [wallet.public_address]


def test_send_transaction(monkeypatch):
    core = WalletCore()
    dummy = DummyClient()
    monkeypatch.setattr(core, "client", dummy)
    wallet = Wallet(name="w1", public_address="A"*32, private_address="BQ==")
    tx = MagicMock()
    kp = MagicMock()
    monkeypatch.setattr(core, "_keypair_from_wallet", lambda w: kp)
    monkeypatch.setattr(dummy, "send_transaction", dummy.send_tx)
    sig = core.send_transaction(wallet, tx)
    assert sig == "sig123"
    assert dummy.tx_calls == [(kp, tx)]
