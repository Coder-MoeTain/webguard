<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">WebGuard RF</h1>
<p align="center">
  <strong>Machine Learning Driven Detection of SQLi, XSS, and CSRF</strong>
</p>
<p align="center">
  A production-style research framework for detecting web application attacks using Random Forest classification.
</p>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Dashboard](#dashboard)
- [Configuration](#configuration)
- [Testing](#testing)
- [Git Ignore](#git-ignore)
- [License](#license)

---

## Overview

WebGuard RF is an end-to-end ML-based web attack detection system for academic cybersecurity research and practical deployment. It generates or ingests up to 5 million samples, extracts security-relevant features, trains Random Forest models, and provides a modern web dashboard for experiment management and live payload testing.

---

## Features

| Feature | Description |
|---------|-------------|
| **Real-time IDS** | Live intrusion detection dashboard with Random Forest model |
| **Multi-class & Binary** | SQLi, XSS, CSRF, Benign (or Attack vs Benign) |
| **5M Sample Dataset** | 80% attack, 20% benign with configurable sub-distribution |
| **Rich Feature Engineering** | Lexical, structural, behavioral, contextual features |
| **Payload-Only & Hybrid** | Detect from payload alone or payload + response behavior |
| **Research-Grade Metrics** | Confusion matrix, ROC-AUC, per-class metrics, feature importance |
| **Robustness Analysis** | Feature ablation, zero-out sensitivity, OOD testing |
| **Live Inference** | Test payloads with confidence scores and explanations |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WebGuard RF Architecture                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐                  │
│  │   Dataset   │───▶│   Feature    │───▶│  Preprocessing  │                  │
│  │  Generator  │    │  Extraction  │    │  & Split        │                  │
│  └─────────────┘    └──────────────┘    └────────┬────────┘                  │
│         │                    │                    │                           │
│         ▼                    ▼                    ▼                           │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐                    │
│  │  CSV/Parquet│    │  Tabular     │    │  Random Forest  │                    │
│  │  Storage    │    │  Features    │    │  Training      │                    │
│  └─────────────┘    └──────────────┘    └────────┬────────┘                    │
│                                                   │                           │
│         ┌─────────────────────────────────────────┘                           │
│         ▼                                                                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Evaluation    │    │  Model Storage  │    │  Live Inference │           │
│  │   & Metrics     │    │  (joblib)       │    │  API            │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **MySQL** 8.0+ or PostgreSQL 14+ (optional)
- **Redis** (optional, for Celery)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd "Random Forest-Sqli"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
# 1. Configure environment (optional)
cp .env.example .env
# Edit .env for database, CORS origins, etc.

# 2. Start backend (port 8001)
python run_backend.py

# 3. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** (or the port Vite shows) and log in with `admin` / `admin123`.

### Docker

```bash
docker-compose up -d
```

Then initialize the database (first run only):

```bash
docker compose exec mysql mysql -uwebguard -pwebguard webguard_rf < database/schema.sql
docker compose exec backend python scripts/init_db.py
```

---

## Project Structure

```
webguard-rf/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/             # API routes (auth, datasets, training, etc.)
│   │   ├── core/            # Config, security, validation
│   │   ├── db/              # Database models
│   │   └── services/        # Business logic
│   └── requirements.txt
├── frontend/                # React + Vite dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── ml_pipeline/             # Standalone ML modules
│   ├── dataset_generator/
│   ├── feature_extraction/
│   └── training/
├── database/                # SQL schema
├── data/                    # Datasets (gitignored)
├── models/                  # Trained models (gitignored)
├── .env.example             # Environment template
├── .gitignore
├── docker-compose.yml
├── run_backend.py
└── requirements.txt
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User registration |
| POST | `/api/datasets/generate` | Start dataset generation |
| POST | `/api/datasets/upload` | Upload dataset |
| POST | `/api/features/extract` | Extract features from dataset |
| POST | `/api/training/start` | Start training job |
| GET | `/api/training/{job_id}/status` | Get training status |
| GET | `/api/models/` | List trained models |
| POST | `/api/inference/predict` | Live payload prediction |
| POST | `/api/ids/analyze` | IDS: Analyze request |
| GET | `/api/ids/alerts` | IDS: List alerts |
| POST | `/api/reports/export` | Export experiment report |

> All endpoints except `/health` and `/api/auth/*` require `Authorization: Bearer <token>`.

---

## Dashboard

| Page | Description |
|------|-------------|
| **Dashboard** | Overview, stats, recent jobs |
| **Dataset Generation** | Configure and run 5M sample generation |
| **Dataset Upload** | Upload CSV/Parquet |
| **Dataset Browser** | Browse, preview, manage datasets |
| **Feature Extraction** | Extract features (payload-only, hybrid, etc.) |
| **Training Config** | Set RF params, start training |
| **Training Monitor** | Live training progress |
| **Inference Testing** | Live payload testing |
| **Model Management** | List, download models |
| **Robustness Analysis** | Feature ablation, sensitivity |
| **IDS Dashboard** | Real-time intrusion detection |

---

## Configuration

Key environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | `change-me-in-production` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000,...` |
| `DB_HOST` | MySQL host | `localhost` |
| `DB_NAME` | Database name | `webguard_rf` |
| `DATA_DIR` | Dataset storage path | `./data` |
| `MODELS_DIR` | Model storage path | `./models` |

---

## Testing

```bash
# Run pytest
pytest tests/ -v

# API smoke test (requires backend running)
python scripts/test_api.py
```

---

## Git Ignore

The project uses a comprehensive `.gitignore` to exclude:

- **Environment files** – `.env`, `venv/`, `.venv/`
- **Python artifacts** – `__pycache__/`, `*.pyc`, `*.egg-info/`
- **Node** – `node_modules/`, `npm-debug.log*`
- **Data & models** – `data/*.parquet`, `data/*.csv`, `models/*.joblib` (large files)
- **IDE** – `.idea/`, `.vscode/`
- **Logs** – `logs/`, `*.log`
- **Build** – `frontend/dist/`, `.pytest_cache/`

See [`.gitignore`](.gitignore) for the full list.

---

## License

MIT License — Research and educational use.
#   w e b g u a r d  
 