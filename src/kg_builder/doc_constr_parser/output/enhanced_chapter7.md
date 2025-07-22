#@SECTION: 7 Internal Behavior
#@SECTION: 7.1 Introduction
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: InternalBehavior
<!-- LLM_CONTEXT FOR CLASS InternalBehavior: Attributes=[adminData, annotation, category, constantMemory, constantValueMapping, dataTypeMapping, desc, exclusiveArea, exclusiveAreaNestingOrder, introduction, longName, shortName, shortNameFragment, staticMemory] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[BswInternalBehavior, SwcInternalBehavior] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcImplementation
<!-- LLM_CONTEXT FOR CLASS SwcImplementation: Attributes=[adminData, annotation, behavior, buildActionManifest, category, codeDescriptor, compiler, desc, generatedArtifact, hwElement, introduction, linker, longName, mcSupport, perInstanceMemorySize, programmingLanguage, requiredArtifact, requiredGeneratorTool, requiredRTEVendor, resourceConsumption, shortName, shortNameFragment, swVersion, swcBswMapping, usedCodeGenerator, variationPoint, vendorId] (包含继承及相关属性); Generalization=[Implementation] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: IncludedDataTypeSet
<!-- LLM_CONTEXT FOR CLASS IncludedDataTypeSet: Attributes=[dataType, literalPrefix] (包含继承及相关属性) -->
#@CLASS: IncludedModeDeclarationGroupSet
<!-- LLM_CONTEXT FOR CLASS IncludedModeDeclarationGroupSet: Attributes=[modeDeclarationGroup, prefix] (包含继承及相关属性) -->
#@CLASS: InstantiationDataDefProps
<!-- LLM_CONTEXT FOR CLASS InstantiationDataDefProps: Attributes=[parameterInstance, swDataDefProps, variableInstance, variationPoint] (包含继承及相关属性) -->
#@CLASS: PortAPIOption
<!-- LLM_CONTEXT FOR CLASS PortAPIOption: Attributes=[enableTakeAddress, errorHandling, indirectAPI, port, portArgValue, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: VariationPointProxy
<!-- LLM_CONTEXT FOR CLASS VariationPointProxy: Attributes=[adminData, annotation, category, conditionAccess, desc, implementationDataType, introduction, longName, postBuildValueAccess, postBuildVariantCondition, shortName, shortNameFragment, valueAccess] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@ENUM: HandleTerminationAndRestartEnum
<!-- LLM_CONTEXT FOR ENUM HandleTerminationAndRestartEnum: Literals=[] (元数据中未找到字面量) -->

[TPS_SWCT_01075] SwcInternalBehavior (cid:100) SwcInternalBehavior provides means for formally defining the behavior of an AtomicSwComponentType. (cid:99)(RS_SWCT_03040)

This chapter focuses on the description of the SwcInternalBehavior meta-class and the various meta-classes it aggregates. An overview of the meta-class is sketched in Figure 7.2. Please note that SwcInternalBehavior inherits from InternalBehavior.

The role of SwcInternalBehavior in the context of an AUTOSAR software component is depicted in Figure 7.1. As mentioned in section 3.2, the reason to make the aggregation of SwcInternalBehavior to AtomicSwComponentType (cid:28)atpSplitable(cid:29) is to allow for the development of SwcInternalBehavior in a later process step (e.g. after the VFB view has been completed).

Figure 7.1: The "big picture" of SwcInternalBehavior

Table 7.1: SwcInternalBehavior

Table 7.2: HandleTerminationAndRestartEnum

Figure 7.2: SwcInternalBehavior

#@SECTION: 7.2 Runnable Entity
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: CompositionSwComponentType
<!-- LLM_CONTEXT FOR CLASS CompositionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, component, connector, consistencyNeeds, constantValueMapping, dataTypeMapping, desc, instantiationRTEEventProps, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类) -->
#@CLASS: ExecutableEntity
<!-- LLM_CONTEXT FOR CLASS ExecutableEntity: Attributes=[activationReason, adminData, annotation, canEnterExclusiveArea, category, desc, exclusiveAreaNestingOrder, introduction, longName, minimumStartInterval, reentrancyLevel, runsInsideExclusiveArea, shortName, shortNameFragment, swAddrMethod] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswModuleEntity, RunnableEntity] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: SwComponentType
<!-- LLM_CONTEXT FOR CLASS SwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[AtomicSwComponentType, CompositionSwComponentType, ParameterSwComponentType] (直接子类) -->
#@CLASS: EcuInstance
<!-- LLM_CONTEXT FOR CLASS EcuInstance: Attributes=[adminData, annotation, associatedComIPduGroup, associatedPdurIPduGroup, canTpAddress, category, clientIdRange, comConfigurationGwTimeBase, comConfigurationRxTimeBase, comConfigurationTxTimeBase, comEnableMDTForCyclicTransmission, commController, connector, desc, diagnosticAddress, diagnosticProps, introduction, longName, partition, pnResetTime, pncPrepareSleepTimer, shortName, shortNameFragment, sleepModeSupported, tpAddress, variationPoint, wakeUpOverBusSupported] (包含继承及相关属性); Generalization=[FibexElement] (直接父类) -->

The concept of RunnableEntity (more details can be found in Figure 7.3) is defined in the specification of the Virtual Function Bus [3].

[TPS_SWCT_01030] RunnableEntity (cid:100) RunnableEntitys are the smallest code fragments that are provided by a software-component and are (at least indirectly) a subject for scheduling by the underlying operating system. (cid:99)(RS_SWCT_00070, RS_SWCT_00090, RS_SWCT_03050)

Figure 7.3: Details of RunnableEntity

[TPS_SWCT_01097]CompositionSwComponentType cannot have RunnableEntitys (cid:100) It is intentionally not possible for CompositionSwComponentType to define a SwcInternalBehavior. Consequently, CompositionSwComponentTypes don't have RunnableEntitys by themselves. (cid:99)(RS_SWCT_00070, RS_SWCT_00090, RS_SWCT_03050)

[TPS_SWCT_01098] Only AtomicSwComponentType can have RunnableEntitys (cid:100) Only the AtomicSwComponentType that are populating a CompositionSwComponentType as SwComponentPrototypes may have RunnableEntitys. (cid:99)(RS_SWCT_00070, RS_SWCT_00090, RS_SWCT_03050)

This correlation is depicted in Figure 7.4.

Figure 7.4: Only AtomicSwComponentTypes may have RunnableEntitys

Please note that RunnableEntitys exist in several categories that have different properties. Please find more explanation about categories of RunnableEntitys in section 7.2.4.4.

Table 7.3: RunnableEntity
[TPS_SWCT_01302] Semantics of minimumStartInterval (cid:100) The attribute ExecutableEntity.minimumStartInterval defines the time interval that the RTE will guarantee to not go below between scheduling two consecutive executions of the corresponding RunnableEntity. (cid:99)()

[TPS_SWCT_01303] symbol attribute describes the RunnableEntity's entry point (cid:100) The RunnableEntity.symbol attribute is describing the RunnableEntity's entry point. (cid:99)()

The implication RunnableEntity.symbol on the uniqueness of symbols in the scope of one EcuInstance is described in [constr_2025] [11].

A RunnableEntity inherits several attributes from its base class ExecutableEntity due to the fact that these are also used in the Basic Software Module Description Template [7]. Here the following constraint applies:

[constr_4082] RunnableEntity.reentrancyLevel shall not be set. (cid:100) The optional attribute reentrancyLevel shall not be set for a RunnableEntity. This attribute would define more specific reentrancy features than the mandatory attribute canBeInvokedConcurrently. These features are currently only supported for Basic Software. (cid:99)()

Please note that the formal definition of the semantics of a RunnableEntity has strong relations to the specification of the AUTOSAR RTE [2]. The definition of the RTE semantics, however, is not in the scope of this document.

However, the formal definition requires some background discussion that can't be completely left out of this document. Otherwise the meaning of specific model elements could not be understood properly.

#@SECTION: 7.2.1 Concurrency and Reentrancy of a RunnableEntity that cannot be Invoked Concurrently
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->

This section applies to the case that the value of the attribute canBeInvokedConcurrently is false. During runtime, each RunnableEntity of each instance of an AtomicSwComponentType is in a specific run-time state.

The details of the definition and semantics of run-time states can be found in [2]. Nevertheless, this chapter contains a brief description of the fundamental concepts in order to properly being able to discuss the formal modeling of RunnableEntitys.

[TPS_SWCT_01313] Conditions for a transition from suspended to to be started (cid:100) The SwcInternalBehavior describes for each RunnableEntity the conditions for a transition from suspended to to be started should occur. This is done using the concept of an RTEEvent. (cid:99)()

When a RunnableEntity is in state to be started, the RTE can decide to start running the RunnableEntity. The delay between entering the state to be started (e.g. a message has been received in response to which the RunnableEntity should run) and moving into the state running (the first instruction of the RunnableEntity has been executed) depends on the scheduling strategy of the RTE, i.e. the mapping of RunnableEntitys on AUTOSAR OS tasks.

The transition from the state running into the state suspended is in the hands of the RunnableEntity: the transition occurs when the RunnableEntity returns (thereby handing over control to the AUTOSAR OS [28]). Some RunnableEntitys (like cat. 2 RunnableEntitys) might never return to the suspended state once they entered the running state.

They might enter the preempted state when being preempted. The same applies if a RunnableEntity needs to wait for a WaitPoint to be unblocked.

[TPS_SWCT_01304] Cat. 1A and 1B RunnableEntitys will eventually terminate (cid:100) Cat. 1A and 1B RunnableEntitys will eventually return after having executed a specific finite algorithm (the execution time of which might be provided). (cid:99)()

[TPS_SWCT_01305] RunnableEntity as one that cannot be invoked concurrently (cid:100) In case the SwcInternalBehavior defines a RunnableEntity as one that cannot be invoked concurrently it is the responsibility of the RTE to make sure that the RunnableEntity is never started concurrently (for example, in two different AUTOSAR OS tasks). This implies that the implementation of the AtomicSwComponentType does not need to worry about concurrency issues. (cid:99)()

For example: The internal behavior of an AtomicSwComponentType MyComponentType describes a RunnableEntity R1 which should be enabled when an operation on a client-server p-port of the AtomicSwComponentType is invoked. The AtomicSwComponentType specifies that the RunnableEntity R1 cannot be invoked concurrently.

The AtomicSwComponentType MyComponentType is instantiated on an ECU. When a call of the operation is received, the corresponding instance of the RunnableEntity R1 is enabled and the RTE will start executing the RunnableEntity (the RunnableEntity is in state running) in a task eventually managed by the AUTOSAR OS.

If another call of the operation is received while the RunnableEntity is in state running it is not allowed that the RTE runs the RunnableEntity again in a second task. Rather, the RTE has to wait (and maybe queue the second incoming request) until the RunnableEntity has returned and has moved to the suspended state.

#@SECTION: 7.2.2 Concurrency and Reentrancy of a RunnableEntity that can be Invoked Concurrently
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

This section applies to the case that the value of the attribute canBeInvokedConcurrently is set to true. In this case, it is allowed that the same RunnableEntity is running several times concurrently in different AUTOSAR OS tasks. This implies that the state machine defined in [2] is not the state of the RunnableEntity any more, but can be cloned an arbitrary number of times.

[TPS_SWCT_01306] Software-component description itself does not put any bounds on the number of concurrent invocations of a RunnableEntity (cid:100) The software-component description itself does not put any bounds on the number of concurrent invocations of the RunnableEntity that are allowed. The software-component description only specifies whether the RunnableEntity can be invoked concurrently or not. Allowing concurrent invocation of a RunnableEntity implies that the implementation of the AtomicSwComponentType needs to take care of this additional form of concurrency. (cid:99)()

For example: The SwcInternalBehavior of a component-type MyComponentType describes a RunnableEntity R1 which should be enabled when a ClientServer Operation on a PPortPrototype typed by a ClientServerInterface of the AtomicSwComponentType is invoked. The AtomicSwComponentType specifies that the RunnableEntity R1 can be invoked concurrently. The AtomicSwComponentType MyComponentType is instantiated on an ECU. When a call of the ClientServerOperation is received the corresponding instance of the RunnableEntity R1 is enabled and the RTE will start executing the RunnableEntity (the RunnableEntity is in state running) in a task eventually managed by the AUTOSAR OS. If another call of the ClientServerOperation is received, it is allowed that the same RunnableEntity is started again in a different task.

A typical use-case of concurrent RunnableEntitys is the implementation of AUTOSAR services. The AUTOSAR services will typically take care of concurrency internally: several software-components can directly use the services in parallel. The ECU-integrator could then decide that the RunnableEntity implementing the AUTOSAR service runs directly in the context (in the task) of the AtomicSwComponentType invoking the service. This is a very efficient and direct coupling between the client and the server: the connector between the client and the server is reduced to a local function-call.

#@SECTION: 7.2.3 Timed Activation of Runnable Entities
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: TimingEvent
<!-- LLM_CONTEXT FOR CLASS TimingEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, period, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->

In many cases, RunnableEntitys need to be activated in response to timing events rather than related to communication (e.g. the reception of a response to an asynchronous operation invocation). Many RunnableEntitys will need to run cyclically with a fixed rate.

The approach taken in the software-component description is to define so-called TimingEvents (please find more details in Figure 7.5) as special kinds of RTEEvents.

So far, only one kind of timing-related RTEEvent has been defined: a simple periodic TimingEvent.

Figure 7.5: Periodic activation of RunnableEntities

[TPS_SWCT_01519] RTE executes certain RunnableEntity periodically (cid:100) If the SwcInternalBehavior of an AtomicSwComponentType requires that the RTE executes certain RunnableEntitys periodically, the description needs to define a TimingEvent with the desired period. This TimingEvent then contains a reference to the Runnable that needs to be executed with this period. (cid:99)()

#@SECTION: 7.2.4 Additional Remarks and Clariﬁcations
#@SECTION: 7.2.4.1 Reentrancy and Multiple Instantiation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: TimingEvent
<!-- LLM_CONTEXT FOR CLASS TimingEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, period, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->

This chapter is emphasizing on the specific meanings of combinations of the attributes SwcInternalBehavior.supportsMultipleInstantiation and RunnableEntity.canBeInvokedConcurrently.

[TPS_SWCT_01307] supportsMultipleInstantiation vs. canBeInvokedConcurrently (cid:100) The semantics of combining the attributes supportsMultipleInstantiation and canBeInvokedConcurrently is summarized in Table 7.4. (cid:99)()

Table 7.4: supportsMultipleInstantiation vs. canBeInvokedConcurrently

In case the implementation of a AtomicSwComponentType decides to map several RunnableEntitys to the same symbol there are reentrancy problems to be sorted out. However, this scenario is not supported by RTE [2] anyway and shall therefore be avoided.

#@SECTION: 7.2.4.2 Reentrancy and “Library Functions”
Note that all code that is called by different RunnableEntitys (like e.g. library routines, etc.) shall obviously be reentrant. A filter algorithm implemented in C, for example, is not allowed to store values from previous runs by means of static variables or variables with external binding.

