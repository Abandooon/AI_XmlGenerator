#@SECTION: 4 Details: Software Components, Ports, and Interfaces
#@SECTION: 4.1 Introduction
#@CLASS: ClientServerInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: SenderReceiverInterface

The specification of the Virtual Functional Bus (VFB) [3] explains the main communication paradigms for communication among software-components: client/server for operation-based communication, and sender/receiver for data-based communication.

The nature of the two communication paradigms is quite different, and so is the modeling of SenderReceiverInterfaces and ClientServerInterfaces and their related meta-classes.

[TPS_SWCT_01516] PortInterface describes the static structure of information interchange (cid:100) PortInterfaces are limited to the description of the static structure of the exchanged information; the dynamic attributes (please refer to chapter 4.5) relevant for communication are attached to PortPrototypes. (cid:99)(RS_SWCT_00010, RS_SWCT_00080, RS_SWCT_00110, RS_SWCT_02030, RS_SWCT_03010)

#@SECTION: 4.2 Port Interface Details

#@SECTION: 4.2.1 Introduction
#@CLASS: ApplicationSwComponentType
#@CLASS: ComplexDeviceDriverSwComponentType
#@CLASS: DataPrototype
#@CLASS: EcuAbstractionSwComponentType
#@CLASS: ImplementationDataType
#@CLASS: NvBlockSwComponentType
#@CLASS: ParameterSwComponentType
#@CLASS: PortInterface
#@CLASS: SensorActuatorSwComponentType
#@CLASS: ServiceSwComponentType
#@CLASS: SwBaseType

The usage of value encodings (for more information please refer to section 5.2.6) is limited within the context of PortInterfaces.

[constr_1045] Supported value encodings for SwBaseType in the context of PortInterfaces (cid:100) The supported value encodings for the usage within a Port Interface are:
• 2C: Two’s complement
• IEEE754: ﬂoating point numbers
• ISO-8859-1: ASCII-Strings
• ISO-8859-2: ASCII-Strings
• WINDOWS-1252: ASCII-Strings
• UTF-8: UCS Transformation Format 8
• UTF-16: Character encoding for Unicode code points based on 16 bit code units [16]
• UCS-2: Universal Character Set 2
• NONE: Unsigned Integer
• BOOLEAN: This represents an integer to be interpreted as boolean. (cid:99)()

[constr_1046] Applicability of [constr_1045] (cid:100) [constr_1045] applies only if the value of the attribute isService is set to false. (cid:99)()

[constr_1295] PortInterfaces and category DATA_REFERENCE (cid:100) A DataPrototype deﬁned in the context of a PortInterface used by an ApplicationSwComponentType or SensorActuatorSwComponentType that is (after potential indirections via TYPE_REFERENCE are resolved) either typed by or mapped to an ImplementationDataType of category DATA_REFERENCE shall only be used if either the provider or the requester of the information represents a ServiceSwComponentType, a ComplexDeviceDriverSwComponentType, a ParameterSwComponentType, or an NvBlockSwComponentType, or the EcuAbstractionSwComponentType. (cid:99)()

Note: [constr_1295] corresponds to [SWS_RTE_07670].

#@SECTION: 4.2.2 Sender Receiver Communication
#@CLASS: AssemblySwConnector
#@CLASS: DataInterface
#@CLASS: DataPrototype
#@CLASS: DelegationSwConnector
#@CLASS: Identifiable
#@CLASS: InvalidationPolicy
#@CLASS: NvDataInterface
#@CLASS: PassThroughSwConnector
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: PRPortPrototype
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: VariableDataPrototype
#@ENUM: HandleInvalidEnum

[TPS_SWCT_01114] SenderReceiverInterface (cid:100) SenderReceiverInterfaces allow for the specification of the typically asynchronous communication pattern where a sender provides data that is required by one or more receivers.

While the actual communication takes place via the respective PortPrototypes, a SenderReceiverInterface allows for formally describing what kind of information is sent and received. (cid:99)()

A sender/receiver interface declares a number of data elements to be sent and received.

Table 4.1: SenderReceiverInterface

Specifies whether the component can actively invalidate a particular dataElement. If no invalidationPolicy points to a dataElement this is considered to yield the identical result as if the handleInvalid attribute was set to dontInvalidate.

Table 4.2: InvalidationPolicy

Enumeration HandleInvalidEnum Strategies of handling the reception of invalidValue. Description Invalidation is switched off. Replace a received invalidValue. The replacement value is sourced from the externalReplacement. The application software is supposed to handle signal invalidation on RTE API level either by DataReceiveErrorEvent or check of error code on read access. Replace a received invalidValue. The replacement value is specified by the initValue.

Table 4.3: HandleInvalidEnum

A SenderReceiverInterface focuses on the description of information items represented by VariableDataPrototypes (see section 5.3). A VariableDataPrototype aggregated in the role of dataElement represents an atomic piece of information transmitted among PortPrototypes typed by a SenderReceiverInterface.

[TPS_SWCT_01115] invalidationPolicy (cid:100) An invalidationPolicy specifies whether the sending component can actively invalidate a particular dataElement and which strategy of handling the reception of invalidValue on the receiver side shall be implemented. (cid:99)()

Further information about the related concept of an invalidValue is provided in chapter 5.4.2

Figure 4.1: dataElements of a SenderReceiverInterface

Note that a SenderReceiverInterface provides a name space for the definition of VariableDataPrototypes. In terms of the AUTOSAR meta-model this aspect is indicated by the inheritance relation to DataPrototype (which in turn inherits from Identifiable). Please find more information on the creation of name spaces in [12].

[TPS_SWCT_01116] swImplPolicy (cid:100) The swImplPolicy (see section 5.4) indicates the way how a VariableDataPrototype shall be processed at the receiver's side. If set to queued the semantics is that the corresponding VariableDataPrototype needs to be added to a queue (or in other words: a FIFO data structure) from which it is later consumed by the actual receiver software-component. (cid:99)()

[constr_1200] Queued communication is not applicable for dataElements owned by PRPortPrototype (cid:100) The swImplPolicy shall not be set to queued for any dataElement owned by a PRPortPrototype. (cid:99)()

[TPS_SWCT_01176] last-is-best semantics for sender-receiver communication (cid:100) If swImplPolicy is set to any other valid value of SwImplPolicyEnum then last is best semantics applies. (cid:99)()

Please note that the definition of VariableDataPrototype may possibly come very close to the reader's idea of a signal. However, different kinds of signals have a specific meaning in the AUTOSAR concept, especially in the context of the AUTOSAR System Template [11].

[TPS_SWCT_01117] Communication patterns for sender-receiver communication (cid:100) PortPrototypes typed by a SenderReceiverInterface may be connected to establish a 1:n (i.e. one sender, multiple receivers) communication relationship. It is also possible to establish a n:1 (i.e. many senders, one receiver) communication pattern. (cid:99)()

[constr_1033] Communication scenarios for sender/receiver communication (cid:100) For sender/receiver communication, it is not allowed to create a communication scenario where n sender are connected to m receivers where m and n are both greater than 1. (cid:99)()

Factually, [constr_1033] is not applicable to a scenario where several PRPortPrototypes are connected by a chain of AssemblySwConnectors or PassThroughSwConnectors.

[constr_1202] Supported connections by AssemblySwConnector for PortPrototypes typed by a SenderReceiverInterface or NvDataInterface (cid:100) For the modeling of AssemblySwConnectors between PortPrototypes typed by a SenderReceiverInterface or NvDataInterface, only the connections documented in Table 4.4 are supported by AUTOSAR. (cid:99)()


<-------------- multimodal context 
|                     | RPortPrototype | PPortPrototype | PRPortPrototype |
|---------------------|---------------|---------------|-----------------|
| **RPortPrototype**  | No            | Yes           | Yes             |
| **PPortPrototype**  | Yes           | No            | Yes             |
| **PRPortPrototype** | Yes           | Yes           | No              | ---------------------->
Table 4.4: Supported connections for PortPrototypes typed by a SenderReceiverInterface or NvDataInterface

[constr_1203] Supported connections by DelegationSwConnector for PortPrototypes typed by a SenderReceiverInterface or NvDataInterface (cid:100) For the modeling of DelegationSwConnectors between PortPrototypes typed by a SenderReceiverInterface or NvDataInterface, only the connections documented in Table 4.5 are supported by AUTOSAR. (cid:99)()


<-------------- multimodal context 
```markdown
| innerPort       | outerPort       |               |                  |
|-----------------|-----------------|---------------|------------------|
|                 | RPortPrototype  | PPortPrototype| PRPortPrototype  |
| RPortPrototype  | Yes             | No            | Yes              |
| PPortPrototype  | No              | Yes           | Yes              |
| PRPortPrototype | Yes             | Yes           | Yes              |
``` ---------------------->
Table 4.5: Supported connections for PortPrototypes typed by a SenderReceiverInterface or NvDataInterface

#@SECTION: 4.2.3 Client Server Communication
#@CLASS: ClientServerOperation

The underlying semantics of a client/server communication is that a client may initiate the execution of an operation by a server that supports the operation. The server executes the operation and, when completed, it provides the client with the result (synchronous operation call) or else the client checks for the completion of the operation by itself (asynchronous operation call).

[constr_1037] Client shall not be connected to multiple servers (cid:100) A client shall not be connected to multiple servers such that an operation call would be handled by more than one server. (cid:99)()

#@SECTION: 4.2.3.1 Client Server Interface
#@CLASS: ArgumentDataPrototype
#@ENUM: ArgumentDirectionEnum
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@ENUM: ServerArgumentImplPolicyEnum
#@CLASS: AutosarDataPrototype
#@CLASS: AutosarDataType
#@CLASS: ApplicationArrayElement
#@CLASS: PortPrototype
#@CLASS: RunnableEntity
#@CLASS: OperationInvokedEvent
#@CLASS: ArgumentImplPolicy
#@CLASS: ImplementationDataType
#@CLASS: ClientServerInterface
#@CLASS: ModeSwitchInterface
#@CLASS: TriggerInterface
#@CLASS: AssemblySwConnector
#@CLASS: DelegationSwConnector

A ClientServerInterface, to some extent, is a counterpart to the Sender ReceiverInterface. Instead of defining pieces of information to be transferred among software components, a ClientServerInterface defines a collection of ClientServerOperations.


Table 4.6: ClientServerInterface

Figure 4.2: ClientServerOperations of a ClientServerInterface

[TPS_SWCT_01118] ClientServerInterface (cid:100) As depicted in Figure 4.2, a ClientServerInterface is composed of ClientServerOperations, i.e. a ClientServerOperation cannot be reused in the context of a different ClientServerInterface (cid:99)()

[TPS_SWCT_01106] ClientServerOperation (cid:100) A ClientServerOperation consists of 0..* ArgumentDataPrototypes. The latter may be
• passed to the operation (i.e. the direction is "in")
• passed to and returned from the operation (i.e. the direction is "inout")
• returned from the operation (i.e. the direction is "out")
The aggregation represents a variation point. (cid:99)(RS_SWCT_03141)

Table 4.7: ClientServerOperation

Table 4.8: ArgumentDataPrototype

[TPS_SWCT_01119] Direction of ArgumentDataPrototypes (cid:100) To cover these cases, ArgumentDataPrototype defines an attribute direction, possible values are in (pass to operation), out (return from operation), and inout (pass to and return from operation). (cid:99)()

In many common programming languages (like C), an operation is yet another data type. This makes it for example possible to pass a reference to an operation as an argument to another operation. This is not allowed in the AUTOSAR concept.

[TPS_SWCT_01517] ClientServerOperation cannot be passed as a reference (cid:100) It is not possible to pass a reference to a ClientServerOperation as an ArgumentDataPrototype in another ClientServerOperation. (cid:99)()

Essentially, all ArgumentDataPrototypes in a ClientServerOperation can be passed (conceptually) by value (from the client to the server and/or from the server to the client depending on the direction of the ArgumentDataPrototype).

[TPS_SWCT_01120] Client needs to provide ArgumentDataPrototypes (cid:100) When the client invokes an operation, it needs to provide a value for each ArgumentDataPrototype that is of direction in or inout. (cid:99)()

[TPS_SWCT_01121] Pass correct data type (cid:100) The value passed to an ArgumentDataPrototype of direction in or inout needs to be of the corresponding Datatype. (cid:99)()

[TPS_SWCT_01122] Synchronous call of ClientServerOperation (cid:100) In the case of synchronous operation call, the client expects to receive a response to the invocation of the operation. As part of the response, it receives a value (of the correct AutosarDataType) for each ArgumentDataPrototype that is of direction out or inout. (cid:99)()

Table 4.9: ArgumentDirectionEnum

Each ClientServerOperation provides a name space for its ArgumentDataPrototypes and therefore has a unique identifier which identifies the operation within the corresponding ClientServerInterface. The ClientServerOperations have no ordering within a ClientServerInterface (there is no such thing as the "first" operation).

[TPS_SWCT_01123] No default values for ArgumentDataPrototypes (cid:100) It is not possible to define default values for ArgumentDataPrototypes defined in the context of a ClientServerOperation. Default values might lead to complicated mappings to programming languages. (cid:99)()

[TPS_SWCT_01124] Definition of ArgumentDataPrototypes within the context of a ClientServerOperation is ordered (cid:100) In contrast to the unordered relationship of ClientServerInterface to ClientServerOperation, the definition of ArgumentDataPrototypes within the context of a ClientServerOperation is ordered, i.e. a ClientServerOperation may have a first argument. (cid:99)()

Please note that ArgumentDataPrototype inherits from AutosarDataPrototype and therefore has a reference to a concrete AutosarDataType. The RTE Generator uses the referred AutosarDataTypes to determine the data types of the arguments depending on the value of the attribute ArgumentDataPrototype.serverArgumentImplPolicy.

Table 4.10: ServerArgumentImplPolicyEnum

Please note that the scenario described in [TPS_SWCT_01125] is depicted in Figure 4.3.

[TPS_SWCT_01125] serverArgumentImplPolicy (cid:100) The option useArrayBaseType is intended to implement "Server Runnables" which are able to handle array typed arguments of different length. In this case the software component does have several Server Ports. At least one argument of the ClientServerOperations is typed by AutosarDataTypes of category ARRAY but the length of the arrays defined by ApplicationArrayElement.maxNumberOfElements respectively arraySize might be different for the individual Server Ports. All ClientServerOperations in the PortPrototypes are triggering the same RunnableEntity with OperationInvokedEvents. If the serverArgumentImplPolicy is set to useArrayBaseType the RTE Generator does not require the compatibility of ClientServerOperations for such ArgumentDataPrototypes and uses the baseType of the array as the argument's data type instead of the array data type with a particular length. The option useVoid is available to implement Server RunnableEntitys which are able to handle arbitrary typed arguments of different length - typically of category STRUCTURE. The design of the software component implementing the server is similar as explained for useArrayBaseType. If the serverArgumentImplPolicy is set to useVoid the RTE Generator does not require the compatibility of ClientServerOperations for such ArgumentDataPrototypes and uses void as the argument data type. (cid:99)()

[constr_1297] Applicability of serverArgumentImplPolicy set to useArrayBaseType (cid:100) The value of the attribute ArgumentDataPrototype.serverArgumentImplPolicy shall only be set to useArrayBaseType for an ArgumentDataPrototype that is (after all TYPE_REFERENCEs are resolved) either an ImplementationDataType of category ARRAY or an ApplicationDataType mapped to (after all TYPE_REFERENCEs are resolved) an ImplementationDataType of category ARRAY. (cid:99)()

[constr_1286] serverArgumentImplPolicy and ArgumentDataPrototype typed by primitive data types (cid:100) The value of the attribute ArgumentDataPrototype.serverArgumentImplPolicy shall not be set to useVoid for an ArgumentDataPrototype of direction in that is typed by an AutosarDataType that boils down to a primitive C data type (see [TPS_SWCT_01565]). (cid:99)()


<-------------- multimodal context 
The diagram shows three AtomicSwComponentType “clients” each with a RequiredPort “C” typed by ClientServerInterface {A}, {B}, or {C}, all assembled via AssemblySwConnectors (with multiplicities n=2,3,4) to three ProvidedPorts on a CompositionSwComponentType “server” that hosts a single Server RunnableEntity. It exemplifies how multiple clients invoke a common server runnable through distinct interfaces with specified connector multiplicities.

• Component hierarchy  
  – Three leaf AtomicSwComponentType clients  
  – One CompositionSwComponentType server containing a Server RunnableEntity  

• Ports & interfaces  
  – Clients: AbstractRequiredPortPrototype “C” typed {A}, {B}, {C}  
  – Server: AbstractProvidedPortPrototype instances typed {A}, {B}, {C}  
  – AssemblySwConnectors link matching ports  

• Data flow  
  – Clients invoke server operations via Assembly connectors  
  – Dashed lines denote RunnableEntity interactions  

• Key AUTOSAR concepts  
  – AbstractRequired/ProvidedPortPrototype  
  – ClientServerInterface with multiplicity “n” on AssemblySwConnector  
  – RunnableEntity inside CompositionSwComponentType  

• Scenario  
  – Multi-client access pattern where 2, 3, and 4 client instances call server interfaces A, B, C respectively to share a central service. ---------------------->
Figure 4.3: Example for [TPS_SWCT_01125]

Please note that the server RunnableEntity needs information about the currently used array length respectively structure size by usage of additionally arguments passed by the Client or via PortDefinedArgumentValue. Note further that a ClientServerInterface does not define any timing information (how quickly the client expects a response of the server). It does not define how the threading works (if the client for example blocks until the response comes back from the server). It also does not define explicitly how information is passed between an implementation of the client and the server and the underlying RTE (for example: through "pointers" or "by value").

