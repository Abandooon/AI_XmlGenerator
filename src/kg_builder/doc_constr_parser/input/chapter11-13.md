#@SECTION: 11 Services
#@SECTION: 11.1 Overview: Generation of Service-related Model Elements
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: PortDefinedArgumentValues
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: RootSwCompositionPrototype
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: ServiceSwComponentType
#@CLASS: SwComponentPrototype
#@CLASS: SwComponentType
#@CLASS: SwcBswMapping
#@CLASS: SwcImplementation
#@CLASS: SwcInternalBehavior
#@CLASS: ServiceNeeds
#@CLASS: AssemblySwConnector
#@CLASS: DelegationSwConnector
#@CLASS: System
#@CLASS: EcuInstance
#@CLASS: InternalBehavior

This chapter covers the description and handling of AUTOSAR Service configuration.

[TPS_SWCT_01397] Hybrid concept between Basic Software Modules and a SwComponentType (cid:100) AUTOSAR Services can be seen as a hybrid concept between Basic Software Modules and a SwComponentType. AUTOSAR Services actually provide access to low-level and ECU-wide "standard functionalities" commonly referred to as "service".

AtomicSwComponentTypes that require AUTOSAR Services use Standardized AUTOSAR Interfaces to communicate with these. The connection of PortPrototypes of the ServiceSwComponentTypes and PortPrototypes of the AtomicSwComponentTypes implement several communication patterns. (cid:99)()

Table 11.1: ServiceConnectorPattern


<-------------- multimodal context 
| I  | II  | III             | IV                                                                                      |
|----|-----|-----------------|-----------------------------------------------------------------------------------------|
| A  | 1:n | PPort : RPort   | distribution of data or modes to n SW-Cs, e.g. used for ECU mode                         |
| A* | 1:n | RPort : PPort   | currently not used, not supported for client-server communication                       |
| B  | 1:1 | PPort : RPort   | SW-C acts as Server, used for so called “call-backs”                                    |
| B  | 1:1 | RPort : PPort   | Service acts as Server, typical Service usage                                          |
| C* | n:1 | PPort : RPort   | conceptually not used to support index abstraction via PortDefinedArgumentValues       |
| C  | n:1 | RPort:PPort     | SW-C acts as Server, used for so called “call-backs” invoked by more than one Service  | ---------------------->
Legend for Table 11.1:
I Pattern name
II Communication pattern (client/server, sender/receiver)
III Kind of PortPrototype at service : software-component
IV Description, use case

[TPS_SWCT_01398] Communication patterns for AUTOSAR services (cid:100) The communication patterns for AUTOSAR services are summarized in Table 11.1. (cid:99)()

[TPS_SWCT_01403] Impact of AUTOSAR services on the methodology (cid:100) Due to this special nature, such AUTOSAR Services need to be handled with particular attention in the methodology [4]. That is, a number of elements need to be generated during ECU integration. (cid:99)()

The following list of paragraphs presents a short overview over the steps required for the configuration of AUTOSAR Services. Note that most of these steps are performed by tools and the model elements being created in these steps are rather specific to Service configuration and are not to be modeled manually within AUTOSAR authoring tools.

#@Hierarchical
In particular, the following requirements apply:
• [TPS_SWCT_01399] Dependency is modeled by aggregating required and provided PortPrototypes (cid:100) The dependency of an AtomicSwComponentType (or more precisely, one of its non-abstract derived meta-classes) from an AUTOSAR Service is modeled by aggregating required and provided PortPrototypes. (cid:99)()

[TPS_SWCT_01400] PortInterface selected from the set of standardized Service Interfaces (cid:100) The PortInterface being implemented by the PortPrototypes needs to be one of a number of standardized Service Interfaces which is indicated by having its isService attribute set to true and is (via several levels of indirection) finally referenced by ServiceNeeds. (cid:99)()

Additionally, the software components and Basic Software Modules shall specify ServiceNeeds containing further input information for the later Service configuration step.

• [TPS_SWCT_01401] Form a top-level RootSwCompositionPrototype (cid:100) When defining a software system, the AtomicSwComponentType is used in the form of SwComponentPrototypes within a CompositionSwComponentType. In this step, the non-service ports of all required interfaces are being connected using AssemblySwConnectors and DelegationSwConnectors in order to eventually form a top-level RootSwCompositionPrototype which can be referenced in an AUTOSAR System. (cid:99)()

• [TPS_SWCT_01402] Mapping of all AtomicSwComponentType instances to EcuInstances (cid:100) In System Configuration Phase, the mapping of all AtomicSwComponentType instances to EcuInstances is done (for the specification of EcuInstance see [11]). The ServiceNeeds may be used by tools to check for available resources on the targeted ECUs. (cid:99)()

• [TPS_SWCT_01404] Creation of the Ecu Extract (cid:100) The ECU Extract is extracted from the System Configuration for each ECU. As explained in the AUTOSAR System Template [11], this contains an ECU-centric view onto the system description. This includes a reduced version of the system's RootSwCompositionPrototype where SwComponentPrototypes not being mapped to the ECU are being left out and all Compositions are stripped off, so that in the ECU Extract only one instance of CompositionSwComponentType remains which aggregates all SwComponentPrototypes on the ECU in a flat manner. (cid:99)()

• [TPS_SWCT_01405] Creation of the ServiceSwComponentTypes (cid:100) In ECU Configuration, for each Service required on the ECU exactly one ServiceSwComponentType is created based on the needs from the AtomicSwComponentTypes: An adequate number of PortPrototypes are created on this ServiceSwComponentType for each needed port at the AtomicSwComponentType. Thereby the specified communication pattern A, B or C for a specific kind of ServicePort has to be considered. See also chapter 11.3 and table 11.1. (cid:99)()

• [TPS_SWCT_01406] Creation of SwComponentPrototype typed by a ServiceSwComponentType (cid:100) Per Service exactly one SwComponentPrototype typed by a ServiceSwComponentType is created based on the ServiceSwComponentType. Additionally, the connectors are constructed that connect the pairs of PortPrototypes belonging to the SwComponentPrototypes requiring services and those belonging to the actual services. (cid:99)()

• [TPS_SWCT_01407] Creation of InternalBehavior typed by a ServiceSwComponentType (cid:100) For each ServiceSwComponentType an SwcInternalBehavior is created or extended providing the information about PortDefinedArgumentValues, RunnableEntitys and RTEEvents necessary for RTE generation. (cid:99)()

Further detailing of the service ports by filling in these PortDefinedArgumentValues is also done in ECU Configuration phase. See also chapter 7.6.3.

• [TPS_SWCT_01408] Creation of SwcBswMapping (cid:100) For the RTE module configuration an implementation of the AUTOSAR Service described by a Basic Software Module Description needs to be selected. The SwcBswMapping to the corresponding SwComponentPrototype needs to be created accordingly. For each SwcInternalBehavior one SwcImplementation is being created. The information for SwcImplementation should be generated based on the available information of BswImplementation(This step does in general not require copying any attributes or elements aggregated in BswImplementation into the generated instance of SwcImplementation since the only mandatory information for the RTE configuration is the reference from SwcImplementation to the selected SwcInternalBehavior.). (cid:99)()

• [TPS_SWCT_01409] Update of PortDefinedArgumentValues (cid:100) Depending of the configuration of the Service BSW it might be necessary to update the ValueSpecifications belonging to the PortDefinedArgumentValues generated in a previous step. (cid:99)()
/#@Hierarchical

Table 11.2: ServiceNeeds

#@SECTION: 11.2 Extending the ECU Software Composition
#@CLASS: AssemblySwConnector
#@CLASS: RootSwCompositionPrototype
#@CLASS: ServiceSwComponentType
#@CLASS: SwComponentPrototype
#@CLASS: System
#@CLASS: EcucValueCollection

As explained in chapter 11.1, Service Configuration takes place in ECU Configuration phase. In the ECU extract of the System, the Software Components and their ECU-internal connectors are represented as a flat set aggregated by RootSwCompositionPrototype as indicated in Figure 11.1.

ECU Configuration extends this aggregation by adding SwComponentPrototypes (each typed by a specific ServiceSwComponentType) and the required AssemblySwConnectors to the RootSwCompositionPrototype. This is possible without changing the initial artifacts of the ECU extract, because these aggregations are stereotyped as (cid:28)atpSplitable(cid:29) in the meta-model.

