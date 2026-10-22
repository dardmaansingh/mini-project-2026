"""
Unit Tests for Wireless Security & Anomaly Detection Engine.

Validates:
- Evil Twin / SSID collision detection with security downgrade or vendor mismatch.
- Deauthentication storm detection (DoS / handshake capture threshold).
- Abnormal RSSI proximity surge detection.
- Path-loss distance and signal quality calculations.
- Known hostile penetration hardware (Wi-Fi Pineapple OUI) detection.
"""

import unittest
from detection.wireless.wireless_analyzer import (
    WirelessAccessPoint,
    WirelessSecurityEngine,
    calculate_signal_quality,
    calculate_estimated_distance,
    channel_to_frequency,
    resolve_oui_vendor,
)


class TestWirelessDetection(unittest.TestCase):

    def setUp(self):
        self.engine = WirelessSecurityEngine(
            rssi_proximity_threshold=-28,
            deauth_rate_threshold=12.0,
            rssi_surge_delta=18,
        )

    def test_signal_quality_and_distance_math(self):
        """Validates standard 802.11 signal quality mapping and path loss distance."""
        # -50 dBm -> 100% quality
        self.assertEqual(calculate_signal_quality(-50), 100)
        # -100 dBm -> 0% quality
        self.assertEqual(calculate_signal_quality(-100), 0)
        # -75 dBm -> 50% quality
        self.assertEqual(calculate_signal_quality(-75), 50)

        # Distance estimation: at -30 dBm (tx_power), distance should be approx 1 meter
        dist_1m = calculate_estimated_distance(-30, tx_power=-30)
        self.assertAlmostEqual(dist_1m, 1.0, places=1)

        # Weaker signal -> further distance
        dist_far = calculate_estimated_distance(-80, tx_power=-30)
        self.assertGreater(dist_far, dist_1m)

    def test_channel_frequency_conversion(self):
        """Verifies 2.4 GHz and 5 GHz channel to frequency calculation."""
        self.assertEqual(channel_to_frequency(1), 2412)
        self.assertEqual(channel_to_frequency(6), 2437)
        self.assertEqual(channel_to_frequency(11), 2462)
        self.assertEqual(channel_to_frequency(36), 5180)
        self.assertEqual(channel_to_frequency(44), 5220)

    def test_oui_vendor_lookup(self):
        """Verifies MAC OUI resolution and randomized MAC detection."""
        self.assertEqual(resolve_oui_vendor("00:14:22:11:22:33"), "Cisco Systems")
        self.assertEqual(resolve_oui_vendor("74:83:C2:AA:BB:CC"), "Aruba Networks (HPE)")
        self.assertEqual(resolve_oui_vendor("00:13:37:01:02:03"), "Hak5 / Wi-Fi Pineapple (Hostile Hardware)")

    def test_evil_twin_detection(self):
        """Verifies that an AP broadcasting the same SSID with downgraded security is flagged."""
        legit_ap = WirelessAccessPoint(
            bssid="00:14:22:3A:4B:5C",
            ssid="Campus_Secure_5G",
            rssi=-50,
            channel=36,
            security="WPA3-SAE",
            vendor="Cisco Systems",
        )

        evil_twin = WirelessAccessPoint(
            bssid="DE:AD:BE:EF:01:23",
            ssid="Campus_Secure_5G",
            rssi=-35,
            channel=1,
            security="OPEN",  # Downgraded to Open!
            vendor="Locally Administered (Spoofed Attacker)",
        )

        all_aps = [legit_ap, evil_twin]
        is_suspicious, score, threat_types, desc, _ = self.engine.evaluate_network(evil_twin, all_aps)

        self.assertTrue(is_suspicious)
        self.assertGreaterEqual(score, 90)
        self.assertIn("EVIL_TWIN", threat_types)
        self.assertIn("Campus_Secure_5G", desc)

    def test_deauth_storm_detection(self):
        """Verifies high deauth frame rates trigger critical alerts."""
        target_ap = WirelessAccessPoint(
            bssid="AC:84:C6:77:88:99",
            ssid="Office_WLAN",
            rssi=-60,
            channel=11,
            security="WPA2-PSK",
        )
        target_ap.deauth_rate = 25.0  # Above 12.0 threshold

        is_suspicious, score, threat_types, _, _ = self.engine.evaluate_network(target_ap, [target_ap])
        self.assertTrue(is_suspicious)
        self.assertIn("DEAUTH_STORM", threat_types)
        self.assertGreaterEqual(score, 90)

    def test_high_power_rogue_and_rssi_surge(self):
        """Verifies that unnatural proximity signal strength (> -28 dBm) triggers alarm."""
        rogue_ap = WirelessAccessPoint(
            bssid="00:13:37:C0:FF:EE",
            ssid="Pineapple_Trap",
            rssi=-22,  # Extreme signal
            channel=6,
            security="OPEN",
            vendor="Hak5 / Wi-Fi Pineapple (Hostile Hardware)",
        )

        is_suspicious, score, threat_types, _, _ = self.engine.evaluate_network(rogue_ap, [rogue_ap])
        self.assertTrue(is_suspicious)
        self.assertIn("HIGH_POWER_ROGUE", threat_types)
        self.assertIn("ATTACKER_HARDWARE", threat_types)
        self.assertGreaterEqual(score, 90)


if __name__ == "__main__":
    unittest.main()
