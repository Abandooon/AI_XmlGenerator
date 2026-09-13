# Railway second-model study and offline review

This English reading guide covers the retained [study report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/%E5%AE%9E%E9%AA%8C%E5%AE%A1%E6%9F%A5%E6%8A%A5%E5%91%8A.md) and [offline-review note](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/%E7%A6%BB%E7%BA%BF%E5%A4%8D%E6%A0%B8%E8%AF%B4%E6%98%8E.md). Their original bytes are retained. The study was completed on 2026-09-10. Use the [current package entry](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/README.md) and [V06](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v06) for executable review instructions.

## Design and comparison

The supplement uses `gpt-5.6-terra` with low reasoning effort on all 24 predefined railway tasks and seed 104729. The task set and order were fixed in advance; tasks were not selected from Luna's failures. Temperature is 1, with strict structured output and non-streaming chat responses.

G0 is initial generation. GS is self-repair using the task and public rules without executed validation findings. GF is repair using validation feedback. GS and GF each start from their own model's shared G0 artifact, rather than from a Luna artifact. Both allow at most two repair proposals over the six permitted field categories.

GS may return `KEEP`; otherwise its last contract-valid selected candidate is evaluated. The policy does not retrospectively choose the most successful intermediate candidate. GF uses validation findings and rejects changes that violate its non-regression requirements. An initially successful G0 artifact is retained in GF without a repair call. The policies therefore need not make the same number of calls.

The Terra completion-token limit is 4,096, compared with 128,000 in the original Luna experiment. The historical Luna responses inspected when choosing the cap comprised 68 responses for the matched seed and 201 across all three seeds, with a maximum of 1,793 completion tokens. No received Terra response reached its cap. These observations establish the observed usage, not equivalence between the two cap settings.

## Results

All 24 tasks and 72 final endpoints are complete. Each condition has a denominator of 24.

| Model configuration | G0 | GS | GF |
| --- | ---: | ---: | ---: |
| Terra, low, seed 104729 | 18 | 22 | 22 |
| Luna, low, matched tasks and seed | 6 | 8 | 13 |

The [paired task records](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/paired_tasks.csv) and [current summary](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/CURRENT_RESULTS_SUMMARY.json) contain the underlying results.

Both Terra repair policies recover four of the six initial failures while retaining all 18 initial successes. Their final successful task sets are not identical.

| Paired conditions, first/second | Both fail | Only first succeeds | Only second succeeds | Both succeed |
| --- | ---: | ---: | ---: | ---: |
| G0 / GS | 2 | 0 | 4 | 18 |
| G0 / GF | 2 | 0 | 4 | 18 |
| GS / GF | 1 | 1 | 1 | 21 |

For the two declared statistical contrasts, the exact two-sided p value for G0 versus GF is 0.125 and its Holm-adjusted value is 0.25. The corresponding values for GS versus GF are both 1. No statistically established advantage of GF over GS follows from this supplement. The comparison across models is descriptive because it uses fixed task templates, one seed and different completion caps. The two models also have different initial failure sets.

### Remaining failures

The six initial Terra failures concern the `SemaphoreNeighbor` query. GS fails on BAL-3-06 after retaining the initial artifact with `KEEP`. On BAL-1-01, a passing first-round candidate is followed by a second-round candidate with a `ConnectedSegments` failure; the policy evaluates the last contract-valid candidate. Here `BUDGET_EXHAUSTED` refers to the two-round repair limit, not exhausted funding.

GF's remaining failures are BAL-2-02 and BAL-1-01, where proposed changes are rejected by non-regression requirements. Each policy therefore has one task that succeeds only under that policy. All final outcomes remain in their predefined denominators.

## Responses and token accounting

The completed study retains 60 received responses from 62 dispatches. Two dispatches have unknown provider usage. A separate pre-dispatch denial did not send a request and is not counted as a model failure or dispatch. The last task, BAL-3-01, required two received responses, for G0 and GS; GF retained the passing G0 artifact.

| Condition | Received responses | Input tokens | Completion tokens |
| --- | ---: | ---: | ---: |
| G0 | 24 | 108,161 | 16,184 |
| GS | 30 | 158,278 | 17,495 |
| GF | 6 | 35,395 | 2,925 |
| Total | 60 | 301,834 | 36,604 |

