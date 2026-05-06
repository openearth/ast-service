"""
KBStoolbox / AST backend — lightweight API analytics (CSV).

What is logged (one row per response, except skipped paths):
  timestamp (ISO 8601 UTC), process (request.path), method, domain (header netloc
  only, from Origin/Referer/Host), status_code.

What is NOT logged:
  IP addresses, user identifiers, session/cookies, request body, query strings as
  part of the domain field.

GDPR / privacy:
  Only the originating host/netloc from Origin, Referer, or Host is stored. This
  is not legal advice; align processing with your legal basis and DPIA as needed.

Configuration:
  ANALYTICS_API_KEY — required for GET /analytics and GET /analytics/download.
  Send the same value in the X-API-Key header.
  Optional: ANALYTICS_LOG_FILE, ANALYTICS_LOCK_FILE (defaults: analytics.csv next
  to this module, and LOG_FILE + ".lock").

Deployment:
  uWSGI runs multiple worker processes; concurrent CSV appends require locking.
  This module uses the third-party ``filelock`` package (not the stdlib) so all
  workers serialize access safely.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse

from filelock import FileLock
from flask import Blueprint, abort, jsonify, request, send_file

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_LOG = os.path.join(_BASE_DIR, "analytics.csv")

LOG_FILE = os.environ.get("ANALYTICS_LOG_FILE", _DEFAULT_LOG)
LOCK_FILE = os.environ.get("ANALYTICS_LOCK_FILE", LOG_FILE + ".lock")

CSV_FIELDNAMES = ("timestamp", "process", "method", "domain", "status_code")

analytics_bp = Blueprint("analytics", __name__)


def _should_skip_logging(path: str) -> bool:
    if path == "/health" or path.startswith("/health/"):
        return True
    if path == "/static" or path.startswith("/static/"):
        return True
    if path == "/analytics" or path.startswith("/analytics/"):
        return True
    return False


def _extract_domain() -> str:
    """Return netloc only: Origin, then Referer, then Host."""
    origin = request.headers.get("Origin", "").strip()
    referer = request.headers.get("Referer", "").strip()
    host = request.headers.get("Host", "").strip()

    for raw in (origin, referer):
        if not raw or raw.lower() == "null":
            continue
        if "://" not in raw and not raw.startswith("//"):
            raw = "//" + raw
        parsed = urlparse(raw)
        if parsed.netloc:
            return parsed.netloc

    if host:
        parsed = urlparse("//" + host, scheme="https")
        return parsed.netloc or host
    return ""


def _ensure_csv_with_headers() -> None:
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    with FileLock(LOCK_FILE, timeout=60):
        if not os.path.isfile(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
            with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(CSV_FIELDNAMES)


def _append_analytics_row(process: str, method: str, domain: str, status_code: int) -> None:
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with FileLock(LOCK_FILE, timeout=60):
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDNAMES).writerow(
                {
                    "timestamp": ts,
                    "process": process,
                    "method": method,
                    "domain": domain,
                    "status_code": status_code,
                }
            )


def log_request_analytics(response):
    try:
        if _should_skip_logging(request.path):
            return response
        _append_analytics_row(
            process=request.path,
            method=request.method,
            domain=_extract_domain(),
            status_code=response.status_code,
        )
    except Exception:
        pass
    return response


def _require_analytics_api_key() -> None:
    expected = os.environ.get("ANALYTICS_API_KEY", "")
    supplied = request.headers.get("X-API-Key", "")
    if not expected or supplied != expected:
        abort(403)


@analytics_bp.get("/analytics")
def analytics_json():
    _require_analytics_api_key()
    process_q = request.args.get("process")
    domain_q = request.args.get("domain")
    try:
        limit = int(request.args.get("limit", "500"))
    except ValueError:
        limit = 500
    limit = max(1, min(limit, 50_000))

    with FileLock(LOCK_FILE, timeout=120):
        with open(LOG_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    filtered = [
        r
        for r in rows
        if (not process_q or r.get("process") == process_q)
        and (not domain_q or r.get("domain") == domain_q)
    ]
    return jsonify(filtered[-limit:])


@analytics_bp.get("/analytics/download")
def analytics_download():
    _require_analytics_api_key()
    with FileLock(LOCK_FILE, timeout=120):
        with open(LOG_FILE, "rb") as f:
            raw = f.read()
    return send_file(
        BytesIO(raw),
        mimetype="text/csv",
        as_attachment=True,
        download_name="analytics.csv",
    )


def init_analytics(app) -> None:
    """
    Initialize CSV analytics on the given Flask app.

    Call exactly once per app instance (e.g. ``init_analytics(application)`` in
    app.py). Safe under uWSGI: each worker runs this on import; filelock
    coordinates CSV access across processes.
    """
    _ensure_csv_with_headers()
    app.after_request(log_request_analytics)
    app.register_blueprint(analytics_bp)
