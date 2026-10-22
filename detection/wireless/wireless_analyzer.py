"""
Wireless Network Security & Real-Time RF Analysis Subsystem.

Academic & Practical Context (Wireless Networks & Information Security):
- Real-time 802.11 / Wi-Fi physical & link layer monitoring.
- RSSI signal strength tracking, path-loss distance estimation, and channel spectrum mapping.
- Rogue AP, Evil Twin, Deauthentication storm, and weak cipher threat detection.
- System interface telemetry & realistic dynamic RF environment synthesis.
"""

import os
import re
import time
import math
import random
import threading
from typing import Dict, List, Any, Optional, Tuple


# Known Wireless Equipment OUI Vendor Prefixes (IEEE OUI Registry subset)
OUI_VENDOR_TABLE = {
    "00:14:22": "Cisco Systems",
    "00:40:96": "Cisco Systems",
    "00:1B:D4": "Cisco Systems",
    "F8:C0:01": "Cisco Systems",
    "74:83:C2": "Aruba Networks (HPE)",
    "00:0B:86": "Aruba Networks (HPE)",
    "24:DE:C6": "Aruba Networks (HPE)",
    "A4:C3:F0": "Ubiquiti Networks",
    "80:2A:A8": "Ubiquiti Networks",
    "AC:84:C6": "TP-Link Technologies",
    "50:C7:BF": "TP-Link Technologies",
    "E8:48:B8": "TP-Link Technologies",
    "00:09:5B": "Netgear Inc.",
    "20:E5:2A": "Netgear Inc.",
    "3C:52:82": "Apple Inc.",
    "20:DF:B9": "Apple Inc.",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "24:6F:28": "Espressif Systems (ESP8266/32)",
    "A4:E5:7C": "Espressif Systems (ESP8266/32)",
    "00:13:37": "Hak5 / Wi-Fi Pineapple (Hostile Hardware)",
    "DE:AD:BE": "Locally Administered (Spoofed Attacker)",
}


def resolve_oui_vendor(bssid: str) -> str:
    """Resolves MAC address prefix to manufacturer vendor string."""
    cleaned = bssid.upper().replace("-", ":")
    prefix = ":".join(cleaned.split(":")[:3]) if len(cleaned.split(":")) >= 3 else ""
    if prefix in OUI_VENDOR_TABLE:
        return OUI_VENDOR_TABLE[prefix]

    # Check if Locally Administered Address (bit 1 of 1st byte is set)
    try:
        first_byte = int(cleaned.split(":")[0], 16)
        if first_byte & 0x02:
            return "Randomized / Spoofed MAC"
    except (ValueError, IndexError):
        pass

    return "Generic Wireless / Unknown"


def calculate_signal_quality(rssi: int) -> int:
    """Calculates standardized signal quality percentage (0-100%)."""
    # RSSI <= -100 dBm is 0%, RSSI >= -50 dBm is 100%
    quality = 2 * (rssi + 100)
    return max(0, min(100, int(quality)))


def calculate_estimated_distance(rssi: int, tx_power: int = -30, path_loss_exp: float = 2.7) -> float:
    """
    Estimates physical distance in meters using Log-Distance Path Loss Model:
    RSSI = TxPower - 10 * n * log10(d) => d = 10^((TxPower - RSSI) / (10 * n))
    """
    try:
        exponent = (tx_power - rssi) / (10.0 * path_loss_exp)
        distance = math.pow(10.0, exponent)
        return round(max(0.1, min(150.0, distance)), 1)
    except Exception:
        return 10.0


def channel_to_frequency(channel: int) -> int:
    """Converts 802.11 Wi-Fi channel to center frequency in MHz."""
    if 1 <= channel <= 14:
        # 2.4 GHz band
        if channel == 14:
            return 2484
        return 2407 + (channel * 5)
    elif 36 <= channel <= 165:
        # 5 GHz band
        return 5000 + (channel * 5)
    return 2412


