#@SECTION: 2 Conceptual Aspects
#@SECTION: 2.1 Introduction

For the sake of a compact description of relevant meta-model elements the discussion
and explanation of conceptual aspects has been concentrated in this chapter.
Reading this chapter is not a pre-requisite for understanding the subsequent chapters.
It just provides a central place for the detailed description of conceptual aspects used
in various other chapters of this document.
The actual explanation of the concept of a software-component starts in chapter 3.

#@SECTION: 2.2 Measurement and Calibration
#@CLASS: DataPrototype
#@CLASS: SwComponentPrototype
#@CLASS: SwcInternalBehavior
#@CLASS: SwComponentType
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortPrototype
#@CLASS: CompositionSwComponentType
#@CLASS: SwConnector
#@CLASS: RPortPrototype
#@CLASS: AssemblySwConnector
#@CLASS: DelegationSwConnector
#@CLASS: AtomicSwComponentType

#@SECTION: 2.2.1 Basic Approach of Measurement and Calibration

While performing the calibration process using a MCD tool (Measurement, Calibration,
and Diagnostic) the calibration engineer needs to have a speciﬁc insight to the data within the CPU at runtime.
This insight is provided by access to ECU internal variables (also called measurements) as well as calibration parameters (sometimes also called characteristic value).
For more details, please refer to [TPS_SWCT_01418]
The description of measurement variables and calibration parameters is basically the same. In AUTOSAR both appear ﬁnally as DataPrototypes.

#@SECTION: 2.2.2 Calibration Parameters Overview

A Calibration Parameter is a parameter which characterizes the dynamics of a control algorithm. From a software implementation point of view, it is a variable with only read-access during the normal operation of an ECU. Characteristics are specialized DataPrototype entities in terms of its associated type but are used in a similar way.
[TPS_SWCT_01418] Ways to deﬁne a calibration parameter (cid:100) This means that Calibration Parameters can be deﬁned
• individually for a SwComponentPrototype in the SwcInternalBehavior of a SwComponentType via an aggregation of an ParameterDataPrototype in the role of perInstanceParameter (similar to PerInstanceMemory) (see chapter 2.2.3.3)
• sharing between all SwComponentPrototypes of the same SwComponentType in its SwcInternalBehavior via an aggregation of an ParameterDataPrototype in the role of sharedParameter or constantMemory (see chapter 2.2.3.2)
• for several SwComponentPrototypes (using the port-/interface-concept with ParameterInterfaces) (see chapter 2.2.3.1).
(cid:99)()

Figure 2.1: Some Categories of calibration parameters
Note: the structure of various calibration objects is visualized in [14].

#@SECTION: 2.2.3 Using Calibration Parameters

As mentioned above, a ParameterDataPrototype can be used in the context of
SwcInternalBehavior as well as in the context of PortPrototypes.

#@SECTION: 2.2.3.1 Sharing Calibration Parameters within Compositions

To provide calibration parameters for being visible in other SwComponentTypes, a dedicated ParameterSwComponentType (see Figure 3.4) that inherits from SwComponentType has to be used as a SwComponentPrototype within a CompositionSwComponentType.

Table 2.1: ParameterSwComponentType

[TPS_SWCT_01420] SwComponentType requiring access to shared calibration parameters needs RPortPrototype typed by a ParameterInterface (cid:100) Every SwComponentType requiring access to shared calibration parameters will have an RPortPrototype typed by a ParameterInterface. The deﬁnition of this shared calibration access in the context of a CompositionSwComponentType will be deﬁned by creating a SwConnector between the relevant SwComponentPrototypes. (cid:99)()

Table 2.2: ParameterInterface

[TPS_SWCT_01421] ParameterInterface is not restricted to parameters which can actually can be calibrated (cid:100) Note that a ParameterInterface is not restricted to parameters which can actually can be calibrated. It can be used whenever there shall be no write access to the data during normal operation of the software, i.e. only constant data are visible over the interface. (cid:99)()

The compatibility rules for ParameterInterfaces are described in chapter 6.4; the compatibility rules for ParameterDataPrototypes are described in chapter 6.4.4.

[TPS_SWCT_01422] Delegation of PortPrototypes typed by a ParameterInterface (cid:100) Access to shared calibration parameters can be provided and required even over CompositionSwComponentTypes using DelegationSwConnectors and AssemblySwConnectors.
This means that each access to calibration parameters between SwComponentPrototypes is explicitly visible. If a SwConnector spans after the mapping of SwComponentPrototypes over two different ECUs the system generation process has to ensure the proper allocation of the ParameterDataPrototype (see Figure 2.2) while the calibration system has to cope with setting the parameter synchronously on the affected ECUs. (cid:99)()

Figure 2.2: ParameterInterface

#@SECTION: 2.2.3.2 Sharing Calibration Parameters between SwComponentPrototypes of the Same SwComponentType

To share calibration parameters between several SwComponentPrototypes of the
same SwComponentType, a ParameterDataPrototype is attached to an SwcInternalBehavior in sharedParameter role (see [TPS_SWCT_01418]).

When the SwcInternalBehavior is aggregated by an AtomicSwComponentType
the actual calibration parameters of the ParameterDataPrototype is the same for all SwComponentPrototypes.

