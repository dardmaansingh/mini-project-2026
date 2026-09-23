"""
Regular Expression Formal Pattern Engine.

Academic Context (Discrete Mathematics & Formal Languages):
- Regular expressions represent Type-3 grammars in the Chomsky Hierarchy, recognized by
  Deterministic Finite Automata (DFA) and Non-deterministic Finite Automata (NFA).
- Formal Safety Property: An alert is triggered ONLY IF the input string w in L(R), where
  L(R) is the regular language accepted by regex pattern R.
- Used to identify known malicious signatures in connection history, service names, and payload URIs.
"""

import re
import urllib.parse
from typing import Dict, List, Optional, Any


class PatternMatchResult:
    """Holds structured outcome of a pattern matching evaluation."""
    def __init__(self, matched: bool, pattern_name: str, matched_text: str, severity: str, description: str):
        self.matched = matched
        self.pattern_name = pattern_name
        self.matched_text = matched_text
        self.severity = severity
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched": self.matched,
            "pattern_name": self.pattern_name,
            "matched_text": self.matched_text,
            "severity": self.severity,
            "description": self.description,
        }


class RegexPatternDetector:
    """
    Regex detection engine applying compiled automata patterns to log attributes.
    """

    def __init__(self):
        # Compiled DFAs for signature detection
        self.patterns = {
            "DIR_TRAVERSAL": {
                "regex": re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%252e%252e%252f)", re.IGNORECASE),
                "severity": "HIGH",
                "description": "Path Traversal attack attempting unauthorized directory access",
            },
            "SQL_INJECTION": {
                "regex": re.compile(r"(union\s+select|select\s+.*from|information_schema|waitfor\s+delay|or\s+1=1)", re.IGNORECASE),
                "severity": "CRITICAL",
                "description": "SQL Injection attempt targeting relational database",
            },
            "COMMAND_INJECTION": {
                "regex": re.compile(r"(;\s*(cat|ls|sh|bash|curl|wget|id|whoami|nc)\b|\|\s*(bash|sh)\b)", re.IGNORECASE),
                "severity": "CRITICAL",
                "description": "OS Command Injection sequence detected in URI or payload",
            },
            "SCANNER_USER_AGENT": {
                "regex": re.compile(r"(sqlmap|nikto|nmap|masscan|zgrab|nessus|openvas|gobuster)", re.IGNORECASE),
                "severity": "MEDIUM",
                "description": "Automated security scanner or reconnaissance tool signature",
            },
            "SENSITIVE_FILE_PROBE": {
                "regex": re.compile(r"(\.env|\.git/config|wp-config\.php|passwd|shadow|web\.config)", re.IGNORECASE),
                "severity": "HIGH",
                "description": "Reconnaissance targeting sensitive credential files",
            },
            "REJECTED_CONNECTION_ANOMALY": {
                "regex": re.compile(r"^(REJ|RSTO|RSTOS0)$"),
                "severity": "LOW",
                "description": "Immediate connection rejection or reset state",
            }
        }

    def evaluate_text(self, text: str) -> Optional[PatternMatchResult]:
        """
        Tests a text string against compiled regular expressions.
        Decodes URL encoding (%20, etc.) for robust deep packet/URI inspection.
        Returns first matching pattern result, or None if no match.
        """
        if not text:
            return None

        # Normalize URL encoding for web strings
        decoded_text = urllib.parse.unquote_plus(text)

        for name, spec in self.patterns.items():
            match = spec["regex"].search(decoded_text)
            if match:
                return PatternMatchResult(
                    matched=True,
                    pattern_name=name,
                    matched_text=match.group(0),
                    severity=spec["severity"],
                    description=spec["description"],
                )
        return None

    def evaluate_event(self, event: Dict[str, Any]) -> List[PatternMatchResult]:
        """
        Inspects all relevant textual fields of a Zeek event.
        """
        results = []

        # Check service / URI / history strings
        fields_to_check = [
            ("service", event.get("service", "")),
            ("history", event.get("history", "")),
            ("conn_state", event.get("conn_state", "")),
            ("uri", event.get("uri", "")),
            ("user_agent", event.get("user_agent", "")),
        ]

        for field_name, value in fields_to_check:
            if value and isinstance(value, str):
                match = self.evaluate_text(value)
                if match:
                    results.append(match)

        return results
