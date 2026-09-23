"""
Unit Tests for KMP String Matching.

Academic Verification (DSA / Discrete Math):
- Verifies LPS array preprocessing.
- Verifies exact search results vs naive search.
- Verifies edge cases (empty strings, pattern longer than text, repeated substrings).
"""

import unittest
from processor.dsa.kmp import compute_lps_array, kmp_search, naive_search, benchmark_kmp_vs_naive


class TestKMPAlgorithm(unittest.TestCase):

    def test_lps_array_computation(self):
        """Validates LPS table for standard patterns."""
        # Pattern "AABAACAABAA"
        lps = compute_lps_array("AABAACAABAA")
        expected = [0, 1, 0, 1, 2, 0, 1, 2, 3, 4, 5]
        self.assertEqual(lps, expected)

        # Pattern with no repeating prefix/suffix
        lps_none = compute_lps_array("ABCDEF")
        self.assertEqual(lps_none, [0, 0, 0, 0, 0, 0])

        # Single character repeating
        lps_rep = compute_lps_array("AAAA")
        self.assertEqual(lps_rep, [0, 1, 2, 3])

    def test_kmp_search_matches(self):
        text = "GET /index.php?user=admin&cmd=cat%20/etc/passwd HTTP/1.1"
        pattern = "/etc/passwd"
        matches = kmp_search(text, pattern)
        self.assertEqual(len(matches), 1)
        self.assertEqual(text[matches[0]:matches[0] + len(pattern)], pattern)

    def test_multiple_occurrences(self):
        text = "union select 1 from users union select 2 from passwords"
        pattern = "union select"
        matches = kmp_search(text, pattern)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches, [0, 26])

    def test_pattern_not_found(self):
        text = "normal benign network connection"
        pattern = "malicious_exploit"
        matches = kmp_search(text, pattern)
        self.assertEqual(matches, [])

    def test_edge_cases(self):
        self.assertEqual(kmp_search("", "pattern"), [])
        self.assertEqual(kmp_search("text", ""), [])
        self.assertEqual(kmp_search("short", "longer_pattern_than_text"), [])

    def test_equivalence_with_naive_search(self):
        corpus = "ababcabcabababd" * 10
        pattern = "ababd"
        kmp_res = kmp_search(corpus, pattern)
        naive_res = naive_search(corpus, pattern)
        self.assertEqual(kmp_res, naive_res)
        self.assertGreater(len(kmp_res), 0)


if __name__ == "__main__":
    unittest.main()