All received responses report `gpt-5.6-terra-2026-07-09`, a `stop` finish reason and content output, without a recorded refusal or truncation. The two missing responses cannot be characterized from their provider output. The largest received completion has 1,197 tokens, including 1,140 reasoning tokens, for BAL-1-08 GS round 1. The largest input has 5,976 tokens, for BAL-3-06 GF round 1. The largest recorded request body has 23,182 bytes. The [received-response table](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/reports/received_responses.csv) retains the individual observations.

### Historical budget and continuation records

The initial approved cap was USD 5. The missing-response dispatches were BAL-3-07 G0 and BAL-1-03 GS round 1. Each had one authorized retry with identical request bytes, while the reservation for the original dispatch remained recorded as unknown usage. Those reservations were USD 1.093728 each.

After 23 tasks were complete, the final task was denied before dispatch because the conservative occupied amount of USD 3.91646325 plus the next reservation would reach USD 5.01019125. An authorized extension raised the cap to USD 6 for the last task. The original ledger prefix and all completed task records were retained, with the extension recorded separately. No third replacement of a missing-response dispatch was introduced by that extension.

Each conservative pre-dispatch reservation used the declared upper input bound and completion cap: 272,000 × 3.75 / 1,000,000 + 4,096 × 18 / 1,000,000 = USD 1.093728. It was not reduced using shorter observed responses.

| Accounting quantity | USD |
| --- | ---: |
| Known usage, cache-component estimate | 1.790614500 |
| Reserved amount for two unknown dispatches | 2.187456000 |
| Known cache-component estimate plus unknown reserve | 3.978070500 |
| Conservative known-usage occupancy | 1.790749500 |
| Combined conservative occupancy | 3.978205500 |
| Known usage at base input/output rates | 1.564374000 |

These are client estimates and reservations, not a provider invoice. The retained historical basis is USD 3 per million ordinary input tokens, USD 0.3 for cache reads, USD 3.75 for cache writes and USD 18 for completion tokens, including reasoning. They are not a statement of current API prices.

## Domain sources and verification

The domain resource is Train Benchmark at commit `9c76520dec5a26213707b0e1f04b263f16b340ee`, described in the [Train Benchmark publication](https://doi.org/10.1007/s10270-016-0571-8). The 24 TaskSpec instances are author-designed synthetic tasks. Native EMF loading and VIATRA evaluation check the model with the six retained queries. Additional task checks cover object identities, permitted fields and non-regression. These task checks were implemented by the authors with LLM assistance.

The independent review evaluates the saved XMI directly. It does not reconstruct a replacement XMI through the generation serializer. The final 72 endpoints occupy 32 distinct groups defined by identical XMI, identity and fixed-task bytes. The retained review found zero score mismatches.

The eight source/plan and execution manifests respectively cover 2,087, 4, 749 and 69 preparation files, and 145, 830, 1,447 and 1,436 run files. An earlier assignment rejection for BAL-3-03 is represented as a known failed endpoint at that stage; missing-artifact states are not all treated as unknown infrastructure outcomes. The historical review also records ten structural tests and eight boundary tests.

## Offline package and current result locations

The archive retains four execution segments, their input and response evidence, unknown-usage and budget records, sources, the matched Luna subset, Java 8, and a portable Python 3.12.14 environment with lxml 6.1.1 and licenses. The current public entry executes the reviewer's selected runtime and writes to a new external directory. It does not import the generation runner or make model calls.

Within the reconstructed archive, `continuation3/run/RESULTS.json` is the completed result. The corresponding summary and tables are under `continuation3/delivery/`, and the independent checker is `review/continuation3/verify_final.py`. Reports from earlier 12-task or 23-task stages remain historical records; they are not the current completion status.

The original ZIP is 157,646,776 bytes with SHA-256 `3382364e8c94a361a496987633c34b8733086d8e074e77bc46f5b069d5e11a7e`. The review checks its 9,433 manifested files. The four public parts reconstruct this ZIP without changing its contents. Personal `.env`, provider configuration and credentials are not required for review. The Chinese basename in the original `PACKAGE_SHA256.txt` is a historical archive identifier; current retrieval follows [PARTS_MANIFEST.json](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway_terra/PARTS_MANIFEST.json).

For the completed independent execution on the public review tree, see the [railway audit](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/RAILWAY_AUDIT.md).
