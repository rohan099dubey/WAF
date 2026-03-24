Technical Architecture Specification: Web Application Firewall (WAF) Simulation

1. Abstract

This specification delineates the technical architecture and empirical validation of a high-fidelity Web Application Firewall (WAF) simulation designed to secure backend services against pervasive HTTP-based attack vectors. By synthesizing a hybrid detection methodology—integrating machine learning-based classification with a robust heuristic fallback engine—the system provides a resilient defense-in-depth intermediary. Operating as a reverse proxy, the system intercepts, analyzes, and logs traffic prior to backend execution. Quantitative analysis of the prototype confirms significant defensive efficacy, yielding a detection accuracy of 87.5% and a minimal processing overhead characterized by an average latency of 18.99 ms. This document serves as a blueprint for modular perimeter defense, balancing computational efficiency with rigorous security observability.

The necessity for such a framework is underscored by the evolving environmental pressures within modern web ecosystems, where the erosion of traditional network perimeters demands sophisticated, application-aware filtering.

2. Introduction and Problem Statement

In the contemporary threat landscape, perimeter-based security remains a strategic imperative for safeguarding the integrity of web-facing ecosystems. As organizations migrate toward highly distributed architectures, the exposure of backend business logic to unauthenticated public traffic creates a vast attack surface. Without a dedicated inspection layer, user-controlled inputs—delivered via query strings, headers, and request bodies—can be leveraged to exploit underlying software vulnerabilities.

The primary threats addressed by this architecture include SQL Injection (SQLi) and Cross-Site Scripting (XSS), which remain dominant in the OWASP Top 10. Direct backend exposure is a critical vulnerability because it assumes the implicit safety of incoming data, a premise that is frequently invalidated by sophisticated adversaries. A WAF serves as a vital intermediary filtering layer, neutralizing malicious payloads at the network edge. This simulation aims to provide a reproducible framework for evaluating the trade-offs between security strictness and operational performance.

The following sections transition from this general problem statement to the specific objectives and measurable goals defined for this architectural simulation.

3. Project Objectives and Scope

In security engineering, the definition of clear, measurable objectives is essential to moving from subjective protection to a quantifiable security posture. Establishing these parameters ensures that the system is not only functional but also defensible under academic and professional scrutiny.

The primary objectives of this simulation include:

- Reverse-Proxy Development: Implementing a functional security proxy capable of intercepting, inspecting, and routing HTTP traffic with high fidelity.
- Hybrid Detection Engine: Constructing a dual-layered classifier that utilizes machine learning for pattern recognition and heuristics to mitigate risks associated with model unavailability.
- Observability Dashboard: Developing a real-time visualization interface to provide strategic oversight of security events, system health, and traffic trends.
- Automated Evaluation Suite: Creating a reproducible testing framework to generate confusion-matrix-based metrics and performance benchmarks.

These objectives establish the structural framework required to achieve a resilient and observable security architecture.

4. High-Level System Architecture

The implementation of a "Security Proxy" architecture is a strategic necessity to ensure that security logic remains decoupled from core business logic. This separation of concerns allows for centralized policy enforcement and ensures that the backend application remains agnostic to the underlying inspection mechanisms.

4.1 Request Flow

For engineers navigating the system, the request lifecycle is defined as follows:

1. Client: Initiates an HTTP request (e.g., GET/POST) directed at the WAF listener.
2. WAF Engine: Intercepts the request, extracts lexical features from the path and body, and executes the hybrid classification logic.
3. Decision Point:

- If Malicious, the WAF terminates the request and returns an HTTP 403 (Forbidden) response.
- If Benign, the WAF reconstructs and forwards the request to the Backend.

4. Backend Application: Processes the validated request and returns the response to the WAF.
5. Observability: The WAF logs the final decision, updates in-memory counters, and feeds data to the Dashboard.

4.2 Primary Components and Port Assignments

The architecture is partitioned into persistent services and discrete CLI utilities:

Persistent Services:

- waf_simulator.py: The main security engine and proxy (Port 8080).
- demo_app.py: The protected target backend service (Port 5001).
- dashboard.py: The visualization and monitoring interface (Port 8501).

CLI Tools:

- tools/evaluate.py: An automated performance evaluation suite (No port assignment).

This structural overview provides the foundation for the granular logic that drives the WAF engine’s internal decision-making processes.

5. Technical Design Deep Dive

A multi-layered detection strategy is the most effective means of mitigating false negatives. By employing redundant analytical layers, the system ensures that even if one detection method is bypassed, the second serves as a safety net.

