# Normative and query source checks

This source note identifies the AUTOSAR specifications and Train Benchmark query versions used by the experiments. It accompanies the retained inputs, code and outcomes without replacing them.

## AUTOSAR

[AUTOSAR_SOURCE_LOCATORS.json](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/reference_source_recheck/AUTOSAR_SOURCE_LOCATORS.json) gives the official R4.2.2 PDF URLs, verified title-page identities, page counts, SHA-256 values and checked pages. SWCT constr_1201 is on page 164; TPS_SWCT_01220 spans pages 164–165; TPS_SWCT_01519 is on page 485; explicit communication is described on pages 518–520. RTE sections 4.2.2.8, 4.3.1.5 and 5.6.4 begin on pages 122, 220 and 500. The original PDFs remain obtainable from the official URLs and are not redistributed here.

The [requirement source guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/AUTOSAR_REQUIREMENT_PROVENANCE_AND_DESIGN.md) identifies how these sources relate to the constructed cases. The [ICM evidence guide](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) follows TPS_SWCT_01519 through its retained constraint record, metamodel links and an executed event check.

## Train Benchmark

[TRAIN_QUERY_SOURCE.json](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/reference_source_recheck/TRAIN_QUERY_SOURCE.json) records the fixed official commit and query/runtime identities. [SwitchSet.vql](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/supporting/reference_source_recheck/SwitchSet.vql) is the byte-identical official query at [commit 9c76520](https://github.com/FTSRG/trainbenchmark/blob/9c76520dec5a26213707b0e1f04b263f16b340ee/trainbenchmark-tool-viatra-patterns/src/hu/bme/mit/trainbenchmark/benchmark/viatra/SwitchSet.vql#L7), with its original attribution. It requires `Route.active(route, true)`.

The Train Benchmark [publication](https://link.springer.com/article/10.1007/s10270-016-0571-8) mentions an active route in Section 3.4, while its Appendix 1.6 formula omits a separate active condition. The experiment follows the pinned official implementation. This note makes that source choice explicit; no query was modified for this recheck.

Inside [railway_evidence_05.zip](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/archives/railway_evidence_05.zip), inspect `frozen/workspace/authority/MANIFEST.json` and `frozen/workspace/authority/SwitchSet.vql`. The release lock `frozen/release/FORMAL_RELEASE.json` is in [railway_evidence_01.zip](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/archives/railway_evidence_01.zip). The [payload manifest](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/PAYLOAD_MANIFEST.json) records original archive members and hashes. The [native receipts](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/results/direct_native_receipts.zip) and [raw-artifact scorer](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/railway/corrected/raw_native_score.py) expose the actual evaluated condition.

Read-only diagnostics verified the stored SwitchSet results for 888 artifact-bearing Luna endpoints and confirmed the active condition using a pair of inputs differing only in that value. Comparing the two predicates on those retained endpoints gave no matching-set differences. This is a source/implementation check, not a new model experiment or a claim of general predicate equivalence; Terra endpoint statistics were not recomputed in this check.
