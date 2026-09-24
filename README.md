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
├── backend/              # Flask REST API routes and services
├── database/             # MySQL schema.sql, seed.sql, connection pool & repositories
├── detection/            # Stateful Rule Engine, KMP, Regex pattern signatures
├── docs/                 # ACADEMIC_MAPPING.md (viva guide across all 6 CSE disciplines)
├── frontend/             # HTML, CSS, JavaScript dashboard presentation interface
├── logs/                 # Sample Zeek logs (conn.log, http.log) & generated test logs
├── processor/            # DSA (Circular Buffer, KMP), Zeek Parser, File Monitor & Workers
├── scripts/              # Pipeline runner & 1000-burst test log generator
├── tests/                # Unit tests, detection accuracy tests, 1000-entry burst test
├── .env.example          # Environment configuration template
├── .gitignore            # Git exclusion rules
├── README.md             # Project overview & documentation
└── requirements.txt      # Python dependencies
```

---

## Quick Start & Verification

### 1. Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run All Automated Tests
```bash
# Run unit tests (Circular buffer, KMP, Zeek parser)
PYTHONPATH=. .venv/bin/python -m unittest tests/unit/test_circular_buffer.py
PYTHONPATH=. .venv/bin/python -m unittest tests/unit/test_kmp.py
PYTHONPATH=. .venv/bin/python -m unittest tests/unit/test_zeek_parser.py

# Run detection accuracy & validation tests (>= 50 real entries)
PYTHONPATH=. .venv/bin/python tests/detection/test_detection_accuracy.py
```

### 3. Run the 1000-Entry Burst Stress Test
```bash
PYTHONPATH=. .venv/bin/python tests/concurrency/test_burst_1000.py
```

**Measured Benchmark Results:**
- **Burst Size:** 1,000 entries
- **Buffer Capacity:** 256 (forces multiple modulo wrap-arounds)
- **Worker Threads:** 4 consumers
- **Lost Entries:** **0 (0.0% loss)**
- **Dropped Entries:** **0**
- **High Water Mark:** 256 / 256 (100% capacity utilized safely)
- **Throughput:** **> 1,700 events/second**

### 4. Run the Pipeline Runner CLI
```bash
PYTHONPATH=. .venv/bin/python scripts/run_pipeline.py --file logs/sample/conn.log
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