[TPS_SWCT_01423] ParameterDataPrototype aggregated in the role constantMemory (cid:100) Additionally, it is possible to describe the implementation of shared characteristic values via a ParameterDataPrototype which is attached to an SwcInternalBehavior in the role constantMemory.
In contrast to the ParameterDataPrototype in sharedParameter role this kind
of memory is not instantiated by the RTE. This supports more efﬁcient implementations (especially for software components provided as object code) by avoidance of the additional indirection caused by the RTE’s component data structure. (cid:99)()

Further on this kind of memory reduces the dependencies of the software-component’s implementation to generated RTE code which is appreciated for safety related functionalities.

Nevertheless the information about these characteristic values has to be taken into account for the A2L ﬁle generation.

A typical example for this kind of sharing code between instances is dealing with two lambda sensors in multiple cylinder-bank engines, where (at least) two SwComponentPrototypes for each lambda sensor will use the very same Calibration Parameters.

#@SECTION: 2.2.3.3 Providing Instance Individual Characteristic Data

[TPS_SWCT_01424] ParameterDataPrototype aggregated in the role perInstanceParameter (cid:100) To provide instance individual calibration parameters a ParameterDataPrototype is owned by a SwcInternalBehavior in perInstanceParameter role.
When the SwcInternalBehavior is attached to an AtomicSwComponentType, the
actual calibration values are speciﬁc for each SwComponentPrototype. (cid:99)()

Figure 2.3: ParameterDataPrototypes in internal behavior

#@SECTION: 2.3 Runtime and Data Consistency Aspects
#@CLASS: RunnableEntity

#@SECTION: 2.3.1 Background: the Issues

This section gives some background information and lists possible strategies concerning the implementation of the RunnableEntitys and the RTE with respect to efﬁcient communication between the RunnableEntitys.
The communication among RunnableEntitys can very efﬁciently be implemented
by means of “sharing memory”.
Please note that the term “sharing memory” can be interpreted on different levels. It is e.g. in the C language possible to use variables with external linkage (a.k.a. “global variables”, although this term is not ofﬁcially deﬁned by the C language) for the purpose of inter-Runnable communication.

This is technically feasible because it is always guaranteed that the RunnableEntitys within an AtomicSwComponentType are always gathered at a speciﬁc processing unit (in other words: distribution is not an option).

Note that the purpose of communication among the RunnableEntitys is to establish a data ﬂow scheme. The latter is a very popular pattern in the application of controltheory to automotive embedded systems. So if “global variables” are used for establishing internal communication among RunnableEntitys they acquire the semantics of so called state-messages.

Nevertheless, directly sharing memory between RunnableEntitys requires a serious problem to be solved: the guarantee of data consistency among communicating RunnableEntitys. The RunnableEntitys will indeed be mapped to tasks so that one RunnableEntity of an AtomicSwComponentType may be preempted by a different RunnableEntity of the same AtomicSwComponentType.

Please note that a purist approach to achieving data consistency not only applies to single accesses of concurrently accessed variables. Rather, it would not be permitted that the value of a concurrently accessed variable (with state-message semantics) is unintentionally changed during the run-time of a RunnableEntity.

The following paragraphs describe some common strategies that can be used to ensure the required data-consistency. We do not attempt to describe the pros or cons of these approaches.

#@SECTION: 2.3.1.1 Mutual Exclusion with Semaphores

Multi-threaded operating systems provide mutexes (mutual exclusion semaphores) that protect access to an exclusive resource that is used from within several tasks.
The RTE could use these OS-provided mutexes to make sure that the RunnableEntitys sharing a memory-space would never run concurrently. The RTE would make sure the task running the RunnableEntity has taken an appropriate mutex before accessing the memory shared between the RunnableEntitys.

#@SECTION: 2.3.1.2 Interrupt Disabling

Another alternative would be the disabling of interrupts during the run-time of RunnableEntitys or at least for a period in time identical to the interval from the ﬁrst to the last usage of a concurrently accessed variable in a RunnableEntity. This approach could lead to seriously non-deterministic execution timing.

#@SECTION: 2.3.1.3 Priority Ceiling

Priority ceiling allows for a non-blocking protection of shared resources. Provided that the priority scheme is static, the AUTOSAR OS is capable of temporarily raising the priority of a task that attempts to access a shared resource to the highest priority of all tasks that would ever attempt to access the resource.
By this means is technically impossible that a task in temporary possession of a resource is ever preempted by a task that attempts to access the resource as well.

#@SECTION: 2.3.1.4 Implicit Communication by Means of Variable Copies

Another alternative is the usage of copies of concurrently accessed variables with state message semantics. Note that this approach directly corresponds to the semantics of “implicit” sender-receiver communication (see 7.5.1.2).
This means in particular that for a concurrently used variable a copy is created on which a RunnableEntity entity can work without any danger of data inconsistency.
This concept requires additional code to write the value of the concurrently accessed variable to the copy before the RunnableEntity that accesses the variable is executed. The value of the copy shall be written back to the concurrently accessed variable after the RunnableEntity has been terminated.
This concept is sketched in Figure 2.4. Since it would be too expensive and error-prone to manually care about the copy routines it would be a good idea to leave the creation of the additional code to a suitable code generator.

Figure 2.4: Generation of copy routines around RunnableEntitys

The additional copy routines as sketched in Figure 2.4 already protect the particular RunnableEntitys from unintended changes of concurrently accessed variables.It would, however, be possible to further optimize the process by reducing the additional code at the beginning and end of each task (see Figure 2.5).

#@SECTION: 2.3.2 Data Consistency at Runtime

