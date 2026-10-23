/**
 * Network Monitor — Clean Dashboard Controller
 * Professional Enterprise Layout · Zero-Dependency Canvas · Standard Restrained Palette
 */

const API_BASE = "/api/v1";

// State
let isScanning = true;
let isSoundEnabled = true;
let activeGraphTab = "panel-rssi";
let activeBand = "2.4";
let currentFilter = "all";
let currentSearch = "";
let currentSeverityFilter = "";
let networksCache = [];
let suspiciousCache = [];
let isolatedBssid = null;
let throughputHistory = [];
let audioContext = null;

// =============================================================================
// Initialization
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    initCanvasResize();
    fetchDashboardData();

    // Poll updates every 2 seconds
    setInterval(fetchDashboardData, 2000);

    // Initial synthetic throughput history (20 samples)
    for (let i = 0; i < 20; i++) {
        throughputHistory.push({ time: Date.now() - (20 - i) * 1000, pps: Math.floor(Math.random() * 40 + 20) });
    }
});

function initEventListeners() {
    // 1. Top Section Tabs (Wireless vs Zeek)
    document.querySelectorAll(".view-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".view-tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".view-content").forEach(c => c.classList.remove("active"));
            tab.classList.add("active");
            const targetId = tab.getAttribute("data-view");
            const content = document.getElementById(targetId);
            if (content) content.classList.add("active");
            if (targetId === "tab-wireless") renderActiveGraph();
        });
    });

    // 2. Scan Now button
    document.getElementById("btn-scan-now")?.addEventListener("click", async () => {
        const btn = document.getElementById("btn-scan-now");
        if (btn) btn.innerText = "Scanning…";
        try {
            const res = await fetch(`${API_BASE}/wireless/scan`, { method: "POST" });
            const json = await res.json();
            if (json.status === "success") {
                showToast("Network scan updated.");
                await fetchDashboardData();
            }
        } catch (err) {
            showToast(`Scan failed: ${err.message}`);
        } finally {
            if (btn) btn.innerText = "Refresh Scan";
        }
    });

    // 3. Toggle scan pause/resume
    document.getElementById("btn-toggle-scan")?.addEventListener("click", async () => {
        try {
            const res = await fetch(`${API_BASE}/wireless/toggle-scan`, { method: "POST" });
            const json = await res.json();
            isScanning = json.is_scanning;
            document.getElementById("scan-toggle-text").innerText = isScanning ? "Pause Scan" : "Resume Scan";
            document.getElementById("val-scan-status").innerText = isScanning ? "Active (2s)" : "Paused";
            showToast(`Scanner ${isScanning ? 'resumed' : 'paused'}.`);
        } catch (err) {
            showToast(`Toggle failed: ${err.message}`);
        }
    });

    // 4. Threat Simulation dropdown
    const btnThreat = document.getElementById("btn-simulate-threat");
    const menuThreat = document.getElementById("threat-menu");
    if (btnThreat && menuThreat) {
        btnThreat.addEventListener("click", (e) => {
            e.stopPropagation();
            menuThreat.classList.toggle("show");
        });

        document.addEventListener("click", () => menuThreat.classList.remove("show"));

        menuThreat.querySelectorAll(".dropdown-link").forEach(item => {
            item.addEventListener("click", async () => {
                const threatType = item.getAttribute("data-threat");
                menuThreat.classList.remove("show");
                await triggerThreatInjection(threatType);
            });
        });
    }

    // 5. Zeek burst & DNS flood buttons
    document.getElementById("btn-dns-flood")?.addEventListener("click", () => triggerDnsFlood(35));
    document.getElementById("btn-burst-100")?.addEventListener("click", () => triggerBurst(100));
    document.getElementById("btn-burst-1000")?.addEventListener("click", () => triggerBurst(1000));

    // 6. Sound toggle
    document.getElementById("btn-toggle-sound")?.addEventListener("click", () => {
        isSoundEnabled = !isSoundEnabled;
        document.getElementById("sound-icon").innerText = isSoundEnabled ? "🔔" : "🔕";
        showToast(isSoundEnabled ? "Alert sounds enabled." : "Alert sounds muted.");
        if (isSoundEnabled) playCyberBlip(440, 0.05);
    });

    // 7. Graph Sub-tabs
    document.querySelectorAll(".graph-toggle-group .toggle-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".graph-toggle-group .toggle-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".graph-panel").forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            activeGraphTab = btn.getAttribute("data-target");
            const panel = document.getElementById(activeGraphTab);
            if (panel) panel.classList.add("active");
            renderActiveGraph();
        });
    });

    // 8. Spectrum Band selector
    document.getElementById("btn-band-24")?.addEventListener("click", () => {
        activeBand = "2.4";
        document.getElementById("btn-band-24")?.classList.add("active");
        document.getElementById("btn-band-50")?.classList.remove("active");
        renderSpectrumGraph();
    });

    document.getElementById("btn-band-50")?.addEventListener("click", () => {
        activeBand = "5";
        document.getElementById("btn-band-50")?.classList.add("active");
        document.getElementById("btn-band-24")?.classList.remove("active");
        renderSpectrumGraph();
    });

    // 9. Table Search and Filters
    const searchInput = document.getElementById("input-network-search");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            currentSearch = e.target.value.toLowerCase().trim();
            renderNetworksTable();
        });
    }

    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.getAttribute("data-filter");
            renderNetworksTable();
        });
    });

    // 10. Modal Close
    document.getElementById("btn-close-modal")?.addEventListener("click", closeModal);
    document.getElementById("btn-modal-dismiss")?.addEventListener("click", closeModal);
    document.getElementById("forensic-modal")?.addEventListener("click", (e) => {
        if (e.target.id === "forensic-modal") closeModal();
    });

    // 11. Scroll to threats
    document.getElementById("btn-scroll-threats")?.addEventListener("click", () => {
        document.getElementById("section-suspicious")?.scrollIntoView({ behavior: "smooth" });
    });

    // 12. Zeek Severity Filter
    document.getElementById("select-severity-filter")?.addEventListener("change", (e) => {
        currentSeverityFilter = e.target.value;
        fetchAlerts();
    });
}