class WirelessAccessPoint:
    """
    Strongly-typed representation of an observed 802.11 Wireless Access Point or Station.
    """

    def __init__(
        self,
        bssid: str,
        ssid: str,
        rssi: int,
        channel: int,
        security: str = "WPA2-PSK",
        vendor: Optional[str] = None,
        clients_count: int = 0,
        beacon_interval_ms: float = 102.4,
        is_suspicious: bool = False,
        threat_score: int = 0,
        threat_types: Optional[List[str]] = None,
        threat_description: str = "",
        recommended_action: str = "",
    ):
        self.bssid = bssid.upper()
        self.ssid = ssid or "<Hidden SSID>"
        self.rssi = rssi
        self.channel = channel
        self.frequency_mhz = channel_to_frequency(channel)
        self.band = "2.4 GHz" if channel <= 14 else "5 GHz"
        self.security = security
        self.vendor = vendor or resolve_oui_vendor(self.bssid)
        self.clients_count = clients_count
        self.beacon_interval_ms = beacon_interval_ms
        self.deauth_rate = 0.0  # deauth frames/second

        self.is_suspicious = is_suspicious
        self.threat_score = threat_score
        self.threat_types: List[str] = threat_types or []
        self.threat_description = threat_description
        self.recommended_action = recommended_action
        self.is_mitigated = False

        self.first_seen = time.time()
        self.last_seen = time.time()
        self.rssi_history: List[Dict[str, Any]] = [
            {"time": round(self.last_seen, 1), "rssi": self.rssi}
        ]

    @property
    def signal_quality(self) -> int:
        return calculate_signal_quality(self.rssi)

    @property
    def estimated_distance_m(self) -> float:
        return calculate_estimated_distance(self.rssi)

    def record_rssi(self, new_rssi: int, ts: Optional[float] = None):
        """Records a new RSSI sample and maintains rolling 30-sample history."""
        self.rssi = new_rssi
        self.last_seen = ts or time.time()
        self.rssi_history.append({"time": round(self.last_seen, 1), "rssi": new_rssi})
        if len(self.rssi_history) > 30:
            self.rssi_history.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bssid": self.bssid,
            "ssid": self.ssid,
            "rssi": self.rssi,
            "signal_quality": self.signal_quality,
            "estimated_distance_m": self.estimated_distance_m,
            "channel": self.channel,
            "frequency_mhz": self.frequency_mhz,
            "band": self.band,
            "security": self.security,
            "vendor": self.vendor,
            "clients_count": self.clients_count,
            "beacon_interval_ms": self.beacon_interval_ms,
            "deauth_rate": round(self.deauth_rate, 1),
            "is_suspicious": self.is_suspicious,
            "threat_score": self.threat_score,
            "threat_types": self.threat_types,
            "threat_description": self.threat_description,
            "recommended_action": self.recommended_action,
            "is_mitigated": self.is_mitigated,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "rssi_history": self.rssi_history[-20:],
        }


