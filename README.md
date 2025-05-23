# v0.8

## Twilio Testing

To verify your Twilio credentials or trigger a Studio Flow, copy `.env.example` to
`.env` and fill in your details. Then run:

```bash
python scripts/twilio_run.py
```

The script loads credentials from the `.env` file (or environment variables) and
uses `scripts/twilio_test.py` to perform the authentication and optional flow
execution.

## Hedge Calculator
The hedge calculator allows adjusting trade modifiers. Modifiers are saved by sending a POST request to `/sonic_labs/sonic_sauce` with JSON payloads for `hedge_modifiers` and `heat_modifiers`.

## Threshold Seeder
Default alert thresholds can be populated (or refreshed) using the seeder script:

```bash
python -m data.threshold_seeder
```

Run it from the project root on Windows or Linux. Existing thresholds will be
updated to match the defaults defined in the script.
