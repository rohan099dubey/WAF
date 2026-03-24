# Web Application Firewall (WAF) Simulation
## Complete Presentation Guide (Basic to Advanced)

## 1. Project in One Line
This project simulates a Web Application Firewall that sits between users and a web app, inspects each HTTP request, and either allows or blocks the request using machine learning (when available) plus security heuristics.

## 2. Why This Project Matters
Web applications are exposed to attacks such as SQL Injection and Cross-Site Scripting (XSS). A WAF is a defensive layer that filters malicious traffic before it reaches the application.

In this project, you demonstrate:
- Security filtering in a realistic proxy setup.
- Practical ML-assisted detection logic.
- Measurable performance and detection metrics.
- A complete reproducible demo stack with dashboard and automated testing.

## 3. Key Learning Objectives
By presenting this project, you show understanding of:
- HTTP request flow and reverse-proxy concepts.
- Feature extraction from URL/body payloads.
- Binary classification outcomes (malicious vs benign).
- Security evaluation metrics (TP, FP, FN, precision, recall, F1).
- Trade-off between security strictness and false positives.

## 4. High-Level Architecture
Request path:
1. Client sends request to WAF endpoint.
2. WAF extracts request features and classifies it.
3. If malicious: WAF returns 403 (blocked).
4. If benign: WAF forwards request to demo backend.
5. WAF logs event + latency and updates metrics.
6. Dashboard reads logs/metrics and visualizes behavior.
7. Evaluation script replays good/bad payloads and computes detection stats.

Main components:
- WAF service: [waf_simulator.py](waf_simulator.py)
- Demo backend app: [demo_app.py](demo_app.py)
- Dashboard UI: [dashboard.py](dashboard.py)
- Attack replay + metrics: [tools/evaluate.py](tools/evaluate.py)
- Docker orchestration: [docker-compose.yml](docker-compose.yml)

## 5. Basic Concepts You Should Explain to Your Professor

### 5.1 What is a WAF?
A WAF filters HTTP traffic to detect and block attack patterns before they hit the actual web application.

### 5.2 Why Proxy Position is Important
Because the WAF is in front of the backend, it can inspect every incoming request and enforce a decision centrally.

### 5.3 What is Being Classified?
Each request is classified as:
- Benign (allow)
- Malicious (block)

### 5.4 Why Use ML + Heuristics?
- ML can capture patterns learned from past data.
- Heuristics provide a reliable fallback if model is unavailable.
- Hybrid design improves robustness for a simulation environment.

## 6. Deep Dive: WAF Engine
Reference: [waf_simulator.py](waf_simulator.py)

### 6.1 Runtime Configuration
Key environment variables:
- BACKEND_URL: where allowed traffic is forwarded.
- WAF_MODEL_PATH: pickle model file path.
- WAF_LOG_FILE: jsonl event log location.

### 6.2 Feature Extraction Strategy
The WAF computes a feature vector from request path/query/body, including:
- Quote counts (single and double).
- SQL-like syntax markers (`--`, `;`, parentheses).
- Angle brackets (`<`, `>`) for XSS-like patterns.
- Encoded character statistics (`%` count threshold).
- Special symbols (`$`, `&`, `|`).
- Path and body length.
- Bad keyword frequency (`select`, `union`, `drop`, `script`, etc.).

These are simple but meaningful lexical security features.

### 6.3 Classification Logic
Flow:
1. Try loading and using trained model from pickle.
2. If model prediction works, decision source is `ml`.
3. If model unavailable/fails, fallback to `heuristic` keyword detection.

This ensures service continuity even when ML dependencies are not installed.

### 6.4 Block vs Allow Behavior
- Blocked requests return HTTP 403 with reason.
- Allowed requests are proxied to backend using original method, args, body, and filtered headers.

### 6.5 State and Metrics
WAF tracks:
- total requests
- blocked count
- allowed count
- malicious_detected
- average latency in milliseconds

Endpoints:
- `/health`
- `/metrics`
- `/events`

## 7. Deep Dive: Demo Backend App
Reference: [demo_app.py](demo_app.py)

Purpose:
- Gives realistic protected endpoints for testing allow/block behavior.

Routes:
- `/` basic API welcome.
- `/search?q=...` useful for injecting payload strings.
- `/login` POST simulation.
- `/product/<id>` simple resource endpoint.

Why needed:
Without a backend app, you cannot clearly demonstrate that benign traffic reaches business logic while malicious traffic is blocked.

## 8. Deep Dive: Dashboard
Reference: [dashboard.py](dashboard.py)

What it shows:
- Total requests.
- Blocked and allowed counts.
- Average latency.
- Recent event table (method, path, status, decision, latency).
- Line chart for latency trend.

How it gets data:
- Reads local jsonl log file when available.
- Falls back to WAF `/metrics` and `/events` APIs.
- Refreshes every 5 seconds.

Presentation value:
The dashboard turns backend security events into visual evidence for your analysis.

## 9. Deep Dive: Evaluation Script and Detection Metrics
Reference: [tools/evaluate.py](tools/evaluate.py)

Inputs:
- Good payload set: [Testing_Data/payloads_good.txt](Testing_Data/payloads_good.txt)
- Bad payload set: [Testing_Data/payloads_bad.txt](Testing_Data/payloads_bad.txt)