function initCanvasResize() {
    window.addEventListener("resize", () => {
        renderActiveGraph();
    });
}

// =============================================================================
// Master Data Fetcher
// =============================================================================
async function fetchDashboardData() {
    await Promise.all([
        fetchWirelessSummary(),
        fetchWirelessNetworks(),
        fetchSuspiciousNetworks(),
        fetchRssiTimeline(),
        fetchSpectrumData(),
        fetchPipelineTelemetry(),
        fetchZeekSummary(),
        fetchProtocols(),
        fetchTopSources(),
        fetchAlerts(),
    ]);
}

// =============================================================================
// Telemetry Handlers
// =============================================================================
async function fetchWirelessSummary() {
    try {
        const res = await fetch(`${API_BASE}/wireless/summary`);
        const json = await res.json();
        if (json.status === "success") {
            const data = json.data;
            document.getElementById("val-total-networks").innerText = data.total_networks;
            document.getElementById("val-clean-networks").innerText = data.clean_count;
            document.getElementById("val-total-clients").innerText = data.total_associated_clients;
            document.getElementById("val-suspicious-count").innerText = data.suspicious_count;
            document.getElementById("val-avg-rssi").innerText = `${data.average_rssi_dbm} dBm`;
            document.getElementById("val-active-iface").innerText = data.active_interface;

            const quality = Math.max(0, Math.min(100, Math.round(2 * (data.average_rssi_dbm + 100))));
            document.getElementById("val-signal-quality").innerText = `${quality}% Quality`;

            const dist = Math.pow(10, (-30 - data.average_rssi_dbm) / (10 * 2.7)).toFixed(1);
            document.getElementById("val-avg-distance").innerText = `~${dist}m`;

            // Threat summary tag
            const tagThreat = document.getElementById("tag-threat-status");
            const subThreat = document.getElementById("threat-subtext");
            if (data.suspicious_count > 0) {
                tagThreat.className = "tag tag-red";
                tagThreat.innerText = `${data.suspicious_count} Flagged`;
                subThreat.innerText = `${data.suspicious_count} rogue access point${data.suspicious_count > 1 ? 's' : ''} detected`;
            } else {
                tagThreat.className = "tag tag-green";
                tagThreat.innerText = "Clean";
                subThreat.innerText = "Perimeter clear of rogue APs";
            }

            // Banner visibility
            const banner = document.getElementById("threat-alert-banner");
            const secSuspicious = document.getElementById("section-suspicious");
            if (data.suspicious_count > 0) {
                banner?.classList.remove("hidden");
                secSuspicious?.classList.remove("hidden");
            } else {
                banner?.classList.add("hidden");
                secSuspicious?.classList.add("hidden");
            }
        }
    } catch (err) {
        console.error("Error fetching wireless summary:", err);
    }
}