In addition, copy routines will only be inserted where appropriate, e.g. a copy routine
for writing the value of a copy back to the concurrently accessed variable will only be
inserted if the RunnableEntity has write access to the concurrently used variable.
Please note that the copy routines have to temporarily make sure that the copy process
is not interrupted in order to be capable of consistently copying the values from and to
the concurrently accessed variable.
These periods, however, are supposed to be very short compared with the overall
run-time consumption of the RunnableEntity and thus would not have a signiﬁcant
impact on the runtime behavior.

Figure 2.5: Optimized insertion of copy routines

Further optimization criteria can be applied, for example:it would be perfectly safe
to avoid the creation of copies for RunnableEntitys that are scheduled in the task
with the highest priority of all tasks that (via contained RunnableEntitys) access a
certain concurrently accessed variable.

In order to keep the application code free of any dependencies from the code gener
ation, access to concurrently accessed variables will be guarded by macros that are
later resolved by the code generator.

The presence of the guard macros directly supports the reuse on the level of source
code. The reuse on the level of object code is only possible if the scheduling scenario
(in terms of the assignment of RunnableEntitys to priority levels) does not change.

This concept can only be implemented properly with the aid of a code generator if the
variables in question can be identiﬁed. In other words: the description of an Atomic
SwComponentType has to expose all concurrently accessed variables to the outside
world.

#@SECTION: 2.3.3 Modeling Aspects of Data Consistency
#@CLASS: ParameterAccess
#@CLASS: VariableAccess
#@CLASS: VariableDataPrototype
The intrinsic meaning of the terms “explicit communication” and “implicit communication” is explained in section 7.5.1.1. 
It would be fair to say that the distinction between implicit and explicit communication establishes a usage pattern in the application domain, i.e. in the world of the developer of AUTOSAR software-components and their implementation.
There is another facet to this subject, however, namely the question how this pattern is implemented in the meta-model. With respect to the application of the pattern for portbased communication the details can be found in section 7.5.1.2, more speciﬁcally in section 7.5.1.3. The consideration of the internal communication based on so-called “inter-runnable variables” is described in section 7.4.2.
By reading the respective text sections it becomes apparent that the two applications of the pattern are modeled differently. The portbased communication uses the VariableAccess to formalize different roles of accessing communication elements. Some of the roles used for this purpose imply explicit communication (e.g. dataSendPoint) and some represent implicit communication (e.g. dataWriteAccess).
The important thing about using the VariableAccess, however, is that the modeling of communication roles is abstracted from the actual communication elements and represents a uniform (meaning: it can refer to the target directly or by a so-called InstanceRef) modeling approach that is applied for all use cases2.
Admittedly, this is handled in a different way for the internal communication. Here, the additional layer of abstraction is not used (although it would have been technically feasible to do so) with respect to the clear separation of “inter-runnable variables with implicit behavior” and “inter-runnable variables with explicit behavior” in the RTE. The implementation of different communication roles (i.e. implicit vs. explicit) is done by directly aggregating VariableDataPrototype in the roles explicitInterRunnableVariable and implicitInterRunnableVariable.
On the other hand, access to internal communication never requires the usage of an InstanceRef and therefore the abstraction might be considered unnecessary over head that blows up the M1 model.
2 On a related note, even for non-communication related data access the same pattern applies implemented by ParameterAccess

#@SECTION: 2.4 Variant Handling in the Software Component Template
#@CLASS: ParameterDataPrototype
#@CLASS: PortPrototype
#@CLASS: RTEEvent
#@CLASS: RunnableEntity
#@CLASS: SwComponentDocumentation
#@CLASS: SwComponentPrototype
#@CLASS: SwConnector
#@CLASS: VariableDataPrototype
The Software Component Template supports the creation of Variants in a subset of its model elements. The full list of model elements that support variation can be found in the appendix.
[TPS_SWCT_01038] Support for Variant Handling in the in Software Component Template (cid:100) The Variant Handling support in the in Software Component Template is mainly driven by the purpose to describe a variable system on Virtual Functional Bus[3] level by varying
• the existence of SwComponentPrototypes
• the existence of SwConnectors
• the existence of Chapters of SwComponentDocumentation
• the existence of PortPrototypes
(cid:99)(RS_SWCT_00220, RS_SWCT_03100, RS_SWCT_03140, RS_SWCT_03142, RS_SWCT_03154)
[TPS_SWCT_01039] Purpose of variant handling (cid:100) This supports adjusting the number and kind of software-component instances as well as their interconnection in a particular system variant. (cid:99)(RS_SWCT_00220)
[TPS_SWCT_01447] Applicable binding times for model elements in the scope of the Software Component Template (cid:100) The ﬁrst three cases are supporting PostBuild binding. For the existence of PortPrototypes only preCompileTime is supported as latest Binding Time. (cid:99)(RS_SWCT_00220)
[TPS_SWCT_01040] SwConnector exists depending on a PostBuild condition (cid:100) 
A SwConnector which exists depending on a PostBuild condition has an impact 
on the behavior of API function calls that apply on a PortPrototype to which the SwConnector is attached. 
If the SwConnector does not exist the behavior of the RTE API functions need to take this into account. 
This means that the RTE implementation of this PortPrototype resembles the behavior of an unconnected PortPrototype. 
(cid:99)(RS_SWCT_00220, RS_SWCT_03100, RS_SWCT_03143)
Please ﬁnd more details in the speciﬁcation of the RTE [2].
[TPS_SWCT_01041] API functions of not existing SwConnector are still part of the software-component’s implementation (cid:100) If SwConnectors do not exist the corresponding API functions are still part of the software-component’s implementation. It is not possible to remove the API functions in a PostBuild step. Therefore the latest reasonable Binding Time for the conditional existence of a PortPrototype is preCompileTime. (cid:99)(RS_SWCT_00220, RS_SWCT_03100)
[TPS_SWCT_01085] Variation on the behavior level (cid:100) In addition to variation of the VFB-related model elements, the description of variant software-component implementations is supported. Please note that this requires a broad support of variability in the Internal Behavior.
The identiﬁed main use case are
• the existence of RunnableEntitys
• the existence of RTEEvents
• the existence of VariableDataPrototypes in the roles implicitInterRunnableVariable and explicitInterRunnableVariable
• the existence of ParameterDataPrototypes in the roles perInstanceParameter, sharedParameter, and constantMemory
(cid:99)(RS_SWCT_03149, RS_SWCT_03150, RS_SWCT_03151, RS_SWCT_03153)
For the same reason that applies on the existence of PortPrototype the latest Binding Time of these kinds of variability is preCompileTime.
In the meta-model, all locations that may exhibit variability are marked with the stereotype (cid:28)atpVariation(cid:29). This allows the deﬁnition of possible variation points. Tagged Values are used to specify additional information, for example the latest binding time.
[TPS_SWCT_01042] Four types of locations in the meta-model which may exhibit variability (cid:100) There are four types of locations in the meta-model which may exhibit variability:
• Aggregations
• Associations
• Attribute Values
• Classes providing property sets
(cid:99)(RS_SWCT_00220, RS_SWCT_03100)
The reasons for the attachment of the stereotype (cid:28)atpVariation(cid:29) to certain model elements and the consequences for other model elements are explained in class tables in the following chapters. More details about the AUTOSAR Variant Handling Concept can be found in the AUTOSAR Generic Structure Template [12].

