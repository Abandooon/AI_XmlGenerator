# AUTOSAR requirement provenance and design

This guide records the sources, construction, scope, and retained evidence of the 20 AUTOSAR requirements. It distinguishes normative definitions, tool documentation, engineering observations, and author-designed cases. It accompanies the frozen experiment without changing its inputs, prompts, execution records, or hashes.

| Inspect | Public package location |
| --- | --- |
| Structured cases | [asw_cases_v3.yaml](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/runtime/atlas_autosar_requirements_v3/asw_cases_v3.yaml) |
| Deterministic prompt renderer | [render_cases.py](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/vllm/runtime/atlas_autosar_requirements_v3/render_cases.py) |
| Rendered prompts and run identities | [AUTOSAR archive](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/frozen/AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02.zip), under `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/requirements/` |
| Worked example, ARXML, and checks | [Evidence map](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/REVIEWER_EVIDENCE_MAP.md#autosar-periodic-component-example) |
| Constraint preparation | [ICM evidence](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/ICM_EVIDENCE.md) |
| Statistical methods | [Statistical analysis](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/docs/STATISTICAL_ANALYSIS.md) |

## 1. Purpose

The guide describes the requirement set's normative, engineering, and tool sources; the experimental reductions; and the evidence available for inspection. The historical engineering project is not distributed. Its recorded name is a provenance identifier, not a required reviewer workspace.

The saved `requirements/rendered/prompts/ASW-FULL-01.txt` and the retained component-generation prompt for that run are in English. This identifies those inputs, without treating the language of historical extraction instructions or source comments as the language of every generation request.

## 2. Requirement set

The 20 cases are author-constructed and reviewed requirements for AUTOSAR Classic 4.2.2 application software component fragments: six minimal, seven standard, and seven full cases. They are not an official AUTOSAR requirement set, official conformance tests, or requirements copied from customer documents.

Construction proceeded as follows:

1. Use the AUTOSAR 4.2.2 Software Component Template, VFB, RTE, Methodology, and XSD to define available model elements, references, enumerations, and value ranges.
2. Identify recurring ASW patterns in an ETAS-based AUTOSAR 4.2.2 project, including P/R ports, Sender-Receiver interfaces, NonqueuedReceiverComSpec, RunnableEntity, TimingEvent, and explicit data access.
3. Consult public Vector DaVinci Developer and ETAS ISOLAR-A documentation for how these elements are configured and checked in tools.
4. Remove surrounding project context, normalize names, simplify and recombine patterns, and divide the cases into three complexity tiers.
5. Deterministically render each structured requirement into a prompt and validation obligations, then precheck it against the fixed XSD and interface context identified by hashes.

The set covers a selected component-modeling subset with identifiable engineering precedents. Its representativeness is limited by the design choices below.

## 3. Roles of the sources

| Source class | Sources | Contribution | Scope limit |
| --- | --- | --- | --- |
| Normative | AUTOSAR 4.2.2 Software Component Template and XSD | Model elements, relationships, constraints, enumerations, ranges, and XML structure | Does not establish industrial representativeness of the 20 cases |
| Concepts and process | SW-C and System Modeling Guide, VFB, Methodology, RTE | Relationships among components, ports, interfaces, runnables, events, RTE, and development stages | Does not replace the target-version template or XSD |
| Tool implementation | Vector DaVinci Developer and ETAS ISOLAR-A | Configuration, visualization, analysis, and generation of specification elements | Does not define the normative AUTOSAR metamodel |
| Engineering observation | ETAS RH850 AUTOSAR 4.2.2 ARXML | Occurrence of selected patterns and parameters in an engineering project | Not an official AUTOSAR example or a sample of production vehicles |
| Author design | Case YAML and renderer | Simplification, parameter variants, tiers, scoring obligations, and repetitions | Not an externally developed independent benchmark |

## 4. Version and validation scope

### 4.1 Target version

The case source fixes `autosar_release: "4.2.2"`. The main normative sources are the Software Component Template, Release 4.2.2, Document ID 062; `AUTOSAR_4-2-2.xsd`; and corresponding VFB, RTE, and Methodology documents, or documents with an explicit 4.2.2 change history. Conceptual explanations from another release do not replace the target-version checks.

### 4.2 Different kinds of conformance

- XSD conformance concerns XML elements, order, types, occurrences, and basic ranges.
- Template semantics concern relationships such as port/interface compatibility, runnable/event links, and VariableAccess direction.
- Component-fragment conformance concerns consistency within the component and its supplied interface context.
- System conformance additionally requires compositions, connectors, system/ECU mappings, deployment, RTE/BSW configuration, and further evidence across artifacts.

The requirement set evaluates implemented checks in the first three categories; it provides no system-level guarantee.

## 5. From AUTOSAR specifications to requirement constructs

### 5.1 Components, ports, and interfaces

The VFB specifies component interaction through ports, with each port typed by one interface. Software Component Template 4.2.2 requirement `[TPS_SWCT_01025]` describes PortPrototype as a component connection point, with PortInterface defining the exchanged information. The cases use:

- `APPLICATION-SW-COMPONENT-TYPE`;
- `P-PORT-PROTOTYPE` and `R-PORT-PROTOTYPE` for provided and required ports;
- `PROVIDED-INTERFACE-TREF` and `REQUIRED-INTERFACE-TREF`;
- `DEST="SENDER-RECEIVER-INTERFACE"`;
- absolute AUTOSAR reference paths into the fixed interface catalog.

These constructs correspond to component boundaries and interface contracts.

### 5.2 Sender-Receiver subset

Sender-Receiver is a standard VFB interface type for distributing information from a sender to one or more receivers. Table 4.59 of the Software Component Template 4.2.2 specifies its combinations with SenderComSpec and ReceiverComSpec. The cases select this communication subset; client-server operations, mode switches, and parameter interfaces are outside the main scoring scope.

### 5.3 Periodic runnable execution

`[TPS_SWCT_01519]` associates periodic execution of a RunnableEntity with a TimingEvent that specifies the period and references the runnable to start. The cases construct:

```text
SWC-INTERNAL-BEHAVIOR
|-- EVENTS
|   `-- TIMING-EVENT
|       |-- START-ON-EVENT-REF -> RUNNABLE-ENTITY
|       `-- PERIOD
`-- RUNNABLES
    `-- RUNNABLE-ENTITY
```

`TimingEvent.period` is expressed in seconds and must be positive. The cases use 0.005, 0.01, 0.015, and 0.02 seconds, corresponding to 5, 10, 15, and 20 ms. Minimal cases omit internal behavior to isolate port/interface/ComSpec generation. Standard and full cases introduce runnables, events, and accesses. This is an experimental decomposition, not a statistical description of complete industrial SWCs.

### 5.4 Explicit runnable reads and writes

The template defines `dataReceivePointByArgument` as VariableAccess entries for explicit reads from Sender-Receiver RPort data elements, and `dataSendPoint` as explicit writes to PPort data elements. `[constr_2004]` restricts send targets to PPort/PRPort; `[constr_2005]` restricts receive-by-argument targets to RPort/PRPort. `AUTOSAR-VARIABLE-IREF` identifies both the PortPrototype and VariableDataPrototype.

These roles correspond to case `reads` and `writes`, ARXML obligations, and the tool concepts of runnable access points and explicit read/write access.

### 5.5 Receiver communication specifications and timeouts

Template Table 4.61 defines NonqueuedReceiverComSpec. `aliveTimeout` is in seconds, with zero disabling timeout monitoring. `handleTimeoutType` selects the timeout strategy: `none` uses no replacement value, while `replace` uses the communication initial value.

The engineering example has three RPorts with `ALIVE-TIMEOUT=0.3` and `HANDLE-TIMEOUT-TYPE=NONE`. The cases preserve this baseline and add other permitted positive timeouts to test exact value preservation.

### 5.6 Initial values

`[constr_1201]` requires `initValue` when NonqueuedReceiverComSpec is owned by RPortPrototype. `[TPS_SWCT_01220]` describes its use when the application reads before data have been received. Accordingly, each benchmark RPort requires a numeric initial value.

The existence requirement comes from the template; the value zero is an author-selected control for component fragments without composition/system context. The engineering example contains no `INIT-VALUE`, so zero was not copied from it. The authors supplemented the observed pattern with the normative requirement and fixed zero to reduce unrelated variation. Absence of a connector in the supplied validation context does not imply that the port would never be connected in a real system.

## 6. Tool documentation

### 6.1 Vector DaVinci Developer

The runnable documentation groups configuration into Properties, Triggers, and Access Points. It describes periodic triggers with configurable values and units, Read Data from nonqueued receiver ports, explicit writes corresponding to `Rte_Write`, and Invoke Operations corresponding to `Rte_Call`. The last category is outside this benchmark.

The Data Exchange Analysis Editor examines assembly/delegation connectors, runnable port access, triggers, and data mapping at component, runnable, and port levels. These materials explain tool operations; normative definitions remain those of AUTOSAR.

### 6.2 ETAS ISOLAR-A

ETAS describes ISOLAR-A as a tool for AUTOSAR Classic architecture, system, and application-software design with AUTOSAR exchange-format support. It supports the use of authoring tools to create and modify ARXML and distinguishes application design from subsequent ECU/BSW configuration. The cases cover an application-component subset, not complete ISOLAR-B/BSW configuration. Public product descriptions establish tool responsibilities, not ETAS endorsement of the benchmark.

## 7. Engineering evidence

### 7.1 Project context

The historical source project is identified as `ETAS_RH850_AR422_OnSiteSupport_Multicore`. Its `ASW_COM.arxml` declares:

```xml
xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_4-2-2.xsd"
```

It is therefore an engineering artifact explicitly targeting the 4.2.2 schema. It is described as an ETAS-based AUTOSAR 4.2.2 engineering example, without claiming production-vehicle or original customer requirements. The unpublished project is not an input required to run the public offline checks.

### 7.2 Observed constructs in the ASW directory

| Construct | Occurrences | Files |
| --- | ---: | ---: |
| `APPLICATION-SW-COMPONENT-TYPE` | 10 | 10 |
| `P-PORT-PROTOTYPE` | 18 | 6 |
| `R-PORT-PROTOTYPE` | 23 | 8 |
| `SENDER-RECEIVER-INTERFACE` | 8 | 2 |
| `SWC-INTERNAL-BEHAVIOR` | 10 | 10 |
| `RUNNABLE-ENTITY` | 27 | 10 |
| `TIMING-EVENT` | 16 | 10 |
| `DATA-SEND-POINTS` | 6 | 5 |
| `DATA-RECEIVE-POINT-BY-ARGUMENTS` | 2 | 2 |
| `NONQUEUED-RECEIVER-COM-SPEC` | 3 | 1 |
| `ALIVE-TIMEOUT` | 3 | 1 |
| `HANDLE-TIMEOUT-TYPE` | 3 | 1 |
| `INIT-VALUE` | 0 | 0 |

These recorded observations establish engineering precedents for the selected combinations. They also explain why the initial-value obligation is a normative addition rather than an observation from this project.

### 7.3 Six-interface mapping

| Case catalog ID | Direction | Engineering interface path | Adaptation |
| --- | --- | --- | --- |
| `MCU01_EmergShutDown` | provided | `/COM_Interface/SR_Interface_MCU01_EmergShutDown` | Interface and data-element names retained |
| `MCU02_MaxTor` | provided | `/COM_Interface/SR_Interface_MCU02_MaxTor` | Interface and data-element names retained |
| `MCU03_NRF_IdcSamp` | provided | `/COM_Interface/SR_Interface_MCU03_NRF_IdcSamp` | Interface and data-element names retained |
| `HCU01_TqCmd` | required | `/COM_Interface/SR_Interface_HCU01_TqCmd` | Interface name retained; `HCU01_Tq_Cmd` normalized to `HCU01_TqCmd` |
| `HCU01_Shift` | required | `/COM_Interface/SR_Interface_HCU01_Shift` | Interface and data-element names retained |
| `HCU02_Poweroff` | required | `/COM_Interface/SR_Interface_HCU02_Poweroff` | Interface and data-element names retained |

`ASW_COM.arxml` contains three PPorts and three RPorts, the three 0.3-second/NONE receiver configurations, one 0.01-second TimingEvent, and one runnable reading all three RPorts and writing all three PPorts. Accesses bind both ports and data elements through `AUTOSAR-VARIABLE-IREF`. `ASW-FULL-01` is the closest reduced baseline; other cases decompose or recombine that pattern.

### 7.4 Public scope

The package provides the adapted constructs, reported observations, source classifications, and hashes. The full ETAS project and local specification copies with copyright or confidentiality markings are not redistributed. Section 14 links official specification sources; the navigation tables identify public experimental artifacts and checks.

## 8. Design of the 20 requirements

### 8.1 Objectives

The benchmark tests port counts and directions, references to fixed interfaces and data elements, receiver ComSpec construction, runnable/event references, correct read/write bindings, exact values and enumerations, cardinalities, XSD ordering, and consistency as structural size increases. It does not reproduce a complete ECU or evaluate application algorithms.

### 8.2 Construction sequence

```text
Permitted AUTOSAR 4.2.2 component subset
  + recurring six-interface engineering pattern
  -> remove surrounding project context and normalize names
  -> decompose port, ComSpec, runnable, event, and access obligations
  -> define minimal / standard / full structural tiers
  -> add period and alive-timeout variants
  -> authoritative structured YAML
  -> deterministic prompts, run definitions, and hash manifest
  -> XSD, structural-obligation, and reference prechecks
```

### 8.3 Complexity tiers

| Tier | Cases | Purpose | Structure |
| --- | ---: | --- | --- |
| minimal | 6 | Isolate ports, interfaces, and receiver ComSpec | One PPort or RPort; no internal behavior required |
| standard | 7 | Complete one periodic runnable read/write chain | 2–3 ports, one runnable, one event, 2–3 accesses |
| full | 7 | Multiple ports, runnables, periods, and parameter variants | Fixed 3P+3R; 1–3 runnables/events; 4–6 accesses |

Complexity denotes element counts, references, repeated structures, and value-preservation obligations, not algorithmic complexity.

### 8.4 Parameter choices

| Parameter | Choice | Origin and role |
| --- | --- | --- |
| Provided interfaces | Three MCU interfaces | Engineering pattern |
| Required interfaces | Three HCU interfaces | Engineering pattern; one data-element name normalized |
| Baseline period | 0.01 s | Observed 10 ms engineering period |
| Period variants | 0.005/0.015/0.02 s | Author-designed positive values |
| Baseline aliveTimeout | 0.3 s | Engineering observation |
| Timeout variants | 0.05/0.1/0.2/0.4/0.5 s | Author-designed positive values |
| handleTimeoutType | `NONE` | Observed permitted enumeration; avoids extra replacement-value semantics |
| InitValue | Numeric zero | Existence required by specification; value fixed by authors |
| Repetitions | Three fixed seeds | Run variation, not additional independent components |

### 8.5 Aggregate case structure

| Metric | Total or distribution |
| --- | --- |
| Cases | 20 |
| PPort / RPort | 33 / 32 |
| Runnable / TimingEvent | 18 / 18 |
| VariableAccess | 55 |
| Periods | 5 ms × 3; 10 ms × 10; 15 ms × 1; 20 ms × 4 |
| aliveTimeout | 0.05 × 1; 0.1 × 4; 0.2 × 3; 0.3 × 21; 0.4 × 2; 0.5 × 1 |
| handleTimeoutType | `NONE` × 32 |

Each provided interface occurs 11 times. `HCU01_TqCmd` and `HCU01_Shift` each occur 11 times, and `HCU02_Poweroff` occurs 10 times, reducing dominance by a single signal name.

## 9. Coverage by case

| Case | Design | P/R | Runnables and periods | Accesses | Source classification |
| --- | --- | ---: | --- | ---: | --- |
| ASW-MIN-01 | Emergency-shutdown PPort | 1/0 | None | 0 | Minimal engineering-interface fragment |
| ASW-MIN-02 | Maximum-torque PPort | 1/0 | None | 0 | Minimal engineering-interface fragment |
| ASW-MIN-03 | Current-sample PPort | 1/0 | None | 0 | Minimal engineering-interface fragment |
| ASW-MIN-04 | Torque-command RPort | 0/1 | None | 0 | Engineering RPort/0.3/NONE plus normative InitValue |
| ASW-MIN-05 | Shift RPort | 0/1 | None | 0 | Engineering RPort/0.3/NONE plus normative InitValue |
| ASW-MIN-06 | Power-off RPort | 0/1 | None | 0 | Engineering RPort/0.3/NONE plus normative InitValue |
| ASW-STD-01 | Torque input to maximum-torque output | 1/1 | 1 × 10 ms | 2 | Reduced engineering chain |
| ASW-STD-02 | Shift input to shutdown output | 1/1 | 1 × 5 ms | 2 | Engineering pattern plus period variant |
| ASW-STD-03 | Power-off input to current output | 1/1 | 1 × 20 ms | 2 | Engineering pattern plus period variant |
| ASW-STD-04 | One input, two outputs | 2/1 | 1 × 10 ms | 3 | Author recombination |
| ASW-STD-05 | Two inputs, one output | 1/2 | 1 × 15 ms | 3 | Author recombination and period variant |
| ASW-STD-06 | One input, two outputs | 2/1 | 1 × 10 ms | 3 | Author recombination |
| ASW-STD-07 | Explicit 0.1 s timeout | 1/1 | 1 × 10 ms | 2 | Exact permitted value |
| ASW-FULL-01 | Three inputs and outputs, one runnable | 3/3 | 1 × 10 ms | 6 | Closest to engineering ASW_COM baseline |
| ASW-FULL-02 | Separate fast and slow runnables | 3/3 | 5/20 ms | 6 | Multiple-rate decomposition |
| ASW-FULL-03 | Control/safety grouping | 3/3 | 10/20 ms | 6 | Author-defined responsibilities |
| ASW-FULL-04 | One input drives all outputs; other RPorts retained | 3/3 | 1 × 10 ms | 4 | Port presence versus access coverage |
| ASW-FULL-05 | All inputs drive one output; other PPorts retained | 3/3 | 1 × 10 ms | 4 | Port presence versus access coverage |
| ASW-FULL-06 | Three disjoint periodic access chains | 3/3 | 5/10/20 ms | 6 | Largest repetition and reference load |
| ASW-FULL-07 | Three different aliveTimeout values | 3/3 | 1 × 10 ms | 6 | Preservation of distinct values |

## 10. Observation, normalization, and author design

| Content | Observed in project | Specification basis | Author contribution |
| --- | --- | --- | --- |
| Six Sender-Receiver paths | Yes | Permitted | Names retained except one normalized data element |
| PPort/RPort direction | Yes | Defined | Recombined across cases |
| 3P+3R baseline | Yes | Permitted | Decomposed into different sizes |
| Runnable and 10 ms event | Yes | Permitted | Extended to 5/15/20 ms |
| Read RPort / write PPort | Yes | Defined | Assigned to 1–3 runnables |
| aliveTimeout=0.3 | Yes | Permitted | Other positive values added |
| handleTimeoutType=NONE | Yes | Permitted | Fixed across cases |
| InitValue existence | No | Required by constr_1201 | Fixed numeric zero |
| 6/7/7 tiers | No | Not prescribed | Author design |
| 20 cases, three repetitions | No | Not prescribed | Author design |
| Scoring obligations | No | Derived from modeled requirements | Author implementation |

The modeling language comes from the specifications, recurring patterns and some parameters from engineering observations, and case boundaries and variations from the authors.

## 11. Included and excluded scope

Included constructs are ApplicationSwComponentType, PPortPrototype, RPortPrototype, SenderReceiverInterface references, SwcInternalBehavior, RunnableEntity, TimingEvent, dataSendPoint, dataReceivePointByArgument, NonqueuedReceiverComSpec, InitValue, AliveTimeout, and HandleTimeoutType.

Excluded are CompositionSwComponentType, SwComponentPrototype and connectors; ECU/system descriptions, networks, communication clusters and data mapping; ECU/deployment/OS-task mapping; generated RTE and BSW configuration; complete ApplicationDataType/ImplementationDataType catalogs; client-server, mode-switch and parameter scoring; application algorithms; and runtime, timing, safety or regulatory evaluation.

## 12. Validation and evidence

### 12.1 Offline precheck

The frozen precheck records 20/20 cases with compiled obligations and deterministic materialization; 20 component ARXML files and 65 per-case interface files; 85/85 XSD passes; 225/225 resolvable references within the supplied context; and 70/70 injected faults detected by XSD, structural obligations, or reference checks. Its overall decision is `PASS`.

These results establish realizable reference structures for the structured requirements. They do not predict LLM success or establish complete system conformance.

### 12.2 Frozen identities

| Artifact | SHA-256 |
| --- | --- |
| `asw_cases_v3.yaml` | `3b61eb5926b5646a12f8767524192cd7ed65a39e27a37aa9672277058489e024` |
| Historical requirement `README.md` | `10d658ee362a627ed5fddd1a5a7d19b04f6f8ed909777f5679eb9cc2eeb23456` |
| `rendered/run_manifest.json` | `0af861da7b10dfe80261080b58dba1c3758378d0a2a1bfe55b5084d90bc202b4` |
| `render_cases.py` | `e3045e1131abd9cbaf7ec16b233c924cf1c7f30f684d454d77a407d98b18f6d5` |
| `AUTOSAR_4-2-2.xsd` | `3c89b2f16d1981eb04e12c7fbe035e7cd6fbd79965a47ff6cf6d6b878feb71ad` |
| Engineering `ASW_COM.arxml` | `1eaac065e23179a8f8ec5ed08501ef43ff189048f26a507d6be96dc61ebb70e3` |

Provenance documentation is maintained separately from these frozen inputs. Updating explanations must not change the YAML or regenerate historical prompts.

## 13. Limitations

The system authors designed the cases. Exact tags, paths, and counts are explicit in the prompts, so the experiment evaluates controlled model construction rather than unrestricted requirement interpretation. Six interfaces come mainly from one engineering context. The full tier is the largest tier within this set, not a complete AUTOSAR system. Sender-Receiver communication and a fixed NONE timeout strategy reduce variation. XSD validity is necessary but insufficient for complete semantic, integration, or runtime correctness.

## 14. Specification and tool sources

1. AUTOSAR, *Software Component Template*, Release 4.2.2, Document ID 062, 2015. Primary source of elements and semantic constraints. <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TPS_SoftwareComponentTemplate.pdf>
2. AUTOSAR, *SW-C and System Modeling Guide*, Release 4.2.2, Document ID 207, 2015. Component and system modeling. <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TR_SWCModelingGuide.pdf>
3. AUTOSAR, *Virtual Functional Bus*, Release 4.2.2, Document ID 056. Ports, interfaces, and communication. <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TR_VFB.pdf>
4. AUTOSAR, *Methodology for Classic Platform*, Release 4.2.2, Document ID 068. ASW design, implementation, and integration. <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_TR_Methodology.pdf>
5. AUTOSAR, *Specification of RTE Software*, Release 4.2.2, Document ID 084. Runnable/event/port relationships to RTE execution and APIs. <https://www.autosar.org/fileadmin/standards/R4.2.2/CP/AUTOSAR_SWS_RTE.pdf>
6. AUTOSAR, *Classic Platform*. Official platform overview. <https://www.autosar.org/standards/classic-platform/>
7. Vector, *Defining Runnable Entities*, DaVinci Developer Classic. Properties, triggers, and access points. <https://help.vector.com/davinci-developer-classic/current/en/help/html/defining_runnable_entities.html>
8. Vector, *Data Exchange Analysis Editor*, DaVinci Developer Classic. Component, runnable, port, and data-exchange analysis. <https://help.vector.com/davinci-developer-classic/current/en/help/html/data_exchange_analysis_editor.html>
9. ETAS, *RTA-CAR Details & Integration — ISOLAR-A*. Architecture, system, and application-software design. <https://www.etas.com/ww/en/products-services/vehicle-software-platform/autosar-classic-profile-rta-car/rta-car-details-integration/>

## 15. Public package locations

The opening table links the case definitions, renderer, formal archive, worked example, statistics, and ICM. Within `AUTOSAR_V20_FORMAL_EVIDENCE_FINAL_2026-09-02/`, inspect `requirements/README.md`, `requirements/rendered/run_manifest.json`, and `requirements/rendered/prompts/`.

The archive also retains `code_snapshot/experiment/ALL_REQUIREMENTS_OFFLINE_PRECHECK_MANIFEST.json` as a historical preparation check. Use the [current AUTOSAR entry](https://github.com/Abandooon/AI_XmlGenerator/blob/ATLAS/experiments/autosar/README.md) for formal-run offline verification. The case specification defines requirements; rendering expresses them; the schedule assigns executions and seeds. The schedule is not their source.

## 16. Formal-run evidence scope (2026-09-02)

The V20 formal run uses these same 20 requirements and the same provenance, language, reductions, and representativeness limits.

- Twenty cases and three fixed seeds produce 60 observations. All 60 artifact bundles pass XSD, artifact-profile, task-obligation, local-reference, and independent checks; all 20 cases pass in all three repetitions.
- All 60 full-corpus decisions remain `INCOMPLETE` because the tasks do not generate system/deployment evidence. This is distinct from XSD or task-obligation failure.
- Normal pre-materialization applies 1,734 task obligations and performs 527 deterministic IR normalization/recovery operations in 49 runs, after the structured response and before ARXML materialization. These are pipeline operations, not manual edits to completed experimental artifacts.
- Controlled repair restores all 85 core fixed-operator units and all 15 predeclared substitute units, including exact recovery of reference artifact bytes.
- The generation batch contains zero natural failures and therefore provides no samples for estimating natural-failure repair rates.
- The hosted AUTOSAR experiment constrains semantic IR through strict JSON Schema but does not expose token masks. Token-level grammar-intervention evidence comes from the separate local vLLM experiment.

V20 content identities are generation `5da533af826edcabca4c08632ffdc684ef31de31a868046be96f70f851ec9ef6`, repair `15b0cd2f2f65756ca6373e9abb7fcfdf68ca108e67bccb77bf329e89d111412c`, and Neo4j context `2ad8bfd31daae20c624bea39d955543ae0ab2544b61c6f06e481291011ba055b`. V17/V18/V19 are earlier development and diagnostic records and are excluded from the formal-run denominator.
