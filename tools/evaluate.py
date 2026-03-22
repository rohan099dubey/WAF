import argparse
import csv
import json
import time
from pathlib import Path

import requests


def read_payloads(path: Path) -> list[str]:
    payloads = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            payloads.append(line)
    return payloads


def compute_metrics(rows: list[dict]) -> dict:
    tp = sum(1 for row in rows if row["label"] == "bad" and row["blocked"])
    tn = sum(1 for row in rows if row["label"] == "good" and not row["blocked"])
    fp = sum(1 for row in rows if row["label"] == "good" and row["blocked"])
    fn = sum(1 for row in rows if row["label"] == "bad" and not row["blocked"])

    total = len(rows)
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    avg_latency = sum(row["latency_ms"] for row in rows) / total if total else 0

    return {
        "total": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "avg_latency_ms": round(avg_latency, 2),
    }


def run_case(base_url: str, payload: str, label: str) -> dict:
    start = time.perf_counter()
    response = requests.get(
        f"{base_url.rstrip('/')}/search",
        params={"q": payload},
        timeout=8,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    blocked = response.status_code == 403
    return {
        "payload": payload,
        "label": label,
        "status_code": response.status_code,
        "blocked": blocked,
        "latency_ms": round(latency_ms, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WAF simulation evaluation")
    parser.add_argument("--base-url", default="http://localhost:8080", help="WAF URL")
    parser.add_argument("--good-file", default="Testing_Data/payloads_good.txt")
    parser.add_argument("--bad-file", default="Testing_Data/payloads_bad.txt")
    parser.add_argument("--output-csv", default="Testing_Data/evaluation_results.csv")
    parser.add_argument("--summary-json", default="Testing_Data/evaluation_summary.json")
    parser.add_argument("--report-md", default="Testing_Data/evaluation_report.md")
    args = parser.parse_args()

    good_payloads = read_payloads(Path(args.good_file))
    bad_payloads = read_payloads(Path(args.bad_file))

    rows: list[dict] = []
    for payload in good_payloads:
        rows.append(run_case(args.base_url, payload, "good"))
    for payload in bad_payloads:
        rows.append(run_case(args.base_url, payload, "bad"))

    output_csv_path = Path(args.output_csv)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["payload", "label", "status_code", "blocked", "latency_ms"],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = compute_metrics(rows)
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report_md = Path(args.report_md)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(
        "\n".join(
            [
                "# WAF Evaluation Report",
                "",
                f"- Total requests: {summary['total']}",
                f"- TP: {summary['tp']}",
                f"- TN: {summary['tn']}",
                f"- FP: {summary['fp']}",
                f"- FN: {summary['fn']}",
                f"- Accuracy: {summary['accuracy']}",
                f"- Precision: {summary['precision']}",
                f"- Recall: {summary['recall']}",
                f"- F1 score: {summary['f1_score']}",
                f"- Avg latency (ms): {summary['avg_latency_ms']}",
                "",
                "## Formula Reference",
                "",
                "- Precision = TP / (TP + FP)",
                "- Recall = TP / (TP + FN)",
                "- F1 = 2 * Precision * Recall / (Precision + Recall)",
            ]
        ),
        encoding="utf-8",
    )

    print("Evaluation complete")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
