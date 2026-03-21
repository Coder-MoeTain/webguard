"""
Defaults for HTTP context flags used in feature extraction.

Training data (``simulate_http_record``) randomizes cookies/token/referrer per row.
The IDS dashboard and many API calls omit ``headers`` entirely, which previously
forced ``token_present=False`` on every request → ``missing_csrf_token=1`` and
``missing_referer=1`` always, biasing multiclass models toward ``csrf`` regardless
of payload. When headers are absent, use neutral defaults aligned with typical
non-CSRF rows (token often present for sqli/xss/benign in the generator).
"""

from typing import Any, Dict, Literal, Optional


def request_context_flags(headers: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """
    Return cookies_present, token_present, referrer_present for ``extract_csrf_features``
    / ``extract_common_features``.

    If ``headers`` is None or empty, assume a normal browser-like session so
    payload-only tests are not all scored as missing CSRF protection.
    """
    if not headers:
        return {
            "cookies_present": True,
            "token_present": True,
            "referrer_present": True,
        }

    h = headers
    cookies_present = bool("Cookie" in str(h) or any(str(k).lower() == "cookie" for k in h))
    token_present = bool(
        any("csrf" in str(k).lower() or "token" in str(k).lower() for k in h)
    )
    referrer_present = bool(
        "Referer" in str(h)
        or "Referrer" in str(h)
        or any(str(k).lower() in ("referer", "referrer") for k in h)
    )
    return {
        "cookies_present": cookies_present,
        "token_present": token_present,
        "referrer_present": referrer_present,
    }


def resolve_request_context(
    headers: Optional[Dict[str, Any]] = None,
    profile: Optional[Literal["csrf_attack"]] = None,
) -> Dict[str, bool]:
    """
    Resolve cookies / CSRF token / referer flags for IDS inference.

    - ``default`` (or omitted): use :func:`request_context_flags` (browser-like defaults
      when headers are absent).
    - ``csrf_attack``: logged-in session **without** CSRF token and **no** referer
      (cross-site style), aligned with many CSRF rows in ``simulate_http_record``.
    """
    if profile == "csrf_attack":
        return {
            "cookies_present": True,
            "token_present": False,
            "referrer_present": False,
        }
    return request_context_flags(headers)
