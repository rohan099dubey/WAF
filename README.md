# Web Application Firewall (WAF) Simulation

This project contains a complete WAF simulation stack for an Internet Security project:

- WAF proxy with ML + heuristic detection
- Demo backend app behind WAF
- Monitoring dashboard (metrics/events/latency)
- Evaluation runner for confusion matrix + quality metrics

## Structured Layout

```text
src/
  apps/
    waf_simulator.py
    demo_app.py
    dashboard.py
  scripts/
    log_parse.py
  legacy/
    Proxy_server.py
models/
  training_model.pkl
data/
  raw/
    Data_Collection/
  testing/
  logs/
docs/
notebooks/
tools/
  evaluate.py
logs/
```

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start services in separate terminals:

```bash
python src/apps/demo_app.py
python src/apps/waf_simulator.py
python src/apps/dashboard.py
```

Open:

- WAF: `http://localhost:8080`
- Demo app: `http://localhost:5001`
- Dashboard: `http://localhost:8501`

## Run Evaluation

With WAF running:

```bash
python tools/evaluate.py --base-url http://localhost:8080
```

Generated outputs:

- `data/testing/evaluation_results.csv`
- `data/testing/evaluation_summary.json`
- `data/testing/evaluation_report.md`

## Docker Compose

Start all services:

```bash
docker compose up --build
```

Run evaluation container:

```bash
docker compose --profile eval run --rm test-runner
```

Stop:

```bash
docker compose down
```

## Notes

- Primary runtime files are in `src/apps/`.
- `src/legacy/Proxy_server.py` and `src/scripts/log_parse.py` are retained for reference.