#@SECTION: 2.5 Communication Speciﬁcation of Composition Component Types
#@CLASS: CompositionSwComponentType
#@CLASS: PortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: ConstantSpecificationMappingSet
#@CLASS: DataTypeMappingSet
#@CLASS: DelegationSwConnector
#@CLASS: ParameterSwComponentType
#@CLASS: PortInterface
#@CLASS: PPortComSpec
#@CLASS: RPortComSpec
#@CLASS: SwComponentPrototype

[TPS_SWCT_01088] ComSpecs defined by CompositionSwComponentTypes (cid:100) It shall be possible to attach ComSpecs to PortPrototypes owned by CompositionSwComponentTypes. (cid:99)(RS_SWCT_03220)

#@SECTION: 2.5.1 Rationale

ComSpecs attached to a PortPrototype owned by an AtomicSwComponentType have a direct impact on the generation of the RTE. The RTE Generator, on the other hand, does not consider the existence of CompositionSwComponentTypes.

Nevertheless, there are some cases where the definition of a ComSpec attached to a PortPrototype owned by a CompositionSwComponentType does make sense. That is, in case an OEM wants to submit the definition of a CompositionSwComponentType to a supplier for adding more details and implementing the behavior the OEM might want to point out that from the OEM’s point of view sender initValues and receiver initValues apply for the elements of PortInterfaces used to type the delegation PortPrototypes.

The idea is that the supplier takes over the initValues attached to the delegation PortPrototypes and copies them to the PortPrototypes owned by SwComponentPrototypes of the CompositionSwComponentType.

[TPS_SWCT_01568] Consideration of RPortComSpec or PPortComSpec depending on the ownership (cid:100) The RTE Generator shall take the attributes of the RPortComSpec or PPortComSpec of the PortPrototypes owned by AtomicSwComponentTypes or ParameterSwComponentType and ignore the attributes of the RPortComSpec or PPortComSpec attached to PortPrototypes owed by CompositionSwComponentType. (cid:99)(RS_SWCT_03220)

Therefore, the initValues of the delegation PortPrototype would be taken as mere templates for the detailing of PortPrototypes connected to the delegation PortPrototypes. It is not required that the initValues of delegated PortPrototype and a PortPrototype connected by means of a DelegationSwConnector match. Although this would certainly make sense in many cases it is eventually still left to the supplier to decide on the specific initValues applicable inside the CompositionSwComponentType.

On the other hand, a requirement that the initValues defined on the surface of CompositionSwComponentType and the inside of the CompositionSwComponentType shall be consistent in any case might effectively prevent the reuse of existing AtomicSwComponentTypes.

Please note that the ability to define a ComSpec in the context of a CompositionSwComponentType implies that it shall be possible to define mappings of ApplicationDataTypes used in a PortInterface to their corresponding ImplementationDataTypes. For this purpose the CompositionSwComponentType owns a DataTypeMappingSet in the role dataTypeMapping and a ConstantSpecificationMappingSet in the role constantValueMapping.

Figure 2.6: Specification of data type mapping for CompositionSwComponentType

#@SECTION: 2.6 PRPortPrototype
#@CLASS: NvBlockSwComponentType
#@CLASS: PortPrototype
#@CLASS: SwComponentType
#@CLASS: ApplicationSwComponentType
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RPortPrototype
#@CLASS: ApplicationSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: RunnableEntity

