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

from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts

from wallets.wallet_service import WalletService
from wallets.wallet import Wallet
from core.logging import log

LAMPORTS_PER_SOL = 1_000_000_000


class WalletCore:
    """Central access point for wallet + blockchain operations."""

    def __init__(self, rpc_endpoint: str = "https://api.mainnet-beta.solana.com"):
        self.service = WalletService()
        self.rpc_endpoint = rpc_endpoint
        self.client = Client(rpc_endpoint)
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
        self.client = Client(endpoint)
        log.debug(f"RPC endpoint switched to {endpoint}", source="WalletCore")

    # ------------------------------------------------------------------
    # Blockchain interaction helpers
    # ------------------------------------------------------------------
    def fetch_balance(self, wallet: Wallet) -> Optional[float]:
        """Fetch the SOL balance for ``wallet`` using the active client."""
        try:
            resp = self.client.get_balance(PublicKey(wallet.public_address), commitment=Confirmed)
            lamports = resp.get("result", {}).get("value")
            if lamports is not None:
                return lamports / LAMPORTS_PER_SOL
        except Exception as e:
            log.error(f"Failed to fetch balance for {wallet.name}: {e}", source="WalletCore")
        return None

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
            recent = self.client.get_recent_blockhash()["result"]["value"]["blockhash"]
            tx.recent_blockhash = recent
            tx.sign(kp)
            resp = self.client.send_transaction(tx, kp, opts=TxOpts(preflight_commitment=Confirmed))
            sig = resp.get("result")
            if sig:
                log.success(f"Transaction sent: {sig}", source="WalletCore")
            return sig
        except Exception as e:
            log.error(f"Failed to send transaction from {wallet.name}: {e}", source="WalletCore")
            return None
