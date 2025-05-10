Cyclone Module Specification
Overview
Cyclone is the core workflow orchestration and alert management engine for an asset monitoring and trading system. It provides centralized logic for market updates, portfolio and position evaluation, alert generation, hedge linkage, and reporting.

Cyclone integrates with various subsystems via the DataLocker interface, acting as the system's heartbeat, and can be triggered via CLI, background jobs, or API endpoints.

Objectives
Monitor asset prices and positions

Evaluate risk and performance metrics

Generate and evaluate alerts at multiple levels (position, portfolio, market)

Manage hedging logic and pairing

Provide interactive console and programmatic API endpoints

Produce visual and programmatic reports

Components
1. Cyclone Engine
Location: cyclone_engine.py
Responsibilities:

Bootstraps key services (AlertCore, PriceMonitor, PositionCore)

Handles main orchestration cycle

Provides routines to:

Update prices

Sync and enrich positions

Link and update hedges

Generate and evaluate alerts

Clear all persisted data

Notable APIs:

python
Copy
Edit
async def run_market_updates()
async def run_composite_position_pipeline()
async def run_cycle(steps=None)
async def run_create_portfolio_alerts()
async def run_create_position_alerts()
async def run_alert_evaluation()
2. CycloneAlertService
Location: cyclone_alert_service.py
Responsibilities:

Creates position, portfolio, and global market alerts

Runs alert enrichment and evaluation cycles

Manages stale alert cleanup

Notable Logic:

Alerts are created using pre-defined thresholds

Enrichment decorates alerts with dynamic evaluation values

Evaluation determines alert level (Normal, Warning, Critical)

Sample Alert Schema:

json
Copy
Edit
{
  "id": "UUID",
  "alert_type": "HeatIndex",
  "alert_class": "Position",
  "asset": "BTC",
  "trigger_value": 50,
  "condition": "ABOVE",
  "level": "Normal",
  ...
}
3. CyclonePositionService
Location: cyclone_position_service.py
Responsibilities:

Interfaces with PositionService and PositionSyncService

Updates, views, enriches, and deletes positions

Links positions for hedge detection

4. CyclonePortfolioService
Location: cyclone_portfolio_service.py
Responsibilities:

Creates predefined alerts based on portfolio-wide metrics

total_value

avg_leverage

value_to_collateral_ratio

Uses DLAlertManager from DataLocker for persistence

5. CycloneHedgeService
Location: cyclone_hedge_service.py
Responsibilities:

Detects hedge groups using HedgeManager

Links and builds hedge groups from raw positions

6. CycloneConsoleApp
Location: cyclone_console_app.py
Features:

Interactive menu using rich for alerts/position operations

Step runner and alert menu

Supports:

Full cycles

Manual enrichment

Alert editing/deletion

Report viewing

7. CycloneReportGenerator
Location: cyclone_report_generator.py
Responsibilities:

Generates HTML reports in dark mode from log and DB data

Summarizes all operations, includes evaluation status

Adds contextual humor (optional) via joke API

8. Cyclone API Module
Location: cyclone_bp.py
Blueprint Endpoints:

/run_market_updates

/run_alert_evaluations

/run_full_cycle

/clear_all_data

/cyclone_logs

All API calls execute core logic in background threads via run_in_background.

Central Data Layer
DataLocker
Location: data_locker.py
Purpose: Unified interface to all data models (alerts, positions, prices, etc.)

Dependencies & Supporting Modules
DLAlertManager, DLPriceManager, DLPositionManager etc. (SQL persistence)

PriceMonitor: Pulls live market data

AlertCore: Engine to evaluate alert triggers

AlertEvaluationService, AlertEnrichmentService: Deep alert logic

Execution Modes
CLI
Run interactively via:

bash
Copy
Edit
python cyclone_console_app.py
Web API
POST to Flask endpoints provided in cyclone_bp.py

Batch/Automated
Run core cycle steps programmatically:

python
Copy
Edit
await Cyclone().run_cycle()
Logging
All modules use the centralized log instance from core.logging. Cyclone uses emoji tags and source metadata for clarity. Logs are persisted and also used by the report generator.

Open Questions ❓
To finalize this specification, I need a bit more input:

🔒 What are the expected security concerns? (e.g., wallet privacy, alert tampering)

🌐 Should Cyclone support remote triggering and result delivery (e.g., via webhook or email)?

📈 Are there planned machine learning integrations for alert prediction or signal enrichment?