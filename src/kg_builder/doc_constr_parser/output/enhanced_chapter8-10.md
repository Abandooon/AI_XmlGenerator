#@SECTION: 8 Implementation
#@CLASS: PerInstanceMemorySize
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemorySize: Attributes=[alignment, perInstanceMemory, size, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcImplementation
<!-- LLM_CONTEXT FOR CLASS SwcImplementation: Attributes=[adminData, annotation, behavior, buildActionManifest, category, codeDescriptor, compiler, desc, generatedArtifact, hwElement, introduction, linker, longName, mcSupport, perInstanceMemorySize, programmingLanguage, requiredArtifact, requiredGeneratorTool, requiredRTEVendor, resourceConsumption, shortName, shortNameFragment, swVersion, swcBswMapping, usedCodeGenerator, variationPoint, vendorId] (包含继承及相关属性); Generalization=[Implementation] (直接父类) -->
#@CLASS: Implementation
<!-- LLM_CONTEXT FOR CLASS Implementation: Attributes=[adminData, annotation, buildActionManifest, category, codeDescriptor, compiler, desc, generatedArtifact, hwElement, introduction, linker, longName, mcSupport, programmingLanguage, requiredArtifact, requiredGeneratorTool, resourceConsumption, shortName, shortNameFragment, swVersion, swcBswMapping, usedCodeGenerator, variationPoint, vendorId] (包含继承及相关属性); Generalization=[ARElement] (直接父类); Childs=[BswImplementation, SwcImplementation] (直接子类) -->
Previous versions of this document contained a comprehensive description of the meta-class Implementation. This meta-class still exists but the description of most of its content has been moved to another document, in particular the specification of the Basic Software Module Description Template [7].

Please note that the Software Component Template and the Basic Software Module Description Template share the content of Implementation. However, the semantics of Implementation is closer to the Basic Software Module Description Template.

Nevertheless, there is still content strictly related to the Software Component Template. This part of Implementation consisting of SwcImplementation (see Figure 8.1) remains in this document.

Figure 8.1: Implementation part specific to the Software Component Template

Table 8.1: SwcImplementation

Table 8.2: PerInstanceMemorySize

#@SECTION: 9 Mode Management
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SwComponentType
<!-- LLM_CONTEXT FOR CLASS SwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[AtomicSwComponentType, CompositionSwComponentType, ParameterSwComponentType] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->

In general, the Software Component Template doesn’t define the kind of modes that shall be supported by State Managers or software-components explicitly. However the Software Component Template provides generic mechanisms for describing modes.

In this section the general relationship between modes, interfaces, and software components is discussed.

The assumption from the software-component point of view is that State Managers are using a Standardized AUTOSAR PortInterface to influence the SwComponentType and also provide a PortInterface to get requests and confirmations from the SwComponentType.

They will be implemented as AUTOSAR services and be part of the Basic Software on each ECU. The actual modes a State Manager provides will have to be standardized as well to allow compatibility between software-components.

It is also possible to define a mode manager in the Application Software and the same functionality is supported as for mode managers implemented in the Basic Software.

[TPS_SWCT_01581] Communication patterns for mode-related communication (cid:100) Mode-related communication shall implement a 1:1 or 1:n scenario but the creation of an n:1 configuration shall be considered invalid. (cid:99)(RS_SWCT_03200, RS_SWCT_03110)

As a consequence of [TPS_SWCT_01581], [constr_1101] is formulated.

[constr_1101] Mode-related communication (cid:100) An RPortPrototype typed by ModeSwitchInterface shall not be referenced by more than one SwConnector. (cid:99)()

#@SECTION: 9.1 Declaration of Modes
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: ModeTransition
<!-- LLM_CONTEXT FOR CLASS ModeTransition: Attributes=[adminData, annotation, category, desc, enteredMode, exitedMode, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[AtpStructureElement, Referrable] (直接父类) -->

The SW-Component Template provides some simple means to define collections of modes.

[TPS_SWCT_01071] ModeDeclaration (cid:100) The name of the mode is the most important attribute that has to be provided for each ModeDeclaration. The ModeDeclarations are grouped together within the ModeDeclarationGroup. (cid:99)(RS_SWCT_03200, RS_SWCT_03110)

[TPS_SWCT_01067] Initial mode (cid:100) The initialMode is active before any mode switches occurred. (cid:99)(RS_SWCT_03200)

This is shown in Figure 9.1

Figure 9.1: ModeDeclaration

The class ModeDeclarationGroup has been introduced to support the grouping of modes and (on M1 level) to provide predefined sets of modes that could be standardized and re-used. The set of modes eventually defines a flat (i.e. no hierarchical states) state-machine where only one mode can be active at a given point in time.

Again, please note that the actual definition of modes and their relationship is not in the responsibility of this document. In other words: the definition of modes represents M1 artifacts whereas this document is limited to describing M2 model elements.

Both ModeDeclaration and ModeDeclarationGroup own attributes that facilitate the generation of C source code from the formal definition.

[TPS_SWCT_01008] Definition of positive integer values that are directly taken over by the RTE generator for creating the programmatic representations of the ModeDeclaration (cid:100) The attributes ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue allow for the definition of positive integer values that are directly taken over by the RTE generator for creating the programmatic representations of the ModeDeclaration and ModeDeclarationGroup in the source code. (cid:99)(RS_SWCT_03200)

[constr_1399] Standardized values of ModeDeclarationGroup.category (cid:100) The AUTOSAR standard defines the following values of the attribute ModeDeclarationGroup.category with a standardized meaning:
• EXPLICIT_ORDER
• ALPHABETIC_ORDER

[TPS_SWCT_01010] defines the meaning of these values. It is not allowed to define any custom or project-specific value of the attribute ModeDeclarationGroup.category. (cid:99)()

As the attributes ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue are optional the following rule applies:

[constr_1298] Existence of attributes if category of a ModeDeclarationGroup is set to EXPLICIT_ORDER (cid:100) The attributes ModeDeclarationGroup.onTransitionValue and ModeDeclaration.value (for each ModeDeclaration) shall be set if the category of a ModeDeclarationGroup is set to EXPLICIT_ORDER. (cid:99)()

[constr_1299] Existence of attributes if category of a ModeDeclarationGroup is set to other than EXPLICIT_ORDER (cid:100) The attributes ModeDeclarationGroup.onTransitionValue or ModeDeclaration.value (for any ModeDeclaration) shall not be set if the category of a ModeDeclarationGroup is set to any value other than EXPLICIT_ORDER. (cid:99)()

[constr_1181] Numerical values used in ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue (cid:100) The numerical values used to define the value attributes and the onTransitionValue attribute of a ModeDeclarationGroup shall not overlap. (cid:99)()

In other words, it is not allowed that the values of two value attributes within one ModeDeclarationGroup have the same numerical value. Neither is it allowed that the numerical value of the ModeDeclarationGroup.onTransitionValue attribute and the numerical value of one of the corresponding value attributes are identical.

[TPS_SWCT_01009] The numerical values used to define the values of ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue can be arbitrarily defined (cid:100) As long as the constraints [constr_1181], [constr_1298], and [constr_1299] are fulfilled, the numerical values used to define the values of ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue can be arbitrarily defined. The numerical values are not required to be consecutive. Gaps are positively allowed. (cid:99)(RS_SWCT_03200)

Example: the following example of a set of numerical values fulfills all requirements on the definition of ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue: {1,2, 5, 100}.

Please note that the ability to define ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue introduces a second heuristics for "ordering" ModeDeclarations. If ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue are not defined the assignment of numerical values to the representations of individual ModeDeclarations it is up to the RTE generator to come up with the applicable numerical values.

[TPS_SWCT_01010] categorys for the definition of a ModeDeclarationGroup (cid:100) In order to support a clear separation between the two possible ways to influence the definition of the programmatic representation of ModeDeclarations two categorys shall be defined for the definition of a ModeDeclarationGroup.
• The value of category of a ModeDeclarationGroup shall be set to EXPLICIT_ORDER if it is intended to control the source code generation by means of the values of the attributes ModeDeclaration.value and ModeDeclarationGroup.onTransitionValue.
• The value of category of a ModeDeclarationGroup shall be set to ALPHABETIC_ORDER if it is intended to let the RTE generator control the source code generation according to the alphabetical sorting.
(cid:99)(RS_SWCT_03200)

More information regarding this aspect can be found in [SWS_Rte_02568].

[TPS_SWCT_01011] Default category of a ModeDeclarationGroup (cid:100) For reasons of backwards-compatibility with previous releases of AUTOSAR the default value the category of a ModeDeclarationGroup shall be ALPHABETIC_ORDER. (cid:99)(RS_SWCT_03200)

Table 9.1: ModeDeclaration

Table 9.2: ModeDeclarationGroup

[TPS_SWCT_01450] Semantics of a ModeTransition (cid:100) In addition to the ability to specify ModeDeclarations within a ModeDeclarationGroup it is also feasible to define possible transitions between ModeDeclarations within the given ModeDeclarationGroup. This can be done by means of aggregation ModeTransition at ModeDeclarationGroup in the role modeTransition. More details are explained in Figure 9.2. (cid:99)(RS_SWCT_03200)

[TPS_SWCT_01451] Relations between ModeTransition and ModeDeclaration (cid:100) ModeTransition has two associations with the multiplicity 1 to ModeDeclaration:
• The reference enteredMode denotes a ModeDeclaration that can be entered as part of the enclosing ModeTransition.
• The reference exitedMode denotes a ModeDeclaration that can be exited as part of the enclosing ModeTransition.
(cid:99)(RS_SWCT_03200)

Figure 9.2: ModeTransition

[constr_1193] ModeDeclaration shall be referenced by at least one ModeTransition in the role enteredMode (cid:100) For each ModeDeclaration at least one ModeTransition shall reference the ModeDeclaration in the role enteredMode. This constraint shall apply only if there is at least one ModeTransition defined in the context of the enclosing ModeDeclarationGroup and it shall not apply to the initialMode. (cid:99)()

For clarification, the ModeDeclarationGroup.initialMode does not need to be referenced by an enteredMode because by identifying this ModeDeclaration in the role initialMode it is clear that the ModeDeclaration will be entered at least once.

Table 9.3: ModeTransition

#@SECTION: 9.2 Modes and Events
#@CLASS: AbstractEvent
<!-- LLM_CONTEXT FOR CLASS AbstractEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswEvent, RTEEvent] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ModeAccessPoint
<!-- LLM_CONTEXT FOR CLASS ModeAccessPoint: Attributes=[ident, modeGroup, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeSwitchPoint
<!-- LLM_CONTEXT FOR CLASS ModeSwitchPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, modeGroup, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ModeSwitchedAckEvent
<!-- LLM_CONTEXT FOR CLASS ModeSwitchedAckEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ModeSwitchedAckRequest
<!-- LLM_CONTEXT FOR CLASS ModeSwitchedAckRequest: Attributes=[timeout] (包含继承及相关属性) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcModeSwitchEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeSwitchEvent: Attributes=[activation, activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, mode, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ModeTransition
<!-- LLM_CONTEXT FOR CLASS ModeTransition: Attributes=[adminData, annotation, category, desc, enteredMode, exitedMode, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[AtpStructureElement, Referrable] (直接父类) -->

[TPS_SWCT_01376] Software-components need to be capable of reacting to state changes (cid:100) Software-components need to be capable of reacting to state changes issued by some Mode Manager and adopt their behavior to the new situation. (cid:99)(RS_SWCT_03110)

Such a mode dependent software-component is shown in Figure 9.3.

[TPS_SWCT_01077] Configure the response to mode changes (cid:100) Since the behavior of AtomicSwComponentTypes is mainly determined by the RunnableEntitys contained in the SwcInternalBehavior it is necessary to configure the response to mode changes on the level of RunnableEntitys. (cid:99)(RS_SWCT_03120)


<-------------- multimodal context 
This diagram illustrates how an AtomicSwComponentType exposes runnables and a ModeAccessPoint to integrate with an AUTOSAR state manager. The SW-Component 1 receives system mode notifications from the ModeManager and dispatches four internal runnables based on mode logic.

• Component hierarchy  
  – One AtomicSwComponentType (“SW-Component 1”)  
  – Four internal RunnableEntities (1a, 1b, 1c, 1d)  

• Ports & interfaces  
  – A single RequiredPortPrototype at the bottom implementing ModeSwitchInterface (ModeManager)  
  – Four Provided/Required DataPorts on the right (unlabeled) for data I/O  

• Data flow  
  – ModeManager → RPort: mode change events  
  – Runnables query ModeAccessPoint to adapt behavior  
  – DataPorts exchange application data with other components  

• Key AUTOSAR concepts  
  – AtomicSwComponentType, RunnableEntity  
  – RequiredPortPrototype, ModeAccessPoint, ModeDeclarationGroup  
  – DelegationConnector for mode interface  

• Scenario  
  – SW-Component 1 adjusts its internal runnables’ execution in response to global mode changes managed by the state manager. ---------------------->
Figure 9.3: State Managers and software-components

Figure 9.4 shows an excerpt of the meta-model illustrating how the relationship between the current mode and the SwcInternalBehavior of the AtomicSwComponentType can be described.

Figure 9.4: Modes and events

[TPS_SWCT_01377] Two mechanisms to define how SwcInternalBehavior should interact with the mode management (cid:100) A AtomicSwComponentType can use two mechanisms to define how its SwcInternalBehavior should interact with the mode management. Both mechanisms are visible in Figure 9.4. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01378] AtomicSwComponentType can define an SwcModeSwitchEvent to execute RunnableEntity (cid:100) Using the first mechanism, an AtomicSwComponentType can define an SwcModeSwitchEvent to specify that a particular RunnableEntity shall be started whenever a mode is entered, exited, or a transition between two specified modes occurs. (cid:99)(RS_SWCT_03110)

[constr_4003] Semantics of SwcModeSwitchEvent (cid:100) If the value of SwcModeSwitchEvent.activation is onTransition then SwcModeSwitchEvent shall refer to two different ModeDeclarations belonging to the same instance of ModeDeclarationGroup. Their order defines the direction of the transition from one mode into another. In all other cases SwcModeSwitchEvent shall refer to exactly one ModeDeclaration. (cid:99)()

[constr_1195] SwcModeSwitchEvent and the definition of ModeTransition (cid:100) For each pair of ModeDeclarations referenced by a SwcModeSwitchEvent with attribute activation set to onTransition a ModeTransition shall be defined in the corresponding direction (i.e. from exitedMode to enteredMode). This constraint shall only apply if the respective ModeDeclarationGroup defines at least one modeTransition. (cid:99)()

[TPS_SWCT_01379] AtomicSwComponentType can indicate whether an RTEEvent that starts an associated RunnableEntity is disabled in a certain mode (cid:100) Using the second mechanism, the AtomicSwComponentType can indicate whether an RTEEvent that starts an associated RunnableEntity is disabled in a certain mode. That is, RTEEvents without an association in the role disabledMode are processed regularly according to their definition. RTEEvents with the optional association disabledMode have the additional limitation that the associated RunnableEntity is not started when the ModeDeclaration referenced as disabledMode is active. (cid:99)(RS_SWCT_03110)

The mechanisms discussed so far have to be applied for the SwcInternalBehavior on the receiver side of mode switches. Since mode switches are received via PortPrototypes the following constraints apply:

[TPS_SWCT_01380] Mode management behavior on the sender side (cid:100) On the sender side, a RunnableEntity shall have ModeSwitchPoints that eventually associate a RunnableEntity with the specific ModeDeclarationGroups which it manages, see Figure 9.5. (cid:99)(RS_SWCT_03110)

Figure 9.5: ModeSwitchPoint

[TPS_SWCT_01383] ModeSwitchPoint (cid:100) The ModeSwitchPoint also allows for the definition of a ModeSwitchedAckEvent if this is requested by the definition of the PPortPrototype (see also 4.5.3). This RTEEvent is eventually owned by a mode manager to allow for getting confirmation of a mode change. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01555] ModeSwitchedAckEvent is triggered by the RTE regardless (cid:100) The ModeSwitchedAckEvent is triggered by the RTE (for more details please refer to [2]) regardless which RunnableEntity has requested the mode switch notification, even if the Meta Model implies a reference from ModeSwitchedAckEvent to a specific ModeSwitchPoint in the role eventSource. (cid:99)(RS_SWCT_03110)

[constr_4012] Timeout of ModeSwitchedAckEvent (cid:100) The timeout value of a Wait Point associated with a ModeSwitchedAckEvent shall be equal to the corresponding ModeSwitchedAckRequest.timeout. (cid:99)()
Table 9.5: ModeSwitchedAckRequest
Table 9.6: ModeSwitchedAckEvent
[TPS_SWCT_01381] Read the currently active mode (cid:100) For Mode Manager and Mode User it might additionally be required to read the currently active mode. For that purpose the a RunnableEntity that requires read access to the ModeDeclarationGroupPrototype's current mode has to define a ModeAccessPoint. (cid:99)(RS_SWCT_03110)

Figure 9.6: ModeAccessPoint
Table 9.7: ModeAccessPoint
[TPS_SWCT_01382] Mode switch requests are handled asynchronously by the RTE (cid:100) Mode switch requests are handled asynchronously by the RTE. Therefore, Mode Manager s implementation might require to read back the current active mode to synchronize internally to the RTE. A ModeSwitchPoint does not automatically provide read access to the ModeDeclarationGroupPrototype's current mode. (cid:99)(RS_SWCT_03110)

[constr_1098] Mode switch and mode disabling (cid:100) A SwcModeSwitchEvent shall not simultaneously reference to the same ModeDeclaration in both the roles mode and disabledMode. (cid:99)()

If [constr_1098] would not apply it might happen that a RunnableEntity would be triggered by a SwcModeSwitchEvent and on the same time it would be suppressed by the mode disabling.

#@SECTION: 9.3 Initialization / Finalization
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
The AUTOSAR standard shall support the execution of initialization code for every AtomicSwComponentType.

[TPS_SWCT_01384] Execution of initialization code for software-components (cid:100) Most AtomicSwComponentTypes will need to initialize by executing specific code; this code shall complete before any other code in the component is executed. Data will be initializing to specific values before the "normal" application software is running. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01385] Execution of finalization code for software-components (cid:100) Most AtomicSwComponentTypes will need to finalize by calling specific code; this code shall complete before the functionality of the application software shut down (e.g. a motor drive in a start or end position). (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01388] Initial modes of AtomicSwComponentTypes are defined by the initialMode (cid:100) The initial modes of AtomicSwComponentTypes are defined by the initialMode references of the required ModeDeclarationGroups. These modes are activated before any other mode activation has occurred. It is the responsibility of the RTE to activate all initial modes on a certain ECU. (cid:99)(RS_SWCT_03110)

For more details please refer to the specification of the SWS RTE [2].

#@SECTION: 9.4 Mode Error Behavior
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: ModeErrorBehavior
<!-- LLM_CONTEXT FOR CLASS ModeErrorBehavior: Attributes=[defaultMode, errorReactionPolicy] (包含继承及相关属性) -->
#@ENUM: ModeErrorReactionPolicyEnum
<!-- LLM_CONTEXT FOR ENUM ModeErrorReactionPolicyEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PortInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS PortInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, Identifiable] (直接父类); Childs=[ClientServerInterfaceMapping, ModeInterfaceMapping, TriggerInterfaceMapping, VariableAndParameterInterfaceMapping] (直接子类) -->
#@CLASS: SwcModeManagerErrorEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeManagerErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, modeGroup, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->

