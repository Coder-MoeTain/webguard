"""
WebGuard RF - Feature Definitions
Lexical, structural, behavioral, and contextual features.
"""

import re
import math
from typing import Dict, Any, List, Optional, Literal

# 37 SQL Injection features for sqli_37 mode (defined first for FEATURE_GROUPS)
SQLI_37_FEATURES = [
    "has_select", "has_union", "has_sleep", "has_or_1_equals_1", "has_drop",
    "has_insert", "has_delete", "has_update", "has_information_schema",
    "has_where", "has_order_by", "has_group_by", "has_having", "has_like",
    "has_in", "has_hex", "has_char", "has_concat", "has_ascii", "has_substring",
    "has_count", "has_benchmark", "has_waitfor", "has_exec", "has_xp_cmdshell",
    "quote_count", "comment_marker_count", "semicolon_count", "equals_count",
    "parentheses_count", "keyword_density", "sqli_entropy", "payload_length",
    "special_char_ratio", "encoded_char_ratio", "logical_op_count", "comparison_count",
]

# Feature groups for payload-only, response-only, hybrid, sqli_37
FEATURE_GROUPS = {
    "sqli_37": SQLI_37_FEATURES,
    "payload_only": [
        "has_select", "has_union", "has_sleep", "has_or_1_equals_1", "has_drop",
        "has_insert", "has_delete", "has_update", "has_information_schema",
        "quote_count", "comment_marker_count", "semicolon_count", "equals_count",
        "parentheses_count", "keyword_density", "sqli_entropy",
        "has_script_tag", "has_javascript_protocol", "has_onerror", "has_onload",
        "has_alert", "has_document_write", "has_eval", "html_tag_count",
        "angle_bracket_count", "encoded_js_pattern", "suspicious_dom_keywords",
        "svg_script_count",
        "missing_csrf_token", "invalid_csrf_token", "cross_origin_flag",
        "missing_referer", "state_change_request", "suspicious_cookie_usage",
        "same_site_violation",
        "request_method_get", "request_method_post", "payload_length",
        "url_length", "number_count", "special_char_ratio", "encoded_char_ratio",
        "whitespace_ratio", "has_cookies", "has_referer",
    ],
    "response_only": [
        "status_code", "response_length", "response_time", "error_flag",
        "redirection_flag",
    ],
    "hybrid": None,  # payload_only + response_only
}

# Research ablation: semantic groups (subset of columns present in payload / hybrid modes).
ABLATION_GROUPS_PAYLOAD: Dict[str, List[str]] = {
    "sqli": [
        "has_select", "has_union", "has_sleep", "has_or_1_equals_1", "has_drop",
        "has_insert", "has_delete", "has_update", "has_information_schema",
        "quote_count", "comment_marker_count", "semicolon_count", "equals_count",
        "parentheses_count", "keyword_density", "sqli_entropy",
    ],
    "xss": [
        "has_script_tag", "has_javascript_protocol", "has_onerror", "has_onload",
        "has_alert", "has_document_write", "has_eval", "html_tag_count",
        "angle_bracket_count", "encoded_js_pattern", "suspicious_dom_keywords",
        "svg_script_count",
    ],
    "csrf": [
        "missing_csrf_token", "invalid_csrf_token", "cross_origin_flag",
        "missing_referer", "state_change_request", "suspicious_cookie_usage",
        "same_site_violation",
    ],
    "common": [
        "request_method_get", "request_method_post", "payload_length",
        "url_length", "number_count", "special_char_ratio", "encoded_char_ratio",
        "whitespace_ratio", "has_cookies", "has_referer",
    ],
}

ABLATION_GROUPS_SQLI_37: Dict[str, List[str]] = {
    "sql_keywords": [
        "has_select", "has_union", "has_sleep", "has_or_1_equals_1", "has_drop",
        "has_insert", "has_delete", "has_update", "has_information_schema",
        "has_where", "has_order_by", "has_group_by", "has_having", "has_like",
        "has_in", "has_hex", "has_char", "has_concat", "has_ascii", "has_substring",
        "has_count", "has_benchmark", "has_waitfor", "has_exec", "has_xp_cmdshell",
    ],
    "structural": [
        "quote_count", "comment_marker_count", "semicolon_count", "equals_count",
        "parentheses_count",
    ],
    "lexical": [
        "keyword_density", "sqli_entropy", "payload_length", "special_char_ratio",
        "encoded_char_ratio", "logical_op_count", "comparison_count",
    ],
}

ABLATION_GROUPS_RESPONSE: Dict[str, List[str]] = {
    "response": list(FEATURE_GROUPS["response_only"]),
}