In some cases SwComponentTypes need to read and write the same piece of data. One of the most prominent examples for this use case is the NvBlockSwComponentType that factually ready and writes blocks of NvRAM. Without the ability to combine read and write semantics in a kind of PortPrototype that supports both read and write semantics work-arounds have to be implemented that come with a certain footprint on memory and processing time.

#@SECTION: 2.6.1 Use Case 1

Without the ability to define a combined read and write semantics the definition of an RPortPrototype and a PPortPrototype is required for reading and writing the applicable data.


<-------------- multimodal context 
This diagram illustrates an Application SW-Component interacting with an NvBlock SW-Component to read and write persistent data (“MyNvData”) through mirrored required/provided port prototypes, with the NvBlock mapping both ports to an internal RAM storage element.

• Component hierarchy  
  – Two AtomicSwComponentTypes: “Application SW Component” and “NvBlock SW Component”  
  – No nested compositions; they are standalone instances linked by assembly connectors  

• Ports & interfaces  
  – Each SW-Component defines an AbstractRequiredPortPrototype (R_MyNvData) and an AbstractProvidedPortPrototype (P_MyNvData)  
  – Both ports use a shared DataInterface (e.g. ApplicationCompositeDataType)  
  – AssemblySwConnectors cross-link P_MyNvData↔R_MyNvData in both directions  

• Data flow  
  – Application invokes its P_MyNvData to send new NvData into the NvBlock  
  – Application reads back stored data via its R_MyNvData, served by the NvBlock’s P_MyNvData  
  – Bidirectional synchronous data exchange routed through the block’s ramBlock  

• Key AUTOSAR concepts  
  – Port prototypes (PRPortPrototype) and ClientServerInterface  
  – ArVariableInImplementationDataInstanceRef mapping of ports to an internal ApplicationDataPrototype (“ramBlock”)  
  – Dashed “mappings” represent DataPrototypeMapping/InstantiationDataDefProps  

• Scenario  
  – Demonstrates how a generic non-volatile storage SWC exposes internal RAM via provided ports for application use, validating the need for PRPortPrototypes in AUTOSAR. ---------------------->
Figure 2.7: Use Case 1 for the existence of PRPortPrototype

Technically, this read and write access is related to the same data item in an NVRAM Block. This requires a consistent connection of the PortPrototypes between an NvBlockSwComponentType and ApplicationSwComponentType as well as a consistent mapping of the corresponding RPortPrototype and a PPortPrototype of the NvBlockSwComponentType and the related element of the ramBlock.

#@SECTION: 2.6.2 Use Case 2

It may happen that a SwComponentType need to consume the same data that it produces. If the only way to achieve this was the connection of a PPortPrototype to an RPortPrototype of the same SwComponentType then the creator of the SwComponentType cannot enforce this connection as it is created on a higher level of abstraction in the context of a CompositionSwComponentType.

In other words, it is impossible to fully specify the semantics of the otherwise self contained SwComponentType.


<-------------- multimodal context 
The diagram illustrates a simple AUTOSAR composition in which Application SW-Component A produces a data element “MyData”, consumes its own output for internal feedback, and forwards it to Application SW-Component B. RunA1 writes to a provided port and reads back the same data via a required port, while RunB1 reads the forwarded value. This use case motivates a combined PRPortPrototype to avoid redundant port definitions when chaining reads and writes across components.

• Component hierarchy  
  – Two AtomicSwComponentType instances: Application SW Component A (with Runnable RunA1) and Application SW Component B (with Runnable RunB1).  

• Ports & interfaces  
  – A: AbstractProvidedPortPrototype P_MyData and AbstractRequiredPortPrototype R_MyData, both typed by a common DataInterface “MyData.”  
  – B: AbstractRequiredPortPrototype MyData (same DataInterface).  
  – One AssemblySwConnector links P_MyData to both R_MyData and B’s MyData port.  

• Data flow  
  – RunA1 writes “MyData” through P_MyData; the data is routed back into A via R_MyData (loopback) and out to B’s MyData port.  
  – RunB1 reads “MyData” via its required port.  

• Key AUTOSAR concepts  
  – Separate RPort/PPort prototypes, DataInterface, AssemblySwConnector, runnable-to-port data access (read/write).  
  – Highlights need for a PRPortPrototype to merge P/R roles.  

• Scenario  
  – Demonstrates self-feedback plus inter-component data provision, driving the justification for a unified PRPortPrototype. ---------------------->
Figure 2.8: Use Case 2 for the existence of PRPortPrototype

This means that only in the in best case one buffer for the data is needed. But depending on the mapping RunnableEntitys to OS tasks additional buffers may need to be allocated by the RTE to fully implement the implicit communication pattern.

As an alternative, the ApplicationSwComponentType could utilize inter-runnable variables but unfortunately this inhibits any optimization in the RTE and will consume additional RAM. In contrast to the previous approach at least two buffers are needed.

#@SECTION: 2.6.3 Use Case 3

In this scenario, several ApplicationSwComponentTypes are iterating over the same large set of data. This means each ApplicationSwComponentType implements one out of many steps of a complex data processing algorithm applied to the same piece of data.


<-------------- multimodal context 
This diagram illustrates a simple three‐component data pipeline using PRPortPrototypes: Component A produces data, B reads and transforms it, and C reads and forwards it. Each component hosts a single runnable that accesses a provided port for output and a required port for input, showing how PRPortPrototypes enable chaining of data interfaces via assembly connectors.

• Component hierarchy  
  – Three AtomicSwComponentTypes: Application SW Component A, B, C  
  – Each contains one RunnableEntity (RunA1 in A and C, RunB1 in B)

