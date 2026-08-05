# ARXML Validator V2

This validator reads one or more ARXML files directly, builds a namespace-
agnostic reference and containment index, and executes the curated validation
plan.  Each rule returns exactly one of `PASS`, `FAIL`, `NOT_EVALUATED`, or
`ERROR`.

Important behavior:

- an applicable rule missing required intent, parameters, targets, reference
  closure, or external evidence returns `NOT_EVALUATED`;
- a rule requiring a complete cross-file reference scope returns
  `NOT_EVALUATED` when invoked with `--reference-scope partial`;
- unresolved or ambiguous references never become a silent pass;
- duplicate findings from dependent source constraints are merged while their
  full constraint provenance is preserved;
- process exit codes are 0 (pass), 1 (failure), 2 (incomplete), and 3 (engine
  error).

Run from the repository root with:

```powershell
python -m src.validation.v2.validate_arxml model.arxml `
  --plan src/generate_formal_constraints/v2/validation_plan.json `
  --reference-scope complete --output validation-report.json
```
