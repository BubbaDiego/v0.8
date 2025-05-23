# v0.8

For an overview of the key modules and architecture, see
[SPECIFICATIONS.md](SPECIFICATIONS.md). This now includes the
[Monitor Core specification](monitor/monitor_module_spec.md).

## Twilio Testing

To verify your Twilio credentials or trigger a Studio Flow, copy `.env.example` to
`.env` and fill in your details. Then run:

```bash
python scripts/twilio_run.py
```

The script loads credentials from the `.env` file (or environment variables) and
uses `scripts/twilio_test.py` to perform the authentication and optional flow
execution.

## Required Environment Variables

The application expects several environment variables for email and Twilio
integration. Create a `.env` file or export them in your shell before running
the app:

```
SMTP_SERVER=your.smtp.server
SMTP_PORT=587
SMTP_USERNAME=you@example.com
SMTP_PASSWORD=your_password
SMTP_DEFAULT_RECIPIENT=you@example.com

TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_PHONE=+1987654321
TWILIO_TO_PHONE=+1234567890
# Optional
TWILIO_FLOW_SID=your_flow_sid_here
```

## Hedge Calculator

## Threshold Seeder
Default alert thresholds can be populated (or refreshed) using the seeder script:

```bash
python -m data.threshold_seeder
```

Run it from the project root on Windows or Linux. Existing thresholds will be
updated to match the defaults defined in the script.