• Ports & interfaces  
  – Each SWC has one ProvidedPortPrototype (PPort) and one RequiredPortPrototype (RPort)  
  – Ports expose a DataInterface for read/write access  
  – AssemblySwConnectors link A→B and B→C ports

• Data flow  
  – RunA1 writes to A’s PPort → B’s RPort  
  – RunB1 reads from B’s RPort, writes to B’s PPort → C’s RPort  
  – RunA1 in C reads from C’s RPort and writes to C’s PPort

• Key AUTOSAR concepts  
  – AbstractProvidedPortPrototype / AbstractRequiredPortPrototype  
  – ClientServer (data) interface, PRPortPrototype usage  
  – Runnable–Port data access relationships

• Scenario  
  – Demonstrates existence and chaining of PRPortPrototypes for inter-component data flow in a producer–consumer chain. ---------------------->
Figure 2.9: Use Case 3 for the existence of PRPortPrototype

For example, this scenario may apply for video signal processing in camera applications. Typically, such applications will not be distributed over several ECUs. It is clear that in this case the allocation of several buffers in the RTE is required to implement the individual connections between the ApplicationSwComponentTypes. In most cases, the processing has to be executed at a certain point in time in a dedicated order.

#@SECTION: 2.6.4 Solution

The solution to the above-mentioned use cases is the ability to define a PortPrototype that can read and write the same piece of data. This solves both the described problem of resource consumption as well as the problem of having to define multiple PortPrototypes as outlets for same piece of data item.

The technical details of the definition of PRPortPrototype are explained in chapters 3.1 and 4.1.

#@SECTION: 2.7 Pretended Networking

#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeSwitchInterface
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: SwComponentType
#@CLASS: AutosarDataType
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: VariableDataPrototype
#@CLASS: PortInterface
[TPS_SWCT_01510] The role of pretended networking (cid:100) Pretended networking is a feature to reduce energy consumption of an ECU by switching the ECU in a mode called Pretended Networking. In this mode the communication on communication networks is reduced and the ECU can go into power saving modes.
When communication via communication networks is required the mode Pretended Networking shall be left by request of a mode change to Normal Mode. (cid:99)()

[TPS_SWCT_01511] Configuration option is encoded into ModeDeclaration (cid:100) The identification of different configuration options for Pretended Networking shall be encoded into the definition of dedicated ModeDeclarations inside a ModeDeclarationGroup. (cid:99)(RS_SWCT_03110)

For example, assume that an implementation of pretended networking supports three configuration options:
• PRETENDED_NW_MODE_OFF
• PRETENDED_NW_MODE_ONE
• PRETENDED_NW_MODE_TWO

In this example case, a ModeDeclarationGroup consisting of three ModeDeclarations shall be defined where each ModeDeclaration shall represent one of the above-mentioned configuration options. The shortNames of the ModeDeclaration shall be taken from the above-mentioned list.

[TPS_SWCT_01512] Request change of Pretended Networking mode (cid:100) A SwComponentType that needs to be able to request a change in the operating mode of Pretended Networking shall provide a PPortPrototype typed by a SenderReceiverInterface (see [TPS_SWCT_01086]) for requesting a change (towards the BswM [15]) of the Pretended Networking mode.

It is out of the scope of this document to define the particular properties of the applicable SenderReceiverInterface. The details of this specific SenderReceiverInterface can be found in the specification of the BswM [15]. (cid:99)(RS_SWCT_03110)

More details about how a mode change is requested can be found in section 9.

[TPS_SWCT_01513] React on the change of Pretended Networking mode (cid:100) A SwComponentType that needs to be able to react on a change in the operating mode of Pretended Networking shall provide an RPortPrototype typed by a ModeSwitchInterface (see [TPS_SWCT_01087]) for reacting on a change (initiated by the BswM [15]) of the Pretended Networking mode.

It is out of the scope of this document to define the particular properties of the applicable ModeSwitchInterface. The details of this specific ModeSwitchInterface can be found in the specification of the BswM [15]. (cid:99)(RS_SWCT_03110)

#@SECTION: 2.8 Variable-size Array Data Types
#@CLASS: ApplicationArrayDataType
#@CLASS: ImplementationDataType
#@CLASS: ApplicationArrayElement
#@CLASS: ImplementationDataTypeElement
#@CLASS: ApplicationDataType
#@CLASS: DataTypeMap
#@CLASS: SwDataDefProps

#@SECTION: 2.8.1 Overview and Use cases

AUTOSAR supports the definition of array data types where the size of the actual payload varies at run-time. As far as the configuration is concerned, it is possible to specify a maximum number of array elements that shall not be exceeded at run-time.
In order to properly understand the approach, it is necessary to understand that the support for Variable-Size Array Data Types has been introduced in two waves that each had a different motivation.

#@SECTION: 2.8.1.1 “Old-world” dynamic-size Arrays

In the ﬁrst wave, the support for Variable-Size Array Data Types was limited to data types that basically boil down to an array where the base type is an unsigned integer data type with a length of exactly one byte.

The main use cases for this scenario are derived from diagnostics requirements as well as support for the J1939 communication protocol.

In both cases the actual length of a Variable-Size Array Data Type could be determined from the context, i.e. either by the diagnostic basic-software module or by the implementation of the J1939 TP.

