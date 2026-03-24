# Internet Security Project Complete Report

## Project: Web Application Firewall (WAF) Simulation

This report is written for a student who is new to the codebase and needs to **present confidently** in class/viva.

---

## 1) Executive Summary (What this project does)

This project simulates a **Web Application Firewall (WAF)** that sits between users and a web application.

- Every incoming HTTP request first reaches the WAF.
- The WAF checks if the request looks malicious.
- If malicious, it blocks the request (`HTTP 403`).
- If safe, it forwards the request to the backend demo app.
- It logs each event and shows metrics in a dashboard.

So the core idea is: **inspect -> decide -> block/allow -> log -> visualize -> evaluate**.

---

## 2) Why this project is important (Internet Security context)

In Internet Security, web apps are exposed to common attacks like:

- SQL Injection
- XSS (Cross-Site Scripting)
- Command-like payloads

A WAF is a practical defensive layer because it can reduce attack traffic **before it reaches application logic**.

This project demonstrates:

1. Security proxy architecture
2. Detection logic (ML + heuristic)
3. Measurable detection quality (TP/TN/FP/FN, precision, recall, F1)
4. Practical observability (dashboard + logs)

---

## 3) Final architecture (How components connect)

### Components

- `demo_app.py`: protected backend service (port 5001)
- `waf_simulator.py`: WAF proxy and classifier (port 8080)
- `dashboard.py`: web dashboard for events/latency (port 8501)
- `tools/evaluate.py`: automated payload testing script

### Request flow

1. User sends request to WAF (`http://localhost:8080/...`).
2. WAF extracts features from URL/body.
3. WAF classifies request:
   - ML model if available
   - heuristic fallback if model unavailable
4. Decision:
   - malicious -> return 403
   - benign -> forward request to backend (`http://localhost:5001`)
5. WAF writes log event and updates metrics.
6. Dashboard reads metrics/events and displays real-time status.

---

## 4) Start point to entry points (what runs first)

When you run each file directly, Python enters the `if __name__ == "__main__":` block.

### A) WAF entry point

File: `waf_simulator.py`

- Starts Flask app on port `8080`
- Exposes:
  - `/health`
  - `/metrics`
  - `/events`
  - catch-all route for proxying (`/` and `/<path:path>`)

This is the **main security engine**.

### B) Backend app entry point

File: `demo_app.py`

- Starts demo Flask app on port `5001`
- Routes:
  - `/`
  - `/search?q=...`
  - `/login`
  - `/product/<id>`

This is the **target app** that WAF protects.

### C) Dashboard entry point

File: `dashboard.py`

- Starts dashboard Flask app on port `8501`
- `/` serves HTML with chart
- `/api/data` returns metrics + recent events

### D) Evaluation entry point

File: `tools/evaluate.py`

- Reads payload files (`good` and `bad`)
- Sends test requests via WAF
- Computes confusion matrix and quality metrics
- Writes outputs in `Testing_Data/`

---

## 5) Deep technical explanation of `waf_simulator.py` (what/why/how)

### 5.1 Configuration

Environment variables:

- `BACKEND_URL` (default `http://localhost:5001`)
- `WAF_MODEL_PATH` (default `training_model.pkl`)
- `WAF_LOG_FILE` (default `logs/waf_events.jsonl`)

Why: makes runtime configurable without code change.

### 5.2 Model loading strategy

Function `load_model()`:

- Tries to load pickled ML model from disk.
- If file missing/error, returns `None`.

Why: system should still work even if model unavailable.

### 5.3 Feature extraction

Function `extract_features(path, body)` creates numeric features such as:

- quote counts (`'`, `"`)
- SQL-like symbols (`--`, `;`, keywords like `select`, `drop`, `union`)
- XSS indicators (`<`, `>`)
- special chars (`$`, `&`, `|`)
- URL/body lengths

Why: ML models and heuristics both need structured indicators of malicious patterns.

### 5.4 Classification

Function `classify_request(path_with_query, body)`:

1. Generate features
2. If model exists, use `MODEL.predict(...)`
3. If model fails or absent, use heuristic keyword detection
4. Return `(malicious_bool, confidence, source)`

Why hybrid detection:

- ML provides data-driven behavior
- heuristic guarantees fallback reliability

### 5.5 Blocking and forwarding logic

Function `proxy_to_backend(path)`:

- Reconstructs full path + query
- Measures latency
- Runs classification
- If malicious:
  - log event
  - update state
  - return `403`
- If benign:
  - forward request using `requests.request(...)`
  - return backend response
  - log + update metrics

### 5.6 Metrics and events

- In-memory `STATE` tracks totals and average latency
- `RECENT_EVENTS` stores latest events
- `/metrics` returns counters
- `/events` returns recent decision logs

This provides observability and supports dashboard visualizations.

---

## 6) Backend app (`demo_app.py`) technical purpose

This app is intentionally simple, so WAF behavior is easy to demonstrate.

- `/search` is the main endpoint for payload testing.
- Safe payload should return normal JSON.
- Malicious payload should be blocked by WAF before reaching this app.

Why this is useful in viva:

- Shows “allowed traffic continues business flow”.
- Shows “malicious traffic is stopped at security layer”.

---

## 7) Dashboard (`dashboard.py`) technical purpose

Dashboard fetches and visualizes:

- total/blocked/allowed counts
- average latency
- recent request table
- latency trend chart

Data strategy:

- First tries local log file
- Falls back to WAF APIs (`/metrics`, `/events`)

Why important:

- Gives real-time visual proof during presentation
- Makes your project look complete and measurable

---

## 8) Evaluation script (`tools/evaluate.py`) and metrics

### Inputs

- `Testing_Data/payloads_good.txt`
- `Testing_Data/payloads_bad.txt`

### Process

1. Send each payload to `/search` through WAF
2. Label expected class (`good` or `bad`)
3. Decision rule: `status_code == 403` means blocked
4. Build confusion matrix

### Formulas

$$
Accuracy = \frac{TP + TN}{TP + TN + FP + FN}
$$

$$
Precision = \frac{TP}{TP + FP}
$$

$$
Recall = \frac{TP}{TP + FN}
$$

$$
F1 = 2\cdot\frac{Precision\cdot Recall}{Precision + Recall}
$$

### Current recorded results (from `Testing_Data/evaluation_summary.json`)

- Total: 16
- TP: 6
- TN: 8
- FP: 0
- FN: 2
- Accuracy: 0.875
- Precision: 1.0
- Recall: 0.75
- F1 score: 0.8571
- Avg latency: 18.99 ms

### Interpretation you can say in viva

- Precision is perfect (no good request blocked in this sample).
- Recall is lower than precision, meaning some bad requests still passed (2 FN).
- This is realistic: stricter detection can increase false positives, so tuning is required.

---

## 9) Legacy files and how to explain them

### `Proxy_server.py`

- Older implementation of proxy/classifier pipeline.
- Includes model usage and feature extraction.
- Not primary runtime now.

### `log_parse.py`

- Legacy parser for log-to-CSV feature extraction from XML/b64 request logs.
- Useful for dataset preparation/training workflows.

In presentation, say:

> “These were earlier experimental/legacy scripts. Final runnable architecture uses `waf_simulator.py`, `demo_app.py`, `dashboard.py`, and `tools/evaluate.py`.”

---

## 10) How to run demo (local)

Use 3 terminals:

1. `python demo_app.py`
2. `python waf_simulator.py`
3. `python dashboard.py`

Open:

- WAF: `http://localhost:8080`
- backend (direct): `http://localhost:5001`
- dashboard: `http://localhost:8501`

Run evaluation:

- `python tools/evaluate.py --base-url http://localhost:8080`

---

## 11) How to run with Docker (best for grading)

- `docker compose up --build`
- `docker compose --profile eval run --rm test-runner`
- `docker compose down`

Why this helps:

- reproducible setup
- easier demo on another system

---

## 12) 10-slide PPT structure (ready content)

### Slide 1: Title

“Web Application Firewall Simulation using ML + Heuristic Detection”