After this step, the RootSwCompositionPrototype (denoted by EcucValueCollection.ecuExtract.rootSoftwareComposition) represents the whole Software Composition on the given ECU. This collection includes both the software components mapped to the ECU and the necessary service components represented as one SwComponentPrototype for each AUTOSAR Service utilized on the given ECU.

Figure 11.1: Usage of RootSwCompositionPrototype on an ECU

#@SECTION: 11.3 Service Software Component Type
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: EcuAbstractionSwComponentType
#@CLASS: ComplexDeviceDriverSwComponentType
#@CLASS: InternalBehavior
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@CLASS: PPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: ServiceSwComponentType
#@CLASS: SwcBswMapping
#@CLASS: SwcInternalBehavior
#@CLASS: SwComponentPrototype
#@CLASS: SwComponentType
#@CLASS: ServiceNeeds

As mentioned in [TPS_SWCT_01405], AUTOSAR Services are represented by a meta model class of their own, the ServiceSwComponentType. As can be seen in Figure 11.2 ServiceSwComponentType is a specialization of AtomicSwComponentType.

Like any other SwComponentType they can aggregate PortPrototypes.

[constr_2019] ServiceSwComponentType shall have service ports only (cid:100) In the case of ServiceSwComponentType, all aggregated PortPrototypes need to have an (cid:28)isOfType(cid:29) relationship to a PortInterface which has its isService attribute set to true. The exceptions described in [TPS_SWCT_01572], [TPS_SWCT_01579] and [TPS_SWCT_01580] apply. (cid:99)()

[TPS_SWCT_01579] Dcm can directly access dataElements in PPortPrototypes typed by a SenderReceiverInterface (cid:100) An exception from the rule described in [constr_2019] applies: the Dcm can directly access dataElements in PortPrototypes (that is both AbstractProvidedPortPrototype and AbstractRequiredPortPrototype) typed by a SenderReceiverInterface. For this purpose, the ServiceSwComponentType that represents the Dcm functionality can have AbstractProvidedPortPrototypes and AbstractRequiredPortPrototypes typed by a compatible SenderReceiverInterface that may set isService to FALSE. (cid:99)()

[TPS_SWCT_01580] Dem can directly access dataElements in PPortPrototypes typed by a SenderReceiverInterface (cid:100) An exception from the rule described in [constr_2019] applies: the Dem can directly access dataElements in AbstractProvidedPortPrototypes typed by a SenderReceiverInterface. For this purpose, the ServiceSwComponentType that represents the Dem functionality can have RPortPrototypes typed by a compatible SenderReceiverInterface that may set isService to FALSE. (cid:99)()

[TPS_SWCT_01411] Use cases for a ServiceSwComponentType to express ServiceNeeds (cid:100) There are valid use cases for a ServiceSwComponentType to express ServiceNeeds(Thereby the previously existing constraint 1127 becomes invalid.). This leads to a situation where ServiceSwComponentTypes are iteratively created in response to ServiceNeeds expressed by other ServiceSwComponentTypes. Please refer to the AUTOSAR methodology [4] for more details about how this shall be implemented into the workﬂow. (cid:99)()

Similar to an EcuAbstractionSwComponentType and a ComplexDeviceDriverSwComponentType, the ServiceSwComponentType represents a hybrid concept between Software Component and Basic Software Module. The BSW part is described by the means of the BSW Module Description Template [7].

The mapping between the ServiceSwComponentType and the corresponding BswModuleDescription is provided by the class SwcBswMapping which in addition also maps the two corresponding InternalBehaviors (see [TPS_SWCT_01408]. This mechanism is further explained in [7]).

Figure 11.2: ServiceSwComponentType

Table 11.3: ServiceSwComponentType

[TPS_SWCT_01412] ServiceSwComponentType shall be added in ECU Configuration phase (cid:100) ServiceSwComponentType shall not be used when modeling application software using CompositionSwComponentType; they are only added in ECU Configuration phase where exactly one SwComponentPrototype per ServiceSwComponentType per ECU is added to the ECU Description model. The Base ECU Config Generator tool needs to take care that for all service ports of SwComponentPrototypes mapped to the ECU service ports at the appropriate ServiceSwComponentTypes are created. In the process the speciﬁed communication pattern A, B, or C for a speciﬁc kind of service port has to be considered, see table 11.1.

In case of pattern A for each different type of service port one port on the ServiceSwComponentType is created. In case of pattern B and C for each service port of a SwComponentPrototype one port on the ServiceSwComponentType is created. More explicitly, all instances of AtomicSwComponentType need to be checked for PortPrototypes of PortInterfaces with isService attribute set to true and referenced by ServiceNeeds and for each of these PortInterface instances belonging to the AUTOSAR Service to be conﬁgured one PortPrototype implementing the same or a compatible PortInterface needs to be created on the ServiceSwComponentType. (cid:99)()

[TPS_SWCT_02500] Roles on Application/Service Components need to Match (cid:100) The roles of the PortPrototypes (required/provided) on the Application Component and the Service Component side obviously need to match. For example an RPortPrototype attached to an application AtomicSwComponentType matches a PPortPrototype attached to a ServiceSwComponentType. (cid:99)()

#@SECTION: 11.4 Service Proxy Component Type
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: ServiceProxySwComponentType
#@CLASS: ServiceSwComponentType
#@CLASS: SwComponentPrototype
#@CLASS: PortInterface

[TPS_SWCT_01413] Local communication with services (cid:100) Application software components may communicate with an instance of a ServiceSwComponentType only locally on an ECU. (cid:99)()

[TPS_SWCT_01414] Mode manager needs to communicate with application software components located on other ECUs (cid:100) There are however use cases for the application and vehicle mode management, where a mode manager (namely the Basic Software Mode Manager, see [15]) is part of the basic software but conceptually still needs to communicate with application software components located on other ECUs (as exemplified by Figure 11.3). In order to make this communication possible, the ServiceProxySwComponentType is used. For the application software and the RTE it behaves like a "normal" AtomicSwComponentType, but it is actually a proxy for an AUTOSAR Service. (cid:99)()


<-------------- multimodal context 
The diagram illustrates a distributed mode‐request use case in which a VehicleClampControl component issues a mode change that is transparently proxied across two ECUs via VehicleClampProxy and the BswM service, reaching a remote application on ECU2.

• Component hierarchy  
  - SW-Components: VehicleClampControl (VCC), VehicleClampProxy (VCP), Application1 (App1), Application2 (App2).  
  - On VFB they float on the virtual bus; in deployment each ECU contains its local RTE, hosting VCC+VCP+App1+BswM on ECU1 and VCP+App2+BswM on ECU2.  

• Ports & interfaces  
  - VCC: PPort “ModeRequest” (ClientServerInterface).  
  - VCP: RPort “ModeRequest” and PPort “ModeRequest” (delegating proxy).  
  - BswM Service: RPort “ModeRequest” and PPort “ModeRequest.”  
  - App1/App2: client ports (black square) for downstream calls.  
  - AssemblySwConnectors link PPorts to RPorts; the network-transparent DelegationSwConnectors carry calls between ECU1 and ECU2.  

• Data flow  
  - VCC invokes the ModeRequest operation on its PPort → VCP.RPort → VCP.PPort → local BswM.RPort.  
  - BswM.PPort sends the request over the network (RTE1→RTE2) to remote BswM.RPort → VCP.RPort on ECU2 → VCP.PPort → App2 client port.  

• Key AUTOSAR concepts  
  - AbstractProvidedPortPrototype (PPort) and AbstractRequiredPortPrototype (RPort) for ClientServerInterface.  
  - AssemblySwConnector for intra-ECU binding, DelegationSwConnector for inter-ECU (network).  
  - ModeAccessPoint via BswM, proxies for location transparency.  
  - CompositionSwComponentType (ECU composition hosting RTE and BSW).  

• Scenario  
  - Design intent: VehicleClampControl issues a mode switch that must reach a remote application on ECU2.  
  - VehicleClampProxy abstracts network, BswM orchestrates mode propagation across ECUs. ---------------------->
Figure 11.3: Mode request over the network [3]

[TPS_SWCT_01415] Interfaces of ServiceProxySwComponentType (cid:100) This means that on the one side it has to communicate over service ports with the ECU-local ServiceSwComponentType it represents. On the other side it has to offer the corresponding PortPrototypes to the ApplicationSwComponentTypes. (cid:99)()