For the lack of a better terminology, this speciﬁcation distinguishes between “old-world” dynamic-size arrays and “new-world” Variable-Size Array Data Types. It will be necessary to clearly deﬁne the characteristics that allow for an disambiguation between the “old-world” dynamic-size arrays and “new-world” Variable-Size Array Data Types.

[TPS_SWCT_01641] Deﬁnition of an “old-world” dynamic-size array data type by means of an ApplicationArrayDataType (cid:100) An ApplicationArrayDataType that doesn’t deﬁne attribute dynamicArraySizeProfile and that aggregates an ApplicationArrayElement where attribute arraySizeSemantics exists and is set to the value variableSize shall be considered an “old-world” dynamic-size array data type. (cid:99)(RS_SWCT_03181)

Please note that [TPS_SWCT_01641] can’t go any deeper into the speciﬁcs of the given data type because it is intentionally focused on ApplicationDataTypes. There are use cases where the distinction between “old-world” dynamic-size arrays and “new-world” Variable-Size Array Data Types must be done in the absence of a corresponding ImplementationDataType.

In general, the disambiguation becomes multi-faceted (but not necessarily easier) if the deﬁnition of a corresponding ImplementationDataType is available (see [TPS_SWCT_01642]).

[TPS_SWCT_01642] Deﬁnition of an “old-world” dynamic-size array data type by means of an ImplementationDataType (cid:100) An ImplementationDataType that (after all type references are resolved) fulﬁlls all of the following conditions shall be considered an “old-world” dynamic-size array data type:

• The value of attribute category is set to ARRAY
• The ImplementationDataType doesn’t deﬁne the attribute dynamicArraySizeProfile
• The ImplementationDataType aggregates a subElement where
  – attribute arraySizeSemantics exists and is set to the value variableSize
  – attribute arraySizeHandling does not exist
• The ImplementationDataType.swDataDefProps.baseType exists and the attribute
  – baseTypeEncoding exists and is set to the value NONE
  – baseTypeSize exists and is set to the value 8
(cid:99)(RS_SWCT_03181)

By and large, the deﬁning characteristics for “old-world” dynamic-size arrays is the absence of a deﬁnition of the attribute ApplicationArrayDataType.dynamicArraySizeProfile resp. ImplementationDataType.dynamicArraySizeProfile.

By regulation of [constr_1387], “old-world” dynamic-size arrays are not supported for transmission by means of a data transformer. The only supported kind of Variable Size Array Data Type that can be transmitted using a data transformer is the “new-world” variable-size arrays.

#@SECTION: 2.8.1.2 “New-world” variable-size Arrays

In contrast to this, the second wave of support for Variable-Size Array Data Types was motivated by the application software layer itself.

Here, the situation is entirely different because the actual size cannot be determined by any context software module. The application itself is responsible for maintaining the proper length of a Variable-Size Array Data Type at run-time.

As a consequence, the speciﬁcation of the actual array size at run-time needs to be reﬂected by the structure of the data types used for hosting the Variable-Size Array Data Type.

[TPS_SWCT_01644] Deﬁnition of a “new-world” variable-size array data type by means of an ApplicationArrayDataType (cid:100) An ApplicationArrayDataType that fulﬁlls all of the following conditions shall be considered an “new-world” dynamic size array data type.
• The ApplicationArrayDataType deﬁnes attribute ApplicationArrayDataType.dynamicArraySizeProfile.
• ApplicationArrayDataType aggregates an ApplicationArrayElement that deﬁnes attribute ApplicationArrayElement.arraySizeHandling.
(cid:99)(RS_SWCT_03181)

[TPS_SWCT_01645] Deﬁnition of a “new-world” variable-size array data type by means of an ImplementationDataType (cid:100) An ImplementationDataType that fulﬁlls all of the following conditions shall be considered an “new-world” dynamic-size array data type.
• The ImplementationDataType deﬁnes attribute ImplementationDataType.dynamicArraySizeProfile.
• ImplementationDataType aggregates an ImplementationDataTypeElement that deﬁnes attribute ImplementationDataTypeElement.arraySizeHandling.
(cid:99)(RS_SWCT_03181)

In contrast to the ﬁrst use case described above, the application-motivated Variable Size Array Data Type cannot be limited in terms of the base type of the array data type, i.e. limiting the underlying data type to an unsigned integer data type with a length of exactly one byte is not an option.

On top of that, several possible structures of Variable-Size Array Data Types have been required. This aspect is depicted in Figure 2.10.

[TPS_SWCT_01636] Deﬁnition of proﬁles for the deﬁnition of Variable-Size Array Data Types (cid:100) The possible variants for Variable-Size Array Data Types are:
Linear The data type of the elements of the Variable-Size Array Data Type itself does not consist of a Variable-Size Array Data Type. This case corresponds to the tag (a) in Figure 2.10. This case corresponds to the possible value VSA_LINEAR of attribute dynamicArraySizeProfile.
Square The data type of the elements of the Variable-Size Array Data Type itself consists of Variable-Size Array Data Types where the maximum number of elements in all “second order” arrays is identical to the maximum number of elements in the “ﬁrst order” array. This case corresponds to the tag (b) in Figure 2.10. This case corresponds to the possible value VSA_SQUARE of attribute dynamicArraySizeProfile.
Rectangular The data type of the elements of the Variable-Size Array Data Type itself consists of Variable-Size Array Data Types data types where the maximum number of elements in “second order” arrays is identical but this value is typically not identical3 to the maximum number of elements in the “ﬁrst order” array. This case corresponds to the tag (c) in Figure 2.10. This case corresponds to the possible value VSA_RECTANGULAR of attribute dynamicArraySizeProfile.
Fully Flexible The data type of the elements of the Variable-Size Array Data Type itself consists of Variable-Size Array Data Types where the maximum number of elements in “second order” arrays is not necessarily identical with each other and (obviously) not necessarily identical to the maximum number of elements in the “ﬁrst order” array. This case corresponds to the tag (d) in Figure 2.10. This case corresponds to the possible value VSA_FULLY_FLEXIBLE of attribute dynamicArraySizeProfile.
(cid:99)(RS_SWCT_03181)


