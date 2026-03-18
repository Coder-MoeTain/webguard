#!/usr/bin/env python3
"""Quick training on sample dataset."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml_pipeline.feature_extraction import FeatureExtractor
from ml_pipeline.training import RandomForestTrainer

if __name__ == "__main__":
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    raw_path = data_dir / "sample_dataset.parquet"
    feat_path = data_dir / "sample_features.parquet"

    if not raw_path.exists():
        print("Run generate_sample_dataset.py first")
        sys.exit(1)

    print("Extracting features...")
    ext = FeatureExtractor(feature_mode="payload_only")
    ext.extract_file(str(raw_path), str(feat_path), format="parquet")

    print("Training...")
    trainer = RandomForestTrainer(n_estimators=50, max_depth=15)
    metrics = trainer.train(str(feat_path), output_dir="models")
    print("Metrics:", metrics.get("test", {}))
