"""
📍 Dedicated blueprint registration module.  Bubba was here.
📌 Imports the actual Flask blueprint and exposes it for app use.
"""

from wallets.wallet_controller import wallet_bp

# 👇 THIS is what sonic_app.py will use
__all__ = ["wallet_bp"]
