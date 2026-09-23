"""
Decision Tree Training Script.

Generates ground-truth network connection training samples representing:
1. Normal Traffic: Established TCP (SF state), standard HTTP/DNS transactions.
2. Port Scan Probes: Rapid SYN attempts without ACK (S0 state), low packet count (< 3), small duration.
3. Denial of Service / SYN Flood: High rate of rejected (REJ) or unanswered (S0) requests.
4. Data Exfiltration: Unusually high payload volume (> 5MB) on single connections.

Trains a scikit-learn DecisionTreeClassifier, evaluates accuracy, and serializes the model.
"""

import os
import random
from typing import List, Tuple
from detection.ml.feature_extractor import NetworkFeatureExtractor

try:
    import joblib
    import numpy as np
    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def generate_synthetic_training_data(n_samples: int = 1000) -> Tuple[List[List[float]], List[int]]:
    """
    Generates realistic network feature vectors and ground-truth labels (0 = Normal, 1 = Suspicious).
    """
    X = []
    y = []

    for _ in range(n_samples):
        traffic_type = random.choices(["normal", "port_scan", "syn_flood", "exfil"], weights=[0.6, 0.2, 0.1, 0.1])[0]

        if traffic_type == "normal":
            # Normal HTTP/DNS/TLS traffic
            duration = random.uniform(0.1, 15.0)
            orig_bytes = random.randint(100, 20000)
            resp_bytes = random.randint(200, 150000)
            proto_tcp = 1.0 if random.random() > 0.3 else 0.0
            proto_udp = 1.0 - proto_tcp
            proto_other = 0.0
            conn_state_failed = 0.0  # SF state
            dest_port_privileged = 1.0 if random.choice([80, 443, 53, 22]) < 1024 else 0.0
            orig_pkts = float(random.randint(3, 40))
            resp_pkts = float(random.randint(3, 80))
            label = 0

        elif traffic_type == "port_scan":
            # Fast scan probe (S0 or REJ, 1-2 packets, 0 payload)
            duration = random.uniform(0.001, 0.2)
            orig_bytes = 0.0
            resp_bytes = 0.0
            proto_tcp = 1.0
            proto_udp = 0.0
            proto_other = 0.0
            conn_state_failed = 1.0  # S0 / REJ
            dest_port_privileged = 1.0 if random.random() > 0.5 else 0.0
            orig_pkts = float(random.choice([1, 2]))
            resp_pkts = 0.0
            label = 1

        elif traffic_type == "syn_flood":
            # Flooding attack (S0 state, zero bytes, 1 packet)
            duration = random.uniform(0.01, 1.0)
            orig_bytes = 0.0
            resp_bytes = 0.0
            proto_tcp = 1.0
            proto_udp = 0.0
            proto_other = 0.0
            conn_state_failed = 1.0
            dest_port_privileged = 1.0
            orig_pkts = float(random.randint(1, 3))
            resp_pkts = 0.0
            label = 1

        else:  # exfiltration
            # Suspicious large transfer
            duration = random.uniform(10.0, 120.0)
            orig_bytes = float(random.randint(6_000_000, 50_000_000))
            resp_bytes = float(random.randint(500, 5000))
            proto_tcp = 1.0
            proto_udp = 0.0
            proto_other = 0.0
            conn_state_failed = 0.0
            dest_port_privileged = 0.0
            orig_pkts = float(random.randint(500, 4000))
            resp_pkts = float(random.randint(100, 500))
            label = 1

        features = [
            duration, orig_bytes, resp_bytes, proto_tcp, proto_udp,
            proto_other, conn_state_failed, dest_port_privileged,
            orig_pkts, resp_pkts
        ]
        X.append(features)
        y.append(label)

    return X, y


def train_and_save_decision_tree():
    """Trains the Decision Tree and serializes model artifact."""
    if not SKLEARN_AVAILABLE:
        print("[!] scikit-learn is not available; skipping binary model serialization.")
        return

    print("[*] Generating synthetic network training dataset (1200 samples)...")
    X, y = generate_synthetic_training_data(1200)

    # Train interpretable CART tree with max_depth=4
    clf = DecisionTreeClassifier(max_depth=4, criterion="gini", random_state=42)
    clf.fit(X, y)

    # Validate training accuracy
    X_val, y_val = generate_synthetic_training_data(300)
    preds = clf.predict(X_val)
    acc = accuracy_score(y_val, preds)
    print(f"[+] Decision Tree Validation Accuracy: {acc * 100:.2f}%")

    model_dir = os.path.join(os.path.dirname(__file__), "model")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "decision_tree.joblib")
    joblib.dump(clf, model_path)
    print(f"[+] Model saved to {model_path}")

    # Print textual representation of tree for viva review
    tree_rules = export_text(clf, feature_names=NetworkFeatureExtractor.FEATURE_NAMES)
    rules_path = os.path.join(model_dir, "tree_rules.txt")
    with open(rules_path, "w") as f:
        f.write(tree_rules)
    print(f"[+] Readable tree rules written to {rules_path}")


if __name__ == "__main__":
    train_and_save_decision_tree()
