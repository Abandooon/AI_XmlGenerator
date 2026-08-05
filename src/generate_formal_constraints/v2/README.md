# Formal Constraint Compiler V2

`compile_validation_plan.py` converts every curated constraint marked
`must_validate=true` into a versioned validation-plan rule. The current plan
contains 400 reviewed Python semantic rules and 154 reviewed typed-DSL rules;
all 554 are implemented. The compiler fails if a must-validate constraint has
no binding decision and never drops a constraint silently.

Assertions requiring runtime, deployment, generated-artifact, external, or
intent evidence remain explicit manual-review obligations rather than fake
static PASS/FAIL rules.

SHACL and SMT can still be used for suitable closed-world subsets, but they are
not the authoritative backend for ARXML reference graphs.  The primary backend
is the reference-aware Python runtime in `src/validation/v2`.