def ablation_groups_for_mode(
    feature_mode: Literal["payload_only", "response_only", "hybrid", "sqli_37"],
    feature_columns: List[str],
) -> Dict[str, List[str]]:
    """Map semantic group names to columns that exist in the trained feature matrix."""
    cols = set(feature_columns)
    if feature_mode == "sqli_37":
        base = ABLATION_GROUPS_SQLI_37.copy()
        for k in ("xss", "csrf", "common"):
            base[k] = [c for c in ABLATION_GROUPS_PAYLOAD[k] if c in cols]
    elif feature_mode == "response_only":
        base = {k: [c for c in v if c in cols] for k, v in ABLATION_GROUPS_RESPONSE.items()}
    elif feature_mode == "hybrid":
        base = {}
        for name, feats in ABLATION_GROUPS_PAYLOAD.items():
            base[name] = [f for f in feats if f in cols]
        base["response"] = [f for f in ABLATION_GROUPS_RESPONSE["response"] if f in cols]
    else:
        base = {k: [f for f in v if f in cols] for k, v in ABLATION_GROUPS_PAYLOAD.items()}
    return {k: v for k, v in base.items() if v}


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0)


def extract_sqli_37_features(payload: str) -> Dict[str, Any]:
    """Extract 37 SQL injection features for dedicated SQLi detection."""
    p = payload.lower()
    keywords = ["select", "union", "sleep", "benchmark", "waitfor", "drop", "insert", "delete", "update", "information_schema", "where", "order", "group", "having", "like", "in"]
    keyword_count = sum(1 for k in keywords if k in p)
    n_special = sum(1 for c in payload if not c.isalnum() and not c.isspace())
    n_encoded = payload.count("%") + len(re.findall(r"&#\d+;", payload)) + len(re.findall(r"\\x[0-9a-fA-F]{2}", payload))
    logical_ops = len(re.findall(r"\b(and|or|not)\b", p))
    comparison_ops = payload.count("=") + payload.count("<") + payload.count(">") + payload.count("!")
    return {
        "has_select": 1 if "select" in p else 0,
        "has_union": 1 if "union" in p else 0,
        "has_sleep": 1 if "sleep" in p else 0,
        "has_or_1_equals_1": 1 if re.search(r"or\s+1\s*=\s*1", p) else 0,
        "has_drop": 1 if "drop" in p else 0,
        "has_insert": 1 if "insert" in p else 0,
        "has_delete": 1 if "delete" in p else 0,
        "has_update": 1 if "update" in p else 0,
        "has_information_schema": 1 if "information_schema" in p else 0,
        "has_where": 1 if "where" in p else 0,
        "has_order_by": 1 if "order" in p and "by" in p else 0,
        "has_group_by": 1 if "group" in p and "by" in p else 0,
        "has_having": 1 if "having" in p else 0,
        "has_like": 1 if "like" in p else 0,
        "has_in": 1 if re.search(r"\bin\b", p) else 0,
        "has_hex": 1 if "0x" in p or "hex(" in p else 0,
        "has_char": 1 if "char(" in p or "chr(" in p else 0,
        "has_concat": 1 if "concat" in p or "||" in payload else 0,
        "has_ascii": 1 if "ascii" in p else 0,
        "has_substring": 1 if "substring" in p or "substr" in p else 0,
        "has_count": 1 if "count(" in p else 0,
        "has_benchmark": 1 if "benchmark" in p else 0,
        "has_waitfor": 1 if "waitfor" in p else 0,
        "has_exec": 1 if "exec" in p or "execute" in p else 0,
        "has_xp_cmdshell": 1 if "xp_cmdshell" in p else 0,
        "quote_count": payload.count("'") + payload.count('"'),
        "comment_marker_count": payload.count("--") + payload.count("#") + payload.count("/*") + payload.count("*/"),
        "semicolon_count": payload.count(";"),
        "equals_count": payload.count("="),
        "parentheses_count": payload.count("(") + payload.count(")"),
        "keyword_density": keyword_count / max(len(payload), 1),
        "sqli_entropy": _entropy(payload),
        "payload_length": len(payload),
        "special_char_ratio": n_special / max(len(payload), 1),
        "encoded_char_ratio": n_encoded / max(len(payload), 1),
        "logical_op_count": logical_ops,
        "comparison_count": comparison_ops,
    }