In the meta-model, the ServiceProxySwComponentType does not differ from an ApplicationSwComponentType except by its class. It is up to the implementer to meet the restrictions imposed by the semantics as a proxy.

[TPS_SWCT_01416] Difference between a ServiceProxySwComponentType and an ApplicationSwComponentType (cid:100) The main difference between a ServiceProxySwComponentType and an ApplicationSwComponentType is on system level: A prototype of a ServiceProxySwComponentType can be mapped to several ECUs even if it appears only once in the VFB system, because such a prototype is required on each ECU, where it has to address a local ServiceSwComponentType. As a result of this, a ServiceProxySwComponentType can only receive but not send signals over the network. More details are explained in the class table below. (cid:99)()

Table 11.4: ServiceProxySwComponentType

[constr_2016] Connections between SwComponentPrototypes of type ServiceProxySwComponentType (cid:100) A connection between PortPrototypes belonging to SwComponentPrototypes where both are typed by ServiceProxySwComponentType is not permitted. (cid:99)()

[constr_2017] Ports of ServiceProxySwComponentTypes (cid:100) ServiceProxySwComponentType is only permitted to define
• RPortPrototypes that are typed by SenderReceiverInterface or
• PortPrototypes that are typed by a PortInterface where the isService attribute is set to true. (cid:99)()

[constr_2018] Supported remote communication of a ServiceProxySwComponentType (cid:100) For remote communication, ServiceProxySwComponentType can have only RPortPrototypes typed by SenderReceiverInterfaces in a 1:n communication scenario. (cid:99)()

#@SECTION: 11.5 Non Volatile Memory
#@SECTION: 11.5.1 Introduction
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarDataTypes
#@CLASS: InternalBehavior
#@CLASS: NvBlockSwComponentType
#@CLASS: PerInstanceMemory
#@CLASS: PortPrototype
#@CLASS: RoleBasedDataAssignment
#@CLASS: NvBlockNeeds
#@CLASS: AutosarDataType

The AUTOSAR Architecture defines two alternatives how a software component can access non volatile memory.

• The first option is that the software component defines in its InternalBehavior a PerInstanceMemory and a NvBlockNeeds referring to the PerInstance Memory via a RoleBasedDataAssignment. In this case the NVRAM Block is exclusively accessed by this software component and the NvM [31]. Therefore the nv data is encapsulated inside the software component and can not be accessed directly by other software components. The PerInstanceMemory can be typed with AutosarDataTypes in the case of arTypedPerInstanceMemory or with C data types in the case of perInstanceMemory. For further information see section 7.7 and 7.11.3.

• The second option is that the software component uses communication based on PortPrototypes to access nv data provided by a NvBlockSwComponentType. In this case it is possible that nv data used by different AtomicSwComponentTypes is packed in one larger NVRAM Block to reduce the NVRAM Block management overhead or that the same nv data used by several software components with a reduced RAM overhead. The nv data of a NvBlockSwComponentType is typed with AutosarDataTypes.

More details regarding particular scenarios of interacting with the NvM [31] can be found in section 7.11.3.1.

#@SECTION: 11.5.2 NvBlockComponent
#@CLASS: AtomicSwComponentType
#@CLASS: ClientServerInterface
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: NvDataInterface
#@CLASS: PortPrototype
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SwComponentPrototype
#@CLASS: SwConnector
#@CLASS: VariableDataPrototype
#@CLASS: ModeSwitchInterface

[TPS_SWCT_01142] non-volatile data are provided by a specialized Atomic SwComponentType (cid:100) On the VFB [3], the non-volatile data are provided by a specialized AtomicSwComponentType, the NvBlockSwComponentType. An NvBlockSwComponentType can represent one or more NVRAM Blocks managed by the NVRAM Manager. The nv data PortPrototypes of the NvBlockSwComponentType are exclusively typed by NvDataInterfaces. (cid:99)(RS_SWCT_03225)

[TPS_SWCT_01143] Non-volatile data represented by an NvBlockSwComponentType can be read and written (cid:100) The non-volatile data represented by an NvBlockSwComponentType can be read and written. For this purpose the NvBlockSwComponentType is allowed to have PPortPrototypes and RPortPrototypes. (cid:99)(RS_SWCT_03225) Additionally, the NvBlockSwComponentType might have client server PortPrototypes to offer the block-related services, administrative services or notifications.

[constr_2009] Supported kinds of PortPrototypes of a NvBlockSwComponentType (cid:100) With respect to external communication, NvBlockSwComponentType is limited to the definition of the following kinds of PortPrototype: 
• PortPrototypes typed by either NvDataInterfaces or ClientServerInterfaces 
• RPortPrototypes typed by ModeSwitchInterfaces 
(cid:99)()

[constr_2010] Connections between SwComponentPrototypes of type NvBlockSwComponentType (cid:100) The existence of SwConnectors that refer to PortPrototypes belonging to SwComponentPrototypes where both are typed by NvBlockSwComponentType is not permitted. (cid:99)()

Table 11.5: NvBlockSwComponentType

Table 11.6: NvDataInterface

Figure 11.4: NvDataInterface

#@SECTION: 11.5.3 Software-Components using NVRAM data of NvBlockComponents
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: ClientServerInterface
#@CLASS: DataInterface
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockNeeds
#@CLASS: NvBlockSwComponentType
#@CLASS: NvDataInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface
#@CLASS: SwComponentPrototype
#@CLASS: SwcServiceDependency

[constr_2011] Connections between SwComponentPrototypes typed by NvBlockSwComponentType and SwComponentPrototypes typed by other AtomicSwComponentTypes (cid:100) The nv data PortPrototypes of the SwComponentPrototype typed by an NvBlockSwComponentType are either connected with PortPrototypes typed by NvDataInterfaces or SenderReceiverInterfaces of other AtomicSwComponentType. (cid:99)()

[constr_1148] PortInterfaces of PortPrototypes used to connect to NvBlockSwComponentTypes (cid:100) PortInterfaces of PortPrototypes used to connect to NvBlockSwComponentTypes as well as the PortInterfaces used in the context of NvBlockSwComponentTypes shall always set the value of the attribute isService to false. (cid:99)()

[constr_1149] PortPrototypes used for NV data management (cid:100) A PortPrototype typed by a ClientServerInterface used for NV data management, i.e. the interaction of ApplicationSwComponentTypes with NvBlockSwComponentTypes, shall be typed by ClientServerInterfaces that are compatible to the particular ClientServerInterfaces derived from MOD_GeneralBlueprints [30]. [constr_1148] applies. (cid:99)()

For details see chapter 6.4.4.

Note: In case of nv data which is read and written and shared between several SwComponentPrototypes the NvBlockSwComponentType establishes a not directly obvious kind of communication. Nevertheless this is intentionally supported and it is under responsibility of the VFB designer to take care that only nv data is shared where the functionality of the software components is not impaired.

To determine for an VFB designer which nv data can be potentially by mapped into the same NVRAM Block a software-component can specify further attributes for its nv data PortPrototypes by the definition of SwcServiceDependency(s) with NvBlockNeeds. In this case the role attribute of the assignedPort has to be set to the value NvDataPort. This aspect is also explained in section 7.11.3.1.4.

Figure 11.5: NvBlockNeeds for nv data PortPrototypes

In contrast to the NvBlockNeeds that describe the expected configuration of a whole NVRAM Block, the NvBlockNeeds for nv data PortPrototypes defines only the attributes which are required from the point of view of a software-component to ensure its functionality.

This means an empty attribute has the semantic of "don't care".

Further on the VFB designer has got the freedom to specify how the requested NVRAM Block attributes are fulfilled by the created NvBlockDescriptor.

For instance, nv data with different writingFrequency might be mapped to one NVRAM Block. In this case the NvBlockNeeds of the NvBlockDescriptor has to indicate the worst case which is the higher frequency.

The recommended relationship is shown in table 11.7. But please note that this table does not represent a binding constraint.

Table 11.7: NvBlockNeeds dependencies
<-------------- multimodal context 