[constr_1204] Supported connections by AssemblySwConnector for Port Prototypes typed by a ClientServerInterface, ModeSwitchInterface, or TriggerInterface (cid:100) For the modeling of AssemblySwConnectors between PortPrototypes typed by a ClientServerInterface, ModeSwitchInterface, or TriggerInterface, only the connections documented in Table 4.11 are supported by AUTOSAR. (cid:99)()


<-------------- multimodal context 
|                     | RPortPrototype | PPortPrototype | PRPortPrototype |
|---------------------|---------------:|---------------:|----------------:|
| **RPortPrototype**  | No             | Yes            | Yes             |
| **PPortPrototype**  | Yes            | No             | No              |
| **PRPortPrototype** | Yes            | No             | No              | ---------------------->
Table 4.11: Supported connections for PortPrototypes typed by a ClientServerInterface, ModeSwitchInterface, or TriggerInterface

[constr_1205] Supported connections by DelegationSwConnector for Port Prototypes typed by a ClientServerInterface, ModeSwitchInterface, or TriggerInterface (cid:100) For the modeling of DelegationSwConnectors between PortPrototypes typed by a ClientServerInterface, ModeSwitchInterface, or TriggerInterface, only the connections documented in Table 4.12 are supported by AUTOSAR. (cid:99)()


<-------------- multimodal context 
```markdown
| innerPort      | outerPort        |                |                   |
|                | RPortPrototype   | PPortPrototype | PRPortPrototype   |
|----------------|------------------|----------------|-------------------|
| RPortPrototype | Yes              | No             | No                |
| PPortPrototype | No               | Yes            | No                |
``` ---------------------->
Table 4.12: Supported connections for PortPrototypes typed by a ClientServerInterface, ModeSwitchInterface, or TriggerInterface

#@SECTION: 4.2.3.2 Error Handling in Client/Server Communication
#@CLASS: ApplicationError
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: SwComponentType

This section describes the handling of errors occurring either within an application software-component or during the communication across the VFB [3]. Errors that are created and consumed by basic software modules are not in the scope of this document and therefore will not be discussed.

Therefore, errors in the scope of this document are divided into two simple classes:
• infrastructure errors and
• application errors.

A software-component implementation uses RTE API methods to communicate with other software-components. During this communication certain errors can occur as a result of infrastructure faults, like a bus is not working, or an expected data value was not arriving in time.

These errors are listed in the RTE specification [2], as they are an inherent feature of the infrastructure provided by the VFB. Software-components will therefore typically not raise infrastructure errors on their own.

Instead, AUTOSAR the basic software and the RTE will determine infrastructure faults and communicate the corresponding error codes to the relevant software-components.

Figure 4.4: Application error meta-model

[TPS_SWCT_01491] AUTOSAR system does not need to explicitly describe infrastructure errors (cid:100) As the fixed set of infrastructure errors is defined as an implicit part of the VFB, a developer of an AUTOSAR system does not need to explicitly describe these. It is assumed that these might occur at run-time and application developers should take measures to handle them. (cid:99)()

Application errors, on the other hand, are specific to the functionality or information that is described in form of a PortInterface. It is not possible to define such errors up front, instead they are defined at design time of a certain PortInterface. In principle, such ApplicationErrors could be part of all kinds of PortInterfaces.

[TPS_SWCT_01490] AUTOSAR supports ApplicationErrors only for ClientServerInterfaces (cid:100) As of now, AUTOSAR supports (as depicted by Figure 4.4) ApplicationErrors only for ClientServerInterfaces. (cid:99)()

[constr_1102] ApplicationError in the scope of one SwComponentType (cid:100) A SwComponentType may have PortPrototypes typed by different PortInterfaces with equal shortName but conflicting ApplicationErrors. ApplicationErrors are considered conflicting if ApplicationErrors with the same shortName do have different errorCodes. (cid:99)()

[constr_1108] Value of ApplicationError.errorCode (cid:100) The value of ApplicationError.errorCode shall not exceed the closed interval 1 .. 63. The following exception applies: only in case possibleError is supposed to represent E_OK the value 0 shall be be allowed. (cid:99)()

By [constr_1108] it is possible to ensure that only the six least significant bits of a return value shall be used for indicating an application error.

Table 4.13: ApplicationError

Consequently, ClientServerOperations may be associated with a number of ApplicationErrors they possibly raise. These errors are defined as part of the ClientServerInterface.

[constr_1038] Reference to ApplicationError (cid:100) A possibleError referenced by a ClientServerOperation shall be owned by the ClientServerInterface that also owns the ClientServerOperation. (cid:99)()

#@SECTION: 4.2.4 External Trigger Event Communication
#@CLASS: MultidimensionalTime
#@CLASS: Trigger
#@CLASS: TriggerInterface
#@CLASS: SwConnectors
#@CLASS: PPortPrototypes
#@CLASS: RPortPrototype
#@CLASS: 

[TPS_SWCT_01196] Semantics of an external trigger event communication (cid:100) The underlying semantics of an external trigger event communication is that a trigger source may initiate the execution of RunnableEntitys in the connected trigger sinks. Typically (but not necessarily) these RunnableEntitys are executed in a sequential order. (cid:99)()

[TPS_SWCT_01197] TriggerInterface (cid:100) The TriggerInterface defines a set of Trigger to be communicated between software-components. The Trigger represents a special kind of events at which occurrence the trigger sinks shall react in a particular manner. (cid:99)()

Table 4.14: TriggerInterface
Table 4.15: Trigger
Table 4.16: MultidimensionalTime
Figure 4.5: Trigger of a TriggerInterface

As illustrated in Figure 4.5, a TriggerInterface is composed of Trigger.

[TPS_SWCT_01198] Period for periodic triggering (cid:100) A Trigger can optionally define a period for periodic triggering. It is expressed via the meta-class MultidimensionalTime in terms of time or angle. Note that the main use case for this is to specify the properties if the trigger is coming from the Basic Software e.g. from a Complex Driver, it is not used as an input for the RTE generator. (cid:99)()

Apart from this, a TriggerInterface does not define any timing information (e.g. how quickly the source expects a reaction of the sinks). This is property of the timing information in the templates.

[constr_1104] Trigger sink and trigger source (cid:100) An RPortPrototype typed by a TriggerInterface shall not be referenced by more than one SwConnectors that are in turn referencing PPortPrototypes typed by TriggerInterfaces that contain Triggers with the same shortName. (cid:99)()

[constr_1104] boils down to the requirement that trigger communication shall not be implemented in a n:1 scenario. To be clear, the n:1 scenario is not supported for trigger communication because there is no active use case for it. Support would require the implementation of queue management for Trigger communication.

[TPS_SWCT_01199] Queued processing of Triggers (cid:100) It may happen that at least tentatively a Trigger source fires Triggers faster than they can be processed on the side of the Trigger sink. To support this use case it is possible to process trigger event communication in a queued manner. In this case the Triggers are added to a queue from where the foremost trigger is dequeued and processed when the processing of the current Trigger is done. Please note that the queue size is not subject to definition in the scope of this document. The actual queue size is defined during the process of RTE configuration. The specification of whether or not a Trigger is subject to queued processing is controlled by the attribute Trigger.swImplPolicy. (cid:99)()

[constr_1169] Allowed values for Trigger.swImplPolicy (cid:100) The only allowed values for the attribute Trigger.swImplPolicy are either STANDARD (in which case the Trigger processing does not use a queue) or QUEUED (in which case the processing of Triggers positively uses a queue). (cid:99)()

For more information regarding the ability to connect different kinds of PortPrototypes typed by a TriggerInterface to each others please refer to [constr_1204] and [constr_1205].

#@SECTION: 4.2.5 Communication of Modes
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: DataTypeMappingSet
#@CLASS: DelegationSwConnector
#@CLASS: ImplementationDataType
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeRequestTypeMap
#@CLASS: ModeSwitchInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: PRPortPrototype
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: ServiceSwComponentType
#@CLASS: SwcInternalBehavior
#@CLASS: SwComponentType
#@ENUM: SwCalibrationAccessEnum
#@CLASS: VariableDataPrototype
#@CLASS: FlatInstanceDescriptor
#@CLASS: CompuMethod
#@CLASS: SwComponentPrototype
#@CLASS: ApplicationDataType

There are two distinctive use cases for the communication of modes via ports:
1. An actual mode transition can be communicated from a mode manager component to its client components to enforce a mode switch.
2. A request for a mode transition can be communicated from any component to a mode manager.

[TPS_SWCT_01087] Propagation of mode information (cid:100) For communicating a mode switch (i.e. the first use case), the Software-Component Template describes the concept of the communication of ModeDeclarationGroupPrototypes similar to the communication of VariableDataPrototypes but is uses a special type of PortInterface: the collections of ModeDeclarations that are required or provided by a SwComponentType are defined (as depicted in Figure 4.6) by means of ModeSwitchInterfaces used to type the PortPrototypes owned by the SwComponentType. (cid:99)(RS_SWCT_03203)

Due to the strong interaction with the RTE for handling the mode switches, this first use case does not allow communication across ECU boundaries:
[constr_4000] Local communication of mode switches (cid:100) Ports with ModeSwitchInterfaces cannot be connected across ECU boundaries. (cid:99)()

[constr_2049] Different ModeDeclarationGroups shall have different shortNames. (cid:100) A software component is not allowed to type multiple PortPrototypes with ModeSwitchInterfaces where the contained ModeDeclarationGroupPrototypes are referencing ModeDeclarationGroups with identical shortNames but different ModeDeclarations. (cid:99)()

Obviously, the rationale for [constr_2049] is to avoid conflicts in generated RTE files. For instance:
Two ModeDeclarationGroups with identical shortName "Foo" are defined.
ModeDeclarationGroup "Foo" contains the ModeDeclarations "X", "Y", "Z"
ModeDeclarationGroup "Foo*" contains ModeDeclarations "W", "X", "Y", "Z"
In this case a software component is only allowed to use either "Foo" or "Foo*"

Table 4.17: ModeSwitchInterface
Table 4.18: ModeDeclarationGroupPrototype

Please note that by aggregating SwCalibrationAccessEnum in the role swCalibrationAccess a ModeDeclarationGroupPrototype gains the ability to become measurable. This implies the following constraint:
[constr_1172] Allowed values of SwCalibrationAccessEnum for ModeDeclarationGroupPrototype (cid:100) The only allowed values of swCalibrationAccess aggregated by ModeDeclarationGroupPrototype are notAccessible and readOnly. (cid:99)()

Table 4.19: SwCalibrationAccessEnum

[TPS_SWCT_01566] Define literals for an MCD system in the context of a FlatInstanceDescriptor (cid:100) If ModeDeclarationGroupPrototype.swCalibrationAccess is set to readOnly a referenced FlatInstanceDescriptor.swDataDefProps may in turn refer to a CompuMethod that defines the particular literals used in the MCD system for displaying values of the the measured ModeDeclarationGroupPrototypes. (cid:99)(RS_SWCT_03203)

The existence of this use case is the reason for putting "AI" at the intersection of compuMethod and FlatInstanceDescriptor.

Another possible scenario (that does not necessarily have to be related to ModeDeclarationGroupPrototypes but to the definition of literals for MCD systems in general) is that a FlatInstanceDescriptor does not exist (e.g. because the affected piece of data exists in the basic software) but still it would be good to have the ability to define particular literals for displaying values in an MCD system.

This case can be supported by the AUTOSAR standard as well by putting "AI" at the intersection of compuMethod and McDataInstance in table 5.39.

[TPS_SWCT_01200] ModeDeclarationGroupPrototype per ModeSwitchInterface (cid:100) The multiplicity of the aggregation of ModeDeclarationGroupPrototype to ModeSwitchInterface is pragmatically limited to 1. (cid:99)(RS_SWCT_03203)

Admittedly, there would be no technical restriction to support a 0..* multiplicity but on the other hand it does not seem as if any reasonable use case for such a scenario exists. If somehow a SwComponentType would have to consider two or even more ModeDeclarationGroupPrototypes it is very likely that these would be part of different ModeSwitchInterfaces.

The containment of a ModeDeclarationGroupPrototype in a ModeSwitchInterface allows for explicitly defining SwConnectors which communicate between SwComponentPrototypes and to define service interfaces for communication with ServiceSwComponentTypes. Due to the compatibility rules of PortInterfaces (see chapter 6) each SwComponentType can rely on the availability of required mode activations.

Figure 4.6: Mode Switch Interface

Please note that each SwComponentType can define (via their PortPrototypes and ModeSwitchInterfaces) a list of required and provided ModeDeclarationGroupPrototypes.

[TPS_SWCT_01201] CompositionSwComponentType requires and provides the modes that are required or provided by its contained SwComponentPrototypes (cid:100) Eventually, a CompositionSwComponentType requires and provides the modes that are required or provided by its contained SwComponentPrototypes. The delegation of these modes from SwComponentPrototypes to the enclosing CompositionSwComponentType is explicitly described by DelegationSwConnectors. (cid:99)(RS_SWCT_03202, RS_SWCT_03203)

The formal description of a software-component does not make any assumptions about the semantics of the required and provided ModeDeclarationGroupPrototypes. It just requires and provides the ModeDeclarationGroupPrototypes by name. For more information about mode declaration refer to section 9.1.

[TPS_SWCT_01086] Request mode change (cid:100) The ability to request a mode (i.e. the second use case) is modeled on the VFB via a SenderReceiverInterface and for the RTE it is like a usual communication, that means the connector can also cross ECU boundaries and the communicated dataElements have to be based on AutosarDataTypes. (cid:99)(RS_SWCT_03202, RS_SWCT_03203)

However, for semantic consistency with the first use case, a communicated mode request shall also be mapped to a corresponding ModeDeclarationGroup. This can be defined by a mapping class as shown in figure 4.7.

The ImplementationDataType mapped to a certain ModeDeclarationGroup can then be used in a PortInterface to represent a ModeDeclaration of the associated ModeDeclarationGroup as a numerical value:
[constr_4002] Unambiguous mapping of modes to data types (cid:100) Within one DataTypeMappingSet, a ModeDeclarationGroup shall not be mapped to different ImplementationDataTypes. (cid:99)()

Figure 4.7: Mapping of modes to data types
Table 4.20: ModeRequestTypeMap

[constr_1166] Restrictions of ModeRequestTypeMap (cid:100) For every ModeDeclarationGroup referenced by a ModeDeclarationGroupPrototype used in a PortPrototype typed by a ModeSwitchInterface a ModeRequestTypeMap shall exist that points to the ModeDeclarationGroup and also to an eligible ImplementationDataType. The ModeRequestTypeMap shall be aggregated by a DataTypeMappingSet which is referenced from the SwcInternalBehavior that is owned by the ApplicationSwComponentType that also owns the PortPrototype. (cid:99)()

Figure 4.8: Big picture of mode declaration mapping

[constr_1167] ImplementationDataTypes used as ModeRequestTypeMap.implementationDataType (cid:100) The ImplementationDataType referenced by a ModeRequestTypeMap shall either be of category VALUE or of category TYPE_REFERENCE that in turn references an ImplementationDataType of category VALUE. The baseType referenced by the ImplementationDataType shall have set the value of the attribute BaseTypeDirectDefinition.baseTypeEncoding to NONE. (cid:99)()

[TPS_SWCT_01202] ApplicationDataType defines a subset of the values used in the ModeDeclarationGroup (cid:100) Please note that the corresponding ApplicationDataType is defining a subset of the values used in the ModeDeclarationGroup and the used labels may differ from the names used for the ModeDeclarations. It is in the responsibility of a system designer to maintain the data types and ModeDeclarationGroups according to the functional needs. For example, a ModeRequester may only request a subset of the available Modes (via SenderReceiverInterface or ClientServerInterface). The ModeManager may additionally decide to indicate failure. (cid:99)(RS_SWCT_03203)

For more information regarding the ability to connect different kinds of PortPrototypes typed by a ModeSwitchInterface to each other please refer to [constr_1204] and [constr_1205].

#@SECTION: 4.2.6 Parameter Communication
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RPortPrototype

Of course, the "communication" of ParameterDataPrototypes as part of a ParameterInterface does not establish an actual transmission of data.

The term is used in a conceptual meaning; and the existence of something like a ParameterInterface is justified by the mere idea of unifying the exposure of calibration parameters at the surface of a software-component on the same formal level as the exposure of other pieces of data, i.e. by means of a PortPrototype typed by a PortInterface.

[constr_1312] PortPrototypes typed by a ParameterInterface (cid:100) PortPrototypes typed by a ParameterInterface can either be PPortPrototypes or RPortPrototypes. The usage of PRPortPrototypes that are typed by a ParameterInterface is not supported. (cid:99)()

#@SECTION: 4.3 PortInterface Mapping and Data Scaling
#@CLASS: CompositionSwComponentType
#@CLASS: DataPrototypeMapping
#@CLASS: NvBlockSwComponentType
#@CLASS: PortInterface
#@CLASS: PortInterfaceMapping
#@CLASS: PortInterfaceMappingSet
#@CLASS: PortPrototype
#@CLASS: ServiceSwComponentType
#@CLASS: SubElementMapping
#@CLASS: VariableDataPrototype
#@CLASS: DataTransformation
#@CLASS: SenderReceiverInterface
#@CLASS: SwConnector
#@CLASS: ARElement

In former versions of this specification, the requirements on PortInterfaces to match each other could lead to situations where PortInterfaces that were “practically” compatible would nevertheless be rejected because of formal reasons (e.g. ShortNames of dataElements do not match).

In order to also support scenarios where the developer of a CompositionSwComponentType needs to connect PortPrototypes that would match to each others but don’t fulfill formal requirements the concept of “port interface mapping” has been introduced.

[TPS_SWCT_01158] Three cases for PortInterfaceMapping (cid:100) In general there are three different cases, where a PortInterfaceMapping is suitable.

