# Provenance conventions

1. **Frozen** means bytes copied from a retained historical source. The original manifest is authoritative for its original scope. An extract that excludes unrelated files identifies its selection rather than claiming to be the complete source archive.
2. **Corrected / offline / tools** identify reviewer replay code and corrections, including the current output-isolation changes. These files were not retrospectively used to produce the original model outputs.
3. **Verification results** describe checks executed on retained evidence. Offline replay does not regenerate a historical model response and cannot recover a missing response or audit tensor.
4. **Release manifest** binds the files in this branch's current tree. It is separate from each experiment's historical manifest. Git identifies the published branch commit. The current execution audit identifies the checked command and result for each review step.
5. Historical absolute paths in frozen records are provenance strings. Supported review entry points use package-relative paths and a caller-specified output directory. Old scripts with author-specific launch defaults remain marked historical where retained for source inspection.
6. New validation paths and timings can change report hashes while scientific outcomes and materialized artifact bytes agree. Each verifier states exactly which equality it establishes.
7. No environment secrets, model weights, unrelated IDE state or personal task histories are required for replay. Third-party runtime files retain their license and source attribution.

The AUTOSAR ZIP and one vLLM archive exclude author documents under the explicit [archive selection](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ARCHIVE_SELECTION.json). Original member bytes and original internal manifests are retained for every included experiment file. Railway and PIL selection inventories explain their curated export. The publication tree does not pool development probes, rejected early batches or withdrawn BESSER results into formal denominators. Removing unrelated current-tree files does not erase Git history.
