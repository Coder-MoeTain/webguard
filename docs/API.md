# WebGuard RF - API Reference

Base URL: `http://localhost:8001`

## Authentication

### POST /api/auth/login
Login and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "username": "admin",
  "role": "admin"
}
```

### POST /api/auth/register
Register new user.

---

## Datasets

### POST /api/datasets/generate
Start background dataset generation.

**Request:**
```json
{
  "total_samples": 5000000,
  "attack_ratio": 0.8,
  "output_format": "parquet",
  "random_seed": 42
}
```

### POST /api/datasets/upload
Upload CSV or Parquet file. Max 500MB.

**Request:** `multipart/form-data` with `file` field.

---

## Features

### POST /api/features/extract
Extract features from dataset.

**Request:**
```json
{
  "input_path": "data/dataset.parquet",
  "output_path": "data/features.parquet",
  "feature_mode": "payload_only",
  "format": "parquet"
}
```

---

## Training

### POST /api/training/start
Start training job.

**Request:**
```json
{
  "data_path": "data/features.parquet",
  "classification_mode": "multiclass",
  "feature_mode": "payload_only",
  "train_ratio": 0.7,
  "val_ratio": 0.15,
  "test_ratio": 0.15,
  "n_estimators": 200,
  "max_depth": 30,
  "min_samples_split": 2,
  "min_samples_leaf": 1,
  "max_features": "sqrt",
  "random_state": 42,
  "hyperparameter_tuning": false
}
```

### GET /api/training/{job_id}/status
Get training job status and metrics when complete.

---

## Models

### GET /api/models/
List all trained models.

### GET /api/models/{model_id}/download
Download model file.

---

## Inference

### POST /api/inference/predict
Predict class for a payload.

**Request:**
```json
{
  "url": "https://example.com/search",
  "body": "' OR 1=1--",
  "query_params": "' OR 1=1--",
  "request_method": "GET",
  "response_status": 200,
  "response_length": 1000,
  "response_time": 100.0,
  "model_id": null
}
```

**Response:**
```json
{
  "prediction": "sqli",
  "confidence": 0.95,
  "top_features": [
    {"name": "has_or_1_equals_1", "importance": 0.12},
    {"name": "quote_count", "importance": 0.08}
  ],
  "risk_explanation": "Classified as sqli with 95.0% confidence. Top indicators: has_or_1_equals_1, quote_count, has_select."
}
```

---

## Reports

### POST /api/reports/export
Export experiment report (HTML/PDF/Markdown).
