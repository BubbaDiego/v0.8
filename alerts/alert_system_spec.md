# Sonic Alert System Specification

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Key Components](#key-components)
3. [Alert Lifecycle](#alert-lifecycle)
4. [Alert Types and Enrichment Logic](#alert-types-and-enrichment-logic)
5. [Evaluation and Alert Levels](#evaluation-and-alert-levels)
6. [Notification Simulation](#notification-simulation)
7. [Testing Infrastructure](#testing-infrastructure)
8. [Directory Structure](#directory-structure)
9. [Important Notes and Future Expansion](#important-notes-and-future-expansion)

---

## 📖 Overview

The Sonic Alert System is a modular, scalable backend service to:

- Create dynamic alerts for various assets/positions
- Enrich alerts based on live market or system data
- Evaluate alerts dynamically against thresholds
- Trigger notifications if alerts meet conditions
- Fully tested at unit, integration, and batch levels

---

## 🛠 Key Components

| Component | Description |
|:---|:---|
| `Alert` (Model) | Core object containing ID, type, asset, trigger_value, evaluated_value, level, etc. |
| `AlertRepository` | Interface between business logic and DataLocker (alerts database) |
| `AlertEnrichmentService` | Populates evaluated_value based on alert type and live data |
| `AlertEvaluationService` | Compares evaluated_value against dynamic thresholds |
| `AlertService` | Orchestrates full alert lifecycle (fetch, enrich, evaluate, update) |
| `Notification Simulation` | Simulates triggering of notifications based on evaluated levels |
| `DataLocker` | In-memory or persistent backend storage for alerts and supporting data |
| `ConfigLoader` | Loads `alert_limits.json` for dynamic LOW, MEDIUM, HIGH thresholds |

---

## 🔄 Alert Lifecycle

1. **Create Alert**
   - Populate fields like `id`, `alert_type`, `trigger_value`, etc.
   - Insert into `DataLocker`.

2. **Enrichment Phase**
   - Populate `evaluated_value` based on live market/position data.
   - Different enrichment strategies per alert type.

3. **Evaluation Phase**
   - Compare `evaluated_value` to thresholds loaded from `alert_limits.json`.
   - Assign `AlertLevel` (`NORMAL`, `LOW`, `MEDIUM`, `HIGH`).

4. **Notification Simulation**
   - Log notification event if alert reaches `MEDIUM` or `HIGH` level.

5. **Persistence Update**
   - Update the enriched and evaluated alert back into `DataLocker`.

---

## 🚀 Alert Types and Enrichment Logic

| Alert Type | Data Source | Enrichment Logic | Evaluated Value Meaning |
|:---|:---|:---|:---|
| `PriceThreshold` | Live price feed | Current price of asset | Price in USD |
| `TravelPercentLiquid` | Position + price feed | Travel % toward liquidation | % traveled from entry |
| `Profit` | Position data | Current realized/unrealized PnL | Profit/Loss in USD |
| `HeatIndex` | Position risk data | Heat Index value | Risk exposure score |

✅ **Each enrichment function** lives in `AlertEnrichmentService` (`_enrich_price_threshold`, `_enrich_profit`, etc.)

---

## 🔍 Evaluation and Alert Levels

| Level | Description |
|:---|:---|
| `NORMAL` | No major deviation, alert is fine |
| `LOW` | Early warning zone |
| `MEDIUM` | Significant risk or movement detected |
| `HIGH` | Critical alert, notification needed |

- **Thresholds dynamically loaded** from `alert_limits.json`.
- **Supports per-alert-type thresholds** (different for Price, Profit, HeatIndex, TravelPercent).

✅ **Handled automatically inside `AlertEvaluationService`.**

---

## 📢 Notification Simulation

After evaluation:

- If `level` is `MEDIUM` or `HIGH`, simulate a notification.
- Currently logged via `ConsoleLogger` (`📢 Notification Triggered for ...`).
- No real external services (SMS/Email) are wired yet — ready for future.

✅ Future-ready for pluggable NotificationService.

---

## 🧪 Testing Infrastructure

| Type | Description |
|:---|:---|
| Unit Tests | Isolated tests for Enrichment and Evaluation functions. |
| System Tests | Full lifecycle tests: Create ➔ Enrich ➔ Evaluate ➔ Notify. |
| Batch Stress Tests | 200+ alerts in pipeline tests to simulate production loads. |
| HTML Reporting | `pytest-html` generates `last_test_report.html` after every run. |
| Test Runner Manager | CLI system to run unit, system, health tests individually or together. |

✅ **System tests auto-generate** an HTML report and auto-open it locally.

---

## 🗂 Directory Structure

