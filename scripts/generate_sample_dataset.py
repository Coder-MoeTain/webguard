#!/usr/bin/env python3
"""Generate a small sample dataset (10k) for quick testing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml_pipeline.dataset_generator import DatasetGenerator

if __name__ == "__main__":
    gen = DatasetGenerator(
        total_samples=10_000,
        attack_ratio=0.8,
        benign_ratio=0.2,
        random_seed=42,
        label_noise_ratio=0.04,
    )
    out = Path("data/sample_dataset.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    gen.generate(output_path=str(out), format="parquet")
    print(f"Generated {out}")