| Attribute of NvBlockNeeds | NvBlockNeeds of different nv data PortPrototypes of software-components | NvBlockNeeds of NvBlockDescriptor |
|------------------------|---------------------------------------------------|--------------------------------|
| readonly | Recommended to match for all connected nv data PortPrototypes if specified. | Recommended to be identical as requested by nv data PortPrototypes. |
| reliability | Can be different. | Recommended to be set to the highest reliability class request by any mapped nv data PortPrototypes. |
| resistantToChangedSw | Recommended to match for all connected nv data PortPrototypes if specified. | Recommended to be identical as requested by nv data PortPrototypes. |
| restoreAtStart | Recommended to match for all connected nv data PortPrototypes if specified. | Recommended to be identical as requested by nv data PortPrototypes. |
| storeAtShutdown | Recommended to match for all connected nvdataports if specified. | Recommended to set to true if any of the nv data PortPrototypes requests writing at shutdown. |
| writeOnlyOnce | Recommended to match for all connected nv data PortPrototypes if specified. | Recommended to be identical as requested by nv data PortPrototypes. |
| writingFrequency | Can be different. | Recommended to be set to the highest requested frequency of the mapped nv data PortPrototypes. |
| writingPriority | Can be different. | Recommended to be set to the highest requested frequency of the mapped nv data PortPrototypes. |
| writeVerification | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests a write verification. |
| calcRamBlockCrc | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests a CRC calculation. |
| checkStaticBlockId | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests a check of the static block ID. |
| ramBlockStatusControl | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests a use of the API for accessing the block. |
| storeAtShutdown | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests writing at shutdown. |
| storeCyclic | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests cyclic writing. |
| storeEmergency | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests emergency writing. |
| storeImmediate | Can be different. | Recommended to set to true if any of the nv data PortPrototypes requests immediate writing. |
------------------------>

