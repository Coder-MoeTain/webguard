# WebGuard RF - Production Upgrade Summary

## Analysis & Upgrades Applied

### Backend

| Area | Before | After |
|------|--------|-------|
| **Auth** | Hardcoded admin check | JWT deps ready (`get_current_user`), AuthProvider context |
| **Rate limiting** | None | In-memory rate limiter (100 req/min per IP) |
| **Error handling** | Unhandled exceptions | Global exception handler, structured logging |
| **Job persistence** | In-memory dict | JSON file store (`data/jobs.json`) survives restarts |
| **Inference** | Always used `hybrid` features | Uses model's stored `feature_mode` for consistency |
| **Training** | No `feature_mode` stored | Stores `feature_mode` in preprocessor for inference |
| **Datasets** | No list endpoint | `GET /api/datasets/` lists available files |
| **Training jobs** | No list | `GET /api/training/` lists jobs |
| **Reports** | Placeholder | HTML/Markdown export, preview endpoint |

### Frontend

| Area | Before | After |
|------|--------|-------|
| **Auth** | `localStorage` only | `AuthContext` + `useAuth`, centralized logout |
| **401 handling** | None | Axios interceptor redirects to login on 401 |
| **Dataset selection** | Manual path input | Dropdown from `GET /api/datasets/` |
| **Training config** | Manual path | Dataset dropdown |
| **Model evaluation** | Manual job ID | Job selector from completed jobs |
| **Inference** | Single model | Model selector when multiple models exist |
| **Report export** | Static text | Job selector, format picker, export + preview |
| **API timeout** | Default | 120s for long operations |

### ML Pipeline

| Area | Change |
|------|--------|
| **RandomForestTrainer** | Accepts `feature_mode`, persists in preprocessor |
| **Inference** | Reads `feature_mode` from preprocessor, uses matching extractor |

### New Files

- `backend/app/core/deps.py` - JWT auth dependencies
- `backend/app/core/rate_limit.py` - Rate limiter
- `backend/app/core/validation.py` - Path validation (path traversal)
- `backend/app/services/job_store.py` - Persistent job status
- `frontend/src/contexts/AuthContext.tsx` - Auth state management

### API Additions

- `GET /api/datasets/` - List datasets
- `GET /api/training/` - List training jobs
- `GET /api/reports/{job_id}/preview` - HTML report preview
- `POST /api/reports/export` - Export report (html/markdown)
