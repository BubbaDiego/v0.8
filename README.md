# v0.8
School Project

## Twilio Authentication Test
Run `python scripts/twilio_auth_test.py --sid <ACCOUNT_SID> --token <AUTH_TOKEN>` to validate your Twilio credentials. The script prints detailed error information if authentication fails.

## Twilio Test
Run `python scripts/twilio_test.py` with the same arguments as above. You can optionally provide `--flow-sid`, `--from-phone`, and `--to-phone` to trigger a Studio Flow after authentication.
