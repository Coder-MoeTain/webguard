"""
WebGuard RF - Real-time IDS Engine
Analyzes HTTP requests using Random Forest model and generates alerts.
"""

import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from ..core.config import settings


@dataclass
class IDSAlert:
    id: str
    timestamp: float
    prediction: str
    confidence: float
    method: str
    url: str
    payload_preview: str
    source_ip: str
    severity: str  # low, medium, high, critical
    top_indicators: list
    # Multiclass diagnostics (runner-up + margin for analyst review)
    second_best: Optional[str] = None
    second_confidence: Optional[float] = None
    confidence_margin: Optional[float] = None
    uncertain: bool = False


_alert_store: list[IDSAlert] = []
_max_alerts = 1000
_stats = {"total_analyzed": 0, "attacks_detected": 0, "benign": 0}


def _get_severity(prediction: str, confidence: float) -> str:
    if prediction == "benign":
        return "info"
    if confidence >= 0.9:
        return "critical"
    if confidence >= 0.7:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def add_alert(
    prediction: str,
    confidence: float,
    method: str,
    url: str,
    payload_preview: str,
    source_ip: str = "unknown",
    top_indicators: Optional[list] = None,
    second_best: Optional[str] = None,
    second_confidence: Optional[float] = None,
    confidence_margin: Optional[float] = None,
    uncertain: bool = False,
) -> Optional[IDSAlert]:
    """Add alert when attack detected. Returns alert if attack, None if benign."""
    _stats["total_analyzed"] += 1
    pred_lower = (prediction or "").lower()
    if pred_lower == "benign":
        _stats["benign"] += 1
        return None

    _stats["attacks_detected"] += 1
    sev = _get_severity(prediction, confidence)
    if uncertain and prediction.lower() != "benign":
        # Downgrade visual severity when the model is split between classes
        if sev == "critical":
            sev = "medium"
        elif sev == "high":
            sev = "medium"
    alert = IDSAlert(
        id=f"alert_{int(time.time() * 1000)}_{len(_alert_store)}",
        timestamp=time.time(),
        prediction=prediction,
        confidence=confidence,
        method=method,
        url=url,
        payload_preview=payload_preview[:200] + ("..." if len(payload_preview) > 200 else ""),
        source_ip=source_ip,
        severity=sev,
        top_indicators=top_indicators or [],
        second_best=second_best,
        second_confidence=second_confidence,
        confidence_margin=confidence_margin,
        uncertain=uncertain,
    )
    _alert_store.append(alert)
    while len(_alert_store) > _max_alerts:
        _alert_store.pop(0)
    return alert


def get_alerts(limit: int = 50, since: Optional[float] = None) -> list[dict]:
    """Get recent alerts."""
    alerts = _alert_store
    if since:
        alerts = [a for a in alerts if a.timestamp >= since]
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp,
            "prediction": a.prediction,
            "confidence": a.confidence,
            "method": a.method,
            "url": a.url,
            "payload_preview": a.payload_preview,
            "source_ip": a.source_ip,
            "severity": a.severity,
            "top_indicators": a.top_indicators,
            "second_best": a.second_best,
            "second_confidence": a.second_confidence,
            "confidence_margin": a.confidence_margin,
            "uncertain": a.uncertain,
        }
        for a in reversed(alerts[-limit:])
    ]


def get_stats() -> dict:
    """Get IDS statistics."""
    return {
        **_stats,
        "alerts_count": len(_alert_store),
        "attack_rate": _stats["attacks_detected"] / max(1, _stats["total_analyzed"]),
    }


def clear_alerts():
    """Clear alert store (for testing)."""
    _alert_store.clear()
    _stats["total_analyzed"] = 0
    _stats["attacks_detected"] = 0
    _stats["benign"] = 0
