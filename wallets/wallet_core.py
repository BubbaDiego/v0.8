"""
WalletCore module
=================

High-level orchestrator for wallet operations.

This class loads wallets through ``WalletService`` and provides helper
methods for interacting with the Solana blockchain via ``solana-py``.
It does not replace existing services or repositories but delegates
persistence to them while offering convenience methods like
``fetch_balance`` and ``send_transaction``.
"""

from __future__ import annotations

from typing import List, Optional

from solana.transaction import Transaction
from solana.keypair import Keypair

from wallets.wallet_service import WalletService
from wallets.wallet import Wallet
from wallets.solana_client import SolanaClient
from core.logging import log


class WalletCore:
    """Central access point for wallet + blockchain operations."""

    def __init__(self, rpc_endpoint: str = "https://api.mainnet-beta.solana.com"):
        self.service = WalletService()
        self.rpc_endpoint = rpc_endpoint
        self.client = SolanaClient(rpc_endpoint)
        log.debug(f"WalletCore initialized with RPC {rpc_endpoint}", source="WalletCore")

    # ------------------------------------------------------------------
    # Data access helpers
    # ------------------------------------------------------------------
    def load_wallets(self) -> List[Wallet]:
        """Return all wallets from the repository as dataclass objects."""
        wallets_out = self.service.list_wallets()
        return [Wallet(**w.dict()) for w in wallets_out]

    def set_rpc_endpoint(self, endpoint: str) -> None:
        """Switch to a different Solana RPC endpoint."""
        self.rpc_endpoint = endpoint
        self.client.set_endpoint(endpoint)
        log.debug(f"RPC endpoint switched to {endpoint}", source="WalletCore")

    # ------------------------------------------------------------------
    # Blockchain interaction helpers
    # ------------------------------------------------------------------
    def fetch_balance(self, wallet: Wallet) -> Optional[float]:
        """Fetch the SOL balance for ``wallet`` using the active client."""
        return self.client.get_balance(wallet.public_address)

    def _keypair_from_wallet(self, wallet: Wallet) -> Keypair:
        if not wallet.private_address:
            raise ValueError("Wallet has no private key")
        try:
            import base58
            secret = base58.b58decode(wallet.private_address)
            return Keypair.from_secret_key(secret)
        except Exception:
            import base64
            secret = base64.b64decode(wallet.private_address)
            return Keypair.from_secret_key(secret)

    def send_transaction(self, wallet: Wallet, tx: Transaction) -> Optional[str]:
        """Sign and submit ``tx`` using ``wallet``'s keypair."""
        try:
            kp = self._keypair_from_wallet(wallet)
            return self.client.send_transaction(kp, tx)
        except Exception as e:
            log.error(f"Failed to send transaction from {wallet.name}: {e}", source="WalletCore")
            return None
