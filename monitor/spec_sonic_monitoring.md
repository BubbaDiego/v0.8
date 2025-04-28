# 📚 Monitor and Ledger System Architecture

## 🗺️ Visual Map

![Monitor Ledger Architecture](sandbox:/mnt/data/monitor_ledger_architecture.png)

---

## 🧩 Components Breakdown

### 1. Monitor Classes

| Class | Purpose | Source |
|:------|:--------|:-------|
| `OperationsMonitor` | Runs POST health checks (pytest), heartbeat writes | `operations_monitor.py` |
| `PositionMonitor` | Fetches positions, calculates total value, logs heartbeat | `positions_monitor.py` |
| `PriceMonitor` | Fetches BTC, ETH, SOL prices from CoinGecko, logs heartbeat | `price_monitor.py` |

Each monitor inherits from `BaseMonitor` which provides cycle handling and ledger writing.


### 2. Ledgers

| Ledger File | Purpose |
|:------------|:--------|
| `monitor/operations_ledger.json` | Heartbeat of OperationsMonitor, POST test results |
| `monitor/position_ledger.json` | Heartbeat of PositionMonitor, number of positions fetched |
| `monitor/price_ledger.json` | Heartbeat of PriceMonitor, number of prices fetched |

- Ledgers are **line-delimited JSON**.
- Each line is a separate event: timestamp, component, operation, metadata.


### 3. Ledger Reader

- **File**: `ledger_reader.py`
- **Function**: `get_ledger_status(file_path)`
- **Purpose**: 
  - Reads the last JSON entry.
  - Computes `age_seconds` (how old the data is).
  - Feeds freshness indicators to the dashboard.


### 4. Cyclone (Controller)

| File | Purpose |
|:-----|:--------|
| `cyclone.py` | Core class: triggers monitor runs, organizes cycles |
| `cyclone_bp.py` | Flask Blueprint API: `/cyclone/run_full_cycle`, `/cyclone/run_market_updates`, etc. |

- Cyclone APIs launch monitors in background threads.
- Results update the ledgers, dashboard reads ledger freshness.


---

## ⚡ How Data Flows

```mermaid
graph TD
  A[User/API Hit Cyclone] --> B[Trigger Specific Monitor]
  B --> C[Fetch Data]
  C --> D[Write Ledger Entry]
  D --> E[Ledger Files (JSON)]
  E --> F[Dashboard reads freshness]
  F --> G[User sees Fresh/Warning/Stale status]
```


## 📋 File Structure Summary

```
monitor/
├── operations_monitor.py
├── positions_monitor.py
├── price_monitor.py
├── operations_ledger.json
├── position_ledger.json
├── price_ledger.json
├── ledger_reader.py
cyclone/
├── cyclone.py
├── cyclone_bp.py