1. Two PortPrototypes shall be connected and the PortInterface elements are compatible except the unequal shortNames. This requires a pure logical mapping of the PortInterface elements.
2. PortInterface elements are logically equivalent but the range and resolution is differently. This requires a data conversion respectively a re-scaling of the provided data and arguments to the required data and arguments range and resolution.
3. invalidationPolicy of PortInterface elements is different. This might require the implementation of different invalidation handling strategies for the same dataElement in parallel on the same ECU.
4. Two PortPrototypes shall be connected and the PortInterface elements shall be converted using the AUTOSAR data transformer approach. (cid:99)(RS_SWCT_03210)

Typically the mapping of such PortInterface is agreed once between the different component vendors and system designer in the early phase of a project.

One (prominent) use-case for item 4 in [TPS_SWCT_01158] is the interaction between the NvBlockSwComponentType and the AUTOSAR Dcm.

Specifically, the RTE will call a data transformer to convert the uint8-array representation of the diagnostic data available from a PortPrototype owned by the Dcm ServiceSwComponentType to a VariableDataPrototype owned by a PortPrototype of NvBlockSwComponentType.

For the configuration of this purpose, the applicable DataPrototypeMapping refers to a DataTransformation in the role firstToSecondDataTransformation (see Figure 4.9).

Figure 4.9: Configuration of Ecu-internal data transformation

Note that for this specific interaction between an ApplicationSwComponentType and a ServiceSwComponentType [TPS_SWCT_01579] applies which defines that attribute isService shall be set to false for the dataElements in PortPrototypes typed by a SenderReceiverInterface.

[TPS_SWCT_01159] Mapping is described separately from the SwConnector as reusable ARElement (cid:100) The mapping is described separately from the SwConnector as reusable ARElement. A set of PortInterfaceMappings is grouped in a PortInterfaceMappingSet. (cid:99)(RS_SWCT_03210)

[TPS_SWCT_01543] PortInterfaceMapping overrides all other compatibility rules (cid:100) The existence of a PortInterfaceMapping overrides all other compatibility rules given that the following statements are fulfilled:
• [constr_1071] applies also for the application of a PortInterfaceMapping.
• [constr_1268] applies also for the application of a PortInterfaceMapping.
• [constr_1269] applies also for the application of a PortInterfaceMapping.
• [constr_1270] applies also for the application of a PortInterfaceMapping.
• A structural difference between mapped DataPrototypes can be mitigated by means of a SubElementMapping. This includes the case that a “structure” data type is mapped to an “array” data type and vice versa. [TPS_SWCT_01195] is also applicable.

When using a PortInterfaceMapping, the developer of a software-component needs to properly understand the consequences in terms of model semantics. (cid:99)(RS_SWCT_03210)

Please note that [TPS_SWCT_01543] does not require a tool implementation to ignore and let go unreported deviations of all other compatibility rules in the presence of a PortInterfaceMapping.

If this is considered helpful, the tool may still issue warnings with respect to compatibility rules defined in section 6 but this is not mandated by the AUTOSAR standard. The tool, however, shall not report errors in this case.
Table 4.21: PortInterfaceMappingSet
Table 4.22: PortInterfaceMapping

#@SECTION: 4.3.1 PortInterface Mapping
#@CLASS: PortInterface
#@CLASS: PortInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: SwConnector

By default, the shortNames of PortInterface elements are used to identify the matching element pairs of connected PortPrototypes. In case of non-matching shortNames (this might be due to distributed development, off-the-shelves development, or reuse of software-components) it is required to explicitly specify which elements of PortInterfaces shall correlate to each other.

This definition is provided with PortInterfaceMappings.

[TPS_SWCT_01099] PortInterfaceMapping (cid:100) Each PortInterfaceMapping describes the mapping of the PortInterface elements of exactly two PortInterfaces. (cid:99)(RS_SWCT_03155, RS_SWCT_03210)

To apply the PortInterfaceMapping a SwConnector has to reference a PortInterfaceMapping.

[constr_1151] Applicability of PortInterfaceMapping (cid:100) A PortInterfaceMapping is only applicable and valid for a SwConnector if the two PortPrototypes which are referenced by the SwConnector are typed by the same two PortInterfaces which are mapped by the PortInterfaceMapping. (cid:99)()

[TPS_SWCT_01100] Precedence of PortInterfaceMapping (cid:100) The mapping via PortInterfaceMapping has a higher precedence than the mapping by equal shortNames as defined in chapter 6. If a connector has an associated PortInterfaceMapping this mapping shall be strictly binding with respect to the number of mapped data elements. (cid:99)(RS_SWCT_03155, RS_SWCT_03210)

[TPS_SWCT_01101] Unmapped elements of PortInterfaces (cid:100) Unmapped PortInterface elements will not be connected by the referencing SwConnector. (cid:99)(RS_SWCT_03155, RS_SWCT_03210)

Figure 4.10: Relevant meta-classes for PortInterface element mapping

#@SECTION: 4.3.1.1 Mapping of Sender Receiver Interface, Parameter Interface and Non Volatile Data Interface Elements

#@CLASS: DataPrototypeMapping
#@CLASS: VariableAndParameterInterfaceMapping
#@CLASS: VariableDataPrototype
#@CLASS: ParameterDataPrototype
#@CLASS: DataInterface
#@CLASS: SenderReceiverInterface
#@CLASS: NvDataInterface
#@CLASS: ParameterInterface
#@CLASS: PortInterface

[TPS_SWCT_01102] VariableAndParameterInterfaceMapping (cid:100) The VariableAndParameterInterfaceMapping defines the correlation of VariableDataPrototypes and ParameterDataPrototypes defined in the context of DataInterfaces, i.e. SenderReceiverInterface, NvDataInterface, or ParameterInterface. (cid:99)(RS_SWCT_03155, RS_SWCT_03210, RS_SWCT_03170)

[constr_1159] Consistency of VariableAndParameterInterfaceMapping with respect to the referenced DataInterfaces (cid:100) Within one VariableAndParameterInterfaceMapping all firstDataPrototypes shall belong to one and only one DataInterface and all secondDataPrototypes shall belong to one other and only one other DataInterface. (cid:99)()

[TPS_SWCT_01103] Mapping between different kinds of PortInterfaces (cid:100) Thereby it is possible to describe the mapping between different kinds of PortInterfaces for instance a ParameterInterface and SenderReceiverInterface. (cid:99)(RS_SWCT_03155, RS_SWCT_03210, RS_SWCT_03170)

[TPS_SWCT_01104] Possible mappings are restricted by the swImplPolicy (cid:100) Nevertheless, the possible mappings of VariableDataPrototypes and ParameterDataPrototypes are restricted by the swImplPolicy attribute. (cid:99)(RS_SWCT_03155, RS_SWCT_03210, RS_SWCT_03170)

[constr_1039] Relevance of swImplPolicy (cid:100) It is not possible to define a mapping between an element where the swImplPolicy is set to queued and an other element where the swImplPolicy is set differently. (cid:99)()

This is required to fulfill the compatibility rules defined in table 6.1

[constr_1040] Conversion of SenderReceiverInterfaces (cid:100) The conversion of elements of SenderReceiverInterfaces is possible if one of the following conditions applies:
• The AutosarDataTypes of the referred DataPrototypes are compatible as described in chapter 6.2.
• A conversion of the data as described in chapter 4.3.2 is available.
• A DataPrototypeMapping.firstToSecondDataTransformation is defined. (cid:99)()

Figure 4.11: Mapping of Sender Receiver Interface, Parameter Interface and Non Volatile Data Interface elements

Table 4.23: VariableAndParameterInterfaceMapping

Table 4.24: DataPrototypeMapping

#@SECTION: 4.3.1.2 Mapping of Client Server Interface Elements
#@CLASS: ApplicationError
#@CLASS: ArgumentDataPrototype
#@CLASS: ClientServerApplicationErrorMapping
#@CLASS: ClientServerInterface
#@CLASS: ClientServerInterfaceMapping
#@CLASS: ClientServerOperation
#@CLASS: ClientServerOperationMapping

[TPS_SWCT_01105] ClientServerInterfaceMapping (cid:100) The ClientServerInterfaceMapping defines the correlation of ClientServerOperations defined in the context of ClientServerInterfaces. (cid:99)(RS_SWCT_03155, RS_SWCT_03210)

[constr_1041] Conversion of ClientServerInterfaces (cid:100) Either the AutosarDataTypes of the referred ArgumentDataPrototypes are compatible as described in chapter 6.2 or a conversion of the data as described in chapter 4.3.2 is available. (cid:99)()

[constr_1237] Scope of mapped ClientServerOperations in the context of a ClientServerOperationMapping (cid:100) All ClientServerOperations referenced by a ClientServerOperationMapping in the role firstOperation shall belong to exactly one ClientServerInterface. All ClientServerOperations referenced by a ClientServerOperationMapping in the role secondOperation shall belong to exactly one other ClientServerInterface. (cid:99)()

[constr_1238] Scope of mapped ApplicationErrors in the context of a ClientServerOperationMapping (cid:100) All ApplicationErrors referenced by a ClientServerApplicationErrorMapping in the role firstApplicationError shall belong to exactly one ClientServerInterface. All ApplicationErrors referenced by a ClientServerApplicationErrorMapping in the role secondApplicationError shall belong to exactly one other ClientServerInterface. (cid:99)()

[constr_1240] Consistency of ArgumentDataPrototypes within the context of a ClientServerOperationMapping (cid:100) For each argument owned by a ClientServerOperationMapping.firstOperation and ClientServerOperationMapping.secondOperation a reference in the role ClientServerOperationMapping.argumentMapping.firstDataPrototype or ClientServerOperationMapping.argumentMapping.secondDataPrototype shall exist originated by one of the ClientServerOperationMapping.argumentMappings owned by the mentioned ClientServerOperationMapping. (cid:99)()

[constr_1268] ArgumentDataPrototype.direction shall be preserved in a ClientServerOperationMapping (cid:100) Within the context of a ClientServerOperationMapping, the value of the argument ArgumentDataPrototype.direction of two mapped ArgumentDataPrototype shall be identical. (cid:99)()

[constr_1269] Number of arguments shall be preserved in a ClientServerOperationMapping (cid:100) Within the context of a ClientServerOperationMapping, the number of arguments of firstOperation and secondOperation shall be identical. (cid:99)()

[constr_1270] ArgumentDataPrototype shall be mapped only once in a ClientServerOperationMapping (cid:100) Within the context of a ClientServerOperationMapping, each argument shall only be referenced once in the role firstDataPrototype or secondDataPrototype. (cid:99)()

Figure 4.12: Mapping of ClientServerInterface elements and mapping of arguments
Figure 4.13: Mapping of ArgumentDataPrototypes
Table 4.25: ClientServerInterfaceMapping
Table 4.26: ClientServerOperationMapping
Table 4.27: ClientServerApplicationErrorMapping

#@SECTION: 4.3.1.3 Mapping of Mode Interface Elements
#@CLASS: ModeDeclarationGroupPrototypeMapping
#@CLASS: ModeDeclarationMapping
#@CLASS: ModeDeclarationMappingSet
#@CLASS: ModeInterfaceMapping
#@CLASS: ModeSwitchInterface

[TPS_SWCT_01160] ModeInterfaceMapping (cid:100) The ModeInterfaceMapping defines the correlation of ModeDeclarationGroupPrototypes defined in the context of ModeSwitchInterfaces. (cid:99)(RS_SWCT_03210)

[TPS_SWCT_01167] Validity of ModeInterfaceMapping (cid:100) The mapping of ModeDeclarationGroupPrototypes is only valid if these are typed by (read "refer to") compatible ModeDeclarationGroups according chapter 6.7. (cid:99)(RS_SWCT_03210)

Table 4.28: ModeInterfaceMapping

Table 4.29: ModeDeclarationGroupPrototypeMapping

[TPS_SWCT_01449] Semantics of a ModeDeclarationGroupPrototypeMapping (cid:100) A ModeDeclarationGroupPrototypeMapping shall be used to identify two ModeDeclarationGroups that afterwards shall be considered compatible. This also applies if the two ModeDeclarationGroups deviate with respect to the contained modeTransitions. (cid:99)(RS_SWCT_03210)

Figure 4.14: Mapping of ModeSwitchInterface elements

[constr_1246] Consistency of firstMode and secondMode in the scope of one ModeDeclarationMappingSet (cid:100) Within the scope of one ModeDeclarationMappingSet, all firstModes shall belong to one and only one ModeDeclarationGroup and all secondModes shall belong to one and only one other ModeDeclarationGroup (cid:99)()

[constr_1247] Consistency of ModeDeclarationMappingSet with respect to the referenced firstModeGroup and secondModeGroup (cid:100) If a ModeDeclarationGroupPrototypeMapping.modeDeclarationMappingSet exists, the ModeDeclarationGroup owning the modeDeclarations referenced in the role firstMode shall be the type of the ModeDeclarationGroupPrototypeMapping.firstModeGroup and the ModeDeclarationGroup owning the modeDeclarations referenced in the role secondMode shall be the type of the ModeDeclarationGroupPrototypeMapping.secondModeGroup. (cid:99)()

[TPS_SWCT_01462] ModeDeclarationMapping defines the explicit correlation of ModeDeclarations (cid:100) The meta-class ModeDeclarationMapping defines the explicit correlation of ModeDeclarations defined in the context of two ModeDeclarationGroups. (cid:99)()

[TPS_SWCT_01463] modeDeclarationMapping defines the applicable set of ModeDeclarationMappings (cid:100) The modeDeclarationMapping defines the applicable set of ModeDeclarationMappings for the connection of ModeDeclarationGroupPrototypes typed by ModeDeclarationGroups with differently named ModeDeclarations and/or with a different number of ModeDeclarations. (cid:99)()

Table 4.30: ModeDeclarationMappingSet

Table 4.31: ModeDeclarationMapping

[TPS_SWCT_01464] ModeDeclaration of a mode user is mapped to exactly one ModeDeclaration of a mode manager (cid:100) The mode that corresponds to the ModeDeclaration of the Mode User is entered or exited when the mode of the mode manager that corresponds to the mapped (i.e. referenced by the same ModeDeclarationMapping) ModeDeclaration of the mode manager is entered or exited. (cid:99)(RS_SWCT_03115)

[TPS_SWCT_01465] ModeDeclaration of a mode user is mapped to several ModeDeclarations of a mode manager (cid:100) The mode that corresponds to the mapped ModeDeclaration of the mode user is entered when any of the modes of the Mode Manager that correspond to ModeDeclarations referenced by the applicable ModeDeclarationMapping is entered. The mode that corresponds to the mapped ModeDeclaration of the mode user is exited when any of the modes of the Mode Manager that correspond to ModeDeclarations referenced by the applicable ModeDeclarationMapping is exited if the new mode is not mapped to related mode of the mode user. (cid:99)(RS_SWCT_03115)

Please note if one ModeDeclaration of a mode user is mapped to several ModeDeclarations of a mode manager by means of several ModeDeclarationMappings the intended semantics is defined in a way that the individual mode transitions of the mode manager are representing "exit" and "enter" events for the Mode User. In other words, the individual transitions are recognizable by the mode user.

If one ModeDeclaration of a mode user is (by utilizing the multiplicity of the role firstMode) mapped to several ModeDeclarations of a mode manager in the context of a single ModeDeclarationMapping the semantics is defined in a way that the individual mode transitions of the Mode Manager are not recognizable to the Mode User.

[constr_1209] Mapping of ModeDeclarations of mode user to ModeDeclaration of mode manager (cid:100) A configuration that maps several ModeDeclarations representing modes of a mode user to one ModeDeclaration representing a mode of a mode manager shall be rejected. (cid:99)()

[constr_1210] Mapping of ModeDeclarations of mode user to all ModeDeclarations of mode manager (cid:100) If a ModeDeclarationMapping exists that references a ModeDeclaration representing a mode of the mode manager then ModeDeclarationMappings shall exist that map all modes of the mode manager to modes of the mode user. (cid:99)()

Please note that [constr_1210] prevents the existence of configurations where the mode user is not in a defined mode when no transition is ongoing.

[TPS_SWCT_01545] ModeDeclaration of a mode user that is not mapped to a ModeDeclaration of a mode manager (cid:100) A ModeDeclaration of a mode user that is not mapped to a ModeDeclaration of a mode manager represents a valid model. In this case the related mode is never entered nor exit during runtime of the ECU. (cid:99)(RS_SWCT_03115)

#@SECTION: 4.3.1.4 Mapping of Trigger Interface Elements
#@CLASS: TriggerInterfaceMapping
#@CLASS: TriggerMapping
#@CLASS: TriggerInterface

[TPS_SWCT_01161] TriggerInterfaceMapping (cid:100) The TriggerInterfaceMapping defines the correlation of Triggers defined in the context TriggerInterfaces. (cid:99)(RS_SWCT_03210)

Table 4.32: TriggerInterfaceMapping
Table 4.33: TriggerMapping
Figure 4.15: Mapping of TriggerInterface elements

#@SECTION: 4.3.1.5 Mapping of Elements of a composite Data Type
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationCompositeDataTypeSubElementRef
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ApplicationCompositeElementInPortInterfaceInstanceRef
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: ArVariableInImplementationDataInstanceRef
#@CLASS: DataInterface
#@CLASS: DataPrototype
#@CLASS: DataPrototypeMapping
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeSubElementRef
#@CLASS: NonqueuedReceiverComSpec
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortInterface
#@CLASS: SubElementMapping
#@CLASS: SubElementRef
#@CLASS: TextTableMapping
#@CLASS: VariableDataPrototype
#@CLASS: AutosarDataPrototype

The mapping of elements of PortInterfaces is not limited to mapping entire DataPrototypes onto each others.

