# WAF Project Report

## Course: Internet Security

## Project Title: Web Application Firewall (WAF) Simulation

---

## Abstract

This project presents a simulation of a Web Application Firewall (WAF) designed to protect a backend web application from malicious HTTP requests. The WAF acts as a reverse proxy and evaluates incoming requests using a hybrid approach: machine learning-based classification (when a trained model is available) and heuristic keyword-based fallback detection. Malicious traffic is blocked with HTTP 403 responses, while benign traffic is forwarded to the backend service. The system provides event logging, real-time metrics, and a dashboard for observability. An automated evaluator replays benign and malicious payloads to generate confusion-matrix-based performance metrics including accuracy, precision, recall, F1 score, and latency.

---

## 1. Introduction

Modern web applications are continuously targeted by attack vectors such as SQL Injection and Cross-Site Scripting (XSS). A practical defense strategy is to place a security inspection layer in front of the application server. This layer, known as a Web Application Firewall, filters requests and blocks suspicious payloads before they reach business logic.

The objective of this project is to design and demonstrate a complete WAF simulation stack suitable for Internet Security coursework, including:

1. A request-inspecting WAF proxy.
2. A protected demo backend application.
3. A dashboard to visualize detections and latency.
4. An evaluation tool to produce measurable security metrics.

---

## 2. Problem Statement

Web applications often directly process user-controlled inputs (query strings, form data, request bodies). Without proper filtering, malicious inputs may trigger vulnerable backend behavior.

The specific problem addressed here is:

> How can incoming HTTP requests be filtered in real time, with measurable effectiveness, while maintaining low overhead and clear explainability for educational purposes?

---

## 3. Objectives

1. Build a WAF proxy that can classify requests as benign or malicious.
2. Use a hybrid detection model (ML + heuristic fallback) for runtime robustness.
3. Maintain logs and operational metrics for monitoring.
4. Visualize activity and performance using a web dashboard.
5. Evaluate detection quality using confusion matrix and latency measurements.
6. Package the system for reproducible runs (local and Docker).

---

## 4. System Architecture

### 4.1 Components

- `waf_simulator.py`: primary WAF proxy and detection engine.
- `demo_app.py`: backend application protected by WAF.
- `dashboard.py`: UI for metrics, events, and latency trend.
- `tools/evaluate.py`: scripted payload replay and metric generation.
- `docker-compose.yml`: orchestration for all services.

### 4.2 Data/Request Flow

1. Client sends request to WAF endpoint (`:8080`).
2. WAF extracts lexical security features from path/query/body.
3. WAF classifies request (ML model or heuristic fallback).
4. If malicious, WAF blocks and returns `403`.
5. If benign, WAF forwards request to backend (`:5001`).
6. Event + latency are logged in JSONL and counters are updated.
7. Dashboard (`:8501`) reads metrics/events and displays status.
8. Evaluation script sends test payloads and computes final metrics.

---

## 5. Implementation Details

### 5.1 WAF Service (`waf_simulator.py`)

#### 5.1.1 Runtime Configurations

- `BACKEND_URL` (default: `http://localhost:5001`)
- `WAF_MODEL_PATH` (default: `training_model.pkl`)
- `WAF_LOG_FILE` (default: `logs/waf_events.jsonl`)

These parameters make deployment flexible without changing code.

#### 5.1.2 Feature Extraction

The WAF derives a numeric feature vector from request path/query/body. Features include:

- Single and double quote counts.
- SQL-like markers (`--`, `;`, keyword frequencies).
- Parentheses and angle brackets.
- Encoded character counts (`%`) and symbol counts (`$`, `&`, `|`).
- Path/body lengths.

This feature design focuses on lightweight lexical indicators that are computationally cheap and interpretable.

#### 5.1.3 Classification Strategy

1. Attempt model prediction from `training_model.pkl`.
2. If model is missing or inference fails, fallback to heuristics.
3. Heuristic mode checks suspicious keyword presence in request text.

This hybrid strategy ensures continuity even when optional ML dependencies/artifacts are unavailable.

#### 5.1.4 Proxy Decision Logic

- Malicious decision:
  - return `403` with JSON reason
  - log event
  - update blocked counters
- Benign decision:
  - forward request method/path/query/body/headers to backend
  - return backend response
  - log event and update allowed counters

#### 5.1.5 Metrics and APIs

