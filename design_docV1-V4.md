# Design Doc V4 — S²D²++ : Constraint‑Aware Multi‑Domain Model Generator

> **Goal upgrade @ V4**  Take the S²D² pipeline from a Section‑Level (JCR Q2) prototype to an SCI‑Q1‑ready, formally‑proved, security‑hardened, multi‑domain generator.

---

## 1 · Executive Summary

S²D²++ (V4) extends the original **S²D²** architecture with five tightly‑coupled innovations that jointly deliver:

* **Conceptual breakthrough** — proof‑carrying *constrained decoding* driven by a *type automaton*.
* **Formal correctness** — an LLM × SMT counter‑example feedback loop that guarantees convergent compliance.
* **Safety‑critical DevLoop** — static analysis, fuzzing, co‑simulation wired into the CI pipeline.
* **In‑place LLM Guardrails** — prompt/output filtering against injection, leakage, malicious code.
* **Cross‑metamodel generality** — one pipeline, three metamodels (AUTOSAR, OPC UA, DDS/HL7).

---

## 2 · Evolution Roadmap

| Version | Positioning              | Key Additions                                                               | Delivered Value                                          |
| ------- | ------------------------ | --------------------------------------------------------------------------- | -------------------------------------------------------- |
| **V1**  | Concept PoC              | 12 modules; KG + XSD + Drools → LLM → validation/repair                     | Closed‑loop *generate–validate–fix* prototype            |
| **V2**  | Unified Constraint Layer | **Constraint Graph**; CG‑Guided Decoding; SHACL; CI/Docker                  | *Generation‑time* hard constraints; DevOps ready         |
| **V3**  | High‑precision Knowledge | LLM‑assisted constraint extraction; human‑in‑the‑loop reviewer UI           | Knowledge correctness ↑; hallucination ↓                 |
| **V4**  | **SCI‑Q1 Launch**        | 5 innovations (type automaton, SMT loop, DevLoop, Guardrails, multi‑domain) | Formal guarantees, safety compliance, domain scalability |

---

## 3 · Key Innovations @ V4

| ID     | Innovation                                                                             | Why it matters (for Q1)                              | Implementation Sketch                                                                                                                                                                         | Success Metrics                                               |
| ------ | -------------------------------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **A1** | **Proof‑carrying Constrained Decoding**<br>Type Automaton (ℳ) embedded into LLM logits | Bridges *method → property → proof* gap              | ① Translate Constraint Graph to prefix‑closed DFA.<br>② Modify vLLM guided‑grammar backend to load DFA.<br>③ Provide *Theorem 1* (prefix monotonicity) & *Theorem 2* (decoding completeness). | One‑shot valid decode ≥ 95 % on 1k random specs.              |
| **A2** | **LLM × SMT Reactive Loop**                                                            | First cross‑domain use of Unsat Core feedback in MDE | Z3/CVC5 produces counter‑example → turned into incremental prompt for GPT‑4o → repeat until SAT.                                                                                              | Iterations ≤ 3, pass‑rate +15 pp over non‑reactive.           |
| **B3** | **Safety‑critical DevLoop**                                                            | Aligns with MISRA / ISO 26262 / FDA guidance         | Post‑gen hooks: cppcheck, pylint, AFL++ fuzz, CARLA/Simulink co‑sim.                                                                                                                          | MISRA violations ↓ 50 %, branch coverage > 85 %.              |
| **B4** | **Built‑in LLM Guardrails**                                                            | Hot topic (prompt injection & data leakage)          | Wrap GPT/vLLM endpoints with Rebuff; classify & block.                                                                                                                                        | False‑negative ≤ 5 %, false‑positive ≤ 10 %.                  |
| **C5** | **Cross‑Metamodel Generality**                                                         | “Once‑learn‑everywhere” ups novelty                  | Grammar auto‑compiler supports AUTOSAR 4.3.1, OPC UA 1.05, OMG DDS‑XML.                                                                                                                       | Class coverage ≥ 85 %, compile success ≥ 95 % across domains. |

---

## 4 · System Architecture