[TPS_SWCT_01023] Mapping of elements of composite data types (cid:100) For applications of DataInterfaces it is also possible to formally describe the mapping of elements of ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY onto each others. (cid:99)(RS_SWCT_03210, RS_SWCT_03135)

This ability can be used if e.g. dataElements on the sender and receiver side are typed by different ApplicationRecordDataTypes.

In this case the mapping of elements of ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY onto each others allows for the definition of specific pairs of elements that fulfill the compatibility rules.

[TPS_SWCT_01551] Mapping of elements on the sender side to elements on the receiver side (cid:100) Unless the attribute swImplPolicy is set to queued, it is not required that all elements on the sender side need to be mapped to elements on the receiver side to achieve compatibility. (cid:99)(RS_SWCT_03210, RS_SWCT_03135)

The details regarding the compatibility rules are explained in chapter 6.3.

[constr_1279] Unmapped elements of ApplicationCompositeDataTypes or ImplementationDataTypes and the attribute swImplPolicy (cid:100) If the attribute swImplPolicy is set to queued it is not allowed to have unmapped elements of ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY on the receiver side. (cid:99)()

[constr_1280] Unmapped dataElement on the receiver side shall have an initValue (cid:100) If elements of ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY are not considered in a SubElementMapping then the enclosing dataElement shall have an initValue if the NonqueuedReceiverComSpec is aggregated by an AbstractRequiredPortPrototype. (cid:99)()

Figure 4.16: Mapping of elements of composite data types

[TPS_SWCT_01024] Combination of ApplicationCompositeDataType and nested ImplementationDataType (cid:100) The mapping of elements of ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY works for both ApplicationCompositeDataType and nested ImplementationDataTypes and even for combinations of one PortInterface may use an ApplicationCompositeDataType while the other PortInterface uses a nested ImplementationDataType. (cid:99)(RS_SWCT_03210, RS_SWCT_03135)

[TPS_SWCT_01195] Mapping of composite element to primitive DataPrototype (cid:100) It is also possible to map an element of a composite data type on the provided side to a primitive DataPrototype on the required side. For this purpose the multiplicity of the firstElement shall be set to 1 and the multiplicity of the secondElement shall be set to 0. (cid:99)(RS_SWCT_03136)

In general, the multiplicity of the firstElement can technically also be set to 0 but this case is reserved for future use.

[constr_1190] Only one mapping for composite to primitive use case (cid:100) In the case described by [TPS_SWCT_01195] only one subElementMapping shall exist at the enclosing DataPrototypeMapping. (cid:99)()

[constr_1300] Primitive DataPrototype on the provider side shall not be mapped to element of a composite data type on the requester side (cid:100) The usage of DataPrototypeMapping resp. SubElementMapping does not support the following configuration:
• The AutosarDataPrototype referenced on the provider/client side is typed by an ApplicationPrimitiveDataType of category VALUE or ImplementationDataType of category VALUE or category TYPE_REFERENCE that eventually resolves to category VALUE.
• The DataPrototypeMapping aggregates a subElementMapping that refers to a ImplementationDataTypeElement or ApplicationCompositeElementDataPrototype on the requester/server side. (cid:99)()

Table 4.34: SubElementMapping
Table 4.35: SubElementRef
Table 4.36: ImplementationDataTypeSubElementRef
Table 4.37: ApplicationCompositeDataTypeSubElementRef

Figure 4.17: Implementation of the InstanceRef for the mapping of elements of composite application data types

[constr_1184] Consistency of rootDataPrototype and base in the context of ApplicationCompositeElementInPortInterfaceInstanceRef (cid:100) The rootDataPrototype referenced by ApplicationCompositeElementInPortInterfaceInstanceRef shall be owned by the applicable subclass of DataInterface referenced in the role base. This implies that the rootDataPrototype shall be a ParameterDataPrototype if the base is a ParameterInterface. Otherwise the rootDataPrototype shall be a VariableDataPrototype. (cid:99)()

[constr_1185] Consistency of data types in the context of ApplicationCompositeElementInPortInterfaceInstanceRef (cid:100) The definition of attributes contextDataPrototype and targetDataPrototype shall (via the type-prototype pattern) be enclosed in the context of the definition of the data type used to type rootDataPrototype. (cid:99)()

In other words, it shall be possible to reach contextDataPrototype and targetDataPrototype by means of the type-prototype chain created by the definition of the data type used to type rootDataPrototype. And, as implied by the definition of the InstanceRef, the contextDataPrototypes shall enclose each others and, eventually, the targetDataPrototype.

Figure 4.18: Implementation of the InstanceRef for the mapping of elements of composite implementation data types

[constr_1186] Consistency of data types in the context of ArVariableInImplementationDataInstanceRef (cid:100) The definition of attributes contextDataPrototype and targetDataPrototype shall be enclosed in the context of the definition of the data type used to type rootDataPrototype. (cid:99)()

#@SECTION: 4.3.2 Data Conversion
#@CLASS: AutosarDataPrototype
#@CLASS: AutosarDataType
#@CLASS: ImplementationDataTypeSubElementRef
#@CLASS: SubElementRef
#@CLASS: VariableDataPrototype
#@CLASS: CompuMethod

[TPS_SWCT_01560] Supported categorys of CompuMethods for data conversion (cid:100) Data conversion shall be supported for AutosarDataTypes that refer to CompuMethods of category LINEAR, IDENTICAL, SCALE_LINEAR_AND_TEXTTABLE, TEXTTABLE, and BITFIELD_TEXTTABLE. (cid:99)(RS_SWCT_03210)

[TPS_SWCT_01561] Application of data conversion to composite AutosarDataTypes (cid:100) Data conversion is also applicable for composite AutosarDataTypes. The actual conversion, however, shall be individually applied to each leaf element of a given composite AutosarDataType. (cid:99)(RS_SWCT_03210)

#@SECTION: 4.3.2.1 Linear Data Scaling
#@CLASS: AutosarDataType
#@CLASS: CompuRationalCoeff
#@CLASS: CompuMethod
#@CLASS: AutosarDataType
#@CLASS: PhysicalDimension
#@CLASS: Unit

A Linear Data Scaling can be defined under following preconditions:

[TPS_SWCT_01549] Definition of linear data scaling (cid:100) The term Linear Scaling is defined as follows:

1. Regarding the existence of CompuMethods one of the following cases shall apply:
(a) The involved AutosarDataTypes refer to CompuMethods of category IDENTICAL, LINEAR, or RAT_FUNC.
(b) If one side (sender or receiver) does not refer a CompuMethod then a "default" CompuMethod of category IDENTICAL shall be assumed.

2. Regarding the existence of Units one of the following cases shall apply:
(a) The CompuMethods refer either to compatible Units or to Units that in turn refer to compatible definitions of PhysicalDimension.
(b) Units and PhysicalDimensions do partially not exist on one side:
• If one side (sender or receiver) does not refer to a Unit, then an "imaginary" Unit with the properties defined in [TPS_SWCT_01492] shall be assumed.
• if the PhysicalDimension is only defined on one side (sender or receiver) then it shall be considered as default for the other side.

3. Both CompuMethods fulfill the following condition:
Int = N0∗phys0+N1∗phys1+N2∗phys2+...+Ni∗physi/D0∗phys0+D1∗phys1+D2∗phys2+...+Di∗physi with
• N2=N3=...=Ni=0
• D1=D2=...=Di=0
• N1 !=0
• D0 !=0
The coefficient N0 represents the offset and can take any value.
(cid:99)(RS_SWCT_03210)

[TPS_SWCT_01550] Definition of reciprocal linear data scaling (cid:100) The term Reciprocal Linear Scaling is defined as follows:
1. The involved AutosarDataTypes refer to CompuMethods of category RAT_FUNC.
2. The CompuMethods refer either to compatible Units or to Units that in turn refer to compatible definitions of PhysicalDimension.
3. Both CompuMethods fulfill the following condition:
Int = N0∗phys0+N1∗phys1+N2∗phys2+...+Ni∗physi /D0∗phys0+D1∗phys1+D2∗phys2+...+Di∗physi with
• N1=N2=...=Ni=0
• D2=D3=...=Di=0
• N0 !=0
• D1 !=0
The coefficient D0 represents the (reciprocal) offset and can take any value.
(cid:99)(RS_SWCT_03210)

[TPS_SWCT_01168] Linear conversion factor can be calculated (cid:100) In such cases a linear conversion factor can be calculated out of the factorSiToUnit and offsetSiToUnit attributes of the referred Units and the CompuRationalCoeffs of a compuInternalToPhys/compuPhysToInternal of the referred CompuMethods.
(cid:99)(RS_SWCT_03210)

#@SECTION: 4.3.2.2 Table Conversion
#@CLASS: DataPrototype
#@CLASS: DataPrototypeMapping
#@ENUM: MappingDirectionEnum
#@CLASS: TextTableMapping
#@CLASS: TextTableValuePair
#@CLASS: AutosarDataType
#@CLASS: CompuMethod
#@CLASS: ImplementationDataType



[TPS_SWCT_01162] Existence of TextTableMapping (cid:100) A TextTableMapping to CompuMethods of category TEXTTABLE, SCALE_LINEAR_AND_TEXTTABLE, and BITFIELD_TEXTTABLE can be defined if the AutosarDataTypes refer. (cid:99)(RS_SWCT_03210)

Please note that the use case behind the appearance of BITFIELD_TEXTTABLE in [TPS_SWCT_01162] is the fact that BSW modules such as the Dem need to put data into the NVRAM that has the nature of single bits embedded into a composite data type.

The TextTableMapping is defined as a table based conversion.

[TPS_SWCT_01163] Conversion from firstValue to secondValue (cid:100) A firstValue of a valuePair is converted into the secondValue in case of a data flow from the firstDataPrototype to the secondDataPrototype. (cid:99)(RS_SWCT_03210)

[TPS_SWCT_01164] Conversion from secondValue to firstValue (cid:100) In case of a data flow from the secondDataPrototype to firstDataPrototype the secondValue is substituted by the firstValue. (cid:99)(RS_SWCT_03210)

[TPS_SWCT_01165] Invertible mapping (cid:100) If the mappingDirection attribute is set to bidirectional then the TextTableMapping has to be invertible. This requires that the list of all firstValues and the list of all secondValues do not contain identical values inside a list. (cid:99)(RS_SWCT_03210)

[TPS_SWCT_01166] Non-invertible mapping (cid:100) For non-invertible TextTableMapping, a dedicated TextTableMapping for each direction can be defined. (cid:99)(RS_SWCT_03210)

[constr_1303] Applicability of TextTableMapping depending on the value of CompuMethod.category (cid:100) If a DataPrototypeMapping aggregates a TextTableMapping then only certain combinations of the value of the applicable CompuMethod.category are supported:
• category of firstDataPrototype: TEXTTABLE, category of secondDataPrototype: TEXTTABLE
• category of firstDataPrototype: SCALE_LINEAR_AND_TEXTTABLE, category of secondDataPrototype: TEXTTABLE
• category of firstDataPrototype: TEXTTABLE, category of secondDataPrototype: SCALE_LINEAR_AND_TEXTTABLE
• category of firstDataPrototype: BITFIELD_TEXTTABLE, category of secondDataPrototype: TEXTTABLE
• category of firstDataPrototype: TEXTTABLE, category of secondDataPrototype: BITFIELD_TEXTTABLE
• category of firstDataPrototype: BITFIELD_TEXTTABLE, category of secondDataPrototype: BITFIELD_TEXTTABLE
(cid:99)()

To some extent, bitfields can be regarded as a hybrid between a primitive and a structured data type:
• On the one hand, a bitfield is defined in the context of a primitive ImplementationDataType.
• On the other hand, by means of the definition of a mask, it is possible to define isolated parts within the primitive ImplementationDataType that potentially can be totally independent from each other with respect to the semantics of the data that match the mask.

In other words, the existence of semantically independent and potentially isolated parts within the primitive ImplementationDataType creates a similar characteristic as if the definitions of the isolated parts were created by means of defining primitive ImplementationDataTypeElements within the context of a composite ImplementationDataType.

And because it is possible to regard the "mission statement" of a DataPrototype that refers to a CompuMethod of category BITFIELD_TEXTTABLE as to mimic the semantics of a structured data type it is also possible to apply some of the rules that are already in place for structured data types in this specific case as well.

This conclusion, in combination with the existence of [TPS_SWCT_01551], sets the stage for [TPS_SWCT_01583].

[TPS_SWCT_01583] Completeness of TextTableMapping is not a requirement (cid:100) If a DataPrototypeMapping contains one or more TextTableMapping(s) where the DataPrototype on the sender side refers to a CompuMethod of category BITFIELD_TEXTTABLE it is not required that for each possible value and each possible bit mask on the sender side corresponding values on the receiver side are specified. (cid:99)(RS_SWCT_03210)

With respect to [TPS_SWCT_01583] it is still important to observe that within a single mask all values on the sender side shall have a mapping to the receiver side. Otherwise the RTE generator would not be able to create mapping code that unambiguously takes care of mapping the correct values onto each other.

[constr_1313] Completeness of TextTableMapping for the values of a given bit mask on the sender side (cid:100) If a DataPrototypeMapping contains one or more TextTableMapping(s) where the DataPrototype on the sender side refers to a CompuMethod of category BITFIELD_TEXTTABLE then all DataPrototypeMapping.textTableMapping shall aggregate a collection of TextTableMapping.valuePair where each possible value of the sender bit mask(5Depending on the applicable case this means either bitfieldTextTableMaskFirst (applies if [TPS_SWCT_01163] is in place) or bitfieldTextTableMaskSecond for the case of [TPS_SWCT_01164].) is represented by exactly one TextTableValuePair.firstValue ([TPS_SWCT_01163]) resp. TextTableValuePair.secondValue ([TPS_SWCT_01164]). (cid:99)()

[constr_1304] Existence of attribute bitfieldTextTableMaskFirst (cid:100) The attribute bitfieldTextTableMaskFirst shall be defined only if the firstDataPrototype of a DataPrototypeMapping refers to a CompuMethod that has the value of category set to BITFIELD_TEXTTABLE. (cid:99)()

[constr_1305] Existence of attribute bitfieldTextTableMaskSecond (cid:100) The attribute bitfieldTextTableMaskSecond shall be defined only if the secondDataPrototype of a DataPrototypeMapping refers to a CompuMethod that has the value of category set to BITFIELD_TEXTTABLE. (cid:99)()

[constr_1306] Limitation of TextTableMapping for CompuMethods that have the value of category set to BITFIELD_TEXTTABLE (cid:100) For any TextTableMapping where both firstDataPrototype and secondDataPrototype refer to CompuMethods that have the value of category set to BITFIELD_TEXTTABLE and where the attribute TextTableMapping.valuePair exists the value of attribute TextTableMapping.identicalMapping shall be set to false. (cid:99)()

[constr_1307] Consistency of values and masks in TextTableMapping (cid:100) If a TextTableMapping element defines bit masks as bitfieldTextTableMaskFirst or bitfieldTextTableMaskSecond then all contained TextTableMapping.valuePair.firstValues as well as all TextTableMapping.valuePair.secondValues shall not specify a value that would be ruled out when - depending on the given value of TextTableMapping.mappingDirection - the relevant bit mask is applied. (cid:99)()

Example for [constr_1307]: For a bit mask 0b00001000 only the corresponding values 8 and 0 are allowed.

Table 4.38: TextTableMapping

Table 4.39: MappingDirectionEnum

Table 4.40: TextTableValuePair

Figure 4.19: Mapping of DataPrototypes that eventually refer to CompuMethods of category TEXTTABLE, SCALE_LINEAR_AND_TEXTTABLE, and BITFIELD_TEXTTABLE

#@SECTION: 4.4 Port Annotation
#@SECTION: 4.4.1 Introduction
#@CLASS: ClientServerAnnotation
#@CLASS: ClientServerInterface
#@CLASS: CompositionSwComponentType
#@CLASS: DelegatedPortAnnotation
#@CLASS: GeneralAnnotation
#@CLASS: IoHwAbstractionServerAnnotation
#@CLASS: ModeInterface
#@CLASS: ModePortAnnotation
#@CLASS: NvDataInterface
#@CLASS: NvDataPortAnnotation
#@CLASS: ParameterInterface
#@CLASS: ParameterPortAnnotation
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: SenderReceiverAnnotation
#@CLASS: SenderReceiverInterface
#@CLASS: TriggerInterface
#@CLASS: TriggerPortAnnotation

[TPS_SWCT_01203] PortPrototype may own port annotations (cid:100) In addition to the formal specification required to implement the communication via ports, a PortPrototype may own so-called port annotations (please find a summary in Figure 4.20). They do not directly influence the signature of calls via this PortPrototype, but contain further information that may be useful for the application developers of the components on both sides of the connection. (cid:99)()

[TPS_SWCT_01204] GeneralAnnotation (cid:100) Beside formally specified attributes it is also possible to place textual information as provided in GeneralAnnotation. (cid:99)()

Figure 4.20: Application Level Port Annotations Overview

#@SECTION: 4.4.2 SenderReceiverAnnotation
#@ENUM: DataLimitKindEnum
#@ENUM: ProcessingKindEnum
#@CLASS: ReceiverAnnotation
#@CLASS: RPortPrototype
#@CLASS: SenderAnnotation
#@CLASS: SenderReceiverAnnotation
#@CLASS: SenderReceiverInterface
#@CLASS: VariableDataPrototype
#@CLASS: CompuMethod

Embedded automotive software is used to implement open-loop and closed-loop control-algorithms. Therefore, a software-component description has to accommodate typical control engineering description means which have only indirect influence of the embedded software itself.

These annotations provide the (function-) developer with a direct indication whether a certain software-component is appropriate for the control-algorithm to be designed. A typical annotation is the signal quality which is characterized by several properties. Each of the property is an annotation in its own.

