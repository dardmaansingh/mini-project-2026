# Wireless Network Traffic Monitor Using Zeek (Mini Project 2026)

A conceptually and academically driven **Multi-Threaded Network Log Analysis and Alerting System** based on Zeek network monitoring, custom Circular Buffer queueing, KMP pattern matching, Regex DFA signatures, MySQL relational persistence, Flask REST API, and webhook alerting.

---

## Architecture Overview

```
Wireless/Network Traffic
        ↓
      Zeek (v9.0.0)
        ↓
   Zeek Log Files (conn.log, http.log)
        ↓
 Python Log Reader / Parser (TSV & JSON)
        ↓
 Custom Circular Buffer (Modulo Pointer Wrap-around)
        ↓
 Producer-Consumer Concurrency (Mutex + Counting Semaphores)
        ↓
 Rule Engine + KMP + Regex Signatures
 (Stateful Engine, Sliding Window, DFA-based patterns)
                      ↓
               Alert Engine (Deduplication)
                      ↓
              MySQL Database (3NF Relational Persistence)
                      ↓
              Flask REST Backend API
                      ↓
          HTML/CSS/JS Presentation Dashboard
                      ↓
             HTTP Webhook Alerting
```

---

## Directory Structure

```
mini-project-2026/
├── alerting/             # AlertManager, Severity definitions, HTTP Webhook dispatcher
├── backend/              # Flask REST API routes (statistics, wireless, alerts, events, pipeline)
├── database/             # MySQL schema.sql, seed.sql, connection pool & repositories
├── detection/            # Stateful Rule Engine, KMP, Regex signatures & Wireless RF Engine
│   └── wireless/         # 802.11 Live RF Monitor, RSSI Tracker, Evil Twin & Rogue Detector
├── docs/                 # ACADEMIC_MAPPING.md (viva guide across all 6 CSE disciplines)
├── frontend/             # Real-time cyber-ops dashboard (Canvas visualizers, Forensics Modal)
├── logs/                 # Sample Zeek logs (conn.log, http.log) & generated test logs
├── processor/            # DSA (Circular Buffer, KMP), Zeek Parser, File Monitor & Workers
├── scripts/              # Pipeline runner & 1000-burst test log generator
├── tests/                # Unit tests, wireless RF tests, accuracy tests, 1000-burst test
├── .env.example          # Environment configuration template
├── .gitignore            # Git exclusion rules
└── README.md             # Project overview & documentation
```

---

## Quick Start & Verification

### 1. Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate
```

### 2. Run All Automated Unit & Integration Tests (41 Tests)
```bash
# Run unit & wireless detection tests
PYTHONPATH=. .venv/bin/python -m unittest tests/unit/test_circular_buffer.py tests/unit/test_kmp.py tests/unit/test_zeek_parser.py tests/unit/test_wireless_detection.py

# Run REST API integration tests (including /api/v1/wireless endpoints)
PYTHONPATH=. .venv/bin/python -m unittest tests/integration/test_flask_api.py tests/integration/test_wireless_api.py

# Run detection accuracy & validation tests (>= 50 real entries)
PYTHONPATH=. .venv/bin/python tests/detection/test_detection_accuracy.py
```

### 3. Run the 1000-Entry Burst Stress Test
```bash
PYTHONPATH=. .venv/bin/python tests/concurrency/test_burst_1000.py
```

### 4. Start the Live Interactive Dashboard Server
```bash
PYTHONPATH=. .venv/bin/python backend/app.py
# Access dashboard at: http://127.0.0.1:5000
```

---

## Academic Alignment (Six CSE Disciplines)

For complete theoretical justifications, complexity proofs, and viva voce defense questions, refer to:
👉 **[docs/ACADEMIC_MAPPING.md](file:///home/dardmaan/mini-project-2026/docs/ACADEMIC_MAPPING.md)**

1. **Data Structures & Algorithms:** Custom Circular Buffer (`processor/dsa/circular_buffer.py`), KMP substring search (`processor/dsa/kmp.py`).
2. **Operating Systems:** Multi-threaded Producer-Consumer architecture with `threading.Lock` and two counting semaphores (`empty_slots`, `filled_slots`), zero race conditions.
3. **Database Management Systems:** 3NF relational schema in MySQL (`database/schema.sql`), indexed foreign keys, parameterized SQL analytical queries (`database/repositories/`).
4. **Discrete Mathematics:** Formal regular language specifications (DFAs/Regex) and formal proofs for Safety ($P \implies Q$) and Liveness ($\Box \Diamond \text{Processed}$) properties.
5. **Computer Networks & Web:** Deep packet inspection with Zeek 9.0, protocol state tracking (`SF`, `S0`, `REJ`), HTTP Webhook dispatch.
6. **Software Engineering:** Department hybrid SDLC (S0 to S7), requirements traceability, and empirical testing validation.