#@SECTION: 7.2.4.3 Compatibility of ClientServerOperations triggering the same RunnableEntity
#@CLASS: ArgumentDataPrototype
<!-- LLM_CONTEXT FOR CLASS ArgumentDataPrototype: Attributes=[adminData, annotation, category, desc, direction, introduction, longName, serverArgumentImplPolicy, shortName, shortNameFragment, swDataDefProps, type, typeBlueprint, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: ImplementationDataTypeElement
<!-- LLM_CONTEXT FOR CLASS ImplementationDataTypeElement: Attributes=[adminData, annotation, arraySize, arraySizeHandling, arraySizeSemantics, category, desc, introduction, longName, shortName, shortNameFragment, subElement, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: PortDefinedArgumentValue
<!-- LLM_CONTEXT FOR CLASS PortDefinedArgumentValue: Attributes=[value, valueType] (包含继承及相关属性) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: OperationInvokedEvent
<!-- LLM_CONTEXT FOR CLASS OperationInvokedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->

[TPS_SWCT_01309] signature of a RunnableEntity depends on the connected RTEEvent (cid:100) The signature of a RunnableEntity depends on the connected RTEEvent. Multiple OperationInvokedEvents are only supported if all referred ClientServerOperations would result in the same RunnableEntity signature for the server RunnableEntity. (cid:99)()

[constr_2000] Compatibility of ClientServerOperations triggering the same RunnableEntity (cid:100) The ClientServerOperations are considered compatible if the number of arguments (which can be ArgumentDataPrototypes or related PortDefinedArgumentValues) is equal and the corresponding arguments (i.e. first argument on both sides, second argument on both sides, etc.) are compatible. In particular, this means that:

• for combinations of ArgumentDataPrototypes and ArgumentDataPrototypes where the serverArgumentImplPolicy is set to useArgumentType the referred ImplementationDataTypes shall be compatible. In case of data types of category STRUCTURE all by order matching ImplementationDataTypeElements shall be named equally.

• for combinations of PortDefinedArgumentValues and ArgumentDataPrototypes where the serverArgumentImplPolicy is set to useArgumentType the referred ImplementationDataTypes shall be compatible.

• for combinations of ArgumentDataPrototypes and ArgumentDataPrototypes where the serverArgumentImplPolicy is set to useArrayBaseType the referred ImplementationDataTypes of category ARRAY shall have compatible ImplementationDataTypeElements. In case of ImplementationDataTypeElements of category STRUCTURE all by order matching ImplementationDataTypeElements of the structure shall be named equally.

• for ArgumentDataPrototypes where the serverArgumentImplPolicy is set to useVoid an arbitrary ImplementationDataType is referred to.

In addition, it is required that the return value defined on both sides shall match (in terms of Std_ReturnType vs. void) and also the possibleErrors are compatible. (cid:99)()

[TPS_SWCT_01520] Implication of the existence of possibleError on compatibility of ClientServerOperations (cid:100) An implication of [constr_2000] is that a ClientServerOperation that defines any possibleError is not compatible with a ClientServerOperation that defines no possibleError at all because this configuration leads to different data type of the return value of the C function that implements the applicable RunnableEntity. (cid:99)()

#@SECTION: 7.2.4.4 Categories of Runnable Entities
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

[TPS_SWCT_01310] Categories of RunnableEntitys (cid:100) RunnableEntitys are subdivided into the following categories:

Category 1 Category 1 RunnableEntitys do not have WaitPoints and are required to terminate in a finite amount of time. Category 1 is divided into two subcategories: Category 1A and Category 1B. Category 1A RunnableEntitys are only allowed to use implicit API’s. Category 1B RunnableEntitys are additionally allowed to invoke a server and use explicit API’s.

Category 2 In contrast to Category 1 RunnableEntitys, RunnableEntitys of category 2 always aggregate at least one WaitPoint, for more details see Figure 7.31. Typically, such a RunnableEntity implements an internal loop where one iteration through the loop is triggered whenever a WaitPoint is resolved. (cid:99)()

1Category 2 RunnableEntitys usually have to be mapped to Extended Tasks, because only extended tasks provide the task state WAITING.

#@SECTION: 7.2.4.5 Arguments of a Runnable Entity
#@CLASS: ArgumentDataPrototype
<!-- LLM_CONTEXT FOR CLASS ArgumentDataPrototype: Attributes=[adminData, annotation, category, desc, direction, introduction, longName, serverArgumentImplPolicy, shortName, shortNameFragment, swDataDefProps, type, typeBlueprint, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: OperationInvokedEvent
<!-- LLM_CONTEXT FOR CLASS OperationInvokedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: PortAPIOption
<!-- LLM_CONTEXT FOR CLASS PortAPIOption: Attributes=[enableTakeAddress, errorHandling, indirectAPI, port, portArgValue, variationPoint] (包含继承及相关属性) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: RunnableEntityArgument
<!-- LLM_CONTEXT FOR CLASS RunnableEntityArgument: Attributes=[symbol] (包含继承及相关属性) -->
#@CLASS: BswModuleEntry
<!-- LLM_CONTEXT FOR CLASS BswModuleEntry: Attributes=[adminData, annotation, argument, blueprintPolicy, callType, category, desc, executionContext, introduction, isReentrant, isSynchronous, longName, returnType, role, serviceId, shortName, shortNameFragment, shortNamePattern, swServiceImplPolicy, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable] (直接父类) -->
#@CLASS: SwServiceArg
<!-- LLM_CONTEXT FOR CLASS SwServiceArg: Attributes=[direction, swArraysize, swDataDefProps, variationPoint] (包含继承及相关属性) -->

In many cases an RTE generator will be able to figure out not only the number and data type of arguments to a RunnableEntity but also the name of the arguments. In some cases, however, formal support from the upstream templates is required to facilitate this task.

[TPS_SWCT_01311] Name of an operation argument (cid:100) This support is available by means of the meta-class RunnableEntityArgument that contributes the name of the argument by means of the value of the attribute symbol.

As a RunnableEntity might need to define many arguments the aggregation of RunnableEntityArgument at RunnableEntity in the role argument has the multiplicity 0..* and as the order of these arguments is significant the meta-model defines the aggregation as ordered. (cid:99)()

as the arguments are ordered they do not need to be Referrable in order to be able to identify individual arguments

[constr_1164] Number of arguments owned by a RunnableEntity (cid:100) If a given RunnableEntity owns RunnableEntityArguments in the role argument, then the number of these RunnableEntityArguments shall be identical to the number of applicable portArgValues of the PortAPIOption that references the PortPrototype that in turn is referenced by the OperationInvokedEvent that references the RunnableEntity plus the number of ArgumentDataPrototypes aggregated in the role argument by the ClientServerOperation referenced by said OperationInvokedEvent. (cid:99)()

[constr_1165] Applicability of RunnableEntityArgument (cid:100) The existence of a RunnableEntityArgument is limited to RunnableEntitys triggered by a ClientServerOperation. (cid:99)()

[TPS_SWCT_01312] RunnableEntity has a mapping to BswModuleEntry (cid:100) The existence of RunnableEntityArguments in the role argument owned by a RunnableEntity shall be ignored by an RTE generator if a mapping to a BswModuleEntry exists. In this case the name of arguments to the RunnableEntity shall be derived from the applicable SwServiceArgs owned by the mapped BswModuleEntry. (cid:99)()

Figure 7.6: Arguments of a RunnableEntity
Table 7.5: RunnableEntityArgument

#@SECTION: 7.2.5 Activation Reason of a Runnable Entity
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ExecutableEntityActivationReason
<!-- LLM_CONTEXT FOR CLASS ExecutableEntityActivationReason: Attributes=[bitPosition, shortName, shortNameFragment, symbol] (包含继承及相关属性); Generalization=[ImplementationProps] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: TimingEvent
<!-- LLM_CONTEXT FOR CLASS TimingEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, period, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

It is feasible to activate a given RunnableEntity by means of several RTEEvents. In many cases, it is therefore necessary to retrieve the information about the activating RTEEvent from within the implementation of the RunnableEntity.

As a typical use case, consider a RunnableEntity that is cyclically activated (by means of a TimingEvent) and in addition it shall also be executed sporadically, e.g. in response to the reception (DataReceivedEvent) of a dataElement.

Figure 7.7: ExecutableEntityActivationReason and RunnableEntity

[TPS_SWCT_01469] RTE API for retrieving the current activation reason (cid:100) The aggregation of a ExecutableEntityActivationReason allows for the RTE generator to create an RTE API for retrieving the current activation reason. (cid:99)(RS_SWCT_03045)

For details about the implementation of this feature, please refer to the speciﬁcation of the RTE [2]

[constr_1226] Applicable range for ExecutableEntityActivationReason.bitPosition (cid:100) The value of attribute ExecutableEntityActivationReason.bitPosition shall be in the range of 0 .. 31. (cid:99)()

[constr_1227] Value of attribute ExecutableEntityActivationReason.bitPosition shall be unique (cid:100) The value of attributes ExecutableEntityActivationReason.bitPosition and ExecutableEntityActivationReason.symbol shall be unique in the context of the enclosing RunnableEntity. (cid:99)()

[constr_1228] RTEEvent that is referenced by a WaitPoint in the role trigger shall not reference ExecutableEntityActivationReason (cid:100) An RTEEvent that is referenced by a WaitPoint in the role trigger shall not reference ExecutableEntityActivationReason in the role activationReasonRepresentation. (cid:99)()

The rationale for the existence of [constr_1228] is obviously that in the described situation the RunnableEntity is already activated and therefore the mentioned RTEEvent does not deliver any information related to the activation reason of said RunnableEntity.

Table 7.6: ExecutableEntityActivationReason

Please note that the attribute ExecutableEntityActivationReason.symbol is needed for the generation of a unique identiﬁer that represents the speciﬁc activation reason in the RTE code.

#@SECTION: 7.2.6 Runnable Entity for Initialization Purpose
#@CLASS: AsynchronousServerCallPoint
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, operation, shortName, shortNameFragment, timeout, variationPoint] (包含继承及相关属性); Generalization=[ServerCallPoint] (直接父类) -->
#@CLASS: AsynchronousServerCallResultPoint
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallResultPoint: Attributes=[adminData, annotation, asynchronousServerCallPoint, category, desc, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: InitEvent
<!-- LLM_CONTEXT FOR CLASS InitEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SynchronousServerCallPoint
<!-- LLM_CONTEXT FOR CLASS SynchronousServerCallPoint: Attributes=[adminData, annotation, calledFromWithinExclusiveArea, category, desc, introduction, longName, operation, shortName, shortNameFragment, timeout, variationPoint] (包含继承及相关属性); Generalization=[ServerCallPoint] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: ExecutableEntity
<!-- LLM_CONTEXT FOR CLASS ExecutableEntity: Attributes=[activationReason, adminData, annotation, canEnterExclusiveArea, category, desc, exclusiveAreaNestingOrder, introduction, longName, minimumStartInterval, reentrancyLevel, runsInsideExclusiveArea, shortName, shortNameFragment, swAddrMethod] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswModuleEntity, RunnableEntity] (直接子类) -->

One way to make sure that certain initializations are applied before a software component enters its state of normal operation is to use the AUTOSAR mode management, in particular by defining a ModeDeclarationGroup that contains a specific ModeDeclaration with the semantics of representing a mode that is exclusively used for setting up and initializing a software-component.

However, this approach comes with a certain amount of footprint that may be acceptable in some cases but there may also be cases where a simpler approach comes in handy. The simple approach to initialization consists of a RunnableEntity that is triggered by a special kind of RTEEvent, i.e. the so-called InitEvent.

[TPS_SWCT_01525] InitEvent references a RunnableEntity in the role startOnEvent (cid:100) In addition to using a mode-based approach for executing initialization RunnableEntitys it is also possible to let an InitEvent reference a RunnableEntity in the role startOnEvent.

This approach to the initialization of software-components is orthogonal to the mode based approach. Especially, the RunnableEntitys triggered by an InitEvent are expected to be executed after the RTE has been fully initialized. This means restrictions regarding the availability of RTE APIs during the ECU initialization are not relevant for RunnableEntitys triggered by an InitEvent. (cid:99)(RS_SWCT_03290)

[constr_1257] No WaitPoints allowed (cid:100) A RunnableEntity referenced by an InitEvent in the role startOnEvent shall not aggregate a WaitPoint. (cid:99)()

Rationale: a WaitPoint may indefinitely defer the completion of the RunnableEntitys triggered by an InitEvent and therefore contradict the semantics of the RunnableEntity.

[constr_1258] Value of minimumStartInterval for RunnableEntitys triggered by an InitEvent (cid:100) The value of the attribute ExecutableEntity.minimumStartInterval for a RunnableEntitys that is triggered by an InitEvent shall always be set to 0. (cid:99)()

Rationale: it does not make sense to talk about intervals of activating RunnableEntitys triggered by an InitEvent as these are not supposed to be executed repeatedly.

[constr_1259] Aggregation of AsynchronousServerCallPoint and AsynchronousServerCallResultPoint (cid:100) A RunnableEntity referenced by an InitEvent in the role startOnEvent may aggregate an AsynchronousServerCallPoint but it shall not aggregate an AsynchronousServerCallResultPoint. (cid:99)()

Rationale: as mentioned before WaitPoints shall not be aggregated by a RunnableEntitys triggered by an InitEvent in the role startOnEvent. It is allowed (although considered unlikely to happen) to have an AsynchronousServerCallPoint but it is not allowed to fetch the result of the call within the same RunnableEntity.

A RunnableEntity triggered by an InitEvent in the role startOnEvent may aggregate a SynchronousServerCallPoint but the usage of this configuration is discouraged.

[constr_1260] No mode disabling for InitEvents (cid:100) An InitEvent shall not have a reference to a ModeDeclaration in the role disabledMode. (cid:99)()

Rationale: the concept of RunnableEntity triggered by an InitEvent is (as mentioned before) orthogonal to the mode concept and therefore shall be implemented independent of modes.

#@SECTION: 7.3 RTEEvent
#@CLASS: AbstractEvent
<!-- LLM_CONTEXT FOR CLASS AbstractEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswEvent, RTEEvent] (直接子类) -->
#@CLASS: AsynchronousServerCallReturnsEvent
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallReturnsEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: BackgroundEvent
<!-- LLM_CONTEXT FOR CLASS BackgroundEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataReceiveErrorEvent
<!-- LLM_CONTEXT FOR CLASS DataReceiveErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataSendCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataSendCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataWriteCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataWriteCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ExternalTriggerOccurredEvent
<!-- LLM_CONTEXT FOR CLASS ExternalTriggerOccurredEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, trigger, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: InitEvent
<!-- LLM_CONTEXT FOR CLASS InitEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: InternalTriggerOccurredEvent
<!-- LLM_CONTEXT FOR CLASS InternalTriggerOccurredEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ModeSwitchedAckEvent
<!-- LLM_CONTEXT FOR CLASS ModeSwitchedAckEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: OperationInvokedEvent
<!-- LLM_CONTEXT FOR CLASS OperationInvokedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SwcModeSwitchEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeSwitchEvent: Attributes=[activation, activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, mode, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: TimingEvent
<!-- LLM_CONTEXT FOR CLASS TimingEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, period, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: TransformerHardErrorEvent
<!-- LLM_CONTEXT FOR CLASS TransformerHardErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, trigger, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

During execution, several RTEEvents will occur, such as the reception of a remote invocation of a ClientServerOperation on a PPortPrototype or a timeout on an RPortPrototype that is not receiving the VariableDataPrototypes it expects to receive.

[TPS_SWCT_01314] RTEEvent (cid:100) The description of an RTEEvent includes two aspects: 1. defining an RTEEvent 2. defining how the RTE should deal with the RTEEvent when it occurs. (cid:99)()

Table 7.7: AbstractEvent

Table 7.8: RTEEvent

Table 7.9: AsynchronousServerCallReturnsEvent

Table 7.10: DataSendCompletedEvent

Table 7.11: DataWriteCompletedEvent

Table 7.12: DataReceivedEvent

Table 7.13: DataReceiveErrorEvent

Table 7.14: OperationInvokedEvent

Table 7.15: TimingEvent

[constr_2031] Period of TimingEvent shall be greater than 0 (cid:100) The value of the attribute period of TimingEvent shall be greater than 0. (cid:99)() 

Note that it is possible to override the attribute period on the level of instantiation. See [TPS_SWCT_02507] for more details.

Table 7.16: BackgroundEvent

Table 7.17: SwcModeSwitchEvent

Table 7.18: ModeSwitchedAckEvent

Table 7.19: ExternalTriggerOccurredEvent

Table 7.20: InternalTriggerOccurredEvent

Table 7.21: InitEvent

Table 7.22: TransformerHardErrorEvent

[constr_1397] Existence of attributes of TransformerHardErrorEvent (cid:100) For any given TransformerHardErrorEvent, either the attribute TransformerHardErrorEvent.operation or TransformerHardErrorEvent.trigger shall exist. (cid:99)() 
In other words, the attributes operation and trigger of meta-class TransformerHardErrorEvent shall be used mutually exclusive.

[TPS_SWCT_01315] Interaction of RunnableEntity with RTEEvent (cid:100) As described in the Virtual Functional Bus specification [3], the RunnableEntitys of an AtomicSwComponentType can interact with the occurrence of such RTEEvents in two ways: • the RTE can be instructed to enable a specific RunnableEntity when the RTEEvent occurs • the RTE can provide WaitPoints, that allow a RunnableEntity to block until an RTEEvent in a set of RTEEvents occurs. (cid:99)()

#@SECTION: 7.3.1 Deﬁning an Event
#@CLASS: AbstractEventAtpStructureElement
<!-- LLM_CONTEXT FOR CLASS AbstractEventAtpStructureElement: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: AsynchronousServerCallResultPoint
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallResultPoint: Attributes=[adminData, annotation, asynchronousServerCallPoint, category, desc, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: AsynchronousServerCallReturnsEvent
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallReturnsEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: AutosarDataPrototype
<!-- LLM_CONTEXT FOR CLASS AutosarDataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[DataPrototype] (直接父类); Childs=[ArgumentDataPrototype, ParameterDataPrototype, VariableDataPrototype] (直接子类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: DataReceiveErrorEvent
<!-- LLM_CONTEXT FOR CLASS DataReceiveErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataSendCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataSendCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataWriteCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataWriteCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ModeActivationKindAtpStructureElement
<!-- LLM_CONTEXT FOR CLASS ModeActivationKindAtpStructureElement: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeErrorBehavior
<!-- LLM_CONTEXT FOR CLASS ModeErrorBehavior: Attributes=[defaultMode, errorReactionPolicy] (包含继承及相关属性) -->
#@ENUM: ModeErrorReactionPolicyEnum
<!-- LLM_CONTEXT FOR ENUM ModeErrorReactionPolicyEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: ModeSwitchPoint
<!-- LLM_CONTEXT FOR CLASS ModeSwitchPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, modeGroup, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ModeSwitchedAckEvent
<!-- LLM_CONTEXT FOR CLASS ModeSwitchedAckEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: OperationInvokedEvent
<!-- LLM_CONTEXT FOR CLASS OperationInvokedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcModeManagerErrorEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeManagerErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, modeGroup, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: SwcModeSwitchEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeSwitchEvent: Attributes=[activation, activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, mode, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: TimingEvent
<!-- LLM_CONTEXT FOR CLASS TimingEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, period, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: VariableAccess
<!-- LLM_CONTEXT FOR CLASS VariableAccess: Attributes=[accessedVariable, adminData, annotation, category, desc, introduction, longName, scope, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

The description of the SwcInternalBehavior includes a description of all The description of RTEEvents that the SwcInternalBehavior of the AtomicSwComponentType relies on.

[TPS_SWCT_01316] Abstract base class RTEEvent (cid:100) The meta-class RTEEvent shows up as an “abstract” base-class (see e.g. Figure 7.8) in the meta-model: the exact attributes of the RTEEvent depend on the speciﬁc sub-class of RTEEvent that is used for the purpose. (cid:99)()

Figure 7.8: RTEEvents used in the context of sender/receiver communication

Figure 7.9: RTEEvents used in the context of client/server communication

Figure 7.10: RTEEvents used in the context of mode communication

Please note that more explanation about the semantics of the meta-classes SwcModeManagerErrorEvent and ModeErrorBehavior can be found in section 9.4.

Figure 7.11: RTEEvent used in the context of data transformation

Figure 7.12: RTEEvents for purposes other than communication

The details of the various kinds of concrete RTEEvents (such as the TimingEvent, DataSendCompletedEvent, etc.), is described in chapters 7.5.1, 7.5.2 and 7.2.3.

#@SECTION: 7.3.2 Deﬁning how to Respond to an Event
#@CLASS: AbstractEventAtpStructureElement
<!-- LLM_CONTEXT FOR CLASS AbstractEventAtpStructureElement: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: AsynchronousServerCallReturnsEvent
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallReturnsEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataSendCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataSendCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ExternalTriggerOccurredEvent
<!-- LLM_CONTEXT FOR CLASS ExternalTriggerOccurredEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, trigger, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: InitEvent
<!-- LLM_CONTEXT FOR CLASS InitEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: InternalTriggerOccurredEvent
<!-- LLM_CONTEXT FOR CLASS InternalTriggerOccurredEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: InternalTriggeringPoint
<!-- LLM_CONTEXT FOR CLASS InternalTriggeringPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swImplPolicy, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ModeSwitchedAckEvent
<!-- LLM_CONTEXT FOR CLASS ModeSwitchedAckEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcModeSwitchEvent
<!-- LLM_CONTEXT FOR CLASS SwcModeSwitchEvent: Attributes=[activation, activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, mode, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: TimingEvent
<!-- LLM_CONTEXT FOR CLASS TimingEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, period, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

[TPS_SWCT_01317] RTE triggers RunnableEntity in response to occurring RTEEvent (cid:100) If the software-component description contains a reference from an RTEEvent to a RunnableEntity in the role startOnEvent it is the responsibility of the RTE to trigger the execution of the corresponding RunnableEntity when the RTEEvent occurs. (cid:99)()

[TPS_SWCT_01318] RunnableEntity and WaitPoint (cid:100) In case the RunnableEntity wants to block and wait for RTEEvents (which makes the RunnableEntity into a cat. 2 RunnableEntity), the description of the RunnableEntity may include the definition of a WaitPoint. 
Such a WaitPoint (see Figure 7.13) contains a reference to an RTEEvent that can unblock the specific WaitPoint. In other words: the WaitPoint will block until the referenced RTEEvents occurs or the period specified in the attribute timeout expires. (cid:99)()

Figure 7.13: Description of the interaction between an RTEEvent and RunnableEntitys

[constr_1090] WaitPoint and RunnableEntity (cid:100) A single RunnableEntity can actually wait only at a single WaitPoint provided that the RunnableEntity can only be scheduled a single time3. (cid:99)()

[constr_1091] RTEEvents that can unblock a WaitPoint (cid:100) The only RTEEvents that are qualified for unblocking a WaitPoint are:
• DataReceivedEvent
• DataSendCompletedEvent
• ModeSwitchedAckEvent
• AsynchronousServerCallReturnsEvent
(cid:99)()

[TPS_SWCT_01319] RTEEvent can be used to trigger WaitPoints in different RunnableEntitys (cid:100) It is in general possible that a single RTEEvent can be used to trigger WaitPoints in different RunnableEntitys. (cid:99)()

This constraint is valid at least in the OSEK standard where an extended task (that can have wait points) can only exist a single time in the context of the scheduler.

Concerning DataReceivedEvents consider as well [constr_2021].

Table 7.23: WaitPoint

[constr_1096] SwcModeSwitchEvent and WaitPoint (cid:100) A RunnableEntity that has a WaitPoint shall not be referenced by a SwcModeSwitchEvent. (cid:99)()

[TPS_SWCT_01320] RunnableEntitys of category 2 (cid:100) RunnableEntitys that aggregate a WaitPoint are by definition of category 2 and therefore are not required to terminate ever. It is therefore difficult to let a RunnableEntity of category 2 implement a mode switch. (cid:99)()

[constr_1097] RunnableEntity that has a WaitPoint (cid:100) A RunnableEntity that has a WaitPoint shall not be referenced by a RTEEvent that has a reference in the role disabledMode. (cid:99)()

[TPS_SWCT_01324] Mode switches need to be completed in finite time (cid:100) Mode switches need to be completed in finite time and a RunnableEntity that has a WaitPoint can never guarantee that the WaitPoint is resolved within finite time. (cid:99)()

In addition to this, the RunnableEntity with a WaitPoint that would be affected by a mode disabling would typically already run when the mode disabling applies. It could not be terminated at this point in time.

#@SECTION: 7.4 Communication among Runnable Entities
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

It is taken for granted that particular RunnableEntitys within a specific AtomicSwComponentType will need to communicate among each other.

[TPS_SWCT_01321] Communication among RunnableEntitys (cid:100) The RTE needs to provide synchronization mechanisms to the RunnableEntitys such that safe (in the multi-threading sense) exchange of data is possible.

In this case, the use of PortPrototypes is (although technically feasible) not required for the purpose. (cid:99)(RS_SWCT_00120)

[TPS_SWCT_01592] Communication among RunnableEntitys of different instances of the same AtomicSwComponentType (cid:100) The communication among RunnableEntitys of different instances of the same AtomicSwComponentType is only supported via PortPrototypes. (cid:99)(RS_SWCT_00120)

Several concepts for implementing communication among RunnableEntitys can be identified.

As an introduction, the section 2.3.1 describes the various techniques that the RTE might use to provide efficient interaction between RunnableEntitys within one AtomicSwComponentType.

Two possible approaches for formal specification of this kind of communication are described:
• Specifying that several RunnableEntitys belong in a specific ExclusiveArea
• Specifying the data exchanged between the RunnableEntitys

#@SECTION: 7.4.1 Description Possibility 1: Exclusive Area
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: InternalBehavior
<!-- LLM_CONTEXT FOR CLASS InternalBehavior: Attributes=[adminData, annotation, category, constantMemory, constantValueMapping, dataTypeMapping, desc, exclusiveArea, exclusiveAreaNestingOrder, introduction, longName, shortName, shortNameFragment, staticMemory] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[BswInternalBehavior, SwcInternalBehavior] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SynchronousServerCallPoint
<!-- LLM_CONTEXT FOR CLASS SynchronousServerCallPoint: Attributes=[adminData, annotation, calledFromWithinExclusiveArea, category, desc, introduction, longName, operation, shortName, shortNameFragment, timeout, variationPoint] (包含继承及相关属性); Generalization=[ServerCallPoint] (直接父类) -->
#@CLASS: ExclusiveArea
<!-- LLM_CONTEXT FOR CLASS ExclusiveArea: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: ExclusiveAreaNestingOrder
<!-- LLM_CONTEXT FOR CLASS ExclusiveAreaNestingOrder: Attributes=[exclusiveArea, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[Referrable] (直接父类) -->

This section describes how the concept of ExclusiveAreas can be used in the description of the SwcInternalBehavior of an AtomicSwComponentType. Please note that ExclusiveAreas are actually owned by the base class of SwcInternalBehavior, i.e. InternalBehavior. These ExclusiveAreas do not imply a specific implementation (e.g. with mutual-exclusion semaphores).

Table 7.24: ExclusiveArea

[TPS_SWCT_01031] ExclusiveArea (cid:100) An ExclusiveArea (please find details about the formal definition of this meta-class in Figure 7.14) merely specifies a constraint on the scheduling policy and configuration of the RTE: If two or more RunnableEntitys refer to the same ExclusiveArea only one of these RunnableEntitys is allowed to be executed while being inside that ExclusiveArea. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

In other words: these RunnableEntitys shall not run concurrently (preempt each other) while executing inside the ExclusiveArea.

Figure 7.14: Description of logical exclusive areas

[TPS_SWCT_01049] Two ways to use the ExclusiveAreas (cid:100) There are in general two ways to use the ExclusiveAreas. During its execution, a RunnableEntity can enter and exit an ExclusiveArea (in which case ExecutableEntity.canEnterExclusiveArea shall exist, see chapter 7.4.1.2). As an alternative, it can be specified that the entire execution of a given RunnableEntity shall be guarded by an ExclusiveArea (this requires the existence of ExecutableEntity.runsInsideExclusiveArea, see chapter 7.4.1.1). (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

Figure 7.15: Description of nested usage of ExclusiveArea

[TPS_SWCT_01457] ExclusiveAreaNestingOrder (cid:100) The optional ExclusiveAreaNestingOrders shall (if used at all) describe possible nesting orders (including single ExclusiveAreas) which can occur in the RunnableEntity. Each possible locking situation requires its own ExclusiveAreaNestingOrder. (cid:99)(RS_SWCT_03055)

[TPS_SWCT_01458] Indicate that the locking behavior is fully described for RunnableEntity (cid:100) All ExclusiveAreas which are configured in the InternalBehavior should be referenced by an ExclusiveAreaNestingOrder to indicate that the locking behavior is fully described for this RunnableEntity. (cid:99)(RS_SWCT_03055)

[TPS_SWCT_01459] Locking behavior is not described for this RunnableEntity (cid:100) If ExclusiveAreas are not referenced by any ExclusiveAreaNestingOrder (this is the default scenario), this means that the locking behavior is not described for this RunnableEntity and the provided information might be incomplete and cannot be used for a global offline analysis of locking behavior. (cid:99)(RS_SWCT_03055)

Figure 7.16: Nested usage of ExclusiveArea and the impact on SynchronousServerCallPoint

An ExclusiveAreaNestingOrder is aggregated by the InternalBehavior that in turn also owns RunnableEntity.

[TPS_SWCT_01460] Relation of SynchronousServerCallPoint to ExclusiveAreaNestingOrder (cid:100) In case other RunnableEntitys are invoked synchronously from within the RunnableEntity the ExclusiveAreaNestingOrder can then be referenced by one or several SynchronousServerCallPoints to specify the calling environment of the invoked server with regard to ExclusiveAreas. (cid:99)(RS_SWCT_03055)

The purpose of this configuration is to analyze the resource locking behavior for complete call trees.

Table 7.25: ExclusiveAreaNestingOrder

#@SECTION: 7.4.1.1 Entire Runnable Runs in the Exclusive Area
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: ExclusiveArea
<!-- LLM_CONTEXT FOR CLASS ExclusiveArea: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

[TPS_SWCT_01050] RunnableEntity always runs inside an ExclusiveArea (cid:100) In the ﬁrst approach, the formal description speciﬁes that certain RunnableEntitys always run inside an ExclusiveArea. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

For example, if the formal description speciﬁes that both RunnableEntity ’r1’ and RunnableEntity ’r2’ run within ExclusiveArea ’s1’, the RTE shall make sure that RunnableEntitys ’r1’ and ’r2’ never run concurrently; the scheduler should never preempt ’r1’ to run ’r2’.

Note that this pattern does not force the RTE to implement this by using semaphores or mutexes that are taken before the RunnableEntity starts and given when the RunnableEntity returns. It only obliges the RTE to make sure that both RunnableEntitys are never running concurrently.

This requirement could be implemented by several of the implementation strategies described above. For example:

1. Scheduling strategy: if, for example, RunnableEntitys ’r1’ and ’r2’ are mapped to the same task, the criterion is automatically satisﬁed. For this purpose it is necessary to make sure that the OS can only execute a single instance of the task into which the RunnableEntitys are put.

2. Mutual exclusion semaphores: in case ’r1’ and ’r2’ are mapped to different tasks is executing (’T1’, respectively ’T2’), the OS shall make sure that while ’T1’ ’r1’, ’T2’ running ’r2’ can never preempt it and vice-versa. This could be implemented by taking a mutual-exclusion semaphore before executing ’r1’ (resp. ’r2’) in the context of ’t1’ (resp. ’t2’) and returning the semaphore on exiting the RunnableEntity.

#@SECTION: 7.4.1.2 Runnable would Dynamically Enter and Leave the Exclusive Area
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

[TPS_SWCT_01051] RunnableEntity explicitly enters and leaves a specific ExclusiveArea (cid:100) In the second approach, the RunnableEntity would explicitly make API-calls to the RTE within the implementation of the RunnableEntity to enter and leave a specific ExclusiveArea. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

This could, for example, be implemented by means of the priority ceiling concept described in chapter 2.3.1.3.

Additionally it is possible to define the execution time the RunnableEntity will spend in this ExclusiveArea segment. Please note that although this aspect is described in [7] the concept can be applied to software-components as well.

#@SECTION: 7.4.2 Description Possibility 2: Inter-Runnable Variable
#@CLASS: AutosarVariableRef
<!-- LLM_CONTEXT FOR CLASS AutosarVariableRef: Attributes=[autosarVariable, autosarVariableInImplDatatype, localVariable] (包含继承及相关属性) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableAccess
<!-- LLM_CONTEXT FOR CLASS VariableAccess: Attributes=[accessedVariable, adminData, annotation, category, desc, introduction, longName, scope, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ExclusiveArea
<!-- LLM_CONTEXT FOR CLASS ExclusiveArea: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->

For certain cases the ExclusiveArea concept does not provide enough information to configure the RTE correctly. In these cases it may be advised to opt for a different approach that is based on the guarded access to variables protected by the RTE.

For the purpose of identifying pieces of data that shall be accessed concurrently from different RunnableEntitys formal support is required. In AUTOSAR, this aspect is summarized under the term "inter-runnable variable".

[TPS_SWCT_01052] Inter-runnable variable (cid:100) These so-called "inter-runnable variables" are described with the element VariableDataPrototype aggregated in the role explicitInterRunnableVariable or implicitInterRunnableVariable. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

[TPS_SWCT_01053] Relationship of interchanged data with RunnableEntitys (cid:100) Furthermore, the relationship of these data with RunnableEntitys shall be specified. For this specific purpose, RunnableEntity aggregates VariableAccess in the roles readLocalVariable and writtenLocalVariable. Also, SwcInternalBehavior aggregates VariableDataPrototype in the roles explicitInterRunnableVariable and implicitInterRunnableVariable. The connection between RunnableEntity and the explicitInterRunnableVariable and implicitInterRunnableVariable is created if the reference AutosarVariableRef.localVariable to the respective VariableDataPrototype exists. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

Figure 7.17: implicitInterRunnableVariable vs. explicitInterRunnableVariable

[TPS_SWCT_01521] Use AutosarVariableRef.localVariable for referencing inter-runnable variables (cid:100) A RunnableEntity that defines a VariableAccess in role writtenLocalVariable and readLocalVariable shall make use of AutosarVariableRef.localVariable. (cid:99)()

[constr_2026] Referenced VariableDataPrototype from AutosarVariableRef of VariableAccess in role writtenLocalVariable and readLocalVariable (cid:100) A VariableDataPrototype in the localVariable reference needs to be owned by the same SwcInternalBehavior as this RunnableEntity belongs to, and the referenced VariableDataPrototype has to be defined in the role implicitInterRunnableVariable or explicitInterRunnableVariable. (cid:99)()

Obviously, the data type of an implicitInterRunnableVariable or explicitInterRunnableVariable is described by the data type of the VariableDataPrototype (which is derived from DataPrototype).

[TPS_SWCT_01637] Initial value for a specific implicitInterRunnableVariable or explicitInterRunnableVariable (cid:100) It is possible (but not mandatory) to define an initial value for a specific implicitInterRunnableVariable or explicitInterRunnableVariable. For this purpose the VariableDataPrototype in the role of explicitInterRunnableVariable or implicitInterRunnableVariable is able to aggregate a ValueSpecification in the role initValue. (cid:99)(RS_SWCT_02090)

The statement made by [TPS_SWCT_01637] is reflected by Figure 7.17

[TPS_SWCT_01522] No initial value is specified for implicitInterRunnableVariable or explicitInterRunnableVariable (cid:100) Please note that the behavior is undefined if no initial value is specified and a RunnableEntity reads an implicitInterRunnableVariable or explicitInterRunnableVariable before it is actually written to by another RunnableEntity. (cid:99)()

As already mentioned before, the concept of an "inter-runnable variable" can be used in two different flavors This is indicated by the two different roles explicitInterRunnableVariable or implicitInterRunnableVariable in which the VariableDataPrototype serving as the "inter-runnable variable" is aggregated. These resemble the communication principles applied for the communication on the level of SwComponentTypes. Please note that the two different kinds of inter-runnable variables are accessed via different RTE [2] API calls.

[TPS_SWCT_01054] Semantics of the explicitInterRunnableVariable (cid:100) The semantics of the explicitInterRunnableVariable is that explicit implies the direct access to the value of an VariableDataPrototype used in the role explicitInterRunnableVariable or implicitInterRunnableVariable. By this means it is possible to get different values for a specific VariableDataPrototype each time the corresponding API call is executed. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

[TPS_SWCT_01055] Semantics of implicitInterRunnableVariable (cid:100) The implicitInterRunnableVariable corresponds to an execution model where the value of an VariableDataPrototype does not change (for the reading RunnableEntity, obviously) during the runtime of a RunnableEntity. This approach is in detail described in chapter 2.3.1.4. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

[constr_1296] DataPrototypes used as explicitInterRunnableVariable or implicitInterRunnableVariable and category DATA_REFERENCE (cid:100) A VariableDataPrototype shall not be aggregated by SwcInternalBehavior in either the role explicitInterRunnableVariable or implicitInterRunnableVariable if the VariableDataPrototype (after potential indirections via TYPE_REFERENCE are resolved) is either typed by or mapped to an ImplementationDataType of category DATA_REFERENCE. (cid:99)()

(### 2.3.1.4 Implicit Communication by Means of Variable Copies

Another alternative is the usage of copies of concurrently accessed variables with state message semantics. Note that this approach directly corresponds to the semantics of “implicit” sender-receiver communication (see 7.5.1.2).

This means in particular that for a concurrently used variable a copy is created on which a `RunnableEntity` entity can work without any danger of data inconsistency.

This concept requires additional code to write the value of the concurrently accessed variable to the copy before the `RunnableEntity` that accesses the variable is executed. The value of the copy shall be written back to the concurrently accessed variable after the `RunnableEntity` has been terminated.

This concept is sketched in Figure 2.4. Since it would be too expensive and error-prone to manually care about the copy routines it would be a good idea to leave the creation of the additional code to a suitable code generator.

*Figure 2.4: Generation of copy routines around `RunnableEntitys`*

**Description of Figure 2.4:**
Figure 2.4 illustrates how a "Code Generator" automates the creation of copy routines for `RunnableEntitys` to ensure data consistency. The diagram depicts:
1.  A box labeled "Code Generator" positioned at the top.
2.  Several arrows originate from the "Code Generator" and point downwards towards components of execution sequences.
3.  Below, there are two visual representations of an execution sequence involving a `RunnableEntity`. Each sequence is a horizontal bar divided into three segments:
    *   The first segment is labeled "Copy to", indicating a routine that copies data to a local variable before the `RunnableEntity` executes.
    *   The middle, larger segment is labeled "Runnable Entity", representing the actual runnable code.
    *   The third segment is labeled "Copy from", indicating a routine that copies data from the local variable back to the original shared variable after the `RunnableEntity` has finished.
The arrows from the "Code Generator" specifically point to the "Copy to" and "Copy from" segments, signifying that the code generator is responsible for generating these wrapper routines around each `RunnableEntity`. This automates the process of creating and managing these copies for implicit communication.

The additional copy routines as sketched in Figure 2.4 already protect the particular `RunnableEntitys` from unintended changes of concurrently accessed variables. It would, however, be possible to further optimize the process by reducing the additional code at the beginning and end of each task (see Figure 2.5).)

#@SECTION: 7.4.3 Inter Runnable Triggering
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: InternalTriggerOccurredEvent
<!-- LLM_CONTEXT FOR CLASS InternalTriggerOccurredEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: InternalTriggeringPoint
<!-- LLM_CONTEXT FOR CLASS InternalTriggeringPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swImplPolicy, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

The concept of inter-runnable triggering allows one RunnableEntity to trigger another RunnableEntity within an AtomicSwComponentType. This approach conceptually supports the decoupling of calculation and processing sequences inside a software-component.

By mappings of the InternalTriggerOccurredEvents to OS Tasks running at different priorities the triggered RunnableEntitys are in turn executed with a different priority as the triggering RunnableEntity.

For example, a cyclically triggered RunnableEntity which shall not exceed a certain worst case execution time (WCET) activates a second RunnableEntity if an error occurred in order to be able to execute a (potentially) time-consuming exception handling on a lower level of priority.

Figure 7.18: Model of software-component Inter Runnable Triggering

As illustrated in Figure 7.18 the triggering RunnableEntity needs an InternalTriggeringPoint.

The activation of RunnableEntitys in the same software-component instance is affected through the generic event-handling mechanism.

[TPS_SWCT_01523] Internal trigger event (cid:100) A RunnableEntity that shall be activated at the occurrence of an internal trigger event is defined by means of an InternalTriggerOccurredEvent which references the particular InternalTriggeringPoint and additionally the to-be-activated RunnableEntity. (cid:99)()

[TPS_SWCT_01022] Queued processing of internal trigger (cid:100) The attribute InternalTriggeringPoint.swImplPolicy can be used to specify a requirement whether or not the internal triggering of the enclosing RunnableEntity using the given InternalTriggeringPoint shall be queued. (cid:99)()

[constr_1182] Allowed values for InternalTriggeringPoint.swImplPolicy (cid:100) The only allowed values for the attribute swImplPolicy of meta-class InternalTriggeringPoint are either STANDARD (in which case the processing of the internal triggering does not use a queue) or QUEUED (in which case the processing of internal triggering positively uses a queue). (cid:99)()

Table 7.26: InternalTriggeringPoint
Table 7.27: InternalTriggerOccurredEvent

The description of the corresponding external trigger communication is contained in chapter 7.5.3.

#@SECTION: 7.5 Data Access of RunnableEntities
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

This section describes the communication properties of an AtomicSwComponentType. This is done mainly from the point of view of a RunnableEntity (the concept of a RunnableEntity is introduced in chapter 7.2).

However, the usage of a PortPrototype in a specific role within an AtomicSwComponentType also has an impact on communication behavior.

#@SECTION: 7.5.1 RunnableEntities and Sender Receiver Communication
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataReceiveErrorEvent
<!-- LLM_CONTEXT FOR CLASS DataReceiveErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: DataSendCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataSendCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->

This section describes aspects relevant for the sender-receiver communication of a software-component. These mainly influence the behavior and API of the AUTOSAR RTE.

[TPS_SWCT_01322] Interaction patterns for the application of the sender receiver paradigm (cid:100) The possible interaction patterns for the application of the sender receiver paradigm are explained, namely: 
1. Data-access in a cat. 1 RunnableEntity, 
2. explicit sending, 
3. the DataSendCompletedEvent: dealing with the success/failure of an explicit send, and 
4. the DataReceivedEvent: responding to the reception of data 
5. the DataReceiveErrorEvent: notifying an error concerning the reception of data. (cid:99)(RS_SWCT_00200)

#@SECTION: 7.5.1.1 Terminology
The AUTOSAR meta-model foresees two different approaches for sender-receiver communication. These are described in detail in chapters 7.5.1.2 and 7.5.1.3. However, it turned out that it is rather cumbersome to discuss issues of communication approaches directly on the basis of meta-classes and their attributes.

Therefore, it seems appropriate to introduce a dedicated terminology for this purpose. The approach eventually selected was originally introduced by the contributors to the RTE specification.

This terminology proposes to use the term “implicit” for communication based on data-access (for more information about details of this approach please consult chapter 7.5.1.2) and “explicit” for communication based on so-called data-points (please refer to chapter 7.5.1.3).

The motivation for the differentiation between “implicit” and “explicit” was originally the characteristics of the RTE specification that foresaw an API for handling a dataSendPoint or dataReceivePointByValue in contrast to the data-access that was supposed to be part of the function signature (therefore, no API was required) of a specific RunnableEntity.

Although the specification of the RTE changed in the meantime (and the original motivation no longer applies) it turned out that the terminology based on “implicit” and “explicit” communication was already widely used within AUTOSAR.

As no consensus could be reached over alternative proposals this terminology approach is taken over by this document as well.

#@SECTION: 7.5.1.2 Data Access
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: AutosarVariableRef
<!-- LLM_CONTEXT FOR CLASS AutosarVariableRef: Attributes=[autosarVariable, autosarVariableInImplDatatype, localVariable] (包含继承及相关属性) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PRPortPrototype
<!-- LLM_CONTEXT FOR CLASS PRPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedRequiredInterface, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableAccess
<!-- LLM_CONTEXT FOR CLASS VariableAccess: Attributes=[accessedVariable, adminData, annotation, category, desc, introduction, longName, scope, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@ENUM: VariableAccessScopeEnum
<!-- LLM_CONTEXT FOR ENUM VariableAccessScopeEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

[TPS_SWCT_01323] Read and write access to a dataElement (cid:100) The SwcInternalBehavior may specify that a RunnableEntity needs read-access (respectively write-access) to the VariableDataPrototypes in the role dataElement of an RPortPrototype (respectively PPortPrototype, or PRPortPrototype). (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01325] Read and write access is only applicable for RunnableEntitys of category 1 (cid:100) The usage of the data-access mechanism to the VariableDataPrototypes is appropriate for cat. 1 RunnableEntitys only because it by concept guarantees finite response time (as opposed to e.g. unlimited blocking wait for some data). (cid:99)(RS_SWCT_00200)

For more explanation, let’s suppose a cat. 2 RunnableEntity would have a dataReadAccess and a dataWriteAccess. The received dataElement would be updated before the RunnableEntity actually starts being executed and even if the RunnableEntity runs for a very long time the value of the dataElement would remain as is and never change.

On the other hand, the RunnableEntity might use its dataWriteAccess to perform a write access on the dataElement but the actual value might never make it beyond the RunnableEntity because:
1. the latter is not required to terminate ever and
2. the actual write access is executed after the RunnableEntity terminates.

Figure 7.19: DataReadAccess and DataWriteAccess

Table 7.28: VariableAccess

Table 7.29: VariableAccessScopeEnum

[TPS_SWCT_01326] Constrain the scope of a specific communication (cid:100) The purpose of the attribute scope of meta-class VariableAccess is to constrain the scope of the corresponding communication. The main use-case for this ability is the development of a software-component where certain end-points of communication from or to the software-component are known to fulfill a certain constraint, e.g. execute within the same partition. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01328] Default value of attribute scope (cid:100) The default value of attribute scope is set to communicationInterEcu. (cid:99)(RS_SWCT_00200)

[constr_1141] Applicability of the scope attribute (cid:100) The attribute scope of meta-class VariableAccess shall only be applied with respect to the aggregation of VariableAccess in the following roles:
• dataReadAccess
• dataWriteAccess
• dataSendPoint
• dataReceivePointByValue
• dataReceivePointByArgument
(cid:99)()

[TPS_SWCT_01329] Access to specific data is implemented by means of aggregating the meta-class VariableAccess in specific roles (cid:100) Please note that from the formal point of view access to specific data is implemented by means of aggregating the meta-class VariableAccess in specific roles. This means that dataReadAccess for a read-access while the write-access is defined by means of aggregating VariableAccess in the role dataWriteAccess. (cid:99)(RS_SWCT_00200)

This aspect is depicted in Figure 7.19. The following constraints apply to the reference target of the AutosarVariableRef of VariableAccess in role dataReadAccess or dataWriteAccess.

[constr_2002] Referenced VariableDataPrototype from AutosarVariableRef of VariableAccess in role dataReadAccess (cid:100) A VariableAccess in the role dataReadAccess shall refer to an RPortPrototype or PRPortPrototype that is typed by either a SenderReceiverInterface or a NvDataInterface. (cid:99)()

[constr_2003] Referenced VariableDataPrototype from AutosarVariableRef of VariableAccess in role dataWriteAccess (cid:100) A VariableAccess in the role dataWriteAccess shall refer to a PPortPrototype or PRPortPrototype that is typed by either a SenderReceiverInterface or a NvDataInterface. (cid:99)()

By access with VariableAccess in the dataReadAccess role always the last value of the VariableDataPrototype buffered before the RunnableEntity starts will be read during the execution of the RunnableEntity. It would therefore not make any sense to provide a queue of values for the purpose of accessing a dataElement in the role dataReadAccess.

[constr_2020] dataReadAccess can not be used for queued communication (cid:100) The swImplPolicy of the VariableDataPrototype referenced by a VariableAccess in role dataReadAccess shall not be set to queued. (cid:99)()

[constr_1256] Acknowledgement feedback in n:1 writer case (cid:100) Within the scope of one SwcInternalBehavior, it is not allowed that two or more aggregated RunnableEntitys own either dataSendPoints or dataWriteAccesss that in turn point to the identical accessedVariable.autosarVariable.targetDataPrototype if the attribute transmissionAcknowledge exists in the context of the SenderComSpec owned by the dataSendPoint.accessedVariable.autosarVariable.portPrototype (or the respective construct for dataWriteAccess) that also refers to said dataElement. (cid:99)()

The background of [constr_1256] is that if two or more RunnableEntitys exist that can write to the identical dataElement it may happen that more than one RunnableEntity actually write to the respective dataElement before the "first" acknowledgement is received. In this case it will never be possible to determine exactly which transmission has been acknowledged.

#@SECTION: 7.5.1.3 Explicit Sending and Receiving
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: AutosarVariableRef
<!-- LLM_CONTEXT FOR CLASS AutosarVariableRef: Attributes=[autosarVariable, autosarVariableInImplDatatype, localVariable] (包含继承及相关属性) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PRPortPrototype
<!-- LLM_CONTEXT FOR CLASS PRPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedRequiredInterface, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableAccess
<!-- LLM_CONTEXT FOR CLASS VariableAccess: Attributes=[accessedVariable, adminData, annotation, category, desc, introduction, longName, scope, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

[TPS_SWCT_01330] RunnableEntity can also have dataSendPoints (cid:100) A RunnableEntity can also have dataSendPoints (i.e. aggregate VariableAccess in the role dataSendPoint). Using an instanceRef association, these eventually reference a VariableDataPrototype in the context of an AbstractProvidedPortPrototype, owned by the AtomicSwComponentType that is associated with the RunnableEntity that in turn owns the dataSendPoint. (cid:99)(RS_SWCT_00200)

[constr_2004] Referenced VariableDataPrototype from AutosarVariableRef of VariableAccess in role dataSendPoint (cid:100) A VariableAccess in the role dataSendPoint shall refer to a PPortPrototype or PRPortPrototype that is typed by either a SenderReceiverInterface or a NvDataInterface. (cid:99)()

[TPS_SWCT_01331] dataWriteAccess vs. dataSendPoint (cid:100) As opposed to the dataWriteAccess:
• Using the dataSendPoint, the RunnableEntity needs to explicitly "send" through an API; when using a dataWriteAccess, the RunnableEntity only needs to modify the value of certain variables.
• Using dataSendPoint, the Runnable can decide to "send" an arbitrary number of times; when using dataWriteAccess the new value of the VariableDataPrototype is not made available before the RunnableEntity returns (exits the "Running" state).
• The presence of a dataSendPoint per definition lets the corresponding RunnableEntity attain cat. 1B. (cid:99)(RS_SWCT_00200)

For more details, please refer to section 4.9.

Figure 7.20: DataSendPoint

[TPS_SWCT_01332] dataReceivePointByValue vs. dataReceivePointByArgument (cid:100) In analogy to explicitly sending data it is also possible to define explicit polling for new available data through a dataReceivePointByValue or dataReceivePointByArgument as shown in Figure 7.21. (cid:99)()

[constr_1277] SwDataDefProps.swImplPolicy of a VariableDataPrototype referenced by a VariableAccess aggregated in the role dataReceivePointByValue (cid:100) The SwDataDefProps.swImplPolicy of a VariableDataPrototype referenced by a VariableAccess aggregated in the role dataReceivePointByValue shall not be set to queued. (cid:99)()

Rationale for [constr_1277]: when using the return value of the applicable RTE API function to return the value of a VariableDataPrototype there is no way to provide an indication that the queue is empty. Therefore, the only safe approach is to not permit this scenario at all, hence the constraint.

Figure 7.21: Definition of an explicit request to receive data

[TPS_SWCT_01333] dataReceivePointByValue/dataReceivePointByArgument vs. dataReadAccess (cid:100) By using a dataReceivePointByValue or dataReceivePointByArgument instead of dataReadAccess the constraining access to the referenced VariableDataPrototype (other RunnableEntitys shall not change the VariableDataPrototype during the read execution) is limited to a short, well-defined amount of time. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01334] RunnableEntitys of category 1 may have dataReceivePointByValues/dataReceivePointByArguments (cid:100) Therefore, category 1 RunnableEntitys may also have dataReceivePointByValues/dataReceivePointByArguments and consequently become RunnableEntitys of category 1B, see section 7.2.4.4. (cid:99)(RS_SWCT_00200)

Similar to the dataReadAccess, constraints apply to the reference target of the AutosarVariableRef of VariableAccess in role dataReceivePointByValue or dataReceivePointByArgument.

[constr_2005] Referenced VariableDataPrototype from AutosarVariableRef of VariableAccess in role dataReceivePointByValue or dataReceivePointByArgument (cid:100) A VariableAccess in the role dataReceivePointByValue or dataReceivePointByArgument shall refer to an RPortPrototype or PRPortPrototype that is typed by either a SenderReceiverInterface or an NvDataInterface. (cid:99)()

[TPS_SWCT_01335] Combine dataReceivePointByValue or dataReceivePointByArgument with a WaitPoint (cid:100) In general, it is possible to combine a dataReceivePointByValue or dataReceivePointByArgument with a WaitPoint in the scope of a particular RunnableEntity. This allows for a call to a blocking receive routine implemented by the RTE. The time out attribute of meta-class WaitPoint can be used to specify the time until the blocking call expires. But in case of non-queued communication it is not supported that a DataReceivedEvent is used in combination with a WaitPoint (see [constr_2021]). This contradicts the approach of the last-is-best semantics. (cid:99)(RS_SWCT_00200)

[constr_2021] WaitPoint referencing a DataReceivedEvent can not be used for non-queued communication (cid:100) A WaitPoint referencing a DataReceivedEvent is permitted if and only if the swImplPolicy of the VariableDataPrototype referenced by this DataReceivedEvent is set to queued. (cid:99)()

#@SECTION: 7.5.1.4 DataSendCompletedEvent
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DataSendCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataSendCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PRPortPrototype
<!-- LLM_CONTEXT FOR CLASS PRPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedRequiredInterface, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: SenderComSpec
<!-- LLM_CONTEXT FOR CLASS SenderComSpec: Attributes=[compositeNetworkRepresentation, dataElement, handleOutOfRange, networkRepresentation, transmissionAcknowledge, usesEndToEndProtection] (包含继承及相关属性); Generalization=[PPortComSpec] (直接父类); Childs=[NonqueuedSenderComSpec, QueuedSenderComSpec] (直接子类) -->
#@CLASS: TransmissionAcknowledgementRequest
<!-- LLM_CONTEXT FOR CLASS TransmissionAcknowledgementRequest: Attributes=[timeout] (包含继承及相关属性) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

[TPS_SWCT_01336] dataSendPoint also allows for the deﬁnition of a DataSendCompletedEvent (cid:100) The dataSendPoint also allows for the deﬁnition of a DataSendCompletedEvent, as shown in Figure 7.20. This RTEEvent occurs when the data has been successfully sent or when an error has occurred during sending. (cid:99)(RS_SWCT_00200)

Please note that this feature can only be used if the AtomicSwComponentType describes the meaning of success or failure of the send operation.

In particular, via a SenderComSpec class different acknowledgement requests (in this case: successful transmission) can be attached to a PPortPrototype or PRPortPrototype, as is shown in Figure 4.33.

This will conﬁgure the RTE such that when data is sent the RTE will try to obtain the speciﬁed acknowledgement; possibly by waiting a certain timeout period.
Table 7.30: DataSendCompletedEvent

[constr_2033] Timeout of DataSendCompletedEvent (cid:100) The timeout value of a WaitPoint associated with a DataSendCompletedEvent shall have the same value as the corresponding value of TransmissionAcknowledgementRequest.timeout. (cid:99)()

#@SECTION: 7.5.1.5 DataWriteCompletedEvent
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DataWriteCompletedEvent
<!-- LLM_CONTEXT FOR CLASS DataWriteCompletedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PRPortPrototype
<!-- LLM_CONTEXT FOR CLASS PRPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedRequiredInterface, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: SenderComSpec
<!-- LLM_CONTEXT FOR CLASS SenderComSpec: Attributes=[compositeNetworkRepresentation, dataElement, handleOutOfRange, networkRepresentation, transmissionAcknowledge, usesEndToEndProtection] (包含继承及相关属性); Generalization=[PPortComSpec] (直接父类); Childs=[NonqueuedSenderComSpec, QueuedSenderComSpec] (直接子类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->

[TPS_SWCT_01557] dataWriteAccess also allows for the definition of a DataWriteCompletedEvent (cid:100) The dataWriteAccess also allows for the definition of a DataWriteCompletedEvent, as shown in Figure 7.22. This RTEEvent occurs when the data has been successfully sent or when an error has occurred during sending. (cid:99)(RS_SWCT_00200)

Please note that this feature can only be used if the AtomicSwComponentType describes the meaning of success or failure of the send operation.

In particular, via a SenderComSpec class different acknowledgement requests (in this case: successful transmission) can be attached to a PPortPrototype or PRPortPrototype, as is shown in Figure 4.33.

[TPS_SWCT_01558] DataWriteCompletedEvent cannot be combined with a WaitPoint (cid:100) Please note that a DataWriteCompletedEvent cannot be associated with a WaitPoint, see [constr_1091]. (cid:99)(RS_SWCT_00200)

However, it is possible to configure the RTE such that when data is sent, the RTE will try to obtain the specified acknowledgement; possibly by waiting a certain timeout period.

Table 7.31: DataWriteCompletedEvent

Figure 7.22: dataWriteAccess

#@SECTION: 7.5.1.6 DataReceivedEvent

#@CLASS: DataReceivedEvent
<!-- LLM_CONTEXT FOR CLASS DataReceivedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

[TPS_SWCT_01337] DataReceivedEvent (cid:100) A receiver is notified through the same event mechanism when a VariableDataPrototype is received. As shown in Figure 7.23, the DataReceivedEvent is directly associated with the corresponding VariableDataPrototype. (cid:99)(RS_SWCT_00200)

Figure 7.23: Receiver is notified by an event when new data has arrived

Table 7.32: DataReceivedEvent

#@SECTION: 7.5.1.7 DataReceiveErrorEvent
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DataReceiveErrorEvent
<!-- LLM_CONTEXT FOR CLASS DataReceiveErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, data, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: ReceiverComSpec
<!-- LLM_CONTEXT FOR CLASS ReceiverComSpec: Attributes=[compositeNetworkRepresentation, dataElement, externalReplacement, handleOutOfRange, handleOutOfRangeStatus, maxDeltaCounterInit, maxNoNewOrRepeatedData, networkRepresentation, replaceWith, syncCounterInit, transformationComSpecProps, usesEndToEndProtection] (包含继承及相关属性); Generalization=[RPortComSpec] (直接父类); Childs=[NonqueuedReceiverComSpec, QueuedReceiverComSpec] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

[TPS_SWCT_01338] DataReceiveErrorEvent (cid:100) A receiver is notified of DataReceiveErrorEvent through the activation of its RunnableEntity which is referenced by this RTEEvent. A DataReceiveErrorEvent includes a reference to a VariableDataPrototype and is raised by the RTE when an error concerning the reception of the referenced data is detected by the COM layer. The following cases present some situations which will cause the RTE to raise a DataReceiveErrorEvent:

• the RTE receives a signal-outdated notification from the COM layer when a monitored periodic signal is not received in time. The COM layer monitors the validity of the signal’s value based on the value of the aliveTimeout attribute of ReceiverComSpec referencing the VariableDataPrototype associated with the signal. If the time elapsed since the last update of a signal’s value exceeds its aliveTimeout then the COM layer notifies the RTE of a signal outdated error.

• The RTE receives a signal invalid notification from the COM layer when the COM layer detects that an incoming signal has the predefined “invalid” value. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01339] RTE activates RunnableEntity in response to DataReceiveErrorEvent (cid:100) A DataReceiveErrorEvent is used by the RTE to activate a RunnableEntity that is supposed to handle the above-mentioned errors. The error code will be made available to the activated RunnableEntity through the appropriate RTE API function. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01340] DataReceiveErrorEvent cannot be combined with a WaitPoint (cid:100) Please note that a DataReceiveErrorEvent cannot be associated with a WaitPoint, see [constr_1091]. It can only be used for the receiver software-component in a sender-receiver communication and its data reference is restricted to VariableDataPrototypes with their swImplPolicy attribute not set to queued. (cid:99)(RS_SWCT_00200)

Figure 7.24: DataReceiveErrorEvent references a Runnable and a VariableDataPrototype

[TPS_SWCT_01341] DataReceiveErrorEvent is directly associated with the corresponding VariableDataPrototype (cid:100) As shown in Figure 7.24, the DataReceiveErrorEvent is directly associated with the corresponding VariableDataPrototype and references the RunnableEntity that is activated due to the occurrence of this RTEEvent. (cid:99)(RS_SWCT_00200)

Table 7.33: DataReceiveErrorEvent

#@SECTION: 7.5.2 RunnableEntities and Client Server Communication
#@SECTION: 7.5.2.1 Invoking an Operation
#@CLASS: AbstractEvent
<!-- LLM_CONTEXT FOR CLASS AbstractEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswEvent, RTEEvent] (直接子类) -->
#@CLASS: AsynchronousServerCallPoint
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, operation, shortName, shortNameFragment, timeout, variationPoint] (包含继承及相关属性); Generalization=[ServerCallPoint] (直接父类) -->
#@CLASS: AsynchronousServerCallResultPoint
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallResultPoint: Attributes=[adminData, annotation, asynchronousServerCallPoint, category, desc, introduction, longName, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: AsynchronousServerCallReturnsEvent
<!-- LLM_CONTEXT FOR CLASS AsynchronousServerCallReturnsEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, eventSource, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: ServerCallPoint
<!-- LLM_CONTEXT FOR CLASS ServerCallPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, operation, shortName, shortNameFragment, timeout, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类); Childs=[AsynchronousServerCallPoint, SynchronousServerCallPoint] (直接子类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SynchronousServerCallPoint
<!-- LLM_CONTEXT FOR CLASS SynchronousServerCallPoint: Attributes=[adminData, annotation, calledFromWithinExclusiveArea, category, desc, introduction, longName, operation, shortName, shortNameFragment, timeout, variationPoint] (包含继承及相关属性); Generalization=[ServerCallPoint] (直接父类) -->
#@CLASS: WaitPoint
<!-- LLM_CONTEXT FOR CLASS WaitPoint: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, timeout, trigger] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->

[TPS_SWCT_01342] Invocation of a server operation (cid:100) A RunnableEntity invokes a server operation formally defined as a ClientServerOperation via an RPortPrototype of the enclosing SwComponentPrototype typed by a particular AtomicSwComponentType. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01343] Synchronous vs. asynchronous invocation (cid:100) A ClientServerOperation itself can be invoked either "synchronously" or "asynchronously". (cid:99)(RS_SWCT_00200) 

In the majority of cases the ClientServerOperation will be invoked at a different SwComponentPrototype but in general it would be possible to invoke a ClientServerOperation on the same SwComponentPrototype as well.

The decision whether a specific ClientServerOperation is called synchronously or asynchronously needs to be specified in the formal description of the corresponding AtomicSwComponentType, namely in the context of an SwcInternalBehavior (see Figure 7.25 for more details). But it is not supported to invoke the same instance of a ClientServerOperation synchronously and asynchronously together.

[constr_2022] Mutually exclusive use of SynchronousServerCallPoints and AsynchronousServerCallPoints (cid:100) A ClientServerOperation of a particular RPortPrototype shall be mutually exclusive referenced by either a SynchronousServerCallPoints or an AsynchronousServerCallPoints. (cid:99)()

[TPS_SWCT_01344] Consistency of values of timeout (cid:100) The timeout values need to be consistent in case of multiple ServerCallPoints referencing the same instance of ClientServerOperation. (cid:99)(RS_SWCT_00200)

[constr_2023] Consistency of timeout values (cid:100) The timeout values of all ServerCallPoints referencing the same instance of ClientServerOperation in a RPortPrototype shall be identical. (cid:99)()

[TPS_SWCT_01345] Synchronous operation invocation (cid:100) In case of a synchronous operation invocation the particular RunnableEntity merely needs a SynchronousServerCallPoint (see Figure 7.25). (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01346] Asynchronous operation invocation (cid:100) Asynchronous invocation is a bit more complex because it is necessary to specify how to respond to a notification about the completion of the corresponding operation. This is done using the generic RTEEvent mechanism: the notification about an asynchronously executed operation having completed is implemented as an AsynchronousServerCallReturnsEvent. Therefore, if an AsynchronousServerCallReturnsEvent is raised the RTE can either trigger the execution of a specific RunnableEntity or the AtomicSwComponentType can implement a WaitPoint that blocks the execution of the calling RunnableEntity until the AsynchronousServerCallReturnsEvent is recognized. (cid:99)(RS_SWCT_00200)

Figure 7.25: Model of a server call point.

For example, let's consider the case of an asynchronous call to a remote operation where the RTE is supposed to trigger a specific RunnableEntity when the operation completes. The description of the corresponding AtomicSwComponentType would typically contain the following elements:

1. The AtomicSwComponentType contains an RPortPrototype 'myPort' typed by a PortInterface that in turn contains the definition of an ClientServerOperation 'remoteOperation'.
2. The AtomicSwComponentType's SwcInternalBehavior contains at least two RunnableEntitys: the RunnableEntity 'main' is supposed to invoke the operation; the RunnableEntity 'callback' is the one that should be called when the operation completes.
3. The description of the RunnableEntity 'main' contains an AsynchronousServerCallPoint 'invokeMyOperation' referencing the respective ClientServerOperation in the PortInterface used to type the PortPrototype 'myPort'. This implies that the RunnableEntity is allowed to invoke this operation asynchronously.
4. The description of the RunnableEntity 'callback' contains an AsynchronousServerCallResultPoint 'fetchMyOperationResults' referencing the respective AsynchronousServerCallPoint 'invokeMyOperation' This implies that the RunnableEntity is allowed to fetch the results of the asynchronously invoked operation.
5. The description of the SwcInternalBehavior includes an AsynchronousServerCallReturnsEvent 'myOperationReturns' which references the previously defined AsynchronousServerCallResultPoint 'fetchMyOperationResults'
6. The description of the AsynchronousServerCallReturnsEvent 'myOperationReturns' references the RunnableEntity 'callback', indicating that the RTE should trigger the execution of this Runnable when 'myOperationReturns' is raised.

Table 7.34: ServerCallPoint

Table 7.35: SynchronousServerCallPoint

Table 7.36: AsynchronousServerCallPoint

Table 7.37: AsynchronousServerCallResultPoint

[constr_2006] Number of AsynchronousServerCallResultPoint referencing to one AsynchronousServerCallPoint (cid:100) The AsynchronousServerCallPoint has to be referenced by exactly one AsynchronousServerCallResultPoint. This means that only the RunnableEntity with this AsynchronousServerCallResultPoint can fetch the result of the asynchronous server invocation of this particular AsynchronousServerCallPoint. (cid:99)()

This information might be used by the RTE generator to optimize the data consistency mechanisms.

Table 7.38: AsynchronousServerCallReturnsEvent

[TPS_SWCT_01347] Blocking access to operation result in an asynchronous operation invocation (cid:100) If the call of the RTE fetching the operations results shall block until the server returns the RunnableEntity with the AsynchronousServerCallResultPoint needs additional a WaitPoint referencing the AsynchronousServerCallReturnsEvent which is associated with the AsynchronousServerCallResultPoint representing the operations results access. In this case the AsynchronousServerCallReturnsEvent shall not define a startOnEvent reference to a RunnableEntity. (cid:99)(RS_SWCT_00200)

[constr_2030] WaitPoint with AsynchronousServerCallResultPoint shall belong to the same RunnableEntity (cid:100) The WaitPoint which references a AsynchronousServerCallReturnsEvent and the AsynchronousServerCallResultPoint which is referenced by this AsynchronousServerCallReturnsEvent shall be aggregated by the same RunnableEntity. (cid:99)()

#@SECTION: 7.5.2.2 Providing an Implementation of an Operation
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: OperationInvokedEvent
<!-- LLM_CONTEXT FOR CLASS OperationInvokedEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

A software-component can define an OperationInvokedEvent for each operation inside one of the server AbstractProvidedPortPrototypes. This way a RunnableEntity may respond to such an invocation through the generic event handling mechanisms described above (as formally expressed in Figure 7.26).

Figure 7.26: The OperationInvokedEvent references the operation that was called by a client.

Table 7.39: OperationInvokedEvent

#@SECTION: 7.5.2.3 Reacting on Data Transformation Errors
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: TransformerHardErrorEvent
<!-- LLM_CONTEXT FOR CLASS TransformerHardErrorEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, operation, shortName, shortNameFragment, startOnEvent, trigger, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: TriggerInterface
<!-- LLM_CONTEXT FOR CLASS TriggerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, trigger, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->

[TPS_SWCT_01624] Hard error occurs during the execution of a transformer chain (cid:100) If a hard error occurs during the execution of a transformer chain which is executed 
• on the server side of a client/server communication and re-transforms the data which trigger a server RunnableEntity or 
• on the trigger sink side of an inter-ECU external trigger communication, 
this server RunnableEntity or trigger sink RunnableEntity cannot be started because the re-transformed data are not available. (cid:99)(RS_SWCT_03222)

This might be a problem for the software-component if the software-component wants to react on transformer errors.

[TPS_SWCT_01616] Semantics of TransformerHardErrorEvent (cid:100) A software component can define a TransformerHardErrorEvent 
• for each ClientServerOperation inside one of the server PPortPrototypes (i.e. typed by a ClientServerInterface) or 
• for each Trigger in trigger sink RPortPrototypes (i.e. typed by a TriggerInterface). 
This way, a given RunnableEntity may define its response to a transformer error. (cid:99)(RS_SWCT_03222)

Table 7.40: TransformerHardErrorEvent

#@SECTION: 7.5.3 RunnableEntities and External Trigger Event Communication
#@SECTION: 7.5.3.1 Trigger Source
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ExternalTriggeringPoint
<!-- LLM_CONTEXT FOR CLASS ExternalTriggeringPoint: Attributes=[ident, trigger, variationPoint] (包含继承及相关属性) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

[TPS_SWCT_01348] Trigger source (cid:100) A RunnableEntity of the triggering software-component raises an external trigger event via an AbstractProvidedPortPrototype of the enclosing SwComponentPrototype typed by a particular AtomicSwComponentType. For this purpose the particular RunnableEntity needs an ExternalTriggeringPoint that references the particular instance of the trigger in a PPortPrototype. (cid:99)(RS_SWCT_00200)

Figure 7.27: Model structure of a trigger source.

Table 7.41: ExternalTriggeringPoint

#@SECTION: 7.5.3.2 Trigger Sink
#@CLASS: ExternalTriggerOccurredEvent
<!-- LLM_CONTEXT FOR CLASS ExternalTriggerOccurredEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, trigger, variationPoint] (包含继承及相关属性); Generalization=[RTEEvent] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

The activation of RunnableEntitys in the trigger sink is effected through the generic event handling mechanism.

[TPS_SWCT_01349] Trigger sink (cid:100) The fact that a RunnableEntity shall be activated on occurrence of an external trigger event is formally defined by means of ExternalTriggerOccurredEvent that references a particular instance of the trigger in a RPortPrototype and additionally the RunnableEntity to be executed in response to the event. (cid:99)(RS_SWCT_00200)

Figure 7.28: Model structure of a trigger sink

Table 7.42: ExternalTriggerOccurredEvent

#@SECTION: 7.5.4 RunnableEntities and Parameter Access
#@CLASS: ArgumentDataPrototype
<!-- LLM_CONTEXT FOR CLASS ArgumentDataPrototype: Attributes=[adminData, annotation, category, desc, direction, introduction, longName, serverArgumentImplPolicy, shortName, shortNameFragment, swDataDefProps, type, typeBlueprint, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ParameterAccess
<!-- LLM_CONTEXT FOR CLASS ParameterAccess: Attributes=[accessedParameter, adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: SwComponentType
<!-- LLM_CONTEXT FOR CLASS SwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[AtomicSwComponentType, CompositionSwComponentType, ParameterSwComponentType] (直接子类) -->
#@CLASS: SwDataDefProps
<!-- LLM_CONTEXT FOR CLASS SwDataDefProps: Attributes=[SwDataDefPropsVariant, additionalNativeTypeQualifier, annotation, baseType, compuMethod, dataConstr, displayFormat, implementationDataType, invalidValue, mcFunction, stepSize, swAddrMethod, swAlignment, swBitRepresentation, swCalibrationAccess, swCalprmAxisSet, swComparisonVariable, swDataDependency, swHostVariable, swImplPolicy, swIntendedResolution, swInterpolationMethod, swIsVirtual, swPointerTargetProps, swRecordLayout, swRefreshTiming, swTextProps, swValueBlockSize, unit, valueAxisDataType] (包含继承及相关属性) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

There are several ways a Calibration Parameter is provided within a software component.

[TPS_SWCT_01350] Calibration Parameters shared among several SwComponentTypes (cid:100) As mentioned above, if Calibration Parameters are shared among several SwComponentTypes a dedicated PortInterface in a PortPrototype will be used. (cid:99)(RS_SWCT_00200)

The designer of a software-component can use this access mechanism when designing a RunnableEntity using, as input value, a DataPrototype
• from an arbitrary RPortPrototype associated with a ClientServerInterface, SenderReceiverInterface or a NvDataInterface,
• VariableDataPrototype in the context of an SwcInternalBehavior

This input value will be fed to an interpolation routine whose result can be used internally or transferred to a adjacent SwComponentPrototype via dedicated PortPrototypes. Typically, there will be a dedicated RunnableEntity (with "ReceiveMode" set to "activation_of_runnable_entity") that itself calls the interpolation routine with the appropriate input value and the appropriate ParameterDataPrototype.

Note that the ParameterAccess also allows to set input values or shared axis through SwDataDefProps which are specific to the access point.

The result of this interpolation routine call is provided as an ArgumentDataPrototype with direction being either set to out or inout in a ClientServerInterface.

Figure 7.29: Runnable Access to a Calibration Port

Table 7.43: ParameterAccess

[TPS_SWCT_01351] Access to a ParameterDataPrototype (cid:100) The access to a ParameterDataPrototype will be indicated
• by the ParameterAccess entity if the RunnableEntity wants to access it from a RPortPrototype. This is shown in Figure 7.29
• by defining the ParameterAccess association from a RunnableEntity to the ParameterDataPrototype in the roles sharedParameter or perInstanceParameter. This is shown in Figure 2.3 in the lower association from RunnableEntity to ParameterDataPrototype (cid:99)(RS_SWCT_00200)

Note: A ParameterDataPrototype in the roles constantMemory is not provided by the RTE and therefore the ParameterAccess association is not required to control the RTE API generation.

#@SECTION: 7.5.4.1 InstantiationDataDefProps
#@CLASS: ApplicationCompositeDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类); Childs=[ApplicationArrayDataType, ApplicationRecordDataType] (直接子类) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: InstantiationDataDefProps
<!-- LLM_CONTEXT FOR CLASS InstantiationDataDefProps: Attributes=[parameterInstance, swDataDefProps, variableInstance, variationPoint] (包含继承及相关属性) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwDataDefProps
<!-- LLM_CONTEXT FOR CLASS SwDataDefProps: Attributes=[SwDataDefPropsVariant, additionalNativeTypeQualifier, annotation, baseType, compuMethod, dataConstr, displayFormat, implementationDataType, invalidValue, mcFunction, stepSize, swAddrMethod, swAlignment, swBitRepresentation, swCalibrationAccess, swCalprmAxisSet, swComparisonVariable, swDataDependency, swHostVariable, swImplPolicy, swIntendedResolution, swInterpolationMethod, swIsVirtual, swPointerTargetProps, swRecordLayout, swRefreshTiming, swTextProps, swValueBlockSize, unit, valueAxisDataType] (包含继承及相关属性) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

Typically, the accessibility and further information like alias names for a particular piece of data is modeled on the level of DataPrototypes (especially VariableDataPrototypes, ParameterDataPrototypes).

But due to the recursive structure of the meta-model concerning data types (an ApplicationCompositeDataType consists of DataPrototypes), a part of the relevant MCD information is described directly in the data type (in case of a ApplicationCompositeDataType).

This is a strong restriction in the reuse of data types because the ApplicationCompositeDataType should be re-used for different VariableDataPrototypes and ParameterDataPrototypes to guarantee type compatibility on C-implementation level (e.g. data of a PortPrototype is stored in a PIM or a ParameterDataPrototype used as ROM Block and shall be typed by the same data type as NVRAM Block).

This restriction is overcome by InstantiationDataDefProps as shown in figure 7.30.

Figure 7.30: applying instantiation specific data definition properties

Table 7.44: InstantiationDataDefProps

#@SECTION: 7.5.5 RunnableEntities and Mode Communication
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@CLASS: RTEEvent
<!-- LLM_CONTEXT FOR CLASS RTEEvent: Attributes=[activationReasonRepresentation, adminData, annotation, category, desc, disabledMode, introduction, longName, shortName, shortNameFragment, startOnEvent, variationPoint] (包含继承及相关属性); Generalization=[AbstractEvent, AtpStructureElement] (直接父类); Childs=[AsynchronousServerCallReturnsEvent, BackgroundEvent, DataReceiveErrorEvent, DataReceivedEvent, DataSendCompletedEvent, DataWriteCompletedEvent, ExternalTriggerOccurredEvent, InitEvent, InternalTriggerOccurredEvent, ModeSwitchedAckEvent, OperationInvokedEvent, SwcModeManagerErrorEvent, SwcModeSwitchEvent, TimingEvent, TransformerHardErrorEvent] (直接子类) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->

For the communication of modes between RunnableEntitys we have to distinguish between two use cases.

[TPS_SWCT_01352] Requested mode is just sent and received as an ordinary data value (cid:100) In the ﬁrst case, a requested mode is just sent and received as an ordinary data value without specifying the details of mode switching in the corresponding port interface. This mechanism is used if the receiving RunnableEntity is not directly implementing a mode switch but does further processing of the mode request. This is especially needed to transfer mode requests between ECUs. In this case, the mode is transferred via sender-receiver communication so that the involved RunnableEntitys just need the same type of APIs against the RTE as for sender-receiver communication.

This is possible, because ModeDeclarationGroupPrototypes can be mapped to an ImplementationDataTypes. This concept and the meta-classes needed for the mapping are further explained in chapter 4.2.5. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01353] RunnableEntitys react on a mode request via a corresponding RTEEvent (cid:100) In the second case, one RunnableEntity "sends" a mode request and one or more other RunnableEntitys react on the request via a corresponding RTEEvent or by being suppressed from being triggered any longer by other RTEEvents. In this case, special APIs against the RTE are required and the RTE has to implement the actual mode switch. This kind of communication is only possible between software components on the same ECU. For further explanation of the general concept refer to chapter 4.2.5 and for the details of the meta-model for mode switches refer to chapter 9. (cid:99)(RS_SWCT_00200, RS_SWCT_03202)

#@SECTION: 7.6 Port API Options
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@ENUM: DataTransformationErrorHandlingEnum
<!-- LLM_CONTEXT FOR ENUM DataTransformationErrorHandlingEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: PortAPIOption
<!-- LLM_CONTEXT FOR CLASS PortAPIOption: Attributes=[enableTakeAddress, errorHandling, indirectAPI, port, portArgValue, variationPoint] (包含继承及相关属性) -->
#@CLASS: PortDefinedArgumentValue
<!-- LLM_CONTEXT FOR CLASS PortDefinedArgumentValue: Attributes=[value, valueType] (包含继承及相关属性) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->

[TPS_SWCT_01354] PortAPIOption (cid:100) The RTE Generator needs additional options per PortPrototype to choose the proper generation schema. These are subsumed in the PortAPIOption element which is shown in Figure 7.31. (cid:99)()

Figure 7.31: Port API Options.

Table 7.45: PortAPIOption

[TPS_SWCT_01626] Error notification of data transformer errors (cid:100) If the attribute PortAPIOption.errorHandling is set to transformerErrorHandling then all RunnableEntitys accessing the PortPrototype referenced by port shall handle the extended transformer error notification. (cid:99)(RS_SWCT_03222)

Enumeration DataTransformationErrorHandlingEnum Package M2::AUTOSARTemplates::SWComponentTemplate::SwcInternalBehavior::PortAPI Options This enumeration defines different ways how runnables shall handle transformer errors. Description A runnable does not handle transformer errors.

Note Literal noTransformerErrorHandling transformerErrorHandling The runnable implements the handling of transformer errors.

Table 7.46: DataTransformationErrorHandlingEnum

#@SECTION: 7.6.1 Enable to Take Address
#@CLASS: PortAPIOption
<!-- LLM_CONTEXT FOR CLASS PortAPIOption: Attributes=[enableTakeAddress, errorHandling, indirectAPI, port, portArgValue, variationPoint] (包含继承及相关属性) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

[TPS_SWCT_01355] enableTakeAddress = true (cid:100) If the attribute enableTakeAddress = true the generated API related to this PortPrototype is provided in a way that the software-component is able to use the API reference for deriving a pointer to an object. (cid:99)()

The main focus of the feature is support for configuration of AUTOSAR Services which are limited to single instances.

[constr_2024] enableTakeAddress is restricted to single instantiation (cid:100) The definition of a PortAPIOption with enableTakeAddress set to true is only permitted for software-components where the attribute SwcInternalBehavior.supportsMultipleInstantiation is set to false. (cid:99)()

#@SECTION: 7.6.2 Indirect API Generation
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->

[TPS_SWCT_01356] indirectAPI option switches the generation of the RTE’s indirect API functionality (cid:100) The indirectAPI option switches the generation of the RTE’s indirect API functionality for a certain PortPrototype. The generated indirect API does allow to iterate over ports within the SW-Component. (cid:99)()

#@SECTION: 7.6.3 Port Deﬁned Argument Value
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PortAPIOption
<!-- LLM_CONTEXT FOR CLASS PortAPIOption: Attributes=[enableTakeAddress, errorHandling, indirectAPI, port, portArgValue, variationPoint] (包含继承及相关属性) -->
#@CLASS: PortDefinedArgumentValue
<!-- LLM_CONTEXT FOR CLASS PortDefinedArgumentValue: Attributes=[value, valueType] (包含继承及相关属性) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->

[TPS_SWCT_01357] Definition of implicit values that are passed by the RTE to the server’s entry point (cid:100) In addition to the formal parameters of a client/server invocation that are defined as part of the server’s PortInterface, it is possible to specify a number of implicit values that are passed by the RTE to the server’s entry point. (cid:99)()

The initial need for this feature arises in the context of basic software services - although it is not limited to those.

For a service like the NVRAM manager, every accessing port is in addition to its logical identity - as a sequence of shortNames - uniquely identified through a NVRAM specific memory block id. This block id shall be defined in the context of ECU integration and not by the client components.

Instead of exposing this mechanism on the logical ClientServerInterface level in form of a formal argument, one or more PortDefinedArgumentValues can be specified.

[TPS_SWCT_01358] Values are hidden from the client components (cid:100) Because these values are specified in the context of the provide-port only they are hidden from the client components keeping their design and code independent from the server component details. (cid:99)()

In the example of the NVRAM manager, this allows to define the block id in the context of ECU integration and not by the client components.

Figure 7.31 shows the meta-model of Port API Options and the portArgValue.

[constr_1150] Usage of valueType for PortDefinedArgumentValue (cid:100) The valueType (typically this boils down to integer values used to specify an “id”) associated with PortDefinedArgumentValue shall be of category VALUE or TYPE_REFERENCE. The latter case is only supported if the value of category of the target data type is set to VALUE. (cid:99)()

In case of a PPortPrototype of the NVRAM example this list would have just one value of type int8 or int16 holding the memory block id.

[constr_1386] PortDefinedArgumentValue shall only be defined for AbstractProvidedPortPrototype (cid:100) A PortAPIOption which aggregates at least one PortDefinedArgumentValue in the role portArgValue shall reference an AbstractProvidedPortPrototype typed by a ClientServerInterface in the role port. (cid:99)()

To be clear, this means that PortDefinedArgumentValues may not be used together with RPortPrototypes.

Table 7.47: PortDefinedArgumentValue

#@SECTION: 7.7 PerInstanceMemory
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

[TPS_SWCT_01359] Private memory per instance (cid:100) AtomicSwComponentTypes that support multiple instantiation (attribute supportsMultipleInstantiation == true) will typically need a given amount of private memory per instance. It is the responsibility of the RTE to provide a mechanisms with which each instance of an AtomicSwComponentType can access its own instance-specific memory. (cid:99)()

[TPS_SWCT_01360] Arbitrary number of per-instance memory blocks (cid:100) An AtomicSwComponentType can define an arbitrary number of per-instance memory blocks. (cid:99)()

Figure 7.32: PerInstanceMemory

[TPS_SWCT_01361] attribute supportsMultipleInstantiation == false (cid:100) AtomicSwComponentTypes that do not support multiple instantiation (attribute supportsMultipleInstantiation == false) do not necessarily need to use the PerInstanceMemory: because there will only be a single instance of the AtomicSwComponentType on an ECU, the AtomicSwComponentType can use static variables to store the AtomicSwComponentType's internal state. However, the usage of PerInstanceMemory is also allowed in this case. (cid:99)()

[TPS_SWCT_01362] Initialization of PerInstanceMemory (cid:100) Note that the PerInstanceMemory is not initialized by the RTE if no initValue is defined. In this case, it is the responsibility of the AtomicSwComponentType to initialize the PerInstanceMemory. (cid:99)()

#@SECTION: 7.7.1 PerInstanceMemory typed by “C” Data Types
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

[TPS_SWCT_01363] PerInstanceMemory typed by "C" Data Types (cid:100) For each such memory block, the software-component description shall provide the name of the data type (the "C"-type) it needs to store in the memory block in the attribute type. This attribute allows for the RTE to generate an API function that provides a convenient and type-safe access to the data item. In addition, the software-component description shall define the data type in the attribute typeDefinition. This attribute is supposed to contain a C typedef of the data type in valid C-syntax. (cid:99)()

In other words, this typeDefinition shall be formulated such that it can be included verbatim in a C header file.

[constr_2007] Consistency of typeDefinition attribute (cid:100) All PerInstanceMemorys of the same SwcInternalBehavior with identical type attribute shall define an identical typeDefinition attribute as well. (cid:99)()

[TPS_SWCT_01364] Initial value of a PerInstanceMemory typed by "C" Data Types (cid:100) The initValue is a comma separated list which can be used verbatim by the RTE generator as constant initializer. (cid:99)()

[TPS_SWCT_01574] PerInstanceMemory.typeDefinition shall not contain a function pointer (cid:100) The attribute PerInstanceMemory.typeDefinition is not allowed to contain a function pointer. (cid:99)()

Please note that, although [TPS_SWCT_01574] is formulated like a constraint and the statement that it makes certainly has a constraint-ish nature, there is hardly a way to actually enforce the regulation because the content of PerInstanceMemory.typeDefinition is non-formal (modeled by the non-specific i.e. String). Therefore, a specification item has been used for the description of the respective semantics rather than a constraint.

More details on the use of these attributes in the generation of software-component header-files can be found in the RTE specification [2].

Table 7.48: PerInstanceMemory

#@SECTION: 7.7.2 PerInstanceMemory typed by AUTOSAR Data Types
#@CLASS: AutosarDataType
<!-- LLM_CONTEXT FOR CLASS AutosarDataType: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpType] (直接父类); Childs=[ApplicationDataType, ImplementationDataType] (直接子类) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ValueSpecification
<!-- LLM_CONTEXT FOR CLASS ValueSpecification: Attributes=[shortLabel, variationPoint] (包含继承及相关属性); Childs=[AbstractRuleBasedValueSpecification, ApplicationValueSpecification, ArrayValueSpecification, ConstantReference, NumericalValueSpecification, RecordValueSpecification, ReferenceValueSpecification, TextValueSpecification] (直接子类) -->
#@CLASS: SwDataDefProps
<!-- LLM_CONTEXT FOR CLASS SwDataDefProps: Attributes=[SwDataDefPropsVariant, additionalNativeTypeQualifier, annotation, baseType, compuMethod, dataConstr, displayFormat, implementationDataType, invalidValue, mcFunction, stepSize, swAddrMethod, swAlignment, swBitRepresentation, swCalibrationAccess, swCalprmAxisSet, swComparisonVariable, swDataDependency, swHostVariable, swImplPolicy, swIntendedResolution, swInterpolationMethod, swIsVirtual, swPointerTargetProps, swRecordLayout, swRefreshTiming, swTextProps, swValueBlockSize, unit, valueAxisDataType] (包含继承及相关属性) -->

[TPS_SWCT_01365] PerInstanceMemory typed by AUTOSAR Data Types (cid:100) A PerInstanceMemory typed with AUTOSAR data types is defined by a VariableDataPrototype in the role arTypedPerInstanceMemory. VariableDataPrototype is derived from DataPrototype which has an association to an AutosarDataType. (cid:99)() 
This defines the data type of the AUTOSAR-typed PerInstanceMemory.

[TPS_SWCT_01366] Initial value of a PerInstanceMemory typed by AUTOSAR Data Types (cid:100) The initValue is described with a ValueSpecification (cid:99)()

typed by C data type (cid:100)
[TPS_SWCT_01367] Typed by AUTOSAR data type vs. In difference to the "C" typed PerInstanceMemory the AUTOSAR-typed PerInstanceMemory is able to define information controlling the visibility in a MCD system via a SwDataDefProps for the purpose of measurement (see chapter 5.4.3) or defining an input value of an axis (see chapter 5.4.5). (cid:99)()

Note: Due to the use of AutosarDataType the AUTOSAR-typed PerInstanceMemory can not support C++ specific types or pointer types directly.

#@SECTION: 7.8 Static Memory and Constant Memory
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: InternalBehavior
<!-- LLM_CONTEXT FOR CLASS InternalBehavior: Attributes=[adminData, annotation, category, constantMemory, constantValueMapping, dataTypeMapping, desc, exclusiveArea, exclusiveAreaNestingOrder, introduction, longName, shortName, shortNameFragment, staticMemory] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[BswInternalBehavior, SwcInternalBehavior] (直接子类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->

[TPS_SWCT_01368] Describe static and constant memory (cid:100) Static memory (formalized by means of InternalBehavior.staticMemory) and constant memory (formalized by means of InternalBehavior.constantMemory) can be used whenever AutosarDataTypes should be used in the implementation of an AtomicSwComponentType but no involvement of the RTE (for memory allocation and management) is required. (cid:99)()

This includes special cases of measurement and calibration but also debugging.

[TPS_SWCT_01483] Use static and constant memory to support Measurement and Calibration (cid:100) The information about these characteristic values and variables is given with the purpose to support Measurement and Calibration (see chapter 2.2) and has to be taken into account for the generation of A2L files. A proprietary generator shall take care of these data for the purpose of generating A2L. (cid:99)()

Figure 7.33: Static Memory and Constant Memory

[TPS_SWCT_01369] Static and constant memory is not instantiated by the RTE (cid:100) In contrast to the other kinds of memory like implicitInterRunnableVariable, implicitInterRunnableVariable, PerInstanceMemory, sharedParameter or perInstanceParameter the staticMemory and constantMemory are not instantiated by the RTE. (cid:99)()

This allows for more efficient implementations (especially for software-components provided as object code) by avoidance of the additional indirection caused by the RTE’s component data structure.

Further on, this kind of memory reduces the dependencies of the software-component implementation to generated RTE code which is appreciated for safety related functionalities.

Due to the instantiation of the memory by the software-component’s implementation the constantMemory behaves like a sharedParameter (see chapter 2.2.3.2)

[constr_2028] staticMemory is restricted to single instantiation (cid:100) The staticMemory is only supported if the attribute supportsMultipleInstantiation of the owning SwcInternalBehavior is set to false (cid:99)()

This constraint prevents hidden communication between SwComponentPrototypes of the same SwComponentType.

[constr_2029] shortName of constantMemory and staticMemory (cid:100) The shortName of a VariableDataPrototype in role staticMemory or a ParameterDataPrototype in role constantMemory has to be equal with the 'C' identifier of the described variable resp. constant. (cid:99)()

#@SECTION: 7.9 Included AUTOSAR Data Types
#@CLASS: AutosarDataType
<!-- LLM_CONTEXT FOR CLASS AutosarDataType: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpType] (直接父类); Childs=[ApplicationDataType, ImplementationDataType] (直接子类) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: IncludedDataTypeSet
<!-- LLM_CONTEXT FOR CLASS IncludedDataTypeSet: Attributes=[dataType, literalPrefix] (包含继承及相关属性) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

[TPS_SWCT_01155] IncludedDataTypeSet (cid:100) An IncludedDataTypeSet declares that a set of AutosarDataTypes are used for the C / C++ implementation of the software component. The AutosarDataTypes become part of the contract. (cid:99)()

[TPS_SWCT_01156] Required if the AutosarDataType is not used for any DataPrototype (cid:100) This information is required if the AutosarDataType is not used for any DataPrototype owned by this software component or if a prefix for C language identifiers belonging to AutosarDataTypes shall be defined. (cid:99)()

Figure 7.34: Included AUTOSAR Data Types

Table 7.49: IncludedDataTypeSet

This supports the common usage of the AUTOSAR data type system for RTE provided memory objects and memory objects declared by the software component implementation.

Further on, this enables the generation of the RTE Application Types Header File for AUTOSAR services containing the required data types for the C-API before the data type usage in dedicated ports for an ECU is known.

[TPS_SWCT_01157] Attribute literalPrefix of IncludedDataTypeSet (cid:100) In addition the literalPrefix might be used to separate the namespace of C language identifiers belonging to equally named AutosarDataTypes used for the same software component C implementation. (cid:99)()

#@SECTION: 7.10 Included Mode Declaration Groups
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: IncludedModeDeclarationGroupSet
<!-- LLM_CONTEXT FOR CLASS IncludedModeDeclarationGroupSet: Attributes=[modeDeclarationGroup, prefix] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

[TPS_SWCT_01153] IncludedModeDeclarationGroupSet (cid:100) Similar to the consideration of data types using IncludedDataTypeSet, SwcInternalBehavior aggregates IncludedModeDeclarationGroupSet that in turn allows for referencing ModeDeclarationGroups with the intent to express that the referenced ModeDeclarationGroups are used in the context of the enclosing AtomicSwComponentType. (cid:99)()

Figure 7.35: Included ModeDeclarationGroups

Table 7.50: IncludedModeDeclarationGroupSet

[TPS_SWCT_01154] Attribute prefix of IncludedModeDeclarationGroupSet (cid:100) The optional attribute prefix of IncludedModeDeclarationGroupSet can be used to define a prefix that the RTE generator shall use to define symbols related to the included ModeDeclarationGroups with the intent to avoid potential name clashes. (cid:99)()

Rationale: If the attribute prefix is required, changes to software-component source code may be necessary.

#@SECTION: 7.11 Service Needs
#@SECTION: 7.11.1 Overview
#@CLASS: ApplicationSwComponentType
<!-- LLM_CONTEXT FOR CLASS ApplicationSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: NvBlockSwComponentType
<!-- LLM_CONTEXT FOR CLASS NvBlockSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, nvBlockDescriptor, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

[TPS_SWCT_01043] ApplicationSwComponentTypes are independent from actual ECU Hardware (cid:100) ApplicationSwComponentTypes are designed to be independent of their mapping to actual ECU Hardware. (cid:99)(RS_SWCT_02060)

However, each software-component might need services which are provided by the ECU Basic Software through AUTOSAR Services. 

[TPS_SWCT_01044] ServiceNeeds (cid:100) The ServiceNeeds (see Figures 7.36, 7.37, 7.38, and 7.39) are used to provide detailed information what the software-component expects from the AUTOSAR Services when integrated on an actual ECU.  
Note that only AtomicSwComponentTypes and NvBlockSwComponentTypes can be connected to AUTOSAR Services. (cid:99)(RS_SWCT_02060)

[TPS_SWCT_01045] Actual values of ECU configuration parameters fulfill the requirements given by the ServiceNeeds (cid:100) When integrating application software components on an ECU, the actual values of ECU configuration parameters shall be chosen so that they fulfill the requirements given by the ServiceNeeds of all the integrated AtomicSwComponentTypes. (cid:99)(RS_SWCT_02060)

Note that the actual values of configuration parameters will in addition depend on the properties of the basic software and the hardware of that specific ECU, see also chapter 11. For further information about the relation between the ServiceNeeds and the ECU configuration parameters see [29].

Table 7.51: ServiceNeeds

The meta-class ServiceNeeds and the sub-classes for several Services are located in the CommonStructure package of the meta-model because they are also used in the Basic Software Module Description Template [7]. The meta-classes derived from ServiceNeeds is shown in the next three figures.

Figure 7.36: ServiceNeeds: General ServiceNeeds

Figure 7.37: General diagnostic service-related ServiceNeeds

Figure 7.38: General diagnostic event-handling related ServiceNeeds

Figure 7.39: ServiceNeeds: Diagnostic-related ServiceNeeds with emphasis on OBD

#@SECTION: 7.11.2 Assignment of Service Needs to Ports and Data
#@CLASS: ARPackage
<!-- LLM_CONTEXT FOR CLASS ARPackage: Attributes=[adminData, annotation, arPackage, blueprintPolicy, category, desc, element, introduction, longName, referenceBase, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, CollectableElement, Identifiable] (直接父类) -->
#@CLASS: SymbolicNameProps
<!-- LLM_CONTEXT FOR CLASS SymbolicNameProps: Attributes=[shortName, shortNameFragment, symbol] (包含继承及相关属性); Generalization=[ImplementationProps] (直接父类) -->
#@CLASS: ApplicationSwComponentType
<!-- LLM_CONTEXT FOR CLASS ApplicationSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: AutosarDataPrototype
<!-- LLM_CONTEXT FOR CLASS AutosarDataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[DataPrototype] (直接父类); Childs=[ArgumentDataPrototype, ParameterDataPrototype, VariableDataPrototype] (直接子类) -->
#@CLASS: AutosarParameterRef
<!-- LLM_CONTEXT FOR CLASS AutosarParameterRef: Attributes=[autosarParameter, localParameter] (包含继承及相关属性) -->
#@CLASS: AutosarVariableRef
<!-- LLM_CONTEXT FOR CLASS AutosarVariableRef: Attributes=[autosarVariable, autosarVariableInImplDatatype, localVariable] (包含继承及相关属性) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: NvBlockSwComponentType
<!-- LLM_CONTEXT FOR CLASS NvBlockSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, nvBlockDescriptor, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PortGroup
<!-- LLM_CONTEXT FOR CLASS PortGroup: Attributes=[adminData, annotation, category, desc, innerGroup, introduction, longName, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RoleBasedDataAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataAssignment: Attributes=[role, usedDataElement, usedParameterElement, usedPim, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedDataTypeAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataTypeAssignment: Attributes=[role, usedImplementationDataType, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ServiceDependency
<!-- LLM_CONTEXT FOR CLASS ServiceDependency: Attributes=[assignedDataType, symbolicNameProps] (包含继承及相关属性); Childs=[BswServiceDependency, SwcServiceDependency] (直接子类) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

[TPS_SWCT_01046] ServiceNeeds are defined in the scope of the SwcInternalBehavior (cid:100) ServiceNeeds specified by AtomicSwComponentTypes are defined in the scope of the SwcInternalBehavior because in several cases they need associations to other parts of the SwcInternalBehavior.

In most cases they are related to certain PortPrototypes belonging to the AtomicSwComponentTypes because AtomicSwComponentTypes communicate with AUTOSAR Services via these PortPrototypes. (cid:99)(RS_SWCT_02060)

In addition, a ServiceNeeds element can also have relations to some data declared within the same SwcInternalBehavior, namely some use cases of the NVRAM Service require a Permanent RAM Block and/or ROM Block declared in the context of the single software component.

A further use case requires that a ServiceNeeds element is linked to a PortGroup. Especially, a ServiceNeeds can represent a group of PortPrototypes as input to configure the communication manager in order to handle the communication state of those PortPrototypes.

These relationships to PortPrototypes, data and PortGroups are required as input for tools in order to generate the XML descriptions and configurations of the basic software which implements the Service according to the needs of several Atomic SwComponentTypes are integrated on an ECU, see chapter 11.

The relationship to PortPrototypes is defined via the meta-class RoleBasedPortAssignment and the relationship to data is defined via the meta-class RoleBasedDataAssignment.

Both are aggregating an attribute role which allows to defined the role of the PortPrototypes or data in the specific context.

[constr_2027] SwcServiceDependency shall be defined for service ports only (cid:100) A PortPrototype that is referenced by a SwcServiceDependency via assignedPort shall be typed by a PortInterface that has isService set to true.

This rule does not apply to PortPrototypes used in the context of NV data management, i.e. for connections between an ApplicationSwComponentType and an NvBlockSwComponentType. (cid:99)()

Please consider: it is permitted that a SwcServiceDependency containing a DiagnosticValueNeeds may reference via assignedData a dataElement instance in a PPortPrototype typed by a SenderReceiverInterface that has its attribute isService set to false.

The actual mapping between the ServiceNeeds element and its various relationships is provided by the meta-class SwcServiceDependency as shown in figure 7.41.

Note the difference between the associations to PortPrototypes and to PortGroups: While the RoleBasedPortAssignment is part of the SwcInternalBehavior a PortGroup is defined for the SwComponentType (thus belongs to the VFB level) and it is linked to the PortGroups of other SwComponentTypes.

Figure 7.40: ServiceDependency is the abstract base class of SwcServiceDependency

This means a PortGroup represents a system feature, whereas the RoleBasedPortAssignment is a local feature for the purpose of communication with the AUTOSAR Service.

[TPS_SWCT_01556] Rule for setting RoleBasedPortAssignment.role (cid:100) The value of RoleBasedPortAssignment.role cannot arbitrarily set but shall to equal to the shortName of the applicable PortInterface taken from the standardized AUTOSAR Service Interface model (this implies that the ARPackage that owns the PortInterface is set to BLUEPRINT(see [TPS_STDT_00033]) and the top-most ARPackage.shortName is set to AUTOSAR, see also [30]). (cid:99)()

Figure 7.41: SwcServiceDependency in the SwcInternalBehavior

Figure 7.42: Details of RoleBasedDataAssignment for local data

Figure 7.43: Details of RoleBasedDataAssignment for accessing DataPrototypes in PortPrototypes

Figure 7.44: Details of RoleBasedDataTypeAssignment for local data

Table 7.52: ServiceDependency

Table 7.53: SwcServiceDependency
Table 7.54: SymbolicNameProps
Table 7.55: RoleBasedPortAssignment

Table 7.56: RoleBasedDataAssignment

Table 7.57: RoleBasedDataTypeAssignment

#@SECTION: 7.11.3 Speciﬁc Service Dependencies
#@SECTION: 7.11.3.1 NvM Service Dependencies
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: NvBlockNeeds
<!-- LLM_CONTEXT FOR CLASS NvBlockNeeds: Attributes=[adminData, annotation, bswMgrNeeds, calcRamBlockCrc, category, checkStaticBlockId, comMgrUserNeeds, cryptoServiceNeeds, cyclicWritingPeriod, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nDataSets, nRomBlocks, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, ramBlockStatusControl, readonly, reliability, resistantToChangedSw, restoreAtStart, shortName, shortNameFragment, storeAtShutdown, storeCyclic, storeEmergency, storeImmediate, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, useAutoValidationAtShutDown, useCRCCompMechanism, warningIndicatorRequestedBitNeeds, writeOnlyOnce, writeVerification, writingFrequency, writingPriority] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: NvBlockSwComponentType
<!-- LLM_CONTEXT FOR CLASS NvBlockSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, nvBlockDescriptor, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

This chapter describes the usage of the specific meta-classes derived from Service Needs within an AtomicSwComponentType.

The meta-class NvBlockNeeds is used to define requirements to configure the NVRAM Manager Service. In addition, it may define requirements how the RTE shall implement writing strategies of an NvBlockSwComponentType.

An SwcInternalBehavior may provide several SwcServiceDependencys that in turn aggregate an NvBlockNeeds element where each defines the requirements from one NVRAM Block (for more information on the AUTOSAR NVRAM Manager see [31]).

There are several use cases how a software-component can interact with the NVRAM Manager service. Each use case is discussed in a separate sub-chapter.

Table 7.58: NvBlockNeeds

Table 7.59: RamBlockStatusControlEnum

#@SECTION: 7.11.3.1.1 Nvm Use Case: Permanent RAM Block
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: NvBlockSwComponentType
<!-- LLM_CONTEXT FOR CLASS NvBlockSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, nvBlockDescriptor, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: RoleBasedDataAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataAssignment: Attributes=[role, usedDataElement, usedParameterElement, usedPim, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

Scenario: a AtomicSwComponentType is using an an NVRAM Block with a Permanent RAM Block implemented by a PerInstanceMemory section or a VariableDataPrototype in the role arTypedPerInstanceMemory. In either case, the required memory for the Permanent RAM Block is allocated by the RTE during ECU Configuration.

In this case the following rules apply:

[TPS_SWCT_02501] Setup for Nvm Use Case: Permanent RAM Block (cid:100)

1. RoleBasedPortAssignment
    For every used ClientServerInterface provided by the NvM it is necessary to create a    RoleBasedPortAssignment and set the value of the attribute role of the     RoleBasedPortAssignment to the name of the used standardized ClientServerInterface. The  following ClientServerInterfaces shall (i.e. lower multiplicity > 0) or can (lower  multiplicity = 0) be used in this context:
        • NvmService [0 .. 1]
        • NvMNotifyJobFinished [0 .. 1]
        • NvMNotifyInitBlock [0 .. 1]
        • NvMAdmin [0 .. 1]

2. RoleBasedDataAssignment
    RoleBasedDataAssignment shall be created that refers to either the PerInstanceMemory in the role usedPim or to the VariableDataPrototype in the role usedDataElement. The value of the attribute role of the RoleBasedDataAssignment shall be set to ramBlock.

    Optionally, it is possible to create an additional RoleBasedDataAssignment to a ParameterDataPrototype in the role usedParameterElement. The value of the ParameterDataPrototype is then taken as the initial or default value for the NVRAM Block. In this case the value of the attribute role of the RoleBasedDataAssignment shall be set to defaultValue. Therefore, the following roles are applicable:
        • ramBlock [1]
        • defaultValue [0 .. 1]

3. RepresentedPortGroup 
    N/A
(cid:99)()

For more information please refer to [SWS_NvM_00734], [SWS_NvM_00735], [SWS_NvM_00736], and [SWS_NvM_00737].

The same mechanism (see description of scenario) applies also for an NvBlockSwComponentType. For each NVRAM Block the NVRAM Manager can be configured (with the help of SwcServiceDependency.assignedData) to use the same Permanent RAM Block.

It is the responsibility of the NVRAM Manager to provide the content of the NVRAM Block in this Permanent RAM Block during startup or on explicit request and to write back the content to the storage medium during shut-down or on explicit request.

#@SECTION: 7.11.3.1.2 Nvm Use Case: Temporary RAM Block
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: RoleBasedDataAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataAssignment: Attributes=[role, usedDataElement, usedParameterElement, usedPim, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedDataTypeAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataTypeAssignment: Attributes=[role, usedImplementationDataType, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

Scenario: an AtomicSwComponentType is using some NVRAM Block with a Temporary RAM Block. In this case the AtomicSwComponentType is responsible for allocating the allocation of sufficient memory. In other words, the AtomicSwComponentType shall provide a memory area that is available to the API call to the NVRAM Manager for storage of the NV data.

[TPS_SWCT_02502] Setup for Nvm Use Case: Temporary RAM Block (cid:100)
1. RoleBasedPortAssignment 
    This is mandatory for the described scenario. For every used ClientServerInterface provided by the Nvm it is necessary to create a RoleBasedPortAssignment and set the value of the attribute role of the RoleBasedPortAssignment to the name of the used ClientServerInterface. The following ClientServerInterfaces shall (i.e. lower multiplicity > 0) or can (lower multiplicity = 0) be used in this context:
        • NvmService [1]
        • NvMNotifyJobFinished [0 .. 1]
        • NvMNotifyInitBlock [0 .. 1]
        • NvMAdmin [0 .. 1]     

2. RoleBasedDataAssignment 
    The usage of a RoleBasedDataAssignment with attribute role set to defaultValue is optional and depends on whether or not an initial value is required.
        • defaultValue [0..1]

3. RoleBasedDataTypeAssignment 
    By this means it is possible to define the data type of a Temporary RAM Block. The data type information can be used to calculate the NVRAM Block size. [constr_1301] applies.
        • temporaryRamBlock [0..1]

4. RepresentedPortGroup 
    n/a
(cid:99)()

[constr_1301] Existence of RoleBasedDataTypeAssignment.role vs. RoleBasedDataAssignment.role (cid:100) The usage of a RoleBasedDataTypeAssignment with attribute role set to the value temporaryRamBlock is only allowed if no RoleBasedDataAssignment defined with attribute role set to value defaultValue exists in the owning SwcServiceDependency. (cid:99)()

The rationale for [constr_1301] is that the existence of a RoleBasedDataAssignment would already provide sufficient information for the intended purpose. The parallel existence of a RoleBasedDataTypeAssignment is therefore fully redundant and could only lead to potential inconsistencies.

For more information please refer to [SWS_NvM_00734], [SWS_NvM_00735], [SWS_NvM_00736], and [SWS_NvM_00737].

#@SECTION: 7.11.3.1.3 Nvm Use Case: RAM Block with explicit synchronization using Mirror Interfaces
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: NvBlockDescriptor
<!-- LLM_CONTEXT FOR CLASS NvBlockDescriptor: Attributes=[adminData, annotation, category, clientServerPort, constantValueMapping, dataTypeMapping, desc, instantiationDataDefProps, introduction, longName, nvBlockDataMapping, nvBlockNeeds, ramBlock, romBlock, shortName, shortNameFragment, supportDirtyFlag, timingEvent, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: NvBlockSwComponentType
<!-- LLM_CONTEXT FOR CLASS NvBlockSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, nvBlockDescriptor, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: NvDataPortAnnotation
<!-- LLM_CONTEXT FOR CLASS NvDataPortAnnotation: Attributes=[annotationOrigin, annotationText, label, variable] (包含继承及相关属性); Generalization=[GeneralAnnotation] (直接父类) -->
#@CLASS: NvMAdmin
<!-- LLM_CONTEXT FOR CLASS NvMAdmin: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: NvMMirror
<!-- LLM_CONTEXT FOR CLASS NvMMirror: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: NvMNotifyInitBlock
<!-- LLM_CONTEXT FOR CLASS NvMNotifyInitBlock: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: NvMNotifyJobFinished
<!-- LLM_CONTEXT FOR CLASS NvMNotifyJobFinished: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: NvMService
<!-- LLM_CONTEXT FOR CLASS NvMService: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PerInstanceMemory
<!-- LLM_CONTEXT FOR CLASS PerInstanceMemory: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, typeDefinition, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: RoleBasedDataAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataAssignment: Attributes=[role, usedDataElement, usedParameterElement, usedPim, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedDataTypeAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataTypeAssignment: Attributes=[role, usedImplementationDataType, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

Scenario: an AtomicSwComponentType is using an NVRAM Block where the RAM Block uses explicit synchronization by means of mirror interfaces. In this case the RAM Block does not necessarily have to be formally described by means of a PerInstanceMemory or a VariableDataPrototype in the role arTypedPerInstanceMemory.

Consequently, the software-component itself is responsible for the allocation of memory. On the other hand, this can also mean that the software-component can use several RAM Blocks instead of just one RAM Block.

[TPS_SWCT_02504] Setup for Nvm Use Case: RAM Block with explicit synchronization using Mirror Interfaces (cid:100)

1. RoleBasedPortAssignment
    This is mandatory for the described scenario. For every used ClientServerInterface provided by the Nvm it is necessary to create a RoleBasedPortAssignment and set the value of the attribute role of the RoleBasedPortAssignment to the name of the used ClientServerInterface. The following ClientServerInterfaces shall (i.e. lower multiplicity > 0) or can (lower multiplicity = 0) be used in this context:
        • NvMService [0..1]
        • NvMNotifyJobFinished [0..1]
        • NvMNotifyInitBlock [0..1]
        • NvMAdmin [0..1]
        • NvMMirror [1]

2. RoleBasedDataAssignment

    In this scenario the existence of a RoleBasedDataAssignment is optional. The RoleBasedDataAssignment needs to reference a ParameterDataPrototype aggregated by the enclosing SwcInternalBehavior in the role perInstanceParameter or sharedParameter.

        • defaultValue [0..1]

3. RoleBasedDataTypeAssignment

    By this means it is possible to define the data type of a temporary RAM Block and used internal data structure in case of explicit synchronization with NvMMirror interface respectively. The data type information can be used to calculate the NVRAM Block size and minimum Permanent RAM Block size. [constr_1301] applies.

        • temporaryRamBlock [0..1]

4. RepresentedPortGroup 
    N/A
(cid:99)()

For more information please refer to [SWS_NvM_00734], [SWS_NvM_00735], [SWS_NvM_00736], [SWS_NvM_00737], and [SWS_NvM_00738].

#@SECTION: 7.11.3.1.4 NVM Use Case: Software-Components using Nv Data provided by NvBlockSwComponentType (not ServiceSwComponent of NvM)

#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: NvBlockSwComponentType
<!-- LLM_CONTEXT FOR CLASS NvBlockSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, nvBlockDescriptor, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: ServiceSwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

Scenario: an AtomicSwComponentType is using an NVRAM Block managed by an NvBlockSwComponentType (see section 11.5.2, as opposed to an NVRAM Block provided by a ServiceSwComponentType). Constraints [constr_1148], [constr_1149], and [constr_2011] apply.

[TPS_SWCT_02503] Setup for NVM Use Case: Software-Components using NvData provided by NvBlockSwComponentType (cid:100)

1. RoleBasedPortAssignment

    This is mandatory for the described scenario. For every used ClientServerInterface provided by the NvM it is necessary to create a RoleBasedPortAssignment and set the value of the attribute role of the RoleBasedPortAssignment to the name of the used ClientServerInterface. The following ClientServerInterfaces shall (i.e. lower multiplicity > 0) or can (lower multiplicity = 0) be used in this context:

        • NvMService [0..1]
        • NvMNotifyJobFinished [0..1]
        • NvMNotifyInitBlock [0..1]
        • NvMAdmin [0..1]

    For every PortPrototype of a software-component typed by an NvDataInterface defining a SwcServiceDependency it is necessary to create a RoleBasedPortAssignment and set the value of the attribute role of the attribute assignedPort to the value NvDataPort:

        • NvDataPort [1..*]

2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroup
    N/A
(cid:99)

For more information please refer to [SWS_NvM_00734], [SWS_NvM_00735], [SWS_NvM_00736], and [SWS_NvM_00737]. Note that NvBlockNeeds described in Chapter 11.5.4 is not in the scope of this use case.

#@SECTION: 7.11.3.2 Watchdog Service Dependencies
#@CLASS: SupervisedEntityNeeds
<!-- LLM_CONTEXT FOR CLASS SupervisedEntityNeeds: Attributes=[activateAtStart, adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, enableDeactivation, expectedAliveCycle, functionInhibitionNeeds, introduction, longName, maxAliveCycle, minAliveCycle, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, toleratedFailedCycles, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->

The meta-class SupervisedEntityNeeds is used to define requirements to configure the Watchdog Service. For the terms related to the AUTOSAR Watchdog Manager see [32].

#@SECTION: 7.11.3.2.1 Watchdog Service use Case: Supervision
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SupervisedEntityNeeds
<!-- LLM_CONTEXT FOR CLASS SupervisedEntityNeeds: Attributes=[activateAtStart, adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, enableDeactivation, expectedAliveCycle, functionInhibitionNeeds, introduction, longName, maxAliveCycle, minAliveCycle, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, toleratedFailedCycles, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->

Table 7.60: SupervisedEntityNeeds

Scenario: an AtomicSwComponentType contains a Supervised Entity. In this case it is required that the Supervised Entity indicates to the Watchdog Manager that a Check point within the Supervised Entity has been reached. Further on the Local Supervision Status of a single Supervised Entity may be signaled to the software component. In this case the following setup applies:

[TPS_SWCT_02018] Setup for AtomicSwComponentType which contains a Supervised Entity (cid:100) 
1. RoleBasedPortAssignment valid roles:
    • WdgM_AliveSupervision [1]
    • WdgM_IndividualMode [0..1] 
2. RoleBasedDataAssignment 
    N/A
3. RepresentedPortGroups 
    N/A
(cid:99)()

For more information please refer to [SWS_WdgM_00333], and [SWS_WdgM_00335].

Please note that an SwcInternalBehavior may provide several SupervisedEntityNeeds elements where each defines the requirements in relation to one supervised entity.

#@SECTION: 7.11.3.2.2 Watchdog Service use Case: Global Supervision Status notiﬁcation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: an AtomicSwComponentType requires to receive the Global Supervision Status that is combined from all individual Supervised Entities. In this case the following setup applies:

[TPS_SWCT_02019] Setup for AtomicSwComponentType which requires Global Supervision Status notification (cid:100)

1. RoleBasedPortAssignment valid roles:
    • WdgM_GlobalMode [1]

2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_WdgM_00336].

#@SECTION: 7.11.3.3 COM Manager Service Needs
#@CLASS: ComMgrUserNeeds
<!-- LLM_CONTEXT FOR CLASS ComMgrUserNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, maxCommMode, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: PortGroup
<!-- LLM_CONTEXT FOR CLASS PortGroup: Attributes=[adminData, annotation, category, desc, innerGroup, introduction, longName, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->

The meta-class ComMgrUserNeeds is used to define requirements to configure the ComM Service. An SwcInternalBehavior may provide several ComMgrUserNeeds elements where each defines the requirements from one "user" of the ComM Service. Especially, it defines which PortGroup is associated with this "user".

Table 7.61: ComMgrUserNeeds

#@SECTION: 7.11.3.3.1 ComM Use Case: read current ComM Mode
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType reads the current ComM mode.

In this case the following rules apply:

[TPS_SWCT_01019] AtomicSwComponentType reads the current ComM mode (cid:100)

1. RoleBasedPortAssignment valid roles:
    • ComM_CurrentMode [1]

2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroup
    N/A
(cid:99)()

For more information please refer to [SWS_ComM_00847].

#@SECTION: 7.11.3.3.2 ComM Use Case: request ComM Mode
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortGroup
<!-- LLM_CONTEXT FOR CLASS PortGroup: Attributes=[adminData, annotation, category, desc, innerGroup, introduction, longName, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->

Scenario: a AtomicSwComponentType requests a ComM mode. It may also check later whether the requested ComM mode has become effective.

In this case the following rules apply:

[TPS_SWCT_01020] AtomicSwComponentType requests a ComM mode. It may also check later whether the requested ComM mode has become effective (cid:100)

1. RoleBasedPortAssignment valid roles:
    • ComM_CurrentMode [1]
    • ComM_UserRequest [1]

2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroup
    Reference to the applicable PortGroup [0..1]
(cid:99)()

For more information please refer to [SWS_ComM_00848].

#@SECTION: 7.11.3.3.3 ComM Use Case: Software-Component acts as a Mode Manager that inﬂuences the ECU State
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType acts as a mode manager that inﬂuences the ECU state.

In this case the following rules apply:

[TPS_SWCT_01021] AtomicSwComponentType acts as a mode manager that inﬂuences the ECU state (cid:100)
1. RoleBasedPortAssignment valid roles:
    • ComM_CurrentMode [0..1]
    • ComM_UserRequest [0..1]
    • ComM_ECUModeLimitation [1]
2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroup
    N/A
(cid:99)()

For more information please refer to [SWS_ComM_00741].

#@SECTION: 7.11.3.4 ECU State Manager Service Needs
#@CLASS: EcuStateMgrUserNeeds
<!-- LLM_CONTEXT FOR CLASS EcuStateMgrUserNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

The meta-class EcuStateMgrUserNeeds is used to define the requirements to configure the ECU State Manager Service. There are actually two variants of AUTOSAR ECU management: flexible and fixed. An SwcInternalBehavior may provide several EcuStateMgrUserNeeds elements where each defines the requirements from one "user" of the EcuM Service (for the terms related to the AUTOSAR ECU State Manager see [33]).

Table 7.62: EcuStateMgrUserNeeds

#@SECTION: 7.11.3.4.1 EcuM Fixed Use Case: read current ECU Mode
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType reads the current ECU mode.

In this case the following rules apply:

[TPS_SWCT_01012] AtomicSwComponentType reads the current ECU mode (fixed variant) (cid:100)

1. RoleBasedPortAssignment valid roles:
    • EcuM_CurrentMode [1]
2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroup
    N/A
(cid:99)()

For more information please refer to [SWS_EcuM_02762] and [SWS_EcuM_02749].

#@SECTION: 7.11.3.4.2 EcuM Fixed Use Case: request a certain ECU state
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

Scenario: a AtomicSwComponentType needs to keep the ECU alive or needs to execute operations before the ECU is shut down. For this purpose the AtomicSwComponentType may request either the state RUN or POST_RUN.

In this case the following rules apply:

[TPS_SWCT_01013] AtomicSwComponentType shall keep the ECU alive (fixed variant) (cid:100)

AtomicSwComponentType needs to keep the ECU alive or needs to execute operations before the ECU is shut down.

1. RoleBasedPortAssignment valid roles:
    • EcuM_StateRequest [1]

2. RoleBasedDataAssignment
    N/A
3. RepresentedPortGroup
    N/A
(cid:99)()

For more information please refer to [SWS_EcuM_02762].

#@SECTION: 7.11.3.4.3 EcuM Fixed Use Case: select Shutdown Target
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

Scenario: a AtomicSwComponentType wants to select a shutdown target. This corresponds to the "select shutdown target" use case of the flex EcuM.

In this case the following rules apply:

[TPS_SWCT_01014] AtomicSwComponentType wants to select a shutdown target (fixed variant) (cid:100)

RoleBasedPortAssignment valid roles:
    • EcuM_ShutdownTarget [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroup
    N/A
(cid:99)()

#@SECTION: 7.11.3.4.4 EcuM Fixed Use Case: select Boot Target
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType wants to select a boot target.

In this case the following rules apply:

[TPS_SWCT_01015] AtomicSwComponentType wants to select a boot target (fixed variant) (cid:100)

RoleBasedPortAssignment valid roles:
    • EcuM_BootTarget [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroup
    N/A
(cid:99)()

#@SECTION: 7.11.3.4.5 EcuM Flex Use Case: select Shutdown Target
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType wants to select a shutdown target. This corresponds to the “select shutdown target” use case of the ﬁx EcuM.

In this case the following rules apply:

[TPS_SWCT_01016] AtomicSwComponentType wants to select a shutdown target (ﬂexible variant) (cid:100)

RoleBasedPortAssignment valid roles:
    • EcuM_ShutdownTarget [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroup
    N/A
(cid:99)()

#@SECTION: 7.11.3.4.6 EcuM Flex Use Case: select Boot Target
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

Scenario: a AtomicSwComponentType wants to select a boot target.

In this case the following rules apply:

[TPS_SWCT_01017] AtomicSwComponentType wants to select a boot target (flexible variant) (cid:100)

RoleBasedPortAssignment valid roles:
    • EcuM_BootTarget [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroup
    N/A
(cid:99)()

#@SECTION: 7.11.3.4.7 EcuM Flex Use Case: use Alarm Clock
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType wants to use an alarm clock.

In this case the following rules apply:

[TPS_SWCT_01018] AtomicSwComponentType wants to use an alarm clock (flexible variant) (cid:100)

RoleBasedPortAssignment valid roles:
    • EcuM_AlarmClock [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroup
    N/A
(cid:99)()

#@SECTION: 7.11.3.5 BswM
#@CLASS: BswMgrNeeds
<!-- LLM_CONTEXT FOR CLASS BswMgrNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

All use cases for interaction of an application software-component with the BswM require the aggregation in the role serviceNeeds of BswMgrNeeds, a subclass of ServiceNeeds, at SwcServiceDependency.

Table 7.63: BswMgrNeeds

#@SECTION: 7.11.3.5.1 Partial Networking
#@CLASS: PortGroup
<!-- LLM_CONTEXT FOR CLASS PortGroup: Attributes=[adminData, annotation, category, desc, innerGroup, introduction, longName, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

One speciﬁc use case for the existence of a SwcServiceDependency with respect to the interaction with the BswM is the support for partial networking, in particular the association of a PortGroup and the associated PortPrototypes that act as VFC control ports and VFC status ports. For more details please refer to section 4.8.

In this case the following rules apply:

[TPS_SWCT_01126] Access to partial networking via BswM (cid:100) 
RoleBasedPortAssignment valid roles:
    • control [0 .. 1]
    • status [0 .. 1]
RoleBasedDataAssignment 
    N/A
RepresentedPortGroup 
    Reference to the applicable PortGroup associated with the particular partial network. 
(cid:99)(RS_SWCT_03201)

The multiplicities of the RoleBasedPortAssignments for this case have been deﬁned under the assumption that a given software-component may or may not have a VFC control port. Also, it may have a VFC status port. Technically, there could be several VFC status ports per software-component but most likely there is only one VFC status port.

#@SECTION: 7.11.3.5.2 Mode Manager
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: ApplicationSwComponentType
<!-- LLM_CONTEXT FOR CLASS ApplicationSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ServiceSwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->

A software-component that acts as a mode manager exposes a PPortPrototype typed by a ModeSwitchInterface. By this means the mode manager communicates changes of the particular mode to the connected mode users.

On the side of the BswM, an RPortPrototype typed by an ModeSwitchInterface used to receive notifications of mode switches will have to be established (for more details, please refer to [SWS_BswM_00196] and [SWS_BswM_00200]).

In this case the following rules apply:

[TPS_SWCT_01552] Software-component acts as a mode manager (cid:100) 
RoleBasedPortAssignment valid roles:
    • AppModeInterface [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroup 
    none. 
(cid:99)(RS_SWCT_03110, RS_SWCT_03200, RS_SWCT_03203)

A slight variation of this use case exists if the Application Mode Manager serves mode users that consist of both the BswM and other ApplicationSwComponentTypes.

[TPS_SWCT_01572] Application Mode Manager interacts with both BswM and other ApplicationSwComponentTypes (cid:100) If an Application Mode Manager interacts with both BswM and other ApplicationSwComponentTypes the following requirements on the modeling of this scenario shall be taken into account:

1. Mode Request 
    For the configuration of mode requests two separate AbstractRequiredPortPrototypes shall exist:
        • One AbstractRequiredPortPrototype shall be typed by a SenderReceiverInterface with attribute isService set to true. This AbstractRequiredPortPrototype shall be connected to the SwComponentPrototype typed by a ServiceSwComponentType representing the BswM.
        • One AbstractRequiredPortPrototype shall be typed by a SenderReceiverInterface with attribute isService set to false. This AbstractRequiredPortPrototype shall be connected to SwComponentPrototypes typed by ApplicationSwComponentTypes that request model changes.

2. Mode Switch Notification 
    An Application Mode Manager that sends mode switch notifications to both BswM and other ApplicationSwComponentTypes shall expose a single AbstractProvidedPortPrototype for sending the mode switch notification to both the BswM and ApplicationSwComponentTypes. The value of the attribute ModeSwitchInterface.isService shall be set to false.
(cid:99)(RS_SWCT_03200, RS_SWCT_03202)

Rationale for [TPS_SWCT_01572]: technically, the existence of two separate AbstractProvidedPortPrototype for sending the mode switch notification to both the BswM and ApplicationSwComponentTypes would end up in two separate mode machines in the RTE and it would be a tough challenge to keep both mode machines perfectly synchronized.

Therefore, the exception regarding the usage of the attribute isService is justified to mitigate this effect.

On the mode request side, however, the situation is entirely different because the mode requests need arbitration by the Application Mode Manager anyway. This is completely in the scope of the implementation of the Application Mode Manager and AUTOSAR has no stakes in further standardizing this aspect.

Therefore, there is no motivation for a further exception with respect to the value of isService.

#@SECTION: 7.11.3.5.3 Mode User
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

A software-component that acts as a mode user exposes an RPortPrototype typed by a ModeSwitchInterface. By this means the software-component can be notified by mode switches executed at the mode manager (in this case the BswM).

On the side of the BswM, an PPortPrototype typed by an ModeSwitchInterface used to send out notifications of mode switches will have to be established (for more details, please refer to [SWS_BswM_00196] and [SWS_BswM_00202]).

In this case the following rules apply:

[TPS_SWCT_01553] Software-component acts as a mode user (cid:100)
RoleBasedPortAssignment valid roles:
    • AppModeInterface [1]
RoleBasedDataAssignment 
    N/A
RepresentedPortGroup 
    none. 
(cid:99)(RS_SWCT_03110, RS_SWCT_03200, RS_SWCT_03203)

#@SECTION: 7.11.3.5.4 Mode Requester
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->

A software-component that acts as a mode requester exposes an PPortPrototype typed by a SenderReceiverInterface. By this means the software-component can send mode requests towards the mode manager (in this case the BswM).

On the side of the BswM, an RPortPrototype typed by an SenderReceiverInterface used to requests for mode switches will have to be established (for more details, please refer to [SWS_BswM_00195] and [SWS_BswM_00201]).

In this case the following rules apply:

[TPS_SWCT_01554] Software-component acts as a mode requester (cid:100)

RoleBasedPortAssignment valid roles:
    • AppModeRequestInterface [1]
RoleBasedDataAssignment 
    N/A
RepresentedPortGroup 
    none. 
(cid:99)(RS_SWCT_03110, RS_SWCT_03200, RS_SWCT_03202)

#@SECTION: 7.11.3.6 Crypto Service Dependencies
#@CLASS: CryptoServiceNeeds
<!-- LLM_CONTEXT FOR CLASS CryptoServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, maximumKeyLength, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

The meta-class CryptoServiceNeeds is used to define the requirements to configure the CryptoServiceManager.

An SwcInternalBehavior may provide several CryptoServiceNeeds elements where each relates to one ConfigID (see [34] for details). In this context it is of special importance to note which PortPrototypes belong to this ConfigID in order to be able to properly generate the callbacks.

Table 7.64: CryptoServiceNeeds

Please note that for all described use cases of the Crypto Service following rule applies: For every used ClientServerInterface it is necessary to create a RoleBasedPortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServer Interface. The possible role attribute values and the multiplicity of the related Port Prototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment.

#@SECTION: 7.11.3.6.1 Crypto Service Service Use Case: Hash calculation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the hash calculation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02020] AtomicSwComponentType uses the hash calculation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmHash [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00775] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.2 Crypto Service Service Use Case: MAC calculation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the message authentication code (MAC) calculation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02021] AtomicSwComponentType uses the message authentication code (MAC) calculation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmMacGenerate [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00776] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.3 Crypto Service Service Use Case: MAC veriﬁcation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the message authentication code (MAC) verification of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02022] AtomicSwComponentType uses the message authentication code (MAC) verification of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmMacVerify [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00777] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.4 Crypto Service Service Use Case: seeding of random generator
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the generation of random numbers of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02023] AtomicSwComponentType uses the generation of random seed of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmRandomSeed [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00778] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.5 Crypto Service Service Use Case: generation of random numbers
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the generation of random numbers of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02024] AtomicSwComponentType uses the generation of random numbers of the Crypto Service (cid:100)
RoleBasedPortAssignment valid roles:
    • CsmRandomGenerate [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00779] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.6 Crypto Service Service Use Case: symmetrical block encryption
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetrical block encryption of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02025] AtomicSwComponentType uses the symmetrical block encryption of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmSymBlockEncrypt [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00780] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.7 Crypto Service Service Use Case: symmetrical block decryption
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetrical block decryption of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02026] AtomicSwComponentType uses the symmetrical block decryption of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmSymBlockDecrypt [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()
For more information please refer to [SWS_Csm_00781] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.8 Crypto Service Service Use Case: symmetrical encryption
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetrical encryption of Crypto Service. In this case the following setup apply:

[TPS_SWCT_02027] AtomicSwComponentType uses the symmetrical encryption of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmSymEncrypt [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00782] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.9 Crypto Service Service Use Case: symmetrical decryption
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetrical decryption of Crypto Service. In this case the following setup apply:

[TPS_SWCT_02028] AtomicSwComponentType uses the symmetrical decryption of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
    • CsmSymDecrypt [1]
    • CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00783] and [SWS_Csm_00801].
#@SECTION: 7.11.3.6.10 Crypto Service Service Use Case: asymmetrical encryption
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical encryption of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02029] AtomicSwComponentType uses the asymmetrical encryption of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmAsymEncrypt [1]
• CsmCallback [1]

RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00784] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.11 Crypto Service Service Use Case: asymmetrical decryption
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical decryption of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02030] AtomicSwComponentType uses the asymmetrical decryption of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmAsymDecrypt [1]
• CsmCallback [1]

RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A (cid:99)()

For more information please refer to [SWS_Csm_00785] and [SWS_Csm_00801].
#@SECTION: 7.11.3.6.12 Crypto Service Service Use Case: signature generation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the signature generation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02031] AtomicSwComponentType uses the signature generation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmSignatureGenerate [1]
• CsmCallback [1]

RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00786] and [SWS_Csm_00801].
#@SECTION: 7.11.3.6.13 Crypto Service Service Use Case: signature veriﬁcation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the signature verification of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02032] AtomicSwComponentType uses the signature verification of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmSignatureVerify [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A  (cid:99)()

For more information please refer to [SWS_Csm_00787] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.14 Crypto Service Service Use Case: checksum calculation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the checksum calculation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02033] AtomicSwComponentType uses the checksum calculation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmChecksum [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00788] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.15 Crypto Service Service Use Case: key derivation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the key derivation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02034] AtomicSwComponentType uses the key derivation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmKeyDerive [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00789] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.16 Crypto Service Service Use Case: symmetric key derivation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetric key derivation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02035] AtomicSwComponentType uses the symmetric key derivation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmKeyDeriveSymKey [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00790] and [SWS_Csm_00801].
#@SECTION: 7.11.3.6.17 Crypto Service Service Use Case: key exchange protocol, public value calculation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the key exchange interface for public value calculation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02036] AtomicSwComponentType uses the key exchange interface for public value calculation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmKeyExchangeCalcPubVal [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00791] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.18 Crypto Service Service Use Case: key exchange protocol, secret value calculation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the key exchange interface for secret value calculation of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02037] AtomicSwComponentType uses the key exchange interface for secret value calculation of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmKeyExchangeCalcSecret [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A

(cid:99)()

For more information please refer to [SWS_Csm_00792] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.19 Crypto Service Service Use Case: key exchange protocol, calculate symmetric key
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the key exchange interface to calculate symmetric key with the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02038] AtomicSwComponentType uses the key exchange interface to calculate symmetric key with the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmKeyExchangeCalcSymKey [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00793] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.20 Crypto Service Service Use Case: symmetrical key extraction
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetrical key extraction of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02039] AtomicSwComponentType uses the symmetrical key extraction of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmSymKeyExtract [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00794] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.21 Crypto Service Service Use Case: symmetrical key wrapping with symmetrical wrapping key
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the symmetrical key wrapping of the Crypto Service to export a symmetrical key structure with a symmetric key. In this case the following setup apply:

[TPS_SWCT_02040] AtomicSwComponentType uses the symmetrical key wrapping of the Crypto Service to export a symmetrical key structure with a symmetric key (cid:100)

RoleBasedPortAssignment valid roles:
• CsmSymKeyWrapSym [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A

(cid:99)()

For more information please refer to [SWS_Csm_00795] and [SWS_Csm_00801].
#@SECTION: 7.11.3.6.22 Crypto Service Service Use Case: symmetrical key wrapping with asymmetrical wrapping key
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical key wrapping of the Crypto Service to export a symmetrical key structure with a asymmetric key. In this case the following setup apply:

[TPS_SWCT_02041] AtomicSwComponentType uses the asymmetrical key wrapping of the Crypto Service to export a symmetrical key structure with a asymmetric key (cid:100)

RoleBasedPortAssignment valid roles:
• CsmSymKeyWrapAsym [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A

(cid:99)()

For more information please refer to [SWS_Csm_00796] and [SWS_Csm_00801].
#@SECTION: 7.11.3.6.23 Crypto Service Service Use Case: asymmetrical public key extraction
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical public key extraction of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02042] AtomicSwComponentType uses the asymmetrical public key extraction of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmAsymPublicKeyExtract [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00797] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.24 Crypto Service Service Use Case: asymmetrical private key extraction
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical private key extraction of the Crypto Service. In this case the following setup apply:

[TPS_SWCT_02043] AtomicSwComponentType uses the asymmetrical private key extraction of the Crypto Service (cid:100)

RoleBasedPortAssignment valid roles:
• CsmAsymPrivateKeyExtract [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00798] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.25 Crypto Service Service Use Case: asymmetrical key wrapping with symmetrical wrapping key
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical key wrapping of the Crypto Service to export a (asymmetric) private key structure with a symmetrical wrapping key. In this case the following setup apply:

[TPS_SWCT_02044] AtomicSwComponentType uses the asymmetrical key wrapping of the Crypto Service to export a (asymmetric) private key structure with a symmetrical wrapping key (cid:100)
RoleBasedPortAssignment valid roles:
• CsmAsymPrivateKeyWrapSym [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00799] and [SWS_Csm_00801].

#@SECTION: 7.11.3.6.26 Crypto Service Service Use Case: asymmetrical key wrapping with asymmetrical wrapping key
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: a AtomicSwComponentType uses the asymmetrical key wrapping of the Crypto Service to export a (asymmetric) private key structure with a asymmetrical wrapping key. In this case the following setup apply:

[TPS_SWCT_02045] AtomicSwComponentType uses the asymmetrical key wrapping of the Crypto Service to export a (asymmetric) private key structure with a asymmetrical wrapping key (cid:100)

RoleBasedPortAssignment valid roles:
• CsmAsymPrivateKeyWrapAsym [1]
• CsmCallback [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Csm_00800] and [SWS_Csm_00801].

#@SECTION: 7.11.3.7 Diagnostic Service Dependency
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

This chapter describes the usage of the specific diagnostic meta-classes derived from ServiceNeeds within an atomic software-component. An overview of common diagnostic service needs has already been introduced in figure 7.36 and can be divided into four main parts: Function Inhibition Needs 7.11.3.7.1, Diagnostic Event Needs 7.11.3.7.2, Diagnostic Communication Needs 7.11.3.7.3, and needs to fulfill the OBD related requirements 7.11.3.7.4.

Please note that for the described use cases of the Diagnostic Services the following rule applies:

[TPS_SWCT_01129] Express diagnostic capabilities (cid:100) For every used ClientServerInterface it is necessary to create a RoleBasedPortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServerInterface.

The possible role attribute values and the multiplicity of the related PortPrototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment. (cid:99)(RS_SWCT_03190)

#@SECTION: 7.11.3.7.1 Function Inhibition Needs
#@CLASS: FunctionInhibitionNeeds
<!-- LLM_CONTEXT FOR CLASS FunctionInhibitionNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->

The meta-class FunctionInhibitionNeeds is used to define requirements in order to configure the Diagnostic Event Manager Service.

An SwcInternalBehavior may provide several FunctionInhibitionNeeds elements, each defines the requirements related to one function inhibition ID (for the terms related to the AUTOSAR Function Inhibition Manager, see [35]).

Table 7.65: FunctionInhibitionNeeds

#@SECTION: 7.11.3.7.1.1 Function Inhibition Manager Service use Case: read function permission
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

[TPS_SWCT_02505] Setup for Function Inhibition Manager Service use Case: read function permission (cid:100) Scenario: a AtomicSwComponentType read the function permission from FiM in order to enable or disable a functionality. In this case the following setup apply:

ServiceNeeds kind FunctionInhibitionNeeds

RoleBasedPortAssignment valid roles:
• FunctionInhibition [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)()

For more information please refer to [SWS_Fim_00090].

#@SECTION: 7.11.3.7.2 Diagnostic Event Needs
#@CLASS: DiagnosticCapabilityElement
<!-- LLM_CONTEXT FOR CLASS DiagnosticCapabilityElement: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类); Childs=[DiagnosticCommunicationManagerNeeds, DiagnosticEnableConditionNeeds, DiagnosticEventInfoNeeds, DiagnosticEventManagerNeeds, DiagnosticEventNeeds, DiagnosticIoControlNeeds, DiagnosticOperationCycleNeeds, DiagnosticRoutineNeeds, DiagnosticStorageConditionNeeds, DiagnosticValueNeeds, DiagnosticsCommunicationSecurityNeeds, DtcStatusChangeNotificationNeeds, ObdControlServiceNeeds, ObdInfoServiceNeeds, ObdMonitorServiceNeeds, ObdPidServiceNeeds, ObdRatioServiceNeeds, WarningIndicatorRequestedBitNeeds] (直接子类) -->
#@CLASS: DiagnosticEnableConditionNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEnableConditionNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, initialStatus, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticEventInfoNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventInfoNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcKind, dtcNumber, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdDtcNumber, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, udsDtcNumber, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticEventManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticEventNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, considerPtoStatus, cryptoServiceNeeds, deferringFid, desc, diagEventDebounceAlgorithm, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcKind, dtcNumber, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, inhibitingFid, inhibitingSecondaryFid, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdDtcNumber, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, reportBehavior, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, udsDtcNumber, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticOperationCycleNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticOperationCycleNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, operationCycle, operationCycleAutomaticEnd, operationCycleAutostart, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticStorageConditionNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticStorageConditionNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, initialStatus, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@ENUM: DtcKindEnum
<!-- LLM_CONTEXT FOR ENUM DtcKindEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: DtcStatusChangeNotificationNeeds
<!-- LLM_CONTEXT FOR CLASS DtcStatusChangeNotificationNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcFormatType, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@ENUM: DtcFormatTypeEnum
<!-- LLM_CONTEXT FOR ENUM DtcFormatTypeEnum: Literals=[] (元数据中未找到字面量) -->
#@ENUM: EventAcceptanceStatusEnum
<!-- LLM_CONTEXT FOR ENUM EventAcceptanceStatusEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: FunctionInhibitionNeeds
<!-- LLM_CONTEXT FOR CLASS FunctionInhibitionNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: ObdRatioServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdRatioServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, connectionType, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, iumprGroup, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, rateBasedMonitoredEvent, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, usedFid, usedSecondaryFid, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@ENUM: OperationCycleTypeEnum
<!-- LLM_CONTEXT FOR ENUM OperationCycleTypeEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@ENUM: ReportBehaviorEnum
<!-- LLM_CONTEXT FOR ENUM ReportBehaviorEnum: Literals=[] (元数据中未找到字面量) -->
#@ENUM: StorageConditionStatusEnum
<!-- LLM_CONTEXT FOR ENUM StorageConditionStatusEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@ENUM: DiagnosticAudienceEnum
<!-- LLM_CONTEXT FOR ENUM DiagnosticAudienceEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: ObdPidServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdPidServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, parameterId, securityAccessLevel, shortName, shortNameFragment, standard, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagEventDebounceAlgorithm
<!-- LLM_CONTEXT FOR CLASS DiagEventDebounceAlgorithm: Attributes=[adminData, annotation, category, desc, diagEventDebounceCounterBased, diagEventDebounceMonitorInternal, diagEventDebounceTimeBased, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[DiagEventDebounceCounterBased, DiagEventDebounceMonitorInternal, DiagEventDebounceTimeBased] (直接子类) -->
#@CLASS: DiagEventDebounceCounterBased
<!-- LLM_CONTEXT FOR CLASS DiagEventDebounceCounterBased: Attributes=[adminData, annotation, category, counterDecrementStepSize, counterFailedThreshold, counterIncrementStepSize, counterJumpDown, counterJumpDownValue, counterJumpUp, counterJumpUpValue, counterPassedThreshold, desc, diagEventDebounceCounterBased, diagEventDebounceMonitorInternal, diagEventDebounceTimeBased, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[DiagEventDebounceAlgorithm] (直接父类) -->
#@CLASS: DiagEventDebounceTimeBased
<!-- LLM_CONTEXT FOR CLASS DiagEventDebounceTimeBased: Attributes=[adminData, annotation, category, desc, diagEventDebounceCounterBased, diagEventDebounceMonitorInternal, diagEventDebounceTimeBased, introduction, longName, shortName, shortNameFragment, timeFailedThreshold, timePassedThreshold] (包含继承及相关属性); Generalization=[DiagEventDebounceAlgorithm] (直接父类) -->
#@CLASS: DiagEventDebounceMonitorInternal
<!-- LLM_CONTEXT FOR CLASS DiagEventDebounceMonitorInternal: Attributes=[adminData, annotation, category, desc, diagEventDebounceCounterBased, diagEventDebounceMonitorInternal, diagEventDebounceTimeBased, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[DiagEventDebounceAlgorithm] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->


The meta-classes DiagnosticEventManagerNeeds is used to define requirements in order to configure the Diagnostic Event Manager Service.

An SwcInternalBehavior may several DiagnosticEventManagerNeeds elements that define the mappings for the general diagnostic event manager behavior (for the terms related to the AUTOSAR Diagnostic Event Manager see [36]).
Table 7.66: DiagnosticEventManagerNeeds

The meta-class DiagnosticCapabilityElement is used to provide generic information about diagnostic capabilities. Further on, the usage of DiagnosticCapabilityElement indicates that all ServiceNeeds which inherit from DiagnosticCapabilityElement express the following intentions:
• Need to interact with AUTOSAR Service Dem or Dcm.
• Provide services for the on-board diagnostics.

Table 7.67: DiagnosticCapabilityElement
Table 7.68: DiagnosticAudienceEnum

The meta-classes DiagnosticEventNeeds is used to define requirements to configure the Diagnostic Event Manager Service. An SwcInternalBehavior may provide several DiagnosticEventNeeds elements where each defines all the requirements related to one diagnostic event (for the terms related to the AUTOSAR Diagnostic Event Manager see [36]).

In addition, ObdPidServiceNeeds and ObdRatioServiceNeeds are required in order to specify the needs for OBD diagnostic service calls.

[TPS_SWCT_01591] Existence of attribute DiagnosticEventNeeds.reportBehavior (cid:100) The attribute DiagnosticEventNeeds.reportBehavior shall be ignored if it is specified in the context of a SwcServiceDependency. (cid:99)(RS_SWCT_03190)

The rationale for the existence of [TPS_SWCT_01591] is that a software-component can never report errors to the Dem before the Dem is fully initialized.
Table 7.69: DiagnosticEventManagerNeeds
Table 7.70: DtcKindEnum

The diagEventDebounceAlgorithm attribute defines the kind of expected debouncing by the Diagnostic Event Manager or defines that the debouncing is implemented by the software component.

The class DiagEventDebounceAlgorithm inherits from Identifiable in order to allow further documentation of the debouncing algorithm as well as non formalized description or non standardized description by the means of Sdg on expected configuration of the DiagEventDebounceAlgorithm in the Diagnostic Event Manager.

[constr_1138] assignedPort and DiagEventDebounceMonitorInternal (cid:100) The existence of an assignedPort in combination with a DiagEventDebounceAlgorithm shall only be respected for the concrete subclass DiagEventDebounceMonitorInternal. (cid:99)()

[constr_1139] assignedPort of DiagEventDebounceMonitorInternal shall refer to an RPortPrototype (cid:100) Concerning the debouncing, the software-component acts as a client and thus the assignedPort defined with respect to a DiagEventDebounceMonitorInternal may only refer to an RPortPrototype. The standardized value of the role identifier of the assignedPort shall be DiagFaultDetectionCounterPort. (cid:99)()

Table 7.71: DiagnosticEventNeeds
Table 7.72: DiagEventDebounceAlgorithm
Table 7.73: DiagEventDebounceCounterBased
Table 7.74: DiagEventDebounceTimeBased
Table 7.75: DiagEventDebounceMonitorInternal
Figure 7.45: Relationship of DiagnosticEventNeeds and FunctionInhibitionNeeds

The figure 7.45 shows the relationship of the class DiagnosticEventNeeds. The given M2 structure support to express following properties of a diagnostic monitor in addition to the basic set of attributes provided by DiagnosticCapabilityElement:

With the inhibitingFid reference to an FunctionInhibitionNeeds instance on M1 it is declared that either the monitoring of a symptom or the reporting of detected faults can be inhibited by the usage of the Function Inhibition Managers.

The used PortPrototype which has to be connected to the Function Inhibition Managers is determined by the RoleBasedPortAssignment of the related FunctionInhibitionNeeds instance on M1.

The reference from a M1 instance of an ObdRatioServiceNeeds to an M1 instance of a DiagnosticEventNeeds specifies that the related Diagnostic Monitor supports Rate Based Monitoring. For further details see 7.11.3.7.4

[TPS_SWCT_01582] Semantics of DiagnosticEventNeeds.deferringFid (cid:100) Diagnostic monitor implementations use Function Identifiers (FID) to acquire permission from FiM before executing the fault detection. Typically, the permission is not granted by FiM if other Events have already been reported as FAILED, which would lead to a double-detection of the same failure. In some cases (see [35]), diagnostic monitor implementations do not only shut down completely in case of "no permission", but fully compute their result and do just not deliver it to Dem before further conditions are fulfilled. Typically, such diagnostics can detect a coarse failure quickly. But it avoids reporting FAIL early to give other Events a chance to deliver a more precise FAIL. In such cases, the delivery of the result is only allowed when FiM grants a permission, with inhibitions on NOT_TESTED of other Events. These Function Inhibitions are specified by means of the attribute DiagnosticEventNeeds.deferringFid. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

As a corresponding concept to DiagnosticEventNeeds, the DiagnosticEventInfoNeeds represents the needs to a a given software-component that is interested to get information about specific DTCs.

Table 7.76: DiagnosticEventInfoNeeds
Table 7.77: DiagnosticOperationCycleNeeds
Table 7.78: OperationCycleTypeEnum
Table 7.79: DiagnosticEnableConditionNeeds
Table 7.80: EventAcceptanceStatusEnum
Table 7.81: DiagnosticStorageConditionNeeds
Table 7.82: StorageConditionStatusEnum
Table 7.83: DtcStatusChangeNotificationNeeds
Table 7.84: DtcFormatTypeEnum

#@SECTION: 7.11.3.7.2.1 Dem Service Use Case: diagnostic monitor, debouncing by Dem
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticEventNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, considerPtoStatus, cryptoServiceNeeds, deferringFid, desc, diagEventDebounceAlgorithm, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcKind, dtcNumber, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, inhibitingFid, inhibitingSecondaryFid, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdDtcNumber, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, reportBehavior, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, udsDtcNumber, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
Scenario: an AtomicSwComponentType implements a Diagnostic Monitor. The debouncing of the failure condition shall be configured and processed by the Dem. In this case the following setup apply:

[TPS_SWCT_01028] AtomicSwComponentType implements a Diagnostic Monitor (cid:100)

1. ServiceNeeds kind DiagnosticEventNeeds
2. RoleBasedPortAssignment valid roles:
    • DiagnosticMonitor [1]
    • DiagnosticInfo [0 .. 1]
    • CallbackInitMonitorForEvent [0 .. 1]
    • CallbackEventStatusChange [0 .. 1]
    • CallbackClearEventAllowed [0 .. 1]
3. RoleBasedDataAssignment
    N/A
4. RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

Please note that for the implementation of this scenario DiagEventDebounceCounterBased or DiagEventDebounceTimeBased algorithm should be used as diagEventDebounceAlgorithm.

#@SECTION: 7.11.3.7.2.2 Dem Service Use Case: diagnostic monitor, debouncing by SWC
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticEventNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, considerPtoStatus, cryptoServiceNeeds, deferringFid, desc, diagEventDebounceAlgorithm, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcKind, dtcNumber, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, inhibitingFid, inhibitingSecondaryFid, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdDtcNumber, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, reportBehavior, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, udsDtcNumber, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType implements a Diagnostic Monitor. The debouncing of the failure condition shall be processed by the software component. In this case the following setup applies:

[TPS_SWCT_01029] AtomicSwComponentType implements a Diagnostic Monitor (cid:100)

1. ServiceNeeds kind DiagnosticEventNeeds
2. RoleBasedPortAssignment valid roles:
    • DiagnosticMonitor [1]
    • DiagnosticInfo [0 .. 1]
    • CallbackInitMonitorForEvent [0 .. 1]
    • CallbackEventStatusChange [0 .. 1]
    • CallbackClearEventAllowed [0 .. 1]
    • CallbackGetFaultDetectCounter [1]
3. RoleBasedDataAssignment
    N/A
4. RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

Please note that for the implementation of this scenario DiagEventDebounceMonitorInternal algorithm should be used as diagEventDebounceAlgorithm.

#@SECTION: 7.11.3.7.2.3 Dem Service Use Case: software-component provides information about operation cycles
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticOperationCycleNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticOperationCycleNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, operationCycle, operationCycleAutomaticEnd, operationCycleAutostart, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType provides information about operating cycles, e.g. ignition cycle or driving cycle.

[TPS_SWCT_01132] AtomicSwComponentType provides information about operating cycles (cid:100)

ServiceNeeds kind DiagnosticOperationCycleNeeds
RoleBasedPortAssignment valid roles:
    • OperationCycle [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)
For more information please refer to [SWS_Dem_00601] and [ECUC_Dem_00703].

#@SECTION: 7.11.3.7.2.4 Dem Service Use Case: software-component provides information about aging cycles
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: DiagnosticEventManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
Scenario: an AtomicSwComponentType provides information about aging cycles.

[TPS_SWCT_01133] AtomicSwComponentType provides information about aging cycles (cid:100)

ServiceNeeds kind DiagnosticEventManagerNeeds
RoleBasedPortAssignment valid roles:
    • AgingCycle [0 .. 1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00602].

#@SECTION: 7.11.3.7.2.5 Dem Service Use Case: software-component enables storage of DTCs in general
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticEnableConditionNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEnableConditionNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, initialStatus, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: a AtomicSwComponentType enables the storage of DTCs in general.

[TPS_SWCT_01134] AtomicSwComponentType enables storage of DTCs in general (cid:100)

ServiceNeeds kind DiagnosticEnableConditionNeeds
RoleBasedPortAssignment valid roles:
    • EnableCondition [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00604] and [ECUC_Dem_00656].

#@SECTION: 7.11.3.7.2.6 Dem Service Use Case: software-component enables storage of subsequent DTCs
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticStorageConditionNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticStorageConditionNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, initialStatus, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType enables the storage of subsequent DTCs.

[TPS_SWCT_01135] AtomicSwComponentType enables storage of subsequent DTCs (cid:100)

ServiceNeeds kind DiagnosticStorageConditionNeeds
RoleBasedPortAssignment valid roles:
    • StorageCondition [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00605].

The relevant DTCs shall be configured in ECUC because at the time the Atomic SwComponentType is designed the information about which DTCs are relevant is not fully available.

#@SECTION: 7.11.3.7.2.7 Dem Service Use Case: retrieve information of the lamp status
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->

Please note that for this specific use case the application of a concrete ServiceNeeds is not yet clarified.

Scenario: an AtomicSwComponentType retrieves information of the lamp status.

[TPS_SWCT_01136] AtomicSwComponentType retrieves information of the lamp status (cid:100)

RoleBasedPortAssignment valid roles:
    • IndicatorStatus [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00606].

#@SECTION: 7.11.3.7.2.8 Dem Service Use Case: DEM provides information that the fault storage overflows
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->

Please note that for this specific use case the application of a concrete ServiceNeeds is not yet clarified.

Scenario: the Dem provides information that the fault storage overflows.

[TPS_SWCT_01137] Dem provides information that the fault storage overflows (cid:100)

RoleBasedPortAssignment valid roles:
    • EvMemOverflowIndication [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)
For more information please refer to [SWS_Dem_00607].

#@SECTION: 7.11.3.7.2.9 Dem Service Use Case: software-component suppresses the storage of DTCs
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticEventManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType suppresses the storage of DTCs within the Dem.

[TPS_SWCT_01138] AtomicSwComponentType suppresses the storage of DTCs within the Dem (cid:100)

ServiceNeeds kind DiagnosticEventManagerNeeds
RoleBasedPortAssignment valid roles:
    • DTCSuppression [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00608].

#@SECTION: 7.11.3.7.2.10 Dem Service Use Case: software-component informs that the PTO is active
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: DiagnosticEventManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType informs the Dem that the PTO is active.

[TPS_SWCT_01139] AtomicSwComponentType informs the Dem that the PTO is active (cid:100)

1.ServiceNeeds kind DiagnosticEventManagerNeeds
2.RoleBasedPortAssignment
    The following roles are applicable:
        • PowerTakeOff [1]
3.RoleBasedDataAssignment
    N/A
4.RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00612].

#@SECTION: 7.11.3.7.2.11 Dem Service Use Case: software-component needs information about any DTC status change
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DtcStatusChangeNotificationNeeds
<!-- LLM_CONTEXT FOR CLASS DtcStatusChangeNotificationNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcFormatType, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@ENUM: DtcFormatTypeEnum
<!-- LLM_CONTEXT FOR ENUM DtcFormatTypeEnum: Literals=[] (元数据中未找到字面量) -->

Scenario: an AtomicSwComponentType needs information about any DTC status change. There is no limitation on the number of software-components requesting the information.

[TPS_SWCT_01140] AtomicSwComponentType needs information about specific DTC without being a diagnostic monitor (cid:100)

ServiceNeeds kind DtcStatusChangeNotificationNeeds
RoleBasedPortAssignment valid roles:
    • CallbackDTCStatusChange [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00617].

In the case the software-component needs notifications about different kinds of the DTC status change (formalized by DtcFormatTypeEnum) it is applicable to create a SwcServiceDependency for each kind of status change.

#@SECTION: 7.11.3.7.2.12 Dem Service Use Case: call operation if the data of a given diagnostic event changes (I)
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: DiagnosticEventInfoNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventInfoNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcKind, dtcNumber, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdDtcNumber, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, udsDtcNumber, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
Scenario: an AtomicSwComponentType provides a PPortPrototype typed by the ClientServerInterface CallbackEventDataChanged. The service component calls the ClientServerOperation EventDataChanged if the corresponding diagnostic event changes in terms of the underlying data.

For each diagnostic events to which the AtomicSwComponentType is conceptually connected it needs to provide one PPortPrototype towards the service component.

[TPS_SWCT_01425] AtomicSwComponentType provides one callback per event if diagnostic event data change (cid:100)

ServiceNeeds kind DiagnosticEventInfoNeeds
RoleBasedPortAssignment valid roles:
    • CallbackEventDataChanged [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00618].

#@SECTION: 7.11.3.7.2.13 Dem Service Use Case: call operation if the data or status of any diagnostic event changes (II)
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: DiagnosticEventManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType shall react on any diagnostic event status change and/or any diagnostic event data change. For instance this may be used to write a time stamp when any event status changes regardless of the event id.

In contrast to the scenario described in chapter 7.11.3.7.2.12 or 7.11.3.7.2.11 this case foresees the existence of a single PPortPrototype that covers all relevant diagnostic events.

[TPS_SWCT_01426] AtomicSwComponentType provides callback if any diagnostic event data and/or status changed (cid:100)

ServiceNeeds kind DiagnosticEventManagerNeeds
RoleBasedPortAssignment valid roles:
    • GeneralCallbackEventDataChanged [0..1]
    • GeneralCallbackEventStatusChange [0..1]
    • GeneralDiagnosticInfo [0..1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
For more information please refer to [SWS_Dem_00616], [SWS_Dem_00619], and [SWS_Dem_00600].

In order to react on diagnostic event status changes the software component shall provide a single PPortPrototype typed as a client server interface compatible to GeneralCallbackEventDataChanged.

In order to react on diagnostic event data changes the software component shall provide a single PPortPrototype typed as a client server interface compatible to GeneralCallbackEventDataChanged.

If the software-component additionally has to read further information of the specific diagnostic event from Dem it shall provide a RPortPrototype typed as a client server interface compatible to GeneralDiagnosticInfo. It shall also specify DiagnosticEventInfoNeeds. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

#@SECTION: 7.11.3.7.2.14 Dem Service Use Case: software-component provides data for diagnostic purposes
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

Please note that for this specific use case the application of a concrete ServiceNeeds is not yet clarified.

Scenario: an AtomicSwComponentType provides data to be used for diagnostic purposes. The provision of data can be done by means of PPortPrototypes typed by either ClientServerInterfaces or SenderReceiverInterfaces. The usage of the latter, however, is not further detailed in the applicable SWS [36] and therefore no more details are to be provided in this document.

[TPS_SWCT_01427] AtomicSwComponentType provides data for diagnostic purposes via ClientServerInterface (cid:100)
RoleBasedPortAssignment valid roles: 
    • DataServices [1] 
RoleBasedDataAssignment 
    N/A
RepresentedPortGroups
    N/A 
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01634] Suffix used for the resulting name of the PortInterface for the Data Services (cid:100) The suffix used for the resulting name of the PortInterface for the Data Services (DataServices_{Data}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00621].

#@SECTION: 7.11.3.7.2.15 Dem Service Use Case: interface to DCM
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: ServiceSwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->
#@CLASS: ApplicationSwComponentType
<!-- LLM_CONTEXT FOR CLASS ApplicationSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->

Please note that for this specific use case the application of a concrete ServiceNeeds is not yet clarified.

Scenario: a ServiceSwComponentType representing the Dem provides a PPortPrototype for the Dcm. Although this scenario does not apply to Application SwComponentTypes it is included for the sake of completeness.

[TPS_SWCT_01428] ServiceSwComponentType representing the Dem provides a PPortPrototype for the Dcm (cid:100)
RoleBasedPortAssignment valid roles:
    • DcmIf [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00609].

#@SECTION: 7.11.3.7.2.16 Dem Service Use Case: software-component gets information about a specific DTC
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticEventInfoNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticEventInfoNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcKind, dtcNumber, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdDtcNumber, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, udsDtcNumber, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedDataAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataAssignment: Attributes=[role, usedDataElement, usedParameterElement, usedPim, variationPoint] (包含继承及相关属性) -->

Scenario: an AtomicSwComponentType specifies DiagnosticEventInfoNeeds in order to be able to get information about specific DTCs. This use case to some extent is similar to [TPS_SWCT_01426] but does not replace that use case.

[TPS_SWCT_01453] Software-component gets information about a specific DTC (cid:100)

ServiceNeeds kind DiagnosticEventInfoNeeds
RoleBasedPortAssignment valid roles:
    • DiagnosticInfo [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00609].

#@SECTION: 7.11.3.7.3 Diagnostic Communication Needs
#@CLASS: DiagnosticCommunicationManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticCommunicationManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, serviceRequestCallbackType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticIoControlNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticIoControlNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, currentValue, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, didNumber, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, freezeCurrentStateSupported, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, resetToDefaultSupported, securityAccessLevel, shortName, shortNameFragment, shortTermAdjustmentSupported, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticRoutineNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticRoutineNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagRoutineType, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, ridNumber, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: DiagnosticValueNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticValueNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueAccess, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, didNumber, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, fixedLength, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, processingStyle, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: SwcInternalBehavior
<!-- LLM_CONTEXT FOR CLASS SwcInternalBehavior: Attributes=[adminData, annotation, arTypedPerInstanceMemory, category, constantMemory, constantValueMapping, dataTypeMapping, desc, event, exclusiveArea, exclusiveAreaNestingOrder, explicitInterRunnableVariable, handleTerminationAndRestart, implicitInterRunnableVariable, includedDataTypeSet, includedModeDeclarationGroupSet, instantiationDataDefProps, introduction, longName, perInstanceMemory, perInstanceParameter, portAPIOption, runnable, serviceDependency, sharedParameter, shortName, shortNameFragment, staticMemory, supportsMultipleInstantiation, variationPoint, variationPointProxy] (包含继承及相关属性); Generalization=[InternalBehavior] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@ENUM: DiagnosticServiceRequestCallbackTypeEnum
<!-- LLM_CONTEXT FOR ENUM DiagnosticServiceRequestCallbackTypeEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: RunnableEntity
<!-- LLM_CONTEXT FOR CLASS RunnableEntity: Attributes=[activationReason, adminData, annotation, argument, asynchronousServerCallResultPoint, canBeInvokedConcurrently, canEnterExclusiveArea, category, dataReadAccess, dataReceivePointByArgument, dataReceivePointByValue, dataSendPoint, dataWriteAccess, desc, exclusiveAreaNestingOrder, externalTriggeringPoint, internalTriggeringPoint, introduction, longName, minimumStartInterval, modeAccessPoint, modeSwitchPoint, parameterAccess, readLocalVariable, reentrancyLevel, runsInsideExclusiveArea, serverCallPoint, shortName, shortNameFragment, swAddrMethod, symbol, variationPoint, waitPoint, writtenLocalVariable] (包含继承及相关属性); Generalization=[AtpStructureElement, ExecutableEntity] (直接父类) -->
#@ENUM: DiagnosticRoutineTypeEnum
<!-- LLM_CONTEXT FOR ENUM DiagnosticRoutineTypeEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: InternalBehavior
<!-- LLM_CONTEXT FOR CLASS InternalBehavior: Attributes=[adminData, annotation, category, constantMemory, constantValueMapping, dataTypeMapping, desc, exclusiveArea, exclusiveAreaNestingOrder, introduction, longName, shortName, shortNameFragment, staticMemory] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[BswInternalBehavior, SwcInternalBehavior] (直接子类) -->
#@CLASS: BswServiceDependency
<!-- LLM_CONTEXT FOR CLASS BswServiceDependency: Attributes=[assignedData, assignedDataType, assignedEntryRole, ident, serviceNeeds, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[ServiceDependency] (直接父类) -->
#@ENUM: DiagnosticValueAccessEnum
<!-- LLM_CONTEXT FOR ENUM DiagnosticValueAccessEnum: Literals=[] (元数据中未找到字面量) -->
#@ENUM: DiagnosticProcessingStyleEnum
<!-- LLM_CONTEXT FOR ENUM DiagnosticProcessingStyleEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: DiagnosticsCommunicationSecurityNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticsCommunicationSecurityNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

The meta-class DiagnosticCommunicationManagerNeeds is used to define requirements in order to configure the Diagnostic Communication Manager Service.

An SwcInternalBehavior may provide a DiagnosticCommunicationManagerNeeds element which defines the mappings for the general diagnostic communication (for the terms related to the AUTOSAR Diagnostic Communication Manager see [37]).

Table 7.85: DiagnosticCommunicationManagerNeeds

Table 7.86: DiagnosticServiceRequestCallbackTypeEnum

The meta-class DiagnosticRoutineNeeds is used to define requirements to configure the Diagnostic Communication Manager Service. A PPortPrototype typed by a ClientServerInterface(where isService shall be set to true) may provide ClientServerOperations (for example, "start", "stop", and "RequestResults").

The PPortPrototype corresponds to the diagnostic service RoutineControl. Within the SwcInternalBehavior up to three RunnableEntitys are defined for implementing the ClientServerOperations mentioned before.

The enumeration parameter DiagnosticRoutineTypeEnum is used to define whether the diagnostic server or client is responsible for stopping the routine.

Please note that [constr_1340] and [constr_1341] apply for the application of DiagnosticRoutineNeeds. These constraints are part of the specification of the DiagnosticExtract [38].

Table 7.87: DiagnosticRoutineNeeds

Table 7.88: DiagnosticRoutineTypeEnum

The meta-class DiagnosticIoControlNeeds is used to define requirements to configure the Diagnostic Communication Manager Service. The PPortPrototype corresponds to the diagnostic service InputOutputControlByIdentifier. Within the SwcInternalBehavior up to three RunnableEntitys are defined for implementing the ClientServerOperations mentioned before.

Table 7.89: DiagnosticIoControlNeeds

The meta-class DiagnosticValueNeeds is used to define requirements in order to configure the Diagnostic Communication Manager Service as well as the Diagnostic Event Manager Service.

The DCM can access either local values via a ClientServerInterface or it may access dataElements in a PPortPrototype typed by a SenderReceiverInterface. For this purpose, the DiagnosticValueNeeds require associations to local values (i.e. inside InternalBehavior) or respectively dataElements.

The attribute DiagnosticValueNeeds.diagnosticValueAccess of type DiagnosticValueAccessEnum allows for distinguishing between current values to read diagnostic information (readOnly) and data elements which are additionally classified as configurable (readWrite).

[constr_1363] Existence of attributes of DiagnosticValueNeeds (cid:100) if DiagnosticValueNeeds is aggregated by a SwcServiceDependency in the role serviceNeeds then the attributes • DiagnosticValueNeeds.diagnosticValueAccess • DiagnosticValueNeeds.dataLength shall not exist. (cid:99)()

[constr_1364] Existence of attributes of DiagnosticIoControlNeeds (cid:100) if DiagnosticIoControlNeeds is aggregated by a SwcServiceDependency in the role serviceNeeds then the attributes • DiagnosticIoControlNeeds.freezeCurrentStateSupported • DiagnosticIoControlNeeds.shortTermAdjustmentSupported shall not exist. (cid:99)()

For all intents and purposes, the statement made by [constr_1363] and [constr_1364] boils down to the fact that these attributes can only be reasonably used in the context of a BswServiceDependency.

Table 7.90: DiagnosticValueNeeds

Table 7.91: DiagnosticValueAccessEnum M2::AUTOSARTemplates::CommonStructure::ServiceNeeds

Table 7.92: DiagnosticProcessingStyleEnum

Table 7.93: DiagnosticsCommunicationSecurityNeeds

#@SECTION: 7.11.3.7.3.1 Dcm Service Use Case: read/write current values by Client Server Interface
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

Scenario: an AtomicSwComponentType offers a PPortPrototype typed by ClientServerInterface to read/write current value via diagnostic services (e.g. measurements, variant coding)

[TPS_SWCT_02002] AtomicSwComponentType offers a PPortPrototype typed by ClientServerInterface to read/write current value via diagnostic services (cid:100)
ServiceNeeds kind DiagnosticValueNeeds
RoleBasedPortAssignment valid roles:
    • DataServices [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups 
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01628] Suffix used for the resulting name of the PortInterface for the Data Services (cid:100) The suffix used for the resulting name of the PortInterface for the Data Services (DataServices_{Data}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00686].

#@SECTION: 7.11.3.7.3.2 Dcm Service Use Case: read/write current values of speciﬁc DID by Client Server Interface
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DiagnosticValueNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticValueNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueAccess, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, didNumber, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, fixedLength, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, processingStyle, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
Scenario: an AtomicSwComponentType offers a PPortPrototype typed by ClientServerInterface to read/write current values via diagnostic services (e.g. measurements, variant coding) where the applicable DID is passed as an argument to the access functions. This use case applies mostly if the software-component provides the information related to more than one DID.

[TPS_SWCT_01639] AtomicSwComponentType offers a PPortPrototype typed by ClientServerInterface to read/write current value via diagnostic services where the applicable DID is passed as an argument to the access functions (cid:100) 
1. ServiceNeeds kind DiagnosticValueNeeds
2. RoleBasedPortAssignment valid roles:
    • DataServices_DIDRange [1]
3. RoleBasedDataAssignment
    N/A
4. RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01640] Suffix used for the resulting name of the PortInterface for the Data Services (cid:100) The suffix used for the resulting name of the PortInterface for the Data Services (DataServices_DIDRange_{Range}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00769].

#@SECTION: 7.11.3.7.3.3 Dcm Service Use Case: read/write current values by Sender Receiver Interface
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DiagnosticValueNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticValueNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueAccess, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, didNumber, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, fixedLength, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, processingStyle, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
Scenario: an AtomicSwComponentType offers PortPrototypes typed by Scenario: SenderReceiverInterfaces to read/write current values via diagnostic services (e.g. measurements, variant coding) This is mainly used for data which are available at ports anyhow used for other communication purpose.

Note: this scenario can be implemented as a regular sender/receiver communication without the necessity to use a SwcServiceDependency. The description of a Swc ServiceDependency (even if it is technically not required) may help to advertise the special role of the corresponding dataElement with respect to diagnostics.

[TPS_SWCT_02003] AtomicSwComponentType offers PortPrototypes typed by SenderReceiverInterfaces to read/write current values via diagnostic services (cid:100) 
1. ServiceNeeds kind DiagnosticValueNeeds 
2. RoleBasedPortAssignment 
    N/A
3. RoleBasedDataAssignment valid roles: 
    • signalBasedDiagnostics [1..2] 
4. RepresentedPortGroups
    N/A

To read the signal the AtomicSwComponentType shall offer an AbstractProvidedPortPrototype, to write the signal the AtomicSwComponentType shall offer an AbstractRequiredPortPrototype. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00687].

#@SECTION: 7.11.3.7.3.4 Dcm Service Use Case: start/stop or request routine results
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DiagnosticRoutineNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticRoutineNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagRoutineType, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, ridNumber, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
Scenario: an AtomicSwComponentType offers a PortPrototype typed by a ClientServerInterface to start/stop or request routine results of diagnostic routines.

[TPS_SWCT_02004] AtomicSwComponentType offers a PortPrototype typed by a ClientServerInterface to start/stop or request routine results of diagnostic routines (cid:100)

ServiceNeeds kind DiagnosticRoutineNeeds
RoleBasedPortAssignment valid roles:
    • RoutineServices [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01632] Suffix used for the resulting name of the PortInterface for the Routine Services (cid:100) The suffix used for the resulting name of the PortInterface for the Routine Services (RoutineServices_{RoutineName}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00690].

#@SECTION: 7.11.3.7.3.5 Dcm Service Use Case: IO control by Client Server Interface
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DiagnosticIoControlNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticIoControlNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, currentValue, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, didNumber, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, freezeCurrentStateSupported, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, resetToDefaultSupported, securityAccessLevel, shortName, shortNameFragment, shortTermAdjustmentSupported, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType offers a PortPrototype typed by a ClientServerInterface to adjust the IO signal via diagnostic services.

[TPS_SWCT_02005] AtomicSwComponentType offers PortPrototypes typed by ClientServerInterfaces to adjust the IO signal via diagnostic services (cid:100)

ServiceNeeds kind DiagnosticIoControlNeeds
RoleBasedPortAssignment valid roles:
    • DataServices [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01629] Suffix used for the resulting name of the PortInterface for the Data Services (cid:100) The suffix used for the resulting name of the PortInterface for the Data Services (DataServices_{Data}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00686].

#@SECTION: 7.11.3.7.3.6 Dcm Service Use Case: IO control by Sender Receiver Interface
#@CLASS: ApplicationSwComponentType
<!-- LLM_CONTEXT FOR CLASS ApplicationSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RoleBasedDataAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedDataAssignment: Attributes=[role, usedDataElement, usedParameterElement, usedPim, variationPoint] (包含继承及相关属性) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ServiceSwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DiagnosticIoControlNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticIoControlNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, currentValue, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, didNumber, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, freezeCurrentStateSupported, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, resetToDefaultSupported, securityAccessLevel, shortName, shortNameFragment, shortTermAdjustmentSupported, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

This use case represents an alternative to the use case described in chapter 7.11.3.7.3.5, i.e. for the same purpose it is also possible to utilize a SenderReceiverInterface.

The essential idea behind the existence of I/O PortPrototypes typed by SenderReceiverInterface is the possibility to have a quick access to the dataElements currently under control.

Especially cases where access to dataElements is required from different partitions (for example in multi core systems) can benefit from this approach.

Scenario: an AtomicSwComponentType offers an RPortPrototype typed by a SenderReceiverInterface (in particular: IOControlRequest) to adjust the I/O signal via diagnostic services and offers a PPortPrototype typed by a SenderReceiverInterface (in particular: IOControlResponse) to provide the IO "operation response".

In case of using IOControlRequest (which owns three dataElements) and IOControlResponse the whole PortPrototype is related to exactly one IO control and needs to be consistent.

Therefore, the usage of RoleBasedPortAssignment (instead of the RoleBasedDataAssignment, which would otherwise typically be used for a sender/receiver based scenario) is required for avoiding modeling overhead.

[TPS_SWCT_01654] AtomicSwComponentType offers PortPrototypes typed by SenderReceiverInterfaces to adjust the IO signal via diagnostic services (cid:100) 
1. ServiceNeeds kind DiagnosticIoControlNeeds 
2. RoleBasedPortAssignment valid roles:
    • IOControlRequest [1]
    • IOControlResponse [1]
3. RoleBasedDataAssignment
    N/A
4. RepresentedPortGroups 
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

The IOControl service requires in its diagnostic response the current value of the IO DID, which is identical to the current value represented by DiagnosticValueNeeds of the ReadDataByIdentifer response.

[TPS_SWCT_01655] Reference from DiagnosticIoControlNeeds to DiagnosticValueNeeds (cid:100) In the scenario described by [TPS_SWCT_01654], the DiagnosticIoControlNeeds shall reference the DiagnosticValueNeeds which relates to the access of the current value via diagnostic services (see [TPS_SWCT_02003]). (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01656] Suffix used for the resulting name of the PortInterface for IOControlRequest and IOControlResponse (cid:100) The suffix used for the resulting name of the PortInterface for the IOControlRequest_Data and IOControlResponse_Data shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

The service use case is visualized in Figure 7.46. The SwComponentPrototype contains two SwcServiceDependencys, one for the I/O Control, and one for the access of the dataElement with the shortName "IOx" by the Dcm.


<-------------- multimodal context 
This architecture depicts an AUTOSAR service use case where an application SW-Component requests and receives IO control commands and diagnostic data from a DCM service SW-Component via well-defined SenderReceiverInterfaces. It shows how service dependencies and data needs inside an ApplicationSwComponentType map onto ports and connect through AssemblySwConnectors to a DcmServiceSwComponentType, enabling two-way IO control and continuous diagnostic value exchange.

• Component hierarchy  
  – SwComponentPrototype “IOControlRequest_IOx” (ApplicationSwComponentType) contains two SwcServiceDependency instances (“IOx” and “Data_IOx”) linked to DiagnosticControlNeeds and DiagnosticValueNeeds.  
  – A separate SwComponentPrototype (DcmServiceSwComponentType) provides the corresponding interfaces.  

• Ports & interfaces  
  – RoleBasedPortAssignment: PPort “IOControlRequest” and RPort “IOControlResponse” use SenderReceiverInterface “IOControlRequest_IOx” and “IOControlResponse_IOx.”  
  – RoleBasedDataAssignment: data port “signalBasedDiagnostics” uses SenderReceiverInterface “DataXY_IO” (elements “IOx,” “IOy”).  
  – AssemblySwConnectors link each matching port prototype.  

• Data flow  
  – Application SW-C sends IOControlRequest to DCM SW-C, which processes and returns IOControlResponse.  
  – Diagnostic values (currentValue) flow from DCM back into the application via DataServices_Data_IOx.  

• Key AUTOSAR concepts  
  – SwComponentPrototype, ApplicationSwComponentType, DcmServiceSwComponentType  
  – RoleBasedPortAssignment, RoleBasedDataAssignment  
  – SenderReceiverInterface, AssemblySwConnector  

• Scenario  
  – Enables an application to issue IO control commands to a diagnostic manager (DCM) and receive both control confirmations and real-time diagnostic data. ---------------------->
Figure 7.46: Visualization of the service use case

Please note that, in this example, the SenderReceiverInterface used on the PPortPrototype of the ApplicationSwComponentType has several dataElements (where the dataElement with the shortName "IOx" is one of them). This is a perfectly valid configuration.

On the other hand, the SenderReceiverInterface used on the RPortPrototype of the ServiceSwComponentType representing the Dcm can only have one dataElement. This single dataElement shall (as far as the example is concerned) be given the shortName "IOx".

Note the reference from the DiagnosticIoControlNeeds to the DiagnosticValueNeeds. this reference explicitly expresses that access to a DID is combined with the usage of I/O control.

[TPS_SWCT_01657] NamingRule for RPortPrototype referenced by a RoleBasedPortAssignment with attribute role set to "IOControlRequest" (cid:100) The shortName of a RPortPrototype referenced by a RoleBasedPortAssignment with attribute role set to "IOControlRequest" shall be created by concatenating the prefix "IOControlRequest" and the SwcServiceDependency.shortName, separated by a single underscore character (i.e. "_"). (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01658] NamingRule for PPortPrototype referenced by a RoleBasedPortAssignment with attribute role set to "IOControlResponse" (cid:100) The shortName of a PPortPrototype referenced by a RoleBasedPortAssignment with attribute role set to "IOControlResponse" shall be created by concatenating the prefix "IOControlResponse" and the SwcServiceDependency.shortName, separated by a single underscore character (i.e. "_"). (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_01308] and [SWS_Dcm_01309].

#@SECTION: 7.11.3.7.3.7 Dcm Service Use Case: Access to protocol, session and security information
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticCommunicationManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticCommunicationManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, serviceRequestCallbackType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType offers a server port to get protocol, session and security information or to request a Reset to Default Session.

[TPS_SWCT_02013] AtomicSwComponentType offers a server port to get protocol, session and security information or to request a Reset to Default Session (cid:100)

1. ServiceNeeds kind DiagnosticCommunicationManagerNeeds
2. RoleBasedPortAssignment valid roles:
    • DCMServices [1]
3. RoleBasedDataAssignment
    N/A
4. RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00698]

#@SECTION: 7.11.3.7.3.8 Dcm Service Use Case: Verify the access to security level
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DiagnosticsCommunicationSecurityNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticsCommunicationSecurityNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType provides a server port to verify the access to security level via diagnostic services.

[TPS_SWCT_02015] AtomicSwComponentType veriﬁes the access to security level via diagnostic services (cid:100)

ServiceNeeds kind DiagnosticsCommunicationSecurityNeeds
RoleBasedPortAssignment valid roles:
    • SecurityAccess [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01627] Sufﬁx used for the resulting name of the PortInterface for the Security Access (cid:100) The sufﬁx used for the resulting name of the PortInterface for the Security Access (SecurityAccess_{SecurityLevel}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00685]

#@SECTION: 7.11.3.7.3.9 Dcm Service Use Case: multiple testers access one ECU
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticCommunicationManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticCommunicationManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, serviceRequestCallbackType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType provides a server port to get information on the status of the protocol communication. Further on the AtomicSwComponentType may disallow a protocol.

[TPS_SWCT_02016] AtomicSwComponentType requires information on the status of the protocol communication and may disallow a protocol (cid:100)

ServiceNeeds kind DiagnosticCommunicationManagerNeeds
RoleBasedPortAssignment valid roles:
    • CallbackDCMRequestServices [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00692]

#@SECTION: 7.11.3.7.3.10 Dcm Service Use Case: Service Request Notiﬁcation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: DiagnosticCommunicationManagerNeeds
<!-- LLM_CONTEXT FOR CLASS DiagnosticCommunicationManagerNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, serviceRequestCallbackType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType provides a server port to get notified about a Service Request via diagnostic services. This indicates the successful reception of a new request to application.

Within this Service Request Notification this function application can examine the permission of the diagnostic service / environment.

Please note that the Service Request Notification can be used in two characteristics ([TPS_SWCT_01577] applies) or as a supplier ([TPS_SWCT_01578] applies).

[TPS_SWCT_01577] AtomicSwComponentType requires the notification about a Service Request via diagnostic services with manufacturer characteristics (cid:100) 
The attribute DiagnosticCommunicationManagerNeeds.serviceRequest The CallbackType shall be set to the value requestCallbackTypeManufacturer. 
1. ServiceNeeds kind DiagnosticCommunicationManagerNeeds 
2. RoleBasedPortAssignment valid roles: 
    • ServiceRequestNotification [1] 
3. RoleBasedDataAssignment 
4. RepresentedPortGroups 
(cid:99)(RS_SWCT_03190)

[TPS_SWCT_01578] AtomicSwComponentType requires the notification about a Service Request via diagnostic services with supplier characteristics (cid:100) 
The attribute DiagnosticCommunicationManagerNeeds.serviceRequest The CallbackType shall be set to the value requestCallbackTypeSupplier. 
ServiceNeeds kind DiagnosticCommunicationManagerNeeds 
RoleBasedPortAssignment valid roles: 
    • ServiceRequestNotification [1] 
RoleBasedDataAssignment 
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00694]

#@SECTION: 7.11.3.7.4 OBD related Needs
#@ENUM: ObdRatioConnectionKindEnum
<!-- LLM_CONTEXT FOR ENUM ObdRatioConnectionKindEnum: Literals=[] (元数据中未找到字面量) -->
#@CLASS: ObdControlServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdControlServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, testId, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: ObdPidServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdPidServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, parameterId, securityAccessLevel, shortName, shortNameFragment, standard, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: ObdInfoServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdInfoServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, infoType, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: ObdMonitorServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdMonitorServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, onBoardMonitorId, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, testId, unitAndScalingId, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: ObdRatioServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdRatioServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, connectionType, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, iumprGroup, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, rateBasedMonitoredEvent, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, usedFid, usedSecondaryFid, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

The ObdRatioServiceNeeds describes further properties of the implementation of the Rate Based Monitoring (e.g. connectionType) as well as the logical dependencies relevant for the ECU configuration (e.g. iumprGroup).

Table 7.94: ObdRatioServiceNeeds

The possible values for the attribute ObdRatioServiceNeeds.iumprGroup are:
• CAT1
• CAT2
• OXS1
• OXS2
• EGR
• SAIR
• EVAP
• SECOXS1
• SECOXS2
• NMHCCAT
• NOXCAT
• NOXADSORB
• PMFILTER
• EGSENSOR
• BOOSTPRS
• NOGROUP
• NONE

Table 7.95: ObdRatioConnectionKindEnum

In addition, ObdPidServiceNeeds, ObdInfoServiceNeeds, ObdMonitorServiceNeeds and ObdControlServiceNeeds are required in order to specify the specific needs for OBD diagnostic service calls. Note that ObdPidServiceNeeds is used for the Diagnostic Event Manager as well.

Table 7.96: ObdControlServiceNeeds

Table 7.97: ObdPidServiceNeeds

Table 7.98: ObdInfoServiceNeeds

Table 7.99: ObdMonitorServiceNeeds

#@SECTION: 7.11.3.7.4.1 Dem Service Use Case: In-Use-Monitor Performance Ratio calculation
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ObdRatioServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdRatioServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, connectionType, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, iumprGroup, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, rateBasedMonitoredEvent, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, usedFid, usedSecondaryFid, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

Scenario: an AtomicSwComponentType implements a OBD system monitor with In Use-Monitor Performance Ratio (IUMPR) and offers client ports to provide the capacity to define the number of times a fault could have been found.

[TPS_SWCT_02007] AtomicSwComponentType implements a OBD system monitor with In-Use-Monitor Performance Ratio (cid:100)
ServiceNeeds kind ObdRatioServiceNeeds
RoleBasedPortAssignment valid roles:
    • IUMPRNumerator [0..1]
    • IUMPRDenominator [0..1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dem_00610] and [SWS_Dem_00611].

[constr_2053] Consistency between role IUMPRNumerator and ObdRatioServiceNeeds.connectionType (cid:100) If a SwcServiceDependency with a ObdRatioServiceNeeds is defined and the attribute connectionType of the contained ObdRatioServiceNeeds is set to ObdRatioConnectionKindEnum.apiUse a RoleBasedPortAssignment with the role value IUMPRNumerator shall be defined.
If the attribute connectionType of the contained ObdRatioServiceNeeds is set to ObdRatioConnectionKindEnum.observer the role value IUMPRNumerator is not applicable. 
(cid:99)()

#@SECTION: 7.11.3.7.4.2 Dcm Service Use Case: read parameter identiﬁer via diagnostic services by Client Server Interface
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: ObdPidServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdPidServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, parameterId, securityAccessLevel, shortName, shortNameFragment, standard, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->

Scenario: an AtomicSwComponentType offers a server port to read/write current value via OBD services.

[TPS_SWCT_02008] AtomicSwComponentType offers a server port to read/write current value via OBD services (cid:100)

1.ServiceNeeds kind ObdPidServiceNeeds
2.RoleBasedPortAssignment
    The following roles are applicable:
        • DataServices [1]
3.RoleBasedDataAssignment
    N/A
4.RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01630] Suffix used for the resulting name of the PortInterface for the Data Services (cid:100) The suffix used for the resulting name of the PortInterface for the Data Services (DataServices_{Data}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00686].

#@SECTION: 7.11.3.7.4.3 Dcm Service Use Case: read parameter identiﬁer via diagnostic services by Sender Receiver Interface
#@CLASS: AbstractProvidedPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractProvidedPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PPortPrototype, PRPortPrototype] (直接子类) -->
#@CLASS: AbstractRequiredPortPrototype
<!-- LLM_CONTEXT FOR CLASS AbstractRequiredPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[PortPrototype] (直接父类); Childs=[PRPortPrototype, RPortPrototype] (直接子类) -->
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ObdPidServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdPidServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, parameterId, securityAccessLevel, shortName, shortNameFragment, standard, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType offers sender receiver ports to read/write current values via OBD services.

[TPS_SWCT_02009] AtomicSwComponentType offers sender receiver ports to read/write current values via OBD services (cid:100)

1.ServiceNeeds kind ObdPidServiceNeeds
2.RoleBasedPortAssignment
    N/A
3.RoleBasedDataAssignment
    The following roles are applicable:
        • signalBasedDiagnostics [1..2]
4.RepresentedPortGroups
    N/A
To read the signal the AtomicSwComponentType shall offer an AbstractProvidedPortPrototype, to write the signal the AtomicSwComponentType shall offer an AbstractRequiredPortPrototype. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00687].

#@SECTION: 7.11.3.7.4.4 Dcm Service Use Case: Request vehicle information
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: ObdInfoServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdInfoServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLength, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, infoType, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType offers a server port to read vehicle information values via OBD services.

[TPS_SWCT_02010] AtomicSwComponentType offers a server port to read vehicle information values via OBD services (cid:100)

ServiceNeeds kind ObdInfoServiceNeeds
RoleBasedPortAssignment valid roles:
    • InfotypeServices [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01631] Suffix used for the resulting name of the PortInterface for the Infotype Services (cid:100) The suffix used for the resulting name of the PortInterface for the Infotype Services (InfotypeServices_{VehInfoData}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00688].

#@SECTION: 7.11.3.7.4.5 Dem Service Use Case: Read DTR data from SW-C for OBD Service $06
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ObdMonitorServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdMonitorServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, onBoardMonitorId, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, testId, unitAndScalingId, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: an AtomicSwComponentType offers a server ports to read DTR value via OBD services.

[TPS_SWCT_02011] AtomicSwComponentType offers a server port to read DTR value via OBD services (cid:100) 
ServiceNeeds kind ObdMonitorServiceNeeds 
RoleBasedPortAssignment valid roles: 
• DTRCentralReport [1] 
RoleBasedDataAssignment 
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190) 

For more information please refer to [SWS_Dcm_00689].

#@SECTION: 7.11.3.7.4.6 Dcm Service Use Case: request control of on-board system, test or component
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: ObdControlServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ObdControlServiceNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, testId, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

Scenario: an AtomicSwComponentType offers a server port for request control of on-board system, test or component via OBD services.

[TPS_SWCT_02012] AtomicSwComponentType offers a server port for request control of on-board system, test or component via OBD services (cid:100)

ServiceNeeds kind ObdControlServiceNeeds
RoleBasedPortAssignment
    The following roles are applicable:
        • RequestControlServices [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_00170, RS_SWCT_03190)

[TPS_SWCT_01633] Suffix used for the resulting name of the PortInterface for the Request Control Services (cid:100) The suffix used for the resulting name of the PortInterface for the Request Control Services (RequestControlServices_{Tid}) shall be taken from the shortName of the applicable SwcServiceDependency. (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00691].

#@SECTION: 7.11.3.7.4.7 Dcm Service Use Case: Response On Event via diagnostic services
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: ServiceNeeds
<!-- LLM_CONTEXT FOR CLASS ServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[Identifiable] (直接父类); Childs=[BswMgrNeeds, ComMgrUserNeeds, CryptoServiceNeeds, DiagnosticCapabilityElement, DltUserNeeds, DoIpServiceNeeds, EcuStateMgrUserNeeds, FunctionInhibitionNeeds, NvBlockNeeds, SupervisedEntityNeeds, SyncTimeBaseMgrUserNeeds] (直接子类) -->

Please note that for this specific use case the application of a concrete ServiceNeeds is not yet clarified.

Scenario: an AtomicSwComponentType offers client server ports to support Response On Event (ROE) via diagnostic services.

[TPS_SWCT_02014] AtomicSwComponentType supports Response On Event (ROE) via diagnostic services (cid:100)

RoleBasedPortAssignment valid roles:
    • Dcm_Roe [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
The role ROEServices is applicable for a server port of the AtomicSwComponentType and the role Dcm_Roe is applicable for a client port of the AtomicSwComponentTypes (cid:99)(RS_SWCT_00170, RS_SWCT_03190)

For more information please refer to [SWS_Dcm_00695] and [SWS_Dcm_00699].

#@SECTION: 7.11.3.7.5 Diagnostics over IP
#@CLASS: DoIpActivationLineNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpActivationLineNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpGidNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpGidNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpGidSynchronizationNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpGidSynchronizationNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpPowerModeStatusNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpPowerModeStatusNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpRoutingActivationAuthenticationNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpRoutingActivationAuthenticationNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLengthRequest, dataLengthResponse, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, routingActivationType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpRoutingActivationConfirmationNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpRoutingActivationConfirmationNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLengthRequest, dataLengthResponse, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, routingActivationType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpServiceNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpServiceNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类); Childs=[DoIpActivationLineNeeds, DoIpGidNeeds, DoIpGidSynchronizationNeeds, DoIpPowerModeStatusNeeds, DoIpRoutingActivationAuthenticationNeeds, DoIpRoutingActivationConfirmationNeeds] (直接子类) -->


This chapter describes the usage of specific meta-classes to support the specification of diagnostics over IP. For more details, please refer to ISO 13400 [39].

Figure 7.47: Subclasses of ServiceNeeds for implementing diagnostics over IP

Table 7.100: DoIpServiceNeeds

Table 7.101: DoIpGidNeeds

Table 7.102: DoIpGidSynchronizationNeeds

Table 7.103: DoIpPowerModeStatusNeeds

Table 7.104: DoIpRoutingActivationAuthenticationNeeds

Table 7.105: DoIpRoutingActivationConfirmationNeeds

Table 7.106: DoIpActivationLineNeeds

#@SECTION: 7.11.3.7.5.1 DoIP Service Use Case: GID synchronization can be necessary if the ECU is DoIP Gid synchronization master
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: DoIpRoutingActivationAuthenticationNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpRoutingActivationAuthenticationNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLengthRequest, dataLengthResponse, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, routingActivationType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
Scenario: on the event of connecting a tester to an ECU a GID synchronization can be necessary if the ECU is DoIP Gid synchronization master. In this case, it is necessary to define a DoIpGidSynchronizationNeeds.

[TPS_SWCT_01537] GID synchronization can be necessary if the ECU is DoIP Gid synchronization master (cid:100)

ServiceNeeds kind DoIpGidSynchronizationNeeds
RoleBasedPortAssignment valid roles:
    • CallbackTriggerGIDSynchronization [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_03310, RS_SWCT_03190)

#@SECTION: 7.11.3.7.5.2 DoIP Service Use Case: Vehicle information is broadcast or can be requested by the tester
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: DoIpGidNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpGidNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->

Scenario: vehicle information is broadcast or can be requested by the tester. In this case, it is necessary to define a DoIpGidNeeds.

[TPS_SWCT_01538] Vehicle information is broadcast or can be requested by the tester (cid:100) 
ServiceNeeds kind DoIpGidNeeds
RoleBasedPortAssignment valid roles:
    • CallbackGetGID [1]
RoleBasedDataAssignment
    N/A 
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_03310, RS_SWCT_03190)

#@SECTION: 7.11.3.7.5.3 DoIP Service Use Case: Tester could also request the power status with respect to diagnostics
#@CLASS: DoIpPowerModeStatusNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpPowerModeStatusNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

Scenario: before starting the diagnostics processing for the DoIP entity or sub networks connected via DoIP, the tester could also request the power status with respect to diagnostics. To support this option it will be necessary to define a DoIpPowerModeStatusNeeds.

[TPS_SWCT_01539] Tester can also request before starting diagnostic processing for the DoIP entity or sub-networks connected via DoIP the power status with respect to diagnostics (cid:100)

ServiceNeeds kind DoIpPowerModeStatusNeeds
RoleBasedPortAssignment valid roles:
    • CallbackGetPowerMode [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_03310, RS_SWCT_03190)

#@SECTION: 7.11.3.7.5.4 DoIP Service Use Case: Routing activation mechanism is used which can lead to additional impact regarding authentication or confirmation
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: DoIpRoutingActivationAuthenticationNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpRoutingActivationAuthenticationNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLengthRequest, dataLengthResponse, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, routingActivationType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->
#@CLASS: DoIpRoutingActivationConfirmationNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpRoutingActivationConfirmationNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, dataLengthRequest, dataLengthResponse, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, routingActivationType, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->

Scenario: to enable diagnostics of the tester to a different target address, the routing activation mechanism is used which can lead to additional impact regarding authentication or confirmation. Here, the definition of DoIpRoutingActivationAuthenticationNeeds and/or DoIpRoutingActivationConfirmationNeeds would be applicable.

[TPS_SWCT_01544] prefix used for the actual name of the used PortInterface for the routing activation (cid:100) The prefix used for the actual name of the used PortInterface for the routing activation shall be taken from the shortName of the enclosing SwcServiceDependency. (cid:99)(RS_SWCT_03310, RS_SWCT_03190)

[TPS_SWCT_01540] Routing activation mechanism is used which can lead to additional impact regarding authentication or confirmation (cid:100)

1. ServiceNeeds kind
    • DoIpRoutingActivationAuthenticationNeeds [0..1]
    • DoIpRoutingActivationConfirmationNeeds [0..1]

2. RoleBasedPortAssignment valid roles:
    • RoutingActivation [1]

3. RoleBasedDataAssignment
    N/A
4. RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_03190)

#@SECTION: 7.11.3.7.5.5 DoIP Service Use Case: a DoIP entity needs to be informed when an external tester is attached or activated.
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: ServiceSwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: DoIpActivationLineNeeds
<!-- LLM_CONTEXT FOR CLASS DoIpActivationLineNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DoIpServiceNeeds] (直接父类) -->

Scenario: to enable diagnostics by connecting a tester to an ECU it is necessary that the application software becomes aware of the tester’s presence.

For this purpose, the applicable ServiceSwComponentType is supposed to provide a PPortPrototype typed by the ModeSwitchInterface named DoIPActivationLineStatus towards the application.

To trigger the existence of the PPortPrototype, DoIpActivationLineNeeds shall be defined.

[TPS_SWCT_01546] Notification when an external tester is attached or activated (cid:100) ServiceNeeds kind DoIpActivationLineNeeds 
RoleBasedPortAssignment valid roles:
    • DoIPActivationLineStatus [1]
RoleBasedDataAssignment
    N/A 
RepresentedPortGroups 
    N/A
(cid:99)(RS_SWCT_03310, RS_SWCT_03190)

#@SECTION: 7.11.3.7.5.6 Service Use Case: Set and reset Warning Indicator Request bit
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: ServiceSwComponentType
<!-- LLM_CONTEXT FOR CLASS ServiceSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[AtomicSwComponentType] (直接父类) -->
#@CLASS: WarningIndicatorRequestedBitNeeds
<!-- LLM_CONTEXT FOR CLASS WarningIndicatorRequestedBitNeeds: Attributes=[adminData, annotation, audience, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagRequirement, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, securityAccessLevel, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[DiagnosticCapabilityElement] (直接父类) -->

Scenario: In some cases (e.g. controlling a failsafe reaction in application) the “Warning Indicator Request”-bit of a corresponding event in Dem shall be set/reset by a special “failsafe software-component”.

The failsafe software-component has to ensure a proper status of the “Warning Indicator Request”-bit (e.g. regarding to ISO14229-1 or manufacture specific requirements).

Therefore the failsafe SW-C can use existing Dem mechanism to get the information about status changes of events in Dem (e.g. Callback EventStatusChanged).

For this purpose, the applicable ServiceSwComponentType is supposed to provide a PPortPrototype typed by the ClientServerInterface named EventStatus towards the application.

To trigger the existence of the PPortPrototype, WarningIndicatorRequestedBitNeeds shall be defined.

[TPS_SWCT_01547] Ability to set and reset the Warning Indicator Request bit (cid:100)

ServiceNeeds kind WarningIndicatorRequestedBitNeeds
RoleBasedPortAssignment valid roles:
    • EventStatus [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A
(cid:99)(RS_SWCT_03190)

Table 7.107: WarningIndicatorRequestedBitNeeds

#@SECTION: 7.11.3.8 Diagnostic Log and Trace Dependency
#@CLASS: DltUserNeeds
<!-- LLM_CONTEXT FOR CLASS DltUserNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->

The meta-class DltUserNeeds is used together with the SwcServiceDependency to define requirements in order to configure the Diagnostic Log and Trace module (for the terms related to the AUTOSAR Specification of Module DLT see [40]).

Table 7.108: DltUserNeeds

Please note that for the described use case of the Dlt Service the following rule applies: For every used ClientServerInterface it is necessary to create a RoleBased PortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServerInterface. The possible role attribute values and the multiplicity of the related PortPrototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment.

#@SECTION: 7.11.3.8.1 Dlt use Case: Application software component accesses the Synchronized Time-Base Manager
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: AtomicSwComponentType sends log messages. In this case the following setup applies:

[TPS_SWCT_02506] Setup for Dlt use Case: Application software component accesses the Synchronized Time-Base Manager (cid:100)
RoleBasedPortAssignment valid roles:
    • DLTService [1]
    • LogTraceSessionControl [1]
    • VerboseModeControl [0..1]
    • InjectionCallback [0..1]

RoleBasedDataAssignment 
    N/A
RepresentedPortGroups (cid:99)()
    N/A

For more information please refer to [SWS_Dlt_00495], [SWS_Dlt_00496], [SWS_Dlt_00497], and [SWS_Dlt_00498].

In this case the software-component has to provide one Client Port (DLTService) in order to register the context and to send log or trace messages. Further on the component has to provide a Server Port (LogTraceSessionControl) to receive the current log level and trace status. Server Ports for VerboseModeControl and InjectionCallback are optional.

#@SECTION: 7.11.3.9 Synchronized Time-Base Manager Dependency
#@CLASS: SwcServiceDependency
<!-- LLM_CONTEXT FOR CLASS SwcServiceDependency: Attributes=[adminData, annotation, assignedData, assignedDataType, assignedPort, category, desc, introduction, longName, representedPortGroup, serviceNeeds, shortName, shortNameFragment, symbolicNameProps, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable, ServiceDependency] (直接父类) -->
#@CLASS: SyncTimeBaseMgrUserNeeds
<!-- LLM_CONTEXT FOR CLASS SyncTimeBaseMgrUserNeeds: Attributes=[adminData, annotation, bswMgrNeeds, category, comMgrUserNeeds, cryptoServiceNeeds, desc, diagnosticCommunicationManagerNeeds, diagnosticEnableConditionNeeds, diagnosticEventInfoNeeds, diagnosticEventManagerNeeds, diagnosticEventNeeds, diagnosticIoControlNeeds, diagnosticOperationCycleNeeds, diagnosticRoutineNeeds, diagnosticStorageConditionNeeds, diagnosticValueNeeds, diagnosticsCommunicationSecurityNeeds, dltUserNeeds, doIpActivationLineNeeds, doIpGidNeeds, doIpGidSynchronizationNeeds, doIpPowerModeStatusNeeds, doIpRoutingActivationAuthenticationNeeds, doIpRoutingActivationConfirmationNeeds, dtcStatusChangeNotificationNeeds, ecuStateMgrUserNeeds, functionInhibitionNeeds, introduction, longName, nvBlockNeeds, obdControlServiceNeeds, obdInfoServiceNeeds, obdMonitorServiceNeeds, obdPidServiceNeeds, obdRatioServiceNeeds, shortName, shortNameFragment, supervisedEntityNeeds, syncTimeBaseMgrUserNeeds, warningIndicatorRequestedBitNeeds] (包含继承及相关属性); Generalization=[ServiceNeeds] (直接父类) -->

The meta-class SyncTimeBaseMgrUserNeeds is used together with the SwcServiceDependency to define requirements in order to configure the Synchronized Time-Base Manager module (for the terms related to the AUTOSAR Specification of Module StbM see [41]).

Table 7.109: SyncTimeBaseMgrUserNeeds

Please note that for the described use cases of the StbM Service following rule applies: For every used ClientServerInterface it is necessary to create a RoleBasedPortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServerInterface. The possible role attribute values and the multiplicity of the related PortPrototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment.

#@SECTION: 7.11.3.9.1 StbM use Case: Application software component accesses the Synchronized Time-Base Manager
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->

Scenario: an AtomicSwComponentType autonomously calls the Synchronized Time Base Manager, getting knowledge about the definition of time and the state of the module. In this case the following setup applies:
RoleBasedPortAssignment valid roles:
    • StbM_TimeBaseValue [1]
RoleBasedDataAssignment
    N/A
RepresentedPortGroups
    N/A

In this (StbM_TimeBaseValue) to case the software component has to provide one Client Port
• access the current status of the synchronized time-base
• access the current definition of time represented by the notion of ticks
• access the current definition of tickDuration

#@SECTION: 7.11.3.9.2 StbM use Case: Synchronized Time-Base Manager notiﬁes application software component
#@CLASS: AtomicSwComponentType
<!-- LLM_CONTEXT FOR CLASS AtomicSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, internalBehavior, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, symbolProps, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类); Childs=[ApplicationSwComponentType, ComplexDeviceDriverSwComponentType, EcuAbstractionSwComponentType, NvBlockSwComponentType, SensorActuatorSwComponentType, ServiceProxySwComponentType, ServiceSwComponentType] (直接子类) -->
#@CLASS: RoleBasedPortAssignment
<!-- LLM_CONTEXT FOR CLASS RoleBasedPortAssignment: Attributes=[portPrototype, role, variationPoint] (包含继承及相关属性) -->

Scenario: an AtomicSwComponentType shall be informed by the Synchronized Time-Base Manager about state changes and/or error occurrences (e.g. the synchronisation state of a time-base has changed). In this case the following setup applies:
RoleBasedPortAssignment valid roles:
    • StbM_TimeBase_TriggerCustomer [0..1]
    • StbM_TimeBase_StateNotification [0..1]
RoleBasedDataAssignment
    N/A 
RepresentedPortGroups
    N/A
In this case the software-component has to provide one Receiver Port (StbM_TimeBase_TriggerCustomer) to receive the current value of the synchronized time-base and / or one Receiver Port (StbM_TimeBase_StateNotification) to receive the current state of the synchronized time-base.

Please note that at least one of the two possible RoleBasedPortAssignments shall exist for this use case.

#@SECTION: 7.12 Variation Point Proxy
#@CLASS: VariationPointProxy
<!-- LLM_CONTEXT FOR CLASS VariationPointProxy: Attributes=[adminData, annotation, category, conditionAccess, desc, implementationDataType, introduction, longName, postBuildValueAccess, postBuildVariantCondition, shortName, shortNameFragment, valueAccess] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: VariationPoint
<!-- LLM_CONTEXT FOR CLASS VariationPoint: Attributes=[blueprintCondition, desc, formalBlueprintCondition, postBuildVariantCondition, sdg, shortLabel, swSyscond] (包含继承及相关属性) -->
#@CLASS: SwSystemconstantValueSet
<!-- LLM_CONTEXT FOR CLASS SwSystemconstantValueSet: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swSystemconstantValue, variationPoint] (包含继承及相关属性); Generalization=[ARElement] (直接父类) -->
#@CLASS: PostBuildVariantCriterionValueSet
<!-- LLM_CONTEXT FOR CLASS PostBuildVariantCriterionValueSet: Attributes=[adminData, annotation, category, desc, introduction, longName, postBuildVariantCriterionValue, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[ARElement] (直接父类) -->
#@CLASS: SwSystemconstDependentFormula
<!-- LLM_CONTEXT FOR CLASS SwSystemconstDependentFormula: Attributes=[sysc, syscString] (包含继承及相关属性); Generalization=[FormulaExpression] (直接父类); Childs=[AttributeValueVariationPoint, BlueprintFormula, ConditionByFormula, FMFormulaByFeaturesAndSwSystemconsts] (直接子类) -->

[TPS_SWCT_01370] VariationPointProxy (cid:100) Variability inside a software component may exist in two different levels of abstraction:

• A structural variation point affects the existence or non-existence of structural model elements. A structural variation point is modeled by means of the meta class VariationPoint.

• A functional variation point affects solely the functionality in the implementation (read: source code) of the software-component. A functional variation point is modeled by means of the meta-class VariationPointProxy.

In other words, this enables the developer of a software-component to implement variability that is limited to the software-component's functionality. This kind of variability is resolved
• by a code generator (bindingTime = codeGenerationTime), 
• by the preprocessor (bindingTime = preCompileTime), 
• or as a post-build value evaluation (in this case postBuildValueAccess and postBuildVariantCondition shall exist). 
(cid:99)(RS_SWCT_03100)

Please note that in the first two cases of the second bullet list in [TPS_SWCT_01370] the evaluation of conditionAccess shall replace the formula by the result.

The name VariationPointProxy was motivated by the fact that it represents a model element that is not directly related to the structure but to the code and from this point of view acts as a proxy to the functional variation existing in the code.

The consequence of the two levels of abstraction is that (from a model processing point of view) it would be possible to bind all structural variation points entirely while keeping some or all of the functional variation points unbound. This is an explanation for the existence of [TPS_SWCT_01371].

[TPS_SWCT_01371] VariationPointProxy vs. VariationPoint (cid:100) The difference between a VariationPoint and a VariationPointProxy is that if during the process of binding the formula evaluates to 0 the VariationPointProxy remains in the model while the VariationPoint as well as its owner is removed from the model. (cid:99)(RS_SWCT_03100)

Nevertheless, the binding of the variability is described by the means of SwSystem constantValueSets and PostBuildVariantCriterionValueSets.

[TPS_SWCT_01448] Pre-defined values for the category of VariationPointProxy (cid:100) AUTOSAR pre-defines two possible values for the category of VariationPointProxy. The meaning of the values, however, depends on the particular modeling of individual VariationPointProxys, see [TPS_SWCT_01370].

VALUE 
    In the "pre-build" case this means that valueAccess shall yield an integer literal. In the "post-build" case, on the other hand, this means that postBuildValueAccess shall yield an integer value conform with the implementation DataType. In this context, [constr_1388] applies.

CONDITION 
    In this case it is possible (though not mandatory) to define a VariationPointProxy that actually works in a combination of the "pre-build" and "post-build" scenario. In other words, in the "pre-build" case conditionAccess shall yield a boolean value and in the "post-build" case postBuildVariantCondition shall also yield a boolean value. An and operator shall be applied to all boolean values returned by conditionAccess and the collection of postBuildVariantCondition in order to yield the actual result of the condition. [TPS_GST_00259] and [SWS_Rte_08069] apply. For the postBuildVariantCondition an implicit reference to the Platform Data Type boolean shall be assumed. In contrast to the value VALUE it is possible to define a VariationPointProxy that uses both conditionAccess and postBuildVariantCondition.
(cid:99)(RS_SWCT_03100)

[constr_1388] VariationPointProxy of category VALUE shall not mix "pre-build" and "post-build" use-cases (cid:100) If the value of category of the VariationPointProxy is set to VALUE then there can only be one value yield from the evaluation of a VariationPointProxy. In other words, a VariationPointProxy of category VALUE shall not mix the "pre-build" and "post-build" use-cases. (cid:99)()

[constr_1389] Restriction regarding the value of category of VariationPointProxy.implementationDataType (cid:100) VariationPointProxy.implementationDataType shall not be of category STRUCTURE, ARRAY, UNION, FUNCTION_REFERENCE, and DATA_REFERENCE. The VariationPointProxy.implementationDataType shall be of category VALUE or TYPE_REFERENCE that, after all references are resolved, yields an ImplementationDataType of category VALUE. (cid:99)()

[TPS_SWCT_01372] bindingTime = preCompileTime (cid:100) In case of bindingTime = preCompileTime the RTE provides macro definitions that can be used for preprocessor directives to implement preCompileTime variability in C/C++ code. (cid:99)(RS_SWCT_03100)

[TPS_SWCT_01373] RTE generator shall evaluate the SwSystemconstDependentFormula (cid:100) It is in the scope of the RTE generator to evaluate the SwSystemconstDependentFormula which has a higher precedence than the standard C Preprocessor and to provide the resulting values to the software-component's implementation. (cid:99)(RS_SWCT_03100)

For further details (beyond the statements made in [TPS_SWCT_01372] and [TPS_SWCT_01373]) about the impact of the existence of a VariationPointProxy on the RTE please refer to [2].

Figure 7.48: VariationPointProxy

Table 7.110: VariationPointProxy

Please note that the usage of attributes of meta-class VariationPointProxy is not arbitrarily possible but subject to conditions. In particular, there are certain use-cases that dictate how and with which multiplicity attributes of VariationPointProxy shall be used. In particular, the applicable use-cases are defined by a combination of the binding time, i.e. PreBuild (all pre-build binding times are summarized as PreBuild) vs. PostBuild, and the value of VariationPointProxy.category (the details are explained in table 7.111 resp. [constr_1253]).

[constr_1253] Supported usage of VariationPointProxy (cid:100) The allowed multiplicities for attributes of VariationPointProxy depending on the applicable binding time and the value of VariationPointProxy.category are documented in Table 7.111. For clarification, the multiplicities of attributes of meta-class VariationPointProxy that are not explicitly mentioned in a given row of table 7.111 shall be interpreted as [0]. (cid:99)()

Table 7.111: Supported usage of VariationPointProxy