def extract_sqli_features(payload: str) -> Dict[str, Any]:
    """Extract SQL injection related features (for combined payload_only mode)."""
    p = payload.lower()
    keywords = ["select", "union", "sleep", "benchmark", "waitfor", "drop", "insert", "delete", "update", "information_schema"]
    keyword_count = sum(1 for k in keywords if k in p)
    return {
        "has_select": 1 if "select" in p else 0,
        "has_union": 1 if "union" in p else 0,
        "has_sleep": 1 if any(x in p for x in ["sleep", "benchmark", "waitfor"]) else 0,
        "has_or_1_equals_1": 1 if re.search(r"or\s+1\s*=\s*1", p) else 0,
        "has_drop": 1 if "drop" in p else 0,
        "has_insert": 1 if "insert" in p else 0,
        "has_delete": 1 if "delete" in p else 0,
        "has_update": 1 if "update" in p else 0,
        "has_information_schema": 1 if "information_schema" in p else 0,
        "quote_count": payload.count("'") + payload.count('"'),
        "comment_marker_count": payload.count("--") + payload.count("#") + payload.count("/*") + payload.count("*/"),
        "semicolon_count": payload.count(";"),
        "equals_count": payload.count("="),
        "parentheses_count": payload.count("(") + payload.count(")"),
        "keyword_density": keyword_count / max(len(payload), 1),
        "sqli_entropy": _entropy(payload),
    }


def extract_xss_features(payload: str) -> Dict[str, Any]:
    """Extract XSS related features."""
    p = payload.lower()
    return {
        "has_script_tag": 1 if "<script" in p else 0,
        "has_javascript_protocol": 1 if "javascript:" in p else 0,
        "has_onerror": 1 if "onerror" in p else 0,
        "has_onload": 1 if "onload" in p else 0,
        "has_alert": 1 if "alert(" in p else 0,
        "has_document_write": 1 if "document.write" in p else 0,
        "has_eval": 1 if "eval(" in p else 0,
        "html_tag_count": len(re.findall(r"<[^>]+>", payload)),
        "angle_bracket_count": payload.count("<") + payload.count(">"),
        "encoded_js_pattern": 1 if re.search(r"%3[cC]|&#60;|\\x3c", payload) else 0,
        "suspicious_dom_keywords": sum(1 for k in ["document", "window", "location", "cookie"] if k in p),
        "svg_script_count": 1 if "<svg" in p and ("script" in p or "onbegin" in p) else 0,
    }


def extract_csrf_features(payload: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract CSRF related features from payload and request metadata."""
    p = payload.lower()
    token_patterns = ["csrf", "token", "x-csrf", "_token", "authenticity_token"]
    has_token_mention = any(t in p for t in token_patterns)
    return {
        "missing_csrf_token": 1 if not record.get("token_present", False) else 0,
        "invalid_csrf_token": 1 if has_token_mention and not record.get("token_present") else 0,
        "cross_origin_flag": 1 if "origin" in p or "evil" in p or "referer" in p else 0,
        "missing_referer": 1 if not record.get("referrer_present", False) else 0,
        "state_change_request": 1 if record.get("request_method", "").upper() in ("POST", "PUT", "DELETE", "PATCH") else 0,
        "suspicious_cookie_usage": 1 if record.get("cookies_present") and not record.get("token_present") else 0,
        "same_site_violation": 1 if "cross" in p or "origin" in p else 0,
    }


def extract_common_features(payload: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract common/contextual features."""
    method = str(record.get("request_method", "GET")).upper()
    url = str(record.get("url", ""))
    n_digits = sum(1 for c in payload if c.isdigit())
    n_special = sum(1 for c in payload if not c.isalnum() and not c.isspace())
    n_encoded = payload.count("%") + len(re.findall(r"&#\d+;", payload))
    n_ws = sum(1 for c in payload if c.isspace())
    return {
        "request_method_get": 1 if method == "GET" else 0,
        "request_method_post": 1 if method == "POST" else 0,
        "payload_length": len(payload),
        "url_length": len(url),
        "number_count": n_digits,
        "special_char_ratio": n_special / max(len(payload), 1),
        "encoded_char_ratio": n_encoded / max(len(payload), 1),
        "whitespace_ratio": n_ws / max(len(payload), 1),
        "has_cookies": 1 if record.get("cookies_present") else 0,
        "has_referer": 1 if record.get("referrer_present") else 0,
    }


def extract_response_features(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract response-only features."""
    return {
        "status_code": int(record.get("response_status", 200)),
        "response_length": int(record.get("response_length", 0)),
        "response_time": float(record.get("response_time", 0)),
        "error_flag": 1 if record.get("error_flag") else 0,
        "redirection_flag": 1 if record.get("redirection_flag") else 0,
    }
