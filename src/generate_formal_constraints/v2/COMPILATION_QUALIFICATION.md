# Constraint compilation qualification

The V2 compiler is fail-closed. A source assertion is marked `implemented`
only when its complete antecedent, consequence, exception set, scope, and XML
binding have been reviewed. Pattern recovery and the legacy SMT/SHACL assets
may contribute path evidence, but they cannot authorize promotion.

## Hybrid backend policy

- XSD validates schema order, XML types, and schema-native multiplicity.
- The typed native DSL validates local/conditional value, existence,
  cardinality, uniqueness, ordering, and reference rules without evaluating
  arbitrary Python, XPath, SPARQL, or prompt text.
- Reviewed Python plugins validate graph algorithms and cross-file AUTOSAR
  reference semantics.
- SMT is reserved for a closed-world, fully grounded finite relation; the old
  open-world template is not used as an authoritative pass/fail backend.
- SHACL may be used as a secondary RDF projection cross-check. It is not the
  authority for XML order, role wrappers, or short-name reference resolution.
- Assertions requiring generated code, runtime traces, ECU/A2L artifacts, or
  external design intent remain manual obligations.

## Current qualification result

The deterministic pipeline publishes 554 must-validation rules. All are
implemented and hash-qualified: 400 use reviewed Python semantic plugins and
154 use the reviewed typed DSL. There is no planned must-rule backlog.

The 51 manual-review obligations remain manual for their full normative claim:
they require generated artifacts, runtime/deployment evidence, external design
evidence, or explicit generation intent. Observable ARXML guards are not used
as substitutes for missing evidence.

Missing context, exact targets, parameters, reference closure, or external
evidence produces `NOT_EVALUATED`/`INCOMPLETE`, never a silent `PASS`.

## Validation output

Validation accumulates every finding across every rule and every well-formed
input document. Each finding carries file, line, XML path, constraint/rule
provenance, expected/actual evidence, and a structured repair action. The
top-level `repair.llm_prompt` instructs a repair model to apply all
non-conflicting actions and revalidate. If one or more input documents are
malformed, parser diagnostics are collected for every malformed document;
semantic evaluation waits until XML syntax is repairable.
