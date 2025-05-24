from __future__ import annotations

from typing import Optional
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.rpc.types import TxOpts

from core.logging import log

LAMPORTS_PER_SOL = 1_000_000_000


class SolanaClient:
    """Lightweight wrapper around ``solana-py`` for common wallet actions."""

    def __init__(self, rpc_endpoint: str = "https://api.mainnet-beta.solana.com"):
        self.endpoint = rpc_endpoint
        self.client = Client(rpc_endpoint)
        log.debug(f"SolanaClient using {rpc_endpoint}", source="SolanaClient")

    def set_endpoint(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.client = Client(endpoint)
        log.debug(f"Endpoint switched to {endpoint}", source="SolanaClient")

    def get_balance(self, address: str) -> Optional[float]:
        try:
            resp = self.client.get_balance(PublicKey(address), commitment=Confirmed)
            lamports = resp.get("result", {}).get("value")
            return lamports / LAMPORTS_PER_SOL if lamports is not None else None
        except Exception as e:
            log.error(f"Balance fetch failed for {address}: {e}", source="SolanaClient")
            return None

    def send_transaction(self, keypair: Keypair, tx: Transaction) -> Optional[str]:
        try:
            recent = self.client.get_recent_blockhash()["result"]["value"]["blockhash"]
            tx.recent_blockhash = recent
            tx.sign(keypair)
            resp = self.client.send_transaction(tx, keypair, opts=TxOpts(preflight_commitment=Confirmed))
            sig = resp.get("result")
            if sig:
                log.success(f"Transaction sent: {sig}", source="SolanaClient")
            return sig
        except Exception as e:
            log.error(f"Transaction failed: {e}", source="SolanaClient")
            return None
