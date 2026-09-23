"""
Knuth-Morris-Pratt (KMP) String Matching Algorithm.

Academic Context (Data Structures & Algorithms / Discrete Math):
- Problem: Searching for occurrences of a pattern P of length M within a text T of length N.
- Naive Approach: Checks all possible alignments. Worst-case time complexity: O(N * M).
- KMP Improvement: Utilizes information gained from partial matches to avoid backtracking
  the text pointer `i`. When a mismatch occurs, the pattern pointer `j` jumps to the index
  indicated by the precomputed Longest Prefix-Suffix (LPS) array.
- Time Complexity:
    - Preprocessing (LPS construction): O(M)
    - Search Phase: O(N)
    - Total Time Complexity: O(N + M)
- Space Complexity: O(M) for the LPS array.
"""

from typing import List, Tuple
import time


def compute_lps_array(pattern: str) -> List[int]:
    """
    Computes the Longest Prefix which is also a proper Suffix (LPS) array.

    For each index i, lps[i] stores the length of the longest proper prefix of
    pattern[0...i] that is also a suffix of pattern[0...i].

    Args:
        pattern (str): The search pattern.

    Returns:
        List[int]: Precomputed LPS table of length len(pattern).
    """
    m = len(pattern)
    lps = [0] * m
    length = 0  # Length of the previous longest prefix suffix
    i = 1

    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                # Do not increment i; check the previous longest prefix
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1

    return lps


def kmp_search(text: str, pattern: str, case_sensitive: bool = True) -> List[int]:
    """
    Searches for all occurrences of pattern in text using KMP.

    Args:
        text (str): The corpus text to search within.
        pattern (str): The keyword/signature to match.
        case_sensitive (bool): If False, both text and pattern are converted to lowercase.

    Returns:
        List[int]: 0-indexed starting positions where pattern occurs in text.
    """
    if not pattern or not text:
        return []

    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()

    n = len(text)
    m = len(pattern)

    if m > n:
        return []

    lps = compute_lps_array(pattern)
    matches = []

    i = 0  # Index for text
    j = 0  # Index for pattern

    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1

        if j == m:
            matches.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return matches


def naive_search(text: str, pattern: str, case_sensitive: bool = True) -> List[int]:
    """
    Naive string matching algorithm for academic comparison and benchmarking.
    Time Complexity: O((N - M + 1) * M).
    """
    if not pattern or not text:
        return []

    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()

    n = len(text)
    m = len(pattern)
    matches = []

    for i in range(n - m + 1):
        match = True
        for j in range(m):
            if text[i + j] != pattern[j]:
                match = False
                break
        if match:
            matches.append(i)

    return matches


def benchmark_kmp_vs_naive(text: str, pattern: str, iterations: int = 100) -> Tuple[float, float, List[int]]:
    """
    Benchmarks execution time of KMP versus Naive search over specified iterations.
    Used for academic demonstration of asymptotic efficiency.
    """
    # Benchmark KMP
    start = time.perf_counter()
    kmp_matches = []
    for _ in range(iterations):
        kmp_matches = kmp_search(text, pattern)
    kmp_duration = time.perf_counter() - start

    # Benchmark Naive
    start = time.perf_counter()
    naive_matches = []
    for _ in range(iterations):
        naive_matches = naive_search(text, pattern)
    naive_duration = time.perf_counter() - start

    assert kmp_matches == naive_matches, "KMP and Naive results must match exactly!"
    return kmp_duration, naive_duration, kmp_matches
