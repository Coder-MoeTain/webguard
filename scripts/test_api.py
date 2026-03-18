#!/usr/bin/env python3
"""Quick API smoke test. Run with backend at http://127.0.0.1:8001."""
import sys
import requests

BASE = "http://127.0.0.1:8001"
FAILED = []


def test(name: str, fn):
    try:
        fn()
        print(f"  OK {name}")
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        FAILED.append(name)


def main():
    print("WebGuard RF API Smoke Test\n")

    test("health", lambda: requests.get(f"{BASE}/health").raise_for_status())
    r = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
    test("login", lambda: r.raise_for_status())
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    test("datasets list", lambda: requests.get(f"{BASE}/api/datasets/", headers=headers).raise_for_status())
    test("models list", lambda: requests.get(f"{BASE}/api/models/", headers=headers).raise_for_status())
    test("training list", lambda: requests.get(f"{BASE}/api/training/", headers=headers).raise_for_status())
    test("inference predict", lambda: requests.post(
        f"{BASE}/api/inference/predict", json={"body": "' OR 1=1--", "request_method": "GET"}, headers=headers
    ).raise_for_status())
    test("ids analyze", lambda: requests.post(
        f"{BASE}/api/ids/analyze", json={"method": "GET", "url": "/search", "query_params": "' OR 1=1--"}, headers=headers
    ).raise_for_status())

    # Ratio validation
    r = requests.post(f"{BASE}/api/training/start", headers=headers, json={
        "data_path": "data/sample_sqli_37_features.parquet",
        "train_ratio": 0.5, "val_ratio": 0.5, "test_ratio": 0.5
    })
    if r.status_code == 422:
        print("  OK training ratio validation (rejects invalid)")
    else:
        print("  FAIL training ratio validation: expected 422")

    print("\n" + ("All passed." if not FAILED else f"Failed: {FAILED}"))
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