```
┌───────────────┐      ┌───────────────┐      ┌────────────────┐
│ Spec Prompt   │──┐   │ Type Automaton│◀──┐ │   Constraint   │
└───────────────┘  │   └───────────────┘   │ │    Graph       │
                   │                       │ └────────────────┘
                   ▼                       │
            ┌───────────────┐   counter‑ex ▼
            │   GPT‑4o      │──▶ SMT Solver ─┐
            └───────────────┘        ▲      │
                   │ JSON‑IR         │ sat/unsat
                   ▼                 │
            ┌───────────────┐ guided │
            │   vLLM 8B     │────────┘
            └───────────────┘
                   │ ARXML/XML
                   ▼
        Static Analysis + Fuzz + Simul.
                   │
                   ▼
           DevLoop Dashboard
```

* **Knowledge Layer** : Constraint Graph + SHACL ➜ Type Automaton.
* **Generation Layer (Dual‑LLM)** : GPT‑4o (planning) + vLLM (constrained emit).
* **Formal Layer** : SMT loop ensures fixed‑point satisfaction.
* **Assurance Layer** : Guardrails, static tools, fuzz & simulation.

---

## 5 · End‑to‑End Workflows

### 5.1 Option A (Recommended): *GPT‑4o → JSON‑IR → vLLM CGD*

1. **Prompt → JSON‑IR** via GPT‑4o *JSON‑mode*.
2. **Guided decoding** with vLLM (+GBNF from automaton).
3. **SMT loop** if first pass fails.
4. **DevLoop checks** → pass/fail badge.

### 5.2 Option B: *KG Query → Template Render*

Used as baseline & GPU‑less deployments.

---

## 6 · Verification & Validation Plan

| Layer              | Tool / Method                   | Pass Criterion             |
| ------------------ | ------------------------------- | -------------------------- |
| Syntax & Types     | vLLM DFA; `xmllint`             | Well‑formed + schema valid |
| Domain Constraints | SHACL; Z3 ‑→ Unsat Core         | `sat`                      |
| Static Safety      | cppcheck, pylint, MISRA‑checker | 0 critical findings        |
| Dynamic Safety     | AFL++ fuzz, CARLA/Simulink      | No crash; coverage > 85 %  |
| Security           | Rebuff policy                   | Leakage < 0.1 %            |

---

## 7 · Evaluation Metrics

* **One‑shot validity** (%)
* **Iteration count** (SMT loop)
* **MISRA violation density** (/kLOC)
* **Fuzz coverage** (%)
* **Guardrail FP / FN**
* **Cross‑domain ANOVA (p‑value)**

---

## 8 · 12‑Week Roadmap

| Week   | Deliverable                       | Acceptance Gate           |
| ------ | --------------------------------- | ------------------------- |
|  1‑3   | DFA compiler + SMT loop           | ≥ 90 % type‑check pass    |
|  4‑6   | AUTOSAR / OPC UA grammar          | Class coverage ≥ 85 %     |
|  7‑8   | DevLoop (cppcheck + fuzz + sim)   | MISRA ↓ 50 % vs hand‑code |
|  9‑10  | Stats scripts, threat model draft | ANOVA p < 0.05            |
|  11‑12 | Proof appendix; Docker+Zenodo     | Full artifact badge       |

---

## 9 · Risk & Mitigation

1. **Automaton state explosion** → sliced verification, on‑demand BFS prune.
2. **Guardrail over‑blocking** → adaptive threshold, allow‑list pass‑through.
3. **Metamodel heterogeneity** → Core‑MM abstraction; domain adapters as plugins.

---

## 10 · Artifact & Reproducibility

* **Repo** : GitHub → Zenodo DOI (tagged v4.0).
* **Docker** : `docker compose up` brings GPT‑4o stub, vLLM, Z3, analysis tools.
* **CI** : GitHub Actions — run full pipeline on every PR.
* **Supplement** : `appendix/proofs.pdf` (λ‑calculus & OCL), `smoke_demo.gif`.

---

### Appendix A · Sample DFA (snippet)

```bnf
<Start> ::= "<AUTOSAR>":<AUTOSAR-HEADER> <AR-PACKAGES>
<AR-PACKAGES> ::= "<AR-PACKAGES>" (<AR-PACKAGE>)+ "</AR-PACKAGES>"
...
```

---

> **V4 TL;DR** : *S²D²++ proves its outputs correct **while** generating them, enforces safety & security on every commit, and generalises to new metamodels with a single grammar swap—checking all three Q1 boxes: **concept depth, verification rigour, and broad applicability**.*
