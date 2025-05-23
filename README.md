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
The hedge calculator interface is split into two parts:

* `hedge_calculator_config.html/js/css` – position selection and modifier inputs.
* `hedge_calculator_results.html` with `hedge_calculator_results.js` – price slider and output display.

Modifiers are saved by sending a POST request to `/sonic_labs/sonic_sauce` with JSON payloads for `hedge_modifiers` and `heat_modifiers`.
