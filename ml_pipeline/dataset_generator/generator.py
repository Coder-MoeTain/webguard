"""
WebGuard RF - Dataset Generator
Scalable generation of 5M samples with HTTP request/response simulation.
"""

import random
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List

import pandas as pd
from tqdm import tqdm

from .payloads import SQLiPayloads, XSSPayloads, CSRFPayloads, BenignPayloads


# HTTP simulation constants
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
ENDPOINTS = [
    "/search", "/login", "/api/users", "/api/products", "/contact",
    "/admin", "/profile", "/cart", "/checkout", "/api/transfer"
]
CONTENT_TYPES = ["application/json", "application/x-www-form-urlencoded", "text/plain", "multipart/form-data"]
STATUS_CODES = [200, 201, 302, 400, 401, 403, 404, 500]


def simulate_http_record(
    payload: str,
    label: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a simulated HTTP request-response record."""
    if seed is not None:
        random.seed(seed)
    r = random.random()

    method = "POST" if label == "csrf" and r < 0.8 else random.choice(METHODS)
    url = f"https://example.com{random.choice(ENDPOINTS)}"
    if method == "GET":
        url += f"?q={payload[:100]}" if len(payload) < 100 else f"?q={payload[:50]}..."

    has_cookies = random.random() < 0.7
    has_token = random.random() < 0.5 and label != "csrf"
    has_referer = random.random() < 0.6

    status = random.choice([200, 201, 302]) if label == "benign" else (
        random.choice([200, 400, 403, 500]) if random.random() < 0.7 else 200
    )
    response_length = random.randint(100, 50000) if status == 200 else random.randint(0, 500)
    response_time = random.uniform(10, 500)

    return {
        "id": str(uuid.uuid4()),
        "payload": payload,
        "label": label,
        "request_method": method,
        "url": url,
        "endpoint_type": "api" if "/api/" in url else "page",
        "headers": "application/json" if "json" in str(payload) else "form",
        "cookies_present": has_cookies,
        "token_present": has_token,
        "referrer_present": has_referer,
        "content_type": random.choice(CONTENT_TYPES),
        "response_status": status,
        "response_length": response_length,
        "response_time": response_time,
        "error_flag": status >= 400,
        "redirection_flag": status in (301, 302, 303),
    }


class DatasetGenerator:
    """Generate large-scale attack/benign datasets with HTTP simulation."""

    def __init__(
        self,
        total_samples: int = 5_000_000,
        attack_ratio: float = 0.8,
        benign_ratio: float = 0.2,
        sqli_ratio: float = 1 / 3,
        xss_ratio: float = 1 / 3,
        csrf_ratio: float = 1 / 3,
        random_seed: Optional[int] = None,
        label_noise_ratio: float = 0.02,
    ):
        self.total_samples = total_samples
        self.attack_ratio = attack_ratio
        self.benign_ratio = benign_ratio
        self.sqli_ratio = sqli_ratio
        self.xss_ratio = xss_ratio
        self.csrf_ratio = csrf_ratio
        self.random_seed = random_seed
        self.label_noise_ratio = label_noise_ratio

        self.sqli_gen = SQLiPayloads()
        self.xss_gen = XSSPayloads()
        self.csrf_gen = CSRFPayloads()
        self.benign_gen = BenignPayloads()

    def _compute_distribution(self) -> Dict[str, int]:
        attack_total = int(self.total_samples * self.attack_ratio)
        benign_total = int(self.total_samples * self.benign_ratio)
        sqli = int(attack_total * self.sqli_ratio)
        xss = int(attack_total * self.xss_ratio)
        csrf = attack_total - sqli - xss
        return {
            "sqli": sqli,
            "xss": xss,
            "csrf": csrf,
            "benign": benign_total,
        }

    def _generate_for_label(self, label: str, count: int, seed_offset: int = 0) -> List[Dict[str, Any]]:
        """Generate records for a single label."""
        if label == "sqli":
            payloads = self.sqli_gen.generate(count, self.random_seed + seed_offset if self.random_seed else None)
        elif label == "xss":
            payloads = self.xss_gen.generate(count, self.random_seed + seed_offset if self.random_seed else None)
        elif label == "csrf":
            payloads = self.csrf_gen.generate(count, self.random_seed + seed_offset if self.random_seed else None)
        else:
            payloads = self.benign_gen.generate(count, self.random_seed + seed_offset if self.random_seed else None)
        records = [simulate_http_record(p, label, self.random_seed) for p in payloads]
        if self.label_noise_ratio > 0:
            records = self._apply_label_noise(records, seed_offset)
        return records

    def _apply_label_noise(self, records: List[Dict[str, Any]], seed_offset: int) -> List[Dict[str, Any]]:
        """Randomly flip a small fraction of labels to simulate real-world imperfection."""
        if self.random_seed is not None:
            random.seed(self.random_seed + seed_offset + 99999)
        labels = ["benign", "sqli", "xss", "csrf"]
        for r in records:
            if random.random() < self.label_noise_ratio:
                r["label"] = random.choice([l for l in labels if l != r["label"]])
        return records

    def generate(
        self,
        output_path: str,
        format: str = "parquet",
        chunk_size: int = 100_000,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Generate full dataset and save to file. Uses chunked writing for memory efficiency."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        dist = self._compute_distribution()
        total = sum(dist.values())
        written = 0

        if format == "parquet":
            first = True
            for label, count in tqdm(dist.items(), desc="Labels"):
                for i in range(0, count, chunk_size):
                    take = min(chunk_size, count - i)
                    records = self._generate_for_label(label, take, seed_offset=written)
                    df = pd.DataFrame(records)
                    if first:
                        df.to_parquet(output_path, index=False, engine="pyarrow")
                        first = False
                    else:
                        existing = pd.read_parquet(output_path)
                        combined = pd.concat([existing, df], ignore_index=True)
                        combined.to_parquet(output_path, index=False, engine="pyarrow")
                    written += len(records)
                    if progress_callback:
                        progress_callback(written, total)
        else:
            dfs = []
            for label, count in tqdm(dist.items(), desc="Labels"):
                for i in range(0, count, chunk_size):
                    take = min(chunk_size, count - i)
                    records = self._generate_for_label(label, take, seed_offset=written)
                    dfs.append(pd.DataFrame(records))
                    written += len(records)
                    if progress_callback:
                        progress_callback(written, total)
            pd.concat(dfs, ignore_index=True).to_csv(output_path, index=False)

        return output_path


def generate_dataset_cli(
    total: int = 5_000_000,
    attack_ratio: float = 0.8,
    output: str = "data/dataset.parquet",
    format: str = "parquet",
    seed: Optional[int] = 42,
) -> None:
    """CLI entry point for dataset generation."""
    gen = DatasetGenerator(
        total_samples=total,
        attack_ratio=attack_ratio,
        benign_ratio=1 - attack_ratio,
        random_seed=seed,
    )
    gen.generate(output_path=output, format=format)
