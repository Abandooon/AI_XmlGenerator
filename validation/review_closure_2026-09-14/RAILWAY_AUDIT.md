# Completed railway offline audit

The railway main study, second-model supplement and native checker recompilation passed on 2026-09-14. The scientific inputs are from public commit `26f1d19f8f6cce1e13616408d55abae896ecf1c8`. No new model generation or paid calls were made. The checks evaluate retained responses and artifacts; they do not regenerate the historical model responses.

## Executed checks

| Command | Observed result | Execution evidence |
| --- | --- | --- |
| [V05: railway main study](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v05) | PASS; 891 endpoints, including 888 with artifacts; zero discrepancies with historical outcomes | [Replay report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/RAILWAY_REPLAY.json) |
| [V06: second railway model](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v06) | PASS; all 24 tasks and 72 endpoints complete; 32 distinct native-validation groups; zero score mismatches | [Package report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/TERRA_REPLAY.json), [independent rescoring](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/TERRA_INDEPENDENT.json) |
| [V09: native recompilation](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v09) | PASS; 101 Java source files compile to 196 byte-identical class files across three project JARs | [Rebuild report](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/NATIVE_REBUILD.json) |
| [V15: rebuild verdict tests](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/COMMANDS.md#v15) | Three tests pass: matching bytes accepted; changed and missing class files rejected | [Test log](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/REBUILD_TESTS.txt) |

[Machine-readable summary](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/AUDIT_SUMMARY.json) records result and source hashes. The command list specifies repository-relative working directories and external output locations. Workstation runtime paths are omitted from the published Terra package report; its original report hash is recorded separately. Its scientific fields are unchanged.

## Recomputed results

| Study component | Conditions in order | Strict successes | Denominator per condition |
| --- | --- | --- | ---: |
| Railway generation and repair | G0 / GS / GF | 23 / 29 / 51 | 72 |
| Railway controlled rule faults | S / V / F | 129 / 140 / 141 | 144 |
| Railway task faults | S / V / F | 67 / 69 / 72 | 72 |
| Railway clean controls | S / V / F | 9 / 9 / 9 | 9 |
| Terra supplement | G0 / GS / GF | 18 / 22 / 22 | 24 |
| Matched Luna subset | G0 / GS / GF | 6 / 8 / 13 | 24 |

The main-study entry checks 30,965 payload files, replays retained generation and patch records, and verifies the artifact endpoints. Its 888 artifact-bearing endpoints include repeated XMI/identity pairs; there are 139 distinct pairs. Three endpoints have no artifact and remain in their denominators. The malformed-namespace negative control is rejected. All listed counts agree with the retained result records and the [experiment data index](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/EXPERIMENT_DATA.md).

The Terra entry reconstructs the unchanged original ZIP and checks all 9,433 package-manifest files. Its independent checker reads the final saved XMI directly and uses EMF/VIATRA and the task checks to rescore the 72 endpoints. It confirms the completed task set, paired results, received-response accounting and recorded budget reservations. It does not use a fresh generation or serialization step to create substitute artifacts.

## Native source and verdict check

The rebuild uses the retained Java model, matcher and runner sources. The three project JARs contain 3, 30 and 163 class files respectively; every recompiled class matches its retained counterpart byte for byte. No class is missing or different. Non-class resources are retained from the original JARs. This check does not rerun the Xcore/VQL code generators or rebuild third-party dependencies.

Review of the comparison script identified a verdict defect: missing classes caused failure, but a nonempty `different_classes` list did not. The current [rebuild entry](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/rebuild_native.py) now rejects both cases. The real recompilation was repeated with this stricter verdict and still passed. The [regression tests](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/test_rebuild_native.py) simulate compiler outputs to check the two failure paths as well as the passing path. No historical scoring rule, model output or result count was changed.

## Environment and evidence preservation

The executed environment was Windows, Python 3.12.14 and Temurin Java/Javac `1.8.0_504-b01`. The Java 8 ZIP was obtained from the [official Temurin release](https://github.com/adoptium/temurin8-binaries/releases/tag/jdk8u504-b01), with SHA-256 `ea43d46ede95b51e44a12c66711706cddc762e0a766c54bccea18954e902b2aa`. It was used as a local review runtime without changing the system Java installation. Runtime acquisition preceded the offline checks; the experiment checks made zero network or model calls.

Frozen archives, original reports, prompts, reference labels and generated artifacts retain their original bytes. Current documentation is in English, with [reading guides](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ENGLISH_REVIEW_GUIDE.md) for historical Chinese records. This directory adds a subsequent execution record; it does not overwrite earlier audit outcomes or submission documents.

The [documentation and data checks](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/validation/review_closure_2026-09-14/DOCUMENT_CHECKS.json) also confirm that all 332 re-aggregated metric records equal the retained report, the English navigation resolves to repository materials, and the AUTOSAR translation preserves all 20 case identifiers, nine hashes and nine official source links.