- `/health`: service and model status
- `/metrics`: total, blocked, allowed, malicious_detected, average latency
- `/events`: recent detection events

---

### 5.2 Demo Backend (`demo_app.py`)

Routes:

- `/` basic root endpoint
- `/search?q=...` payload testing endpoint
- `/login` form simulation endpoint
- `/product/<id>` resource retrieval endpoint

This service provides safe target behavior to verify that benign traffic passes through WAF controls.

---

### 5.3 Dashboard (`dashboard.py`)

The dashboard displays:

- total requests
- blocked requests
- allowed requests
- average latency
- recent events table
- latency line chart

Data is collected from WAF endpoints and/or event logs.

---

### 5.4 Evaluator (`tools/evaluate.py`)

Inputs:

- `Testing_Data/payloads_good.txt`
- `Testing_Data/payloads_bad.txt`

Workflow:

1. Send payloads through WAF (`/search`).
2. Mark request as blocked if response status is `403`.
3. Compare result with expected label.
4. Compute confusion matrix + quality metrics.
5. Save CSV, JSON summary, and markdown report.

Generated outputs:

- `Testing_Data/evaluation_results.csv`
- `Testing_Data/evaluation_summary.json`
- `Testing_Data/evaluation_report.md`

---

## 6. Mathematical Evaluation Metrics

Let:

- TP = malicious correctly blocked
- TN = benign correctly allowed
- FP = benign incorrectly blocked
- FN = malicious incorrectly allowed

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

$$
Average\ Latency = \frac{\sum_{i=1}^{N} latency_i}{N}
$$

---

## 7. Experimental Results (Current Project Outputs)

From `Testing_Data/evaluation_summary.json`:

- Total Requests: `16`
- TP: `6`
- TN: `8`
- FP: `0`
- FN: `2`
- Accuracy: `0.875` (87.5%)
- Precision: `1.0` (100%)
- Recall: `0.75` (75%)
- F1 Score: `0.8571` (85.71%)
- Average Latency: `18.99 ms`

### 7.1 Result Interpretation

- Very high precision indicates no benign sample was wrongly blocked in this run.
- Recall is lower than precision, indicating some malicious requests escaped detection.
- This suggests the model/rules are conservative and should be expanded for stronger attack coverage.

---

## 8. Security Relevance and Learning Outcomes

This project demonstrates key Internet Security concepts:

1. Reverse proxy as a security control point.
2. Input inspection and attack surface reduction.
3. Hybrid detection design under operational constraints.
4. Evidence-based security assessment using confusion matrix.
5. Trade-off between strict blocking and false positives.

---

## 9. Limitations

1. Detection features are mostly lexical and simple.
2. Heuristic fallback may miss obfuscated payloads.
3. Model lifecycle (continuous retraining) is not automated.
4. Current setup uses development-grade Flask runtime.
5. This is a simulation/prototype, not a production-grade enterprise WAF.

---

## 10. Future Enhancements

1. Add richer signature/rule engine (regex + policy sets).
2. Add payload normalization and deobfuscation pipeline.
3. Automate periodic model retraining from labeled logs.
4. Add endpoint-specific policies and rate-limiting controls.
5. Integrate production observability (Prometheus/Grafana).
6. Add load testing with p95/p99 latency and throughput analysis.

---

## 11. Reproducibility and Execution

### 11.1 Local Run

1. `pip install -r requirements.txt`
2. Start backend: `python demo_app.py`
3. Start WAF: `python waf_simulator.py`
4. Start dashboard: `python dashboard.py`
5. Evaluate: `python tools/evaluate.py --base-url http://localhost:8080`

### 11.2 Docker Run

1. `docker compose up --build`
2. `docker compose --profile eval run --rm test-runner`
3. `docker compose down`

---

## 12. Conclusion

The project successfully implements a complete WAF simulation pipeline that inspects, classifies, blocks/forwards, logs, visualizes, and evaluates HTTP traffic. It is technically appropriate for Internet Security coursework because it combines practical defensive architecture with measurable outcomes. Current results show strong precision and acceptable latency, while highlighting opportunities to improve recall through richer detection features and advanced rule/model tuning.

---

## 13. References (Project Artifacts)

- `README.md`
- `waf_simulator.py`
- `demo_app.py`
- `dashboard.py`
- `tools/evaluate.py`
- `docker-compose.yml`
- `Testing_Data/evaluation_summary.json`
- `Testing_Data/evaluation_report.md`
