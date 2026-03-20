"""
WebGuard RF - Feature Extractor
Extract tabular features for Random Forest from raw records.
"""

from pathlib import Path
from typing import Optional, List, Literal, Callable

import pandas as pd
from tqdm import tqdm

from .features import (
    FEATURE_GROUPS,
    SQLI_37_FEATURES,
    extract_sqli_features,
    extract_sqli_37_features,
    extract_xss_features,
    extract_csrf_features,
    extract_common_features,
    extract_response_features,
)


class FeatureExtractor:
    """Extract security-relevant features from dataset records."""

    def __init__(
        self,
        feature_mode: Literal["payload_only", "response_only", "hybrid", "sqli_37"] = "payload_only",
    ):
        self.feature_mode = feature_mode
        if feature_mode == "sqli_37":
            # In sqli_37 mode we still want a full payload feature set
            # (SQLi + XSS + CSRF + common indicators), not only the 37 SQLi features.
            payload_cols = FEATURE_GROUPS["payload_only"]
            self.feature_columns = list(dict.fromkeys(SQLI_37_FEATURES + payload_cols))
        else:
            payload_cols = FEATURE_GROUPS["payload_only"]
            response_cols = FEATURE_GROUPS["response_only"]
            if feature_mode == "payload_only":
                self.feature_columns = payload_cols
            elif feature_mode == "response_only":
                self.feature_columns = response_cols
            else:
                self.feature_columns = payload_cols + response_cols

    def extract_single(self, row: dict) -> dict:
        """Extract features from a single record."""
        payload = str(row.get("payload", ""))
        record = {k: row.get(k) for k in row}

        features = {}
        if self.feature_mode == "sqli_37":
            features.update(extract_sqli_37_features(payload))
            features.update(extract_xss_features(payload))
            features.update(extract_csrf_features(payload, record))
            features.update(extract_common_features(payload, record))
        else:
            features.update(extract_sqli_features(payload))
            features.update(extract_xss_features(payload))
            features.update(extract_csrf_features(payload, record))
            features.update(extract_common_features(payload, record))

        if self.feature_mode in ("response_only", "hybrid"):
            features.update(extract_response_features(record))

        return {k: features[k] for k in self.feature_columns if k in features}

    def extract_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from a DataFrame."""
        rows = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Extracting features"):
            feat = self.extract_single(row.to_dict())
            feat["label"] = row.get("label", "benign")
            rows.append(feat)
        return pd.DataFrame(rows)

    def extract_file(
        self,
        input_path: str,
        output_path: str,
        format: str = "parquet",
        chunk_size: int = 50_000,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Extract features from file with chunked processing. Input must have a 'payload' column."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        first = True

        if input_path.endswith(".parquet"):
            import pyarrow.parquet as pq
            table = pq.read_table(input_path)
            # Validate: raw dataset must have 'payload' column (feature files don't)
            cols = table.column_names
            if "payload" not in cols:
                raise ValueError(
                    "Input file must be a raw dataset with a 'payload' column. "
                    "Feature files (has_select, has_union, etc.) cannot be re-extracted. "
                    "Use sample_dataset.parquet or similar raw data."
                )
            total_rows = table.num_rows
            for i in tqdm(range(0, total_rows, chunk_size), desc="Chunks"):
                chunk_table = table.slice(i, min(chunk_size, total_rows - i))
                chunk = chunk_table.to_pandas()
                feat_df = self.extract_dataframe(chunk)
                if progress_callback:
                    written = min(i + len(chunk), total_rows)
                    progress_callback(written, total_rows)
                if first:
                    feat_df.to_parquet(output_path, index=False) if format == "parquet" else feat_df.to_csv(output_path, index=False)
                    first = False
                else:
                    existing = pd.read_parquet(output_path) if format == "parquet" else pd.read_csv(output_path)
                    combined = pd.concat([existing, feat_df], ignore_index=True)
                    (combined.to_parquet(output_path, index=False) if format == "parquet" else combined.to_csv(output_path, index=False))
        else:
            first_chunk = True
            total_rows = 0
            # Best-effort line counting for progress percent (used for CSV).
            try:
                with open(input_path, "rb") as f:
                    total_rows = sum(1 for _ in f) - 1  # subtract header line
                total_rows = max(0, total_rows)
            except Exception:
                total_rows = 0
            written_rows = 0
            for chunk in pd.read_csv(input_path, chunksize=chunk_size):
                if first_chunk and "payload" not in chunk.columns:
                    raise ValueError(
                        "Input file must be a raw dataset with a 'payload' column. "
                        "Use sample_dataset.parquet or similar raw data."
                    )
                first_chunk = False
                feat_df = self.extract_dataframe(chunk)
                if progress_callback:
                    written_rows += len(chunk)
                    progress_callback(written_rows, total_rows)
                if first:
                    feat_df.to_parquet(output_path, index=False) if format == "parquet" else feat_df.to_csv(output_path, index=False)
                    first = False
                else:
                    existing = pd.read_parquet(output_path) if format == "parquet" else pd.read_csv(output_path)
                    combined = pd.concat([existing, feat_df], ignore_index=True)
                    (combined.to_parquet(output_path, index=False) if format == "parquet" else combined.to_csv(output_path, index=False))

        return output_path
