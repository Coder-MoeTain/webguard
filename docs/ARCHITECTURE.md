# WebGuard RF - System Architecture

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              WebGuard RF System                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ┌─────────────┐         ┌─────────────┐         ┌─────────────────────────┐   │
│   │   React     │  HTTP   │   FastAPI   │  Queue  │   Celery Workers        │   │
│   │  Dashboard  │◀───────▶│   Backend   │◀───────▶│   (ML Pipeline)         │   │
│   └─────────────┘         └──────┬──────┘         └───────────┬─────────────┘   │
│                                  │                             │                 │
│                                  │                             │                 │
│   ┌─────────────┐         ┌──────▼──────┐         ┌───────────▼─────────────┐   │
│   │   Redis     │         │   MySQL     │         │   File Storage          │   │
│   │   (Cache)   │         │   (Metadata)│         │   (Models, Datasets)     │   │
│   └─────────────┘         └─────────────┘         └─────────────────────────┘   │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## ML Workflow Diagram

```
Dataset Generation          Feature Extraction         Training
┌─────────────────┐        ┌─────────────────┐       ┌─────────────────┐
│ SQLi Payloads   │        │ Lexical         │       │ Stratified      │
│ XSS Payloads    │───────▶│ Structural      │──────▶│ Split           │
│ CSRF Patterns   │        │ Behavioral      │       │ 70/15/15        │
│ Benign Samples  │        │ Contextual      │       └────────┬────────┘
└─────────────────┘        └─────────────────┘                │
                                                               ▼
Evaluation                  Model Storage              ┌─────────────────┐
┌─────────────────┐        ┌─────────────────┐       │ Random Forest   │
│ Confusion Matrix│◀───────│ joblib/pickle   │◀──────│ n_estimators    │
│ ROC-AUC         │        │ Preprocessing   │       │ max_depth       │
│ Feature Import  │        └─────────────────┘       └─────────────────┘
└─────────────────┘
```

## Dataset Generation Flow

```
                    ┌──────────────────┐
                    │  Start Generation │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  SQLi    │  │   XSS    │  │  CSRF    │
        │  (33.3%) │  │  (33.3%) │  │  (33.3%) │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                          ▼
                    ┌──────────┐
                    │  Benign  │
                    │  (20%)   │
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
                    │  HTTP    │
                    │  Simulate│
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
                    │ CSV/     │
                    │ Parquet  │
                    └──────────┘
```

## Feature Engineering Table

| Category | Feature | Description |
|----------|---------|-------------|
| SQLi | has_select | Boolean: contains SELECT keyword |
| SQLi | has_union | Boolean: contains UNION |
| SQLi | has_sleep | Boolean: contains SLEEP/BENCHMARK |
| SQLi | has_or_1_equals_1 | Boolean: OR 1=1 pattern |
| SQLi | quote_count | Count of single/double quotes |
| SQLi | comment_marker_count | Count of --, #, /* */ |
| SQLi | semicolon_count | Count of semicolons |
| XSS | has_script_tag | Boolean: <script> present |
| XSS | has_javascript_protocol | Boolean: javascript: |
| XSS | has_onerror | Boolean: onerror handler |
| XSS | has_onload | Boolean: onload handler |
| XSS | angle_bracket_count | Count of < > |
| CSRF | missing_csrf_token | Boolean: no CSRF token |
| CSRF | cross_origin_flag | Boolean: cross-origin |
| CSRF | missing_referer | Boolean: no Referer |
| Common | payload_length | Integer length |
| Common | special_char_ratio | Ratio 0-1 |
| Common | entropy | Shannon entropy |

## API Design

### Authentication
- JWT-based with refresh tokens
- Role-based: admin, researcher, viewer

### Rate Limiting
- 100 requests/minute per user
- 10 concurrent training jobs per user

### Pagination
- Default: 20 items per page
- Max: 100 items per page