async function fetchWirelessNetworks() {
    try {
        const res = await fetch(`${API_BASE}/wireless/networks`);
        const json = await res.json();
        if (json.status === "success") {
            networksCache = json.data || [];
            renderNetworksTable();
            renderLegend();
        }
    } catch (err) {
        console.error("Error fetching networks:", err);
    }
}

async function fetchSuspiciousNetworks() {
    try {
        const res = await fetch(`${API_BASE}/wireless/suspicious`);
        const json = await res.json();
        if (json.status === "success") {
            const prevCount = suspiciousCache.length;
            suspiciousCache = json.data || [];
            renderSuspiciousSection();

            if (suspiciousCache.length > prevCount && isSoundEnabled) {
                playThreatAlarm();
            }
        }
    } catch (err) {
        console.error("Error fetching suspicious:", err);
    }
}

// =============================================================================
// DOM Rendering: Suspicious List & Clean Directory Table
// =============================================================================
function renderSuspiciousSection() {
    const container = document.getElementById("suspicious-cards-container");
    const countBadge = document.getElementById("badge-threat-count");
    if (!container) return;

    if (countBadge) countBadge.innerText = `${suspiciousCache.length} Flagged`;

    if (suspiciousCache.length === 0) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = suspiciousCache.map(ap => {
        const primaryThreat = (ap.threat_types && ap.threat_types[0]) ? ap.threat_types[0].replace(/_/g, ' ') : "ROGUE AP";

        return `
            <div class="sus-card-clean">
                <div>
                    <div class="sus-card-top">
                        <span class="sus-ssid-clean">${escapeHtml(ap.ssid)}</span>
                        <span class="tag tag-red">${primaryThreat}</span>
                    </div>

                    <div class="sus-mac-clean">
                        BSSID: ${ap.bssid} · Vendor: ${escapeHtml(ap.vendor)}
                    </div>

                    <div class="sus-reason-clean">
                        ${escapeHtml(ap.threat_description)}
                    </div>

                    <div class="sus-meta-row">
                        <span>Signal: <strong style="color:var(--red);">${ap.rssi} dBm</strong></span>
                        <span>Channel: <strong>Ch ${ap.channel} (${ap.band})</strong></span>
                        <span>Distance: <strong>~${ap.estimated_distance_m}m</strong></span>
                    </div>
                </div>

                <div style="display:flex; gap:0.5rem; margin-top:0.5rem;">
                    <button class="btn btn-secondary btn-sm" onclick="openForensicsModal('${ap.bssid}')">
                        Inspect
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="mitigateNetwork('${ap.bssid}')">
                        Quarantine
                    </button>
                </div>
            </div>
        `;
    }).join("");
}

