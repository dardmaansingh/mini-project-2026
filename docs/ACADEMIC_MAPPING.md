# Academic Course Integration & Technical Concepts Guide
**Mini Project 2026: Wireless Network Traffic Monitor Using Zeek**

This document consolidates how all six foundational computer science disciplines are actively implemented, utilized, and verified in the codebase for viva voce and faculty evaluation.

---

## 1. Data Structures & Algorithms (DSA)

### A. Custom Circular Buffer (`processor/dsa/circular_buffer.py`)
- **What it is:** A fixed-size array (`[None] * capacity`) that treats memory as continuous and circular using modulo arithmetic wrap-around.
- **Where it is used:** Between the Zeek log ingestion producer and the multi-threaded consumer worker pool.
- **Implementation Highlights:**
  - Pointers: `head` (front/read), `tail` (rear/write), `count` (current size).
  - Wrap-around logic: `tail = (tail + 1) % capacity` and `head = (head + 1) % capacity`.
  - Operations: $O(1)$ time complexity for both `enqueue()` and `dequeue()`.
  - Memory bounds: Strictly bounded memory footprints—prevents unbounded queue memory leaks during high traffic spikes.
- **Why we selected it vs. Python `queue.Queue`:** `queue.Queue` hides pointer manipulation and internal allocations. Building it from scratch demonstrates fundamental memory buffer management and pointer arithmetic required for real-time operating systems.

### B. Knuth-Morris-Pratt (KMP) String Matching (`processor/dsa/kmp.py`)
- **What it is:** A linear-time substring search algorithm that avoids redundant comparisons upon character mismatches.
- **Where it is used:** `detection/rules/rule_engine.py` to search for malicious signatures (e.g., `etc/passwd`, `etc/shadow`, `/bin/sh`, `eval(`, `<script>`) within connection history, service strings, and URI paths.
- **Complexity:**
  - Preprocessing: $O(M)$ time to construct the Longest Prefix Suffix (LPS) table.
  - Search: $O(N)$ time over text of length $N$. Total time: $O(N + M)$ vs. Naive $O(N \cdot M)$.
- **Empirical Demonstration:** Verified via unit tests comparing execution and output against naive search.

### C. Decision Tree Classifier (`detection/ml/decision_tree.py` & `detection/ml/train.py`)
- **What it is:** Supervised machine learning classification using greedy recursive binary splitting (CART algorithm).
- **Where it is used:** Tier-3 network anomaly classification on 10 extracted numerical connection features.
- **Why selected:** Full interpretability. Unlike "black box" neural networks, every branch can be inspected as a human-readable If-Then rule (saved in `detection/ml/model/tree_rules.txt`).

---

## 2. Operating Systems (OS) & Concurrency

### Producer-Consumer Architecture (`processor/workers/`)
- **Shared State:** The `CircularBuffer` instance.
- **Synchronization Primitives:**
  1. **Mutual Exclusion Lock (`threading.Lock`):** Protects the critical section during read/write pointer updates (`tail`, `head`, `count`) to eliminate race conditions.
  2. **Empty Slots Semaphore (`threading.Semaphore(capacity)`):** Initialized to buffer capacity. Producer decrements (blocks if buffer is full); consumer increments when freeing a slot.
  3. **Filled Slots Semaphore (`threading.Semaphore(0)`):** Initialized to 0. Producer increments when placing an item; consumer decrements (blocks if buffer is empty).
- **Deadlock Freedom:** Both producer and consumer acquire the counting semaphore *before* acquiring the mutex, guaranteeing no cyclic wait conditions.
- **1000-Entry Burst Stress Test (`tests/concurrency/test_burst_1000.py`):**
  - Proves the system handles a 1000-packet traffic burst across a 256-slot buffer with 4 worker threads.
  - Result: 0 lost entries, 0 dropped items, 100% throughput fidelity (> 1,700 events/sec).

---

## 3. Database Management Systems (DBMS)

### Relational Schema (`database/schema.sql`)
- **Normalized 3NF Architecture:**
  - `network_logs`: Stores connection events with attributes (`uid`, `timestamp`, `source_ip`, `destination_port`, `protocol`, `duration`, `orig_bytes`, etc.).
  - `alerts`: Stores security incidents linked to originating logs via Foreign Key (`log_id`), with JSON evidence columns.
  - `system_metrics`: Stores aggregated time-series telemetry.
- **Indexes:** B-Tree indexes on high-frequency filter columns (`timestamp`, `source_ip`, `severity`, `protocol`).
- **Required Aggregation Queries (`database/repositories/log_repository.py`):**
  ```sql
  SELECT source_ip, COUNT(*) AS connection_count
  FROM network_logs
  GROUP BY source_ip
  ORDER BY connection_count DESC
  LIMIT 10;
  ```

---

## 4. Discrete Mathematics & Formal Languages

### A. Regular Expressions as Type-3 Grammars (`detection/patterns/regex_patterns.py`)
- Regular expressions represent formal regular languages recognized by Deterministic Finite Automata (DFA).
- Pre-compiled patterns recognize:
  - Path traversal (`(\.\./|\.\.\\)`)
  - SQL Injection (`union\s+select|select\s+.*from|information_schema`)
  - Command Injection (`(;\s*(cat|ls|sh|bash|curl|wget)\b)`)
  - Automated security scanners (`sqlmap|nikto|nmap|masscan`)

### B. Formal System Properties
- **Safety Property ($P \implies Q$):** "No false alerts triggered without verifiable evidence." Formally, the alert manager never generates an alert for an event $e$ unless $\exists \text{ rule } r \text{ s.t. } r(e) = \text{True}$.
- **Liveness Property ($\Box \Diamond \text{Processed}$):** "Every valid event placed into the circular buffer will eventually be dequeued and processed by an active consumer thread." Guaranteed by non-zero worker count and starvation-free semaphore queuing.

---

## 5. Web & Computer Networks

- **Zeek Network Monitoring:** Deep packet inspection extracting session state, protocol analysis (TCP, UDP, ICMP), service discovery (HTTP, DNS, SSL), and connection state machines (`SF`, `S0`, `REJ`, `RSTO`).
- **HTTP Webhook Alerting (`alerting/webhook.py`):** Asynchronous push notifications via standard HTTP POST with JSON event payloads to external notification endpoints.

---

## 6. Software Engineering & SDLC

- **Hybrid SDLC Traceability:**
  - S0 Discovery $\rightarrow$ Problem Formulation & Scope
  - S1 Requirements $\rightarrow$ FRs/NFRs & Testability
  - S2 Architecture $\rightarrow$ 9 Modular Engines
  - S3 Data Design $\rightarrow$ 3NF Relational Schema & REST Contracts
  - S4 Implementation $\rightarrow$ Dependency-ordered builds
  - S5 Verification $\rightarrow$ Unit, Concurrency, and Empirical Accuracy Benchmarks
  - S6 RCA $\rightarrow$ Diagnosing URL encoding edge case during HTTP regex test and adding `unquote_plus` decoding.