With the advent of partitions in the AUTOSAR standard, it is important to consider the behavior of mode management with respect to the following scenarios:

• The partition of the mode manager is terminated.
• The partition of the mode user is terminated.

Whenever one of the two scenarios becomes reality, it is important to implement a stable reaction of both mode manager and mode user to the event. In addition, mode manager and mode user should be able to synchronize in terms of which mode shall apply as fast and seamless as possible.

For this purpose, additional modeling support has been defined such that the applicable ModeDeclarationGroup (which is part of the contract between mode manager and mode user) becomes the place where the policy towards a reaction to e.g. a partition restart is defined.

[TPS_SWCT_01530] Error behavior of mode manager and mode user (cid:100) The behavior in response to a mode manager getting out of sync with a mode user (because the partition of the mode user has been terminated) or vice versa (because the partition of the mode manager has been terminated) can be defined for the mode manager by means of the attribute ModeDeclarationGroup.modeManagerErrorBehavior and for the mode user by means of the attribute ModeDeclarationGroup.modeUserErrorBehavior. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01531] The semantics of ModeErrorReactionPolicyEnum (cid:100) The attribute ModeErrorBehavior.errorReactionPolicy shall be used to specify the behavior in the event of a mode error: 
lastMode 
  The last mode applicable before the event shall be assumed. 
