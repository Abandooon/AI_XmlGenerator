(set-logic ALL)
; SMT template for given constraints
; NOTE: Sorts and predicate signatures are declared here.
; Concrete XML-to-model binding is provided separately in mapping JSON.
; Do NOT add (check-sat) here.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Common Sort declarations
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(declare-sort RUNNABLE-ENTITY 0)
(declare-sort VARIABLE-ACCESS 0)

(declare-sort CLIENT-SERVER-INTERFACE 0)
(declare-sort NV-DATA-INTERFACE 0)
(declare-sort PARAMETER-INTERFACE 0)
(declare-sort SENDER-RECEIVER-INTERFACE 0)
(declare-sort MODE-SWITCH-INTERFACE 0)
(declare-sort TRIGGER-INTERFACE 0)

(declare-sort APPLICATION-COMPOSITE-DATA-TYPE 0)
(declare-sort APPLICATION-PRIMITIVE-DATA-TYPE 0)

(declare-sort SW-DATA-DEF-PROPS-CONTENT 0)
(declare-sort SW-BASE-TYPE 0)
(declare-sort COMPU-METHOD 0)
(declare-sort UNIT 0)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; TPS_SWCT_01323 - Read and write access to a dataElement
; (No precise logical constraint beyond structural access; omitted)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; Potential predicates (declared for completeness, but no core axiom)
(declare-fun has_dataReadAccess (RUNNABLE-ENTITY VARIABLE-ACCESS) Bool)
(declare-fun has_dataWriteAccess (RUNNABLE-ENTITY VARIABLE-ACCESS) Bool)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; TPS_SWCT_01004 - Default value if serviceKind is not defined
; If serviceKind is not defined, default value anyStandardized is assumed.
; This is a semantic default, not directly checkable from XML presence
; alone, so we model it as documentation only (no hard axiom).
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; We introduce an abstract enumeration sort for SERVICE-KIND
(declare-sort SERVICE-KIND 0)
(declare-const anyStandardized SERVICE-KIND)

; For each PortInterface kind, we assume a (partial) function giving
; the effective serviceKind (including defaulting).
(declare-fun serviceKindOf_CLIENT-SERVER-INTERFACE (CLIENT-SERVER-INTERFACE) SERVICE-KIND)
(declare-fun serviceKindDefined_CLIENT-SERVER-INTERFACE (CLIENT-SERVER-INTERFACE) Bool)

(declare-fun serviceKindOf_NV-DATA-INTERFACE (NV-DATA-INTERFACE) SERVICE-KIND)
(declare-fun serviceKindDefined_NV-DATA-INTERFACE (NV-DATA-INTERFACE) Bool)

(declare-fun serviceKindOf_PARAMETER-INTERFACE (PARAMETER-INTERFACE) SERVICE-KIND)
(declare-fun serviceKindDefined_PARAMETER-INTERFACE (PARAMETER-INTERFACE) Bool)

(declare-fun serviceKindOf_SENDER-RECEIVER-INTERFACE (SENDER-RECEIVER-INTERFACE) SERVICE-KIND)
(declare-fun serviceKindDefined_SENDER-RECEIVER-INTERFACE (SENDER-RECEIVER-INTERFACE) Bool)

(declare-fun serviceKindOf_MODE-SWITCH-INTERFACE (MODE-SWITCH-INTERFACE) SERVICE-KIND)
(declare-fun serviceKindDefined_MODE-SWITCH-INTERFACE (MODE-SWITCH-INTERFACE) Bool)

(declare-fun serviceKindOf_TRIGGER-INTERFACE (TRIGGER-INTERFACE) SERVICE-KIND)
(declare-fun serviceKindDefined_TRIGGER-INTERFACE (TRIGGER-INTERFACE) Bool)

; Core defaulting axioms (Info-level semantics)
(assert
  (forall ((p CLIENT-SERVER-INTERFACE))
    (=> (not (serviceKindDefined_CLIENT-SERVER-INTERFACE p))
        (= (serviceKindOf_CLIENT-SERVER-INTERFACE p) anyStandardized))))

(assert
  (forall ((p NV-DATA-INTERFACE))
    (=> (not (serviceKindDefined_NV-DATA-INTERFACE p))
        (= (serviceKindOf_NV-DATA-INTERFACE p) anyStandardized))))

(assert
  (forall ((p PARAMETER-INTERFACE))
    (=> (not (serviceKindDefined_PARAMETER-INTERFACE p))
        (= (serviceKindOf_PARAMETER-INTERFACE p) anyStandardized))))

(assert
  (forall ((p SENDER-RECEIVER-INTERFACE))
    (=> (not (serviceKindDefined_SENDER-RECEIVER-INTERFACE p))
        (= (serviceKindOf_SENDER-RECEIVER-INTERFACE p) anyStandardized))))

(assert
  (forall ((p MODE-SWITCH-INTERFACE))
    (=> (not (serviceKindDefined_MODE-SWITCH-INTERFACE p))
        (= (serviceKindOf_MODE-SWITCH-INTERFACE p) anyStandardized))))

(assert
  (forall ((p TRIGGER-INTERFACE))
    (=> (not (serviceKindDefined_TRIGGER-INTERFACE p))
        (= (serviceKindOf_TRIGGER-INTERFACE p) anyStandardized))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Constr_ApplicationCompositeDataType_SemanticMeaning
; Purely semantic statement: the composite type as a whole has no
; particular semantic meaning; semantics are on contained primitives.
; We model this as documentation only, no enforceable axiom.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; No SMT assertion generated.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Constr_ApplicationDataType_Precedence
; If an ApplicationDataType is referenced via valueAxisDataType,
; this supersedes CompuMethod, Unit, and BaseType if these are
; defined in parallel.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; Predicates indicating presence of the various references
(declare-fun has_valueAxisDataTypeRef (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun has_compuMethodRef (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun has_unitRef (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun has_baseTypeRef (SW-DATA-DEF-PROPS-CONTENT) Bool)

; Optional: functions giving the referenced objects (if present)
(declare-fun valueAxisDataTypeRef (SW-DATA-DEF-PROPS-CONTENT) APPLICATION-PRIMITIVE-DATA-TYPE)
(declare-fun compuMethodRef (SW-DATA-DEF-PROPS-CONTENT) COMPU-METHOD)
(declare-fun unitRef (SW-DATA-DEF-PROPS-CONTENT) UNIT)
(declare-fun baseTypeRef (SW-DATA-DEF-PROPS-CONTENT) SW-BASE-TYPE)

; Core precedence axiom:
; When valueAxisDataTypeRef is present, the others are superseded.
; We model this as mutual exclusion (cannot be defined in parallel).
(assert
  (forall ((x SW-DATA-DEF-PROPS-CONTENT))
    (=> (has_valueAxisDataTypeRef x)
        (and (not (has_compuMethodRef x))
             (not (has_unitRef x))
             (not (has_baseTypeRef x))))))

; End of SMT template (no (check-sat))
