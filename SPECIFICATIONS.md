# System Specifications Index

This repository contains multiple subsystems that make up the overall trading and monitoring platform.  Each module has its own specification document with details on structure and responsibilities. This index provides a high level summary and links to the individual specs.

## Modules

### Cyclone
The [Cyclone module](cyclone/cyclone_module_spec.md) drives workflow orchestration and alert management. It processes market updates, evaluates portfolio risk and positions, generates alerts, and coordinates hedging logic.

### Positions
The [Positions module](positions/position_module_spec.md) manages trading positions. It handles enrichment of positions with risk metrics, synchronization with external services, grouping for hedge analysis, and database persistence.

### Alerts
The [Alert module](alert_core/alert_module_spec.md) defines the lifecycle for alerts. It evaluates alert conditions, stores alert data, enriches values, and routes notifications.

### Portfolio
The [Portfolio position module](portfolio/position_module_spec.md) focuses on managing and updating position data within the portfolio. It exposes API endpoints, records snapshots, and triggers alert re-evaluation when positions change.

### Data
The [Sonic Data module](data/sonic_data_module_spec.md) defines the core data models and the DataLocker database layer used across the system. It provides persistence, schema management, and overall data integrity enforcement.

---

Each linked specification contains more detailed design notes, functional requirements, and example workflows.
