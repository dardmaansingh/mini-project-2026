/**
 * Zeek Network Traffic Monitor - Live Dashboard Controller
 * Handles real-time polling, REST API communication, charts, and burst injection.
 */

const API_BASE = "/api/v1";
let currentSeverityFilter = "";

document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    fetchDashboardData();
    // Poll updates every 2 seconds
    setInterval(fetchDashboardData, 2000);
});

function initEventListeners() {
    // Burst injection buttons
    document.getElementById("btn-burst-100")?.addEventListener("click", () => triggerBurst(100));
    document.getElementById("btn-burst-1000")?.addEventListener("click", () => triggerBurst(1000));

    // Severity filter dropdown
    const filterSelect = document.getElementById("select-severity-filter");
    if (filterSelect) {
        filterSelect.addEventListener("change", (e) => {
            currentSeverityFilter = e.target.value;
            fetchAlerts();
        });
    }
}

async function fetchDashboardData() {
    await Promise.all([
        fetchSummary(),
        fetchProtocols(),
        fetchTopSources(),
        fetchPipelineTelemetry(),
        fetchAlerts()
    ]);
}

/**
 * 1. Fetch Top-Level Summary Telemetry
 */
async function fetchSummary() {
    try {
        const res = await fetch(`${API_BASE}/statistics/summary`);
        const json = await res.json();
        if (json.status === "success") {
            const data = json.data;
            document.getElementById("val-total-connections").innerText = Number(data.total_connections).toLocaleString();
            document.getElementById("val-total-bytes").innerText = formatBytes(data.total_bytes);
            document.getElementById("val-avg-duration").innerText = `${data.avg_duration.toFixed(3)}s`;
            document.getElementById("val-total-alerts").innerText = data.total_alerts;

            // Severity chips
            const sevs = data.severity_counts || {};
            document.getElementById("chip-crit").innerText = `${sevs.CRITICAL || 0} CRIT`;
            document.getElementById("chip-high").innerText = `${sevs.HIGH || 0} HIGH`;
            document.getElementById("chip-med").innerText = `${sevs.MEDIUM || 0} MED`;

            // Database status badge
            const dbBadge = document.getElementById("db-status-badge");
            if (dbBadge) {
                if (data.database_connected) {
                    dbBadge.className = "status-pill status-online";
                    dbBadge.innerHTML = `<span class="pulse-dot"></span> MySQL: Online`;
                } else {
                    dbBadge.className = "status-pill status-warning";
                    dbBadge.innerHTML = `<span class="dot" style="background:#f59e0b"></span> DB: In-Memory (MySQL Pending)`;
                }
            }
        }
    } catch (err) {
        console.error("Error fetching summary:", err);
    }
}

/**
 * 2. Fetch Protocol Breakdown (L4)
 */
async function fetchProtocols() {
    try {
        const res = await fetch(`${API_BASE}/statistics/protocols`);
        const json = await res.json();
        if (json.status === "success") {
            const container = document.getElementById("protocol-bars");
            if (!container) return;

            const items = json.data || [];
            const total = items.reduce((acc, curr) => acc + curr.count, 0) || 1;

            if (items.length === 0) {
                container.innerHTML = `<div class="text-muted text-center py-2">No protocol data recorded yet.</div>`;
                return;
            }

            container.innerHTML = items.map(p => {
                const pct = Math.round((p.count / total) * 100);
                const protoLower = p.protocol.toLowerCase();
                return `
                    <div class="proto-row">
                        <span class="proto-name">${p.protocol}</span>
                        <div class="proto-track">
                            <div class="proto-fill ${protoLower}" style="width: ${pct}%"></div>
                        </div>
                        <span class="proto-val">${pct}% (${p.count})</span>
                    </div>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Error fetching protocols:", err);
    }
}

/**
 * 3. Fetch Top Source IPs (GROUP BY source_ip)
 */
async function fetchTopSources() {
    try {
        const res = await fetch(`${API_BASE}/statistics/top-sources`);
        const json = await res.json();
        if (json.status === "success") {
            const tbody = document.getElementById("top-sources-body");
            if (!tbody) return;

            const list = json.data || [];
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted">Awaiting traffic events...</td></tr>`;
                return;
            }

            tbody.innerHTML = list.map(item => {
                const count = item.connection_count;
                const isSuspicious = count > 15;
                const statusBadge = isSuspicious
                    ? `<span class="sev-badge sev-HIGH">SUSPICIOUS PROBE</span>`
                    : `<span class="sev-badge sev-LOW">BENIGN HOST</span>`;

                return `
                    <tr>
                        <td class="font-mono">${item.source_ip}</td>
                        <td class="font-mono">${count}</td>
                        <td>${statusBadge}</td>
                    </tr>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Error fetching top sources:", err);
    }
}

/**
 * 4. Fetch Circular Buffer & Concurrency Telemetry
 */
async function fetchPipelineTelemetry() {
    try {
        const res = await fetch(`${API_BASE}/pipeline/telemetry`);
        const json = await res.json();
        if (json.status === "success") {
            const buf = json.data.buffer;
            const size = buf.current_size;
            const cap = buf.capacity;
            const pct = buf.utilization_percent;

            document.getElementById("val-buffer-utilization").innerText = `${size} / ${cap} (${pct}%)`;
            document.getElementById("val-buffer-hwm").innerText = `${buf.high_water_mark} / ${cap}`;
            document.getElementById("val-buffer-dropped").innerText = buf.dropped_count;

            const progressBar = document.getElementById("buffer-progress-bar");
            if (progressBar) {
                progressBar.style.width = `${pct}%`;
            }
        }
    } catch (err) {
        console.error("Error fetching telemetry:", err);
    }
}

/**
 * 5. Fetch Security Alerts Table
 */
async function fetchAlerts() {
    try {
        let url = `${API_BASE}/alerts?limit=25`;
        if (currentSeverityFilter) {
            url += `&severity=${currentSeverityFilter}`;
        }

        const res = await fetch(url);
        const json = await res.json();
        if (json.status === "success") {
            const tbody = document.getElementById("alerts-table-body");
            if (!tbody) return;

            const alerts = json.data || [];
            if (alerts.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No security alerts matching filter.</td></tr>`;
                return;
            }

            tbody.innerHTML = alerts.map(a => {
                const ts = new Date(a.timestamp * 1000).toLocaleTimeString();
                return `
                    <tr>
                        <td class="font-mono highlight">${a.alert_id}</td>
                        <td class="font-mono text-muted">${ts}</td>
                        <td class="font-mono">${a.source_ip}</td>
                        <td class="font-mono">${a.destination_ip}</td>
                        <td><span class="badge font-mono">${a.detection_method}</span></td>
                        <td>${a.description}</td>
                        <td><span class="sev-badge sev-${a.severity}">${a.severity}</span></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Error fetching alerts:", err);
    }
}

/**
 * Inject On-Demand Traffic Burst
 */
async function triggerBurst(count) {
    showToast(`Injecting burst of ${count} events into Circular Buffer...`);
    try {
        const res = await fetch(`${API_BASE}/events/inject-burst`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: count })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`✔ Burst complete: ${json.data.enqueued} events enqueued in ${json.data.injection_time_seconds}s!`);
            fetchDashboardData();
        } else {
            showToast(`✖ Failed: ${json.message}`);
        }
    } catch (err) {
        showToast(`✖ Error triggering burst: ${err.message}`);
    }
}

function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
