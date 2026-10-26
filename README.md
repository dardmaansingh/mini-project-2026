# NetSentinel — Real-Time College Network Security Monitoring and Alert Generation System

> **A Full-Stack Cybersecurity Operations Center (SOC) for Academic Campus Networks**  
> Built with **FastAPI (Python 3.14)**, **SQLAlchemy Async**, **WebSocket Streaming**, **React 18**, **Vite**, **TypeScript**, and **Tailwind CSS**.

---

## 🏛️ Project Overview

**NetSentinel** is an enterprise-grade, real-time network security monitoring and automated incident detection platform engineered for college and university campuses. Academic environments present unique security challenges: high-density student BYOD devices, high-bandwidth research labs, IoT door controllers, campus-wide roaming across dozens of Wireless Access Points, and open guest Wi-Fi.

NetSentinel addresses these challenges through a **hybrid telemetry architecture**:
- **Demonstration & Development Mode**: A high-fidelity **Synthetic Event Generator** models realistic campus diurnal rhythms (class rush hours, dorm peak downloads, library roaming) and allows security analysts to trigger live attack scenarios (e.g., Port Scans, DNS Exfiltration, SSH Brute Force, Rogue DHCP).
- **Production Integration Mode**: Seamlessly ingests industry-standard network telemetry (Zeek `conn.log`/`dns.log`, Syslog UDP:514, RADIUS 802.1X accounting, NetFlow v9/IPFIX) without altering application core logic or detection pipelines.

---

## 🏗️ System Architecture

```
                                  CAMPUS TELEMETRY SOURCES
    ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
    │  Synthetic Event Engine   │  Syslog / RFC 5424 Feeds  │  Zeek Sensor (conn/dns)   │
    │  (Diurnal Campus Sim)     │  (Campus DNS & Firewalls) │  (Mirror / TAP Sensor)    │
    └─────────────┬─────────────┴─────────────┬─────────────┴─────────────┬─────────────┘
                  │                           │                           │
                  └───────────────────────────┼───────────────────────────┘
                                              ▼
                                 FASTAPI INGESTION PIPELINE
                     ┌─────────────────────────────────────────────────┐
                     │ • Normalization Engine (Unified Schema)         │
                     │ • Asynchronous Event Validation (Pydantic v2)   │
                     │ • Ring-Buffer WebSocket Broadcast Manager       │
                     └────────────────────────┬────────────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
          SLIDING WINDOW DETECTION ENGINE                ASYNC DATABASE PERSISTENCE
     ┌──────────────────────────────────────┐        ┌──────────────────────────────────┐
     │ • 10 Correlation Rules (MITRE ATT&CK)│        │ • SQLite / PostgreSQL Async      │
     │ • State-bucketed Sliding Windows     │        │ • Event Store & Audit Trails     │
     │ • Deduplication & Cooldown Tracker   │        │ • Asset Inventory & AP Topology  │
     └──────────────────┬───────────────────┘        └──────────────────────────────────┘
                        │
                        ▼
               SOC ALERT MANAGER & WS PUSH
                        │
                        ▼  (WebSocket ws://.../ws/events & REST /api/...)
        ┌───────────────────────────────────────────────────────────────┐
        │                 REACT 18 + VITE SOC DASHBOARD                 │
        │ • Page A: Executive SOC Overview & Time-Series Volume Charts  │
        │ • Page B: Real-Time Event Explorer & Field Search             │
        │ • Page C: Access Point Topology & Wireless Monitoring         │
        │ • Page D: Security Incident Alerts & Analyst Triage Workflow  │
        │ • Page E: Campus Asset Inventory & Rogue Device Flags         │
        │ • Page F: Detection Rule Configurator & Test Simulator        │
        │ • Page G: Ingestion Adapters & Attack Scenario Console        │
        │ • Page H: SecOps Audit Logs & Academic Governance             │
        └───────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 10 Detection Rules Engine

NetSentinel implements 10 stateful correlation rules addressing the most prevalent academic cyber threats:

| Rule ID | Rule Name | Category | Severity | Window | Threshold | Detection Mechanism |
|---|---|---|---|---|---|---|
| `RULE-001` | **DNS Query Rate Anomaly** | DNS | Medium | 60s | 50 queries | Sliding window query counter; detects C2 tunneling or DNS exfiltration bursts. |
| `RULE-002` | **Port Scan Detected** | Network | High | 60s | 20 ports | Multi-value destination port tracker; detects reconnaissance probes across subnets. |
| `RULE-003` | **Authentication Brute Force** | Auth | Medium | 60s | 5 failures | Multi-user & single-user failed login aggregator across campus services. |
| `RULE-004` | **Bandwidth Surge / Exfiltration** | Flow | Medium | 60s | 100 MB | Statistical outlier detection on outbound byte volume over rolling intervals. |
| `RULE-005` | **Suspicious Outbound Communication** | Threat Intel | High | 60s | Instant | Matches connections against blacklisted destination IPs and known malicious TLDs. |
| `RULE-006` | **Unauthorized Device on Network** | Asset | Medium | 3600s | Instant | Cross-references new MAC/IP discoveries against the approved Campus Asset Inventory. |
| `RULE-007` | **DHCP Anomaly / Rogue Server** | DHCP | High | 60s | Instant | Flags unauthorized DHCP `OFFER` messages attempting Man-in-the-Middle (MitM). |
| `RULE-008` | **Possible Lateral Movement** | Network | High | 300s | 10 hosts | Identifies workstation-to-workstation SMB/RDP scans indicative of worm propagation. |
| `RULE-009` | **Infrastructure Link Flapping** | Infra | Low | 300s | Instant | Detects erratic Access Point reboots, disconnects, or switch port error storms. |
| `RULE-010` | **Monitoring / Log Source Gap** | Monitoring | Info | 300s | 300s silent | Emits a warning if a critical logging source abruptly stops transmitting heartbeats. |

---

## 💻 Tech Stack & Standards

- **Backend**: Python 3.14, FastAPI 0.115, Uvicorn, SQLAlchemy 2.0 (AsyncIO), aiosqlite / asyncpg, Pydantic Settings, WebSockets.
- **Frontend**: React 18, Vite 5, TypeScript 5, Tailwind CSS 3, Recharts 2, Lucide React, Date-fns.
- **Testing**: Pytest, Pytest-Asyncio, HTTPX (18 automated tests passing).
- **Design System**: Kibana / Elastic Security inspired SOC Dark Theme (`#030712` navy palette, glassmorphism cards, micro-animations, accessible severity badges).