[TPS_SWCT_01205] Typical annotations for sender/receiver communication (cid:100) Typical annotations for sender/receiver communication are:
• Signal Age: this attribute expresses that the associated software-component will only work correctly given that the propagation of the signal from a sensor to a consumer can be finished within a particular time-limit. Of course, this cannot be identified on component or role level, but has to take into account the instance view as well as the actual ECU- and bus-scheduling.
• Raw: a raw signal is typically taken directly from the basic software modules of the ECU abstraction layer. In particular, no sensor software-component has filtered its original value. A dataElement in an RPortPrototype of a SwComponentType using this annotation indicates to the control engineer (who develops a control-algorithm for this component) that the signal has to be filtered (This relationship applies for SenderReceiverInterfaces).
• Filtered: this attribute indicates that a raw signal has been manipulated by some application software-components by using a certain filter.
• Computed: this attribute indicates that this signal is not measured directly but calculated from tentatively several other measured or calculated signals. In a vehicle, there might be alternative signals to be used from other components having a better quality, e.g. a raw signal.
• Min: this annotation indicates that the signal carries a minimum value. If, for example, a reference value computed in the software-component is below that value some dedicated actions (e.g. failure-mode) might have to be taken.
• Max: this annotation indicates that the signal carries a maximum value. If, for example, a reference value computed in the software-component is above that value some dedicated actions (e.g. failure-mode) might have to be taken.

In the meta-model this aspect is implemented by the abstract meta-class SenderReceiverAnnotation which represents the base class of both SenderAnnotation and ReceiverAnnotation. This relationship is depicted in Figure 4.21. (cid:99)()

Table 4.41: SenderReceiverAnnotation

Table 4.42: SenderAnnotation

Table 4.43: ReceiverAnnotation

Table 4.44: ProcessingKindEnum

Table 4.45: DataLimitKindEnum

[TPS_SWCT_01206] Min and Max annotations are valid for a certain amount of time (cid:100) The Min and Max annotations are valid for a certain amount of time. The value is likely to change to another valid value while the ECU is running. E.g. the maximal torque which can be requested from an engine is a typical use-case. (cid:99)()

This value might vary depending on e.g.the status of the climate control system. Therefore, these annotations shall not be mismatched with the min and max attributes of CompuMethods.

Figure 4.21: SenderReceiverAnnotation

The application level port annotations for sender/receiver communication have to be associated to each dataElement in a PortPrototype, e.g. there might be a "raw" dataElement and a "filtered" dataElement in the same PortPrototype!

[TPS_SWCT_01207] VariableDataPrototypes use the same application-level SenderReceiverAnnotation (cid:100) Furthermore, if two VariableDataPrototypes use the same application-level SenderReceiverAnnotation, a reference from the annotation to the VariableDataPrototypes will be established by an appropriate tool. (cid:99)()

[TPS_SWCT_01208] Grouping for SenderReceiverAnnotation (cid:100) As shown in Figure 4.21 the SenderReceiverAnnotation for sender/receiver communication are grouped into

• processing type, indicating to some extend the direct quality of the signal,

• computed, which is just a flag or,

• limit type, showing the component expects an actual limit.

In the case of an RPortPrototype, the signal age of the value, carried by the associated SwConnector, can be specified. Each of these groups can be interpreted as a property of the signal-quality. (cid:99)()

[constr_4004] Context of SenderReceiverAnnotation (cid:100) A SenderReceiverAnnotation shall only be aggregated by a PortPrototype typed by a SenderReceiverInterface. (cid:99)()

#@SECTION: 4.4.3 ClientServerAnnotation
#@CLASS: ClientServerAnnotation
#@CLASS: ClientServerOperation
#@CLASS: PortPrototype

[TPS_SWCT_01209] ClientServerAnnotation (cid:100) The ClientServerAnnotation can be used to provide more information with respect to the ClientServerOperation of the PortPrototype. (cid:99)()

Table 4.46: ClientServerAnnotation

Figure 4.22: ClientServerAnnotation

[constr_4005] Context of ClientServerAnnotation (cid:100) A ClientServerAnnotation shall only be aggregated by a PortPrototype typed by a ClientServerInterface. (cid:99)()

#@SECTION: 4.4.4 Annotation for the I/O Hardware Abstraction Layer
#@CLASS: ArgumentDataPrototype
#@ENUM: FilterDebouncingEnum
#@CLASS: IoHwAbstractionServerAnnotation
#@ENUM: PulseTestEnum
#@CLASS: SensorActuatorSwComponentType
#@CLASS: VariableDataPrototype
#@CLASS: NvDataInterface



Within the ECU-Abstraction Layer there are ECU-signals defined. These signals represent the electrical signals as they arrive in the micro-controller peripheral and are fetched from the registers via the MCAL.

Access to the I/O Hardware Abstraction Layer is done via service interfaces, i.e. the I/O Hardware Abstraction Layer provides GET- and SET-operations at the specified service ports of a SensorActuatorSwComponentType.

[TPS_SWCT_01524] Usage of IoHwAbstractionServerAnnotation (cid:100) IoHwAbstractionServerAnnotation can be used for all kinds of PortInterfaces except NvDataInterface. (cid:99)()

Figure 4.23: IoHwAbstractionServerAnnotation
Table 4.47: IoHwAbstractionServerAnnotation
Table 4.48: FilterDebouncingEnum
Table 4.49: PulseTestEnum

[TPS_SWCT_01211] Assign several annotations to ArgumentDataPrototype (cid:100) The ClientServerOperations provide an ArgumentDataPrototype where several annotations can be assigned to. They are depicted in the IoHwAbstraction ServerAnnotation meta-class in Figure 4.23. (cid:99)()

A detailed description of the attributes can be found in the IoHwAbstraction Layer software specification document [17]. For example, the signal age has a very dedicated meaning in this particular interface with respect to a register whereas the signal age in the SenderReceiverAnnotation is more generic. Especially, there is no relationship with the micro-controller peripherals.

#@SECTION: 4.4.5 Parameter Port Annotation
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: ParameterPortAnnotation
#@CLASS: ParameterSwComponentType
#@CLASS: PortPrototype
#@CLASS: PPortPrototype

[TPS_SWCT_01212] ParameterPortAnnotation (cid:100) The ParameterPortAnnotation can be used to provide more information with respect to calibration parameter prototypes of the PortPrototype. The data provided at the PortPrototype is calibration parameters. The ParameterPortAnnotation provides a reference to a particular ParameterDataPrototype. (cid:99)()

Table 4.50: ParameterPortAnnotation
Figure 4.24: ParameterPortAnnotation

[constr_4006] Context of ParameterPortAnnotation (cid:100) A ParameterPortAnnotation shall only be aggregated by a PPortPrototype owned by a ParameterSwComponentType. (cid:99)()

#@SECTION: 4.4.6 Mode Port Annotation
#@CLASS: ModePortAnnotation
#@CLASS: ModeSwitchInterface
#@CLASS: PortPrototype
[TPS_SWCT_01213] ModePortAnnotation (cid:100) The ModePortAnnotation can be used to provide more information with respect to the mode declaration group prototype of the PortPrototype. (cid:99)()

Table 4.51: ModePortAnnotation
The main use-case is to allow for the definition of additional information related to the mode declaration group prototype.

Figure 4.25: ModePortAnnotation

[constr_4007] Context of ModePortAnnotation (cid:100) A ModePortAnnotation shall only be aggregated by a PortPrototype typed by a ModeSwitchInterface. (cid:99)()

#@SECTION: 4.4.7 Trigger Port Annotation
#@CLASS: TriggerPortAnnotation
#@CLASS: PortPrototype
#@CLASS: TriggerInterface

[TPS_SWCT_01214] TriggerPortAnnotation (cid:100) The TriggerPortAnnotation can be used to provide more information with respect to the trigger of the PortPrototype. (cid:99)()

The main use-case is to allow define additional information related to the trigger.

Table 4.52: TriggerPortAnnotation

Figure 4.26: TriggerPortAnnotation

[constr_4008] Context of TriggerPortAnnotation (cid:100) A TriggerPortAnnotation shall only be aggregated by a PortPrototype typed by a TriggerInterface. (cid:99)()

#@SECTION: 4.4.8 Non Volatile Data Port Annotation
#@CLASS: NvDataPortAnnotation
#@CLASS: PortPrototype
#@CLASS: VariableDataPrototype
#@CLASS: NvDataInterface

[TPS_SWCT_01215] NvDataPortAnnotation (cid:100) The NvDataPortAnnotation can be used to provide more information with respect to the non volatile data of the PortPrototype. (cid:99)()
Table 4.53: NvDataPortAnnotation

The main use-case is to allow define additional information related to the non volatile data elements.

Figure 4.27: NvDataPortAnnotation

[constr_4009] Context of NvDataPortAnnotation (cid:100) An NvDataPortAnnotation shall only be aggregated by a PortPrototype typed by an NvDataInterface. (cid:99)()

#@SECTION: 4.4.9 Delegated Port Annotations
#@CLASS: AssemblySwConnector
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: CompositionSwComponentType
#@CLASS: DelegatedPortAnnotation
#@CLASS: DelegationSwConnector
#@CLASS: PortPrototype
#@CLASS: SenderReceiverInterface
#@ENUM: SignalFanEnum
#@CLASS: VariableDataPrototype

[TPS_SWCT_01216] DelegatedPortAnnotation (cid:100) The DelegatedPortAnnotation is used to define the Signal Fan In or Signal Fan Out inside the CompositionSwComponentType.

This information is used to pre-define and pre-check resulting communication patterns in the VFB (1:n, n:1, 1:1) if empty CompositionSwComponentTypes are used as interface definition for sub-systems.

The DelegatedPortAnnotation guides either the system designer in connecting the empty CompositionSwComponentType or the sub-system designer in applying communication pattern (1:n, n:1, 1:1) inside of the CompositionSwComponentType. (cid:99)()

Table 4.54: DelegatedPortAnnotation
Table 4.55: SignalFanEnum

[TPS_SWCT_01217] Semantics of DelegatedPortAnnotation.signalFan (cid:100) The attribute values have following definition:

• single: the internal connections in the CompositionSwComponentType via DelegationSwConnectors and AssemblySwConnectors are defined in a way that each dataElement present in the SenderReceiverInterfaces or operation in the ClientServerInterfaces of the outer PortPrototype is involved in a 1:1 communication pattern only.

• nfold: The internal connections in the CompositionSwComponentType via DelegationSwConnectors and AssemblySwConnectors are defined in a way that at least one dataElement present in the SenderReceiverInterfaces or one operation in the ClientServerInterfaces of the outer PortPrototype is involved in a 1:n or n:1 communication pattern. (cid:99)()

[constr_4010] Context of DelegatedPortAnnotation (cid:100) A DelegatedPortAnnotation shall only be aggregated by a PortPrototype aggregated by a CompositionSwComponentType. (cid:99)()

#@SECTION: 4.4.10 General Annotation
#@CLASS: GeneralAnnotation

Besides formally specified attributes it is also possible to place textual information as provided in the abstract GeneralAnnotation (see Figure 4.28 for an overview).

Figure 4.28: textual information in annotations
Table 4.56: GeneralAnnotation

#@SECTION: 4.5 Communication Speciﬁcation
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: ClientComSpec
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: CompositionSwComponentType
#@CLASS: ModeSwitchInterface
#@CLASS: ModeSwitchReceiverComSpec
#@CLASS: ModeSwitchSenderComSpec
#@CLASS: NvDataInterface
#@CLASS: NvProvideComSpec
#@CLASS: NvRequireComSpec
#@CLASS: ParameterInterface
#@CLASS: ParameterProvideComSpec
#@CLASS: ParameterRequireComSpec
#@CLASS: PPortComSpec
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RPortComSpec
#@CLASS: RPortPrototype
#@CLASS: ReceiverComSpec
#@CLASS: SenderComSpec
#@CLASS: SenderReceiverInterface
#@CLASS: ServerComSpec
#@CLASS: SwComponentType
PortPrototype

[TPS_SWCT_01218] Big picture of ComSpec (cid:100) The highest level of description of information exchanged between components in an AUTOSAR system is the Port Interfaces, as shown in earlier sections. Such PortInterface however, only describes structure and does not include information about whether communication needs to be done reliably, or whether an initial value exists in case the real data is not yet available.

This information is role-specific, i.e. it shall be applied on the level of PortPrototypes rather than PortInterfaces. Therefore, most communication-relevant attributes are related to the PortPrototypes of an SwComponentType.

The communication attributes are organized in a so-called communication specification (in terms of the meta-model: ComSpec) classes. (cid:99)()

Note that the communication specification is optional, i.e. its existence is not required in any case. Figures 4.29 and 4.30 provide an overview of communication specifications. The derived meta-classes are explained in the following sub-chapters.

Figure 4.29: Overview of communication attributes of RPortPrototype

Figure 4.30: Overview of communication attributes of PPortPrototype

As explained before, ComSpec meta-classes which are required on the level of a SwComponentType are attached to the PortPrototype declarations which in turn are part of the definition of a SwComponentType. Nevertheless, the usage of ComSpecs is not restricted to the PortPrototypes of AtomicSwComponentTypes (for more details please refer to section 2.5).

Sections 7.5.1 and 7.5.2 then explain the sender-receiver and client-server communication patterns with respect to the RTE, the RTE events and the corresponding communication attributes.

Several ComSpecs allow to define initValues in relation to the associated DataPrototype. For further details about the representation of initValues please refer to section 5.7.2.

Furthermore, semantic constraints apply such that specific subclasses of ComSpec can only be owned by PortPrototypes typed by the corresponding kind of PortInterface.

[constr_1290] Limitation on the number of PPortComSpecs in the context of one PPortPrototype (cid:100) Within the context of one PPortPrototype there can only be one PPortComSpec that references a given dataElement or clientServerOperation. (cid:99)()

In other words, it is not allowed that two or more PPortComSpec exist in the context of a one PPortPrototype that refer to the same dataElement or clientServerOperation.

[constr_1291] Limitation on the number of RPortComSpecs in the context of one PPortPrototype (cid:100) Within the context of one RPortPrototype, there can only be one RPortComSpec that references a given dataElement or clientServerOperation. (cid:99)()

In other words, it is not allowed that two or more RPortComSpec exist in the context of a one RPortPrototype that refer to the same dataElement or clientServerOperation.

[TPS_SWCT_01454] PRPortPrototype can own both RPortComSpecs and PPortComSpecs (cid:100) In contrast to PPortPrototype and RPortPrototype, PRPortPrototype can own both RPortComSpecs and PPortComSpecs at the same time. (cid:99)(RS_SWCT_03250)

Nevertheless, the following restriction applies:

[constr_1292] Limitation on the number of RPortComSpecs/PPortComSpecs in the context of one PRPortPrototype (cid:100) Within the context of one PRPortPrototype, there can only be one RPortComSpec and one PPortComSpec that references a given dataElement or clientServerOperation. (cid:99)()

In other words, it is not allowed that two or more PPortComSpec exist in the context of a one PRPortPrototype that refer to the same dataElement or clientServerOperation. In the same manner, not allowed that two or more RPortComSpec exist in the context of a one PRPortPrototype that refer to the same dataElement or clientServerOperation.

The rationale for the existence of [constr_1290], [constr_1291], and [constr_1292] is that the AUTOSAR communication layer needs an unambiguous specification of the communication behavior. The existence of redundant RPortComSpecs/PPortComSpecs may easily be contradicting each other and this would inhibit the creation of a valid configuration for the AUTOSAR Com.

Table 4.57: PPortComSpec

Table 4.58: RPortComSpec

[constr_1043] PortInterface vs. ComSpec (cid:100) The allowed combinations of a specific kind of PortInterface and a kind of ComSpec are documented in Table 4.59. (cid:99)()


<-------------- multimodal context 
| PortInterface              | ComSpec                                                          |
|----------------------------|------------------------------------------------------------------|
| SenderReceiverInterface    | SenderComSpec, ReceiverComSpec                                   |
| ClientServerInterface      | ClientComSpec, ServerComSpec                                     |
| ModeSwitchInterface        | ModeSwitchSenderComSpec, ModeSwitchReceiverComSpec               |
| ParameterInterface         | ParameterProvideComSpec, ParameterRequireComSpec                 |
| NvDataInterface            | NvRequireComSpec, NvProvideComSpec                               | ---------------------->
Table 4.59: PortInterface vs. ComSpec

As explained in section 2.5, there are cases where PortPrototypes owned by a CompositionSwComponentType could have initValues.

Therefore, it is possible that PortPrototypes owned by CompositionSwComponentTypes can have ComSpecs. It is not required that the ComSpecs defined on the composition level match the ComSpecs defined inside the CompositionSwComponentType.

If consistency would be required this constraint might be a major obstacle for integrating existing AtomicSwComponentTypes into a CompositionSwComponentType that has PortPrototypes with ComSpecs.

#@SECTION: 4.5.1 Communication Speciﬁcation for Sender-Receiver Communication
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: CompositeNetworkRepresentation
#@CLASS: DataFilter
#@ENUM: DataFilterTypeEnum
#@ENUM: HandleOutOfRangeEnum
#@ENUM: HandleTimeoutEnum
#@CLASS: NonqueuedReceiverComSpec
#@CLASS: NonqueuedSenderComSpec
#@CLASS: PPortPrototype
#@CLASS: QueuedReceiverComSpec
#@CLASS: QueuedSenderComSpec
#@CLASS: ReceiverComSpec
#@CLASS: RPortPrototype
#@CLASS: SenderComSpec
#@CLASS: SenderReceiverInterface
#@CLASS: SwDataDefProps
#@CLASS: TimeValue
#@CLASS: TransmissionAcknowledgementRequest
#@CLASS: VariableAccess
#@CLASS: VariableDataPrototype
#@CLASS: EndToEndTransformationDescription