Include: name, course (Internet Security), date.

### Slide 2: Problem Statement

- Web apps face injection attacks.
- Need filtering before app layer.

### Slide 3: Objective

- Build WAF proxy simulation
- Detect malicious requests
- Measure effectiveness and latency

### Slide 4: Architecture Diagram

Client -> WAF -> Backend + Logs -> Dashboard

### Slide 5: Detection Logic

- feature extraction
- ML prediction
- heuristic fallback
- block vs allow decision

### Slide 6: Implementation Stack

- Python, Flask, Requests
- Optional scikit-learn model
- Docker Compose orchestration

### Slide 7: Evaluation Method

- good vs bad payload replay
- confusion matrix metrics
- latency measurement

### Slide 8: Results

Use current numbers:

- Accuracy 87.5%
- Precision 100%
- Recall 75%
- F1 85.71%
- Avg latency 18.99 ms

### Slide 9: Limitations and Future Work

- lexical features only
- no advanced deobfuscation
- add rule engine + retraining + load test

### Slide 10: Conclusion

- Working WAF prototype with measurable outcomes
- practical Internet Security learning achieved

---

## 13) Live demo speaking script (simple and safe)

Use this exact flow:

1. “First, I start backend, WAF, and dashboard.”
2. “Now I send a normal query to `/search?q=hello` and it is allowed.”
3. “Now I send a malicious payload like `' OR 1=1 --` and WAF blocks with 403.”
4. “Dashboard shows blocked/allowed counts and latency in real time.”
5. “Finally I run automated evaluator and show TP/FP/FN metrics files.”
6. “This demonstrates both functional security filtering and quantitative analysis.”

---

## 14) Viva questions with strong answers

### Q1) Why combine ML and heuristics?

ML improves pattern learning, while heuristics ensure reliable fallback when model is unavailable.

### Q2) What is false negative risk?

False negatives are malicious requests that pass through. In current results FN=2, so we need stronger features/rules.

### Q3) How did you measure WAF quality?

Using confusion matrix (TP, TN, FP, FN), precision, recall, F1, and average latency overhead.

### Q4) Is this production ready?

No, this is an academic simulation prototype. Production WAF needs hardened deployment, advanced parsing/rules, and large-scale load testing.

### Q5) What is your key contribution?

End-to-end WAF simulation with detection, proxying, logging, dashboard visualization, and automated measurable evaluation.

---

## 15) Risk/limitation section (say this confidently)

- Static model file (no automated retraining)
- simple lexical features
- some malicious payloads can evade current checks
- Flask dev servers, not hardened production runtime

This honesty usually improves evaluator confidence in your understanding.

---

## 16) What to practice before presentation (checklist)

1. Practice architecture explanation in 60 seconds.
2. Memorize TP/TN/FP/FN meanings.
3. Rehearse one benign and one malicious request demo.
4. Keep evaluation output files ready (`csv/json/md`).
5. Keep one backup: Docker demo command sequence.

---

## 17) 2-minute opening speech (you can read this directly)

“Good morning. My project is a Web Application Firewall simulation for Internet Security. The goal is to protect a backend web app by inspecting incoming HTTP requests and deciding whether to allow or block them. The architecture has four main parts: a demo backend app, a WAF proxy, a dashboard, and an automated evaluator. The WAF extracts request features such as suspicious keywords and special characters, then classifies requests using a machine learning model when available, with a heuristic fallback for reliability. If a request is malicious, the WAF blocks it with HTTP 403; otherwise it forwards to the backend. I also log each request decision and latency, and visualize these in a dashboard. To validate performance, I replayed good and bad payloads and measured confusion-matrix metrics. The current results show 87.5% accuracy, 100% precision, 75% recall, and average latency around 19 milliseconds. This demonstrates a practical, measurable security defense pipeline and also highlights future improvement areas like better feature engineering and reduced false negatives.”

---

## 18) Final one-line conclusion for viva

This project successfully demonstrates a complete, measurable, and explainable WAF prototype that combines secure request filtering, monitoring, and evaluation in a reproducible setup.
