"""Rule-level reviewed native DSL specifications.

Every entry in this module was compared with the complete source assertion and
the AUTOSAR 4.2.2 XML role/path.  Absence from this catalog is deliberate: a
pattern-derived candidate is not an executable rule until it receives the same
review.
"""

from __future__ import annotations

from typing import Any


def _check(op: str, path: str | None, message: str, **values: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"op": op, "message": message, **values}
    if path is not None:
        item["path"] = path
    return item


def _spec(family: str, checks: list[dict], reason: str, selector: list[str]) -> dict[str, Any]:
    return {
        "language": "autosar-constraint-ir/1.0",
        "status": "reviewed",
        "coverage": "full",
        "rule_family": family,
        "checks": checks,
        "qualification_reason": reason,
        "reviewed_selector_tags": selector,
        "review_basis": "complete_source_assertion_and_autosar_4_2_2_xml_path",
    }


def reviewed_specs(title: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    def add(cid: str, family: str, selector: list[str], checks: list[dict], reason: str) -> None:
        result[cid] = _spec(family, checks, reason, selector)

    def add_service_need_table(
        cid: str,
        need_tags: list[str],
        port_roles: dict[str, tuple[int, int | None]],
        *,
        data_na: bool = True,
        represented_na: bool = True,
    ) -> None:
        antecedent_items = [
            {"path": f"SERVICE-NEEDS/{tag}", "exists": True}
            for tag in need_tags
        ]
        antecedent = antecedent_items[0] if len(antecedent_items) == 1 else {"any": antecedent_items}
        role_path = "ASSIGNED-PORTS/ROLE-BASED-PORT-ASSIGNMENT/ROLE"
        checks: list[dict] = []
        if port_roles:
            checks.append(_check(
                "value_domain", role_path, title,
                allowed=list(port_roles), when=antecedent,
            ))
            for role, (minimum, maximum) in port_roles.items():
                checks.append(_check(
                    "count_matching", role_path, title,
                    allowed=[role], min=minimum, max=maximum, when=antecedent,
                ))
        else:
            checks.append(_check("count", role_path, title, min=0, max=0, when=antecedent))
        if data_na:
            checks.append(_check(
                "count", "ASSIGNED-DATAS/ROLE-BASED-DATA-ASSIGNMENT", title,
                min=0, max=0, when=antecedent,
            ))
        if represented_na:
            checks.append(_check(
                "forbidden", "REPRESENTED-PORT-GROUP-REF", title, when=antecedent,
            ))
        add(
            cid, "cardinality", ["SWC-SERVICE-DEPENDENCY"], checks,
            "The ServiceNeeds subtype is the observable use-case antecedent; all listed role domains and multiplicities are encoded.",
        )

    def add_intent_service_table(
        cid: str,
        port_roles: dict[str, tuple[int, int | None]] | None,
        *,
        need_tag: str | None = None,
        data_roles: dict[str, tuple[int, int | None]] | None = None,
        data_na: bool = True,
        represented: tuple[int, int | None] | None = (0, 0),
    ) -> None:
        """Compile a complete CID-100 service-use-case table.

        Several tables share the same ServiceNeeds subtype, and several have
        no subtype discriminator at all.  They are executable only for an
        exact SwcServiceDependency path explicitly bound in the signed
        validation-context manifest.
        """
        checks: list[dict] = []
        if need_tag:
            checks.append(_check("exists", f"SERVICE-NEEDS/{need_tag}", title))

        def add_roles(
            path: str,
            roles: dict[str, tuple[int, int | None]] | None,
        ) -> None:
            if roles is None:
                checks.append(_check("count", path.rsplit("/", 1)[0], title, min=0, max=0))
                return
            checks.append(_check("value_domain", path, title, allowed=list(roles)))
            for role, (minimum, maximum) in roles.items():
                checks.append(_check(
                    "count_matching", path, title,
                    allowed=[role], min=minimum, max=maximum,
                ))

        add_roles(
            "ASSIGNED-PORTS/ROLE-BASED-PORT-ASSIGNMENT/ROLE",
            port_roles,
        )
        if data_roles is not None or data_na:
            add_roles(
                "ASSIGNED-DATAS/ROLE-BASED-DATA-ASSIGNMENT/ROLE",
                data_roles,
            )
        if represented is not None:
            checks.append(_check(
                "count", "REPRESENTED-PORT-GROUP-REF", title,
                min=represented[0], max=represented[1],
            ))
        add(
            cid, "cardinality", ["SWC-SERVICE-DEPENDENCY"], checks,
            "The complete normative CID-100 role table is encoded and is gated by an exact manifest target.",
        )
        result[cid]["activation"] = {
            "requires_validation_context": True,
            "requires_declared_constraint": True,
            "requires_declared_targets": True,
        }
        result[cid]["review_basis"] = (
            "normative_cid100_table_and_autosar_4_2_2_xml_paths_with_exact_target_binding"
        )

    # Closed value domains.
    add("constr_1014", "value_domain", ["SW-BASE-TYPE"], [
        _check("value_domain", "BASE-TYPE-ENCODING", title, allowed=[
            "1C", "2C", "BCD-P", "BCD-UP", "DSP-FRACTIONAL", "SM", "IEEE754",
            "ISO-8859-1", "ISO-8859-2", "WINDOWS-1252", "UTF-8", "UTF-16",
            "UCS-2", "NONE", "VOID", "BOOLEAN",
        ]),
    ], "The source enumerates the complete BaseType encoding domain.")
    add("TPS_SWCT_01010", "value_domain", ["MODE-DECLARATION-GROUP"], [
        _check("value_domain", "CATEGORY", title, allowed=["EXPLICIT_ORDER", "ALPHABETIC_ORDER"]),
    ], "The two permitted ModeDeclarationGroup categories are explicit.")

    policy_rules = {
        "constr_2035": (["VARIABLE-DATA-PROTOTYPE"], ["STANDARD", "QUEUED", "MEASUREMENT-POINT"], {"ancestor_tags": ["SENDER-RECEIVER-INTERFACE"]}),
        "constr_2036": (["VARIABLE-DATA-PROTOTYPE"], ["STANDARD"], {"ancestor_tags": ["NV-DATA-INTERFACE"]}),
        "constr_2037": (["RAM-BLOCK"], ["STANDARD"], {}),
        "constr_2038": (["VARIABLE-DATA-PROTOTYPE"], ["STANDARD"], {"ancestor_tags": ["IMPLICIT-INTER-RUNNABLE-VARIABLES"]}),
        "constr_2039": (["VARIABLE-DATA-PROTOTYPE"], ["STANDARD"], {"ancestor_tags": ["EXPLICIT-INTER-RUNNABLE-VARIABLES"]}),
        "constr_2040": (["VARIABLE-DATA-PROTOTYPE"], ["STANDARD", "MEASUREMENT-POINT"], {"ancestor_tags": ["AR-TYPED-PER-INSTANCE-MEMORYS"]}),
        "constr_2041": (["VARIABLE-DATA-PROTOTYPE"], ["STANDARD", "MEASUREMENT-POINT", "MESSAGE"], {"ancestor_tags": ["STATIC-MEMORYS"]}),
        "constr_2042": (["PARAMETER-DATA-PROTOTYPE"], ["STANDARD", "CONST", "FIXED"], {"ancestor_tags": ["PARAMETER-INTERFACE"]}),
        "constr_2044": (["PARAMETER-DATA-PROTOTYPE"], ["STANDARD"], {"ancestor_tags": ["SHARED-PARAMETERS"]}),
        "constr_2047": (["ARGUMENT-DATA-PROTOTYPE"], ["STANDARD"], {}),
        "constr_2048": (["SW-SERVICE-ARG"], ["STANDARD", "CONST"], {}),
    }
    for cid, (selector, allowed, when) in policy_rules.items():
        check = _check(
            "value_domain",
            "SW-IMPL-POLICY",
            title,
            allowed=allowed,
            search="descendant",
        )
        if when:
            check["when"] = when
        add(cid, "value_domain", selector, [check], "The complete role-specific swImplPolicy domain is explicit.")

    # Profile-specific EndToEndDescription numeric rules.
    def profile_check(path: str, minimum: int, maximum: int, profile: str, *, modulo: int | None = None) -> list[dict]:
        when = {"path": "CATEGORY", "equals": profile}
        checks = [_check("numeric_range", path, title, min=minimum, max=maximum, when=when)]
        if modulo is not None:
            checks.append(_check("numeric_modulo", path, title, modulus=modulo, remainder=0, when=when))
        return checks

    add("constr_1111", "value_range", ["END-TO-END-DESCRIPTION"], [
        _check("count", "DATA-IDS/DATA-ID", title, min=1, max=1, when={"path": "CATEGORY", "equals": "PROFILE_01"}),
        *profile_check("DATA-IDS/DATA-ID", 0, 65535, "PROFILE_01"),
    ], "PROFILE_01 cardinality and closed numeric range are both explicit.")
    add("constr_1112", "value_range", ["END-TO-END-DESCRIPTION"], profile_check("DATA-ID-MODE", 0, 3, "PROFILE_01"), "The conditional numeric range is explicit.")
    add("constr_1114", "value_range", ["END-TO-END-DESCRIPTION"], profile_check("CRC-OFFSET", 0, 65535, "PROFILE_01", modulo=4), "Both range and divisibility are encoded.")
    add("constr_1115", "value_range", ["END-TO-END-DESCRIPTION"], profile_check("COUNTER-OFFSET", 0, 65535, "PROFILE_01", modulo=4), "Both range and divisibility are encoded.")
    add("constr_1116", "value_range", ["END-TO-END-DESCRIPTION"], profile_check("DATA-LENGTH", 0, 240, "PROFILE_01", modulo=8), "Both range and divisibility are encoded.")
    add("constr_1119", "value_range", ["END-TO-END-DESCRIPTION"], profile_check("DATA-LENGTH", 0, 65535, "PROFILE_02", modulo=8), "Both range and divisibility are encoded.")
    add("constr_1120", "value_range", ["END-TO-END-DESCRIPTION"], [
        _check("count", "DATA-IDS/DATA-ID", title, min=16, max=16, when={"path": "CATEGORY", "equals": "PROFILE_02"}),
        *profile_check("DATA-IDS/DATA-ID", 0, 255, "PROFILE_02"),
    ], "PROFILE_02 cardinality and closed numeric range are both explicit.")

    add("TPS_SWCT_01006", "required_existence", ["IMPLEMENTATION-DATA-TYPE"], [
        _check(
            "exists",
            "SUB-ELEMENTS/IMPLEMENTATION-DATA-TYPE-ELEMENT/ARRAY-SIZE",
            title,
            when={"path": "CATEGORY", "equals": "ARRAY"},
        ),
    ], "An ARRAY ImplementationDataType must serialize arraySize on its subElement.")
    add("constr_1178", "mutual_exclusion", ["SW-DATA-DEF-PROPS-CONDITIONAL"], [{
        "op": "mutually_exclusive",
        "paths": ["BASE-TYPE-REF", "SW-POINTER-TARGET-PROPS", "IMPLEMENTATION-DATA-TYPE-REF"],
        "max_present": 1,
        "when": {"ancestor_tags": ["IMPLEMENTATION-DATA-TYPE"]},
        "message": title,
    }], "The three alternatives and their ImplementationDataType containment scope are explicit.")
    add("constr_1388", "mutual_exclusion", ["VARIATION-POINT-PROXY"], [{
        "op": "mutually_exclusive",
        "paths": ["VALUE-ACCESS", "POST-BUILD-VALUE-ACCESS-REF"],
        "max_present": 1,
        "when": {"path": "CATEGORY", "equals": "VALUE"},
        "message": title,
    }], "The VALUE category antecedent and pre-build/post-build value alternatives are explicit.")

    add("constr_1105", "value_range", ["IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"], [
        _check("numeric_range", "ARRAY-SIZE", title, min=0, max=None, min_exclusive=True, search="descendant", when={"path": "CATEGORY", "equals": "ARRAY"}),
    ], "The ARRAY category antecedent and strict positive bound are explicit.")
    add("constr_1264", "value_range", ["SW-RECORD-LAYOUT-V"], [
        _check("value_domain", "SW-RECORD-LAYOUT-V-INDEX", title, forbidden=["0"], when={"path": "CATEGORY", "not_in": ["VALUE", "VAL_BLK"]}),
    ], "The complete category exception and forbidden index value are encoded.")

    # Conditional existence/applicability rules whose antecedent and full
    # consequence are both represented in the same XML object subtree.
    add("constr_1113", "conditional_existence", ["END-TO-END-DESCRIPTION"], [
        _check("exists", "DATA-LENGTH", title, when={"path": "CATEGORY", "equals": "PROFILE_01"}),
        _check("exists", "DATA-IDS/DATA-ID", title, when={"path": "CATEGORY", "equals": "PROFILE_01"}),
    ], "Both mandatory PROFILE_01 properties are encoded.")
    add("constr_1261", "conditional_existence", ["END-TO-END-DESCRIPTION"], [
        _check("forbidden", "DATA-ID-NIBBLE-OFFSET", title, when={"not": {"all": [
            {"path": "DATA-ID-MODE", "equals": "3"},
            {"path": "CATEGORY", "equals": "PROFILE_01"},
        ]}}),
    ], "The only-if antecedent is encoded as a prohibition outside the complete condition.")
    add("constr_1398", "conditional_existence", ["SW-BASE-TYPE"], [
        _check("exists", "BYTE-ORDER", title, search="descendant", when={"path": "BASE-TYPE-ENCODING", "equals": "UTF-16"}),
        _check("value_domain", "BYTE-ORDER", title, search="descendant", when={"path": "BASE-TYPE-ENCODING", "equals": "UTF-16"}, allowed=[
            "MOST-SIGNIFICANT-BYTE-FIRST", "MOST-SIGNIFICANT-BYTE-LAST",
        ]),
    ], "The UTF-16 antecedent, existence, and restricted byte-order domain are encoded.")
    add("constr_1175", "conditional_existence", ["COMPU-METHOD"], [
        _check("exists", "UNIT-REF", title, when={"path": "CATEGORY", "not_in": [
            "TEXTTABLE", "BITFIELD_TEXTTABLE", "IDENTICAL",
        ]}),
    ], "The complete exception set and required unit reference are explicit.")
    add("constr_1146", "conditional_existence", ["COMPU-METHOD"], [
        _check("forbidden", "SYMBOL", title, search="descendant", when={"path": "CATEGORY", "not_in": [
            "SCALE_LINEAR_AND_TEXTTABLE", "SCALE_RATIONAL_AND_TEXTTABLE",
            "TEXTTABLE", "BITFIELD_TEXTTABLE",
        ]}),
    ], "CompuScale symbols are prohibited outside the complete category allow-list.")
    add("constr_2058", "conditional_existence", ["APPLICATION-RULE-BASED-VALUE-SPECIFICATION"], [
        _check("exists", "SW-ARRAYSIZE", title, search="descendant", when={"all": [
            {"path": "CATEGORY", "in": ["CURVE", "MAP", "CUBOID", "CUBE_4", "CUBE_5", "COM_AXIS", "RES_AXIS", "CURVE_AXIS", "VAL_BLK", "ARRAY"]},
            {"path": "RULE-BASED-VALUE-CONT", "exists": True, "search": "descendant"},
        ]}),
    ], "All triggering categories and the required swArraysize are encoded.")
    add("constr_2051", "conditional_existence", ["APPLICATION-VALUE-SPECIFICATION"], [
        _check("exists", "SW-ARRAYSIZE", title, search="descendant", when={"all": [
            {"path": "CATEGORY", "in": ["CURVE", "MAP", "CUBOID", "CUBE_4", "CUBE_5", "COM_AXIS", "RES_AXIS", "VAL_BLK"]},
            {"path": "SW-VALUE-CONT", "exists": True, "search": "descendant"},
        ]}),
    ], "All triggering categories and the required swArraysize are encoded.")
    add("constr_1363", "conditional_existence", ["DIAGNOSTIC-VALUE-NEEDS"], [
        _check("forbidden", "DIAGNOSTIC-VALUE-ACCESS", title, when={"ancestor_tags": ["SERVICE-NEEDS"]}),
        _check("forbidden", "DATA-LENGTH", title, when={"ancestor_tags": ["SERVICE-NEEDS"]}),
    ], "Both prohibited properties and the serviceNeeds containment antecedent are encoded.")
    add("constr_1364", "conditional_existence", ["DIAGNOSTIC-IO-CONTROL-NEEDS"], [
        _check("forbidden", "FREEZE-CURRENT-STATE-SUPPORTED", title, when={"ancestor_tags": ["SERVICE-NEEDS"]}),
        _check("forbidden", "SHORT-TERM-ADJUSTMENT-SUPPORTED", title, when={"ancestor_tags": ["SERVICE-NEEDS"]}),
    ], "Both prohibited properties and the serviceNeeds containment antecedent are encoded.")
    add("TPS_SWCT_01532", "conditional_existence", ["MODE-ERROR-BEHAVIOR"], [
        _check("exists", "DEFAULT-MODE-REF", title, when={"path": "ERROR-REACTION-POLICY", "equals": "DEFAULT-MODE"}),
    ], "The error policy antecedent and required mode reference are explicit.")
    add("TPS_SWCT_01370", "conditional_existence", ["VARIATION-POINT-PROXY"], [
        _check("exists", "POST-BUILD-VALUE-ACCESS-REF", title, when={"path": "POST-BUILD-VARIANT-CONDITIONS/POST-BUILD-VARIANT-CONDITION", "exists": True}),
        _check("exists", "POST-BUILD-VARIANT-CONDITIONS/POST-BUILD-VARIANT-CONDITION", title, when={"path": "POST-BUILD-VALUE-ACCESS-REF", "exists": True}),
    ], "A functional post-build variation is observable and requires both post-build operands.")
    add("constr_1118", "conditional_existence", ["END-TO-END-DESCRIPTION"], [
        *[
            _check("forbidden", path, title, when={"path": "CATEGORY", "equals": "PROFILE_02"})
            for path in (
                "DATA-ID-MODE", "MAX-DELTA-COUNTER-INIT", "CRC-OFFSET",
                "COUNTER-OFFSET", "MAX-NO-NEW-OR-REPEATED-DATA",
                "SYNC-COUNTER-INIT", "DATA-ID-NIBBLE-OFFSET",
            )
        ],
    ], "Every EndToEndDescription property excluded by the PROFILE_02 allow-list is prohibited.")
    add("constr_1310", "conditional_existence", ["SWC-SERVICE-DEPENDENCY"], [
        _check(
            "count_matching",
            "ASSIGNED-PORTS/ROLE-BASED-PORT-ASSIGNMENT/ROLE",
            title,
            min=1,
            max=None,
            allowed=["NvDataPort"],
            when={"all": [
                {"path": "SERVICE-NEEDS/NV-BLOCK-NEEDS", "exists": True},
                {"any": [
                    {"path": f"SERVICE-NEEDS/NV-BLOCK-NEEDS/{path}", "exists": True}
                    for path in (
                        "STORE-CYCLIC", "CYCLIC-WRITING-PERIOD",
                        "STORE-EMERGENCY", "STORE-IMMEDIATE",
                    )
                ]},
            ]},
        ),
    ], "The NvBlockNeeds antecedent, four guarded properties, and NvDataPort role are explicit.")
    add("constr_2053", "conditional_existence", ["SWC-SERVICE-DEPENDENCY"], [
        _check(
            "count_matching",
            "ASSIGNED-PORTS/ROLE-BASED-PORT-ASSIGNMENT/ROLE",
            title,
            min=1,
            max=None,
            allowed=["IUMPRNumerator"],
            when={"path": "SERVICE-NEEDS/OBD-RATIO-SERVICE-NEEDS/CONNECTION-TYPE", "equals": "API-USE"},
        ),
        _check(
            "count_matching",
            "ASSIGNED-PORTS/ROLE-BASED-PORT-ASSIGNMENT/ROLE",
            title,
            min=0,
            max=0,
            allowed=["IUMPRNumerator"],
            when={"path": "SERVICE-NEEDS/OBD-RATIO-SERVICE-NEEDS/CONNECTION-TYPE", "equals": "OBSERVER"},
        ),
    ], "Both connectionType branches and the IUMPRNumerator multiplicity are encoded.")

    # Required and forbidden model structure.
    add("constr_1201", "required_existence", ["NONQUEUED-RECEIVER-COM-SPEC"], [
        _check("exists", "INIT-VALUE", title, when={"ancestor_tags": ["R-PORT-PROTOTYPE"]}),
    ], "The R-port containment antecedent and required child are observable.")
    add("constr_1093", "required_existence", ["APPLICATION-PRIMITIVE-DATA-TYPE"], [
        _check("exists", "SW-TEXT-PROPS", title, search="descendant", when={"path": "CATEGORY", "equals": "STRING"}),
        _check("exists", "ARRAY-SIZE-SEMANTICS", title, search="descendant", when={"path": "CATEGORY", "equals": "STRING"}),
        _check("exists", "SW-MAX-TEXT-SIZE", title, search="descendant", when={"path": "CATEGORY", "equals": "STRING"}),
    ], "All three consequences for category STRING are encoded.")
    for cid, category in (("constr_1106", "STRUCTURE"), ("constr_1107", "UNION")):
        add(cid, "required_existence", ["IMPLEMENTATION-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE-ELEMENT"], [
            _check("count", "IMPLEMENTATION-DATA-TYPE-ELEMENT", title, min=1, max=None, search="descendant", when={"path": "CATEGORY", "equals": category}),
        ], f"The {category} antecedent and non-empty sub-element obligation are explicit.")
    add("TPS_SWCT_01363", "required_existence", ["PER-INSTANCE-MEMORY"], [
        _check("exists", "TYPE", title),
        _check("exists", "TYPE-DEFINITION", title),
    ], "Both required PerInstanceMemory attributes are explicitly stated.")

    add("constr_1200", "forbidden_existence", ["PR-PORT-PROTOTYPE"], [
        _check("value_domain", "SW-IMPL-POLICY", title, forbidden=["QUEUED"], search="descendant"),
    ], "All data elements owned by the PR port are within its subtree.")
    add("constr_1241", "forbidden_existence", ["APPLICATION-PRIMITIVE-DATA-TYPE"], [
        _check("forbidden", "INVALID-VALUE", title, search="descendant", when={"path": "CATEGORY", "not_equals": "STRING"}),
    ], "The category antecedent and forbidden property are explicit.")
    add("constr_1244", "forbidden_existence", [
        "APPLICATION-SW-COMPONENT-TYPE", "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
        "ECU-ABSTRACTION-SW-COMPONENT-TYPE", "NV-BLOCK-SW-COMPONENT-TYPE",
        "SENSOR-ACTUATOR-SW-COMPONENT-TYPE", "SERVICE-PROXY-SW-COMPONENT-TYPE",
        "SERVICE-SW-COMPONENT-TYPE",
    ], [
        _check("value_domain", "ADDITIONAL-NATIVE-TYPE-QUALIFIER", title, forbidden=["enum", "ENUM"], search="descendant"),
    ], "Atomic component ownership is represented by XML containment.")
    add("TPS_SWCT_01097", "forbidden_existence", ["COMPOSITION-SW-COMPONENT-TYPE"], [
        _check("forbidden", "SWC-INTERNAL-BEHAVIOR", title, search="descendant"),
        _check("forbidden", "RUNNABLE-ENTITY", title, search="descendant"),
    ], "Composition ownership and both forbidden structures are observable.")

    # Service-needs tables with a unique, observable ServiceNeeds subtype.
    # Tables sharing the same subtype across indistinguishable use cases are
    # deliberately excluded because absence cannot be judged from ARXML alone.
    service_tables = {
        "TPS_SWCT_02505": (["FUNCTION-INHIBITION-NEEDS"], {"FunctionInhibition": (1, 1)}),
        "TPS_SWCT_01132": (["DIAGNOSTIC-OPERATION-CYCLE-NEEDS"], {"OperationCycle": (1, 1)}),
        "TPS_SWCT_01134": (["DIAGNOSTIC-ENABLE-CONDITION-NEEDS"], {"EnableCondition": (1, 1)}),
        "TPS_SWCT_01135": (["DIAGNOSTIC-STORAGE-CONDITION-NEEDS"], {"StorageCondition": (1, 1)}),
        "TPS_SWCT_01140": (["DTC-STATUS-CHANGE-NOTIFICATION-NEEDS"], {"CallbackDTCStatusChange": (1, 1)}),
        "TPS_SWCT_02004": (["DIAGNOSTIC-ROUTINE-NEEDS"], {"RoutineServices": (1, 1)}),
        "TPS_SWCT_02015": (["DIAGNOSTICS-COMMUNICATION-SECURITY-NEEDS"], {"SecurityAccess": (1, 1)}),
        "TPS_SWCT_02010": (["OBD-INFO-SERVICE-NEEDS"], {"InfotypeServices": (1, 1)}),
        "TPS_SWCT_02011": (["OBD-MONITOR-SERVICE-NEEDS"], {"DTRCentralReport": (1, 1)}),
        "TPS_SWCT_02012": (["OBD-CONTROL-SERVICE-NEEDS"], {"RequestControlServices": (1, 1)}),
        "TPS_SWCT_01537": (["DO-IP-GID-SYNCHRONIZATION-NEEDS"], {"CallbackTriggerGIDSynchronization": (1, 1)}),
        "TPS_SWCT_01538": (["DO-IP-GID-NEEDS"], {"CallbackGetGID": (1, 1)}),
        "TPS_SWCT_01539": (["DO-IP-POWER-MODE-STATUS-NEEDS"], {"CallbackGetPowerMode": (1, 1)}),
        "TPS_SWCT_01540": (["DO-IP-ROUTING-ACTIVATION-AUTHENTICATION-NEEDS", "DO-IP-ROUTING-ACTIVATION-CONFIRMATION-NEEDS"], {"RoutingActivation": (1, 1)}),
        "TPS_SWCT_01546": (["DO-IP-ACTIVATION-LINE-NEEDS"], {"DoIPActivationLineStatus": (1, 1)}),
        "TPS_SWCT_01547": (["WARNING-INDICATOR-REQUESTED-BIT-NEEDS"], {"EventStatus": (1, 1)}),
        "TPS_SWCT_02007": (["OBD-RATIO-SERVICE-NEEDS"], {"IUMPRNumerator": (0, 1), "IUMPRDenominator": (0, 1)}),
    }
    for cid, (need_tags, roles) in service_tables.items():
        add_service_need_table(cid, need_tags, roles)

    # Service-use-case tables whose intent cannot be inferred from class
    # retrieval alone.  Each one requires a signed exact dependency target.
    intent_service_tables = {
        "TPS_SWCT_01012": ({"EcuM_CurrentMode": (1, 1)}, None),
        "TPS_SWCT_01013": ({"EcuM_StateRequest": (1, 1)}, None),
        "TPS_SWCT_01014": ({"EcuM_ShutdownTarget": (1, 1)}, None),
        "TPS_SWCT_01015": ({"EcuM_BootTarget": (1, 1)}, None),
        "TPS_SWCT_01016": ({"EcuM_ShutdownTarget": (1, 1)}, None),
        "TPS_SWCT_01017": ({"EcuM_BootTarget": (1, 1)}, None),
        "TPS_SWCT_01018": ({"EcuM_AlarmClock": (1, 1)}, None),
        "TPS_SWCT_01019": ({"ComM_CurrentMode": (1, 1)}, None),
        "TPS_SWCT_01021": ({
            "ComM_CurrentMode": (0, 1), "ComM_UserRequest": (0, 1),
            "ComM_ECUModeLimitation": (1, 1),
        }, None),
        "TPS_SWCT_01028": ({
            "DiagnosticMonitor": (1, 1), "DiagnosticInfo": (0, 1),
            "CallbackInitMonitorForEvent": (0, 1),
            "CallbackEventStatusChange": (0, 1),
            "CallbackClearEventAllowed": (0, 1),
        }, "DIAGNOSTIC-EVENT-NEEDS"),
        "TPS_SWCT_01029": ({
            "DiagnosticMonitor": (1, 1), "DiagnosticInfo": (0, 1),
            "CallbackInitMonitorForEvent": (0, 1),
            "CallbackEventStatusChange": (0, 1),
            "CallbackClearEventAllowed": (0, 1),
            "CallbackGetFaultDetectCounter": (1, 1),
        }, "DIAGNOSTIC-EVENT-NEEDS"),
        "TPS_SWCT_01133": ({"AgingCycle": (0, 1)}, "DIAGNOSTIC-EVENT-MANAGER-NEEDS"),
        "TPS_SWCT_01136": ({"IndicatorStatus": (1, 1)}, None),
        "TPS_SWCT_01137": ({"EvMemOverflowIndication": (1, 1)}, None),
        "TPS_SWCT_01138": ({"DTCSuppression": (1, 1)}, "DIAGNOSTIC-EVENT-MANAGER-NEEDS"),
        "TPS_SWCT_01139": ({"PowerTakeOff": (1, 1)}, "DIAGNOSTIC-EVENT-MANAGER-NEEDS"),
        "TPS_SWCT_01425": ({"CallbackEventDataChanged": (1, 1)}, "DIAGNOSTIC-EVENT-INFO-NEEDS"),
        "TPS_SWCT_01426": ({
            "GeneralCallbackEventDataChanged": (0, 1),
            "GeneralCallbackEventStatusChange": (0, 1),
            "GeneralDiagnosticInfo": (0, 1),
        }, "DIAGNOSTIC-EVENT-MANAGER-NEEDS"),
        "TPS_SWCT_01427": ({"DataServices": (1, 1)}, None),
        "TPS_SWCT_01428": ({"DcmIf": (1, 1)}, None),
        "TPS_SWCT_01552": ({"AppModeInterface": (1, 1)}, None),
        "TPS_SWCT_01553": ({"AppModeInterface": (1, 1)}, None),
        "TPS_SWCT_01554": ({"AppModeRequestInterface": (1, 1)}, None),
        "TPS_SWCT_01639": ({"DataServices_DIDRange": (1, 1)}, "DIAGNOSTIC-VALUE-NEEDS"),
        "TPS_SWCT_01654": ({
            "IOControlRequest": (1, 1), "IOControlResponse": (1, 1),
        }, "DIAGNOSTIC-IO-CONTROL-NEEDS"),
        "TPS_SWCT_02002": ({"DataServices": (1, 1)}, "DIAGNOSTIC-VALUE-NEEDS"),
        "TPS_SWCT_02005": ({"DataServices": (1, 1)}, "DIAGNOSTIC-IO-CONTROL-NEEDS"),
        "TPS_SWCT_02008": ({"DataServices": (1, 1)}, "OBD-PID-SERVICE-NEEDS"),
        "TPS_SWCT_02013": ({"DCMServices": (1, 1)}, "DIAGNOSTIC-COMMUNICATION-MANAGER-NEEDS"),
        "TPS_SWCT_02018": ({"WdgM_AliveSupervision": (1, 1), "WdgM_IndividualMode": (0, 1)}, None),
        "TPS_SWCT_02019": ({"WdgM_GlobalMode": (1, 1)}, None),
        "TPS_SWCT_02506": ({
            "DLTService": (1, 1), "LogTraceSessionControl": (1, 1),
            "VerboseModeControl": (0, 1), "InjectionCallback": (0, 1),
        }, None),
    }
    crypto_roles = {
        "TPS_SWCT_02022": "CsmMacVerify",
        "TPS_SWCT_02023": "CsmRandomSeed",
        "TPS_SWCT_02024": "CsmRandomGenerate",
        "TPS_SWCT_02029": "CsmAsymEncrypt",
        "TPS_SWCT_02030": "CsmAsymDecrypt",
        "TPS_SWCT_02031": "CsmSignatureGenerate",
        "TPS_SWCT_02032": "CsmSignatureVerify",
        "TPS_SWCT_02033": "CsmChecksum",
        "TPS_SWCT_02034": "CsmKeyDerive",
        "TPS_SWCT_02035": "CsmKeyDeriveSymKey",
        "TPS_SWCT_02036": "CsmKeyExchangeCalcPubVal",
        "TPS_SWCT_02037": "CsmKeyExchangeCalcSecret",
        "TPS_SWCT_02038": "CsmKeyExchangeCalcSymKey",
        "TPS_SWCT_02039": "CsmSymKeyExtract",
        "TPS_SWCT_02040": "CsmSymKeyWrapSym",
        "TPS_SWCT_02041": "CsmSymKeyWrapAsym",
        "TPS_SWCT_02042": "CsmAsymPublicKeyExtract",
    }
    for cid, (roles, need_tag) in intent_service_tables.items():
        represented = (0, 1) if cid == "TPS_SWCT_01020" else (0, 0)
        add_intent_service_table(cid, roles, need_tag=need_tag, represented=represented)
    add_intent_service_table(
        "TPS_SWCT_01020", {"ComM_CurrentMode": (1, 1), "ComM_UserRequest": (1, 1)},
        represented=(0, 1),
    )
    for cid, specific_role in crypto_roles.items():
        add_intent_service_table(cid, {specific_role: (1, 1), "CsmCallback": (1, 1)})
    for cid, need_tag in (
        ("TPS_SWCT_02003", "DIAGNOSTIC-VALUE-NEEDS"),
        ("TPS_SWCT_02009", "OBD-PID-SERVICE-NEEDS"),
    ):
        add_intent_service_table(
            cid, None, need_tag=need_tag,
            data_roles={"signalBasedDiagnostics": (1, 2)},
        )
    add_intent_service_table(
        "TPS_SWCT_01126", {"control": (0, 1), "status": (0, 1)},
        represented=(1, 1),
    )
    add_intent_service_table(
        "TPS_SWCT_01453", {"DiagnosticInfo": (1, 1)},
        need_tag="DIAGNOSTIC-EVENT-INFO-NEEDS",
    )
    add_intent_service_table(
        "TPS_SWCT_02016", {"CallbackDCMRequestServices": (1, 1)},
        need_tag="DIAGNOSTIC-COMMUNICATION-MANAGER-NEEDS",
    )
    for cid, role in {
        "TPS_SWCT_02020": "CsmHash", "TPS_SWCT_02021": "CsmMacGenerate",
        "TPS_SWCT_02025": "CsmSymBlockEncrypt", "TPS_SWCT_02026": "CsmSymBlockDecrypt",
        "TPS_SWCT_02027": "CsmSymEncrypt", "TPS_SWCT_02028": "CsmSymDecrypt",
        "TPS_SWCT_02043": "CsmAsymPrivateKeyExtract",
        "TPS_SWCT_02044": "CsmAsymPrivateKeyWrapSym",
        "TPS_SWCT_02045": "CsmAsymPrivateKeyWrapAsym",
    }.items():
        add_intent_service_table(cid, {role: (1, 1), "CsmCallback": (1, 1)})
    for cid, callback_type, data_na, represented in (
        ("TPS_SWCT_01577", "REQUEST-CALLBACK-TYPE-MANUFACTURER", False, None),
        ("TPS_SWCT_01578", "REQUEST-CALLBACK-TYPE-SUPPLIER", True, (0, 0)),
    ):
        add_intent_service_table(
            cid, {"ServiceRequestNotification": (1, 1)},
            need_tag="DIAGNOSTIC-COMMUNICATION-MANAGER-NEEDS",
            data_na=data_na, represented=represented,
        )
        result[cid]["checks"].append(_check(
            "value_domain",
            "SERVICE-NEEDS/DIAGNOSTIC-COMMUNICATION-MANAGER-NEEDS/SERVICE-REQUEST-CALLBACK-TYPE",
            title, allowed=[callback_type], required=True,
        ))

    # Local cardinality rules.
    add("TPS_SWCT_01200", "cardinality", ["MODE-SWITCH-INTERFACE"], [
        _check("count", "MODE-GROUP", title, min=0, max=1),
    ], "The source sets an unconditional upper bound of one mode group.")
    add("constr_1311", "cardinality", ["MEMORY-SECTION", "SW-ADDR-METHOD"], [
        _check("count_matching", "OPTION", title, min=0, max=1, search="descendant", allowed=[
            "safetyQM", "safetyAsilA", "safetyAsilB", "safetyAsilC", "safetyAsilD",
        ]),
    ], "The complete safety option set and at-most-one cardinality are explicit.")
    add("constr_1381", "cardinality", ["MEMORY-SECTION", "SW-ADDR-METHOD"], [
        _check("count_matching", "OPTION", title, min=0, max=1, search="descendant", allowed=[
            "coreGlobal", "coreLocal",
        ]),
    ], "The complete core locality option set and at-most-one cardinality are explicit.")

    # Local mutual exclusion and uniqueness.
    add("constr_1196", "mutual_exclusion", [
        "NONQUEUED-RECEIVER-COM-SPEC", "QUEUED-RECEIVER-COM-SPEC",
        "NONQUEUED-SENDER-COM-SPEC", "QUEUED-SENDER-COM-SPEC",
    ], [{
        "op": "mutually_exclusive",
        "paths": ["NETWORK-REPRESENTATION", "COMPOSITE-NETWORK-REPRESENTATION"],
        "max_present": 1,
        "message": title,
    }], "The two alternatives are direct properties of the same ComSpec.")
    for cid, category, required, forbidden in (
        ("constr_1012", "FIXED_LENGTH", "BASE-TYPE-SIZE", "MAX-BASE-TYPE-SIZE"),
        ("constr_1013", "VARIABLE_LENGTH", "MAX-BASE-TYPE-SIZE", "BASE-TYPE-SIZE"),
    ):
        when = {"path": "CATEGORY", "equals": category}
        add(cid, "mutual_exclusion", ["SW-BASE-TYPE"], [
            _check("exists", required, title, search="descendant", when=when),
            _check("forbidden", forbidden, title, search="descendant", when=when),
        ], "The category antecedent, required size and forbidden alternative are all encoded.")

    add("constr_1135", "format_pattern", ["COMPU-CONST", "COMPU-CONST-TEXT-CONTENT"], [
        _check("pattern", "VT", title, regex=r".*\\|.*", forbid_match=True),
    ], "The source forbids one literal separator character.")
    add("TPS_SWCT_01249", "uniqueness", ["APPLICATION-RECORD-DATA-TYPE"], [
        _check("unique", "APPLICATION-RECORD-ELEMENT", title, key_path="SHORT-NAME", search="descendant"),
    ], "Element shortName uniqueness is scoped by its owning record type.")
    add("constr_1270", "uniqueness", ["CLIENT-SERVER-OPERATION-MAPPING"], [
        _check("unique", None, title, paths=["FIRST-DATA-PROTOTYPE-REF", "SECOND-DATA-PROTOTYPE-REF"], search="descendant"),
    ], "Both reference roles are combined into one uniqueness key set.")
    add("constr_1001", "uniqueness", ["SYSTEM"], [
        _check("unique", "DATA-ID", title, search="descendant"),
    ], "DATA-ID values are checked within each System scope.")

    # Closed category domains from tables 5.7 and 5.74.
    add("constr_1142", "value_domain", ["COMPU-METHOD"], [
        _check("value_domain", "CATEGORY", title, allowed=[
            "IDENTICAL", "LINEAR", "SCALE_LINEAR", "RAT_FUNC",
            "SCALE_RAT_FUNC", "TEXTTABLE", "BITFIELD_TEXTTABLE",
            "SCALE_LINEAR_AND_TEXTTABLE", "SCALE_RATIONAL_AND_TEXTTABLE",
            "TAB_NOINTP",
        ]),
    ], "Table 5.74 enumerates the complete non-extensible CompuMethod category domain.")
    add("constr_1143", "value_domain", [
        "APPLICATION-ARRAY-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE",
        "APPLICATION-PRIMITIVE-DATA-TYPE", "IMPLEMENTATION-DATA-TYPE",
    ], [
        _check("value_domain", "CATEGORY", title, allowed=["ARRAY"],
               when={"subject_tags": ["APPLICATION-ARRAY-DATA-TYPE"]}),
        _check("value_domain", "CATEGORY", title, allowed=["STRUCTURE"],
               when={"subject_tags": ["APPLICATION-RECORD-DATA-TYPE"]}),
        _check("value_domain", "CATEGORY", title, allowed=[
            "VALUE", "VAL_BLK", "STRING", "BOOLEAN", "COM_AXIS", "RES_AXIS",
            "CURVE_AXIS", "CURVE", "MAP", "CUBOID", "CUBE_4", "CUBE_5",
        ], when={"subject_tags": ["APPLICATION-PRIMITIVE-DATA-TYPE"]}),
        _check("value_domain", "CATEGORY", title, allowed=[
            "VALUE", "DATA_REFERENCE", "FUNCTION_REFERENCE", "TYPE_REFERENCE",
            "STRUCTURE", "UNION", "ARRAY",
        ], when={"subject_tags": ["IMPLEMENTATION-DATA-TYPE"]}),
    ], "Table 5.7 provides the complete category domain for each concrete AutosarDataType.")

    # Bound local value and structure assertions.
    add("constr_1191", "value_range", ["LIMIT"], [
        _check("numeric_range", "$self", title, min=None, max=None, required=True),
    ], "Decimal parsing of the bound LIMIT content implements the complete numerical-value assertion.")
    add("TPS_SWCT_01165", "uniqueness", ["TEXT-TABLE-MAPPING"], [
        _check(
            "unique", "VALUE-PAIRS/TEXT-TABLE-VALUE-PAIR/FIRST-VALUE", title,
            when={"path": "MAPPING-DIRECTION", "equals": "BIDIRECTIONAL"},
        ),
        _check(
            "unique", "VALUE-PAIRS/TEXT-TABLE-VALUE-PAIR/SECOND-VALUE", title,
            when={"path": "MAPPING-DIRECTION", "equals": "BIDIRECTIONAL"},
        ),
    ], "Both firstValue and secondValue lists are independently unique in the bidirectional branch.")
    add("TPS_SWCT_01617", "cardinality", ["IMPLEMENTATION-DATA-TYPE"], [
        _check("value_domain", "CATEGORY", title, allowed=["STRUCTURE"], required=True),
        _check("count", "SUB-ELEMENTS/IMPLEMENTATION-DATA-TYPE-ELEMENT", title, min=2, max=2),
    ], "The exact VSA target must be STRUCTURE and contain exactly two sub-elements.")
    result["TPS_SWCT_01617"]["activation"] = {
        "requires_validation_context": True,
        "requires_declared_constraint": True,
        "requires_declared_targets": True,
    }
    result["TPS_SWCT_01617"]["review_basis"] = (
        "complete_source_assertion_with_exact_vsa_implementation_type_target"
    )
    for cid, selector in (
        ("constr_1290", ["P-PORT-PROTOTYPE"]),
        ("constr_1291", ["R-PORT-PROTOTYPE"]),
        ("constr_1292", ["PR-PORT-PROTOTYPE"]),
    ):
        add(cid, "uniqueness", selector, [
            _check("unique", None, title, paths=["DATA-ELEMENT-REF", "OPERATION-REF"], search="descendant"),
        ], "ComSpec target references are checked for duplicates within one port.")

    return result