---

## 🚀 Quick Start Guide

You can run and manage the entire NetSentinel platform with **just 1 or 2 commands**:

### ⚡ Option A: Single-Command Run (Recommended)

Run everything (FastAPI Backend + Vite Frontend) concurrently in a single terminal:

```bash
# Start both services with unified live colored logs (Press Ctrl+C to stop both cleanly)
./start.sh
# (or: ./scripts/start_all.sh)
```

Or run in the background (daemon mode):
```bash
./start.sh --background

# Stop anytime:
./stop.sh
# (or: ./scripts/stop_all.sh)
```

*(Standard npm and make shortcuts are also supported: `npm start`, `npm run stop`, `make dev`, `make stop`)*

---

### 🛠️ The 3 Core Workflow Commands

| Goal | Root Shortcut | Script Path | Description |
|---|---|---|---|
| **1. Setup / Update** | `./setup.sh` | `./scripts/setup_all.sh` | Creates `.venv`, installs Python & Node packages, checks DB schema. |
| **2. Run Everything** | `./start.sh` | `./scripts/start_all.sh` | Starts Backend (`:8000`) and Frontend (`:5173`) with unified live logs. |
| **3. Stop Services** | `./stop.sh` | `./scripts/stop_all.sh` | Gracefully shuts down both processes and frees ports 8000 & 5173. |
| **4. Run Tests** *(Bonus)* | `./test.sh` | `.venv/bin/pytest tests/` | Executes all 18 automated unit and integration tests. |

---


---

## 🧪 Running Automated Tests

All test suites execute against the asynchronous engine and REST APIs:

```bash
source .venv/bin/activate

# Run all 18 automated unit and integration tests
pytest tests/ -v
```

Test coverage includes:
- `test_detection_engine.py`: DNS query rates, TCP port scanning, auth brute forcing, and rogue DHCP detection.
- `test_synthetic_generator.py`: Normal traffic cadence, scenario injection, and pause/resume mechanics.
- `test_api_endpoints.py`: REST routes for health, metrics, paginated events, alerts triage, assets, and audit logs.

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & service metadata |
| `GET` | `/api/metrics/overview` | Executive metrics: 24h volume, alert severity distribution |
| `GET` | `/api/events` | Filterable, paginated normalized network event stream |
| `GET` | `/api/alerts` | Active and historical security incident alerts |
| `PATCH`| `/api/alerts/{id}/status` | Triage alert status (*acknowledged*, *investigating*, *resolved*) |
| `POST` | `/api/alerts/{id}/notes` | Attach analyst forensic notes to an alert |
| `GET` | `/api/access-points` | Access Point inventory with live event and alert counts |
| `GET` | `/api/assets` | Registered campus devices (switches, servers, workstations) |
| `POST` | `/api/assets` | Register a new asset in the inventory |
| `GET` | `/api/rules` | All 10 detection rules and current configurations |
| `PATCH`| `/api/rules/{id}` | Update rule thresholds, windows, cooldowns, or toggle enabled |
| `POST` | `/api/synthetic/trigger/port-scan` | Inject synthetic port scan burst |
| `POST` | `/api/synthetic/trigger/dns-spike` | Inject synthetic DNS exfiltration spike |
| `POST` | `/api/synthetic/trigger/brute-force` | Inject synthetic SSH/Web brute force attack |
| `WS`   | `/ws/events` | Real-time WebSocket event and alert broadcast |

---

## 🎓 Academic Viva Voce Defense Guide

For academic defense across Computer Science disciplines:

1. **Computer Networks**: Normalization of heterogeneous layer 2–7 protocols (Zeek connection states `SF`/`S0`/`REJ`, 802.11 AP BSSID association, DNS RR types `A`/`AAAA`/`TXT`).
2. **Operating Systems**: Non-blocking asynchronous I/O event loops (`asyncio`, `uvloop`), memory-bounded ring buffers, and concurrency primitives preventing thread starvation.
3. **Data Structures & Algorithms**: O(1) sliding window eviction via `collections.deque` timestamp bucket queues; multi-value set tracking for port-scan cardinality.
4. **Database Systems**: 3NF relational schemas, async connection pooling, B-tree indexed timestamps for high-throughput temporal queries.
5. **Software Engineering & Governance**: Compliance with academic privacy standards (no student payload capture, FERPA/GDPR compliance disclaimer, tamper-evident SOC audit logging).