Communication specification applies in different ways to specific kinds of communication. Figure 4.31 shows the meta-model of the communication attributes relevant sender-receiver communication at an RPortPrototype.

[TPS_SWCT_01455] Duplicate existence of initValue in the context of a PR PortPrototype (cid:100) If an initValue is defined in a NonqueuedReceiverComSpec owned by a PRPortPrototype its value shall be ignored. (cid:99)(RS_SWCT_03250)

Figure 4.31: Communication attributes of RPortPrototype with respect to sender receiver communication.

[TPS_SWCT_01219] ComSpec for queued and non-queued sender-receiver communication (cid:100) Sender-receiver communication might be queued or non-queued. This aspect is primarily reflected in the value of dataElement.swDataDefProps.swImplPolicy. If the value of this attribute is set to queued then QueuedSenderComSpec and/or QueuedReceiverComSpec shall be defined. In all other applicable cases NonqueuedSenderComSpec resp. NonqueuedReceiverComSpec shall be used.

Thus, the constraints [constr_1129], [constr_1130], [constr_1131], and [constr_1132] shall apply.

While in the case of queued communication the queueLength attribute remains the only information item the non-queued case foresees several attributes for controlling communication behavior. (cid:99)()

Table 4.60: ReceiverComSpec
Table 4.61: NonqueuedReceiverComSpec
Table 4.62: QueuedReceiverComSpec
Table 4.63: HandleTimeoutEnum
able 4.64: TimeValue

[constr_1103] NonqueuedReceiverComSpec and enableUpdate (cid:100) A NonqueuedReceiverComSpec that has attribute enableUpdate set to true may not reference a dataElement that in turn is referenced by a VariableAccess in the role dataReadAccess. (cid:99)()

[constr_1201] initValue shall exist in an RPortPrototype (cid:100) The optional attribute initValue shall exist if the enclosing NonqueuedReceiverComSpec is owned by an RPortPrototype. (cid:99)()

[constr_1129] swImplPolicy and NonqueuedReceiverComSpec (cid:100) The attribute swImplPolicy of a dataElement referenced by a NonqueuedReceiverComSpec shall not be set to the value queued. (cid:99)()

[constr_1130] swImplPolicy and QueuedReceiverComSpec (cid:100) The attribute swImplPolicy of a dataElement referenced by a QueuedReceiverComSpec shall be set to the value queued. (cid:99)()

[constr_1188] Existence of ReceiverComSpec.replaceWith (cid:100) The aggregation of VariableAccess in the role ReceiverComSpec.replaceWith shall exist if and only if at least one of the following conditions is fulfilled:
• Attribute ReceiverComSpec.handleOutOfRange is set to the value externalReplacement.
• Attribute SenderReceiverInterface.invalidationPolicy.handleInvalid is set to the value externalReplacement.
(cid:99)()

[constr_1131] swImplPolicy and NonqueuedSenderComSpec (cid:100) The attribute swImplPolicy of a dataElement referenced by a NonqueuedSenderComSpec shall not be set to the value queued. (cid:99)()

[constr_1132] swImplPolicy and QueuedSenderComSpec (cid:100) The attribute swImplPolicy of a dataElement referenced by a QueuedSenderComSpec shall be set to the value queued. (cid:99)()

[TPS_SWCT_01220] initValue defines an initial value that shall be taken if the corresponding dataElement has not yet been received (cid:100) The aggregation of ValueSpecification in the role initValue defines an initial value that shall be taken if the corresponding dataElement has not yet been received but the application software is attempting to access its value. This is the only relevant definition of an initial value for data transmission. That is, any initValue defined in the context of VariableDataPrototype is ignored! (cid:99)()

The communication attributes on the sender side are sketched in Figure 4.33.

Figure 4.32: DataFilter and its communication attributes.

Figure 4.32 shows the model of the communication attributes relevant for defining data filters.

[TPS_SWCT_01221] DataFilter (cid:100) For every RPortPrototype typed by a SenderReceiverInterface a DataFilter can be defined given that non-queued communication is foreseen. (cid:99)()

Fifteen filter algorithms formally described by the enumeration type DataFilterTypeEnum in the meta-model are taken from OSEK COM 3.0.3 specification [18] that is referenced by the RTE specification [2].

[TPS_SWCT_01222] Applicability of DataFilter (cid:100) This OSEK specification states that "filtering is only used for messages that can be interpreted as C language unsigned integer types (characters, unsigned integers and enumerations)." (cid:99)(RS_SWCT_03221)

[constr_1044] Applicability of DataFilter (cid:100) According to the origin of DataFilter, i.e. OSEK COM 3.0.3 specification [18], DataFilters can only be applied to values with an integer base type. (cid:99)()
Table 4.65: DataFilter
Table 4.66: DataFilterTypeEnum
[TPS_SWCT_01593] Semantics of attribute ReceiverComSpec.transformationComSpecProps (cid:100) The ReceiverComSpec.transformationComSpecProps is used to configure PortPrototype-specific properties for data transformation in case of receiving inter-ECU communication. (cid:99)()

[constr_1323] Applicability of attribute ReceiverComSpec.usesEndToEndProtection (cid:100) The attribute ReceiverComSpec.usesEndToEndProtection shall be set to false for all ReceiverComSpec that aggregate EndToEndTransformationDescription in the role transformationComSpecProps. (cid:99)()

See chapter 4.5.6 for details.

Figure 4.33: Communication attributes of PPortPrototype with respect to sender receiver communication.
Table 4.67: SenderComSpec
Table 4.68: QueuedSenderComSpec
Table 4.69: NonqueuedSenderComSpec
Table 4.70: TransmissionAcknowledgementRequest
Table 4.71: HandleOutOfRangeEnum

[TPS_SWCT_01223] networkRepresentation defines how a specific dataElement is represented on a communication bus (cid:100) For sender-receiver communication, it is possible to specify how dataElements are represented given that the communication requires the usage of a dedicated communication bus. That is, by means of the networkRepresentation it is possible to define how a specific dataElement is represented on a communication bus. For this purpose the networkRepresentation is implemented as an aggregation of SwDataDefProps. (cid:99)()

[TPS_SWCT_01224] CompuMethods of dataElement and the networkRepresentation are used for conversion purposes (cid:100) The attached CompuMethods of both the dataElement and the networkRepresentation can be used to identify the conversion between the two. The advantage of this approach is that this can also be used without any modifications in combination with a general remapping and rescaling of dataElements between different SwComponentTypes, regardless whether they are located on the same or on different ECUs. (cid:99)()

Please note that the decision whether or not to take the networkRepresentation for data mapping is done in the context of the AUTOSAR System Template [11]. Please find more detailed information about this aspect in the applicable specification.

[TPS_SWCT_01452] Applicability of networkRepresentation for ApplicationCompositeDataType (cid:100) The aggregation of networkRepresentation at the ReceiverComSpec or SenderComSpec only applies for dataElements typed by ApplicationPrimitiveDataTypes. For the case of using an ApplicationCompositeDataType an additional mechanism shall be used. In particular, compositeNetworkRepresentation shall be used to define the networkRepresentation of leaf elements of ApplicationCompositeDataTypes. (cid:99)()

[constr_1196] Existence of networkRepresentation vs. compositeNetworkRepresentation (cid:100) If a ReceiverComSpec or SenderComSpec aggregates networkRepresentation it shall not aggregate compositeNetworkRepresentation at the same time (and vice versa). (cid:99)()

[constr_1197] Existence of compositeNetworkRepresentation shall be comprehensive (cid:100) If at least one compositeNetworkRepresentation exists then for each leaf ApplicationCompositeElementDataPrototype of the affected ApplicationCompositeDataType exactly one compositeNetworkRepresentation shall be defined. (cid:99)()

Granted, the definition of [constr_1197] to some extent has a recursive character. The meaning is that if it is actually intended to define a compositeNetworkRepresentation then the definition shall be completely covering the entire set of leaf elements of the corresponding ApplicationCompositeDataType. In other words, it's all or nothing.
Table 4.72: CompositeNetworkRepresentation

#@SECTION: 4.5.2 Communication Speciﬁcation for Client-Server Communication
#@CLASS: ClientComSpec
#@CLASS: RPortPrototype
#@CLASS: ServerComSpec
#@CLASS: TransformationComSpecProps
#@CLASS: PortPrototype
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: OperationInvokedEvent
#@CLASS: RunnableEntity
#@CLASS: ClientServerOperations
#@CLASS: ApplicationCompositeElementDataPrototype


The communication aspects relevant for client communication are sketched in Figure 4.34.

Figure 4.34: Communication attributes of RPortPrototype with respect to client-server communication.

Table 4.73: ClientComSpec

The server side looks very similar but provides an attribute for specifying the queue length.

Figure 4.35: Communication attributes of PPortPrototype with respect to client-server communication.

Table 4.74: ServerComSpec

[TPS_SWCT_01225] RunnableEntity implements the functionality of two or more ClientServerOperations (cid:100) Please note that it is technically possible to let a single RunnableEntity implement the functionality of two or more ClientServerOperations. For this purpose two or more OperationInvokedEvents need to reference this single RunnableEntity.
In this case, however, it is essential that the queue length associated with each of the ClientServerOperations has the same value. In other words: (cid:99)()

[constr_1128] Queue length of ClientServerOperations associated with the same RunnableEntity (cid:100) If two or more OperationInvokedEvents reference a single RunnableEntity the value of the ServerComSpec attribute queueLength shall be identical for all ServerComSpecs owned by PPortPrototypes of the enclosing SwComponentType that reference one of the ClientServerOperations that are also referenced by the OperationInvokedEvents. (cid:99)()

[TPS_SWCT_01595] Semantics of attribute ClientComSpec.transformationComSpecProps (cid:100) The attribute ClientComSpec.transformationComSpecProps shall be used to configure PortPrototype-specific properties for data transformation in case of Client/Server inter-ECU communication for the reception of the server's response. (cid:99)(RS_SWCT_03221)

[TPS_SWCT_01596] Semantics of attribute ServerComSpec.transformationComSpecProps (cid:100) The attribute ServerComSpec.transformationComSpecProps shall be used to configure PortPrototype-specific properties for data transformation in case of Client/Server inter-ECU communication for the reception of the client's request. (cid:99)(RS_SWCT_03221)

See chapter 4.5.6 for details.

#@SECTION: 4.5.3 Communication Speciﬁcation for Mode Switch Communication
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeSwitchReceiverComSpec
#@CLASS: ModeSwitchSenderComSpec
#@CLASS: ModeSwitchedAckRequest
#@CLASS: PPortComSpec
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: PortPrototype
#@CLASS: RPortComSpec

In analogy to the previous section, Figure 4.36 shows the meta-model elements relevant for a mode switch communication. On the sender side it is possible to specify that an acknowledgement is supposed to be returned that indicates the successful processing of the mode switch request.

Figure 4.36: Communication attributes of PPortPrototype with respect to mode switch communication.

Figure 4.37: Communication attributes of PPortPrototype with respect to mode switch communication.

[TPS_SWCT_01514] Duplicate existence of enhancedModeApi in the context of a PRPortPrototype (cid:100) If the attribute enhancedModeApi is defined in a ModeSwitchReceiverComSpec owned by a PRPortPrototype its value shall be ignored. (cid:99)(RS_SWCT_03250)

Table 4.75: ModeSwitchSenderComSpec
Table 4.76: ModeSwitchedAckRequest
Table 4.77: ModeSwitchReceiverComSpec

#@SECTION: 4.5.4 Communication Speciﬁcation for Parameters
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: ParameterProvideComSpec
#@CLASS: ParameterRequireComSpec
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype

Granted, the deﬁnition of a ComSpec for ParameterDataPrototypes looks strange on ﬁrst sight. A ParameterDataPrototype owned by a PPortPrototype typed by a ParameterInterface is not actually transmitted over any communication medium. Therefore, the term communication should in this case be taken with a grain of salt.

However, it is generally necessary to be able to deﬁne role-speciﬁc initial values for ParameterDataPrototypes aggregated in a ParameterInterface. In other words, the actual problem closely resembles the deﬁnition of initial values in the case of sender-receiver communication.

[TPS_SWCT_01226] initValue on the level of a ComSpec is relevant for connections to the corresponding PortPrototype (cid:100) Please note that (along the example of sender-receiver communication) only the initValue deﬁned in the context of a ParameterProvideComSpec or ParameterRequireComSpec is relevant for connections to the corresponding PortPrototype. An initValue deﬁned in the scope of a ParameterDataPrototype is ignored. (cid:99)()

Therefore, it is only reasonable to apply the existing and well-known pattern to the deﬁnition of initial values for ParameterDataPrototypes aggregated in a ParameterInterface. The actual modeling is sketched in Figure 4.38 for provided ParameterDataPrototypes and in Figure 4.39 for required ParameterDataPrototypes.

Figure 4.38: Communication attributes of ParameterDataPrototypes with respect to PPortPrototype

Figure 4.39: Communication attributes of ParameterDataPrototypes with respect to RPortPrototype

Table 4.78: ParameterProvideComSpec

Table 4.79: ParameterRequireComSpec

#@SECTION: 4.5.5 Communication Speciﬁcation for NV Data
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: NvDataInterface
#@CLASS: NvProvideComSpec
#@CLASS: NvRequireComSpec
#@CLASS: SensorActuatorSwComponentType
#@CLASS: VariableDataPrototype

[TPS_SWCT_01141] AtomicSwComponentType may have AbstractRequiredPortPrototypes typed by an NvDataInterface (cid:100) An AtomicSwComponentType may have AbstractRequiredPortPrototypes typed by an NvDataInterface. If such an AbstractRequiredPortPrototype remains unconnected the nvData still need to have reasonable value. (cid:99)(RS_SWCT_03225)

Note that it is assumed that only a subset of meta-classes that inherit from AtomicSwComponentType will actually apply for the definition of initial values for nvData. Most likely the ApplicationSwComponentType and the SensorActuatorSwComponentType will be candidates for using this feature but it will obviously not be reasonable for e.g. NvBlockSwComponentType.

[TPS_SWCT_01227] Unconnected AbstractRequiredPortPrototype typed by NvDataInterface (cid:100) For this purpose it is possible to let the AbstractRequiredPortPrototype own an NvRequireComSpec that in turn owns a ValueSpecification in the role of initValue. It is therefore possible to provide an nvData with a reasonable value even if the corresponding AbstractRequiredPortPrototype remains unconnected. (cid:99)(RS_SWCT_03225)

Figure 4.40: Communication attributes of a required VariableDataPrototypes used in the context of an NvDataInterface

Please note that (along the example of sender-receiver communication, see [TPS_SWCT_01226]) only the initValue defined in the context of a NvRequireComSpec is relevant for connections to the corresponding PortPrototype. An initValue defined in the scope of a VariableDataPrototype is ignored.

[TPS_SWCT_01228] NvProvideComSpec (cid:100) As communication with an NvBlockSwComponentType is in most cases bi-directional it is also necessary to consider role specific communication attributes for AbstractProvidedPortPrototypes typed by an NvDataInterface. For this purpose the NvProvideComSpec (see Figure 4.41) is defined.
The main purpose of this kind of ComSpec is the definition of initial values for the RAM Block and the ROM Block that corresponds to an nvData defined in the context of the NvDataInterface used to type the given AbstractProvidedPortPrototype. (cid:99)(RS_SWCT_03225)

Note that these initial values can be taken as an input for designing an NvBlockSwComponentType, in particular the ramBlocks and romBlocks of NvBlockDescriptors owned by the NvBlockSwComponentType. Further details are explained in Figure 11.6.

Figure 4.41: Communication attributes of a provided VariableDataPrototypes used in the context of an NvDataInterface

In other words, by means of the NvProvideComSpec the author of an ApplicationSwComponentType can express detailed requirements on the later design of a corresponding NvBlockSwComponentType.

Table 4.80: NvRequireComSpec
Table 4.81: NvProvideComSpec

#@SECTION: 4.5.6 Conﬁguration of Data Transformation
#@CLASS: ClientComSpec
#@CLASS: EndToEndTransformationComSpecProps
#@CLASS: PortPrototype
#@CLASS: ReceiverComSpec
#@CLASS: ServerComSpec
#@CLASS: TransformationComSpecProps
#@CLASS: TransformationTechnology
#@CLASS: UserDefinedTransformationComSpecProps
#@CLASS: ISignal
#@CLASS: DataMapping
#@CLASS: DataPrototypeMapping
#@CLASS: VariableDataPrototype
#@CLASS: SystemSignal
#@CLASS: ISignalGroup

Using the TransformationComSpecProps it is possible to define configuration options for specific transformers of inter-ecu communication which is subject to data transformation.

[TPS_SWCT_01594] Semantics of TransformationComSpecProps (cid:100) The definition of a TransformationComSpecProps can always be provided in the SWC description but the configuration shall only have an effect if
1. the actual communication involves at least two EcuInstances
2. the respective data transformer (given by the used TransformationComSpecProps) is used during data transformation (see DataTransformation) (cid:99)(RS_SWCT_03221)

For clarification, the configuration given in TransformationComSpecProps will simply be ignored if the conditions defined by [TPS_SWCT_01594] do not apply.

[TPS_SWCT_01597] PortPrototype-specific data transformation configuration (cid:100) Meta-class TransformationComSpecProps shall be used for the specification of PortPrototype-specific configuration options for data transformation of inter-ECU communication. (cid:99)(RS_SWCT_03221)

