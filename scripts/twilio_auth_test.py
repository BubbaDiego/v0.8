#!/usr/bin/env python3
"""Simple Twilio authentication test script.

Usage:
    python scripts/twilio_auth_test.py --sid <ACCOUNT_SID> --token <AUTH_TOKEN>

If --sid or --token are omitted, the script will try to use the
TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables.
"""

import argparse
import os
import sys

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import requests


def trigger_flow(client: Client, flow_sid: str, from_phone: str, to_phone: str) -> int:
    """Triggers a Twilio Studio Flow and prints details on failure."""
    try:
        execution = client.studio.v2.flows(flow_sid).executions.create(
            to=to_phone,
            from_=from_phone,
        )
        print("✅ Flow triggered successfully")
        print(f"Execution SID: {execution.sid}")
        return 0
    except TwilioRestException as exc:
        print("❌ Flow trigger failed")
        print(f"HTTP Status: {exc.status}")
        print(f"Error Code: {exc.code}")
        print(f"Message: {exc.msg}")
        if exc.more_info:
            print(f"More Info: {exc.more_info}")
        return 1
    except requests.exceptions.RequestException as exc:
        print("❌ Network error while contacting Twilio")
        print(str(exc))
        return 1
    except Exception as exc:
        print("❌ Unexpected error while triggering flow")
        print(str(exc))
        return 1


def test_twilio_auth(account_sid: str, auth_token: str) -> int:
    """Attempts to authenticate with Twilio and prints detailed results."""
    try:
        client = Client(account_sid, auth_token)
        account = client.api.accounts(account_sid).fetch()
        print("✅ Authentication succeeded")
        print(f"Account SID: {account.sid}")
        print(f"Friendly Name: {account.friendly_name}")
        return 0
    except TwilioRestException as exc:
        print("❌ Authentication failed")
        print(f"HTTP Status: {exc.status}")
        print(f"Error Code: {exc.code}")
        print(f"Message: {exc.msg}")
        if exc.more_info:
            print(f"More Info: {exc.more_info}")
        return 1
    except requests.exceptions.RequestException as exc:
        print("❌ Network error while contacting Twilio")
        print(str(exc))
        return 1
    except Exception as exc:
        print("❌ Unexpected error")
        print(str(exc))
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test Twilio credentials and optionally trigger a Studio Flow"
    )
    parser.add_argument("--sid", help="Twilio Account SID")
    parser.add_argument("--token", help="Twilio Auth Token")
    parser.add_argument("--flow", help="Twilio Flow SID to trigger")
    parser.add_argument("--from-phone", help="Phone number to send from")
    parser.add_argument("--to-phone", help="Phone number to send to")
    args = parser.parse_args()

    sid = args.sid or os.getenv("TWILIO_ACCOUNT_SID")
    token = args.token or os.getenv("TWILIO_AUTH_TOKEN")
    flow_sid = args.flow or os.getenv("TWILIO_FLOW_SID")
    from_phone = args.from_phone or os.getenv("TWILIO_FROM_PHONE")
    to_phone = args.to_phone or os.getenv("TWILIO_TO_PHONE")

    if not sid or not token:
        print("Account SID and Auth Token are required")
        return 1

    client = Client(sid, token)

    status = test_twilio_auth(sid, token)
    if status != 0:
        return status

    if flow_sid and from_phone and to_phone:
        return trigger_flow(client, flow_sid, from_phone, to_phone)

    return 0


if __name__ == "__main__":
    sys.exit(main())