defaultMode 
  This represents the ability to specify a dedicated mode that shall be made applicable. The identified ModeDeclaration could be identical to the ModeDeclarationGroup.initialMode but it can just as well be any other ModeDeclaration defined in the context of the enclosing ModeDeclarationGroup. 
(cid:99)(RS_SWCT_03110)

[TPS_SWCT_01532] The role of ModeErrorBehavior.defaultMode (cid:100) The attribute ModeErrorBehavior.defaultMode shall be used to identify the particular ModeDeclaration if ModeErrorBehavior.errorReactionPolicy is set to defaultMode. (cid:99)(RS_SWCT_03110)

[constr_1263] Existence of ModeErrorBehavior.defaultMode (cid:100) The optional attribute ModeErrorBehavior.defaultMode shall exist if the value of the attribute ModeErrorBehavior.errorReactionPolicy is set to defaultMode. (cid:99)()

[TPS_SWCT_01533] ModeDeclarationGroup.initialMode shall be assumed in the absence of ModeDeclarationGroup.modeManagerErrorBehavior (cid:100) If the attribute ModeDeclarationGroup.modeManagerErrorBehavior is not defined it shall be assumed that the ModeDeclarationGroup.initialMode becomes applicable in case of the mode manager getting out of sync with a mode user (because the partition of the mode user has been terminated). (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01534] ModeDeclarationGroup.initialMode shall be assumed in the absence of ModeDeclarationGroup.modeUserErrorBehavior (cid:100) If the attribute ModeDeclarationGroup.modeUserErrorBehavior is not defined it shall be assumed that the ModeDeclarationGroup.initialMode becomes applicable in case of the mode user getting out of sync with a mode manager (because the partition of the mode manager has been terminated). (cid:99)(RS_SWCT_03110)