Please note that only some transformers offer PortPrototype-specific configuration (e.g. SOME/IP transformer doesn't have TransformationComSpecProps).

Figure 4.42: Specification of data transformation properties within ReceiverComSpec, ServerComSpec, and ClientComSpec
Table 4.82: TransformationComSpecProps
It can be determined by the specific TransformationComSpecProps to which transformer this configuration is applicable:
• The configuration in EndToEndTransformationComSpecProps is applicable to E2E transformer (protocol of TransformationTechnology is set to EndToEnd).
• The configuration in UserDefinedTransformationComSpecProps is applicable to a user-defined transformer.

[TPS_SWCT_01598] More than one user-defined transformer is used within one transformer chain (cid:100) If more than one user-defined transformer is used within one transformer chain (defined by meta-class TransformationTechnology), the UserDefinedTransformationComSpecProps shall be assigned to the correct user-defined custom transformer in TransformationTechnology. (cid:99)(RS_SWCT_03221)

Figure 4.43: Big picture of data transformation in the AUTOSAR meta-model

[constr_1400] Reference to a specific DataTransformation (cid:100) A specific DataTransformation shall only be referenced by either
• a DataPrototypeMapping in the role firstToSecondDataTransformation or
• an ISignal in the role dataTransformation or
• an ISignalGroup in the role comBasedSignalGroupTransformation (cid:99)()

[constr_1401] Restrictions on the relation between DataPrototypeMapping and DataTransformation (cid:100) A VariableDataPrototype in the context of a PortPrototype shall not be referenced by a DataPrototypeMapping that references a DataTransformation while a DataMapping exists that points to this VariableDataPrototype (via the SystemSignal) that also refers to an ISignal that in turn references a DataTransformation. (cid:99)()

In other words: a VariableDataPrototype can either become a part of a DataPrototypeMapping-based data transformation or of an ISignal-based data transformation.

Please note that in a composite software structure the VariableDataPrototype can be delegated throughout the CompositionSwComponentType and [constr_1401] still applies.
Table 4.83: TransformationTechnology
Based on the user defined attributes inside UserDefinedTransformationComSpecProps (which are, of course, not standardized), the generator of the user defined transformer shall determine to which user-defined transformer a UserDefinedTransformationComSpecProps belongs to.
Table 4.84: UserDefinedTransformationComSpecProps
[TPS_SWCT_01599] PortPrototype-specific configuration for custom transformers (cid:100) Meta-class UserDefinedTransformationComSpecProps shall be used for the specification of PortPrototype-specific configuration options for custom transformers. (cid:99)(RS_SWCT_03221)

Please note that it is possible to add custom configuration items in UserDefinedTransformationComSpecProps by means of the attribute adminData.sdg.
Table 4.85: EndToEndTransformationComSpecProps
[TPS_SWCT_01600] PortPrototype-specific configuration for data transformers related to end-to-end protection (cid:100) Meta-class EndToEndTransformationComSpecProps shall be used for the specification of PortPrototype-specific configuration options for data transformers related to end-to-end protection. (cid:99)(RS_SWCT_03221)

#@SECTION: 4.6 Port Groups within Component Types
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: PortGroup
#@CLASS: PortPrototype
#@CLASS: SwComponentPrototype
#@CLASS: SwComponentType
#@CLASS: ServiceNeeds

[TPS_SWCT_01063] PortGroup (cid:100) A SwComponentType can declare that some of its PortPrototypes belong to a PortGroup. Such a port group defines a logical grouping of PortPrototypes which is used as input to configure the implementation of mode managers in the basic software, for example the communication of bus signals associated with the grouped ports maybe suppressed in a certain mode. (cid:99)(RS_SWCT_03200, RS_SWCT_03201)

Figure 4.44: Declaration of PortGroups
Table 4.86: PortGroup

[TPS_SWCT_01064] PortGroups have to be defined on the VFB level (cid:100) Though the declaration PortGroups is not relevant for the RTE, they have to be defined on the VFB level, because they represent design decisions taken on this level. Accordingly, PortGroups can be defined for CompositionSwComponentTypes as well as for AtomicSwComponentTypes. (cid:99)(RS_SWCT_03200, RS_SWCT_03201)

[TPS_SWCT_01065] PortPrototype may belong to more than one PortGroups (cid:100) A PortPrototype may belong to more than one PortGroups and PortGroups can be associated with the "inner" PortGroups of SwComponentPrototypes which are aggregated by the same SwComponentType as the PortGroup. By this, PortGroups can be locally defined but still traced down the component hierarchy. (cid:99)(RS_SWCT_03200, RS_SWCT_03201)

[TPS_SWCT_01066] PortGroups can be associated with certain ServiceNeeds (cid:100) PortGroups can be associated with certain ServiceNeeds in order to trace the information down to the configuration of the basic software, for details see chapter 7.11.2. (cid:99)(RS_SWCT_03200, RS_SWCT_03201)

[constr_1147] Standardized values for the attribute category of meta-class PortGroup (cid:100) The following values of the attribute category of meta-class PortGroup are reserved by the AUTOSAR standard:
• MODE_MANAGEMENT: This represents the usage of the PortGroup for the purpose of mode management
• PARTIAL_NETWORKING: This represents the usage of the PortGroup for the purpose of partial networking (cid:99)()

#@SECTION: 4.7 End to End Protection
#@CLASS: EndToEndDescription
#@CLASS: EndToEndProtection
#@CLASS: EndToEndProtectionSet
#@CLASS: EndToEndProtectionVariablePrototype
#@CLASS: RPortPrototype
#@CLASS: ReceiverComSpec

The aspect of end-to-end protection has seen different support by the AUTOSAR meta model.

On the one hand, there is the definition of dedicated meta-classes, e.g. EndToEndDescription, which aim at an implementation that uses a so-called E2E wrapper (an approach with a software component above RTE invoking the E2E library) or AUTOSAR Com module callout mechanism (with Com callouts used to invoke E2E library). This approach is documented in chapter 4.7 of this document.

As an alternative approach, it is possible to implement end-to-end protection using so-called data transformers. The detailed description of how this approach can be configured is beyond the scope of this document. Please refer to the TPS System Template [11] where the details of the alternative approach are explained.

In contrast to the approach based on the EndToEndProtection and EndToEndDescription (which partly involves technologies that are not subjected to the AUTOSAR standard), the second approach is fully standardized by AUTOSAR.

As described in [19] there are cases where safety-related software-components protect the data exchanged between each other. For this purpose modeling support is provided by the software-component template.

Note that several end-to-end profiles are selectable for a specific application. The specific end-to-end profile is represented by the attribute category of meta-class EndToEndDescription. Semantically, the category value represents an identification of the specific end-to-end profile applicable for the communication of the corresponding data element. According to [19] there are two pre-defined profiles that can be used.

[TPS_SWCT_01089] end-to-end communication protection (cid:100) The information specific to each profile is expressed by the set of attributes of EndToEndDescription owned by EndToEndProtection in the role endToEndProfile. (cid:99)(RS_SWCT_03240)
Table 4.87: EndToEndDescription
[TPS_SWCT_01090] EndToEndProtection (cid:100) EndToEndProtection is the Identifiable class that owns specific elements for referencing the to-be-protected data elements and signals • EndToEndProtectionVariablePrototype: a specific dataElement owned by a specific PortPrototype • EndToEndProtectionISignalIPdu: a specific ISignalGroup in the context of an ISignalIPdu. For more details please refer to [11] (cid:99)(RS_SWCT_03240)

[TPS_SWCT_01091] Two cases for end-to-end protection (cid:100) In order to protect a VariableDataPrototype the EndToEndProtectionVariablePrototype shall be defined. If communication is defined between ECUs using AUTOSAR COM the EndToEndProtectionISignalIPdu shall be defined as well. (cid:99)(RS_SWCT_03240)

The following features apply:
#@Hierarchical
• [constr_1000] End-to-end protection is limited to sender/receive communication (cid:100) end-to-end protection applies for sender/receiver communication only (cid:99)()
• The value of the dataId is assigned by a central authority rather than by the developer of the software-component.
• The information about the dataId shall be available at both the sender and the receiver(s).
• [constr_1001] Value of dataId shall be unique (cid:100) The value of the dataId shall be unique within the scope of the System. (cid:99)()
• [TPS_SWCT_01508] Scope of end-to-end protection (cid:100) End-to-end protection applies to local (i.e. within the ECU) as well as remote (i.e. ECU to ECU) communication. (cid:99)(RS_SWCT_03240)
/#@Hierarchical
[TPS_SWCT_01092] EndToEndProtectionSet (cid:100) The meta-class EndToEndProtectionSet provides a container for EndToEndProtection. The aggregation is stereotyped (cid:28)atpSplitable(cid:29) because the information about end-to-end protection is added at a later step in the development workflow. (cid:99)(RS_SWCT_03240)

It also has the stereotype (cid:28)atpVariation(cid:29) because this allows for implementing the software-component in two variants, one that uses end-to-end protection and one that does not use it. It also might happen that the communication ends themselves are variant.

EndToEndProtection maintains InstanceRefs to one dataElement in the role of sender and to one or many dataElements in the role of receiver. By this means it is possible to support a 1:n communication scenario.

[TPS_SWCT_01093] Definition of end-to-end protection is splitable (cid:100) EndToEndProtection stereotype (cid:28)atpSplitable(cid:29). By this means it is for the integrator of an ECU possible to generally specify the nature of a specific end-to-end protection but leave the actual assignment of values (e.g. for dataId) to a later process step. (cid:99)(RS_SWCT_03240)

Figure 4.45: Details of the modeling of end-to-end protection

According to [19] the following constraints apply on the attributes of EndToEndProtection (note that additional M1 constraints apply as described in [19]):

[constr_1110] Value of category in EndToEndDescription (cid:100) The attribute category of EndToEndDescription can have the following values:
• NONE 
• PROFILE_01 
• PROFILE_02 (cid:99)()

[TPS_SWCT_01094] category of EndToEndDescription (cid:100) The values for the category of EndToEndDescription mentioned in [constr_1110] are standardized and reserved for being used in the way the AUTOSAR standard foresees. In addition, it is positively possible to use other than the standardized values for the category. (cid:99)(RS_SWCT_03240)

This aspect will be clarified in more detail in later revisions of the AUTOSAR standard. For the time being, it shall be noted that the usage of other than the standardized values shall not create name clashes with future standardized values. This can be achieved by using e.g. a company-specific prefix or suffix to the value of category.

The semantics of the categorys is:
#@Hierarchical
NONE this indicates that the E2E framework shall be enabled for the given sender/receiver respectively the given iSignalIPdu. The wrapper code shall be generated but it shall not invoke E2E library protection routines. E2E wrapper works as pass-through. This may be used when a profile selection or profile options are not yet selected in a given system but it is required that the system can be built successfully under consideration of the E2E library. This would also be applicable for migrating from/to a system with/without E2E protection.

[TPS_SWCT_01095] category set to NONE (cid:100) If attributes exist in the presence of the category being set to NONE the attributes shall be ignored. (cid:99)(RS_SWCT_03240)
/#@Hierarchical

#@Hierarchical
PROFILE_01 This indicates that the settings of E2E profile 1 (that uses a SAE CRC8, implicit 16 bit data ID, and a 4 bit alive counter) apply.

[constr_1113] Existence of attributes in PROFILE_01 (cid:100) In PROFILE_01, the following attributes shall exist: 
• dataLength 
• dataId (cid:99)()

Please note that the attribute maxDeltaCounterInit is also part of PROFILE_01 but it does not necessarily have to exist provided that ReceiverComSpec.maxDeltaCounterInit exists.

[constr_1170] Interpretation of attribute maxDeltaCounterInit owned by EndToEndDescription (cid:100) If EndToEndProtection.endToEndProtectionVariablePrototype.receiver is identical to the RPortPrototype.requiredComSpec.dataElement and RPortPrototype.requiredComSpec.maxDeltaCounterInit is defined then the value of RPortPrototype.requiredComSpec.maxDeltaCounterInit shall be preferred over the value of EndToEndProtection.endToEndProfile.maxDeltaCounterInit. If the value of category of EndToEndDescription is set to PROFILE_01 and either the described correspondence rule concerning the referenced VariableDataPrototype is not fulfilled or RPortPrototype.requiredComSpec.maxDeltaCounterInit is not defined then EndToEndProtection.endToEndProfile.maxDeltaCounterInit shall exist. (cid:99)()

[constr_1111] Constraints of dataId in PROFILE_01 (cid:100) In PROFILE_01, there shall be only one element in the set and the applicable range of values is [0 .. 65535]. (cid:99)()

[constr_1112] Constraints of dataIdMode in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for dataIdMode is [0 .. 3]. (cid:99)()

[constr_1114] Constraints of crcOffset in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for crcOffset is [0 .. 65535]. For the value of this attribute the constraint value mod 4 = 0 applies. (cid:99)()

[constr_1115] Constraints of counterOffset in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for counterOffset is [0 .. 65535]. For the value of this attribute the constraint value mod 4 = 0 applies. (cid:99)()

[constr_1116] Constraints of dataLength in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for dataLength is [0 .. 240]. For the value of this attribute the constraint value mod 8 = 0 applies. (cid:99)()

[constr_1117] Constraints of maxDeltaCounterInit in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for EndToEndDescription.maxDeltaCounterInit and ReceiverComSpec.maxDeltaCounterInit is [0 .. 14]. (cid:99)()

[constr_1211] Constraints of maxNoNewOrRepeatedData in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for EndToEndDescription.maxNoNewOrRepeatedData and ReceiverComSpec.maxNoNewOrRepeatedData is [0 .. 14]. (cid:99)()

[constr_1212] Constraints of syncCounterInit in PROFILE_01 (cid:100) In PROFILE_01, the applicable range of values for EndToEndDescription.syncCounterInit and ReceiverComSpec.syncCounterInit is [0 .. 14]. (cid:99)()

[constr_1215] Interpretation of attribute maxNoNewOrRepeatedData owned by EndToEndDescription in PROFILE_01 (cid:100) If EndToEndProtection.endToEndProtectionVariablePrototype.receiver is identical to the RPortPrototype.requiredComSpec.dataElement and RPortPrototype.requiredComSpec.maxNoNewOrRepeatedData is defined then the value of RPortPrototype.requiredComSpec.maxNoNewOrRepeatedData shall be preferred over the value of EndToEndProtection.endToEndProfile.maxNoNewOrRepeatedData. If the value of category of EndToEndDescription is set to PROFILE_01 and either the described correspondence rule concerning the referenced VariableDataPrototype is not fulfilled or RPortPrototype.requiredComSpec.maxNoNewOrRepeatedData is not defined then EndToEndProtection.endToEndProfile.maxNoNewOrRepeatedData shall exist. (cid:99)()

[constr_1216] Interpretation of attribute syncCounterInit owned by EndToEndDescription in PROFILE_01 (cid:100) If EndToEndProtection.endToEndProtectionVariablePrototype.receiver is identical to the RPortPrototype.requiredComSpec.dataElement and RPortPrototype.requiredComSpec.syncCounterInit is defined then the value of RPortPrototype.requiredComSpec.syncCounterInit shall be preferred over the value of EndToEndProtection.endToEndProfile.syncCounterInit. If the value of category of EndToEndDescription is set to PROFILE_01 and either the described correspondence rule concerning the referenced VariableDataPrototype is not fulfilled or RPortPrototype.requiredComSpec.syncCounterInit is not defined then EndToEndProtection.endToEndProfile.syncCounterInit shall exist. (cid:99)()

[constr_1261] Applicability for EndToEndDescription.dataIdNibbleOffset (cid:100) EndToEndDescription.dataIdNibbleOffset shall be used only if EndToEndDescription.dataIdMode is set to the value 3 and at the same time EndToEndDescription.category is set to PROFILE_01. (cid:99)()

[TPS_SWCT_01529] Default value for EndToEndDescription.dataIdNibbleOffset (cid:100) If EndToEndDescription.dataIdMode is set to the value 3 and at the same time EndToEndDescription.category is set to the value PROFILE_01 and EndToEndDescription.dataIdNibbleOffset is not specified, then the default value of 12 (bits) shall be assumed for the attribute EndToEndDescription.dataIdNibbleOffset. (cid:99)(RS_SWCT_03240)
/#@Hierarchical
#@Hierarchical
PROFILE_02 this indicates that the settings of E2E profile 2 apply.

[constr_1118] Existence of attributes in PROFILE_02 (cid:100) In PROFILE_02, only the following attributes shall exist: 
• dataLength 
• dataId (cid:99)()

Please note that the attribute maxDeltaCounterInit is also part of PROFILE_01 but it does not necessarily have to exist provided that ReceiverComSpec.maxDeltaCounterInit exists.

[constr_1171] Interpretation of attribute maxDeltaCounterInit of EndToEndDescription (cid:100) If EndToEndProtection.endToEndProtectionVariablePrototype.receiver is identical to the RPortPrototype.requiredComSpec.dataElement and RPortPrototype.requiredComSpec.maxDeltaCounterInit is defined then the value of RPortPrototype.requiredComSpec.maxDeltaCounterInit shall be preferred over the value of EndToEndProtection.endToEndProfile.maxDeltaCounterInit. If the value of category of EndToEndDescription is set to PROFILE_02 and either the described correspondence rule concerning the referenced VariableDataPrototype is not fulfilled or RPortPrototype.requiredComSpec.maxDeltaCounterInit is not defined then EndToEndProtection.endToEndProfile.maxDeltaCounterInit shall exist. (cid:99)()

[constr_1119] Constraints of dataLength in PROFILE_02 (cid:100) In PROFILE_02, the applicable range of values for dataLength is [0 .. 65535]. For the value of this attribute the constraint value mod 8 = 0 applies. (cid:99)()

[constr_1120] Constraints of dataId in PROFILE_02 (cid:100) In PROFILE_02, there shall be exactly ordered 16 elements in the set and the applicable range of values is [0 .. 255]. (cid:99)()

[constr_1121] Constraints of maxDeltaCounterInit in PROFILE_02 (cid:100) In PROFILE_02, the applicable range of values for EndToEndDescription.maxDeltaCounterInit and ReceiverComSpec.maxDeltaCounterInit is [0 .. 15]. (cid:99)()

[constr_1213] Constraints of maxNoNewOrRepeatedData in PROFILE_02 (cid:100) In PROFILE_02, the applicable range of values for EndToEndDescription.maxNoNewOrRepeatedData and ReceiverComSpec.maxNoNewOrRepeatedData is [0 .. 15]. (cid:99)()

[constr_1214] Constraints of syncCounterInit in PROFILE_02 (cid:100) In PROFILE_02, the applicable range of values for EndToEndDescription.syncCounterInit and ReceiverComSpec.syncCounterInit is [0 .. 15]. (cid:99)()

[constr_1217] Interpretation of attribute maxNoNewOrRepeatedData owned by EndToEndDescription in PROFILE_02 (cid:100) If EndToEndProtection.endToEndProtectionVariablePrototype.receiver is identical to the RPortPrototype.requiredComSpec.dataElement and RPortPrototype.requiredComSpec.maxNoNewOrRepeatedData is defined then the value of RPortPrototype.requiredComSpec.maxNoNewOrRepeatedData shall be preferred over the value of EndToEndProtection.endToEndProfile.maxNoNewOrRepeatedData. If the value of category of EndToEndDescription is set to PROFILE_02 and either the described correspondence rule concerning the referenced VariableDataPrototype is not fulfilled or RPortPrototype.requiredComSpec.maxNoNewOrRepeatedData is not defined then EndToEndProtection.endToEndProfile.maxNoNewOrRepeatedData shall exist. (cid:99)()

[constr_1218] Interpretation of attribute syncCounterInit owned by EndToEndDescription in PROFILE_02 (cid:100) If EndToEndProtection.endToEndProtectionVariablePrototype.receiver is identical to the RPortPrototype.requiredComSpec.dataElement and RPortPrototype.requiredComSpec.syncCounterInit is defined then the value of RPortPrototype.requiredComSpec.syncCounterInit shall be preferred over the value of EndToEndProtection.endToEndProfile.syncCounterInit. If the value of category of EndToEndDescription is set to PROFILE_02 and either the described correspondence rule concerning the referenced VariableDataPrototype is not fulfilled or RPortPrototype.requiredComSpec.syncCounterInit is not defined then EndToEndProtection.endToEndProfile.syncCounterInit shall exist. (cid:99)()
/#@Hierarchical

Table 4.87: EndToEndDescription
Table 4.88: EndToEndProtectionSet
Table 4.89: EndToEndProtection
Table 4.90: EndToEndProtectionVariablePrototype

Please note that using end-to-end protection it is explicitly supported that one sender may correspond to one or more receivers.

[constr_1183] EndToEndProtectionVariablePrototypes aggregated by EndToEndProtection (cid:100) All EndToEndProtectionVariablePrototypes aggregated by the same EndToEndProtection shall refer to the identical sender. (cid:99)()

#@SECTION: 4.8 Partial Networking
#@CLASS: PortGroup
#@CLASS: PortPrototype
#@CLASS: SenderReceiver
#@CLASS: VirtualFunctionCluster

[TPS_SWCT_01169] Support for partial networking (cid:100) On the level of the Software Component Template, partial networking is supported by means of the concept of a “Virtual Function Cluster” (VFC). The latter groups all communication on the VFB with respect to a given function. However, the conceptual idea of a Virtual Function Cluster is not represented in the meta-model as such. Instead, PortGroups (see chapter 4.6) are used to specify the grouping of PortPrototypes to the higher conceptual level of a Virtual Function Cluster. (cid:99)(RS_SWCT_03241, RS_SWCT_03201)

There are no restrictions regarding the structure of PortGroup definitions on M1. One PortPrototype may become a member of several PortGroups, thereby creating overlapping PortGroups.

[TPS_SWCT_01170] Purpose of Virtual Function Cluster (cid:100) The purpose of Virtual Function Cluster within the Software Component Template mainly has three aspects:

1. assign PortPrototypes (non service related) of Sender Receiver or Client Server communication to Virtual Function Clusters.
2. control the behavior of the corresponding function in terms of whether or not it is required at a given point in time. This aspect is implemented by the concept of a control port. Software-components that implement control ports of a Virtual Function Cluster conceptually become VFC Controllers.
3. allow for the application software to retrieve the status of a given Virtual Function Cluster. This aspect is implemented by the concept of a status port. (cid:99)(RS_SWCT_03241)

The usage of the generic concept of PortGroups for the purpose of partial networks shall be indicated by setting the value of the attribute category of PortGroup to PARTIAL_NETWORKING.

#@SECTION: 4.8.1 VFC Control Ports
#@CLASS: ClientServerInterface
#@CLASS: PortGroup
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface
#@CLASS: SwcServiceDependency
#@CLASS: PortInterface
[TPS_SWCT_01171] Purpose of a control port (cid:100) The purpose of a control port is to request or release a VFC. Requesting means that the VFC is actively using the communication resources while release boils down to the VFC being inactive, i.e. corresponding partial network may be shut down until further notice. As the requesting and releasing semantics is implemented by means of interfacing the BSW the corresponding control ports need to be typed by a PortInterface that has the attribute isService set to true. (cid:99)(RS_SWCT_03241)

[TPS_SWCT_01172] Requesting and releasing partial networks (cid:100) For requesting and releasing partial networks, the BSW can be interfaced in two alternative (i.e. either one or the other) ways:
• ComM: ClientServerInterface using the standardized ComM_UserRequest.RequestComMode [20]
• BswM: SenderReceiverInterface using the standardized AppModeRequestInterface.requestedMode [15]
(cid:99)(RS_SWCT_03241)

[TPS_SWCT_01173] Control port shall not become a part of the PortGroup (cid:100) Please note that the control port shall not become a part of the PortGroup that defines the particular VFC the control port is going to service. The relationship is implemented by means of a specific SwcServiceDependency that owns a RoleBasedPortAssignment to the intended control port. (cid:99)(RS_SWCT_03241, RS_SWCT_03201)

#@SECTION: 4.8.2 VFC Status Ports
#@CLASS: ClientServerInterface
#@CLASS: ModeDeclaration
#@CLASS: ModeSwitchInterface
#@CLASS: PortGroup
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface
#@CLASS: SwcServiceDependency

[TPS_SWCT_01175] Actively query the status of a partial network (cid:100) Very much like mode management, the concept of partial networking supports the ability to actively query the status of a partial network.

This can be done by means of interfacing the BSW in three alternative (as in “one of”) ways:
• ComM: ClientServerInterface using the standardized ComM_UserRequest.GetCurrentComMode [20]
• ComM: ModeSwitchInterface using the standardized ComM_CurrentMode.currentMode [20]
• BswM: ModeSwitchInterface using the standardized AppModeInterface.currentMode [15] (cid:99)(RS_SWCT_03241)

As mentioned above, the ComM can be retrieved by either a ClientServerInterface or a SenderReceiverInterface. Which of the two alternatives applies in a speciﬁc case is up to the author of a software-component.

When using one of the possible SenderReceiverInterfaces, the correspondence of the status port concept with mode management extends to the point that the status of the partial network is returned as an actual ModeDeclaration.
The usage of the ClientServerInterface effectively implements a “pull” approach for the mode
information while the usage of the SenderReceiverInterface resembles a “push” approach if it is used in combination with a SwcModeSwitchEvent.
This implies that all mechanisms foreseen by the Software Component Template to react on mode changes are in place and can be used within the application software.

To assure that the communication via PortPrototypes that belong to a partial network is valid the software component shall consider the status of the partial network before communicating in order to assert its activity.

[TPS_SWCT_01174] Status port shall not become a member of the PortGroup (cid:100) A status port shall not become a member of the PortGroup that corresponds to the partial network subject to the status port. The relationship is implemented by means of a speciﬁc SwcServiceDependency that owns a RoleBasedPortAssignment to the intended status port. (cid:99)(RS_SWCT_03241, RS_SWCT_03201)

#@SECTION: 4.9 Formal Deﬁnition of implicit Communication Behavior
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: ConsistencyNeeds
#@CLASS: DataPrototype
#@CLASS: DataPrototypeGroup
#@CLASS: RunnableEntity
#@CLASS: RunnableEntityGroup
#@CLASS: VariableDataPrototype

[TPS_SWCT_01509] Implicit communication behavior (cid:100) The purpose of the formal definition of the behavior of a SwComponentType with respect to the implicit communication can conceptually condensed to two basic aspects:

• Stable data during the execution of a group of RunnableEntitys. This means that all data values read by different RunnableEntitys are from the same age. Therefore the value is not changing during the execution of the chain of RunnableEntitys.

• Coherent data consumption and propagation for a group of DataPrototypes. This means that a set of interdependent data values are from the same calculation iteration. Therefore the set of values has to be propagated at once to RunnableEntitys requiring the complete result of the calculation. RunnableEntitys which are part of the calculation chain may still consume partly updated values. (cid:99)(RS_SWCT_03065)

[TPS_SWCT_01481] The meaning of the term stability with respect to ConsistencyNeeds (cid:100) The meaning of the term stability is that the values of a group of VariableDataPrototypes shall not change values during the execution of a group of RunnableEntitys. (cid:99)(RS_SWCT_03065)

[TPS_SWCT_01482] The meaning of the term coherence with respect to ConsistencyNeeds (cid:100) The meaning of the term coherence means that the values of a group of VariableDataPrototypes shall not be read by receiving RunnableEntitys until all the producing RunnableEntitys are terminated. (cid:99)(RS_SWCT_03065)

In response to these goals the meta-model provides means to express the correlation between a group of RunnableEntitys and a group of DataPrototypes. These groups might be defined hierarchically.

The information (in terms of ConsistencyNeeds) can be defined primarily during the design of an AtomicSwComponentType but it is just as well possible to specify this ConsistencyNeeds during the definition of CompositionSwComponentTypes.

For example, the existence of stable data is typically expected for the execution of RunnableEntitys of several AtomicSwComponentTypes.

Figure 4.46: Formal definition of implicit communication behavior

Please note that the two aspects stability and coherence are not necessarily connected to each other. It is possible to require stability without coherence and vice versa. For this purpose the roles dpgDoesNotRequireCoherence and regDoesNotRequireStability are needed.

[TPS_SWCT_01480] Stability and/or coherence is not required (cid:100) In order to be able to clearly separate the aspect of stability from coherence it is possible to use the roles dpgDoesNotRequireCoherence to express that a group of VariableDataPrototypes explicitly does not require consistency. Likewise, regDoesNotRequireStability can be used to express that for a group of RunnableEntitys stability with respect to data access is not required. (cid:99)()

[TPS_SWCT_01479] Applicability of ConsistencyNeeds (cid:100) ConsistencyNeeds can only be applied to RunnableEntitys that make use of "implicit" communication. (cid:99)(RS_SWCT_03065)

[TPS_SWCT_01466] ConsistencyNeeds applied on RunnableEntitys that do not use implicit communication (cid:100) If a ConsistencyNeeds is applied on RunnableEntitys that do not use implicit communication it shall be ignored. (cid:99)(RS_SWCT_03065)

The formal definition of the implicit communication behavior foresees the grouping of model elements in order to indicate their relevance for consistent implicit communication.

[TPS_SWCT_01470] RunnableEntityGroup (cid:100) A RunnableEntitys belongs to a specific RunnableEntityGroup if it is associated either directly with the given RunnableEntityGroup or if the RunnableEntityGroup the RunnableEntity belongs to is eventually (there can be more than one nesting level) referenced by the given RunnableEntityGroup. (cid:99)(RS_SWCT_03065)

[TPS_SWCT_01471] DataPrototypeGroup (cid:100) A VariableDataPrototypes belongs to a specific DataPrototypeGroup if it is associated either directly with the given DataPrototypeGroup or if the DataPrototypeGroup the VariableDataPrototype belongs to is eventually (there can be more than one nesting level) referenced by the given DataPrototypeGroup. (cid:99)(RS_SWCT_03065)

[constr_1231] ConsistencyNeeds aggregated by CompositionSwComponentType (cid:100) If ConsistencyNeeds are aggregated by a CompositionSwComponentType the associations stereotyped (cid:28)instanceRef(cid:29) may only refer to context and target elements within the context of this CompositionSwComponentType. (cid:99)()

For clarification, [constr_1231] includes VariableDataPrototypes owned by delegation PortPrototypes of the owning CompositionSwComponentType, VariableDataPrototypes in delegation PortPrototypes of CompositionSwComponentType instantiated in the enclosing CompositionSwComponentType, or VariableDataPrototypes in PortPrototypes owned by AtomicSwComponentTypes instantiated inside the context of the enclosing CompositionSwComponentType.

[constr_1232] ConsistencyNeeds aggregated by AtomicSwComponentType (cid:100) If ConsistencyNeeds are aggregated by a AtomicSwComponentType the associations stereotyped (cid:28)instanceRef(cid:29) may only refer to context and target elements within the context of this AtomicSwComponentType. (cid:99)()

Strictly speaking, these are the RunnableEntitys and PortPrototypes of this particular AtomicSwComponentType or RunnableEntityGroups and DataPrototypeGroups which are owned by the same AtomicSwComponentType.

Please note that pre-defined values for the category of RunnableEntityGroup and DataPrototypeGroup are described in [1].

Table 4.91: ConsistencyNeeds
Table 4.92: RunnableEntityGroup
Table 4.93: DataPrototypeGroup

#@SECTION: 4.9.1 Consistency Needs on Receiver Side
#@CLASS: DataPrototypeGroup
#@CLASS: RunnableEntity
#@CLASS: RunnableEntityGroup
#@CLASS: SwComponentType
#@CLASS: VariableDataPrototype

[TPS_SWCT_01472] Receiving SwComponentType owns a DataPrototypeGroup in the role dpgRequiresCoherence (cid:100) If a receiving SwComponentType owns a DataPrototypeGroup in the role dpgRequiresCoherence for one or several of its RunnableEntitys it is required that VariableDataPrototypes belonging to the same DataPrototypeGroup are produced coherently. This means the values of the VariableDataPrototypes shall be of the same age. (cid:99)(RS_SWCT_03065)

[TPS_SWCT_01473] Receiving SwComponentType owns a RunnableEntityGroup in the role regRequiresStability (cid:100) If a receiving SwComponentType owns a RunnableEntityGroup in the role regRequiresStability for one or several of its RunnableEntitys it is required that the values of implicitly communicated VariableDataPrototypes are kept stable over the execution of all RunnableEntitys belonging to the given RunnableEntityGroup. (cid:99)(RS_SWCT_03065)

[TPS_SWCT_01474] Receiving SwComponentType owns a RunnableEntityGroup in the role regRequiresStability and also owns one or several DataPrototypeGroups in the role dpgRequiresCoherence (cid:100) If a receiving SwComponentType owns a RunnableEntityGroup in the role regRequiresStability and also owns one or several DataPrototypeGroups in the role dpgRequiresCoherence it is required that values of VariableDataPrototypes belonging to the same DataPrototypeGroup are produced coherently. This means that the values of the VariableDataPrototypes shall be of the same age and are kept stable over the execution of all RunnableEntitys belonging to the given RunnableEntityGroup. (cid:99)()

#@SECTION: 4.9.2 Consistency Needs on Sender Side
#@CLASS: DataPrototypeGroup
#@CLASS: RunnableEntity
#@CLASS: RunnableEntityGroup
#@CLASS: SwComponentType
#@CLASS: VariableDataPrototype

[TPS_SWCT_01475] Sending SwComponentType owns a DataPrototypeGroup in the role dpgRequiresCoherence (cid:100) If a sending SwComponentType owns a DataPrototypeGroup in the role dpgRequiresCoherence for one or several of its RunnableEntitys it is required that VariableDataPrototypes belonging to the same DataPrototypeGroup are propagated at the same point of time to RunnableEntitys which are not belonging to the group of producing RunnableEntitys (which may, but don’t have to be formally described as a RunnableEntity Group). (cid:99)(RS_SWCT_03065)

The coherence is created at the point in time when the RunnableEntitys of the producing group of RunnableEntitys terminate (and the implicit data get updated). If those RunnableEntitys are reading the data also, those read accesses will not read the coherent values but the intermediary values written by RunnableEntitys of the same group. For all other RunnableEntitys that are not member of the producing group of RunnableEntitys it appears as if the data have been updated at this very point coherently. In order to avoid incorrect configurations its possible to explicitly define the group of RunnableEntitys for which the coherency does not apply.

[TPS_SWCT_01625] Sending SwComponentType owns a DataPrototypeGroup in the role dpgRequiresCoherence and also RunnableEntityGroups (cid:100) If a sending SwComponentType owns a DataPrototypeGroup in the role dpgRequiresCoherence, RunnableEntityGroups in the role regDoesNotRequireStability may exist. Read accesses from RunnableEntitys in those RunnableEntityGroups will not read the coherent values but the intermediary values written by RunnableEntitys of the same group. (cid:99)(RS_SWCT_03065)

#@SECTION: 4.9.3 Consistency Needs for Senders and receivers of the same Data inside on RunnableEntityGroup
#@CLASS: RunnableEntityGroup
#@CLASS: VariableDataPrototypes

[TPS_SWCT_01476] Sender and receiver of the same implicitly communicated VariableDataPrototypes are associated with the same RunnableEntity Group (cid:100) For the case of sender and receiver of the same implicitly communicated VariableDataPrototypes are associated with the same RunnableEntityGroup [TPS_SWCT_01472], [TPS_SWCT_01473], [TPS_SWCT_01475] as well as [TPS_SWCT_01475] apply with the exception that updates of the values of implicitly communicated VariableDataPrototypes inside the given RunnableEntityGroup become visible immediately after the producing RunnableEntity was terminated. (cid:99)(RS_SWCT_03065)
