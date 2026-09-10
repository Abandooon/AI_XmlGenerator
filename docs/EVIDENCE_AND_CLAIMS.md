# Evidence and claim boundaries

## AUTOSAR V20

This is the dynamic hosted-model pipeline: task analysis, admitted intermediate representation, domain knowledge and deterministic constraint assembly, structured generation, materialization and validation. Case-authored exact specifications and an existing interface catalogue are also inputs: the adapter binds precise objects, references and values. The case specification independently supplies the task acceptance expectations, rather than relying only on the model's plan. This study evaluates the complete supported workflow; it does not isolate extraction of these exact requirements from natural language or attribute upstream decisions to the final decoder.

The 60 accepted bundles contain 255 ARXML files and 675 references. Artifact-specific acceptance is distinct from full-corpus AUTOSAR compliance: all full-corpus verdicts are INCOMPLETE. The 100 repair cells contain 85 core and 15 substitution cases with controlled mutations and a previously accepted baseline. They do not estimate repair success on naturally occurring model failures. Historical pre-intervention Phase1 bodies and complete repair interaction bodies were not retained in the formal archive; final artifacts and retained records can be checked, but the entire original interaction cannot be replayed.

## Local vLLM–AUTOSAR V6.3.4

This is a separate Qwen3.5-9B study using vLLM 0.26 and xgrammar 0.2.6rc1 on two RTX 4090 GPUs. U/G/A share the model, prompts and schedule; G and A enable structured decoding, with A also collecting audit observations. The execution contracts are finite precompiled case contracts. This study is not a rerun of the V20 Phase1-plus-Neo4j pipeline.

The structural endpoint is 45/60, 60/60 and 60/60. G and A have identical retained outputs and token counts. At the case level, five cases improve, none worsen and fifteen tie; the two-sided sign-test p value is 0.0625. The audit records 516 bound steps among 54,942 evaluable steps (0.9392%). The retained booleans and hash chain can be checked; full historical logits and packed token masks were not stored. Mean elapsed time is U 13.5253 s, G 10.3650 s and A 13.2515 s; the A/G ratio indicates approximately 27.85% audit overhead in this setup. This is not a general productivity claim.

## PIL V4.1 and Erratum1

The formal denominator is 720 units. Endpoint counts for P0/P1/P2/P3 are 73/96/101/143 of 180. Gold compatibility alone is 74/102/105/144; delivery is 91/117/118/180; release is 180/178/180/176. These distinct quantities must not be interchanged. P3–P2 is +23.33 percentage points with the frozen bootstrap 95% CI [13.33, 33.89]; P3–P0 is +38.89 with CI [27.78, 50.00]. P1–P0 does not survive the original Holm adjustment, and P2–P1 is not a reliable isolated improvement.

The repair subset contains 40 gold-compatibility recoveries, 42 final narrow-endpoint successes among 62 repairs, and 58 releases. Three repaired answers introduce gold incompatibility. The narrow contract is not a complete substantive legal evaluator. The case-tailored knowledge base shares the same 60-case development corpus and uses 31 dependence clusters; this evidence does not estimate independent population-level legal accuracy.

Xinyue Yang designed the cases. The author confirmed that Xinyue Yang and Yirui Wang initially reviewed independently without viewing each other's judgments, then discussed disagreements; Codex assisted form filling. This confirmation is recorded as an author clarification, without fabricating historical signatures. The September 9 supplement contains three targeted post hoc assessments, leaving 717 of 720 outputs unreviewed by that supplement. Case19 has acceptable substantive reasoning with an ambiguous historical Boolean; case42 P1-R1 is unacceptable despite passing the narrow endpoint, and P3-R1 is conditionally acceptable. The clarified future field semantics were not used to generate the historical responses.

## Railway V5

There are 747 completed actions and 891 endpoints, including 888 endpoints with artifacts and 139 unique XMI byte sequences. The native replay checks both accepted and rejected artifacts; agreement with a recorded failure is not an artifact pass. Generation strict success is G0 23/72, GS 29/72 and GF 51/72. For repair, S/V/F are 129/144, 140/144 and 141/144; the +1 F-over-V result does not establish a robust incremental repair benefit. Task-obligation fault injection (T), including mistakenly disabled and mistakenly enabled services, yields S/V/F 67/69/72 of 72.

The 24 bases use three families and eight layouts with a shared ancestor, and were development-exposed. This supports bounded near-domain model-artifact workflow transfer, not arbitrary domain generalization, railway safety or Train Benchmark query-performance claims. The transport record has 1,085 send intents, 1,074 unique responses and 11 unknown outcomes/usage; unknown usage is not zero. Seventy inherited responses were not sent again.

## Railway second-model supplement

The completed Terra study retains all 24 predefined tasks and 72 known endpoints: G0/GS/GF 18/22/22 of 24. Both repair branches recover four of six initial failures, preserve all initial successes, and have one uniquely successful task each. The same-task, same-seed Luna subset is 6/8/13 of 24. Cross-model comparisons are descriptive, with different initial failure sets and different completion-token caps. They do not establish monotonically better repair with model capability.

The Terra internal GF–G0 and GF–GS Holm-adjusted p values are 0.25 and 1. No significant improvement over self-repair or equivalence is established. The 24/30/6 received responses for shared generation/GS additions/GF additions reflect feedback, acceptance and early-stopping policies jointly, not an isolated localization-efficiency effect. Sixty responses from 62 dispatches account for 338,438 known tokens; two unknown outcomes keep their reserves. The known cache-component cost estimate is USD 1.7906145 and conservative client occupancy USD 3.9782055, not a final provider invoice.

## Across tracks

Do not combine denominators or interpret cross-track rates as a model ranking. The release supports bounded artifact production, validation, failure localization and recorded repair behavior. It does not establish universal semantic correctness, production compliance, complete model necessity or human productivity gains.