class WirelessSecurityEngine:
    """
    Stateful Rule & Anomaly Detector for 802.11 Wireless Environments.
    Flags Evil Twins, Rogue APs, Deauth Flooding, Proximity Spikes, and Insecure Ciphers.
    """

    def __init__(
        self,
        rssi_proximity_threshold: int = -28,
        deauth_rate_threshold: float = 12.0,
        rssi_surge_delta: int = 18,
    ):
        self.rssi_proximity_threshold = rssi_proximity_threshold
        self.deauth_rate_threshold = deauth_rate_threshold
        self.rssi_surge_delta = rssi_surge_delta

    def evaluate_network(
        self,
        target_ap: WirelessAccessPoint,
        all_aps: List[WirelessAccessPoint],
    ) -> Tuple[bool, int, List[str], str, str]:
        """
        Runs comprehensive security rules on a single access point relative to the RF environment.
        Returns: (is_suspicious, threat_score, threat_types, threat_description, recommended_action)
        """
        threat_score = 0
        threat_types = []
        reasons = []
        mitigations = []

        # ----------------------------------------------------------------------
        # Rule 1: Evil Twin / SSID Spoofing Collision Detection
        # Multiple APs broadcasting identical SSID with mismatched BSSID & security downgrade or vendor conflict
        # ----------------------------------------------------------------------
        if target_ap.ssid and target_ap.ssid != "<Hidden SSID>":
            same_ssid_peers = [
                ap for ap in all_aps
                if ap.bssid != target_ap.bssid and ap.ssid.lower() == target_ap.ssid.lower()
            ]

            if same_ssid_peers:
                for peer in same_ssid_peers:
                    # Case A: One peer is Enterprise/WPA3 while the other is Open or WPA2-PSK
                    target_sec = target_ap.security.upper()
                    peer_sec = peer.security.upper()
                    is_downgrade = (
                        ("OPEN" in target_sec and "WPA" in peer_sec) or
                        ("WPA2" in target_sec and "WPA3" in peer_sec)
                    )
                    vendor_mismatch = (target_ap.vendor != peer.vendor and "Generic" not in target_ap.vendor and "Generic" not in peer.vendor)

                    if is_downgrade or vendor_mismatch:
                        threat_score = max(threat_score, 95)
                        threat_types.append("EVIL_TWIN")
                        reasons.append(
                            f"Evil Twin Detected: SSID '{target_ap.ssid}' duplicated across conflicting BSSIDs "
                            f"({target_ap.bssid} vs {peer.bssid}). "
                            f"Security: [{target_ap.security}] vs [{peer.security}]. Vendor: [{target_ap.vendor}]."
                        )
                        mitigations.append("Block BSSID on Wireless Controller; Do not connect; Verify AP physical MAC.")
                        break

        # ----------------------------------------------------------------------
        # Rule 2: Deauthentication / Disassociation Storm Attack (802.11 DoS / Handshake Harvest)
        # ----------------------------------------------------------------------
        if target_ap.deauth_rate >= self.deauth_rate_threshold:
            threat_score = max(threat_score, 90)
            threat_types.append("DEAUTH_STORM")
            reasons.append(
                f"Deauthentication Flood Detected: {target_ap.deauth_rate:.1f} deauth frames/sec directed at BSSID "
                f"{target_ap.bssid}. Indicates active WPA handshake capture or jamming tool (aireplay-ng / flipper zero)."
            )
            mitigations.append("Enable 802.11w Protected Management Frames (PMF); Locate RF source.")

        # ----------------------------------------------------------------------
        # Rule 3: Abnormal RSSI Proximity Spike / High-Gain Rogue AP
        # ----------------------------------------------------------------------
        if target_ap.rssi >= self.rssi_proximity_threshold:
            threat_score = max(threat_score, 82)
            threat_types.append("HIGH_POWER_ROGUE")
            reasons.append(
                f"Abnormal RSSI Proximity ({target_ap.rssi} dBm): Transmitter is unusually close (< 1.5m) "
                f"or operating with an unauthorized high-gain directional amplifier."
            )
            mitigations.append("Perform physical sweep of premises for unauthorized transmitter or rogue rogue dongle.")

        # Check RSSI surge in history
        if len(target_ap.rssi_history) >= 2:
            prev_rssi = target_ap.rssi_history[-2]["rssi"]
            delta = target_ap.rssi - prev_rssi
            if delta >= self.rssi_surge_delta:
                threat_score = max(threat_score, 75)
                threat_types.append("RSSI_SURGE")
                reasons.append(
                    f"Sudden RSSI Surge (+{delta} dBm): Signal jumped from {prev_rssi} dBm to {target_ap.rssi} dBm in seconds."
                )

        # ----------------------------------------------------------------------
        # Rule 4: Known Attacker Hardware Fingerprint (Hak5 Pineapple / Espressif Deauther)
        # ----------------------------------------------------------------------
        if "Hak5" in target_ap.vendor or "Pineapple" in target_ap.vendor or "00:13:37" in target_ap.bssid:
            threat_score = max(threat_score, 98)
            threat_types.append("ATTACKER_HARDWARE")
            reasons.append(
                f"Known Hostile Penetration Hardware Detected: BSSID matches Wi-Fi Pineapple OUI signature."
            )
            mitigations.append("Isolate perimeter immediately; initiate physical security protocol.")

        # ----------------------------------------------------------------------
        # Rule 5: Open Insecure Masquerading / Karma Honeypot
        # ----------------------------------------------------------------------
        if target_ap.security.upper() == "OPEN" and any(
            kw in target_ap.ssid.lower() for kw in ["secure", "corp", "internal", "faculty", "admin", "bank", "free_wifi"]
        ):
            threat_score = max(threat_score, 70)
            threat_types.append("OPEN_HONEYPOT")
            reasons.append(
                f"Suspicious Open Honeypot / Karma: Unencrypted AP broadcasting enticing name '{target_ap.ssid}'."
            )
            mitigations.append("Advise users against connecting; enforce captive portal validation.")

        # ----------------------------------------------------------------------
        # Rule 6: Deprecated Cryptography (WEP / WPA1)
        # ----------------------------------------------------------------------
        if "WEP" in target_ap.security.upper():
            threat_score = max(threat_score, 60)
            threat_types.append("WEAK_CIPHER_WEP")
            reasons.append(
                f"Critical Cryptographic Vulnerability: Network uses obsolete WEP cipher with known key recovery flaws."
            )
            mitigations.append("Upgrade AP to WPA2-AES (CCMP) or WPA3-SAE immediately.")

        is_suspicious = threat_score >= 50
        desc = " | ".join(reasons) if reasons else "Normal authorized wireless telemetry."
        mit = " | ".join(mitigations) if mitigations else "No action required."

        return is_suspicious, threat_score, threat_types, desc, mit


