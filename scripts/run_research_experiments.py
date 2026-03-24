#!/usr/bin/env python3
"""
Run multi-seed training plus optional calibration / ablation / evasion metrics for papers.
Example: python scripts/run_research_experiments.py --config configs/research.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _resolve(root: Path, p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (root / path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Research experiment runner")
    parser.add_argument(
        "--config",
        default=str(ROOT / "configs" / "research.yaml"),
        help="Path to research YAML config",
    )
    args = parser.parse_args()

    from ml_pipeline.research.config import load_research_config
    from ml_pipeline.research.external_dataset import load_raw_table, validate_raw_research_dataset
    from ml_pipeline.research.evasion import run_evasion_battery
    from ml_pipeline.feature_extraction import FeatureExtractor
    from ml_pipeline.training import RandomForestTrainer, ALGORITHMS

    cfg = load_research_config(args.config)
    fe_cfg = cfg["feature_extraction"]
    tr_cfg = cfg["training"]
    ev_cfg = cfg["evasion"]

    if fe_cfg.get("enabled"):
        raw_p = _resolve(ROOT, fe_cfg["raw_path"])
        out_p = _resolve(ROOT, fe_cfg["output_path"])
        if not raw_p.exists():
            print(f"Missing raw data for feature extraction: {raw_p}", file=sys.stderr)
            return 1
        validate_raw_research_dataset(load_raw_table(raw_p))
        print(f"Extracting features: {raw_p} -> {out_p}")
        ext = FeatureExtractor(feature_mode=fe_cfg.get("feature_mode", "payload_only"))
        ext.extract_file(str(raw_p), str(out_p), format="parquet")
        data_path = out_p
    else:
        data_path = _resolve(ROOT, cfg["featured_data_path"])

    if not data_path.exists():
        print(
            f"Featured dataset not found: {data_path}. "
            "Enable feature_extraction in the config or run scripts/quick_train.py first.",
            file=sys.stderr,
        )
        return 1

    out_dir = _resolve(ROOT, tr_cfg.get("output_dir", "models/research"))
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir = _resolve(ROOT, cfg.get("report_dir", "data/research_reports"))
    report_dir.mkdir(parents=True, exist_ok=True)

    algorithms = tr_cfg.get("algorithms") or ["random_forest"]
    for a in algorithms:
        if a not in ALGORITHMS:
            print(f"Unknown algorithm '{a}'. Choose from: {ALGORITHMS}", file=sys.stderr)
            return 1

    seeds = tr_cfg.get("seeds") or [42]
    last_only = tr_cfg.get("extended_research_on_last_seed_only", True)
    bootstrap_n = int(tr_cfg.get("bootstrap_resamples", 500))

    report: dict = {
        "config_path": str(Path(args.config).resolve()),
        "data_path": str(data_path.resolve()),
        "runs": [],
    }

    for algo in algorithms:
        run_entry: dict = {"algorithm": algo, "seeds": []}
        last_metrics = None
        for i, seed in enumerate(seeds):
            extended = bool(tr_cfg.get("extended_research_metrics", True))
            if last_only:
                extended = extended and (i == len(seeds) - 1)
            print(f"Training algorithm={algo} seed={seed} extended_research={extended}")
            trainer = RandomForestTrainer(
                algorithm=algo,
                classification_mode=tr_cfg.get("classification_mode", "multiclass"),
                feature_mode=tr_cfg.get("feature_mode", "payload_only"),
                n_estimators=int(tr_cfg.get("n_estimators", 200)),
                max_depth=tr_cfg.get("max_depth"),
                random_state=int(seed),
            )
            try:
                metrics = trainer.train(
                    str(data_path),
                    output_dir=str(out_dir),
                    extended_research_metrics=extended,
                    bootstrap_resamples=bootstrap_n,
                )
            except RuntimeError as e:
                run_entry["seeds"].append({"seed": seed, "error": str(e)})
                print(f"  failed: {e}", file=sys.stderr)
                continue

            test = metrics.get("test", {})
            run_entry["seeds"].append(
                {
                    "seed": seed,
                    "test_f1_macro": test.get("f1_macro"),
                    "test_accuracy": test.get("accuracy"),
                    "model_id": metrics.get("model_id"),
                    "research": metrics.get("research"),
                }
            )
            last_metrics = metrics

        if last_metrics and ev_cfg.get("enabled"):
            raw_path = _resolve(ROOT, cfg.get("raw_data_path", ""))
            if raw_path.exists():
                import joblib

                model_path = Path(last_metrics["model_path"])
                prep_path = Path(last_metrics["preprocessor_path"])
                model = joblib.load(model_path)
                prep_blob = joblib.load(prep_path)
                cols = prep_blob.get("feature_columns", [])
                fmode = prep_blob.get("feature_mode", tr_cfg.get("feature_mode", "payload_only"))
                raw_df = load_raw_table(raw_path)
                validate_raw_research_dataset(raw_df)
                ev = run_evasion_battery(
                    raw_df,
                    model,
                    cols,
                    fmode,
                    transform_names=ev_cfg.get("transforms"),
                    n_samples=int(ev_cfg.get("n_samples", 300)),
                    random_state=int(seeds[-1]),
                )
                run_entry["evasion"] = ev
            else:
                run_entry["evasion"] = {"skipped": True, "reason": f"raw_data_path missing: {raw_path}"}

        report["runs"].append(run_entry)

    # Aggregate multi-seed summary for the last algorithm block
    for run in report["runs"]:
        f1s = [s["test_f1_macro"] for s in run["seeds"] if "test_f1_macro" in s]
        if f1s:
            import statistics

            run["summary"] = {
                "test_f1_macro_mean": float(statistics.mean(f1s)),
                "test_f1_macro_stdev": float(statistics.pstdev(f1s)) if len(f1s) > 1 else 0.0,
                "n_seeds_ok": len(f1s),
            }

    out_file = report_dir / f"research_report_{int(time.time())}.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
