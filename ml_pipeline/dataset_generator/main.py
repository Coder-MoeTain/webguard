"""
WebGuard RF - Dataset Generator CLI
Usage: python -m ml_pipeline.dataset_generator.main --total 5000000 --attack-ratio 0.8
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="WebGuard RF Dataset Generator")
    parser.add_argument("--total", type=int, default=5_000_000, help="Total samples")
    parser.add_argument("--attack-ratio", type=float, default=0.8, help="Attack ratio (0-1)")
    parser.add_argument("--output", type=str, default="data/dataset.parquet", help="Output path")
    parser.add_argument("--format", choices=["csv", "parquet"], default="parquet")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    from .generator import DatasetGenerator

    gen = DatasetGenerator(
        total_samples=args.total,
        attack_ratio=args.attack_ratio,
        benign_ratio=1 - args.attack_ratio,
        random_seed=args.seed,
    )
    gen.generate(output_path=args.output, format=args.format)
    print(f"Dataset saved to {args.output}")


if __name__ == "__main__":
    main()
