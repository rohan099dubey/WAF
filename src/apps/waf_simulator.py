import json
import os
import pickle
import time
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import unquote_plus

import requests
from flask import Flask, Response, jsonify, request

APP = Flask(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")
MODEL_PATH = os.getenv("WAF_MODEL_PATH", "models/training_model.pkl")
LOG_FILE = Path(os.getenv("WAF_LOG_FILE", "logs/waf_events.jsonl"))
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

BADWORDS = [
    "sleep",
    "uid",
    "select",
    "waitfor",
    "delay",
    "system",
    "union",
    "order by",
    "group by",
    "admin",
    "drop",
    "script",
]

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

STATE_LOCK = Lock()
STATE = {
    "total": 0,
    "blocked": 0,
    "allowed": 0,
    "malicious_detected": 0,
    "avg_latency_ms": 0.0,
}
RECENT_EVENTS: deque[dict[str, Any]] = deque(maxlen=250)


def load_model() -> Any | None:
    if not Path(MODEL_PATH).exists():
        return None
    try:
        with open(MODEL_PATH, "rb") as handle:
            return pickle.load(handle)
    except Exception:
        return None


MODEL = load_model()


def extract_features(path: str, body: str) -> list[int]:
    path = str(path)
    body = str(body)
    combined_raw = path + body

    raw_percentages = combined_raw.count("%")
    raw_spaces = combined_raw.count(" ")

    raw_percentages_count = raw_percentages if raw_percentages > 3 else 0

    path_decoded = unquote_plus(path)
    body_decoded = unquote_plus(body)

    single_q = path_decoded.count("'") + body_decoded.count("'")
    double_q = path_decoded.count('"') + body_decoded.count('"')
    dashes = path_decoded.count("--") + body_decoded.count("--")
    braces = path_decoded.count("(") + body_decoded.count("(")
    spaces = path_decoded.count(" ") + body_decoded.count(" ")
    semicolons = path_decoded.count(";") + body_decoded.count(";")
    angle_brackets = (
        path_decoded.count("<")
        + path_decoded.count(">")
        + body_decoded.count("<")
        + body_decoded.count(">")
    )
    special_chars = sum(path_decoded.count(c) + body_decoded.count(c) for c in "$&|")
    badwords_count = sum(
        path_decoded.lower().count(word) + body_decoded.lower().count(word)
        for word in BADWORDS
    )

    path_length = len(path_decoded)
    body_length = len(body_decoded)

    return [
        single_q,
        double_q,
        dashes,
        braces,
        spaces,
        raw_percentages_count,
        semicolons,
        angle_brackets,
        special_chars,
        path_length,
        body_length,
        badwords_count,
    ]


def heuristic_is_malicious(path: str, body: str) -> bool:
    joined = f"{path} {body}".lower()
    return any(keyword in joined for keyword in BADWORDS)


def classify_request(path_with_query: str, body: str) -> tuple[bool, float, str]:
    features = extract_features(path_with_query, body)

    if MODEL is not None:
        try:
            arr = [features]
            pred = int(MODEL.predict(arr)[0])
            if hasattr(MODEL, "predict_proba"):
                confidence = float(MODEL.predict_proba(arr)[0][pred])
            else:
                confidence = 1.0
            return pred == 1, confidence, "ml"
        except Exception:
            pass

    heuristic_pred = heuristic_is_malicious(path_with_query, body)
    return heuristic_pred, 0.8 if heuristic_pred else 0.7, "heuristic"


def update_state(latency_ms: float, blocked: bool, malicious_detected: bool) -> None:
    with STATE_LOCK:
        previous_total = STATE["total"]
        STATE["total"] += 1
        STATE["blocked"] += int(blocked)
        STATE["allowed"] += int(not blocked)
        STATE["malicious_detected"] += int(malicious_detected)
        if previous_total == 0:
            STATE["avg_latency_ms"] = latency_ms
        else:
            STATE["avg_latency_ms"] = (
                STATE["avg_latency_ms"] * previous_total + latency_ms
            ) / STATE["total"]


def write_event(event: dict[str, Any]) -> None:
    RECENT_EVENTS.appendleft(event)
    with open(LOG_FILE, "a", encoding="utf-8") as log_handle:
        log_handle.write(json.dumps(event) + "\n")


def proxy_to_backend(path: str) -> Response:
    query_string = request.query_string.decode("utf-8", errors="ignore")
    full_path = f"/{path}"
    if query_string:
        full_path = f"{full_path}?{query_string}"

    body = request.get_data(as_text=True)
    method = request.method

    start = time.perf_counter()
    malicious, confidence, model_source = classify_request(full_path, body)

    if malicious:
        latency_ms = (time.perf_counter() - start) * 1000
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": method,
            "path": full_path,
            "blocked": True,
            "model_source": model_source,
            "confidence": round(confidence, 4),
            "status_code": 403,
            "latency_ms": round(latency_ms, 2),
        }
        write_event(event)
        update_state(latency_ms=latency_ms, blocked=True, malicious_detected=True)
        return jsonify({"message": "Blocked by WAF", "reason": "malicious pattern detected"}), 403

    forward_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }

    backend_url = f"{BACKEND_URL}/{path}"
    backend_response = requests.request(
        method=method,
        url=backend_url,
        params=request.args,
        data=request.get_data(),
        headers=forward_headers,
        timeout=8,
        allow_redirects=False,
    )

    latency_ms = (time.perf_counter() - start) * 1000
    event = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": method,
        "path": full_path,
        "blocked": False,
        "model_source": model_source,
        "confidence": round(confidence, 4),
        "status_code": backend_response.status_code,
        "latency_ms": round(latency_ms, 2),
    }
    write_event(event)
    update_state(latency_ms=latency_ms, blocked=False, malicious_detected=False)

    response_headers = [
        (name, value)
        for name, value in backend_response.raw.headers.items()
        if name.lower() not in HOP_BY_HOP_HEADERS
    ]
    return Response(backend_response.content, backend_response.status_code, response_headers)


@APP.route("/health", methods=["GET"])
def health() -> Response:
    return jsonify({"status": "ok", "model_loaded": MODEL is not None})


@APP.route("/metrics", methods=["GET"])
def metrics() -> Response:
    with STATE_LOCK:
        return jsonify(dict(STATE))


@APP.route("/events", methods=["GET"])
def events() -> Response:
    limit = int(request.args.get("limit", 100))
    limited = list(RECENT_EVENTS)[: max(1, min(limit, 250))]
    return jsonify({"events": limited})


@APP.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@APP.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def catch_all(path: str) -> Response:
    return proxy_to_backend(path)


if __name__ == "__main__":
    host = os.getenv("WAF_HOST", "0.0.0.0")
    port = int(os.getenv("WAF_PORT", "8080"))
    APP.run(host=host, port=port)