Figure 9.7: Mode Error Behavior
Table 9.8: ModeErrorBehavior
Table 9.9: ModeErrorReactionPolicyEnum

[TPS_SWCT_01535] Mode manager reacts on mode error (cid:100) If the mode manager is getting out of sync with a mode user (because the partition of the mode user has been terminated) or vice versa (because the partition of the mode manager has been terminated) it shall be possible for the mode manager to react on such an event. For this purpose the formal SwcModeManagerErrorEvent is defined that can be taken to e.g. trigger the execution of a RunnableEntity in response to an error with respect to mode switch communication. (cid:99)(RS_SWCT_03110)

Table 9.10: SwcModeManagerErrorEvent

As mentioned in [constr_1075], it is possible to overrule the default compatibility rules by the definition of a PortInterfaceMapping. In this case the demand for having identical definitions of ModeDeclarationGroup.modeUserErrorBehavior and ModeDeclarationGroup.modeManagerErrorBehavior is no longer valid. However, there is one additional caveat to observe in this case. This affects the implementation of error behavior in case that several mode users are connected to a mode manager.

[TPS_SWCT_01536] Coherent behavior of all mode users in case of errors in the mode switch communication (cid:100) The behavior in case of errors with the communication of mode switches needs to be coherent for all connected mode users especially if the individual SwConnectors are legitimized by the existence of a PortInterfaceMapping. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01541] Preferential selection of modeUserErrorBehavior (cid:100) The definition of mode error behavior on the provided side of shall be considered dominant over the definition of mode error behavior on the required side. This means that a ModeSwitchInterface.modeGroup.type.modeUserErrorBehavior used to type an AbstractProvidedPortPrototype shall be considered dominant over the definition of a corresponding modeUserErrorBehavior and defined in the context of an AbstractRequiredPortPrototype. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01542] Preferential selection of modeManagerErrorBehavior (cid:100) The definition of mode error behavior on the provided side of shall be considered dominant over the definition of mode error behavior on the required side. This means that a ModeSwitchInterface.modeGroup.type.modeManagerErrorBehavior used to type an AbstractProvidedPortPrototype shall be considered dominant over the definition of a corresponding modeManagerErrorBehavior defined in the context of an AbstractRequiredPortPrototype. (cid:99)(RS_SWCT_03110)

The consequence of [TPS_SWCT_01541] and [TPS_SWCT_01542] is that the mode manager shall be considered the master of the definition of mode error behavior. Please note that the statements made in [TPS_SWCT_01541] is further underlined by [SWS_Rte_06795] and the statement made by [TPS_SWCT_01542] is further underlined by [SWS_Rte_06795].

The details of how the run-time behavior of mode manager and mode user shall look like in the event of the mode manager getting out of sync with a mode user (because the partition of the mode user has been terminated) or vice versa (because the partition of the mode manager has been terminated) as well as the applicable RTE APIs are explained in [2].