5.1 Reverse-Proxy Behavior

The WAF utilizes a high-fidelity proxying mechanism to ensure traffic transparency. Upon a "Benign" classification, the engine reconstructs the request for the backend by preserving the original HTTP method, query arguments, request body, and filtered headers. This ensures that the WAF remains invisible to the application logic while maintaining the integrity of the data stream.

5.2 Feature Extraction Strategy

The engine translates raw HTTP requests into numeric feature vectors. Lexical features were selected because they are computationally cheap and interpretable, providing high performance without the overhead of deep packet inspection or abstract syntax tree (AST) parsing.

Feature Category Indicators Extracted Rationale
SQLi Markers quotes (', "), dashes (--), ;, select, union, drop Detects attempts to break SQL syntax or execute unauthorized commands.
XSS Indicators Angle brackets (<, >), script keyword Identifies potential script injection and HTML tag manipulation.
Encodings Percent signs (%), symbols ($, &, |) Targets obfuscation techniques and command-injection attempts.
Structure Path length, body length, parentheses Analyzes anomalies in request size and structural complexity.

5.3 Hybrid Classifier

The system employs an "ML-first with heuristic fallback" strategy to address the risk of Distribution Shift—where the machine learning model encounters attack patterns it did not see during training—and to mitigate "model drift."

1. ML Mode: The engine attempts to load training_model.pkl. If available, it uses data-driven patterns to classify traffic.
2. Heuristic Fallback: If the model is absent, inference fails, or the distribution shift makes ML results uncertain, the system defaults to keyword-based detection. This ensures continuous security coverage and provides human-interpretable reasons for blocked traffic.

5.4 Logging and Metrics

System observability is anchored in a JSONL (JSON Lines) logging lifecycle. Every decision is recorded with associated metadata and latency. The WAF exposes /metrics for real-time counters and /events for recent decision logs, providing the data necessary for the dashboard's visualization layer.

This internal logic is realized through a modular implementation designed for maintainability and extensibility.

6. Implementation Component Breakdown

Modular software design facilitates independent security testing and isolated system maintenance, ensuring that updates to the detection engine do not disrupt the protected backend.

6.1 WAF Engine (waf_simulator.py)

As the core security component, the WAF Engine is configurable via environment variables (e.g., BACKEND_URL, WAF_LOG_FILE). It manages the lifecycle of every request, from extraction to the final block/allow decision.

6.2 Backend Application (demo_app.py)

This service acts as the "protected target," offering endpoints like /search, /login, and /product. Its primary role is to validate the WAF's pass-through capabilities; a successful search result for a benign query proves the proxy's fidelity.

6.3 Dashboard (dashboard.py)

The dashboard provides a strategic overview of system health. To ensure high availability of data, the dashboard employs a prioritized data acquisition strategy:

1. Primary: It attempts to parse the local JSONL log file for the most granular event history.
2. Fallback: If the log file is inaccessible, it queries the WAF APIs (/metrics and /events) directly.

Having implemented these components, the architecture requires quantitative validation to confirm its security posture.

7. Evaluation Methodology and Mathematical Metrics

In security engineering, quantitative validation is mandatory to move beyond anecdotal evidence. The evaluation suite replays datasets to determine the system's objective effectiveness.

7.1 Payload Replay Process

The evaluation suite utilizes two localized datasets:

- payloads_good.txt: Benign requests used to measure False Positives.
- payloads_bad.txt: Malicious injection strings used to measure detection Recall.

The tool replays these through the WAF and treats an HTTP 403 response as a "Blocked" decision and any other code as "Allowed."

7.2 Mathematical Framework

Performance is assessed via a Confusion Matrix, where True Positives (TP) are correctly blocked attacks, True Negatives (TN) are correctly allowed benign requests, False Positives (FP) are false alarms, and False Negatives (FN) are missed attacks.

Accuracy = \frac{TP + TN}{TP + TN + FP + FN} Precision = \frac{TP}{TP + FP} Recall = \frac{TP}{TP + FN} F1 = 2 \cdot \frac{Precision \cdot Recall}{Precision + Recall}

These formulas allow us to interpret the actual experimental data generated by the prototype.

8. Experimental Results and Interpretation

Analyzing empirical data is the final step in refining a security posture. The results below reflect a standardized run of the evaluation suite.

8.1 Performance Data

- Total Requests: 16
- TP: 6 | TN: 8 | FP: 0 | FN: 2

  8.2 Summary Metrics

Metric Value
Accuracy 0.875 (87.5%)
Precision 1.0 (100%)
Recall 0.75 (75%)
F1 Score 0.8571
Avg Latency 18.99 ms

8.3 Interpretation

- Precision (1.0): This is an ideal strategic outcome. A precision of 1.0 indicates zero false alarms, ensuring that legitimate business traffic is never disrupted by the security layer.
- Recall (0.75): While effective, the system missed 25% of the malicious payloads. These 2 False Negatives indicate that certain sophisticated or novel payloads bypassed the lexical features, suggesting a need for expanded rules or model retraining.
- Latency (18.99 ms): The minimal overhead confirms that the "Security Proxy" architecture is viable for real-time web traffic.

While these results are strong, they must be contextualized within the inherent risks of the system.

9. Security Analysis: Risks and Limitations

Technical honesty is a hallmark of professional architectural documentation. Identifying weaknesses is the first step toward remediation.

9.1 System Strengths

- End-to-End Observability: The integration of JSONL logs and real-time visualization allows for immediate incident response.
- Hybrid Fallback: The system is resilient to model drift or artifact loss, ensuring a baseline of protection is always active.

  9.2 Limitations and Risks

- Lexical Constraints: The current engine relies on text-based patterns and does not parse protocol semantics, making it vulnerable to semantic-aware attacks.
- Lack of Deobfuscation: The current prototype lacks a normalization layer; attackers could use complex encoding (e.g., nested Base64 or URL encoding) to evade detection.
- Static Intelligence: The ML model is static. Without an automated retraining pipeline, the system's detection capability will degrade as new attack variants emerge.
- False Negative Risk: The 2 missed attacks (FN) demonstrate that the current feature set is not exhaustive.

These limitations inform the future technical roadmap.

10. Future Enhancements

The development of security controls is an iterative process. The following roadmap is proposed to advance the prototype:

1. Signature/Rule Engine Integration: Incorporating established rule sets, such as the OWASP Core Rule Set (CRS), to supplement ML detection.
2. Automated Retraining Pipelines: Establishing a workflow to automatically retrain the ML model using new, verified logs to improve Recall.
3. Payload Normalization: Implementing a pre-processing stage to decode and deobfuscate payloads before they reach the classification engine.
4. Advanced Performance Benchmarking: Stress-testing the system to identify p99 latency and throughput limits under high-concurrency loads.

5. Conclusion

The WAF Simulation project successfully demonstrates a measurable and reproducible prototype for perimeter defense. By integrating machine learning with heuristic fallback logic within a reverse-proxy architecture, the system achieves a balanced security posture characterized by perfect precision and efficient latency. While the current recall gaps highlight the ongoing challenge of feature engineering, the prototype provides a robust, observable foundation for further research into automated threat mitigation and internet security architectures.

12. Appendix A: Viva Preparation (Q&A)

Q1: Why combine machine learning with heuristics? ML identifies complex, learned patterns, but it can fail due to distribution shift. Heuristics provide a reliable, interpretable fallback, ensuring the system remains functional even if the model is missing or the traffic deviates from the training set.

Q2: What is the risk of the 2 False Negatives in your results? False Negatives are missed attacks that reach the backend. In our tests, FN=2, meaning some malicious payloads were not caught. This indicates the need for more diverse feature extraction or a broader signature-based rule set.

Q3: How was WAF effectiveness measured? We used a confusion matrix to calculate accuracy, precision, recall, and F1 score. We also measured average latency to ensure that the security layer does not cause significant performance degradation for the user.

Q4: Is this system ready for a production environment? No. This is an academic simulation. A production-grade WAF requires TLS termination, full protocol semantics parsing, hardened deployment environments, and deep payload deobfuscation to handle real-world evasion techniques.

Q5: What is the key contribution of this architecture? The primary contribution is the creation of an end-to-end, measurable security pipeline that integrates detection, proxying, and real-time visualization into a single, reproducible stack.

13. Appendix B: Demo & Execution Guide

Local Execution (Three-Terminal Setup)

1. Terminal 1 (Backend): python demo_app.py
2. Terminal 2 (WAF): python waf_simulator.py
3. Terminal 3 (Dashboard): python dashboard.py
4. Evaluation: python tools/evaluate.py --base-url http://localhost:8080

Docker Compose Workflow

1. Build and Start: docker compose up --build
2. Run Evaluation: docker compose --profile eval run --rm test-runner
3. Shutdown: docker compose down

System URLs

- WAF Proxy (Interception Layer): http://localhost:8080
- Backend Application (Protected): http://localhost:5001
- Observability Dashboard: http://localhost:8501