class LiveWirelessScanner:
    """
    Autonomous Live Wireless Monitoring Engine.
    Combines real Linux system interface scanning with high-fidelity realistic dynamic RF simulation.
    """

    _instance: Optional["LiveWirelessScanner"] = None
    _lock = threading.RLock()

    def __init__(self):
        self.aps: Dict[str, WirelessAccessPoint] = {}
        self.security_engine = WirelessSecurityEngine()
        self.is_scanning = True
        self.scan_interval = 2.0  # seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Telemetry counters
        self.total_scans_performed = 0
        self.active_interface_name = "wlan0 (Monitored)"
        self.hardware_mode = "Autonomous Live RF & Interface Monitor"

        # Initialize base networks
        self._init_default_networks()
        self.start()

    @classmethod
    def get_instance(cls) -> "LiveWirelessScanner":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _init_default_networks(self):
        """Initializes baseline realistic enterprise and domestic wireless environment."""
        initial_networks = [
            WirelessAccessPoint(
                bssid="00:14:22:3A:4B:5C",
                ssid="Campus_Secure_5G",
                rssi=-48,
                channel=36,
                security="WPA3-SAE",
                vendor="Cisco Systems",
                clients_count=18,
            ),
            WirelessAccessPoint(
                bssid="00:14:22:3A:4B:5D",
                ssid="Faculty_Staff_WiFi",
                rssi=-54,
                channel=44,
                security="WPA2-Enterprise",
                vendor="Cisco Systems",
                clients_count=12,
            ),
            WirelessAccessPoint(
                bssid="74:83:C2:11:22:33",
                ssid="Library_Study_Zone",
                rssi=-62,
                channel=6,
                security="WPA2-PSK",
                vendor="Aruba Networks (HPE)",
                clients_count=29,
            ),
            WirelessAccessPoint(
                bssid="B8:27:EB:44:55:66",
                ssid="IoT_SmartHub_Sensors",
                rssi=-71,
                channel=1,
                security="WPA2-PSK",
                vendor="Raspberry Pi Foundation",
                clients_count=8,
            ),
            WirelessAccessPoint(
                bssid="AC:84:C6:77:88:99",
                ssid="Guest_Cafeteria_Free",
                rssi=-65,
                channel=11,
                security="OPEN",
                vendor="TP-Link Technologies",
                clients_count=14,
            ),
            # Default Rogue AP for immediate live detection visibility
            WirelessAccessPoint(
                bssid="DE:AD:BE:EF:01:23",
                ssid="Campus_Secure_5G",  # Identical SSID -> Evil Twin!
                rssi=-35,
                channel=1,               # Mismatched band & channel!
                security="OPEN",         # Downgraded to Open!
                vendor="Locally Administered (Spoofed Attacker)",
                clients_count=3,
            ),
        ]

        with self._lock:
            for ap in initial_networks:
                self.aps[ap.bssid] = ap
                # Initial evaluation
                self._evaluate_single_ap(ap)

    def start(self):
        """Launches continuous background RF monitoring loop."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._scan_loop, daemon=True, name="LiveWirelessScannerThread")
            self._thread.start()

    def stop(self):
        """Halts the scanner background loop."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _scan_loop(self):
        """Continuous background scanning thread with realistic RF dynamics."""
        while not self._stop_event.is_set():
            if self.is_scanning:
                self._perform_scan_cycle()
            time.sleep(self.scan_interval)

    def _perform_scan_cycle(self):
        """Performs one scan update cycle."""
        with self._lock:
            self.total_scans_performed += 1
            now = time.time()

            # 1. Inspect real OS network interfaces if possible
            real_ifaces = self._discover_system_interfaces()
            if real_ifaces:
                # Update active interface name to first real wireless or primary interface
                for iface in real_ifaces:
                    if iface["is_wireless"] or iface["is_up"]:
                        self.active_interface_name = iface["name"]
                        break

            # 2. Update RF signals for all tracked access points
            all_aps = list(self.aps.values())
            for ap in all_aps:
                if ap.is_mitigated:
                    continue

                # Realistic RF Jitter (Gaussian noise +- 1 to 2 dBm)
                jitter = int(round(random.gauss(0, 1.2)))
                new_rssi = ap.rssi + jitter
                # Clamp within reasonable physical bounds (-95 to -20 dBm)
                new_rssi = max(-95, min(-20, new_rssi))
                ap.record_rssi(new_rssi, ts=now)

                # Minor client drift
                if random.random() < 0.2:
                    ap.clients_count = max(0, ap.clients_count + random.choice([-1, 0, 1]))

                # If AP has deauth attack in progress, decay or sustain
                if ap.deauth_rate > 0:
                    ap.deauth_rate = max(0.0, ap.deauth_rate - 1.5)

                # Re-evaluate security state
                self._evaluate_single_ap(ap)

    def _evaluate_single_ap(self, ap: WirelessAccessPoint):
        """Evaluates an AP against all rules using the full environment."""
        all_aps = list(self.aps.values())
        suspicious, score, types, desc, action = self.security_engine.evaluate_network(ap, all_aps)
        ap.is_suspicious = suspicious
        ap.threat_score = score
        ap.threat_types = types
        ap.threat_description = desc
        ap.recommended_action = action

    def _discover_system_interfaces(self) -> List[Dict[str, Any]]:
        """Reads host network interfaces and live traffic statistics via /proc/net/dev."""
        interfaces = []
        proc_dev = "/proc/net/dev"
        if not os.path.exists(proc_dev):
            return interfaces

        try:
            with open(proc_dev, "r") as f:
                lines = f.readlines()

            for line in lines[2:]:  # Skip headers
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                iface = iface.strip()
                fields = data.split()
                if len(fields) >= 16:
                    rx_bytes = int(fields[0])
                    rx_packets = int(fields[1])
                    tx_bytes = int(fields[8])
                    tx_packets = int(fields[9])
                else:
                    rx_bytes = rx_packets = tx_bytes = tx_packets = 0

                is_wireless = iface.startswith("wl") or "wlan" in iface
                interfaces.append({
                    "name": iface,
                    "is_wireless": is_wireless,
                    "is_up": True,
                    "state": "up",
                    "mac_address": "02:00:00:00:00:01" if iface == "lo" else "00:15:5d:01:02:03",
                    "rx_bytes": rx_bytes,
                    "tx_bytes": tx_bytes,
                    "rx_packets": rx_packets,
                    "tx_packets": tx_packets,
                })
        except Exception:
            pass

        return interfaces

    def trigger_scan(self) -> Dict[str, Any]:
        """Triggers an instantaneous scan cycle."""
        self._perform_scan_cycle()
        return self.get_summary()

    def get_all_networks(self, suspicious_only: bool = False) -> List[Dict[str, Any]]:
        """Returns serialized dictionaries of all or suspicious networks."""
        with self._lock:
            networks = list(self.aps.values())
            if suspicious_only:
                networks = [ap for ap in networks if ap.is_suspicious]
            # Sort by RSSI descending (strongest signal first)
            networks.sort(key=lambda x: (x.is_suspicious, x.rssi), reverse=True)
            return [ap.to_dict() for ap in networks]

    def get_suspicious_networks(self) -> List[Dict[str, Any]]:
        """Returns only networks flagged as suspicious or rogue."""
        return self.get_all_networks(suspicious_only=True)

    def get_spectrum_data(self) -> Dict[str, Any]:
        """
        Calculates 2.4 GHz and 5 GHz channel occupancy & RSSI distributions for spectrum analysis.
        """
        with self._lock:
            # 2.4 GHz channels 1 to 14
            channels_24 = {ch: {"count": 0, "strongest_rssi": -100, "networks": []} for ch in range(1, 15)}
            # 5 GHz primary channels
            channels_50 = {ch: {"count": 0, "strongest_rssi": -100, "networks": []} for ch in [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 149, 153, 157, 161, 165]}

            for ap in self.aps.values():
                ch = ap.channel
                net_info = {
                    "ssid": ap.ssid,
                    "bssid": ap.bssid,
                    "rssi": ap.rssi,
                    "is_suspicious": ap.is_suspicious,
                    "security": ap.security,
                }

                if ch in channels_24:
                    channels_24[ch]["count"] += 1
                    channels_24[ch]["networks"].append(net_info)
                    if ap.rssi > channels_24[ch]["strongest_rssi"]:
                        channels_24[ch]["strongest_rssi"] = ap.rssi
                elif ch in channels_50:
                    channels_50[ch]["count"] += 1
                    channels_50[ch]["networks"].append(net_info)
                    if ap.rssi > channels_50[ch]["strongest_rssi"]:
                        channels_50[ch]["strongest_rssi"] = ap.rssi

            return {
                "band_2_4ghz": channels_24,
                "band_5ghz": channels_50,
                "timestamp": time.time(),
            }

    def get_rssi_history_timeline(self, limit: int = 15) -> Dict[str, Any]:
        """
        Returns structured time-series RSSI data for top and suspicious networks for plotting.
        """
        with self._lock:
            series = []
            for ap in sorted(self.aps.values(), key=lambda x: (x.is_suspicious, x.rssi), reverse=True)[:limit]:
                series.append({
                    "bssid": ap.bssid,
                    "ssid": ap.ssid,
                    "is_suspicious": ap.is_suspicious,
                    "threat_score": ap.threat_score,
                    "current_rssi": ap.rssi,
                    "color": "#f43f5e" if ap.is_suspicious else "#00f0ff" if ap.band == "5 GHz" else "#10b981",
                    "history": ap.rssi_history,
                })
            return {"timeline_series": series, "timestamp": time.time()}

    def inject_threat(self, threat_type: str) -> Dict[str, Any]:
        """
        Injects a dynamic live wireless threat for interactive testing and viva demonstrations.
        """
        with self._lock:
            now = time.time()
            if threat_type == "EVIL_TWIN":
                rogue = WirelessAccessPoint(
                    bssid=f"02:AA:BB:{random.randint(10,99)}:{random.randint(10,99)}:{random.randint(10,99)}",
                    ssid="Faculty_Staff_WiFi",  # Spoofing legitimate enterprise SSID
                    rssi=-32,
                    channel=6,
                    security="OPEN",  # Rogue downgrade
                    vendor="Locally Administered (Spoofed Attacker)",
                    clients_count=2,
                )
                self.aps[rogue.bssid] = rogue
                self._evaluate_single_ap(rogue)
                return {"status": "injected", "threat": "EVIL_TWIN", "target": rogue.to_dict()}

            elif threat_type == "DEAUTH_STORM":
                # Target first legitimate network with high deauth rate
                target = next((ap for ap in self.aps.values() if not ap.is_suspicious), None)
                if target:
                    target.deauth_rate = 34.5  # 34.5 deauth/sec!
                    self._evaluate_single_ap(target)
                    return {"status": "injected", "threat": "DEAUTH_STORM", "target": target.to_dict()}

            elif threat_type == "HIGH_POWER_ROGUE":
                rogue = WirelessAccessPoint(
                    bssid="00:13:37:C0:FF:EE",
                    ssid="PINEAPPLE_ROGUE_GUEST",
                    rssi=-22,  # Ultra-strong proximity signal!
                    channel=11,
                    security="OPEN",
                    vendor="Hak5 / Wi-Fi Pineapple (Hostile Hardware)",
                    clients_count=7,
                )
                self.aps[rogue.bssid] = rogue
                self._evaluate_single_ap(rogue)
                return {"status": "injected", "threat": "HIGH_POWER_ROGUE", "target": rogue.to_dict()}

            elif threat_type == "WEP_LEGACY":
                rogue = WirelessAccessPoint(
                    bssid="00:09:5B:DE:AD:01",
                    ssid="Old_Warehouse_AP",
                    rssi=-58,
                    channel=3,
                    security="WEP-64",
                    vendor="Netgear Inc.",
                    clients_count=1,
                )
                self.aps[rogue.bssid] = rogue
                self._evaluate_single_ap(rogue)
                return {"status": "injected", "threat": "WEP_LEGACY", "target": rogue.to_dict()}

            return {"status": "error", "message": f"Unknown threat type: {threat_type}"}

    def mitigate_network(self, bssid: str) -> bool:
        """Flags a rogue network as mitigated / quarantined."""
        with self._lock:
            ap = self.aps.get(bssid.upper())
            if ap:
                ap.is_mitigated = True
                ap.is_suspicious = False
                ap.threat_description = "Quarantined and mitigated by network administrator."
                ap.threat_score = 0
                return True
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Returns holistic wireless environment summary metrics."""
        with self._lock:
            all_aps = list(self.aps.values())
            suspicious_aps = [ap for ap in all_aps if ap.is_suspicious and not ap.is_mitigated]
            avg_rssi = sum(ap.rssi for ap in all_aps) / len(all_aps) if all_aps else -70.0
            total_clients = sum(ap.clients_count for ap in all_aps)

            # System interfaces
            interfaces = self._discover_system_interfaces()

            return {
                "total_networks": len(all_aps),
                "suspicious_count": len(suspicious_aps),
                "clean_count": len(all_aps) - len(suspicious_aps),
                "average_rssi_dbm": round(avg_rssi, 1),
                "total_associated_clients": total_clients,
                "active_interface": self.active_interface_name,
                "hardware_mode": self.hardware_mode,
                "is_scanning": self.is_scanning,
                "total_scans_performed": self.total_scans_performed,
                "system_interfaces": interfaces,
                "timestamp": time.time(),
            }


def get_wireless_scanner() -> LiveWirelessScanner:
    """Helper accessor for the LiveWirelessScanner singleton."""
    return LiveWirelessScanner.get_instance()
