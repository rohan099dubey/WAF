# Web Application Firewall (WAF) Simulation

This repository now contains a complete WAF simulation setup for an Internet Security project submission, including:

- WAF proxy service with ML-based and heuristic request classification.
- Demo web application behind the WAF.
- Automated attack simulation runner to compute TP, TN, FP, FN.
- Evaluation output files (CSV + JSON + markdown report).
- Dashboard for detections and latency visualization.
- Docker Compose setup for reproducible execution.

## Project Structure

- `waf_simulator.py`: Main WAF proxy and classifier service.
- `demo_app.py`: Demo backend application protected by the WAF.
- `dashboard.py`: Dashboard server for events and latency charts.
- `tools/evaluate.py`: Automated payload replay and metric generation.
- `Testing_Data/payloads_good.txt`: Benign payload list.
- `Testing_Data/payloads_bad.txt`: Malicious payload list.
- `docker-compose.yml`: Full multi-service orchestration.

## 1) Run Locally (without Docker)

### Install dependencies

```bash
pip install -r requirements.txt
```

If pip fails on Windows with `Preparing metadata (pyproject.toml)` for pandas/meson, use the minimal runtime dependencies above first. ML notebook/training dependencies are optional and moved to:

```bash
pip install -r requirements-ml-optional.txt
```

If you still need optional ML packages and see build-tool errors, create a Python 3.11 virtual environment (prebuilt wheels are more reliable):

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-ml-optional.txt
```

### Start backend demo app

```bash
python demo_app.py
```

### Start WAF service (new terminal)

```bash
python waf_simulator.py
```

### Start dashboard (new terminal)

```bash
python dashboard.py
```

Open:

- WAF: `http://localhost:8080`
- Demo app (direct): `http://localhost:5001`
- Dashboard: `http://localhost:8501`

## 2) Run Attack Evaluation

With WAF running, execute:

```bash
python tools/evaluate.py --base-url http://localhost:8080
```

Generated outputs:

- `Testing_Data/evaluation_results.csv`
- `Testing_Data/evaluation_summary.json`

## 3) Run with Docker Compose (recommended for submission)

Start all services:

```bash
docker compose up --build
```

Run evaluation runner container:

```bash
docker compose --profile eval run --rm test-runner
```

Stop services:

```bash
docker compose down
```

## Evaluation Metrics Produced

The evaluation script computes:

- Confusion matrix counts: TP, TN, FP, FN
- Accuracy
- Precision
- Recall
- F1 score
- Average request latency through WAF

## Suggested Demo Flow (for viva/presentation)

1. Open dashboard and show baseline traffic.
2. Send normal request to `/search?q=hello` and show ALLOWED.
3. Send malicious request to `/search?q=' OR 1=1 --` and show BLOCKED.
4. Run `tools/evaluate.py` and present generated TP/FP/FN numbers.

## Legacy Files

- `Proxy_server.py` and `log_parse.py` are retained from original implementation.
- The new simulation pipeline uses `waf_simulator.py` as the primary WAF runtime.


