# WebGuard RF - Example Research Report

## Experiment Summary

**Date:** 2024-03-18  
**Model:** Random Forest (payload-only)  
**Dataset:** 5,000,000 samples (80% attack, 20% benign)

## Configuration

| Parameter | Value |
|-----------|-------|
| n_estimators | 200 |
| max_depth | 30 |
| train/val/test | 70/15/15 |
| feature_mode | payload_only |

## Results

### Test Set Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 0.9823 |
| Precision (macro) | 0.9812 |
| Recall (macro) | 0.9801 |
| F1 (macro) | 0.9805 |
| F1 (weighted) | 0.9822 |
| ROC-AUC | 0.9987 |

### Per-Class Performance

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| benign | 0.9912 | 0.9856 | 0.9884 |
| sqli | 0.9823 | 0.9812 | 0.9817 |
| xss | 0.9756 | 0.9723 | 0.9739 |
| csrf | 0.9756 | 0.9812 | 0.9784 |

### Confusion Matrix

```
              benign   sqli    xss   csrf
benign        9856     42     58     44
sqli            38   9812     82     68
xss             52     95   9723    130
csrf            41     71    108   9780
```

### Top 10 Feature Importance

1. has_script_tag (0.118)
2. has_union (0.092)
3. angle_bracket_count (0.081)
4. payload_length (0.067)
5. has_select (0.061)
6. quote_count (0.055)
7. special_char_ratio (0.048)
8. has_onerror (0.042)
9. has_or_1_equals_1 (0.038)
10. semicolon_count (0.035)

## Conclusion

The payload-only Random Forest achieves strong multi-class detection with 98.2% accuracy. Hybrid mode (payload + response) may improve CSRF detection. Future work: XGBoost, Isolation Forest.