#@SECTION: 9.5 Summary Meta-Model Excerpt Related to Modes
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeSwitchedAckEvent
<!-- LLM_CONTEXT FOR CLASS ModeSwitchedAckEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PRPortPrototype
<!-- LLM_CONTEXT FOR CLASS PRPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedRequiredInterface, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: ServiceProxySwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceProxySwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwComponentType
<!-- LLM_CONTEXT FOR CLASS SwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[AtomicSwComponentType, CompositionSwComponentType, ParameterSwComponentType] (直接子类) -->
#@CLASS: SwcModeSwitchEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeSwitchEvent: Attributes=[activation, activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, mode, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: PortGroup
<!-- LLM_CONTEXT FOR CLASS PortGroup: Attributes=[adminData, annotation, category, desc, innerGroup, introduction, longName, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->

Figure 9.8 provides an overview of all meta-model elements that have a direct relationship to the meta-classes involved in the modelling of mode switches.

To get the complete picture, it should be noted that also the concepts of PortGroups (see 4.6) and ServiceProxySwComponentType (see 11.4) have a semantical relationship to mode management, though this is not expressed via relations in the meta model.


<-------------- multimodal context 
This diagram excerpt illustrates the AUTOSAR meta-model for atomic SW-components with mode management: it shows how SwComponentType and its AtomicSwComponentType specialization host ports, internal behaviors, runnables, RTE events, mode declarations and transitions. It captures the structural elements and their relationships, defining how mode switch requests and client-server communications are integrated into a component’s runnable execution and mode lifecycle.

• Component hierarchy  
  – SwComponentType → AtomicSwComponentType contains an InternalBehavior (SwInternalBehavior) with RunnableEntity instances.  
  – Composition relations link Component, AtpBlueprint/AtpPrototype, and ARElement.  

• Ports & interfaces  
  – AbstractProvidedPortPrototype → PPortPrototype (client-server), PRPortPrototype  
  – AbstractRequiredPortPrototype → RPortPrototype  
  – PortInterface defines provided/required interfaces; ModeSwitchInterface uses AtpPrototype (ModeDeclarationGroupPrototype).  

• Data flow  
  – RTE events (AsynchronousServerCallPoint/ResultPoint, DataReceivedEvent) drive runnable activation (+startOnEvent).  
  – AssemblySwConnector/DelegationSwConnector connect ports across components.  
  – Mode events (SwcModeSwitchEvent, ModeSwitchedAckEvent) signal mode changes.  

• Key AUTOSAR concepts  
  – Prototypes: AtpBlueprint, AtpPrototype, Abstract(Provided/Required)PortPrototype  
  – Interfaces: PortInterface, ClientServerInterface, ModeSwitchInterface  
  – Modes: ModeDeclarationGroup, ModeDeclaration, ModeTransition  
  – RTE elements: RTEEvent, InternalTriggeringPoint, RunnableEntity  

• Scenario  
  – An atomic SW-component receives mode-switch requests via a PPort/ModeSwitchInterface, acknowledges via ModeSwitchedAckEvent, and triggers runnables through RTE events to implement behavior per active mode. ---------------------->
Figure 9.8: Summary meta-model excerpt related to modes

#@SECTION: 10 ECU Abstraction and Complex Drivers
#@SECTION: 10.1 Introduction
#@CLASS: ECUResourceTemplate
<!-- LLM_CONTEXT FOR CLASS ECUResourceTemplate: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: SoftwareComponentTemplate
<!-- LLM_CONTEXT FOR CLASS SoftwareComponentTemplate: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->

During the design of embedded systems there is one crucial point where the hardware and software have to be related. In AUTOSAR the ECU Resource Template describes the provided hardware resources.

On the other hand, the Software Component Template describes software generally without specific hardware in mind. But there are some places where both have to meet and fit.

One interface between hardware and software is discussed in the memory and execution time section of [7]. In this chapter the overall system view of the interface between sensors/actuators and software is described and the consequences for the Software Component Template are derived.

#@SECTION: 10.2 High Level Hardware and Software Architecture
#@CLASS: SensorActuatorSwComponentType
<!-- LLM_CONTEXT FOR CLASS SensorActuatorSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, sensorActuator, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->

The AUTOSAR concept defines a software architecture (see Figure 10.1) and within this layered architecture the interfaces between the hardware and the software are explicitly modeled.


<-------------- multimodal context 
This diagram illustrates a layered AUTOSAR ECU software architecture where Application, Actuator, and Sensor Software Components (SWCs) communicate via the Runtime Environment (RTE) with underlying Basic Software modules (OS, Services, Communication, ECU & Microcontroller Abstraction, Complex Device Drivers) to access ECU hardware.

• Component hierarchy  
  – AtomicSwComponentType instances: Application SWC, Actuator SWC, Sensor SWC  
  – CompositionSwComponentType (implicitly shown) hosts these SWCs  
  – Basic Software layers: OperatingSystem, Services, Communication, ECU Abstraction, Microcontroller Abstraction, Complex Device Drivers  

• Ports & interfaces  
  – SWCs expose AbstractProvidedPortPrototype (PPort) and AbstractRequiredPortPrototype (RPort)  
  – DataInterfaces and ClientServerInterfaces bind SWC ports via AssemblySwConnector and DelegationSwConnector into the RTE  
  – Standardized interfaces between RTE and each BSW module  

• Data flow  
  – Sensor SWC RPort pushes data through RTE → Communication service → Actuator SWC PPort  
  – Application SWC issues client-server calls via RTE to Services/ECU Abstraction  
  – Complex Device Drivers deliver specialized I/O events into RTE  

• Key AUTOSAR concepts  
  – ApplicationSwComponentType, AtomicSwComponentType  
  – AbstractRPortPrototype/AbstractPPortPrototype, DataInterface, ClientServerInterface  
  – Standardized interfaces, DelegationSwConnector, AssemblySwConnector  

• Scenario  
  – A typical ECU use-case: sensor data acquisition, in-ECU processing, actuator command output, all decoupled from hardware by RTE and Basic Software layers. ---------------------->
Figure 10.1: AUTOSAR ECU Software Architecture

The signal flow from a hardware to software and vice versa will be described in the following sections. A sensor is converting a physical value (1) in Figure 10.2 (e.g. light intensity) into an electrical signal (2) which can be either a current or a voltage. temperature, force, Inside the ECU generally there will be some electronics to enhance the electrical signal provided by the sensor. In AUTOSAR this is called ECU Electronics. This electronics is also responsible for the conversion of the electrical signal into a microcontroller compatible form (3), usually a voltage.

After the electrical signal has been enhanced and converted it will be captured by the microcontroller. This can either be done by a simple digital input, an analogue to digital converter or maybe a pulse-width demodulation module. Now the electrical signal is available as a software data value (4). This signal flow is sketched in the top part of Figure 10.2.

1The term "signal" is not going to be used here at its own but more specific terms will be used for the different abstractions of signals at the different stages of the signal flow.

2For the sake of simplicity this discussion is limited to the sensor aspects. Nevertheless, the same applies also for actuators.


<-------------- multimodal context 
This diagram illustrates an AUTOSAR layered SW-component architecture for reading car velocity and sensor current, routing them through abstraction layers to an application, and driving microcontroller peripherals via MCAL.

• Component hierarchy  
  – Topology: Application SW-C ←→ Sensor SW-C ←→ ECU Abstraction SW-C ←→ MCAL  
  – Hardware view: Car environment → Sensor → ECU Electronics → µC Peripherals  

• Ports & interfaces  
  – Sensor SW-C provides get_v(), requires get_I_sensor()  
  – Application SW-C requires get_v()  
  – ECU Abstraction provides get_I_sensor(), requires ADC_get(), provides DIO_set()  
  – DataInterfaces: car velocity (physical), I_sensor [0..200 mA], U_ECU [0..5 V]  

• Data flow  
  – Application invokes get_v() on Sensor SW-C → Sensor reads I_sensor via ECU Abstraction → ECU Abstraction calls ADC_get() → Sensor computes velocity → Application receives v  

• Key AUTOSAR concepts  
  – AtomicSwComponentType, ClientServerInterface (RPort/PPort), DataInterface, MCAL abstraction, DelegationSwConnector  

• Scenario  
  – Use-case: sample car speed and sensor current, abstract hardware details, and supply data to application logic while controlling ADC and digital I/O via MCAL. ---------------------->
Figure 10.2: Interfaces between hardware and software

This signal chain is represented one to one in the AUTOSAR software architecture and depicted in the lower part of Figure 10.2.

In an implementation of AUTOSAR only the Microcontroller Abstraction (MCAL) has direct access to the peripheral hardware. This layer is going to be standardized and all hardware access should go through this layer. The idea of the AUTOSAR signal flow is to map the hardware to the corresponding software modules.

So if an electrical current is the input to the microcontroller peripheral, the MCAL will deliver a data value that represents this current. As the ECU Electronics has enhanced and converted the electrical signal prior to the microcontroller, the corresponding software entity is reversing this conversion. This is performed in the ECU Abstraction layer.

So if the input to the ECU is an electrical current and the ECU Electronics has converted this current into a voltage (from 2 to 3), the ECU Abstraction will convert the data value voltage into an AUTOSAR signal representing a current (from 4 to 5). This AUTOSAR signal represents the actual current that was provided by the sensor (2).

Now the first step in the conversion has to be reversed: the sensor has converted a physical value into an electrical signal. And so the Sensor Software Component has to reverse this again. The Sensor Software Component will read the AUTOSAR signal representing the electrical value and transform it into an AUTOSAR signal representation of the physical value (from 5 to 6).

Now this physical value is available on the RTE and can be consumed or read by other SW-Components. Although the interface between the ECU Abstraction and the Sensor Software Component is also an AUTOSAR interface and could be routed through some communication bus, it will not be practical to separate the ECU Abstraction and the corresponding SensorActuatorSwComponentType due to potentially high communication effort.

In Figure 10.3 a complete signal flow from a sensor input to an actuator output is shown.


<-------------- multimodal context 
This diagram illustrates the layered AUTOSAR design for reading a vehicle’s speed and driving a lamp actuator. Application SW-C modules invoke Sensor and Actuator SW-C components, which use an ECU Abstraction SW-C and the MCAL (μCAL) driver to convert between physical signals and digital I/O on a microcontroller, enforcing clear abstraction and reuse.

- Component hierarchy  
  ­­• Application SW-C1 and SW-C2 at the top  
  ­­• Sensor SW-C and Actuator SW-C as AtomicSwComponentType  
  ­­• ECU Abstraction SW-C in the middle  
  ­­• μCAL (MCAL Driver) and μC Peripherals at the bottom  
- Ports & interfaces  
  ­­• Sensor SW-C has RPort get_v() and PPort get_I_ECU() (ClientServerInterface)  
  ­­• Actuator SW-C has RPort set_lamp() and PPort set_I_ECU()  
  ­­• ECU Abstraction exposes RPorts DIO_get(), DIO_set() to μCAL  
- Data flow  
  ­­• get_v() fetches sensor voltage → get_I_ECU() → DIO_get() → MCAL → hardware  
  ­­• set_lamp() → set_I_ECU() → DIO_set() → MCAL → physical lamp  
- Key AUTOSAR concepts  
  ­­• AbstractRequired/ProvidedPortPrototype, ClientServerOperation, DataInterface  
  ­­• Layered Component types (AtomicSwComponentType, ComplexDeviceDriver)  
  ­­• Delegation (AssemblySwConnector) from ECU Abstraction to MCAL  
- Scenario  
  ­­• Read car velocity via a voltage sensor and drive a car-light actuator through a microcontroller abstraction stack ---------------------->
Figure 10.3: Sensor and Actuator Signal Flow

In the next section the interfaces between the involved software modules are discussed.

#@SECTION: 10.3 Interfaces and APIs
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: SensorActuatorSwComponentType
<!-- LLM_CONTEXT FOR CLASS SensorActuatorSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, sensorActuator, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->

Two fundamentally different interfaces are involved when converting from sensors/actuators to software components, see markers “4” and “5” in Figure 10.2.

The interface between the Microcontroller Abstraction and the ECU Abstraction is a Standardized Interface (see AUTOSAR Glossary [42]). This interface is not visible on the Virtual Function Bus and therefore the MCAL and ECU Abstraction have to be present on the same ECU.

For further description of this interface please refer to the ECU Resource Template documentation.

The interface to the SensorActuatorSwComponentTypes is visible on the Virtual Function Bus. In general the SensorActuatorSwComponentType should be on the same ECU as the ECU hardware abstraction.

Also the interface between the SensorActuatorSwComponentTypes and the actual AtomicSwComponentTypes representing the application is visible on the VFB. To describe the data that is going to be exchanged via this interface the standard AUTOSAR Interface description mechanisms are used (see chapter 3.4).

#@SECTION: 10.3.1 ECU Abstraction and its AUTOSAR Interfaces
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SensorActuatorSwComponentType
<!-- LLM_CONTEXT FOR CLASS SensorActuatorSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, sensorActuator, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->

Since the AUTOSAR standard is designed with the focus on the integration of software components coming from different contractors, the interfaces between the different software-components obviously have to be compatible.

In the case of the sensors and actuators the interface is gathered in the ECU Abstraction. For each sensor and actuator there is one AUTOSAR PortPrototype that represents the AUTOSAR Signal that is delivered by the sensor or the AUTOSAR Signal that is consumed by the actuator. This relationship is depicted in Figure 10.4.


<-------------- multimodal context 
This diagram shows a minimal AUTOSAR application layer where a Sensor SW-C obtains raw measurements via a required port and then offers processed velocity data through a provided port to an ECU Abstraction SW-C. It illustrates how client/server interfaces and port connectors realize signal-based communication within the RTE.

• Component hierarchy  
  – Two AtomicSwComponentTypes in a Composition: Sensor SW-C and ECU Abstraction  
  – Sensor SW-C sits “below” ECU Abstraction in the data chain  

• Ports & interfaces  
  – Sensor SW-C has a RequiredPortPrototype (RPort) IF_3 for get_velocity()  
  – Sensor SW-C has a ProvidedPortPrototype (PPort) IF_2 for get_velocity_current()  
  – ECU Abstraction has an RPort IF_1 for get_velocity_current()  
  – AssemblySwConnector links IF_2 → IF_1  

• Data flow  
  – Sensor SW-C invokes IF_3 to read raw velocity/current  
  – Sensor SW-C then calls IF_2 to provide current velocity to ECU Abstraction  
  – ECU Abstraction receives data via IF_1 for further processing  

• Key AUTOSAR concepts  
  – AtomicSwComponentType, RequiredPortPrototype, ProvidedPortPrototype  
  – ClientServerInterface with two operations (get_velocity, get_velocity_current)  
  – AssemblySwConnector, ApplicationPrimitiveDataType for signal semantics  

• Scenario  
  – Decouple physical sensor acquisition from higher-level ECU logic by standardizing get_velocity services through a software abstraction layer. ---------------------->
Figure 10.4: Interfaces of signals in software

Each sensor and actuator has an AUTOSAR PortPrototype at the ECU Abstraction. Connected to this port is the SensorActuatorSwComponentType. The SensorActuatorSwComponentType has one PortPrototype (i.e. IF_2) to the ECU Abstraction (which provides the values via IF_1) where it gets the AUTOSAR signals from the hardware, and one PortPrototype (i.e. IF_3) to AtomicSwComponentTypes where it provides the actual physical value to the rest of AUTOSAR on the RTE.

In addition, the Interfaces between the ECU Abstraction and the SensorActuatorSwComponentType have to be compatible like defined in chapter 6.

#@SECTION: 10.4 Sensors/Actuators
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ComplexDeviceDriverSwComponentType
<!-- LLM_CONTEXT FOR CLASS ComplexDeviceDriverSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, hardwareElement, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: EcuAbstractionSwComponentType
<!-- LLM_CONTEXT FOR CLASS EcuAbstractionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, hardwareElement, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SensorActuatorSwComponentType
<!-- LLM_CONTEXT FOR CLASS SensorActuatorSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, sensorActuator, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: HwType
<!-- LLM_CONTEXT FOR CLASS HwType: Attributes=[adminData, annotation, category, desc, hwAttributeValue, hwCategory, hwType, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[ARElement, HwDescriptionEntity] (直接父类) -->
#@CLASS: HwDescriptionEntity
<!-- LLM_CONTEXT FOR CLASS HwDescriptionEntity: Attributes=[hwAttributeValue, hwCategory, hwType, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[Referrable] (直接父类); Childs=[HwElement, HwPin, HwPinGroup, HwType] (直接子类) -->
#@CLASS: HwElement
<!-- LLM_CONTEXT FOR CLASS HwElement: Attributes=[adminData, annotation, category, desc, hwAttributeValue, hwCategory, hwElementConnection, hwPinGroup, hwType, introduction, longName, nestedElement, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[ARElement, HwDescriptionEntity] (直接父类) -->
In the layered software architecture described in [6] each hardware sensor/actuator is coupled to a SensorActuatorSwComponentType (see Figure 10.5).

[TPS_SWCT_01047] Reference from the software representation of a sensor/actuator to the actual hardware element (cid:100) Since the Software Component Template is going to be used to describe the SensorActuatorSwComponentType as well, there is also a reference needed from the software representation of a sensor/actuator to the actual hardware element described in the ECU Resource description. (cid:99)(RS_SWCT_02080, RS_SWCT_03090)


<-------------- multimodal context 
This diagram illustrates how a physical sensor resource is encapsulated into an AUTOSAR Software Component Template, enabling reuse and standardized interfacing across ECUs.

• Component hierarchy  
  – ECU Resource Template “Sensor” (atomic resource model)  
  – SW-C Template “Sensor SW-C” referencing the ECU Resource Template  

• Ports & interfaces  
  – Sensor SW-C provides a PPort (yellow square) and requires an RPort (green circle)  
  – Both ports use a Sensor-related DataInterface  
  – Dashed “reference” link realizes the binding between SW-C and ECU resource  

• Data flow  
  – Physical sensor delivers data into its ECU Resource Template (input arrow)  
  – Sensor SW-C forwards this data through its PPort to downstream consumers  
  – RPort on Sensor SW-C allows configuration or control signals back to the resource  

• Key AUTOSAR concepts  
  – AtomicSwComponentType (Sensor SW-C) vs. Complex/EcuAbstractionSwComponentType (resource)  
  – AbstractProvidedPortPrototype, AbstractRequiredPortPrototype  
  – AssemblySwConnector (reference binding)  
  – Use of SW-C Template to encapsulate hardware resources  

• Scenario  
  – Packaging (“shipment”) of a hardware sensor into a reusable SW-C, standardizing its access and integration across ECUs. ---------------------->
Figure 10.5: Shipment of a sensor

So each time a sensor/actuator is selected to be connected to an ECU also the corresponding SensorActuatorSwComponentType is available.

[constr_1144] SensorActuatorSwComponentType, EcuAbstractionSwComponentType, and ComplexDeviceDriverSwComponentType may only reference a HwType (cid:100) The attribute sensorActuator of SensorActuatorSwComponentType, the attribute hardwareElement of EcuAbstractionSwComponentType, and the attribute hardwareElement of ComplexDeviceDriverSwComponentType may only reference a HwType. References to other subclasses of HwDescriptionEntity are not allowed. (cid:99)()

Figure 10.6: Sensor/actuator to Hardware Relationship

Figure 10.6 depicts the reference of SensorActuatorSwComponentType designed as a specialization of an AtomicSwComponentType with an additional reference to a HwType.

[constr_1109] Mapping of SwComponentPrototypes typed by a SensorActuatorSwComponentType (cid:100) A SwComponentPrototype typed by a SensorActuatorSwComponentType needs to be mapped and run on exactly that ECU that contains the HwElement corresponding to the HwType that its SensorActuatorSwComponentType refers to in case it accesses the hardware via the I/O hardware abstraction layer. (cid:99)()

[TPS_SWCT_01048] SensorActuatorSwComponentType may use the I/O hardware abstraction directly (cid:100) In contrast to an ApplicationSwComponentType, a SensorActuatorSwComponentType may use the I/O hardware abstraction directly (via ports/connectors). (cid:99)(RS_SWCT_02080, RS_SWCT_03090)

In case the sensor/actuator hardware is accessed via bus communication, e.g. is located on a LIN slave, no such mapping constraints apply (note that this is not handled via the IO hardware abstraction layer).

Table 10.1: SensorActuatorSwComponentType

#@SECTION: 10.5 I/O Hardware Abstraction
#@CLASS: EcuAbstractionSwComponentType
<!-- LLM_CONTEXT FOR CLASS EcuAbstractionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, hardwareElement, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: HwElement
<!-- LLM_CONTEXT FOR CLASS HwElement: Attributes=[adminData, annotation, category, desc, hwAttributeValue, hwCategory, hwElementConnection, hwPinGroup, hwType, introduction, longName, nestedElement, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[ARElement, HwDescriptionEntity] (直接父类) -->
#@CLASS: BswModuleDescription
<!-- LLM_CONTEXT FOR CLASS BswModuleDescription: Attributes=[adminData, annotation, blueprintPolicy, bswModuleDependency, bswModuleDocumentation, category, desc, internalBehavior, introduction, longName, moduleId, outgoingCallback, providedClientServerEntry, providedData, providedEntry, providedModeGroup, releasedTrigger, requiredClientServerEntry, requiredData, requiredModeGroup, requiredTrigger, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpStructureElement] (直接父类) -->
#@CLASS: SwcBswMapping
<!-- LLM_CONTEXT FOR CLASS SwcBswMapping: Attributes=[adminData, annotation, bswBehavior, category, desc, introduction, longName, runnableMapping, shortName, shortNameFragment, swcBehavior, synchronizedModeGroup, synchronizedTrigger, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpStructureElement] (直接父类) -->
#@CLASS: InternalBehavior
<!-- LLM_CONTEXT FOR CLASS InternalBehavior: Attributes=[adminData, annotation, category, constantMemory, constantValueMapping, dataTypeMapping, desc, exclusiveArea, exclusiveAreaNestingOrder, introduction, longName, shortName, shortNameFragment, staticMemory] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[BswInternalBehavior, SwcInternalBehavior] (直接子类) -->

[TPS_SWCT_01389] I/O Hardware Abstraction interfaces MCAL drivers (cid:100) The I/O Hardware Abstraction interfaces on one side the MCAL drivers via Standardized Interfaces and on the other side the Sensor Actuator Software Component via AUTOSAR Interfaces. On the VFB[3] the I/O Hardware Abstraction is represented by the EcuAbstractionSwComponentType. (cid:99)()

[TPS_SWCT_01390] I/O Hardware Abstraction might have sub-structures (cid:100) Depending on the complexity of an ECU, the I/O Hardware Abstraction might have sub-structures. In this case the I/O Hardware Abstraction Layer is described by several different EcuAbstractionSwComponentTypes on M1. (cid:99)()

Table 10.2: EcuAbstractionSwComponentType

[TPS_SWCT_01391] I/O Hardware Abstraction abstracts from the location of peripheral I/O devices (cid:100) The I/O Hardware Abstraction abstracts from the location of peripheral I/O devices (on-chip or on-board) and the ECU hardware layout and has therefore dependencies to ECU Hardware described by HwElements. In addition, the EcuAbstractionSwComponentType is a hybrid concept sharing features of both software-components and basic software modules. (cid:99)()

[TPS_SWCT_01392] Mapping between the EcuAbstractionSwComponentType and the corresponding BswModuleDescription (cid:100) The BSW part is described by the means of the Basic Software Module Template. The mapping between the EcuAbstractionSwComponentType and the corresponding BswModuleDescription is provided by the class SwcBswMapping which in addition also maps the two corresponding InternalBehaviors. This mechanism is further explained in [7]. (cid:99)()

Figure 10.7: EcuAbstractionSwComponentType

#@SECTION: 10.6 Complex Driver
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ComplexDeviceDriverSwComponentType
<!-- LLM_CONTEXT FOR CLASS ComplexDeviceDriverSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, hardwareElement, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: EcuAbstractionSwComponentType
<!-- LLM_CONTEXT FOR CLASS EcuAbstractionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, hardwareElement, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwcBswMapping
<!-- LLM_CONTEXT FOR CLASS SwcBswMapping: Attributes=[adminData, annotation, bswBehavior, category, desc, introduction, longName, runnableMapping, shortName, shortNameFragment, swcBehavior, synchronizedModeGroup, synchronizedTrigger, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpStructureElement] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: HwElement
<!-- LLM_CONTEXT FOR CLASS HwElement: Attributes=[adminData, annotation, category, desc, hwAttributeValue, hwCategory, hwElementConnection, hwPinGroup, hwType, introduction, longName, nestedElement, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[ARElement, HwDescriptionEntity] (直接父类) -->
#@CLASS: BswModuleDescription
<!-- LLM_CONTEXT FOR CLASS BswModuleDescription: Attributes=[adminData, annotation, blueprintPolicy, bswModuleDependency, bswModuleDocumentation, category, desc, internalBehavior, introduction, longName, moduleId, outgoingCallback, providedClientServerEntry, providedData, providedEntry, providedModeGroup, releasedTrigger, requiredClientServerEntry, requiredData, requiredModeGroup, requiredTrigger, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpStructureElement] (直接父类) -->
#@CLASS: SwcBswMapping
<!-- LLM_CONTEXT FOR CLASS SwcBswMapping: Attributes=[adminData, annotation, bswBehavior, category, desc, introduction, longName, runnableMapping, shortName, shortNameFragment, swcBehavior, synchronizedModeGroup, synchronizedTrigger, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpStructureElement] (直接父类) -->
#@CLASS: InternalBehavior
<!-- LLM_CONTEXT FOR CLASS InternalBehavior: Attributes=[adminData, annotation, category, constantMemory, constantValueMapping, dataTypeMapping, desc, exclusiveArea, exclusiveAreaNestingOrder, introduction, longName, shortName, shortNameFragment, staticMemory] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[BswInternalBehavior, SwcInternalBehavior] (直接子类) -->

[TPS_SWCT_01393] Complex Driver (cid:100) A Complex Driver implements complex sensor evaluation and actuator control with direct access to the Microcontroller using specific interrupts and/or complex Microcontroller peripherals to fulfill the special functional and timing requirements. In addition it might be used to implement enhanced services / protocols or encapsulates legacy functionality of a non-AUTOSAR system. (cid:99)() 
See also document [3].

[TPS_SWCT_01394] Complex Driver is represented by the ComplexDeviceDriverSwComponentType (cid:100) On the VFB the Complex Driver is represented by the ComplexDeviceDriverSwComponentType. An ECU might have zero to many different ComplexDeviceDriverSwComponentTypes. (cid:99)()

Table 10.3: ComplexDeviceDriverSwComponentType

[TPS_SWCT_01395] ComplexDeviceDriverSwComponentType has dependencies to ECU Hardware (cid:100) Similar to EcuAbstractionSwComponentType the ComplexDeviceDriverSwComponentType has dependencies to ECU Hardware described by HwElements and is a hybrid between Software Component and Basic Software Module. (cid:99)()

[TPS_SWCT_01396] Mapping between the ComplexDeviceDriverSwComponentType and the corresponding BswModuleDescription (cid:100) The BSW part is described by the means of the Basic Software Module Template. The mapping between the ComplexDeviceDriverSwComponentType and the corresponding BswModuleDescription is provided by the class SwcBswMapping which in addition also maps the two corresponding InternalBehaviors. This mechanism is further explained in [7]. (cid:99)()

Figure 10.8: ComplexDeviceDriverSwComponentType