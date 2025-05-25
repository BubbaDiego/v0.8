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
JUPITER_API_BASE=https://perps-api.jup.ag
```

`JUPITER_API_BASE` lets you override the default Jupiter endpoint if it changes.

## Twilio Monitor

The `twilio_monitor` runs as part of the background monitor suite. It uses
`CheckTwilioHeartbeartService` in dry‑run mode to verify that credentials are
valid without placing an actual call.

## Hedge Calculator

## Threshold Seeder
Default alert thresholds can still be populated using the dedicated module:

```bash
python -m data.threshold_seeder
```

However, the main database initializer now exposes the same functionality via

the `--seed-thresholds` flag, allowing all seeding tasks to be consolidated into
a single command.

## Exporting Alert Thresholds

Use the **Export** button on the Alert Thresholds page (or the
`/system/alert_thresholds/export` API endpoint) to download a JSON snapshot of
the threshold limits currently stored in the database. These exported values are
the limits the system uses when evaluating alerts—they do **not** represent the
current alerts themselves.

## Running `sonic_app.py`

The Flask dashboard can be started directly from the project root. Ensure that
all required environment variables above are set (either in a `.env` file or in
your shell) and then run:

```bash
python sonic_app.py
```

By default the server listens on `0.0.0.0:5000`. Open
`http://127.0.0.1:5000/` in your browser to access the dashboard. Use the
`--monitor` flag if you want to also launch the local monitor process in a
separate console.


## Initializing the Database

To create the SQLite database and all required tables, run:

```bash
python scripts/init_db.py
```

The script creates `mother_brain.db` in the `data` directory (or the path set via
the `DB_PATH` environment variable) and ensures every table exists.  Additional
flags allow optional seeding and resets:

```bash
# wipe the DB and seed thresholds and wallets
python scripts/init_db.py --reset --seed-thresholds --seed-wallets

# run every available seeder
python scripts/init_db.py --all
```

**Existing Installations**

If you have an older database created before version 0.8.5, add the new `status` column manually:

```sql
ALTER TABLE positions ADD COLUMN status TEXT DEFAULT 'ACTIVE';
```

## Startup Service

`utils.startup_service` provides a unified `StartUpService` helper. Running
`StartUpService.run_all()` ensures the `mother_brain.db` database exists, checks
for required configuration files and creates the `logs/` and `data/` directories
if needed. Progress is shown via a simple dot spinner between steps. Environment
variables are automatically loaded from a `.env` file in the project root (with
`.env.example` as a fallback) before any checks run. When all checks pass a
short startup sound (`static/sounds/web_station_startup.mp3`) will play. On
failure the "death spiral" tone is used instead. Invoke this at application
launch to verify the environment is ready. The Launch Pad console exposes this
check via a **Startup Service** option in its main menu.

## Database Recovery

If the SQLite file becomes corrupted, you can rebuild it directly from the
Launch Pad utility:

```bash
python launch_pad.py
```

Open the **Operations** menu and choose **Recover Database**. This deletes the
damaged `mother_brain.db` and recreates it with the required tables.

## Windows Branch Name Compatibility
If a remote branch name contains characters that are invalid on Windows (such as `>` or `:`), Git cannot create the local reference. Rename the branch on a Unix-like system or ask the author to rename it. For example:

```bash
git checkout codex/fix-->=-not-supported--error-in-apply_color
git branch -m codex/fix-not-supported-error-in-apply_color
git push origin :codex/fix-->=-not-supported--error-in-apply_color codex/fix-not-supported-error-in-apply_color
```

After renaming, Windows users can fetch the branch normally.