With respect to the completeness of table 11.7 (which intentionally doesn't contain a remark regarding the value of cyclicWritingPeriod), it should be noted that (according to [TPS_SWCT_01585]) the value of NvBlockDescriptor.nvBlockNeeds.cyclicWritingPeriod shall be ignored in favor of NvBlockDescriptor.timingEvent.period.

Therefore, the missing statement for cyclicWritingPeriod in the spirit of table 11.7 is that the values of SwcServiceDependency.serviceNeeds.cyclicWritingPeriod can be different from the value of NvBlockDescriptor.timingEvent.period.

It is recommended that the value of NvBlockDescriptor.timingEvent.period shall be set to the lowest requested time value of the mapped nv data PortPrototypes (implemented by SwcServiceDependency.serviceNeeds.cyclicWritingPeriod).

#@SECTION: 11.5.4 NvBlockDescriptor
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarDataPrototype
#@CLASS: NvBlockDataMapping
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockNeeds
#@CLASS: NvBlockSwComponentType
#@CLASS: ParameterDataPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: TimingEvent
#@CLASS: VariableDataPrototype

[TPS_SWCT_01144] NvBlockDescriptor specifies the properties of exactly one NVRAM Block (cid:100) A NvBlockDescriptor specifies the properties of exactly one NVRAM Block of a NvBlockSwComponentType.

It contains information about the requested NVRAM Block configuration of the NVRAM Manager, ramBlock and romBlock, the mapping between the PortPrototypes of the NvBlockSwComponentType and the data inside a ramBlock as well as the role of the clientServerPorts expressed in terms of RoleBasedPortAssignment. (cid:99)()

Table 11.8: NvBlockDescriptor

For more explanation about the semantics of the attribute NvBlockDescriptor.supportDirtyFlag please refer to the SWS RTE [2].

Figure 11.6: NvBlockSwComponentType and NvBlockDescriptor

[constr_1095] Values of nDataSets vs. reliability (cid:100) If the value of nDataSets is greater than 0 the value of reliability shall not be set to errorCorrection. (cid:99)()

The reason for the existence of [constr_1095] is that the AUTOSAR NvM [31] does not support error correction for NV data sets. If the value of nDataSets is equal to 0 the value of reliability can take any value out of NvBlockNeedsReliabilityEnum.

#@SECTION: 11.5.4.1 Writing Strategies
#@CLASS: AtomicSwComponentType
#@CLASS: DataReceivedEvent
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: SwcInternalBehavior
#@CLASS: TimingEvent
#@CLASS: NvBlockNeeds

[TPS_SWCT_01586] Writing strategies for nv data (cid:100) By setting certain attributes in the meta-class NvBlockDescriptor it is possible to configure different writing strategies for the values of an RAM Block to the NVRAM storage. [constr_1310] applies.

The following use cases are supported:

• Write data cyclically. This use case requires the existence of attribute NvBlockDescriptor.nvBlockNeeds.storeCyclic with the value true and also attribute NvBlockDescriptor.cyclicWritingPeriod needs to exist and have a reasonable value. In the context of using the attribute NvBlockDescriptor.cyclicWritingPeriod the constraints [constr_1308] and [constr_1309] apply. Please refer to [TPS_SWCT_01587] and Figure 11.7 for more information about how this aspect can be configured.

• Write data immediately. This means that data send to the NvBlockSwComponentType will be written immediately to NVRAM storage. This use case corresponds to setting the value of attribute NvBlockDescriptor.nvBlockNeeds.storeImmediate to the value true. Please refer to [TPS_SWCT_01588] and Figure 11.8 for more information about how this aspect can be configured.

• Write on emergency. With this setting, data shall be written to NVRAM storage if the ECU fails in some way. This use case corresponds to setting the value of attribute NvBlockDescriptor.nvBlockNeeds.storeEmergency to true. As explained in [TPS_SWCT_01589], setting the value of this attribute is not sufficient to achieve the intended semantics.

• Write at shutdown. Here, the data are written to NVRAM storage when the ECU shuts down. This use case corresponds to setting the value of attribute NvBlockDescriptor.nvBlockNeeds.storeAtShutdown to true. 
(cid:99)(RS_SWCT_03225)

Of course, the actual implementation of the different writing strategies goes beyond setting the value of attributes and requires the existence of dedicated RunnableEntitys in the SwcInternalBehavior of the enclosing NvBlockSwComponentType that are triggered in response to RTEEvents applicable for the particular use case.

[TPS_SWCT_01587] The cyclic writing of nv data requires the existence of a TimingEvent (cid:100) The implementation of cyclic writing of nv data requires the existence of a TimingEvent that can be taken to trigger a corresponding RunnableEntity that in turn takes care of calling the respective APIs for writing the data. (cid:99)(RS_SWCT_03225) This aspect is depicted in Figure 11.7.

Figure 11.7: How to model a cyclic writing strategy for nv data

[TPS_SWCT_01588] DataReceivedEvent for storing nv data immediately (cid:100) The approach to store data immediately after reception by an NvBlockSwComponentType requires the activation of a RunnableEntity by a DataReceivedEvent. (cid:99)(RS_SWCT_03225) This approach is depicted in Figure 11.8.

Figure 11.8: How to model an immediate writing strategy for nv data

[TPS_SWCT_01589] Implementation of emergency storing of nv data (cid:100) The use case for storeEmergency can only be implemented by means of a Complex Driver. In particular, the Complex Driver is responsible for the detection of an ECU failure. If a relevant error occurs the Complex Driver should call the NvM write block operation for the emergency blocks directly. (cid:99)(RS_SWCT_03225) 

This consequently means that the NvM shall react to write operations coming from the Complex Driver by giving them the highest priority (re-queuing of NvM write block requests). Please note that the behavior described in [TPS_SWCT_01587] in general is supported by AUTOSAR by requiring that NVRAM Blocks shall have to be configured with "immediate priority". The technical implications are explained in the respective SWS [31], e.g. in [SWS_NvM_00182] and [SWS_NvM_00300].

[TPS_SWCT_01590] Combination of writing strategies for nv data is possible (cid:100) AUTOSAR positively supports the configuration of a combination of writing strategies for nv data. (cid:99)(RS_SWCT_03225) 

In other words, in consequence of [TPS_SWCT_01590] it is possible that (for example) both NvBlockDescriptor.storeImmediate as well as NvBlockDescriptor.storeCyclic may exist and set to true in the context of the same NvBlockNeeds.

#@SECTION: 11.5.4.2 NvBlockNeeds
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockNeeds
#@ENUM: NvBlockNeedsReliabilityEnum
#@ENUM: NvBlockNeedsWritingPriorityEnum
#@CLASS: ApplicationSwComponentType
#@CLASS: SwcServiceDependency

The requested NVRAM Block configuration of the NVRAM Manager is described by the NvBlockNeeds of the NvBlockDescriptor.

This information can be evaluated during ECU configuration similar to the NvBlock Needs of an atomic software component or a BSW module. For further details see section 7.11.3.

Figure 11.9: NvBlockNeeds

[constr_1308] Existence of NvBlockNeeds.cyclicWritingPeriod (cid:100) The attribute NvBlockNeeds.cyclicWritingPeriod shall exist if and only if the attribute NvBlockNeeds.storeCyclic exists and its value is set to true. (cid:99)()

Table 11.9: NvBlockNeeds

Table 11.10: NvBlockNeedsReliabilityEnum

[constr_1310] Existence of attributes of meta-class NvBlockNeeds (cid:100) If in the context of an ApplicationSwComponentType the attribute SwcServiceDependency.serviceNeeds is implemented by an NvBlockNeeds then the following attributes 
• NvBlockNeeds.storeCyclic 
• NvBlockNeeds.cyclicWritingPeriod 
• NvBlockNeeds.storeEmergency 
• NvBlockNeeds.storeImmediate 
shall only exist if in the context of the same SwcServiceDependency a SwcServiceDependency.assignedPort exists that has the attribute role set to the value NvDataPort. (cid:99)()

#@SECTION: 11.5.4.3 RAM Block and ROM Block
#@CLASS: AutosarDataType
#@CLASS: ParameterDataPrototype
#@CLASS: VariableDataPrototype
#@CLASS: PortPrototype
#@CLASS: ClientServerInterface
#@CLASS: ImplementationDataType
#@CLASS: SwDataDefProps
InstantiationDataDefProps
[TPS_SWCT_01145] ramBlock and the romBlock are described by a VariableDataPrototype and a ParameterDataPrototype (cid:100) The ramBlock and the romBlock are described by a VariableDataPrototype and a ParameterDataPrototype which are typed by an AutosarDataType. (cid:99)()

[TPS_SWCT_01146] romBlock is optional (cid:100) The romBlock is optional. If a romBlock is configured the RTE copies the romBlock constants into the RAM Block in case of a block initialization notification (NvMNotifyInitBlock). (cid:99)()

[TPS_SWCT_01147] No romBlock is configured (cid:100) If there is no romBlock configured the connected software components are either required to offer this functionality by a proper implementation of block initialization notification or the NVRAM Block has to be configured, that no ROM Block is needed. (cid:99)()

As a mitigation against a failed read operation from NV memory it is recommended to always define a romBlock with suitable initial values to ensure the proper initialization of the corresponding ramBlock.

In particular, for software-components that don’t define a PortPrototype typed by the ClientServerInterface with the standardized shortName NotifyInitBlock [31] it may happen that the ramBlock might not be properly initialized in case of failure.

[constr_2012] Compatibility of ImplementationDataTypes used for ramBlock and romBlock (cid:100) The ramBlock and the romBlock shall have compatible ImplementationDataTypes to ensure, that the NVRAM Block default values in the ROM Block can be copied into the RAM Block. (cid:99)()

Additionally it is possible that RAM Block and ROM Block are defined to be able to calibrate or measurable. Preceding SwDataDefProps might be defined with the means of an InstantiationDataDefProps.

#@SECTION: 11.5.4.4 NvBlockDataMapping
#@CLASS: ApplicationDataType
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarVariableRef
#@CLASS: ImplementationDataType
#@CLASS: NvBlockDataMapping
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: NvDataInterface
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: PortInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency
#@CLASS: VariableDataPrototype
#@CLASS: ImplementationDataTypeElement
#@CLASS: VariableInAtomicSWCTypeInstanceRef


[TPS_SWCT_01148] NvBlockDataMapping (cid:100) The meta-class NvBlockDataMapping specifies the mapping of VariableDataPrototypes of the NvBlockSwComponentType’s ports (PPortPrototypes / RPortPrototypes) to VariableDataPrototypes inside the RAM Block. (cid:99)()

This ensures a flexible but deterministic NVRAM Block memory structure given by the ImplementationDataType of the ramBlock and romBlock and its association to the PortPrototypes of the NvBlockSwComponentType.

[constr_2013] Compatibility of ImplementationDataTypes for NvBlockDataMapping (cid:100) The NvBlockDataMapping is only valid if the ImplementationDataType of the referenced VariableDataPrototype or ImplementationDataTypeElement in the role nvRamBlockElement is compatible to the ImplementationDataType used to type the VariableDataPrototype aggregated by NvBlockDataMapping in the role writtenNvData, writtenReadNvData, or readNvData. (cid:99)()

[constr_1285] Applicability of roles vs. PortPrototypes (cid:100) The aggregation of AutosarVariableRef aggregated by NvBlockDataMapping in the roles writtenNvData, writtenReadNvData, or readNvData is subject to limitation depending on the applicable subclass of PortPrototype:
• The role writtenNvData shall only be used if the corresponding PortPrototype is a RPortPrototype
• The role writtenReadNvData shall only be used if the corresponding PortPrototype is a PRPortPrototype
• The role readNvData shall only be used if the corresponding PortPrototype is a PPortPrototype
(cid:99)()

But nevertheless it is valid, that not all ImplementationDataTypeElements within the VariableDataPrototype aggregated by NvBlockDescriptor in the role ramBlock are mapped to a VariableDataPrototype located in a PortPrototype.

This enables to have fill elements or logistic data in the NVRAM Block which are not accessed by software components. This is exempliﬁed by the element x in Figure 11.10.

Please note that the VariableDataPrototype located in the PortPrototype, in the vast majority of cases, will be typed by an ApplicationDataType which in turn (at least before the actual code generation starts) ﬁnally shall have a mapping to an ImplementationDataType. This aspect is explained in chapter 5.2.2.

[TPS_SWCT_01659] Mapping of VariableDataPrototype to a NvBlockDescriptor (cid:100) There are three ways to map a VariableDataPrototype (i.e. NvDataInterface.nvData in the context of a speciﬁc PortPrototype) to either an NvBlockDescriptor.ramBlock or a sub-element thereof:
• NvDataInterface.nvData is directly and completely mapped, i.e. AutosarVariableRef.autosarVariable shall exist and autosarVariable.targetDataPrototype shall refer to the NvDataInterface.nvData.
• Every leaf element of NvDataInterface.nvData is mapped individually. This means that either:
  - AutosarVariableRef.autosarVariableInImplDatatype shall exist and autosarVariableInImplDatatype.targetDataPrototype shall refer to the respective leaf element of NvDataInterface.nvData.
  - AutosarVariableRef.autosarVariable shall exist and autosarVariable.targetDataPrototype shall refer to the respective leaf element of NvDataInterface.nvData.
• A sub-element of NvDataInterface.nvData - which is not a leaf element - may be directly mapped and consequently all the leaf elements of the respective sub-element of NvDataInterface.nvData are indirectly mapped as well. This means that:
  - AutosarVariableRef.autosarVariableInImplDatatype shall exist and autosarVariableInImplDatatype.targetDataPrototype shall refer to the sub-element element of NvDataInterface.nvData.
  - AutosarVariableRef.autosarVariable shall exist and autosarVariable.targetDataPrototype shall refer to the sub-element element of NvDataInterface.nvData.
(cid:99)()

Please note that a mixing of mutually exclusive mappings for entire sub-elements or leaf elements as described by [TPS_SWCT_01659] is positively supported (see Figure 11.10).


<-------------- multimodal context 
This diagram illustrates an AUTOSAR NvBlockSwComponent that exposes a single NvDataInterface port (nvData) mapped onto an internal NvBlockDescriptor (ramBlock). It demonstrates how root, leaf and sub-elements of a composite NvData structure are bound to fields of an in-component RAM data block for non-volatile data storage.

• Component hierarchy  
  – AtomicSwComponentType “NvBlockSwComponent”  
  – Exposes one AbstractProvidedPortPrototype linked to NvDataInterface  
  – Contains an internal implementation data type NvBlockDescriptor  

• Ports & interfaces  
  – PPort: nvData : NvDataInterface  
  – Data elements: a, b, g (root); h, j, s (inside g); u, w (inside s)  
  – Internal data instance: ramBlock with matching fields  

• Data flow  
  – nvData root elements a/b map directly to ramBlock.a/ramBlock.b  
  – Leaf elements h/j map to ramBlock.h/ramBlock.j  
  – Sub-element s maps to ramBlock.s, whose u/w map to ramBlock.s.u/ramBlock.s.w  

• Key AUTOSAR concepts  
  – Provided port, data interface, application composite data prototypes  
  – Element-level mapping kinds: “nvData root,” “leaf element,” “sub-element”  
  – No mode switches or events shown  

• Scenario  
  – Example of TPS_SWCT_01659 NvBlockDataMapping: binding an external NvDataInterface to an internal RAM descriptor for persistent storage. ---------------------->
Figure 11.10: Example NvBlockDataMapping to explain [TPS_SWCT_01659]

[constr_1395] NvBlockDataMapping shall be complete (cid:100) If an NvBlockDataMapping refers to sub-elements or leaf elements of the NvDataInterface.nvData in the context of a particular PortPrototype then all remaining sub-elements or leaf elements shall effectively be mapped according to [TPS_SWCT_01659] by means of a collection of NvBlockDataMappings. (cid:99)()

[constr_1403] NvBlockDataMappings to a given nvData shall be unambiguous (cid:100) If an NvBlockDataMapping exists that directly and completely maps a speciﬁc NvDataInterface.nvData in the context of a particular PortPrototype then no other NvBlockDataMapping which maps sub-elements of the NvDataInterface.nvData shall exist. (cid:99)()

The interaction with AUTOSAR services is centrally deﬁned in the context of the SwcServiceDependency. The latter gathers a collection of PortPrototypes by means of RoleBasedPortAssignments that implement a closely related service functionality.

In the speciﬁc case of interaction between AtomicSwComponentType and NvBlockSwComponentType (as described by [TPS_SWCT_02503]), there are PortPrototypes referenced by a RoleBasedPortAssignment with attribute RoleBasedPortAssignment.role set to NvDataPort. These PortPrototypes contain the collected Nv Data of the service use case.

Furthermore, there is the possibility to receive notiﬁcations when the writing of the mapped NV Block to the NvRam is ﬁnished.

In order to be able to properly assign such a notiﬁcation to the content of the related Nv Data PortPrototypes in the scope of the same SwcServiceDependency it is necessary that the Nv Data of all these PortPrototypes is mapped to the same Nv Block (because the notiﬁcations are created per block).

This motivates the existence of [constr_1404]:
[constr_1404] All NvDataInterface.nvData of PortPrototypes in the context of a speciﬁc SwcServiceDependency shall be mapped to the same NvBlockDescriptor (cid:100) In the context of a given SwcServiceDependency (which, in turn, is owned by an AtomicSwComponentType), all NvDataInterface.nvData of PortPrototypes referenced by a RoleBasedPortAssignment with attribute RoleBasedPortAssignment.role set to NvDataPort shall be connected (either directly or via the deﬁnition of suitable PortInterfaceMappings) to NvDataInterface.nvData (on the side of the NvBlockSwComponentType) that are completely mapped (via NvBlockDataMappings) to the identical NvBlockDescriptor.ramBlock. (cid:99)()


<-------------- multimodal context 
This architecture defines an Application SW-Component and an NvBlock SW-Component collaborating to persist and retrieve non-volatile data. The Application SWC exposes DataX via NvDataPorts and invokes an SwcServiceDependency for NVRAM operations; the NvBlock SWC implements the storage mapping, links ramBlockY to BlockY, and signals completion through the NvMNotifyJobFinished Client-Server interface.

• Component hierarchy  
  – Two SwComponentPrototype instances: one typed by ApplicationSwComponentType containing SwcServiceDependency “DataX” and NvDataInterface/DataX1, DataX2; one typed by NvBlockSwComponentType housing NvBlockDataMapping, VariableDataPrototype “ramBlockY” and NvBlockDescriptor “BlockY.”  

• Ports & interfaces  
  – RoleBasedPortAssignment for roles NvDataPort (PPort/RPort for DataX1/DataX2) and NvMNotifyJobFinished (ClientServerInterface); NvBlockNeeds «isOfType» DataX; NvDataInterface «isOfType» DataY2.  

• Data flow  
  – Application sends DataX to NvBlock via NvDataPort assemblies; NvBlock stores it in ramBlockY/BlockY; upon completion, NvBlock invokes NvMNotifyJobFinished back to the Application.  

• Key AUTOSAR concepts  
  – SwcServiceDependency, RoleBasedPortAssignment, AssemblySwConnector, DelegationSwConnector, «isOfType» associations, ClientServerInterface, NvBlockDataMapping, VariableDataPrototype, NvBlockDescriptor.  

• Scenario  
  – Design intent: enable the Application component to offload non-volatile data storage to an NvBlock SWC and receive asynchronous job-finished notifications. ---------------------->
Figure 11.11: Visualization of the statement made by [constr_1404]

The statement made by [constr_1404] is visualized in Figure 11.11. The context deﬁning model elements, i.e. SwcServiceDependency owned by the AtomicSwComponentType as well as NvBlockDescriptor owned by the NvBlockSwComponentType, are colored in light orange.

The diagram is focused on the NvBlockDescriptor.ramBlock. As stressed by [constr_1404], all Nv Data provided by the PortPrototypes referenced by the speciﬁc SwcServiceDependency ﬁnally ends up in the one depicted ramBlock (colored in blue).

Please note that the graphical representation of the NvBlockDataMapping in Figure 11.11 has been simpliﬁed for the sake of clarity.

Table 11.11: NvBlockDataMapping

Figure 11.12: NvBlockToPortMapping and InstantiationDataDefProps

#@SECTION: 11.5.4.5 Client Server Ports
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RPortPrototype
#@CLASS: RoleBasedPortAssignment

[TPS_SWCT_01149] RoleBasedPortAssignment of NvBlockDescriptor (cid:100) The clientServerPort of the NvBlockDescriptor describes which client/server PortPrototype of the NvBlockSwComponentType serves for which purpose. The role specifies if the port serves for block-related services, administrative services or notification. (cid:99)()

[constr_2014] Limitation of RoleBasedPortAssignment.role in NvBlockDescriptors (cid:100) The role has to be set to a valid name of the Standardized AUTOSAR Interface used for the NVRAM Manager e.g. NvMNotifyJobFinished or NvMNotifyInitBlock. (cid:99)()

In case of notifications one common callback function is provided by the RTE for each individual kind of notification defined by the role.

Figure 11.13: NvBlockNotification

#@SECTION: 11.5.5 SwcInternalBehavior of an NvBlockSwComponentType
#@CLASS: ClientServerInterface
#@CLASS: DataReceivedEvent
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: OperationInvokedEvent
#@CLASS: PortAPIOption
#@CLASS: PortDefinedArgumentValue
#@CLASS: PortPrototype
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: SwcInternalBehavior
#@CLASS: SwcModeSwitchEvent
#@CLASS: SwcServiceDependency
#@CLASS: TimingEvent
#@CLASS: VariableAccess
#@CLASS: InternalBehavior
#@CLASS: PPortPrototype
#@CLASS: NvBlockNeeds
#@CLASS: ModeDeclaration
#@CLASS: NvBlockDescriptor
[TPS_SWCT_01150] InternalBehavior of a NvBlockSwComponentType to enable access to the NVRAM Block management API (cid:100) In general, the InternalBehavior of a NvBlockSwComponentType is only used for a limited scope. The main use case is that the NvBlockSwComponentType defines PPortPrototypes typed by a ClientServerInterface to enable access to the NVRAM Block management API. To enable the configuration of the server invocation in the RTE’s ECU configuration, the NvBlockSwComponentType needs to provide the following model elements: 
• OperationInvokedEvents 
• server RunnableEntity 
• PortDefinedArgumentValues to define the NVRAM Block ID which has to be passed to the NvM In addition to the above list further model elements may qualify; the details are explained in [TPS_SWCT_01584]. (cid:99)()

[TPS_SWCT_01584] InternalBehavior of a NvBlockSwComponentType for implementing a writing strategy (cid:100) For the use case that NvBlockDescriptors exists that aggregate NvBlockNeeds which, in turn, define particular NV data writing strategies (by defining any of the attributes storeAtShutdown, storeImmediate, storeEmergency, or storeCyclic) the InternalBehavior of a NvBlockSwComponentType needs to support further model elements. Particularly, In addition to the model elements listed in [TPS_SWCT_01150], the following list of model elements can be used in the InternalBehavior of a NvBlockSwComponentType for implementing writing strategies: 
• TimingEvents (which may include references to ModeDeclarations in the role disabledMode) 
• DataReceivedEvents (which may include references to ModeDeclarations in the role disabledMode) 
• SwcModeSwitchEvents 
• RunnableEntitys 
(cid:99)(RS_SWCT_03225)

Figure 11.14: NvBlockSwComponentType and SwcInternalBehavior

[TPS_SWCT_01152] InternalBehavior does not have further attributes (cid:100) It is not expected, that such InternalBehavior do have further attributes like ExclusiveAreas, per-instance memory or inter-runnable variables, etc. (cid:99)()

[TPS_SWCT_01151] RunnableEntitys do not have further attributes (cid:100) The same condition exists for the RunnableEntitys of such InternalBehavior which shall not define further attributes, e.g. data access points (implemented by means of references from SwcInternalBehavior to VariableAccess) or ServerCallPoints. (cid:99)()

[constr_1234] Value of RunnableEntity.symbol (cid:100) The value of a RunnableEntity.symbol owned by an NvBlockSwComponentType that is triggered by an OperationInvokedEvent shall only be taken from the set of API names associated with the NvM. (cid:99)() 

For example, RunnableEntity.symbol owned by an NvBlockSwComponentType could rightfully be set to NvM_ReadBlock [31] but an arbitrary value like ReadThisBlock is not permitted. The rationale for [constr_1234] is that the RunnableEntitys that are triggered by an OperationInvokedEvent are not existing as such but are mapped to the respective function calls of the NvM. For more details of how this mapping can be achieved please refer to [7]. Please note that no restriction applies for the value of attribute RunnableEntity.symbol of any RunnableEntity owned by an NvBlockSwComponentType that is triggered by an RTEEvent other than OperationInvokedEvent.

[constr_2015] Limitation of SwcInternalBehavior of a NvBlockSwComponentType (cid:100) The SwcInternalBehavior of a NvBlockSwComponentType is only permitted to define 
• OperationInvokedEvents 
• RunnableEntitys triggered by OperationInvokedEvents (server RunnableEntitys) 
• RunnableEntitys which defines only the mandatory attributes symbol and canBeInvokedConcurrently 
• PortAPIOptions defining PortDefinedArgumentValues 
• TimingEvents (which may include references to ModeDeclarations in the role disabledMode) 
• DataReceivedEvents (which may include references to ModeDeclarations in the role disabledMode) 
• SwcModeSwitchEvents 
• RunnableEntitys triggered by TimingEvents 
• RunnableEntitys triggered by DataReceivedEvents 
• RunnableEntitys triggered by SwcModeSwitchEvents 
(cid:99)()

[constr_1309] Existence of NvBlockDescriptor.timingEvent (cid:100) The attribute NvBlockDescriptor.timingEvent shall exist if and only if the NvBlockDescriptor.nvBlockNeeds.storeCyclic exists and is set to the value true. (cid:99)() 

Note that there is a conceptual connection between the values of the two attributes NvBlockDescriptor.timingEvent.period and SwcServiceDependency.serviceNeeds.cyclicWritingPeriod. Specifically, the SwcServiceDependency.serviceNeeds.cyclicWritingPeriod represents a requirement and the NvBlockDescriptor.timingEvent.period is supposed to fulfill the requirement.

[TPS_SWCT_01585] Relevance of NvBlockDescriptor.timingEvent.period (cid:100) For any given NvBlockDescriptor, the value of the attribute NvBlockDescriptor.nvBlockNeeds.cyclicWritingPeriod shall be ignored and the value of NvBlockDescriptor.timingEvent.period shall be taken to specify the effective writing frequency for cyclic storage. (cid:99)(RS_SWCT_03225)

#@SECTION: 12 Software Component Documentation
#@CLASS: SwComponentDocumentation
#@CLASS: Chapter
AUTOSAR supports documentation of software component types by adopting the principles of ASAM-FSX [43] Standard to AUTOSAR. With AUTOSAR Release 4.0 the AUTOSAR XML schema provides support for integrated and well structured documentation. More details about the AUTOSAR Documentation Support Concept can be found in the AUTOSAR Generic Structure Template [12].

[TPS_SWCT_01062] Documentation of software-components (cid:100) As shown in figure 12.1, the documentation of a software component is composed of several chapters. Some chapters are predeﬁned, describing the component from the perspective of different activities performed on the component like testing it (swTestDesc), maintaining it (swMaintenanceNotes), calibrating it (swCalibrationNotes) or performing diagnostic (swDiagnosticsNotes) on the component. (cid:99)(RS_SWCT_02110, RS_SWCT_03230)

Two other predeﬁned chapters describe the component (swFeatureDesc) and deﬁne its physical functionality (swFeatureDef). In order to describe additional aspects of a software component, an arbitrary number of free chapters can be deﬁned.

The predeﬁned chapters typically provide informal guideline (e.g., recommendation) or documentation. Formal information can be captured using special data groups [12] or annotating documentation construct with semantic information. This could be used to extend the predeﬁned chapters or in separate free chapters.

Note that the documentation of a software component can be stored in a different ﬁle than the component itself (i.e., it is (cid:28)atpSplitable(cid:29) from the component).

Each of the predeﬁned and free chapters follows the (cid:28)atpVariation(cid:29) stereotype to support variant handling (see [12]) on the documentation at the chapter level. These variation points have a post-build as latest binding time, because the decision to include or exclude a chapter as well as the decision which variant of this chapter should be included can be made when the component has been built.

Figure 12.1: Software component documentation

Table 12.1: SwComponentDocumentation

#@SECTION: 13 Rapid Prototyping Scenarios
#@SECTION: 13.1 Deﬁnition of Rapid Prototyping Scenario
#@CLASS: RapidPrototypingScenario
#@CLASS: RptContainer
#@CLASS: RptHook

A Rapid Prototyping Scenario consist out of two main aspects: The description of the byPassPoints and the relation to a rptHook. A Rapid Prototyping Scenario is structured by means of RptContainers. The correct usage of RptContainer structure is described in 13.2.

Figure 13.1: Rapid Prototyping Scenario

Table 13.1: RapidPrototypingScenario

Table 13.2: RptContainer

Table 13.3: RptHook

[TPS_SWCT_02046] byPassPoint specifies the rapid prototyping capability (cid:100) The byPassPoints are used to describe the preparation of the host ECU. At the byPassPoints the host ECU shall be capable to communicate with a RPT System in order to support the execution of the rapid prototyping algorithms with the original data calculated by the host system and to replace dedicated results of the host system by the results of the rapid prototyping algorithm. (cid:99)(RS_SWCT_03280)

[TPS_SWCT_02047] rptHook specifies the link to rapid prototyping algorithm (cid:100) The rptHook describes the link between the byPassPoint and the rapid prototyping algorithm. If the rapid prototyping algorithm is described as an AUTOSAR Software Component the rptArHook reference is applicable. Otherwise the definition of a codeLabel and optionally mcdIdentifier shall be used. (cid:99)(RS_SWCT_03280)

In order to describe an RPT system as AUTOSAR software component a System with the category RPT_SYSTEM shall be defined.

[constr_2054] Valid targets of rptSystem (cid:100) The System referenced in the role rptSystem shall be of category RPT_SYSTEM. (cid:99)()

#@SECTION: 13.2 Usage of RptContainers on M1
#@CLASS: AsynchronousServerCallResultPoint
#@CLASS: AtomicSwComponentType
#@CLASS: DataPrototype
#@CLASS: ExternalTriggeringPoint
#@CLASS: InternalTriggeringPoint
#@CLASS: ModeAccessPoint
#@CLASS: ModeSwitchPoint
#@CLASS: ParameterAccess
#@CLASS: RapidPrototypingScenario
#@CLASS: RunnableEntity
#@CLASS: ServerCallPoint
#@CLASS: SwComponentPrototype
#@CLASS: VariableAccess
#@CLASS: PortPrototype
#@CLASS: RptContainer
#@CLASS: System

The RptContainer structure on M1 shall follow the M1 structure of the Software Component Descriptions. The category attribute denotes which level of the Software Component Description is annotated.

The following values of the attribute category are predefined by the AUTOSAR standard:

Table 13.4: Category of RptContainers
<-------------- multimodal context 


| Category | Meaning | Specific properties |
|----------|---------|-------------------|
| SW_COMPONENT_PROTOTYPE | Adds one SwComponentPrototype to an RapidPrototypingScenario. | The byPassPoint and rptArHook shall reference a SwComponentPrototypes. |
| DATA_PROTOTYPE | Adds one instance of a DataPrototype to an RapidPrototypingScenario. | The byPassPoint and rptArHook shall reference a DataPrototype instances in PortPrototypes |
| RUNNABLE_ENTITY | Adds one RunnableEntity to an RapidPrototypingScenario. | The byPassPoint and rptArHook shall reference a RunnableEntity instances. |
| ACCESS_POINTS | Adds one VariableAccess, ParameterAccess, ServerCallPoint, AsynchronousServerCallResultPoint, InternalTriggeringPoint, ModeSwitchPoint, ModeAccessPoint or ExternalTriggeringPoint to an RapidPrototypingScenario. | The byPassPoint and rptArHook shall reference a VariableAccess, ParameterAccess, ServerCallPoint, AsynchronousServerCallResultPoint, InternalTriggeringPoint, ModeSwitchPoint, ModeAccessPoint or ExternalTriggeringPoint instances. |
------------------------>

[constr_2055] Valid targets of byPassPoint and rptHook reference (cid:100) Depending on the category value the targets of byPassPoint and rptHook references are restricted according table 13.4. (cid:99)()

Hereby, the following semantic applies:

[TPS_SWCT_02048] Implicit SwComponentPrototype selection for Rapid Prototyping Scenario (cid:100) If a SwComponentPrototype is referenced in the role byPassPoint by a RptContainer without further "Sub" rptContainer all RTE Interfaces of the AtomicSwComponentType shall be able to support a connection to a rptHook. (cid:99)(RS_SWCT_03280)

[TPS_SWCT_02049] Implicit RunnableEntity selection for Rapid Prototyping Scenario (cid:100) If a RunnableEntity is referenced in the role byPassPoint by a RptContainer without further "Sub" rptContainer all RTE Interfaces of the RunnableEntity shall be able to support a connection to a rptHook. (cid:99)(RS_SWCT_03280)

[TPS_SWCT_02050] Explicit access point selection for Rapid Prototyping Scenario (cid:100) If a VariableAccess, ParameterAccess, ServerCallPoint, AsynchronousServerCallResultPoint, InternalTriggeringPoint, ModeSwitchPoint, ModeAccessPoint or ExternalTriggeringPoint is referenced in the role byPassPoint by a RptContainer only RTE Interfaces related to the specific access point are required be able to support a connection to a rptHook. (cid:99)(RS_SWCT_03280)

[TPS_SWCT_02051] Explicit DataPrototype selection for Rapid Prototyping Scenario (cid:100) If a DataPrototype instances in a PortPrototypes is referenced in the role byPassPoint by a RptContainer only RTE Interfaces related to the specific DataPrototype are required be able to support a connection to a rptHook. (cid:99)(RS_SWCT_03280)

[constr_2056] Consistency of RapidPrototypingScenario with respect to rptSystem and rptArHook references (cid:100) Within one RapidPrototypingScenario all rptSystem references shall point to instances in one and only one System and if existent all rptArHook shall point to instances in one other and only one other System. (cid:99)()

#@SECTION: 13.3 Usage of atpSplitable for RptContainers on M1
#@CLASS: RptContainer
#@CLASS: RptHook
#@CLASS: SwComponentPrototype
#@CLASS: VariableAccess

In order to support the later definition of the RptHooks, which may require as well the detailed specification byPassPoints, the aggregation of RptContainer and RptHook is (cid:28)atpSplitable(cid:29).

[TPS_SWCT_02052] Definition of Rapid Prototyping Scenario is splittable (cid:100) Aggregation of RptContainer, byPassPoint and rptHook using stereotype (cid:28)atpSplitable(cid:29). By this means it is possible to generally specify the definition the RptHooks in a later process step. (cid:99)(RS_SWCT_03280)

Please note that the later specification of RptHooks may require additional byPass Points as well to show their relationship to lower level elements in a component description, such as VariableAccess where in contrast the byPassPoints may only specified on higher level elements such as SwComponentPrototypes in a first step.

#@SECTION: 13.4 Modiﬁcations of the Meta-Model for supporting the RPT sce
#@CLASS: ExternalTriggeringPoint
#@CLASS: ExternalTriggeringPointIdent
#@CLASS: IdentCaption
#@CLASS: ModeAccessPoint
#@CLASS: ModeAccessPointIdent
#@CLASS: Referrable


The implementation of the rapid prototyping scenario implies the definition of access points (see table 13.4). To be able to fulfill this role, the access points shall be represented by meta-classes derived from Referrable.

Most candidates for becoming access points are already inheriting from Referrable and therefore do not require further treatment (see Figure 13.2). Two meta-classes in this collection, however, are not derived from Referrable:

• ExternalTriggeringPoint
• ModeAccessPoint

It is not feasible to fix this issue by simply letting the two meta-classes inherit from Referrable because this would break the backwards compatibility of the AUTOSAR XML Schema(Because in this case the shortName becomes mandatory.). Therefore, a different approach (as sketched in Figure 13.2) has been implemented.

Figure 13.2: Access Points used in the context of the Rapid Prototyping Scenario

A new meta-class IdentCaption is created that introduces the capabilities of the meta-class Identifiable (that, in turn, inherits from Referrable) to its subclasses, ModeAccessPointIdent and ExternalTriggeringPointIdent.

These, in turn, are optionally(Again, this is necessary to not break the backwards compatibility) aggregated in the role ident by ModeAccessPoint, resp. in the role ident by meta-class ExternalTriggeringPoint.

Table 13.5: IdentCaption

Table 13.6: ModeAccessPointIdent

 ExternalTriggeringPointIdent

The following (simplified) listing 13.1 sketches the usage of the meta-class IdentCaption for the purpose of effectively allowing references to a ModeAccessPoint.

Listing 13.1: Example for the definition of a RPT scenario
<AR-PACKAGE>
<SHORT-NAME>IC_Example</SHORT-NAME>
<ELEMENTS>
<APPLICATION-SW-COMPONENT-TYPE>
<SHORT-NAME>ASCT</SHORT-NAME>
<INTERNAL-BEHAVIORS>
<SWC-INTERNAL-BEHAVIOR>
<SHORT-NAME>IB</SHORT-NAME>
<RUNNABLES>
<RUNNABLE-ENTITY>
<SHORT-NAME>RE</SHORT-NAME>
<MODE-ACCESS-POINTS>
<MODE-ACCESS-POINT>
<IDENT>
<SHORT-NAME>ident</SHORT-NAME>
</IDENT>
</MODE-ACCESS-POINT>
</MODE-ACCESS-POINTS>
</RUNNABLE-ENTITY>
</RUNNABLES>
</SWC-INTERNAL-BEHAVIOR>
</INTERNAL-BEHAVIORS>
</APPLICATION-SW-COMPONENT-TYPE>
<COMPOSITION-SW-COMPONENT-TYPE>
<SHORT-NAME>CSCT</SHORT-NAME>
<COMPONENTS>
<SW-COMPONENT-PROTOTYPE>
<SHORT-NAME>SCP</SHORT-NAME>
<TYPE-TREF DEST="APPLICATION-SW-COMPONENT-TYPE">/IC_Example/ASCT</TYPE-TREF>
</SW-COMPONENT-PROTOTYPE>
</COMPONENTS>
</COMPOSITION-SW-COMPONENT-TYPE>
<RAPID-PROTOTYPING-SCENARIO>
<SHORT-NAME>rptScenario</SHORT-NAME>
<RPT-CONTAINERS>
<RPT-CONTAINER>
<SHORT-NAME>rptContainer</SHORT-NAME>
<BY-PASS-POINT-IREFS>
<BY-PASS-POINT-IREF>
<CONTEXT-ELEMENT-REF DEST="SW-COMPONENT-PROTOTYPE">/IC_Example/CSCT/SCP</CONTEXT-ELEMENT-REF>
<TARGET-REF DEST="MODE-ACCESS-POINT-IDENT">/IC_Example/ASCT/IB/RE/ident</TARGET-REF>
</BY-PASS-POINT-IREF>
</BY-PASS-POINT-IREFS>
</RPT-CONTAINER>
</RPT-CONTAINERS>
</RAPID-PROTOTYPING-SCENARIO>
</ELEMENTS>
</AR-PACKAGE>