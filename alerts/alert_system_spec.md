# Sonic Alert Component Specification

## Overview

The **Sonic Alert Component** is a real-time, event-driven alerting system integrated into the trading platform. It continuously monitors trading positions and market data, evaluates alert conditions, enriches alerts with context, and dispatches notifications through multiple channels (SMS, Email, Phone Call). It uses dynamic threshold-based logic and supports extensible alert types.

## Objectives

* Define a robust alert processing pipeline
* Support multiple alert types: PriceThreshold, Profit, HeatIndex, TravelPercentLiquid, Portfolio
* Provide real-time evaluation and enrichment
* Enable configurable thresholds and cooldown periods
* Send notifications via multiple channels
* Allow UI integration via Flask APIs

## Architecture Components

### 1. `Alert`

* **Model:** `data/alert.py`
* **Fields:**

  * `alert_type`, `trigger_value`, `evaluated_value`, `condition`, `level`, `frequency`, `counter`, `position_reference_id`, etc.
* **Enums:** `AlertType`, `Condition`, `AlertLevel`, `Status`, `NotificationType`

### 2. `AlertServiceManager`

* **Singleton:** Instantiated once to coordinate services
* **Composition:**

  * `AlertService`
  * `NotificationService`
  * `AlertRepository`
  * `AlertEnrichmentService`

### 3. `AlertService`

* **Function:**

  * Fetch active alerts
  * Enrich alerts (via enrichment service)
  * Evaluate them (using config thresholds)
  * Trigger notifications
  * Update DB with results

### 4. `AlertEvaluationService`

* Evaluates alert against:

  * Config thresholds (`alert_limits.json`)
  * Condition logic (`ABOVE`/`BELOW`)
  * Default fallback if thresholds unavailable

### 5. `AlertEnrichmentService`

* Enriches alerts based on type:

  * `PriceThreshold`: fetches current price
  * `Profit`: reads `pnl_after_fees_usd`
  * `TravelPercentLiquid`: computes distance to liquidation
  * `HeatIndex`: derives custom heat metric
  * `Portfolio`: injects aggregated portfolio metrics from `dashboard_service.get_dashboard_context()`

    * Evaluated fields:

      * `total_value`, `total_collateral`, `total_size`, `avg_leverage`, `avg_travel_percent`, `heat_index`, `value_to_collateral_ratio`

### 6. `AlertRepository`

* Interfaces with `DataLocker`
* Handles fetch, create, update operations on alerts

### 7. `DataLocker`

* SQLite3 storage for alerts, positions, prices, system vars
* Centralized persistence layer
* Tracks mappings between positions and alerts

## API Interface

### Flask Routes (`alerts_bp.py`)

* `POST /alerts/refresh`: triggers reevaluation
* `GET /alerts/monitor`: active alerts status
* `POST /alerts/test_sms`: tests SMS channel
* `GET /alerts/alert_matrix`: matrix UI
* `POST /alerts/create_all`: create sample alerts
* `POST /alerts/delete_all`: wipe all alerts
* `GET /alerts/config`: serve configuration UI
* `POST /alerts/update_config`: save new alert config

## Configuration File

* `alert_limits.json`

  * `alert_ranges`: thresholds per alert type
  * `alert_config`: notification parameters
  * `global_alert_config`: general system settings
  * `total_portfolio_limits`: thresholds for portfolio-level alerts

    * `total_value_limits`: `{low, medium, high}`
    * `total_size_limits`: `{low, medium, high}`
    * `total_leverage_limits`: `{low, medium, high}`
    * `value_to_collateral_ratio_limits`: `{low, medium, high}`
    * `avg_travel_percent_limits`: `{low, medium, high}`
    * `total_heat_limits`: `{low, medium, high}`
  * `notifications`: define how to notify per alert type and level (includes `portfolio` alert section)

## Alert Lifecycle

1. **Created** → `create_alert()`
2. **Enriched** → `AlertEnrichmentService.enrich()`
3. **Evaluated** → `AlertEvaluationService.evaluate()`
4. **Notified** → `NotificationService.send_alert()`
5. **Updated** → `update_alert_level()`

## Normalization Logic

* File: `alert_utils.py`
* Normalizes alert type, condition, and notification type strings into enums

## Extensibility

* To add a new alert type:

  1. Extend `AlertType` enum with `Portfolio`
  2. Add logic to `AlertEnrichmentService` to inject aggregated totals
  3. Add evaluation rules in `AlertEvaluationService`
  4. Configure thresholds in `alert_limits.json` under `total_portfolio_limits` using precise naming like `total_value_limits`

## Error Handling

* All critical components log to `ConsoleLogger`
* Fallback to default behavior on evaluation/enrichment failure

## Testability

* Mock alerts can be created via `create_all_alerts()`
* Alerts can be monitored live via `/monitor` endpoint
* Manual enrichment and evaluation can be triggered through `AlertService`

## UI Integration

* Matrix view renders `alerts` with threshold coloring and metadata
* Config editor loads/saves JSON config
* Portfolio alert evaluations sourced from `dashboard_service.get_dashboard_context()`

## Dependencies

* Python 3.8+
* Flask
* SQLite3
* Pydantic[alert.py](../data/alert.py)
* Custom utils: `console_logger`, `json_manager`, `calc_services`

## Future Enhancements

* Add snooze/silence mechanism
* WebSocket push for live updates
* Notification retry policy
* Richer templates for emails/SMS
* Alert grouping and deduplication