function renderNetworksTable() {
    const tbody = document.getElementById("wireless-table-body");
    if (!tbody) return;

    let filtered = [...networksCache];

    if (currentFilter === "suspicious") {
        filtered = filtered.filter(ap => ap.is_suspicious && !ap.is_mitigated);
    } else if (currentFilter === "2.4") {
        filtered = filtered.filter(ap => ap.band === "2.4 GHz");
    } else if (currentFilter === "5") {
        filtered = filtered.filter(ap => ap.band === "5 GHz");
    } else if (currentFilter === "open") {
        filtered = filtered.filter(ap => ap.security.toUpperCase() === "OPEN");
    }

    if (currentSearch) {
        filtered = filtered.filter(ap =>
            ap.ssid.toLowerCase().includes(currentSearch) ||
            ap.bssid.toLowerCase().includes(currentSearch) ||
            ap.vendor.toLowerCase().includes(currentSearch)
        );
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="center text-muted">No networks matching filter.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(ap => {
        let statusTag = `<span class="tag tag-green">Clean</span>`;
        if (ap.is_mitigated) {
            statusTag = `<span class="tag tag-gray">Mitigated</span>`;
        } else if (ap.is_suspicious) {
            statusTag = `<span class="tag tag-red">Suspicious</span>`;
        }

        // Clean signal track class
        let sigClass = "good";
        if (ap.rssi < -80) sigClass = "bad";
        else if (ap.rssi < -70) sigClass = "poor";
        else if (ap.rssi < -55) sigClass = "fair";

        const rowDanger = ap.is_suspicious && !ap.is_mitigated ? "row-danger" : "";

        return `
            <tr class="${rowDanger}">
                <td>${statusTag}</td>
                <td><strong style="color:var(--text-primary);">${escapeHtml(ap.ssid)}</strong></td>
                <td><span class="mono">${ap.bssid}</span></td>
                <td>${escapeHtml(ap.vendor)}</td>
                <td>
                    <div class="signal-cell">
                        <div class="signal-track">
                            <div class="signal-fill ${sigClass}" style="width: ${ap.signal_quality}%"></div>
                        </div>
                        <span class="mono" style="font-size:0.72rem; min-width: 60px;">${ap.rssi} dBm</span>
                    </div>
                </td>
                <td>Ch ${ap.channel} (${ap.band})</td>
                <td><span class="tag tag-gray">${escapeHtml(ap.security)}</span></td>
                <td>${ap.clients_count}</td>
                <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="openForensicsModal('${ap.bssid}')">
                        Details
                    </button>
                    ${ap.is_suspicious && !ap.is_mitigated ? `
                        <button class="btn btn-danger btn-sm" onclick="mitigateNetwork('${ap.bssid}')" style="margin-left:0.25rem;">
                            Quarantine
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join("");
}

// =============================================================================
// Canvas Visualizers (Clean, Solid, No Neon Blur)
// =============================================================================
let rssiTimelineData = [];
let spectrumData = null;

async function fetchRssiTimeline() {
    try {
        const res = await fetch(`${API_BASE}/wireless/rssi-timeline`);
        const json = await res.json();
        if (json.status === "success") {
            rssiTimelineData = json.data.timeline_series || [];
            if (activeGraphTab === "panel-rssi") renderRssiGraph();
        }
    } catch (err) {
        console.error("Error fetching timeline:", err);
    }
}

async function fetchSpectrumData() {
    try {
        const res = await fetch(`${API_BASE}/wireless/spectrum`);
        const json = await res.json();
        if (json.status === "success") {
            spectrumData = json.data;
            if (activeGraphTab === "panel-spectrum") renderSpectrumGraph();
        }
    } catch (err) {
        console.error("Error fetching spectrum:", err);
    }
}

function renderActiveGraph() {
    if (activeGraphTab === "panel-rssi") renderRssiGraph();
    else if (activeGraphTab === "panel-spectrum") renderSpectrumGraph();
    else if (activeGraphTab === "panel-throughput") renderThroughputGraph();
}

/**
 * Clean RSSI Timeline (Solid lines, crisp grid, zero blur)
 */
function renderRssiGraph() {
    const canvas = document.getElementById("canvas-rssi-timeline");
    if (!canvas) return;

    const ctx = setupHiDpiCanvas(canvas);
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    ctx.clearRect(0, 0, width, height);

    const padL = 50, padR = 20, padT = 20, padB = 30;
    const chartW = width - padL - padR;
    const chartH = height - padT - padB;

    const minRssi = -95;
    const maxRssi = -30;

    // Gridlines & Y-Axis Labels
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#1f2937";
    ctx.fillStyle = "#6b7280";
    ctx.font = "11px Inter, sans-serif";
    ctx.textAlign = "right";

    const dbmSteps = [-30, -45, -60, -75, -90];
    for (const dbm of dbmSteps) {
        const y = padT + ((maxRssi - dbm) / (maxRssi - minRssi)) * chartH;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(width - padR, y);
        ctx.stroke();
        ctx.fillText(`${dbm}`, padL - 8, y + 4);
    }

    // Time Axis (0s to 30s)
    ctx.textAlign = "center";
    for (let s = 0; s <= 30; s += 5) {
        const x = padL + (s / 30) * chartW;
        ctx.fillText(`${30 - s}s`, x, height - padB + 16);
    }

    if (!rssiTimelineData || rssiTimelineData.length === 0) return;

    // Palette: Clean Slate Blue & Clean Red for rogue
    const standardColors = ["#60a5fa", "#34d399", "#818cf8", "#38bdf8", "#fbbf24"];

    rssiTimelineData.forEach((series, idx) => {
        if (isolatedBssid && series.bssid !== isolatedBssid) return;

        const history = series.history || [];
        if (history.length < 2) return;

        // Solid clear color
        const lineColor = series.is_suspicious ? "#ef4444" : standardColors[idx % standardColors.length];
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = series.is_suspicious ? 2.5 : 1.5;
        ctx.shadowBlur = 0; // ZERO GLOW

        ctx.beginPath();
        const stepX = chartW / Math.max(1, history.length - 1);

        history.forEach((pt, i) => {
            const x = padL + (i * stepX);
            const clampedRssi = Math.max(minRssi, Math.min(maxRssi, pt.rssi));
            const y = padT + ((maxRssi - clampedRssi) / (maxRssi - minRssi)) * chartH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Points
        history.forEach((pt, i) => {
            const x = padL + (i * stepX);
            const clampedRssi = Math.max(minRssi, Math.min(maxRssi, pt.rssi));
            const y = padT + ((maxRssi - clampedRssi) / (maxRssi - minRssi)) * chartH;
            ctx.fillStyle = lineColor;
            ctx.beginPath();
            ctx.arc(x, y, series.is_suspicious ? 3 : 2, 0, Math.PI * 2);
            ctx.fill();
        });
    });
}

function renderLegend() {
    const legend = document.getElementById("rssi-graph-legend");
    if (!legend) return;

    const standardColors = ["#60a5fa", "#34d399", "#818cf8", "#38bdf8", "#fbbf24"];

    legend.innerHTML = networksCache.slice(0, 6).map((ap, idx) => {
        const color = ap.is_suspicious ? "#ef4444" : standardColors[idx % standardColors.length];
        const isDim = isolatedBssid && isolatedBssid !== ap.bssid;
        return `
            <div class="legend-tag ${isDim ? 'dim' : ''}" onclick="toggleIsolateNetwork('${ap.bssid}')">
                <span class="legend-box" style="background:${color};"></span>
                <span>${escapeHtml(ap.ssid)}</span>
            </div>
        `;
    }).join("");
}

function toggleIsolateNetwork(bssid) {
    isolatedBssid = isolatedBssid === bssid ? null : bssid;
    renderRssiGraph();
    renderLegend();
}

/**
 * Clean Wi-Fi Spectrum Analyzer (Parabolic envelopes)
 */
function renderSpectrumGraph() {
    const canvas = document.getElementById("canvas-spectrum");
    if (!canvas || !spectrumData) return;

    const ctx = setupHiDpiCanvas(canvas);
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    ctx.clearRect(0, 0, width, height);

    const padL = 50, padR = 20, padT = 25, padB = 30;
    const chartW = width - padL - padR;
    const chartH = height - padT - padB;

    // Baseline
    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, height - padB);
    ctx.lineTo(width - padR, height - padB);
    ctx.stroke();

    const is24 = activeBand === "2.4";
    const channels = is24 ? [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] : [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 149, 153, 157, 161, 165];

    ctx.fillStyle = "#6b7280";
    ctx.font = "11px Inter, sans-serif";
    ctx.textAlign = "center";

    const chStep = chartW / (channels.length + 1);

    channels.forEach((ch, idx) => {
        const cx = padL + (idx + 1) * chStep;
        ctx.fillText(`${ch}`, cx, height - padB + 16);
    });

    const apsInBand = networksCache.filter(ap => (is24 && ap.channel <= 14) || (!is24 && ap.channel > 14));

    apsInBand.forEach(ap => {
        const chIdx = channels.indexOf(ap.channel);
        if (chIdx === -1) return;

        const centerX = padL + (chIdx + 1) * chStep;
        const curveRadius = chStep * 1.6;
        const normHeight = Math.max(0.15, Math.min(0.9, (ap.rssi + 95) / 65));
        const peakY = (height - padB) - (normHeight * chartH);

        ctx.beginPath();
        ctx.moveTo(centerX - curveRadius, height - padB);
        ctx.quadraticCurveTo(centerX, peakY, centerX + curveRadius, height - padB);

        const isSus = ap.is_suspicious && !ap.is_mitigated;
        const strokeColor = isSus ? "#ef4444" : "#3b82f6";
        const fillColor = isSus ? "rgba(239, 68, 68, 0.15)" : "rgba(59, 130, 246, 0.12)";

        ctx.fillStyle = fillColor;
        ctx.fill();

        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = isSus ? 2 : 1.5;
        ctx.stroke();

        ctx.fillStyle = isSus ? "#ef4444" : "#cbd5e1";
        ctx.font = "10px Inter, sans-serif";
        ctx.fillText(`${ap.ssid} (${ap.rssi}dBm)`, centerX, peakY - 6);
    });
}

/**
 * Clean Throughput Chart
 */
function renderThroughputGraph() {
    const canvas = document.getElementById("canvas-throughput");
    if (!canvas) return;

    const ctx = setupHiDpiCanvas(canvas);
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    ctx.clearRect(0, 0, width, height);

    const padL = 50, padR = 20, padT = 20, padB = 30;
    const chartW = width - padL - padR;
    const chartH = height - padT - padB;

    const now = Date.now();
    const lastPps = throughputHistory.length > 0 ? throughputHistory[throughputHistory.length - 1].pps : 40;
    const nextPps = Math.max(10, Math.min(100, lastPps + Math.floor(Math.random() * 16 - 8)));
    throughputHistory.push({ time: now, pps: nextPps });
    if (throughputHistory.length > 30) throughputHistory.shift();

    const maxPps = Math.max(80, ...throughputHistory.map(d => d.pps));

    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#6b7280";
    ctx.font = "11px Inter, sans-serif";
    ctx.textAlign = "right";

    [0, Math.round(maxPps * 0.5), maxPps].forEach(val => {
        const y = padT + (1 - val / maxPps) * chartH;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(width - padR, y);
        ctx.stroke();
        ctx.fillText(`${val} PPS`, padL - 8, y + 4);
    });

    // Area Fill
    const stepX = chartW / (throughputHistory.length - 1);
    ctx.beginPath();
    throughputHistory.forEach((pt, i) => {
        const x = padL + i * stepX;
        const y = padT + (1 - pt.pps / maxPps) * chartH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.lineTo(padL + (throughputHistory.length - 1) * stepX, height - padB);
    ctx.lineTo(padL, height - padB);
    ctx.closePath();
    ctx.fillStyle = "rgba(59, 130, 246, 0.08)";
    ctx.fill();

    // Line
    ctx.beginPath();
    throughputHistory.forEach((pt, i) => {
        const x = padL + i * stepX;
        const y = padT + (1 - pt.pps / maxPps) * chartH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 1.5;
    ctx.stroke();
}

function setupHiDpiCanvas(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    return ctx;
}

// =============================================================================
// Forensics Inspection Dialog
// =============================================================================
function openForensicsModal(bssid) {
    const ap = networksCache.find(n => n.bssid === bssid) || suspiciousCache.find(n => n.bssid === bssid);
    if (!ap) return;

    document.getElementById("modal-network-ssid").innerText = ap.ssid;
    document.getElementById("modal-network-bssid").innerText = ap.bssid;
    document.getElementById("modal-rssi").innerText = `${ap.rssi} dBm`;
    document.getElementById("modal-signal-pct").innerText = `${ap.signal_quality}% Signal Quality`;
    document.getElementById("modal-distance").innerText = `${ap.estimated_distance_m} m`;
    document.getElementById("modal-channel").innerText = `Ch ${ap.channel} (${ap.band})`;
    document.getElementById("modal-freq").innerText = `${ap.frequency_mhz} MHz`;
    document.getElementById("modal-security").innerText = ap.security;
    document.getElementById("modal-vendor").innerText = ap.vendor;
    document.getElementById("modal-beacon").innerText = `${ap.beacon_interval_ms} ms`;
    document.getElementById("modal-deauth").innerText = `${ap.deauth_rate || 0.0} frames/sec`;
    document.getElementById("modal-clients").innerText = `${ap.clients_count} STAs`;

    const badge = document.getElementById("modal-threat-badge");
    const evidenceBox = document.getElementById("modal-evidence-box");
    const desc = document.getElementById("modal-threat-description");
    const mitText = document.getElementById("modal-mitigation-text");
    const mitBtn = document.getElementById("btn-modal-mitigate");

    if (ap.is_suspicious && !ap.is_mitigated) {
        badge.innerText = "Suspicious AP";
        badge.className = "tag tag-red";
        evidenceBox.className = "diagnostic-box is-threat";
        desc.innerText = ap.threat_description;
        mitText.innerText = ap.recommended_action || "Block BSSID on Wireless Controller.";
        if (mitBtn) {
            mitBtn.style.display = "inline-flex";
            mitBtn.onclick = () => mitigateNetwork(ap.bssid);
        }
    } else {
        badge.innerText = ap.is_mitigated ? "Mitigated" : "Verified AP";
        badge.className = ap.is_mitigated ? "tag tag-gray" : "tag tag-green";
        evidenceBox.className = "diagnostic-box";
        desc.innerText = ap.is_mitigated ? "Access point has been mitigated." : "Access point complies with expected physical and security parameters.";
        mitText.innerText = "No action required.";
        if (mitBtn) mitBtn.style.display = "none";
    }

    document.getElementById("btn-modal-export").onclick = () => exportForensicJson(ap);

    document.getElementById("forensic-modal")?.classList.remove("hidden");
}

function closeModal() {
    document.getElementById("forensic-modal")?.classList.add("hidden");
}

function exportForensicJson(ap) {
    const blob = new Blob([JSON.stringify(ap, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Report_${ap.bssid.replace(/:/g, '')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${ap.bssid} report.`);
}

async function mitigateNetwork(bssid) {
    try {
        const res = await fetch(`${API_BASE}/wireless/mitigate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ bssid: bssid })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`BSSID ${bssid} mitigated.`);
            closeModal();
            await fetchDashboardData();
        } else {
            showToast(`Mitigation failed: ${json.message}`);
        }
    } catch (err) {
        showToast(`Error: ${err.message}`);
    }
}

// =============================================================================
// Threat Injection Handler
// =============================================================================
async function triggerThreatInjection(threatType) {
    if (threatType === "DNS_FLOOD") {
        await triggerDnsFlood(35);
        return;
    }
    showToast(`Simulating scenario: ${threatType}...`);
    try {
        const res = await fetch(`${API_BASE}/wireless/inject-threat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ threat_type: threatType })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`Scenario active: ${threatType}`);
            await fetchDashboardData();
            document.getElementById("section-suspicious")?.scrollIntoView({ behavior: "smooth" });
        } else {
            showToast(`Failed: ${json.message}`);
        }
    } catch (err) {
        showToast(`Error: ${err.message}`);
    }
}

// =============================================================================
// Zeek Telemetry & Backend Handlers
// =============================================================================
async function fetchZeekSummary() {
    try {
        const res = await fetch(`${API_BASE}/statistics/summary`);
        const json = await res.json();
        if (json.status === "success") {
            const data = json.data;
            document.getElementById("val-total-connections").innerText = Number(data.total_connections).toLocaleString();
            document.getElementById("val-total-bytes").innerText = formatBytes(data.total_bytes);

            const dot = document.getElementById("db-dot");
            const dbText = document.getElementById("val-db-status");
            if (data.database_connected) {
                dot.className = "status-dot green";
                dbText.innerText = "MySQL Connected";
            } else {
                dot.className = "status-dot amber";
                dbText.innerText = "In-Memory Mode";
            }
        }
    } catch (err) {
        console.error("Error fetching zeek summary:", err);
    }
}

async function fetchPipelineTelemetry() {
    try {
        const res = await fetch(`${API_BASE}/pipeline/telemetry`);
        const json = await res.json();
        if (json.status === "success") {
            const buf = json.data.buffer;
            document.getElementById("val-buffer-utilization").innerText = `${buf.current_size} / ${buf.capacity}`;
            document.getElementById("val-buffer-hwm").innerText = `${buf.high_water_mark}`;
        }
    } catch (err) {
        console.error("Error fetching pipeline telemetry:", err);
    }
}

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
                container.innerHTML = `<div class="text-muted" style="padding:1rem 0;">No protocol events recorded.</div>`;
                return;
            }

            container.innerHTML = items.map(p => {
                const pct = Math.round((p.count / total) * 100);
                return `
                    <div class="proto-item">
                        <span class="proto-lbl">${p.protocol}</span>
                        <div class="proto-bar-track">
                            <div class="proto-bar-fill" style="width: ${pct}%"></div>
                        </div>
                        <span class="mono" style="font-size:0.72rem; min-width:60px; text-align:right;">${pct}% (${p.count})</span>
                    </div>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Error fetching protocols:", err);
    }
}

async function fetchTopSources() {
    try {
        const res = await fetch(`${API_BASE}/statistics/top-sources`);
        const json = await res.json();
        if (json.status === "success") {
            const tbody = document.getElementById("top-sources-body");
            if (!tbody) return;

            const list = json.data || [];
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="center text-muted">Awaiting traffic…</td></tr>`;
                return;
            }

            tbody.innerHTML = list.map(item => `
                <tr>
                    <td class="mono">${item.source_ip}</td>
                    <td class="mono">${item.connection_count}</td>
                    <td>${item.connection_count > 15 ? '<span class="tag tag-red">Suspicious</span>' : '<span class="tag tag-green">Clean</span>'}</td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.error("Error fetching top sources:", err);
    }
}

async function fetchAlerts() {
    try {
        let url = `${API_BASE}/alerts?limit=15`;
        if (currentSeverityFilter) url += `&severity=${currentSeverityFilter}`;

        const res = await fetch(url);
        const json = await res.json();
        if (json.status === "success") {
            const tbody = document.getElementById("alerts-table-body");
            if (!tbody) return;

            const alerts = json.data || [];
            if (alerts.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="center text-muted">No security alerts matching filter.</td></tr>`;
                return;
            }

            tbody.innerHTML = alerts.map(a => {
                const ts = new Date(a.timestamp * 1000).toLocaleTimeString();
                return `
                    <tr>
                        <td><span class="mono text-muted">${a.alert_id}</span></td>
                        <td class="mono text-muted">${ts}</td>
                        <td class="mono">${a.source_ip}</td>
                        <td class="mono">${a.destination_ip}</td>
                        <td><span class="tag tag-gray">${a.detection_method}</span></td>
                        <td>${escapeHtml(a.description)}</td>
                        <td><span class="badge-sev ${a.severity}">${a.severity}</span></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Error fetching alerts:", err);
    }
}

async function triggerBurst(count) {
    showToast(`Injecting ${count} events into Circular Buffer...`);
    try {
        const res = await fetch(`${API_BASE}/events/inject-burst`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: count })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`Injected ${json.data.enqueued} events in ${json.data.injection_time_seconds}s.`);
            await fetchDashboardData();
        } else {
            showToast(`Failed: ${json.message}`);
        }
    } catch (err) {
        showToast(`Error: ${err.message}`);
    }
}

async function triggerDnsFlood(count = 35) {
    showToast(`Emitting ${count} live DNS queries into conn.log & dns.log...`);
    try {
        const res = await fetch(`${API_BASE}/events/inject-dns-flood`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: count, attacker_ip: "192.168.1.155" })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`Wrote ${json.data.written_to_disk} live DNS queries to disk & buffer! Checking alerts...`);
            if (isSoundEnabled) playCyberAlert();
            await fetchDashboardData();
        } else {
            showToast(`Failed: ${json.message}`);
        }
    } catch (err) {
        showToast(`Error: ${err.message}`);
    }
}

// =============================================================================
// Clean Audio Alerts (Subtle Bleeps, No Sirens)
// =============================================================================
function initAudio() {
    if (!audioContext) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) audioContext = new AudioCtx();
    }
}

function playCyberBlip(freq = 480, duration = 0.05) {
    if (!isSoundEnabled) return;
    try {
        initAudio();
        if (!audioContext) return;
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, audioContext.currentTime);
        gain.gain.setValueAtTime(0.05, audioContext.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioContext.destination);
        osc.start();
        osc.stop(audioContext.currentTime + duration);
    } catch (e) {}
}

function playThreatAlarm() {
    if (!isSoundEnabled) return;
    try {
        initAudio();
        if (!audioContext) return;
        const now = audioContext.currentTime;
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(650, now);
        osc.frequency.setValueAtTime(520, now + 0.1);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        osc.connect(gain);
        gain.connect(audioContext.destination);
        osc.start(now);
        osc.stop(now + 0.25);
    } catch (e) {}
}

// =============================================================================
// Utilities
// =============================================================================
function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2800);
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[m]);
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