<-------------- multimodal context 
This diagram illustrates the structural variants of AUTOSAR ApplicationArrayDataType definitions when the array length is not fixed. It shows how a single variable-size array, nested arrays, segmented arrays, and arrays with heterogeneous element sizes can be modeled purely at the data-type level to support differing runtime sizing requirements.

• Component hierarchy  
  – One top-level ApplicationArrayDataType in each variant  
  – (b) and (c) show nested ApplicationArrayElement groups (i.e. arrays of arrays)  
  – (d) demonstrates heterogeneous element sizing within one ApplicationArrayDataType  

• “Ports & interfaces”  
  – No RPort/PPort here; these are pure DataPrototype definitions  
  – Each ApplicationArrayElement acts like an inner data prototype group  

• Data flow  
  – Not IPC but static data composition  
  – Consumers read from the outer array; inner elements are materialized at runtime  

• Key AUTOSAR concepts  
  – ApplicationArrayDataType with variableSizeAllowed = true  
  – ApplicationArrayElement and ApplicationCompositeDataTypeSubElementRef  
  – Use of heterogeneous vs. homogeneous sub-element modeling  

• Scenario / design intent  
  – Provide flexible array structures for calibration tables, sensor buffers or dynamic payloads where element count or size must vary at configuration time rather than code-generation time. ---------------------->
Figure 2.10: Structural variety of array data types with variable size

Please note that the leaf elements in a Variable-Size Array Data Type doesn’t have to be primitive data types. As mentioned before, it is possible to deﬁne multiple dimension Variable-Size Array Data Types. The “terminal” elements can be recognized as such in that they don’t establish further Variable-Size Array Data Types.

#@SECTION: 2.8.2 Modeling Aspects regarding Application Data Types

In the context of the AUTOSAR layered data type concept, the level of ApplicationDataTypes is not concerned about the structure of how the Variable-Size Array Data Types. If it was, the case boils down to the rectangular scenario tagged (b).

In other words, aspects of the implementation of this kind of data type is intentionally abstracted as much as possible in order to support the idea behind the definition of ApplicationDataTypes as a concept that is independent from an implementation to the applicable degree.

Consequently, the support for Variable-Size Array Data Types on the level of ApplicationDataTypes requires the addition of a couple of additional attributes. Details can be found in chapter 5.2.4.2.

If a Variable-Size Array Data Type is modeled on the level of ApplicationDataType it is necessary to also provide a companion ImplementationDataType as well as a DataTypeMap that refers to both the ApplicationDataType and the ImplementationDataType.

The contrary is not applicable, i.e. it is possible to define a Variable-Size Array Data Type with only an ImplementationDataType, see [TPS_SWCT_01622].

#@SECTION: 2.8.3 Modeling Aspects regarding Implementation Data Types

On the other hand, the data type used for the actual hosting of the Variable Size Array Data Type corresponds directly to the level of the Implementation DataType. Here, it is possible to define how an ImplementationDataType can be used to define a Variable-Size Array Data Type. The definition of ImplementationDataType in the AUTOSAR meta-model comes with a certain level of generic nature the support for Variable-Size Array Data Types on this level comes as a mixture of dedicated attributes in the meta-model and a set of recipes how to support different use cases of Variable-Size Array Data Types. This means that the definition of ImplementationDataTypes for the purpose of creating Variable-Size Array Data Types only has a chance to take off if the structure of these data types is replicated in different implementations of AUTOSAR software. Therefore, AUTOSAR defines a common way of how ImplementationDataTypes for the purpose of creating Variable-Size Array Data Types shall be defined such that the ImplementationDataType shall be of category STRUCTURE with the following sub-elements:
1. A numerical value that determines the actual size. This element shall be called the Size Indicator throughout this document.
2. An array of the base-type of the Variable-Size Array Data Type that implements the payload of the Variable-Size Array Data Type. The dimension of the array shall be defined such that the intended maximum number of elements fits in.

A Size Indicator of a Variable-Size Array Data Type holds the number of valid elements of the array. This information is necessary for the RTE to handle the array efficiently.

On the sender-side this indicator is actively updated by the software-component which is the only instance that knows how many elements of the array are valid. So the number of valid elements and the Size Indicator have to be kept consistent by the application. When the software-component sends the data over the RTE the RTE hands the data over to the transformer.

The transformer may evaluate the Size Indicator (depends on the transformer) and only work on the valid array elements. The output of the transformer can vary in length and only contain necessary data. Therefore it can be more resource saving.

On the receiver side, the last transformer in the execution order restores the data elements of the array and the value of the Size Indicator. This output is handed over by the RTE to the software-component. The application now is aware of the number of valid elements in the array.

The details of how ImplementationDataTypes need to be modeled for the implementation of Variable-Size Array Data Types can be found in chapter 5.2.5 and a couple of examples is available in the appendix E.1.