Process:
1. Send requests to `/search` through WAF.
2. Mark blocked status from HTTP code 403.
3. Compare expected label (good/bad) vs WAF decision.
4. Compute confusion matrix and quality metrics.

Outputs:
- Row-level results CSV: [Testing_Data/evaluation_results.csv](Testing_Data/evaluation_results.csv)
- Summary JSON: [Testing_Data/evaluation_summary.json](Testing_Data/evaluation_summary.json)
- Human-readable report: [Testing_Data/evaluation_report.md](Testing_Data/evaluation_report.md)

### 9.1 Metric Formulas
Let:
- TP = bad payload correctly blocked
- TN = good payload correctly allowed
- FP = good payload wrongly blocked
- FN = bad payload wrongly allowed

Then:
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
F1 = 2 \cdot \frac{Precision \cdot Recall}{Precision + Recall}
$$

Latency metric:
$$
AvgLatency = \frac{\sum latency_i}{N}
$$

### 9.2 Interpretation Guidance
- High precision means fewer false alarms.
- High recall means more attacks caught.
- Lower latency means less performance overhead.
- In security, improving recall often increases false positives, so tuning is needed.

## 10. Docker Reproducibility Story
Reference: [docker-compose.yml](docker-compose.yml)

Services:
- demo-app
- waf
- dashboard
- test-runner (profile: eval)

Why this is important academically:
- Any evaluator can run the same stack with same behavior.
- Eliminates local machine dependency issues.
- Shows engineering maturity beyond just code.

## 11. End-to-End Demo Script (What to Say During Presentation)

### Step 1: Start services
Show that all components are running.

### Step 2: Explain traffic path
Client -> WAF -> Backend (if allowed).

### Step 3: Show benign request
Example: `/search?q=hello world`
Expected: Allowed and forwarded.

### Step 4: Show malicious request
Example: `/search?q=' OR 1=1 --`
Expected: HTTP 403 blocked by WAF.

### Step 5: Open dashboard
Show count increments, decision labels, and latency chart.

### Step 6: Run automated evaluation
Generate metrics files and discuss TP/FP/FN trade-offs.

### Step 7: Conclude with limitations and improvements
Show technical honesty and future roadmap.

## 12. Important Design Choices You Can Defend
- Hybrid detection: model + heuristic fallback for reliability.
- Lightweight lexical features for interpretability.
- JSONL event logging for easy ingestion and traceability.
- Dedicated evaluator for objective metric reporting.
- Docker Compose for reproducible grading.

## 13. Known Limitations (Be Honest)
- Current feature set is lexical and does not parse full protocol semantics.
- Heuristic fallback may miss obfuscated attacks or over-block edge cases.
- Model is static; no online learning or periodic retraining pipeline.
- Dashboard is functional but not role-based or hardened for production.
- No TLS termination or enterprise-grade WAF rule engine in this simulation.

## 14. Future Work (Strong Closing Section)
- Add signature/rule engine (regex and OWASP CRS-like checks).
- Add model retraining pipeline from new labeled logs.
- Add payload normalization/deobfuscation stage.
- Add per-endpoint policy profiles and rate limiting.
- Add richer observability (Prometheus + Grafana).
- Benchmark under load (RPS, p95/p99 latency, throughput).

## 15. Viva Questions and Suggested Answers

Q1. Why not only machine learning?
A: Pure ML can fail under distribution shift; heuristic fallback keeps service operational and interpretable.

Q2. How do you measure effectiveness?
A: Using confusion matrix metrics (TP, FP, FN, TN), precision/recall/F1, and added latency.

Q3. What happens if model file is missing?
A: WAF automatically switches to heuristic mode and continues filtering.

Q4. Why include a dashboard?
A: It provides real-time evidence of behavior, improving explainability and demonstration quality.

Q5. Is this production-ready?
A: It is a simulation/prototype for academic demonstration; production WAF would need stronger rule engines, richer parsing, robust hardening, and scale testing.

## 16. Files You Should Be Ready to Walk Through
- [waf_simulator.py](waf_simulator.py)
- [demo_app.py](demo_app.py)
- [dashboard.py](dashboard.py)
- [tools/evaluate.py](tools/evaluate.py)
- [docker-compose.yml](docker-compose.yml)
- [Testing_Data/evaluation_report.md](Testing_Data/evaluation_report.md)

## 17. Quick Run Commands (Windows)

Install minimal runtime:
```bat
pip install -r requirements.txt
```

Run locally (3 terminals):
```bat
python demo_app.py
python waf_simulator.py
python dashboard.py
```

Run evaluator:
```bat
python tools/evaluate.py --base-url http://localhost:8080
```

Run with Docker:
```bat
docker compose up --build
docker compose --profile eval run --rm test-runner
docker compose down
```

## 18. Submission Checklist
- Code and documentation complete.
- Local demo verified.
- Evaluation files generated.
- Dashboard screenshots captured.
- Architecture flow explained in slides.
- Limitation and future work included.

---
Use this guide as your speaking script: begin with problem statement, then architecture, then request flow, then metrics evidence, then limitations/future work.
