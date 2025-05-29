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
#@CLASS: AssemblySwConnectors
#@CLASS: DelegationSwConnectors
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

[TPS_SWCT_01420] SwComponentType requiring access to shared calibration
parameters needs RPortPrototype typed by a ParameterInterface (cid:100) Every
SwComponentType requiring access to shared calibration parameters will have an
RPortPrototype typed by a ParameterInterface. The deﬁnition of this shared
calibration access in the context of a CompositionSwComponentType will be deﬁned by creating a SwConnector between the relevant SwComponentPrototypes. (cid:99)()

Table 2.2: ParameterInterface

[TPS_SWCT_01421] ParameterInterface is not restricted to parameters which
can actually can be calibrated (cid:100) Note that a ParameterInterface is not restricted to parameters which can actually can be calibrated. It can be used whenever there shall be no write access to the data during normal operation of the software, i.e. only constant data are visible over the interface. (cid:99)()

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

#@SECTION: 3 Overview: Software Components, Ports, and Interfaces

#@SECTION: 3.1 Introduction

The detailed introduction of all aspects of the Software Component Template in
one move is considered too complex. This chapter therefore provides an overview
of the main conceptual aspects of software components, ports and interfaces. The
overview will then be broken down into further details in chapter 4.

One of the goals of the AUTOSAR concept is the support of re-usability on the level of
application software. In other words: it should be possible to re-use existing artifacts to
create further model elements instead of being forced to create every single modeling
detail from scratch. One of the consequences of this approach is the application of the
so-called type-prototype pattern [12].

Among other things, this concept allows for creating hierarchical structures of software
components with arbitrary complexity. However, the creation of hierarchical structures
itself does not have an impact on the run-time behavior of the overall system. The
actual behavior is completely deﬁned within the individual software-components.

This conclusion is backed by the understanding that software-components are devel
oped against the so-called Virtual Functional Bus (VFB), an abstract communication
channel without direct dependency on ECUs and communication buses. The VFB does
not provide any means for expressing a hierarchy of software-components.

Of course, the usage of the VFB has further consequences on the design of software
components which shall not directly call the operating system or the communication
hardware. As a result, software-components can be deployed to actual ECUs at a
rather late stage in the development process.

In order to make the description more precise, the following text preferably uses accu
rate meta-model terms instead of the rather vague terminology of “composition” and
“software-component”.

#@SECTION: 3.2 Software Component
#@SECTION: 3.2.1 Overview
#@CLASS: SwComponentType 

Application software within AUTOSAR is organized in self-contained units called Atom
icSwComponentTypes. Such AtomicSwComponentTypes encapsulate the imple
mentation of their functionality and behavior and merely expose well-deﬁned connec
tion points, called PortPrototypes, to the outside world.


<-------------- multimodal context 
This diagram illustrates how an atomic AUTOSAR Software Component defines and exposes its communication façades via ports and connectors. It shows both client-server and sender-receiver interactions, including a dedicated service port and attribute port, enabling synchronous operations, asynchronous signal exchange, and configuration data flow within an ECU software architecture.

• Component hierarchy  
  – A single AtomicSwComponentType (“AUTOSAR-SW-Component”), no nested compositions  

• Ports & interfaces  
  – Provided PortPrototype (PPort), ClientServerInterface  
  – Required PortPrototype (RPort), ClientServerInterface  
  – Provided PortPrototype, SenderReceiverInterface  
  – Required PortPrototype, SenderReceiverInterface  
  – Required service PortPrototype, SenderReceiverInterface  
  – Provided PortPrototype (attribute port), SenderReceiverInterface  

• Data flow  
  – ConnectorPrototypes link provided/required ClientServer ports (RPC request/response)  
  – Connectors link SenderReceiver ports for publish/subscription of data and attributes  
  – Service port used for on-demand data exchange  

• Key AUTOSAR concepts  
  – AbstractProvidedPortPrototype, AbstractRequiredPortPrototype  
  – PortInterface (ClientServerInterface, SenderReceiverInterface)  
  – ConnectorPrototype, service PortPrototype, attributes on ports  

• Scenario  
  – Demonstrates a component offering and consuming services (RPC), publishing signals and attributes, and subscribing to asynchronous events in an ECU network. ---------------------->
Figure 3.1: Graphical representation of software-components in AUTOSAR

The graphical appearance of AUTOSAR software-components according to [3] is depicted in Figure 3.1.
Table 3.1: SwComponentType

#@SECTION: 3.2.2 PortPrototype

#@CLASS: PortPrototype 
Table 3.2: PortPrototype
Figure 3.2: Overview of PortPrototype

#@CLASS: AbstractRequiredPortPrototype 
Table 3.3: AbstractRequiredPortPrototype

#@CLASS: AbstractProvidedPortPrototype 
Table 3.4: AbstractProvidedPortPrototype

#@CLASS: RPortPrototype
Table 3.5: RPortPrototype

#@CLASS: PPortPrototype
Table 3.6: PPortPrototype

#@CLASS: PRPortPrototype
Table 3.7: PRPortPrototype

Figure 3.3: Components and Ports
#@CLASS: PortGroup

Please note that PortPrototypes of a SwComponentType are supposed to be used
for attaching SwConnectors that establish an actual connection between SwCompo
nentPrototypes (see chapter 3.3).

[TPS_SWCT_01002] SwComponentTypes may only interact by means of their
PortPrototypes (cid:100) AtomicSwComponentTypes (and also the more general
SwComponentTypes may only interact by means of their PortPrototypes). Hidden
communication dependencies that are not expressed by means of PortPrototypes are strictly forbidden.
(cid:99)(RS_SWCT_00020, RS_SWCT_00030, RS_SWCT_00150,RS_SWCT_00160, RS_SWCT_00200, RS_SWCT_00210, RS_SWCT_02010,RS_SWCT_02030)

Therefore, software-components are in theory exchangeable as long as they implement
the same functionality and provide the same public communication interface to the
remaining system.

[TPS_SWCT_01111] PortPrototypes need an additional model artifact, the
PortInterface (cid:100) Please note that PortPrototypes actually need an additional
model artifact, the PortInterface, for fully describing the details of the PortPro
totype. The concept of the PortInterface as another means for establishing a
high degree of re-usability is described in chapter 3.4. (cid:99)(RS_SWCT_00010)

[TPS_SWCT_01112] Semantics of PortPrototypes (cid:100) As depicted in Figure 3.2,
PortPrototypes can have the following semantics:
• A require-port (in technical terms: RPortPrototype) requires certain services or data.
• A provide-port (or PPortPrototype) on the other hand provides services or data.
• A provide-require-port (or PRPortPrototype) combines the ability to provide and require services or data in one entity. (cid:99)(RS_SWCT_03250)

[TPS_SWCT_01573] A PRPortPrototype is never considered unconnected
(cid:100) A PRPortPrototype is never considered unconnected, even if
there are no SwConnectors actually referring to it.
(cid:99)(RS_SWCT_00010, RS_SWCT_03250,RS_SWCT_03130)

Please note that [TPS_SWCT_01573] represents the immediate consequence of the
semantics deﬁned in [TPS_SWCT_01112].

[TPS_SWCT_01113] Connecting two PortPrototypes (cid:100) Two SwComponentPrototypes are eventually connected by hooking up a PPortPrototype or PRPortPrototype of one SwComponentPrototype to a compatible RPortPrototype or PRPortPrototype of the other SwComponentPrototypes. Please ﬁnd more information concerning the deﬁnition of “compatibility” in section 6. (cid:99)(RS_SWCT_03130,RS_SWCT_03250)


[TPS_SWCT_01096] PortGroup (cid:100) PortPrototypes can be logically grouped into
PortGroups. This mechanism is used for implementing mode management features
and further explained in chapter 4.6. (cid:99)(RS_SWCT_03201)

#@SECTION: 3.2.3 AtomicSwComponentType

#@CLASS: InternalBehavior
#@CLASS: AtomicSwComponentType 
Table 3.8: AtomicSwComponentType
Figure 3.4: Overview of Component Types
#@CLASS: ApplicationSwComponentType
Table 3.9: ApplicationSwComponentType

[TPS_SWCT_01108] Added value of an AtomicSwComponentType (cid:100) As mentioned
before, the term AtomicSwComponentType is a speciﬁc form of the general concept
of the SwComponentType. The added value of an AtomicSwComponentType is that
it can aggregate an InternalBehavior (see chapter 7). (cid:99)(RS_SWCT_03040)

[TPS_SWCT_01109] Adding the SwcInternalBehavior in a later process step
(cid:100) The aggregation of SwcInternalBehavior is stereotyped (cid:28)atpSplitable(cid:29) to allow for adding the SwcInternalBehavior in a later process step. In other words, it
is possible to completely develop the VFB view of a software-component and later add
more details like InternalBehavior. (cid:99)()

There are several specialized SwComponentTypes to describe speciﬁc software
components used in the different parts of the AUTOSAR Layered Architecture [6]. Fur
ther details are mentioned in chapter 10 and 11.

The ApplicationSwComponentType is a specialization of AtomicSwComponent
Type for representing hardware-independent application software. The Parameter
SwComponentType is a specialization of SwComponentType that can - in contrast to
AtomicSwComponentType - not aggregate SwcInternalBehavior.

The purpose of the NvBlockSwComponentType is described in detail in section 11.5.2. The ServiceSwComponentType is described in section 11.3. Further on,the EcuAbstractionSwComponentType and the ComplexDeviceDriverSwComponentType are discussed in detail in section 10.

A description of the ServiceProxySwComponentType can be found in section 11.4
while the SensorActuatorSwComponentType is described in section 10.4.



#@SECTION: 3.2.4 ParameterSwComponentType
#@CLASS: ParameterSwComponentType
#@CLASS: SwcInternalBehavior
Figure 3.5: Details of ParameterSwComponentType

[constr_1092] ParameterSwComponentType (cid:100) A ParameterSwComponentType
shall never aggregate a SwcInternalBehavior and also owns exclusively PPort
Prototypes of type ParameterInterface. (cid:99)()

However, a ParameterSwComponentType shall have the ability to aggregate In
stantiationDataDefProps. By this means it is possible to deﬁne role-speciﬁcdata properties of elements of composite data types used for the deﬁnition of calibration parameters in the scope of a ParameterSwComponentType.

For more information about this aspect please refer to section 7.5.4.

#@SECTION: 3.2.5 Symbolic Name of a Software-Component
#@CLASS: SymbolProps
Table 3.10: SymbolProps
Figure 3.6: Overview of AtomicSwComponentType

Please note that an AtomicSwComponentType manifests itself in the source code of
an RTE into which an instance of the AtomicSwComponentType is deployed. This
implies potential naming conﬂicts if instances of AtomicSwComponentType that have
identical shortNames are deployed into a speciﬁc RTE.

[TPS_SWCT_01110] Symbolic name of a software-component (cid:100) To mitigate this
potential hazard it is possible to provide the AtomicSwComponentType along with
an accompanying symbolic name that can be used for resolving the name clash. The
symbolic name is provided by means of the attribute symbol of the meta-class Sym
bolProps owned by AtomicSwComponentType in the role symbolProps (for more
information, please refer to Figure 3.6). (cid:99)()

For more detailed information about how SymbolProps can be used to mitigate name
clashes occurring during the integration of software-components on an AUTOSAR
ECU, please refer to [4].

[TPS_SWCT_01000] Usage of attribute symbol of the symbolProps (cid:100) In particular,
the RTE generator shall take over the value of the attribute symbol of the symbolProps owned by a given AtomicSwComponentType.If and only if symbolProps is not deﬁned the RTE generator shall take the shortName of the AtomicSwComponentType. For the generation of symbols for RunnableEntitys [TPS_SWCT_01001] shall be observed. (cid:99)()

[TPS_SWCT_01001] Preﬁx symbols generated for the RunnableEntity (cid:100) If and
only if the attribute symbol of a symbolProps owned by an AtomicSwComponent
Type exists, its value shall also be taken for preﬁxing the symbols generated for the
RunnableEntitys owned by the AtomicSwComponentType. (cid:99)()

Note: if symbolProps is not deﬁned the behavior of the RTE generator is fully back
wards compatible, i.e. existing implementations of RunnableEntitys do not have to
be touched in order to conform with this version of the AUTOSAR standard.

This is a further measure to mitigate the risk of potential name clashes in the RTE
code.

[TPS_SWCT_01635] Naming conventions may support the effectiveness of SymbolProps (cid:100) Of course, there is a residual risk that even in the presence of SymbolProps name clashes may occur. Therefore, the deﬁnition of naming conventions may facilitate the avoidance of name clashes to the further degree.
However, these naming conventions can (with the support of the meta-model, e.g. by
utilizing SymbolProps or shortNamePattern) still only be deﬁned on the model level. (cid:99)(RS_SWCT_00230)



#@SECTION: 3.3 Composition
#@SECTION: 3.3.1 Overview
#@CLASS: CompositionSwComponentType
#@CLASS: SwComponentType

Figure 3.7: The recursive relation of software-components and compositions

[TPS_SWCT_01032] CompositionSwComponentType (cid:100) The purpose of an AUTOSAR CompositionSwComponentType is to allow the encapsulation of speciﬁc functionality by aggregating existing software-components. (cid:99)(RS_SWCT_00190,RS_SWCT_02000,RS_SWCT_02020, RS_SWCT_03000)

[TPS_SWCT_01033] Nested deﬁnition of CompositionSwComponentTypes (cid:100)
Since a CompositionSwComponentType is also a SwComponentType, it again may
be aggregated in further CompositionSwComponentTypes. (cid:99)(RS_SWCT_00190,RS_SWCT_02000, RS_SWCT_02020, RS_SWCT_03000)

This recursive relation is formally expressed in Figure 3.7.

It is important to understand that while compositions allow for (sub-) system abstrac
tion, they are solely an architectural element for the implementation of model scalabil
ity. They simply group existing software-components and thereby take away complexity
when viewing or designing logical software architecture.

Therefore, the deﬁnition of CompositionSwComponentTypes has no effect on how
software-components interact with the Virtual Functional Bus (VFB). Composition
SwComponentTypes do not add any new functionality to what is already provided by
the software-components they aggregate.

[TPS_SWCT_01034] CompositionSwComponentTypes do not have any binary footprint (cid:100) As the main consequence, CompositionSwComponentTypes do not have any binary footprint in the ECU software.(cid:99)(RS_SWCT_00190,RS_SWCT_02000, RS_SWCT_02020, RS_SWCT_03000)


#@SECTION: 3.3.2 SwComponentPrototype
#@CLASS: CompositionSwComponentType
Table 3.11: CompositionSwComponentType
#@CLASS: SwComponentPrototype
Table 3.12: SwComponentPrototype
Figure 3.8: Composition and the meta-classes aggregated
#@CLASS: AtomicSwComponentType
#@CLASS: PortPrototype

[TPS_SWCT_01035] CompositionSwComponentType aggregates SwComponentPrototypes (cid:100) In terms of the AUTOSAR meta-model, a composition of softwarecomponents realized by the meta-class CompositionSwComponentType aggregates SwComponentPrototypes which in turn are typed by a SwComponentType.(cid:99)(RS_SWCT_00190, RS_SWCT_02000, RS_SWCT_02020,RS_SWCT_03000)

Please note that a CompositionSwComponentType is also a SwComponentType.

[TPS_SWCT_01036] SwComponentPrototype implements a speciﬁc role (cid:100)
Therefore, a SwComponentPrototype implements the usage of a SwComponent
Type in a speciﬁc role. (cid:99)(RS_SWCT_00190, RS_SWCT_02000, RS_SWCT_02020,
RS_SWCT_03000)

[TPS_SWCT_01037] arbitrary numbers of SwComponentPrototypes can be created (cid:100) In general, arbitrary numbers of SwComponentPrototypes that refer to speciﬁc SwComponentTypes can be created. (cid:99)(RS_SWCT_00190, RS_SWCT_02000,RS_SWCT_02020, RS_SWCT_03000)

Example: a SwComponentPrototype “LeftDoorControl” fulﬁlls the role of implement
ing the SwComponentType “DoorControl” for the left door of a vehicle while the
SwComponentPrototype “RightDoorControl” fulﬁlls the role of the SwComponent
Type “DoorControl” for the right door.

[TPS_SWCT_01080] Delegation ports (cid:100) Note that being a SwComponentType,
a CompositionSwComponentType also exposes PortPrototypes to the out side world.
However,the PortPrototypes are only delegated and do not play the same role as PortPrototypes attached to AtomicSwComponentTypes.(cid:99)(RS_SWCT_03130)

[TPS_SWCT_01081] Implications of being a delegation port (cid:100) Being a PortPro
totype attached to a CompositionSwComponentType has the following implications:
• The delegation has to follow the rules deﬁned in chapter 6.
• By creating PortPrototypes on the surface of a speciﬁc CompositionSwComponentType it is explicitly decided whether or not the contents of an “inner” port contained in the CompositionSwComponentType is exposed to the outside world.(cid:99)(RS_SWCT_03130)

Please note that the semantics of the delegation of PortPrototypes are similar to en
capsulation mechanisms like public and private members in object-oriented program
ming languages.

One implication of the concept of CompositionSwComponentType is that the appli
cation software of an entire vehicle eventually is represented by one Composition
SwComponentType. This so-called top-level composition has a special role in the
context of the AUTOSAR System Template [11].

However, please note that a top-level composition might have (unconnected) Port
Prototypes in order to allow for reuse as part of another system.

[constr_1035] Recursive deﬁnition of CompositionSwComponentType (cid:100) The recursive deﬁnition of a CompositionSwComponentType that eventually contains a SwComponentPrototype typed by the same CompositionSwComponentType shall not be feasible. (cid:99)()

#@SECTION: 3.3.3 Connectors
#@CLASS: SwConnector
#@CLASS: CompositionSwComponent
#@CLASS: DelegationSwConnector
#@CLASS: AssemblySwConnector
#@CLASS: PassThroughSwConnector
#@CLASS: PPortInCompositionInstanceRef
#@CLASS: PRPortPrototype
#@CLASS: DataInterface
Table 3.13: SwConnector
Table 3.14: AssemblySwConnector
Table 3.15: DelegationSwConnector

<-------------- multimodal context 
This diagram illustrates a Composition SW Component that delegates two data ports through an inner Application SW Component, using PassThroughSwConnectors to forward input data to a Runnable (“RunA1”) and then emit an output trigger back to the outer world.

• Component hierarchy  
  – A CompositionSwComponent contains one ApplicationSwComponent (AtomicSwComponentType)  
  – Outer and inner ports are linked via DelegationSwConnectors and PassThroughSwConnectors  

• Ports & interfaces  
  – External ports on the Composition: one ProvidedPortPrototype (>>) and one RequiredPortPrototype (▷) on each side  
  – Internal ports on the Application SWC: corresponding AbstractProvidedPortPrototype and AbstractRequiredPortPrototype  
  – DataInterface instances map the ports; connectors: DelegationSwConnector (to composition boundary) and PassThroughSwConnector (between inner ports)  

• Data flow  
  – Incoming data arrives at the inner RPort, passes through to RunA1 as an argument (dashed arrow)  
  – RunA1 is activated by an RTO timing event, produces a “Trigger” on the inner PPort  
  – The trigger is passed through to the external PPort and delivered to downstream components  

• Key AUTOSAR concepts  
  – RunnableEntity (“RunA1”) with InternalTriggeringPoint (RTO)  
  – AbstractProvided/RequiredPortPrototypes, DataInterfaces, DelegationSwConnector, PassThroughSwConnector  
  – Event-driven vs. data-triggered invocation, port-based communication  

• Scenario  
  – Demonstrates a pass-through use case: forwarding raw data into an application runnable and routing its event-triggered output unchanged to an external consumer. ---------------------->
Figure 3.9: Use case for PassThroughSwConnector (I)
Table 3.16: PassThroughSwConnector
Figure 3.10: Connectors

<-------------- multimodal context 
This diagram illustrates a Composition SWC using a PassThroughSwConnector pattern: it exposes client-server interfaces on its outer ports that are directly delegated to an inner Application SWC’s matching ports via DelegationSwConnectors and a PortInterfaceMapping, enabling transparent forwarding of operation calls and responses without additional composition-level logic.

- Component hierarchy – one CompositionSwComponent encapsulates a single ApplicationSwComponent; child ports are linked to parent ports by DelegationSwConnectors.  
- Ports & interfaces – two outer Provided ports (PPorts, “>>” icon) and one outer Required port (RPort, “>” icon) on the composition; inner ApplicationSwComponent defines corresponding AbstractProvidedPortPrototype and AbstractRequiredPortPrototype typed by a ClientServerInterface.  
- Data flow – client sends an asynchronous server call to the composition’s RPort, which is delegated to the inner RPort; the inner PPort returns the result back through the composition’s PPort.  
- Key AUTOSAR concepts – DelegationSwConnector, PortInterfaceMapping, AbstractProvidedPortPrototype/AbstractRequiredPortPrototype, ClientServerInterface, AsynchronousServerCallPoint/ReturnsEvent.  
- Scenario – a transparent container pattern that groups and re-exposes an SWC’s interface unchanged for layering, reuse, or packaging. ---------------------->
Figure 3.11: Use case for PassThroughSwConnector (II)

[TPS_SWCT_01079] SwConnector (cid:100) Note that CompositionSwComponent
Type also aggregates the abstract meta-class SwConnector for connecting
the SwComponentPrototypes contained among each other(see Figure 3.8).(cid:99)(RS_SWCT_03130)

CompositionSwComponentTypes contain two kinds of SwConnectors:
#@Hierarchical
• [TPS_SWCT_01082] AssemblySwConnector (cid:100) AssemblySwConnectors in
terconnect PortPrototypes of SwComponentPrototypes that are part of the CompositionSwComponentType. (cid:99)(RS_SWCT_03130)
• [TPS_SWCT_01083] DelegationSwConnector (cid:100) DelegationSwConnectors connect from “inner” PortPrototypes to delegated “outer” PortPrototypes. (cid:99)(RS_SWCT_03130)

[constr_1032] DelegationSwConnector can only connect PortPrototypes of the same kind (cid:100) A DelegationSwConnector can only connect PortPrototypes of the same kind, i.e. PPortPrototype to PPortPrototype and RPortPrototype to RPortPrototype. (cid:99)()

[TPS_SWCT_01084] Outer PortPrototype is referenced by multiple DelegationSwConnectors (cid:100) In the case that an outer PortPrototype is referenced by multiple DelegationSwConnectors the semantic is the multiplication of the AssemblySwConnectors referencing the outer PortPrototypes.(cid:99)(RS_SWCT_03130)
/#@Hierarchical

[constr_1086] SwConnector between two speciﬁc PortPrototypes (cid:100) Each pair
of PortPrototypes can only be connected by one and only one SwConnector. (cid:99)()

In other words, it is not supported to create two different SwConnectors that connect
the same pair of PortPrototypes.

[TPS_SWCT_01638] Existence of SwConnector between two PRPortPrototypes (cid:100) [constr_1086] applies also in the case that two PRPortPrototypes are connected with each other. In particular, the roles
• AssemblySwConnector.requester
• AssemblySwConnector.provider
• PassThroughSwConnector.providedOuterPort
• PassThroughSwConnector.requiredOuterPort
do not establish a direction in this case. (cid:99)()

For clariﬁcation, [TPS_SWCT_01638] means that the SwConnector represents the
ability for bi-directional communication between the two PRPortPrototypes.

[constr_1087] AssemblySwConnector inside CompositionSwComponentType (cid:100)
An AssemblySwConnector can only connect PortPrototypes of SwComponentPrototypes that are owned by the same CompositionSwComponentType (cid:99)()

[constr_1088] DelegationSwConnector inside CompositionSwComponentType (cid:100) A DelegationSwConnector can only connect a PortPrototype of a SwComponentPrototype that is owned by the same CompositionSwComponentType that also owns the connected delegationPortPrototype. (cid:99)()

In the context of attaching a DelegationSwConnector to an inner PRPortProto
type there is some ambiguity to be considered. In particular, from the formal point of
view it would be feasible to use either a PPortInCompositionInstanceRef or a
RPortInCompositionInstanceRef.

The ability to use one or the other meta-class arbitrarily is considered confusing. There
fore, [TPS_SWCT_01515] has been deﬁned to remove the unnecessary degree of freedom.

[TPS_SWCT_01515] PPortInCompositionInstanceRef shall be used for attaching DelegationSwConnector to an inner PRPortPrototype (cid:100) For the implementation of the attachment of a DelegationSwConnector to an inner PRPortPrototype the meta-class PPortInCompositionInstanceRef shall be used. (cid:99)()

[constr_1100] Unconnected RPortPrototype typed by a DataInterface (cid:100) For
any element in an unconnected RPortPrototype typed by a DataInterface there
shall be a requiredComSpec that deﬁnes an initValue. (cid:99)()

One speciﬁc use case for the application of SwConnectors is exempliﬁed by the ﬁg
ures 3.9 and 3.11. A speciﬁc CompositionSwComponentType exists in two variants
where one (more complex) variant foresees the existence of a SwComponentPrototype inside the CompositionSwComponentType (depicted by 3.9) and the other(because it is implementing a simpler semantics) does not need the SwComponentPrototype.

Without the ability to deﬁne a PassThroughSwConnector the second variant could
only be implemented by deﬁning a dummy SwComponentPrototype inside the
CompositionSwComponentType. However, the dummy SwComponentPrototype
would need to deﬁne RunnableEntitys that are created for the sole purpose of being
able to shovel the data from (e.g. for sender-receiver communication) RPortPrototypes to PPortPrototypes.

This would not only be cumbersome it would also obviously require additional re
sources (memory and code) at run-time. Plus, the existence of addition RunnableEn
titys also unnecessarily increases the propagation delay of information ﬂowing
around inside the ECU.

[TPS_SWCT_01507] The role of PassThroughSwConnector (cid:100) PassThrough
SwConnector can be taken to connect PortPrototypes owned by the same Com
positionSwComponentType. In other words, PassThroughSwConnector creates
a bypass inside a CompositionSwComponentType form the requiredOuterPort
to the the providedOuterPort (or vice versa) without involving SwComponentPro
totypes. (cid:99)()

[constr_1252] Creation of a loop involving a PassThroughSwConnector is not
allowed (cid:100) A PassThroughSwConnector is not allowed if the required outer Port
Prototype is directly or indirectly connected to the provided outer PortPrototype
without the placement of a SwComponentPrototype typed by an AtomicSwCompo
nentType in the chain of SwConnectors. (cid:99)()

In other words, according to [constr_1252] it is not allowed to create a “inﬁnite loop” by
means of a PassThroughSwConnector and at least one AssemblySwConnector
that connects the requiredOuterPort to the providedOuterPort.

#@SECTION: 3.3.4 Instantiation-speciﬁc RTEEvents
#@CLASS: RTEEvent
#@CLASS: InstantiationRTEEventProps
#@CLASS: ApplicationSwComponentType
#@CLASS: SwcInternalBehavior
#@CLASS: CompositionSwComponentType
Figure 3.12: Instantiation speciﬁc Properties of RTEEvents
Table 3.17: InstantiationRTEEventProps

[TPS_SWCT_02507] Instantiation-speciﬁc RTEEvents (cid:100) It is possible to specify
instantiation speciﬁc properties of an RTEEvent by applying InstantiationRTEEventProps in the role instantiationRteEventProps.This allows to use the same ApplicationSwComponentType in different timing scenarios. Even if the scheduling is an issue of the SwcInternalBehavior, the instancespeciﬁc deﬁnition of timing needs to be speciﬁed on the level of a CompositionSwComponentType. (cid:99)(RS_SWCT_03046, RS_SWCT_03270)

As an example for [TPS_SWCT_02507], please consider a software-component that
implements a closed-loop control algorithm.

This software-component can potentially be deployed to “slow” and “fast” control scenarios. As the actual time-base of the control algorithm is derived from the scheduling implemented in the RTE it obviously facilitates the overall design if the timing can bedeﬁned on“instance” level.

[constr_1233] InstantiationTimingEventProps shall only reference TimingEvent (cid:100) An 
InstantiationTimingEventProps shall only reference TimingEvent in the role refinedEvent. A reference to other kinds of RTEEvents is not supported. (cid:99)()

#@SECTION: 3.4 Port Interface
#@CLASS: PortPrototype
#@CLASS: PortInterface
#@CLASS: SenderReceiverInterface
#@CLASS: NvDataInterface
#@CLASS: ParameterInterface
#@CLASS: ModeSwitchInterface
#@CLASS: ClientServerInterface
#@CLASS: TriggerInterface
#@ENUM: ServiceProviderEnum

Figure 3.13: DataInterface as an abstract base class
Table 3.18: PortInterface
Table 3.19: DataInterface
Figure 3.14: PortInterfaces in the AUTOSAR meta-model
Figure 3.15: PortInterfaces and AUTOSAR services
Table 3.20: ServiceProviderEnum

[TPS_SWCT_01025] The role of PortPrototypes in the AUTOSAR architecture (cid:100) A PortPrototype mainly contributes the functionality of being a connection point to the AUTOSAR concept.The details, i.e. with respect to what kind of information is actually transported between two PortPrototypes is deﬁned by the PortInterface.(cid:99)(RS_SWCT_00010,
RS_SWCT_00080, RS_SWCT_00110, RS_SWCT_02030, RS_SWCT_03010)

[TPS_SWCT_01026] The role of PortInterfaces in the AUTOSAR architecture (cid:100) PortInterfaces (see Figure 3.14) are used to support a design-by-contract workﬂow, i.e. a PortInterface provides means to formally verify structural and dynamic compatibility between software-components. (cid:99)(RS_SWCT_00010, RS_SWCT_00080,RS_SWCT_00110, RS_SWCT_02030,RS_SWCT_03010)

In other words: PortInterfaces represent a pivotal point in the AUTOSAR concept.

Please note that a PortInterface creates a name space for the information con
tained. This allows for deﬁning the details of a speciﬁc PortInterface without hav
ing to care for possible side-effects on other PortInterfaces. Again, this property
of the AUTOSAR concept directly supports re-usability.

[TPS_SWCT_01027] Different ﬂavors of PortInterfaces (cid:100) Within the AUTOSAR
concept, different ﬂavors of PortInterfaces are deﬁned:
• SenderReceiverInterface
• NvDataInterface
• ParameterInterface
• ModeSwitchInterface
• ClientServerInterface
• TriggerInterface
(cid:99)(RS_SWCT_00010, RS_SWCT_00080, RS_SWCT_00110, RS_SWCT_02030)

[TPS_SWCT_01069] DataInterface is deﬁned as abstract base class (cid:100)
Please note that the conceptual relationship of SenderReceiverInterface, NvDataInterface, and ParameterInterface is expressed by the deﬁnition of the abstract base class DataInterface. (cid:99)(RS_SWCT_00010, RS_SWCT_00080,RS_SWCT_00110, RS_SWCT_03010)

Please ﬁnd more details about the specialization of the PortInterface concept in
chapter 4.2.3 and 4.2.2.

[TPS_SWCT_01070] PortInterface acts as a type for a PortPrototype (cid:100) From
an abstract point of view, a PortInterface acts as a type for a PortPrototype. This means in particular that several PortPrototypes can be typed by the same PortInterface. (cid:99)(RS_SWCT_00010, RS_SWCT_00080, RS_SWCT_00110,RS_SWCT_03010)

Of course, this aspect facilitates the creation of valid connections between software
components dramatically. By using a speciﬁc PortInterface for typing particular
PortPrototypes the latter are eligible for being connected to each other by deﬁnition.

However, the creation of a valid connection does not need to be based on the usage of
identical PortInterfaces. It is also possible to use different, but compatible Port
Interfaces. The details about compatibility of PortInterfaces are described in
chapter 6.

[constr_1036] Connect kinds of PortInterfaces (cid:100) It shall not be possible to connect PortPrototypes typed by PortInterfaces of different kinds. Subclasses of DataInterface make an exception from this rule and can be used for creating connections to each other. (cid:99)()

For clariﬁcation, a connection between a PortPrototype typed by a SenderReceiverInterface and a PortPrototype typed by a ClientServerInterface shall not be possible. However, the creation of a connection between a PortPrototype typed by a SenderReceiverInterface and a PortPrototype typed by a ParameterInterface is supported.

[constr_1137] Applicability of ParameterInterface (cid:100) A PPortPrototype typed
by a ParameterInterface can only be owned by a ParameterSwComponentType. (cid:99)()

Please note that PortInterfaces also play an important role in the context of deﬁning so-called AUTOSAR services. In particular, by means of the attribute isService
a PortInterface can deﬁne whether or not it is supposed to be used in the context
of an AUTOSAR service and in addition to this it may deﬁne (by means of the attribute
serviceKind) what kind of service is intended.

The information contained in serviceKind can be used in various ways. The primary
intent is to distinguish between the usage of standardized AUTOSAR services from
the usage of a vendor-speciﬁc service. This information may have an impact on the
development- and build process of software-components that use the PortInter
face.

In addition, it is also possible to use the information contained in serviceKind for
ﬁltering the presentation of an AUTOSAR model in an AUTOSAR authoring tool and
e.g. display the nature of the service PortPrototypes independently of the content
of the corresponding PortInterface.

[TPS_SWCT_01003] Inconsistencies regarding the value of serviceKind and
the actual implementation of the PortInterface (cid:100) In case of inconsistencies
between the value of serviceKind and the actual implementation of the PortInterface the implementation of the PortInterface wins over the value of attribute PortInterface.serviceKind (which, for the intended purpose shall be considered an annotation rather than a semantically binding information). (cid:99)()

[TPS_SWCT_01004] Default value if serviceKind is not deﬁned (cid:100) if the attribute
serviceKind is not deﬁned in the context of a speciﬁc PortInterface the default
value anyStandardized shall be assumed. (cid:99)()

[constr_1174] PortInterfaces used in the context of CompositionSwComponentTypes cannot refer to AUTOSAR services (cid:100) CompositionSwComponentTypes shall not own PortPrototypes typed by PortInterfaces where the attribute isService is set to true. (cid:99)()

[TPS_SWCT_01005] Usage of SwcServiceDependencys for vendor-speciﬁc services (cid:100) SwcServiceDependencys can also be used for vendor-speciﬁc services.In this case the SwcServiceDependency shall not contain any of the standardized ServiceNeeds. (cid:99)()

Please ﬁnd more details about the relation of PortInterfaces to AUTOSAR services
in chapter 11.

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

#@SECTION: 5 Data Description
#@SECTION: 5.1 Introduction
#@CLASS: ApplicationDataType
#@CLASS: ApplicationSwComponentType
#@CLASS: BaseType
#@CLASS: ImplementationDataType
#@CLASS: PlatformDataType
#@CLASS: StandardType
#@CLASS: SwDataDefProps
#@CLASS: DataPrototype
#@CLASS: SwRecordLayout

[TPS_SWCT_01229] Three different levels of abstraction regarding the definition of data types (cid:100) In the context of defining data types and prototypes, the AUTOSAR concept distinguishes between three different levels of abstraction as depicted in Table 5.1. (cid:99)(RS_SWCT_03215, RS_SWCT_03216, RS_SWCT_03217)

Application Data Level
Implementation Data Level
Base Type Level

<-------------- multimodal context 
```markdown
| Application Data Level    |
|---------------------------|
| Implementation Data Level |
| Base Type Level           |
``` ---------------------->
Table 5.1: Abstraction Levels for Describing Data

[TPS_SWCT_01230] Application Data Level (cid:100) The Application Data Level is the common level at which ApplicationSwComponentTypes specify a data type or prototype. This level allows to define all the data attributes which are needed from the application point of view, in order to exchange data between software components or between a software component and a measurement and calibration tool. It is possible to specify data communication of a complete Virtual Function Bus based on this level only.

This level includes among other things the numerical range of values, the data structure as well as the physical semantics. Data semantics (e.g. physical units) is not in the focus1 for the RTE in order to make communication technically possible. However, it is important for a unique interpretation of data in the application software and in measurement and calibration systems. (cid:99)(RS_SWCT_03216)

In former version of this specification, this level was not clearly separated from the implementation level. These had the following drawbacks which are now solved:

• The model of primitive types (like integer, boolean, real, opaque) was anticipating implementation aspects already on a very high level of design.
• The data type model used within ports, focusing on communication via the RTE, was not sufficient to model all type-aspects of variables and parameters which are visible within an AUTOSAR system for other purposes than RTE-communication, namely NvM-data access, calibration, measurement, diagnostics, BSW-module interfaces. Using a uniform type system covering all these aspects is now favored.
• Calibration parameters were not completely incorporated into the data type concept. Some of their attributes (especially for curves and maps) could be specified only on the level of prototypes or were not completely formalized within AUTOSAR (like SwRecordLayout).
• The data type system was not compatible with the usage in calibration standards like ASAM-MCD (namely the usage of categorys).
• Adding implementation specific elements like a base type, was not possible without formally changing the data type used in a VFB design. A mapping mechanism that could be used in later project phases and is common in other parts of AUTOSAR (e.g. for mapping components to ECUs) was missing.
• The RTE Specification contained many default rules and assumptions on how to implement certain data types or prototypes in C. With a more formal description of all relevant implementation aspects, the generation of C-interfaces is better determined. But these aspects should be separated from the application level design.
• Since there could be many data types on the application level in a big system, the probability of name clashes in the interfaces to the RTE was rather high. Using a separate set of types to implement the RTE interfaces solves this issue.

[TPS_SWCT_01231] Application level may impose strong requirements on the design of the corresponding implementation level (cid:100) It should be pointed out, that with the specification of computation methods and record layouts, the application level imposes strong requirements on the design of the corresponding implementation level (for further information see 6.2.5). It might even be the case, that when anticipating different implementations, these elements might be chosen differently.

This is due to the nature of these elements which form a bridge from the physical world to the numerical representation (and vice versa). Nonetheless we consider the specification of these elements as belonging to the application level.

On the one hand, this information is required by MCD-tools and thus shall be part of a rather high-level design. On the other hand, this approach will allow to use a limited set of implementation data types. (cid:99)(RS_SWCT_03215, RS_SWCT_03216, RS_SWCT_03217)

[TPS_SWCT_01232] Implementation Data Level (cid:100) The Implementation Data Level is closer to the actual code implementation in a programming language like C, though it is still an abstraction of the code.

Its values correspond to the actual binary numbers handled by the programming language on the CPU. It contains concepts like pointers and unions which relate to the organization of data in memory and are not relevant for the application level.

This level also defines structure, but it can be more granular. For example, the application level may define a text to be transferred to an instrument cluster as a primitive type (if the structure is not relevant for the application), whereas on the implementation level it could be modeled as an array of bytes. (cid:99)(RS_SWCT_03217)

[TPS_SWCT_01233] Use case for the Implementation Data Level (cid:100) There are several use cases for this level in AUTOSAR:

• First of all, the Implementation Data level can be used in the description of interfaces, and data (e.g. debug data) within the basic software, see [7] for more details on these use cases.
• ImplementationDataTypes should also be used to describe the interfaces of libraries which operate on a purely numerical level.
• Implementation Data is also used for the description of interfaces between software-components and and the basic software (namely AUTOSAR Services), because these typically cover implementation aspects only.
• It is possible to define communication in a VFB system directly on this level if the physical and semantical abstraction is not of interest.
• Last not least the input for the RTE generator is defined by data descriptions on this level. This means that in case a SWC defines its data only on application level a corresponding set of implementation data types shall be created (or generated) as part of the ECU extract before the RTE can be generated.

(cid:99)(RS_SWCT_03217)

[TPS_SWCT_01234] Base Level (cid:100) The Base Type Level is used to describe the primitive elements in terms of bits and bytes from which the implementation data is built up. It is considered as a separate level in order to allow for reuse of the basic types defined on this level.

These base types still do not completely determine the actual implementation on a programming language, but they impose strong restrictions for this as they define for example the number of bits and bytes to be used.

Depending on the use case, the base types can be defined as platform independent or can also contain platform specific attributes (namely endianess and alignment). (cid:99)()

[TPS_SWCT_01235] Mapping of data defined on the Application level to the Implementation and Base Type level (cid:100) It is important to understand, that the mapping of data defined on the Application level to the Implementation and Base Type level depends on the medium on which the data is transported.

For example, if a physical value can be expressed with sufficient accuracy and range by a 16-bit unsigned integer, it still might look very different when sent over CAN, when seen by a software-component on a big-endian 32-bit machine or when seen by a software-component on a little-endian 16-bit processor.

Conversion between several data implementations of the same application data type might be necessary in case of communication between components on different ECUs. AUTOSAR COM [21] is responsible for this.

It implies that the configuration depends on the definition of the data that are transmitted between components. (cid:99)(RS_SWCT_03215, RS_SWCT_03216, RS_SWCT_03217)
More exactly speaking, the data shall be converted to and from a so-called SystemSignal.

AUTOSAR COM might need to convert a 16-bit integer between little-endian and big-endian representations; whereas an array of 16 bytes does not need to be swapped even if the endianess changes. In case of intra-ECU communication byte order conversion is not necessary, since the software-components reside on the same machine.

[TPS_SWCT_01236] Big picture of data types (cid:100) Another way of approaching the concept of data types in AUTOSAR (especially with respect to the question of what "kind" of data type in related to which modeling meta-level) is to sketch the following "big picture" of data types:
#@Hierarchical
ApplicationDataType Defined on M2 - provides the meta model for data types on application level. It covers the application-relevant aspects of a data type. An ApplicationDataType shall finally be mapped to an ImplementationDataType.
/#@Hierarchical
#@Hierarchical
ImplementationDataType Defined on M2 - provides the meta-model for data types on implementation level. With respect to C source code, an ImplementationDataType finally boils down to a typedef.
/#@Hierarchical
#@Hierarchical
BaseType Defined on M2 - provides the platform-dependent part of an ImplementationDataType. the dependency on the platform covers the following aspects:
• Definition on the level of the C language - using nativeDeclaration
• Technical representation on the target platform (byte order, alignment, encoding) as required for the support of MCD systems.
/#@Hierarchical
#@Hierarchical
Platform Data Type Defined on M1 - provided by AUTOSAR. Platform types shall be available on each platform on which an AUTOSAR-System can run. The name of the Platform Data Type and the properties with respect to the interface between modules / components is the same on every platform. The particular representation varies from platform to platform. Platform Data Types shall be modeled using ImplementationDataTypes.

Note that in AUTOSAR R3.x the platform types are implemented manually and could even not be expressed on ARXML model (see [SRS_Rte_00150]). In AUTOSAR R4.1 the Platform Data Types can be represented in the ARXML model. Subsequent releases of AUTOSAR may generate the Platform Data Types directly from the ARXML Model.
/#@Hierarchical
#@Hierarchical
Standard Type Defined on M1 - provided by AUTOSAR. Standard types are defined by referring to platform types.
/#@Hierarchical
(cid:99)(RS_SWCT_03215, RS_SWCT_03216, RS_SWCT_03217)

[TPS_SWCT_01237] SwDataDefProps (cid:100) The properties of data are summarized in the meta-class SwDataDefProps. This meta-class itself is the superset of all applicable properties. (cid:99)(RS_SWCT_03216, RS_SWCT_03217)

Subsets of SwDataDefProps are applicable in specific case, for a summary please refer to the following tables:
• The data categorys are summarized in table 5.7.
• Properties for ApplicationDataTypes are summarized in table 5.8.
• Properties for ImplementationDataTypes are summarized in table 5.18.
• Properties for DataPrototypes typed by ApplicationDataTypes are summarized in table 5.31.
• Properties for DataPrototypes typed by ImplementationDataTypes are summarized in table 5.32.
• Applicability of SwDataDefProps is summarized in table 5.39.

#@SECTION: 5.2 Data Types
#@SECTION: 5.2.1 Overview
#@CLASS: ApplicationDataType
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: AutosarDataType
#@CLASS: ImplementationDataType

As explained in section 5.1 it is possible to describe data provided by a software component from the application as well as from the implementation point of view.

[TPS_SWCT_01072] ApplicationDataType and ImplementationDataType (cid:100) The common concept behind this is expressed by the abstract meta-class AutosarDataType, from which an ApplicationDataType and an ImplementationDataType is derived. (cid:99)(RS_SWCT_03215, RS_SWCT_03216, RS_SWCT_03217)

Figure 5.1 shows a summary of the basic meta-classes used for the definition of AutosarDataTypes.

Figure 5.1: Summary of AutosarDataType
Table 5.2:AutosarDataType
Table 5.3: ApplicationDataType
Table 5.4: ImplementationDataType

[TPS_SWCT_01073] Composite ApplicationDataType (cid:100) An ApplicationDataType can be composed (in form of a record or an array) of elements which themselves are typed by another ApplicationDataType. (cid:99)(RS_SWCT_03215, RS_SWCT_03216)

[TPS_SWCT_01074] Composite ImplementationDataType (cid:100) An ImplementationDataType can also be composed of elements but in this case no type/prototype concept (see [12]) has been applied. Both concepts will be explained in the following chapters in more detail. (cid:99)(RS_SWCT_03215, RS_SWCT_03217)

#@SECTION: 5.2.2 Data Type Mapping
#@CLASS: DataTypeMap
#@CLASS: DataTypeMappingSet
#@CLASS: ModeRequestTypeMap
#@CLASS: ApplicationDataType
#@CLASS: InternalBehavior
#@CLASS: ParameterSwComponentType
#@CLASS: NvBlockDescriptor
#@CLASS: CompositionSwComponentType
#@CLASS: PortPrototypes
#@CLASS: DelegationSwConnector
#@CLASS: PassThroughSwConnector

As explained above, the concept of application data types as well as that of implementation data types can be used to instantiate a data prototype in an M1 model. However there are use cases, especially in order to generate the RTE contract for ApplicationSwComponentTypes, where it is required to consider both levels for one given data prototype.

[TPS_SWCT_01189] DataTypeMap (cid:100) This is supported by the meta-class DataTypeMap by which an ApplicationDataType and an ImplementationDataType can be mapped to each others in order to describe both aspects of one dataElement. (cid:99)(RS_SWCT_03216, RS_SWCT_03217, RS_SWCT_03215)

This class represents the relationship between ApplicationDataType and its implementing ImplementationDataType. This is the corresponding ImplementationDataType. This is the corresponding ApplicationDataType.

Table 5.5: DataTypeMap

If, for example, a dataElement in a SenderReceiverInterface is typed by an ApplicationDataType it shall additionally be associated to an ImplementationDataType in order to be able to generate the RTE.

[TPS_SWCT_01190] ModeRequestTypeMap (cid:100) Another mapping class, ModeRequestTypeMap, has been introduced in order to allow the transport of mode related information via "normal" sender-receiver communication. Apart from this, mode information is not handled by the usual type system but needs special meta-classes. This is explained in more detail in chapter 4.2.5. (cid:99)(RS_SWCT_03110)

Note that the mapping classes instead of direct associations have been introduced for process reasons: It allows to maintain application and implementation types in separate M1 artifacts without direct links.

For example, if a software component is moved to another hardware platform the mapping between application and implementation types might be changed in the scope of the specific component without changing the overall VFB model.

[TPS_SWCT_01191] mapped ApplicationDataType and ImplementationDataType shall be compatible (cid:100) In order to set up a valid DataTypeMap between an ApplicationDataType and an ImplementationDataType the two types shall be compatible. This is further explained in chapter 6.2.5. Of course, if ImplementationDataTypes are generated from existing ApplicationDataTypes it is expected that they will be automatically compatible. (cid:99)(RS_SWCT_03216, RS_SWCT_03217)

Furthermore, the various mappings are aggregated in a container DataTypeMappingSet for easier maintenance in artifacts.

Table 5.6: DataTypeMappingSet

Note that the meta-classes AutosarDataType, ModeDeclarationGroup and DataTypeMappingSet are derived from ARElement. This means that these and the meta-classes derived from them can be declared on the M1 level as part of an ARPackage and thus can be used in several different Software Component or Basic Software Module Descriptions.

How to organize DataTypeMappingSets for a software system, for example whether there is a separate mapping set for each ECU or even for each software component, is considered as project specific. However, the RTE generator needs a well defined DataTypeMappingSet as input in relation those artifacts which might define data typed as ApplicationDataTypes.

[TPS_SWCT_01192] Meta-classes that have an association to a DataTypeMappingSet (cid:100) Therefore, the following meta-classes in the scope of this document have an association to a DataTypeMappingSet:
• InternalBehavior, because it represents the interface between the software component's code and the RTE and all data types belonging to the particular component type have to be uniquely provided on implementation level.
• ParameterSwComponentType, for the same reason (this component type doesn't have an InternalBehavior).
• NvBlockDescriptor, because this meta-class also leads to generation of code from data types and is not associated to an InternalBehavior.
• CompositionSwComponentType, to support the definition of ComSpecs in the context of a CompositionSwComponentType. Please note that this definition of a data type mapping is informal (i.e. it shall be taken as a hint for delegation PortPrototypes that are not yet referenced by a DelegationSwConnector or PassThroughSwConnector) and shall not be regarded as a binding contract towards the inner elements of the CompositionSwComponentType. (cid:99)()

For more details about this aspect please refer to figure 5.60.

[TPS_SWCT_01193] Mappings between application and implementation types do not necessarily have to form a 1:1 relation (cid:100) In general, it is not required that the sum of all mappings between ApplicationDataType and ImplementationDataType in a given system form a 1:1 relation. Depending on the use case and on the scope, 1:n as well as n:1 mappings are possible:
• Several different ApplicationDataTypes may be mapped to the same ImplementationDataType in the scope of a system, an ECU, or even a single InternalBehavior of an atomic software component. Of course, this requires that the different ApplicationDataTypes are used for different DataPrototypes and thus that the DataPrototypes are typed by them (and not by the ImplementationDataTypes). This allows to establish a more simple type system on the implementation level, than on the application model level.
• The same ApplicationDataTypes may be mapped to different ImplementationDataTypes for different ECUs. This scenario allows to chose the implementation data types according to the needs of specific ECUs.
• [constr_1004] Mapping of ApplicationDataTypes (cid:100) The same ApplicationDataTypes may be mapped to different ImplementationDataTypes even in the scope of a single ECU (more exactly speaking, a single RTE), but not in the scope of a single atomic software component. (cid:99)() This improves the portability of software components which were developed independently or are ported between ECUs.

[constr_1005] Compatibility of ImplementationDataTypes mapped to the same ApplicationDataType (cid:100) It is required that ImplementationDataTypes which are taken for connecting corresponding elements of PortInterfaces and thus refer to compatible ApplicationDataTypes are also compatible among each other (so that RTE is able to cope with possible connections by converting the data accordingly). (cid:99)()

This constraint is visualized in figure 5.2.


<-------------- multimodal context 
This diagram illustrates AUTOSAR’s rules for ensuring type compatibility between application-level data definitions on connected ports and their corresponding implementation-level representations. It shows how two ApplicationDataType prototypes on a sender and receiver side must be mutually compatible and connected, how each maps down to an ImplementationDataType in its respective SW-component, and how those implementation types must themselves be compatible to guarantee correct end-to-end data exchange.

• Component hierarchy  
  – Two ApplicationDataType elements (source and sink) and two corresponding ImplementationDataType elements  
  – Implicitly tied to two SW-component instances via their ports  

• Ports & interfaces  
  – RPort/PPort exchanging ApplicationDataType  
  – DataPrototype mapping steps from ApplicationDataType to ImplementationDataType  

• Data flow  
  – Bidirectional “compatible and connected” at application level  
  – Unidirectional “compatible and mapped” down to implementation  
  – Dashed link “shall also be compatible” between implementation types  

• Key AUTOSAR concepts  
  – ApplicationDataType vs. ImplementationDataType  
  – DataPrototype mapping and compatibility rules  
  – Port interfaces and type compatibility requirements  

• Scenario  
  – Design intent: enforce transitive type compatibility from port interfaces through to code-level data structures for safe inter-SWC communication. ---------------------->
Figure 5.2: Compatibility of Data Types

#@SECTION: 5.2.3 Data Categories
#@CLASS: ApplicationDataType
#@CLASS: AutosarDataType
#@CLASS: ImplementationDataType
#@CLASS: SwDataDefProps
#@CLASS: SwSystemconst
#@CLASS: ImplementationDataType
#@CLASS: McDataInstance
#@CLASS: Identifiable
An AutosarDataType is derived from Identifiable, thus having a longName, a shortName, a category, and several further attributes for administrative and documentation purposes (for details see [12]).

[TPS_SWCT_01238] Attribute category used in the context of Autosar DataType (cid:100) The category attribute is used to set constraints for the various properties which can be specified for an AutosarDataType. These properties are defined by aggregating the meta-class SwDataDefProps which contains several attributes and references, see detailed description in chapter 5.4 and 5.4. (cid:99)()

[constr_1143] category of AutosarDataType shall not be extended (cid:100) In contrast to the general rule that category can be extended by user-specific values it is not allowed to extend the meaning of the attribute category of meta-class AutosarDataType (cid:99)()

This approach avoids a very deep and complicated inheritance tree which otherwise would be needed on the M2 level for AutosarDataType. There is to some extend a redundancy between setting the category and defining the attributes of AutosarDataType.swDataDefProps. This redundancy is intended and allows to for a tool to rule out senseless configurations via simple rules.

In former version of this specification the categories were only used for calibration parameters. Due to several extensions the categories are now applicable for all use cases of the AutosarDataType.

An overview on all valid categorys defined for AutosarDataType is shown in table 5.7. Some of the categorys are also applied to sub-elements of the type system (column "Applicable to ..." in table 5.7). This is explained in more detail in the following sections.

Please note that the column "RTE + BSW" of table 5.7 is only applicable for categorys that are relevant either for ImplementationDataTypes and/or the aspect of measurement and calibration in McDataInstance.

[constr_1006] applicable data categories (cid:100) Table 5.7 defines the applicable categorys depending on specific model elements related to data definition properties. (cid:99)()

Table 5.7: Usage of category for Data Types
<-------------- multimodal context 


| Category |Applicable to ApplicationArrayDataype |Applicable to ApplicationRecordDataType |Applicable to ApplicationPrimitiveDataTpe |Applicable to ApplicationRecordElement |Applicable to ApplicationArrayElement |Applicable to ApplicationValueSpecification | Applicable to ImplementationDataype |Applicable to ImplementationDataTypeElement |Applicable to SwServiceArg |Applicable to SwSystemconst |Applicable to MCDatanstance |use case for Calibration |use case for Measurement |use case for CommunicationPortInterfaces |use case for RTE+BSW | Description |
|----------|------------------------|---------------------------|----------------------------|-------------------------|------------------------|------------------------------|----------------------|------------------------------|--------------|---------------|---------------|-------------|-------------|---------------------------|---------|-------------|
| VALUE | | | X | X | X | X | X | X | | X | X | X | X |X | x | Contains a single value. |
| VAL_BLK | | | X | X | X | X | | | | | X | X | | | | A value block defines values stored together within one calibration parameter object.It is similar to an value array but it stores the values by means of an axis instead (only important for calibration data handling). |
| DATA_REFERENCE | | | | | | | X | X | X | | | | | | X | Contains an address of another DataPrototype(whose type is given via SwDataDefProps.swPointerTargetProps). |
| FUNCTION_REFERENCE | | | | | | | X | X | X | | | | | | X | Contains an address of a function prototype(whose signature is given via SwDataDefProps.swPointerTargetProps.functionPointerSignature). |
| TYPE_REFERENCE | | | | | | | X | x | X | | | | | X | x | The element is defined via reference to another data type (via SwDataDefProps.implementationDataType). |
| STRUCTURE | | X | | X | X | | X | X | | | X | X | X | X | x | Holds one or several further elements which can have different AutosarDataTypes.The underlying elements are defined in the same manner as normal data except for the association to SwAddrMethod:This has to be the same for all underlying elements.Corresponds to a Record if used in the application domain. |
| UNION | | | | | | | X | X | | | x | X | X | | x | Can hold values of different data types.It is similar to STRUCTURE except that all of its members start at the same location in memory.A UNION data prototype can contain only one of its elements at a time.The size of the UNION is at least the size of the largest member. |
| ARRAY | x | | | x | X | | X | X | | | x | X | x | x | x | An array of sub-elements which are of the same type. |
| BIT | | | | | | | | | | | x | X | X | | x | One or several bits within a host variable,which are treated as an own data object. |
| HOST | | | | | | | | | | | x | X | X | | x | A HOST data type is like a simple VALUE,but it is used for packed bit definition.That means it can host several BIT variables which have their own description and measurement access. |
| STRING | | | X | X | X | X | | | | | x | x | X | X | | Contains a single value interpreted as a text string(note that it appears as a single value for the application domain;the internal representation can be an array). |
| BOOLEAN | | | X | X | X | X | | | | | x | x | X | X | | Contains one boolean state.Depending on the CPU direct addressing of single bits may not be available.So a byte or a word can be used to store only one logical state. |
| COM_AXIS | | | X | | x | X | | | | | x | X | | | | An axis definition as separate calibration parameter which can be referenced by any CURVE,MAP,CUBOID,CUBE_4,and CUBE_5.The benefits by using a common axis is that it saves memory space;because it is stored only one time and can be used in multiple CURVES,MAPS,CUBOIDS,CUBE_4s,and CUBE_5S. |
| RES_AXIS | | | X | | x | x | | | | | x | X | | | | A RES_AXIS(rescale axis)is also a shared axis like COM_AXIS,the difference is that this kind of axis can be used for rescaling.Note that the RES_AXIS is by nature a CURVE which is used to implement a non linear scaling(rescale)of the axis.In addition to saving memory space via the shared usage like a COM_AXIS,it can compress a huge range to a non-linear distributed axis points thus retaining the required accuracy. |
| CURVE_AXIS | | | X | X | X | X | | | | | x | x | | | | CURVE_AXIS uses a separate CURVE to rescale the axis.The referenced CURVE is used to lookup an axis index,and the index value is used by the controller to determine the operating point in the CURVE,MAP,CUBOID,CUBE_4,or CUBE_5. |
| CURVE | | | X | X | X | X | | | | | X | X | | | | Calibration parameter with one input value and one output value.That means output values can be defined depending on the input value.The granularity of implemented functionality can be changed by using different number of axis points.A CURVE has always one input axis and one output axis.The output axis is a characteristic of the curve and every time present but the input axis can be defined within the curve definition or separately. |
| MAP | | | X | X | X | X | | | | | x | x | | | | Calibration parameter with two input values and one output value.That means output values can be defined depending on the input values.The granularity of implemented functionality can be changed by using different number of axis points for y-and x-axis.A MAP has always two input axes and one output axis.The output axis is a characteristic of the MAP and every time present but the input axes can be defined within the MAP definition or separately. |
| CUBOID | | | X | X | X | X | | | | | X | X | | | | Calibration parameter with three input values and one output value.That means output values can be defined depending on the input values.The granularity of implemented functionality can be changed by using different number of axis points for the input axes.A CUBOID has always three input axes and one output axis.The output axis is a characteristic of the CUBOID and every time present but the input axes can be defined within the CUBOID definition or separately. |
| CUBE_4 | | | X | X | X | X | | | | | x | x | | | | Calibration parameter with four input values and one output value.That means output values can be defined depending on the input values.The granularity of implemented functionality can be changed by using different number of axis points for the input axes.A CUBE_4 has always four input axes and one output axis.The output axis is a characteristic of the CUBE_4 and every time present but the input axes can be defined within the CUBE_4 definition or separately. |
| CUBE_5 | | | X | X | X | X | | | | | x | x | | | | Calibration parameter with five input values and one output value.That means output values can be defined depending on the input values.The granularity of implemented functionality can be changed by using different number of axis points for the input axes.A CUBE_5 has always five input axes and one output axis.The output axis is a characteristic of the CUBE_5 and every time present but the input axes can be defined within the CUBE_5 definition or separately. |
| MACRO | | | | | | | | | X | | |  | | x| x | This represents an argument to a C macro. |
------------------------->

[TPS_SWCT_01239] default value for attribute category used in the context of SwSystemconst (cid:100) The default value for the category of a SwSystemconst shall be VALUE. This has to be applied if no explicit definition of the category can be found. (cid:99)()

#@SECTION: 5.2.4 Application Data Type
#@CLASS: ApplicationArrayDataType
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: SwDataDefProps
#@CLASS: DataPrototype
[TPS_SWCT_01240] Subclasses of ApplicationDataType (cid:100) As figure 5.3 explains, the abstract meta-class ApplicationDataType is further derived into an ApplicationPrimitiveDataType and an ApplicationCompositeDataType which are further explained in the following sub-chapters. (cid:99)(RS_SWCT_03216)

Figure 5.3: Basic Meta-Model for ApplicationDataType
Table 5.8: Allowed Attributes vs. category for ApplicationDataTypes
<-------------- multimodal context 

| Attribute of **SwDataDefProps** | ApplicationDataType | ApplicationRecordElement | ApplicationArrayElement | VALUE | VAL_BLK | STRUCTURE | ARRAY | STRING | BOOLEAN | COM_AXIS | RES_AXIS | CURVE | MAP | CUBOID | CUBE_4 | CUBE_5 |
|--------------------------------|:-------------------:|:------------------------:|:-----------------------:|:-----:|:-------:|:---------:|:-----:|:------:|:-------:|:--------:|:--------:|:-----:|:---:|:------:|:------:|:------:|
| additionalNativeTypeQualifier |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| annotation | x | x | x | * | * | * | * | * | * | * | * | * | * | * | * | * |
| baseType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| compuMethod | x |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| dataConstr | x | x | x | 0..1 | 0..1 |  |  | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| displayFormat | x | x | x | 0..1 | 0..1 |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| implementationDataType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| invalidValue | x |  |  | 0..1 |  |  |  | 0..1 | 0..1 |  |  |  |  |  |  |  |
| stepSize | x | x | x | 0..1 | 0..1 |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swAddrMethod | x |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swAlignment |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swBitRepresentation |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swCalibrationAccess | x |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| swCalprmAxisSet | x |  |  |  |  |  |  |  |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| swComparisonVariable |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swDataDependency |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swHostVariable |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swImplPolicy | x |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swIntendedResolution | x | x | x | 0..1 |  |  |  |  |  |  |  |  |  |  |  |  |
| swInterpolationMethod | x |  |  | 0..1 |  |  |  |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swIsVirtual |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swPointerTargetProps |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swRecordLayout | x |  |  | 0..1 | 0..1（note） |  |  | 0..1 |  | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| swRefreshTiming | x |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 |  |  |  |  |  |  |  |
| swTextProps | x |  |  |  |  |  |  | 1 |  |  |  |  |  |  |  |  |
| swValueBlockSize | x |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |
| unit | x |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| valueAxisDataType | x |  |  |   |  0..1  |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| **Other attributes below the root element** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| element: ApplicationRecordElement | x | x | x |  |  | 1..* |  |  |  |  |  |  |  |  |  |  |
| element: ApplicationArrayElement | x | x | x |  |  |  | 1 |  |  |  |  |  |  |  |  |  |
| ApplicationArrayElemen.arraySizeSemantics | x |  |  |  |  |  | 0..1 |  |  |  |  |  |  |  |  |  |
| ApplicationArrayElement.maxNumberOfElements | x |  |  |  | |  | 1 |  |  |  |  |  |  |  |  |  |
note：This is required by [TPS_SWCT_01179].
----------------------------------------------->

This is required by [TPS_SWCT_01179].

Table 5.9: ApplicationPrimitiveDataType
Table 5.10: ApplicationCompositeDataType

[TPS_SWCT_01241] Applicable categorys for subclasses of ApplicationDataType (cid:100) Like any AutosarDataType, also the primitive and composite types on application level are characterized by their category and their SwDataDefProps. For a given category, only a limited set of attributes of the SwDataDefProps makes sense. (cid:99)(RS_SWCT_03216)

[constr_1007] Allowed attributes of SwDataDefProps for ApplicationDataTypes (cid:100) The allowed attributes of SwDataDefProps for ApplicationDataTypes and their allowed multiplicities are listed as an overview in table 5.8. (cid:99)()

This list makes use of the SwDataDefProps and other meta-model elements which are explained in detail in the further sections of this chapter.

[constr_1008] Applicability of categorys STRUCTURE and ARRAY (cid:100) The categories STRUCTURE and ARRAY correspond to ApplicationCompositeDataTypes whereas all other categorys can be applied only for ApplicationPrimitiveDataTypes. (cid:99)()

#@SECTION: 5.2.4.1 Application Primitive Data Types
#@SECTION: 5.2.4.1.1 Data Types for Single Values
#@CLASS: ApplicationDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: AutosarDataType
#@CLASS: BaseType
#@CLASS: CompuMethod
#@CLASS: DataConstr
#@CLASS: DataConstrRule
#@CLASS: ImplementationDataType
#@CLASS: Limit
#@CLASS: PhysConstrs
#@CLASS: SwDataDefProps
#@CLASS: Unit

In contrast to prior versions (R3.x) of the AUTOSAR standard, the primitive application data types on M2 level are no longer specified. Instead of this, the meta-class ApplicationPrimitiveDataType in combination with the attached swDataDefProps is used on the level of the M2 (meta-) model to specify the details on M1 modeling level.

[TPS_SWCT_01242] category characterizes the nature of a data type on application level (cid:100) The category is used in addition to characterize the nature of a data type on application level. (cid:99)(RS_SWCT_03216)

For example, the IntegerType as of AUTOSAR R3.x allows for specifying lower and upper ranges that constrain the applicable value interval. That aspect is still supported by this version of AUTOSAR, but the meta-model is different from the former approach. Especially it is no more considered of importance to specify that an ApplicationPrimitiveDataType is actually represented by “integer” numbers.

Figure 5.4 provides a sketch of how limits are defined now. The key feature is the aggregation of SwDataDefProps at AutosarDataType. The meta-class SwDataDefProps allows for creating a reference to a DataConstr that in turn aggregates a DataConstrRule. The latter aggregates PhysConstrs and this meta-class finally owns two Limits in the roles lowerLimit and upperLimit.

Figure 5.4: Specification of Physical Limits

Another example is shown in Figure 5.5. By making again use of SwDataDefProps, this figure shows how semantics in form of a CompuMethod and a Unit can be attached. Also an initValue can be defined which is used by the RTE in order to initialize values of DataPrototypes defined locally in a software-component.

Figure 5.5: Some Properties of ApplicationPrimitiveDataTypes

Figure 5.6 illustrates the relationship between the data constraints for ApplicationDataType, CompuMethod, ImplementationDataType, BaseType and also the invalidValue.

Figure 5.6: Value ranges and invalid values

[constr_2544] Limits need to be consistent (cid:100)
• The limits of ApplicationDataType shall be inside of the definition range of the CompuMethod
The CompuMethod needs to be applicable for limits of an ApplicationDataType. The reason is that the internal representation of the limits for the ApplicationDataType are calculated by applying the CompuMethod.
• The such defined internal limits of the ApplicationDataType shall be within or equal the internalConstrs of the mapped ImplementationDataType.
• The limits of the ImplementationDataType shall be within or equal to the limits defined by the size of the BaseType.
(cid:99)()

[constr_1281] invalidValue is inside the scope of the compuMethod (cid:100) If the value of the invalidValue of an ApplicationPrimitiveDataType of category VALUE is supposed to be inside the scope of the applicable CompuMethod an ApplicationValueSpecification is used to describe the invalidValue of the ApplicationPrimitiveDataType. (cid:99)()

[constr_1281] means that the value of the ApplicationValueSpecification shall be within the bounds defined by swDataDefProps.compuMethod.compuPhysToInternal.compuContent.compuScale.lowerLimit resp. upperLimit or the inverse case that is based on the bounds defined by swDataDefProps.compuMethod.compuInternalToPhys.compuContent.compuScale.lowerLimit resp. upperLimit.

[constr_1283] invalidValue is outside the scope of the compuMethod (cid:100) If the value of the invalidValue of an ApplicationPrimitiveDataType of category VALUE is supposed to be outside the scope of the applicable CompuMethod a NumericalValueSpecification shall be used to describe the invalidValue of the ApplicationPrimitiveDataType. (cid:99)()

The handling of invalidValue for ApplicationPrimitiveDataType of category STRING is defined by [constr_1242].

For a more detailed description of the properties that can be defined for data types (and data prototypes as well) see sections 5.4 and 5.4.2.

#@SECTION: 5.2.4.1.2 About Enumerations
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: CompuMethod
#@CLASS: ImplementationDataType
#@CLASS: SwDataDefProps
#@CLASS: ApplicationValueSpecification
#@CLASS: ApplicationRuleBasedValueSpecification
[TPS_SWCT_01243] Definition of enumeration types (cid:100) In the AUTOSAR meta model, an enumeration is not implemented by means of an ApplicationCompositeDataType. Instead, a range of integer numbers can be used as a structural description for a single ApplicationPrimitiveDataType or an ImplementationDataType of category VALUE or TYPE_REFERENCE that boils down to an ImplementationDataType of category VALUE. The mapping of the integer numbers to labels in the scope of the definition of an enumeration is considered part of the semantical definition via an attached CompuMethod rather than part of the structural description. (cid:99)(RS_SWCT_03216)

[TPS_SWCT_01562] Specification of values of an enumeration (cid:100) For the specification of values of an enumeration on the basis of the labels defined in the applicable CompuMethod it is necessary to distinguish two approaches based on the used AutosarDataType:
• ImplementationDataType: as mentioned by [constr_1225], the definition of the labels of an enumeration shall only be done by using TextValueSpecification.
• ApplicationPrimitiveDataType: use the ApplicationValueSpecification.swValueCont.swValuesPhys.vt or ApplicationRuleBasedValueSpecification.swValueCont.ruleBasedValues.arguments.vt. (cid:99)()

The relevant meta-classes in the context of SwDataDefProps are sketched in Figure 5.7. This includes all meta-classes that may contribute to the definition of the symbol of a CompuScale in C code, see [TPS_SWCT_01431].

Figure 5.7: Relevant meta-classes for the specification of enumerations

An example of how an enumeration looks like in ARXML is contained in section 5.5.1.3.

#@SECTION: 5.2.4.1.3 Data Types for Calibration Parameters
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationDataType
#@CLASS: AutosarDataType
#@CLASS: DataPrototype
#@CLASS: SwDataDefProps

[TPS_SWCT_01244] Data types for calibration parameters are also described as primitive types (cid:100) Data types for calibration parameters are from the application perspective also described as primitive types. This is obvious, if they are simple values (category VALUE). Also the category STRING is treated as a primitive type on application level.

Less obvious is the fact that ApplicationDataTypes of the categories VAL_BLK, COM_AXIS, RES_AXIS, CURVE, MAP, CUBOID, CUBE_4, and CUBE_5 are not described as composite data types (as far as the application level is concerned) although they admittedly possess some kind of internal structure.

In contrast to ApplicationCompositeDataTypes, they are not composed in a self similar way of other AutosarDataTypes. Their substructure needs a special description in oder to be compatible with existing calibration techniques. (cid:99)()

[TPS_SWCT_01245] SwDataDefProps control the structure of calibration parameters (cid:100) The substructure of these types is attached to the SwDataDefProps. By this means it is possible to define on the level of DataPrototypes or other artifacts, where the SwDataDefProps come into play. For details on these part of the SwDataDefProps see chapters 5.4.4 and 5.5.5. (cid:99)()

#@SECTION: 5.2.4.1.4 Data Types for Textual Strings
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationValueSpecification
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeElement
#@CLASS: SwBaseType
#@CLASS: SwDataDefProps
#@CLASS: SwRecordLayout
#@CLASS: SwRecordLayoutGroup
#@CLASS: SwRecordLayoutV
#@CLASS: SwTextProps
#@CLASS: DataTypeMap
#@CLASS: DataTypeMappingSet


[constr_1093]Definition of textual strings (cid:100) An ApplicationPrimitiveDataType[constr_1093] Definition of DataType of category STRING shall have a swTextProps which determines the arraySizeSemantics and swMaxTextSize. (cid:99)()

[TPS_SWCT_01488] ApplicationPrimitiveDataType shall be interpreted as a string of a particular encoding (cid:100) To indicate that an ApplicationPrimitiveDataType shall be interpreted as a string of a particular encoding it shall reference swDataDefProps.swTextProps.baseType and the only attribute of the referenced SwBaseType relevant for this purpose is the BaseTypeDirectDefinition.baseTypeEncoding. (cid:99)()

Figure 5.8: Specification of textual strings
Table 5.11: SwTextProps

[TPS_SWCT_01127] Byte array with variable size (cid:100) SwTextProps can be used to define byte arrays of variable size. (cid:99)(RS_SWCT_03182, RS_SWCT_03181)

[TPS_SWCT_01246] SwRecordLayout may also be required for A2L generation (cid:100) A SwRecordLayout may also be required for the generation of A2L if the string is part of calibration data. (cid:99)()

As stated by [TPS_SWCT_01128], the definition of SwDataDefProps.swRecordLayout is considered mandatory anyway for ApplicationPrimitiveDataTypes of category STRING.

The following series of XML fragments exemplifies the definition of a data type for the representation of a textual string. First, the applicable ApplicationPrimitiveDataType is defined (see Figure 5.8):

Listing 5.1: Example for the definition of a string ApplicationPrimitiveDataType
<AR-PACKAGE>
<SHORT-NAME>ApplicationDataTypes</SHORT-NAME>
<ELEMENTS>
<APPLICATION-PRIMITIVE-DATA-TYPE>
<SHORT-NAME>MyApplicationStringType</SHORT-NAME>
<CATEGORY>STRING</CATEGORY>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<SW-TEXT-PROPS>
<ARRAY-SIZE-SEMANTICS>VARIABLE-SIZE</ARRAY-SIZE-SEMANTICS>
<SW-MAX-TEXT-SIZE>50</SW-MAX-TEXT-SIZE>
<BASE-TYPE-REF DEST="SW-BASE-TYPE" BASE="default">BaseTypes/MyTextBaseType</BASE-TYPE-REF>
</SW-TEXT-PROPS>
<INVALID-VALUE>
<APPLICATION-VALUE-SPECIFICATION>
<CATEGORY>STRING</CATEGORY>
<SW-VALUE-CONT>
<SW-VALUES-PHYS>
<VT>inv</VT>
</SW-VALUES-PHYS>
</SW-VALUE-CONT>
</APPLICATION-VALUE-SPECIFICATION>
</INVALID-VALUE>
<SW-RECORD-LAYOUT-REF DEST="SW-RECORD-LAYOUT" BASE="default">RecordLayouts/StringDescriptor</SW-RECORD-LAYOUT-REF>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</APPLICATION-PRIMITIVE-DATA-TYPE>
</ELEMENTS>
</AR-PACKAGE>

Note that the category is set to the value STRING. Also the ApplicationPrimitiveDataType.swDataDefProps.swTextProps indicate the width of the string and also define (by means of the reference to baseType) the encoding this string data type is supposed to utilize.

Note further that the fact that an ApplicationDataType directly references (across the implementation level) to a SwBaseType represents an exception to the rule that ApplicationDataType should not be concerned about the lowest level of data type definition in AUTOSAR.
If the bridging of the implementation level were accepted as a general pattern for the
modeling of ApplicationDataType it would easily be possible to bypass the implementation level to some extent and this would render ApplicationDataTypes less
versatile.
[TPS_SWCT_01128] SwRecordLayout needed for ApplicationPrimitiveDataType of category STRING (cid:100) As mentioned in [TPS_SWCT_01179], an ApplicationPrimitiveDataType of category STRING is considered a Compound Primitive Data Type. Therefore, it needs a reference to the definition of a SwRecordLayout that presets the approach for creating a matching ImplementationDataType. (cid:99)()

In this specific example the definition of the SwRecordLayout foresees the ApplicationPrimitiveDataType of category STRING to be implemented as a structured data type that consists of:
1. the size of an instance of the string data type in terms of the number of characters plus
2. an array that can be used to store the individual characters contained in an instance of the string data type.

Depending on the used encoding the array may need to be bigger (in terms of the
number of elements) than the corresponding value of the size. Furthermore, the definition of the SwRecordLayout already takes into account that the implementation of an array data type by means of an ImplementationDataType requires the definition of an ImplementationDataTypeElement.

The meaning of the standardized values of SwRecordLayoutV.swRecordLayoutVProp are documented in [TPS_SWCT_01489]. In the scope of this example the values COUNT and VALUE are used.

The fact that the swRecordLayoutGroupTo contains the value -1 means that the
iteration ends at the last element of the array.

Listing 5.2: Example for the definition of a SwRecordLayout for an ApplicationPrimitiveDataType of category STRING
<AR-PACKAGE>
<SHORT-NAME>RecordLayouts</SHORT-NAME>
<ELEMENTS>
<SW-RECORD-LAYOUT>
<SHORT-NAME>StringDescriptor</SHORT-NAME>
<LONG-NAME>
<L-4 L="EN">String by descriptor</L-4>
</LONG-NAME>
<INTRODUCTION>
<VERBATIM>
<L-5 L="EN" xml:space="default">
struct{
size,
char[]
}
</L-5>
</VERBATIM>
</INTRODUCTION>
<SW-RECORD-LAYOUT-GROUP>
<SW-RECORD-LAYOUT-V>
<SHORT-LABEL>size</SHORT-LABEL>
<SW-RECORD-LAYOUT-V-AXIS>STRING</SW-RECORD-LAYOUT-V-AXIS>
<SW-RECORD-LAYOUT-V-PROP>COUNT</SW-RECORD-LAYOUT-V-PROP>
</SW-RECORD-LAYOUT-V>
<SW-RECORD-LAYOUT-GROUP>
<SHORT-LABEL>chars</SHORT-LABEL>
<SW-RECORD-LAYOUT-GROUP-AXIS>STRING</SW-RECORD-LAYOUT-GROUP-AXIS>
<SW-RECORD-LAYOUT-GROUP-FROM>0</SW-RECORD-LAYOUT-GROUP-FROM>
<SW-RECORD-LAYOUT-GROUP-TO>-1</SW-RECORD-LAYOUT-GROUP-TO>
<SW-RECORD-LAYOUT-V>
<SHORT-LABEL>char</SHORT-LABEL>
<SW-RECORD-LAYOUT-V-PROP>VALUE</SW-RECORD-LAYOUT-V-PROP>
</SW-RECORD-LAYOUT-V>
</SW-RECORD-LAYOUT-GROUP>
</SW-RECORD-LAYOUT-GROUP>
</SW-RECORD-LAYOUT>
</ELEMENTS>
</AR-PACKAGE>

Please note further that the discussed example of an ApplicationPrimitiveDataType of category STRING also contains the definition of an invalidValue for the string data type.
The next step is the definition of an ImplementationDataType that represents the
string type on the implementation level. The definition of the ImplementationDataType can be derived from the definition of the applicable SwRecordLayout.
Please note that the ImplementationDataType also defines an invalidValue. As mentioned in [TPS_SWCT_01487], the consistency of the invalidValue defined in the scope of the ApplicationPrimitiveDataType of category STRING and the invalidValue defined in the scope of the corresponding ImplementationDataType cannot formally be checked.


Listing 5.3: Example for the definition of a string ImplementationDataType
<AR-PACKAGE>
<SHORT-NAME>ImplementationDataTypes</SHORT-NAME>
<ELEMENTS>
<IMPLEMENTATION-DATA-TYPE>
<SHORT-NAME>uint8</SHORT-NAME>
<CATEGORY>VALUE</CATEGORY>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<BASE-TYPE-REF DEST="SW-BASE-TYPE">BaseTypes/uint8BaseType</BASE-TYPE-REF>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</IMPLEMENTATION-DATA-TYPE>
<IMPLEMENTATION-DATA-TYPE>
<SHORT-NAME>MyImplementationStringType</SHORT-NAME>
<CATEGORY>STRUCTURE</CATEGORY>
<SUB-ELEMENTS>
<IMPLEMENTATION-DATA-TYPE-ELEMENT>
<SHORT-NAME>size</SHORT-NAME>
<CATEGORY>TYPE_REFERENCE</CATEGORY>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<IMPLEMENTATION-DATA-TYPE-REF DEST="IMPLEMENTATION-DATA-TYPE">ImplementationDataTypes/uint8</IMPLEMENTATION-DATA-TYPE-REF>
<INVALID-VALUE>
<NUMERICAL-VALUE-SPECIFICATION>
<VALUE>-1</VALUE>
</NUMERICAL-VALUE-SPECIFICATION>
</INVALID-VALUE>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</IMPLEMENTATION-DATA-TYPE-ELEMENT>
<IMPLEMENTATION-DATA-TYPE-ELEMENT>
<SHORT-NAME>string</SHORT-NAME>
<CATEGORY>ARRAY</CATEGORY>
<SUB-ELEMENTS>
<IMPLEMENTATION-DATA-TYPE-ELEMENT>
<SHORT-NAME>character</SHORT-NAME>
<CATEGORY>TYPE_REFERENCE</CATEGORY>
<ARRAY-SIZE>50</ARRAY-SIZE>
<ARRAY-SIZE-SEMANTICS>FIXED-SIZE</ARRAY-SIZE-SEMANTICS>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<IMPLEMENTATION-DATA-TYPE-REF DEST="IMPLEMENTATION-DATA-TYPE">ImplementationDataTypes/uint8</IMPLEMENTATION-DATA-TYPE-REF>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</IMPLEMENTATION-DATA-TYPE-ELEMENT>
</SUB-ELEMENTS>
</IMPLEMENTATION-DATA-TYPE-ELEMENT>
</SUB-ELEMENTS>
</IMPLEMENTATION-DATA-TYPE>
</ELEMENTS>
</AR-PACKAGE>

The interesting part about this definition is the fact that on the implementation level, it
was (driven by the definition of the SwRecordLayout) decided to implement the string
as a structure of a size element (that goes by the shortName “size”) and a value
element (that goes by the shortName “string”) which in turn is defined as an array
data type and therefore has a sub-element that goes by the shortName “character”.
The latter references (in the role swDataDefProps.implementationDataType)
the Platform Data Type “uint8” (that, according to the rules of Platform Data
Types, is realized by an ImplementationDataType “uint8”).
Please note that the ApplicationPrimitiveDataType named “MyApplicationStringType” references the SwBaseType named “MyTextBaseType” which is defined
in the following XML fragment:

Listing 5.4: Example for the definition of a string SwBaseType
<AR-PACKAGE>
<SHORT-NAME>BaseTypes</SHORT-NAME>
<ELEMENTS>
<SW-BASE-TYPE>
<SHORT-NAME>MyTextBaseType</SHORT-NAME>
<BASE-TYPE-SIZE>8</BASE-TYPE-SIZE>
<BASE-TYPE-ENCODING>UTF-8</BASE-TYPE-ENCODING>
</SW-BASE-TYPE>
<SW-BASE-TYPE>
<SHORT-NAME>uint8BaseType</SHORT-NAME>
<BASE-TYPE-SIZE>8</BASE-TYPE-SIZE>
</SW-BASE-TYPE>
</ELEMENTS>
</AR-PACKAGE>

The contribution of this definition of SwBaseType to the overall definition of a string
data type is represented by the definition of the encoding (which is set to UTF-8). However, there ist still one important part missing, i.e. the definition of the mapping of ApplicationPrimitiveDataType to ImplementationDataType (and vice versa):

Listing 5.5: Example for the definition of the applicable DataTypeMappingSet
<AR-PACKAGE>
<SHORT-NAME>DataTypeMappingSets</SHORT-NAME>
<ELEMENTS>
<DATA-TYPE-MAPPING-SET>
<SHORT-NAME>theExample</SHORT-NAME>
<DATA-TYPE-MAPS>
<DATA-TYPE-MAP>
<APPLICATION-DATA-TYPE-REF DEST="APPLICATION-PRIMITIVE-DATA-TYPE" BASE="default">ApplicationDataTypes/MyApplicationStringType</APPLICATION-DATA-TYPE-REF>
<IMPLEMENTATION-DATA-TYPE-REF DEST="IMPLEMENTATION-DATA-TYPE" BASE="default">ImplementationDataTypes/MyImplementationStringType</IMPLEMENTATION-DATA-TYPE-REF>
</DATA-TYPE-MAP>
</DATA-TYPE-MAPS>
</DATA-TYPE-MAPPING-SET>
</ELEMENTS>
</AR-PACKAGE>
As mentioned before, the definition of an ImplementationDataType that corresponds to an ApplicationPrimitiveDataType of category STRING can be
to some extent derived from the ApplicationPrimitiveDataType.swDataDefProps.swRecordLayout.

[TPS_SWCT_01570] DataTypeMap is mandatory in the presence of ApplicationPrimitiveDataType.swDataDefProps.swRecordLayout (cid:100) The definition of a DataTypeMap is mandatory even if an ImplementationDataType has been derived from an ApplicationPrimitiveDataType that defines a SwRecordLayout. (cid:99)()

One motivation for the existence of [TPS_SWCT_01570] is that the integrator of an
AUTOSAR ECU may rightfully decide to take a different ImplementationDataType
other than the one that has been generated on the basis of the SwRecordLayout.

#@SECTION: 5.2.4.2 Application Composite Data Types
#@CLASS: ApplicationArrayDataType
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: ApplicationRecordElement

[TPS_SWCT_01247] ApplicationArrayDataType and ApplicationRecordDataType (cid:100) The meta-classes ApplicationArrayDataType and ApplicationRecordDataType (details are depicted in Figure 5.9) provide the means to define composite data types.

Such a composite data type is required if the application software wants to have access to the individual elements of the composite as well as to do operations with the whole composite, e.g. wants to communicate the complete record or array in a single transaction.

It is possible to use a combination of ApplicationArrayDataType and ApplicationRecordDataType, so that an ApplicationArrayDataType could be defined as ApplicationRecordElement of a ApplicationRecordDataType and in the same manner a ApplicationRecordDataType could be used as the base type of an ApplicationArrayDataType. The creation of nested ApplicationCompositeDataTypes is also possible. (cid:99)

Figure 5.9: Summary of ApplicationCompositeDataType

#@SECTION: 5.2.4.2.1 ApplicationArrayDataType
#@CLASS: ApplicationArrayDataType
#@CLASS: ApplicationArrayElement
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ApplicationDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: ApplicationRecordElement
#@ENUM: ArraySizeHandlingEnum
#@ENUM: ArraySizeSemanticsEnum
#@CLASS: AutosarDataType
#@CLASS: DataPrototype
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeElement
#@CLASS: SwSystemconst

[TPS_SWCT_01078] Configurable array size (cid:100) An ApplicationArrayDataType may contain maxNumberOfElements ApplicationArrayElements. Each of these ApplicationArrayElements has the same data type. When referring to an element of an ApplicationArrayDataType within a software component description, the element-index runs from 0 to the value of maxNumberOfElements-1. (cid:99)(RS_SWCT_03144)

This applies although the multiplicity in the meta-model is 1. In fact, it would be possible to model ApplicationArrayDataType without ApplicationArrayElement. The latter exists only so that it can be the target of a reference within an AUTOSAR XML file.

Table 5.12: ApplicationArrayDataType

Table 5.13: ApplicationArrayElement

Please note that the information about the number of elements of a specific ApplicationArrayDataType is not absolute but allows for further interpretation.

[TPS_SWCT_01076] Number of elements of a specific ApplicationArrayDataType might vary at run-time (cid:100) That is, there are cases where the number of elements of a specific ApplicationArrayDataType might vary at run-time. To be precise, the number of elements might vary between 0 and the value denoted by maxNumberOfElements. For this purpose an additional attribute arraySizeSemantics is available that can be used to clarify the meaning of maxNumberOfElements.
For clarification, it might indeed happen that the actual number of elements in a specific ApplicationArrayDataType yields 0 simply because the respective DataPrototype is part of a higher-level protocol where under certain circumstances the DataPrototype of ApplicationArrayDataType is simply not required for expressing a given semantics. (cid:99)(RS_SWCT_03180, RS_SWCT_03181, RS_SWCT_03144)

Table 5.14: ArraySizeSemanticsEnum

Please note that the ability to define the semantic meaning of maxNumberOfElements is not only limited to the application data type level. The same approach also applies for ImplementationDataType.

[constr_1152] category of ApplicationArrayElement and AutosarDataType referenced in the role type shall be kept in sync (cid:100) The value of category of an ApplicationArrayElement shall always be identical to the value of category of the AutosarDataType referenced by the ApplicationArrayElement. (cid:99)()

[TPS_SWCT_01601] Size Indicator shall be updated by software-component (cid:100) If a software-component changes the number of valid elements in a variable size array, it shall also update the Size Indicator in the ImplementationDataType. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01602] Size Indicator shall be read by the software-component (cid:100) If a software-component receives a variable size array, it shall use the Size Indicator in the ImplementationDataType to determine the number of valid elements in the array. (cid:99)(RS_SWCT_03181)

Table 5.15: ArraySizeHandlingEnum

[TPS_SWCT_01604] Enable Size Indicator (cid:100) To enable the RTE's ability to consider the number of valid elements inside a Variable-Size Array Data Type the ApplicationArrayDataType.dynamicArraySizeProfile of ApplicationArrayDataType and ApplicationArrayElement.arraySizeHandling shall be set. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01605] Semantics of ApplicationArrayElement.arraySizeHandling (cid:100) The attribute ApplicationArrayElement.arraySizeHandling specifies how the size is determined in case of multi-dimensional variable size array. (cid:99)(RS_SWCT_03181)

This allows to specify coherencies between the sizes of the nested variable size arrays in case of multiple dimensions. With a suitable ImplementationDataType, it is possible to enable other software components, RTE, and other BSW modules to make use of the Size Indicator and only transfer the valid data elements from the sender to the receiver.

[TPS_SWCT_01606] Internal structure of mapped ImplementationDataType (cid:100) The attribute dynamicArraySizeProfile specifies which internal structure the ImplementationDataType that is mapped to the ApplicationDataType shall follow. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01607] Profiles for internal structure of mapped ImplementationDataType (cid:100) For the structure of the ImplementationDataType that is mapped to the ApplicationDataType the following profiles are defined for dynamicArraySizeProfile: VSA_LINEAR, VSA_SQUARE, VSA_RECTANGULAR, and VSA_FULLY_FLEXIBLE. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01608] Custom profiles for internal structure of mapped ImplementationDataType (cid:100) Custom profiles can be added to dynamicArraySizeProfile. They shall have a company-specific prefix. (cid:99)(RS_SWCT_03181)

As it is a general rule for the definition of custom profiles or values of category, the custom value should start with a company-specific prefix in order to avoid clashes with later extensions of the AUTOSAR standard.

dynamicArraySizeProfile is used to specify how the number of elements of the multiple dimensions of a variable size array correlate. They could be totally independent (VSA_FULLY_FLEXIBLE) on the one hand or each dimension has the same number of valid elements (VSA_SQUARE).

[TPS_SWCT_01623] Justification for the existence of attributes ApplicationArrayDataType.dynamicArraySizeProfile and ApplicationArrayElement.arraySizeHandling (cid:100) At the first glance, the two attributes ApplicationArrayDataType.dynamicArraySizeProfile and ApplicationArrayElement.arraySizeHandling seem equivalent. However, both are needed because they have to be used if multi dimensional variable size arrays have to be described. In this case, multiple combinations of sizes could occur which cannot be specified beforehand. (cid:99)(RS_SWCT_03181)

The ImplementationDataType has to follow certain rules depending on the chosen profile. See chapter 5.2.5 for details.

[constr_1314] Profile VSA_LINEAR for ApplicationArrayDataType (cid:100) If the dynamicArraySizeProfile of ApplicationArrayDataType is set to VSA_LINEAR, the contained ApplicationArrayElement shall fulfill all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
• The ApplicationArrayElement shall be typed by an ApplicationDataType that is not an ApplicationArrayDataType where the attribute dynamicArraySizeProfile exists. (cid:99)()

The part of that demands that the ApplicationArrayElement shall be typed by an ApplicationDataType that is not an ApplicationArrayDataType where the attribute dynamicArraySizeProfile exists basically boils down to the simple explanation that the "leaf" data type of the Variable-Size Array Data Type can be anything but a Variable-Size Array Data Type.

[constr_1315] Profile VSA_SQUARE for ApplicationArrayDataType (cid:100) If the dynamicArraySizeProfile of ApplicationArrayDataType is set to VSA_SQUARE, the contained ApplicationArrayElement shall fulfill all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall not be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value inheritedFromArrayElementTypeSize.
• The ApplicationArrayElement shall be typed by an ApplicationArrayDataType.

The referred ApplicationArrayDataType shall refer over a chain (under consideration of the number of dimensions of the "root" ApplicationArrayDataType) of nested ApplicationArrayDataTypes with ApplicationArrayElements to an ApplicationDataType that is not an ApplicationArrayDataType where the attribute dynamicArraySizeProfile exists.

The last ApplicationArrayDataType in that chain shall have an ApplicationArrayElement that fulfills all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling set to the value allIndicesSameArraySize.

All ApplicationArrayDataTypes before shall have an ApplicationArrayElement that fulfills all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall not be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value inheritedFromArrayElementTypeSize.
• The ApplicationArrayElement shall be typed by an ApplicationArrayDataType. (cid:99)()

The part of [constr_1315], [constr_1316], and [constr_1317] that demands that the referred ApplicationArrayDataType shall refer over a chain (under consideration
of the number of dimensions of the “root” ApplicationArrayDataType) of nested
ApplicationArrayDataTypes with ApplicationArrayElements to an ApplicationDataType that is not an ApplicationArrayDataType where the attribute
dynamicArraySizeProfile exists basically boils down to the simple explanation
that the “leaf” data type of the Variable-Size Array Data Type can be anything
but a Variable-Size Array Data Type.

[constr_1316] Profile VSA_RECTANGULAR for ApplicationArrayDataType (cid:100) If the dynamicArraySizeProfile of ApplicationArrayDataType is set to VSA_RECTANGULAR the contained ApplicationArrayElement shall fulfill all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
• The ApplicationArrayElement shall be typed by an ApplicationArrayDataType.

The referred ApplicationArrayDataType shall refer over a chain (under consideration of the number of dimensions of the "root" ApplicationArrayDataType) of nested ApplicationArrayDataTypes with ApplicationArrayElements to an ApplicationDataType that is not an ApplicationArrayDataType where the attribute dynamicArraySizeProfile exists.

The last ApplicationArrayDataType in that chain shall have an ApplicationArrayElement that fulfills all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.

All ApplicationArrayDataTypes before shall have an ApplicationArrayElement that fulfills all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall set to the value variableSize
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
• The ApplicationArrayElement shall be typed by an ApplicationArrayDataType. (cid:99)()

[constr_1317] Profile VSA_FULLY_FLEXIBLE for ApplicationArrayDataType (cid:100) If the dynamicArraySizeProfile of ApplicationArrayDataType is set to VSA_FULLY_FLEXIBLE, the contained ApplicationArrayElement shall fulfill all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesDifferentArraySize.
• The ApplicationArrayElement shall be typed by an ApplicationArrayDataType.

The referred ApplicationArrayDataType shall refer over a chain (under consideration of the number of dimensions of the "root" ApplicationArrayDataType) of nested ApplicationArrayDataTypes with ApplicationArrayElements to an ApplicationDataType that is not an ApplicationArrayDataType where the attribute dynamicArraySizeProfile exist.

The last ApplicationArrayDataType in that chain shall have an ApplicationArrayElement that fulfills all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.

All ApplicationArrayDataTypes before shall have an ApplicationArrayElement that fulfills all of the following conditions:
• The attribute ApplicationArrayElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ApplicationArrayElement.maxNumberOfElements shall be defined.
• The attribute ApplicationArrayElement.arraySizeHandling shall be set to the value allIndicesDifferentArraySize.
• The ApplicationArrayElement shall be typed by an ApplicationArrayDataType. (cid:99)()

For examples see Appendix E.1.

[TPS_SWCT_01256] Definition of multi-dimensional array data types (cid:100) In order to describe multi dimensional arrays an ApplicationArrayElement references again another ApplicationArrayDataType. Hereby, one ApplicationArrayDataType per dimension is required.

This multiple dimensions do have a well-defined correlation to the individual dimensions of an ImplementationDataType of category ARRAY when the ApplicationArrayDataType is mapped to an ImplementationDataType as described in section 5.2.2

The ApplicationArrayElements are mapping in the order of the ApplicationArrayElement to ApplicationArrayDataType references to ImplementationDataTypeElements in the order of first ImplementationDataTypeElement of the ImplementationDataType to leaf ImplementationDataTypeElement.

In other words the ApplicationArrayElement of the top level ApplicationArrayDataType relates to the first ImplementationDataTypeElement of the ImplementationDataType. The ApplicationArrayElement of the referenced ApplicationArrayDataTypes relates to the sub ImplementationDataTypeElements in the order of the ApplicationArrayElement -> ApplicationArrayDataType references. (cid:99)(RS_SWCT_03216)

Figure 5.10: Example of a three dimensional array type

Figure 5.10 shows a three dimensional array described with a set of ApplicationArrayDataTypes on the left hand side. The array element is typed by an ApplicationPrimitiveDataType of category BOOLEAN. On the right hand side the implementation of the three dimensional array is described with an ImplementationDataType which contains three nested ImplementationDataTypeElements.

Matching ApplicationArrayElements and ImplementationDataTypeElements are shown on the same layer. For the sake of clarity correlating maxNumberOfElements and arraySize attributes are described with the identical instance of a SwSystemconst instead of a value. Further details of variant rich M1 models are not in the scope of this example.

The data type of the array element is described by the ApplicationArrayDataType with the means of a ApplicationPrimitiveDataType of category BOOLEAN. In order to fulfill [constr_1152] the category of ApplicationArrayElement "Dim3" is set to BOOLEAN. This ApplicationPrimitiveDataType "BOOLEAN" correlates to the ImplementationDataType "boolean" of category VALUE which is typically the boolean type of the AUTOSAR Platform Types. Please note here [constr_1063].

#@SECTION: 5.2.4.2.2 ApplicationRecordDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: ApplicationRecordElement

[TPS_SWCT_01249] ApplicationRecordDataType (cid:100) A declaration of ApplicationRecordDataType describes a non-empty set of objects, each of which has a unique identiﬁer with respect to the ApplicationRecordDataType and each has an own ApplicationDataType. The shortName of each ApplicationRecordElement within the scope of an ApplicationRecordDataType shall be unique. (cid:99)(RS_SWCT_03216)

Table 5.16: ApplicationRecordDataType
Table 5.17: ApplicationRecordElement

#@SECTION: 5.2.5 Implementation Data Type
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeElement
#@CLASS: SwPointerTargetProps
#@CLASS: ImplementationProps
#@CLASS: SymbolProps
#@CLASS: SwDataDefProps
#@CLASS: SwBaseType
#@CLASS: BswModuleEntry
#@CLASS: ImplementationProps
#@CLASS: SymbolProps
#@CLASS: SwDataDefProps
#@CLASS: AutosarDataType
#@CLASS: CompuMethod
#@CLASS: DataConstr

[TPS_SWCT_01250] ImplementationDataType has been introduced to optimize the formal support for data type handling on the implementation level (cid:100) The concept of an ImplementationDataType has been introduced to optimize the formal support for data type handling on the implementation level.

That is, an ImplementationDataType conceptually corresponds to the level of (C) source code. For example, ImplementationDataTypes have a direct impact on the contract (please find an explanation of this term in [2]) of a software-component and the RTE. (cid:99)(RS_SWCT_03217)

There is a use case for the definition of an invalidValue for category ARRAY and therefore category STRUCTURE is also supported for the sake of symmetry.
This represents an exception such that it would make sense to use an entire ArrayValueSpecification as the invalidValue because a string semantically is more than just a bunch of characters in a row.


Table 5.18: Allowed Attributes vs. category for ImplementationDataType
<-------------- multimodal context 


| Attributes | Root Element |  |  |  | Attribute Existence per Category |  |  |  |  |  |  |
|------------|--------------|--|--|--|------------------|-----------------|-------------------|-----------------|-----------|-------|-------|
|  | ImplementationDataType | ImplementationDataTypeElement | SwPointerTargetProps | SwServiceArg | VALUE | DATA REFERENCE | FUNCTION REFERENCE | TYPE_REFERENCE | STRUCTURE | UNION | ARRAY |
| additionalNativeTypeQualifier | X | X | X | X | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| annotation | X | X | X | X | * | * | * | * | * | * | * |
| baseType | X | X | X | X | 1 |  |  |  |  |  |  |
| compuMethod | X | X | X | X | 0..1 |  |  | 0..1 |  |  |  |
| dataConstr | X | X | X | X | 0..1 |  |  | 0..1 |  |  |  |
| displayFormat | X | X |  |  | 0..1 |  |  |  | 0..1 | 0..1 | 0..1 |
| implementationDataType | X | X | X | X |  |  |  | 1 |  |  |  |
| invalidValue | X | X | X |  | 0..1 |  |  | 0..1 | 0..1(note1) |  | 0..1(note2) |
| stepSize | X | X |  |  | 0..1 |  |  |  |  |  |  |
| swAddrMethod | X | X | X |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swAlignment | X |  |  |  | 0..1 | 0..1 | 0..1 |  | 0..1 | 0..1 | 0..1 |
| swBitRepresentation |  |  |  |  |  |  |  |  |  |  |  |
| swCalibrationAccess | X | X |  |  | 0..1 |  |  |  | 0..1 | 0..1 | 0..1 |
| swCalprmAxisSet |  |  |  |  |  |  |  |  |  |  |  |
| swComparisonVariable |  |  |  |  |  |  |  |  |  |  |  |
| swDataDependency |  |  |  |  |  |  |  |  |  |  |  |
| swHostVariable |  |  |  |  |  |  |  |  |  |  |  |
| swImplPolicy | X |  | X | X | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swIntendedResolution |  |  |  |  |  |  |  |  |  |  |  |
| swInterpolationMethod |  |  |  |  |  |  |  |  |  |  |  |
| swIsVirtual |  |  |  |  |  |  |  |  |  |  |  |
| swPointerTargetProps | X | X | X | X |  | 1 | 1 |  |  |  |  |
| swPointerTargetProps.swDataDefProps | X | X | X | X |  | 1 |  |  |  |  |  |
| swPointerTargetProps.functionPointerSignature | X | X | X | X |  |  | 1 |  |  |  |  |
| swRecordLayout |  |  |  |  |  |  |  |  |  |  |  |
| swRefreshTiming | X | X | X | X | 0..1 |  |  |  | 0..1 | 0..1 | 0..1 |
| swTextProps |  |  |  |  |  |  |  |  |  |  |  |
| swValueBlockSize |  |  |  |  |  |  |  |  |  |  |  |
| unit |  |  |  |  |  |  |  |  |  |  |  |
| valueAxisDataType |  |  |  |  |  |  |  |  |  |  |  |
### Other Attributes
| subElement: ImplementationDataTypeElement | X | X |  |  |  |  |  |  | 1..* | 1..* | 1 |
| subElement.arraySizeSemantics | X | X |  |  |  |  |  |  |  |  | 0..1 |
| subElement.arraySize | X | X |  |  |  |  |  |  |  |  | 1 |
note1:There is a use case for the definition of an invalidValue for category ARRAY and therefore category STRUCTURE is also supported for the sake of symmetry.
note2:This represents an exception such that it would make sense to use an entire ArrayValueSpecification as the invalidValue because a string semantically is more than just a bunch of characters in a row.
--------------------------->
[TPS_SWCT_01251] Limited set of values for category are applicable for ImplementationDataType (cid:100) Like any AutosarDataType, also the data types on implementation level are characterized by its category and its SwDataDefProps. For a given category, only a limited set of attributes of the SwDataDefProps makes sense. (cid:99)(RS_SWCT_03217)

[constr_1009] SwDataDefProps applicable to ImplementationDataTypes (cid:100) A complete list of the SwDataDefProps and other attributes and their multiplicities which are allowed for a given category is shown in table 5.18. (cid:99)()

This list makes use of the SwDataDefProps and other meta-model elements which are explained in detail in the further sections of this chapter.

[constr_1158] Applicable categorys for attribute ImplementationDataType.swDataDefProps.compuMethod (cid:100) The definition of the reference ImplementationDataType.swDataDefProps.compuMethod is restricted to a CompuMethod of either category BITFIELD_TEXTTABLE or category TEXTTABLE (these might be seen as implementation specific in certain cases). (cid:99)()

[constr_1383] Existence of CompuMethod and DataConstr for ImplementationDataTypes of category TYPE_REFERENCE (cid:100) The existence of ImplementationDataType.swDataDefProps.compuMethod and ImplementationDataType.swDataDefProps.dataConstr for ImplementationDataTypes of category TYPE_REFERENCE is only allowed if the respective ImplementationDataType, after all type references are resolved, ends up in an ImplementationDataType of category VALUE. (cid:99)()

Please note that, as a consequence of the existence of [constr_1383], it is possible that the elements of a composite ImplementationDataType define individual CompuMethods. However, the definition of one CompuMethod that applies to the entire composite ImplementationDataType is not supported.

[TPS_SWCT_01252] ImplementationDataType can express concepts not available on application level (cid:100) As a consequence of the specific focus, it is possible to express concepts with an ImplementationDataType that are not supported on the application level, i.e. by ApplicationDataType:

• ImplementationDataType supports the definition of pointers
• It is possible to define "alias" names just as in a typedef
• It is possible to define nested ImplementationDataTypes but in contrast to the concept implemented for ApplicationDataType these implement a direct aggregation of sub-elements rather than applying the type-prototype pattern.

(cid:99)(RS_SWCT_03217)

The general structure of ImplementationDataType is sketched in Figure 5.11. If a specific ImplementationDataType is supposed to define a composite data type the ImplementationDataType aggregates ImplementationDataTypeElements.

Figure 5.11: ImplementationDataType overview

Table 5.19: ImplementationDataType

[TPS_SWCT_01253] Rules apply for the usage of the attribute ImplementationDataType.typeEmitter (cid:100) The following set of rules applies for the usage of the attribute ImplementationDataType.typeEmitter:

• If the value of attribute typeEmitter is NOT defined and a nativeDeclaration is provided the RTE generator shall generate the corresponding data type definition7.
• If the value of attribute typeEmitter is set to "RTE" and a nativeDeclaration is provided the RTE generator shall generate the corresponding data type definition.
• If the value of the attribute typeEmitter is set to "RTE" and no nativeDeclaration is provided the RTE generator shall issue an error message.
• If the value of attribute typeEmitter is set to anything else but "RTE" the RTE generator shall silently not generate the corresponding data type definition regardless of the existence of nativeDeclaration attribute.

(cid:99)(RS_SWCT_03217)

Note that the rules listed above imply that the allowed values of the attribute typeEmitter are not constrained with the singular exception that the definition of the behavior in case of "RTE" is claimed by AUTOSAR. Other values can be provided; the consequences of this provision are implementation-dependent and outside the scope of the definition of the AUTOSAR standard.

[TPS_SWCT_01248] Nested definition of ImplementationDataType (cid:100) If an ImplementationDataTypeElement also represents a composite data type it can aggregate ImplementationDataTypeElements in the role of subElement. Again, the type-prototype pattern does not apply in this case. (cid:99)(RS_SWCT_03217)

[constr_1106] Structure shall have at least one element (cid:100) An ImplementationDataType or ImplementationDataTypeElement of category STRUCTURE shall own at least one ImplementationDataTypeElement. (cid:99)()

[constr_1107] Union shall have at least one element (cid:100) An ImplementationDataType or ImplementationDataTypeElement of category UNION shall own at least one ImplementationDataTypeElement. (cid:99)()

Table 5.20: ImplementationDataTypeElement

[TPS_SWCT_01254] ImplementationDataType with array semantics (cid:100) Of course, it is also possible to define an ImplementationDataType that provides array semantics. (cid:99)(RS_SWCT_03217)

[TPS_SWCT_01006] ImplementationDataType.subElement.arraySize shall be used to define the size of the array (cid:100) The primitive attribute ImplementationDataType.subElement.arraySize shall be used to define the size of the array. (cid:99)()

[TPS_SWCT_01007] Semantics of array index (cid:100) For an ImplementationDataType that implements an array data type, the semantics of the array index is such that
• it shall start with the value 0
• it shall run to the value of arraySize -1
(cid:99)()

[constr_1105] Value of arraySize (cid:100) The value of the attribute arraySize of an ImplementationDataTypeElement owned by an ImplementationDataType or ImplementationDataTypeElement of category ARRAY shall be greater than 0. (cid:99)()

[TPS_SWCT_01478] Array size is defined as an attribute of the ImplementationDataTypeElement (cid:100) Please note that the array size is not defined as an attribute of the ImplementationDataType which stands for the whole array. It is actually defined as an attribute of the ImplementationDataTypeElement which is describing the array element (note that the same pattern is used in ApplicationArrayDataType). (cid:99)()

Consequently, if a "struct" element represents an array this specific struct-element is given by an ImplementationDataTypeElement of category ARRAY which in turn aggregates another ImplementationDataTypeElement of e.g. category VALUE representing the array element and containing the size.

[TPS_SWCT_01255] Indicate whether the array is supposed to have a fixed size or whether the actual size might change during run-time (cid:100) It is also possible to indicate whether the array is supposed to have a fixed size or whether the actual size might change during run-time. (cid:99)(RS_SWCT_03217)

In the same way as for ApplicationDataTypes, it is also possible to specific a Size Indicator of a variable size array which holds the number of valid elements of the array in the ImplementationDataType.

Please find more information about this topic in section 5.2.4.2.

[TPS_SWCT_01622] Modeling of a Variable-Size Array Data Type only with ImplementationDataType (cid:100) The modeling of a Variable-Size Array Data Type does not require the existence of an ApplicationCompositeDataType and a DataTypeMap. A Variable-Size Array Data Type can be created by just setting up an ImplementationDataType. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01610] Modeling of a Variable-Size Array Data Type with Size Indicator enabled (cid:100) An ImplementationDataType with category STRUCTURE where the attribute ImplementationDataType.dynamicArraySizeProfile exists represents a Variable-Size Array Data Type with Size Indicator enabled. For the sake of a proper definition of terminology, this ImplementationDataType shall be called the VSA ImplementationDataType. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01650] Structure of the VSA ImplementationDataType (cid:100) The VSA ImplementationDataType shall consist of
• an ImplementationDataTypeElement representing the Size Indicator and
• an ImplementationDataTypeElement representing the Payload of the Variable-Size Array Data Type (see section 2.8.1.2).
For the sake of a proper definition of terminology, these ImplementationDataTypeElements shall be called the VSA Size Indicator ImplementationDataTypeElement and the VSA Payload ImplementationDataTypeElement respectively. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01612] arraySizeHandling specifies how the size is determined (cid:100) arraySizeHandling specifies how the size is determined in case of multi dimensional variable size array. (cid:99)(RS_SWCT_03181)

The statement made by [TPS_SWCT_01612] allows the specification of coherencies between the sizes of the nested variable size arrays in case of multiple dimensions.

[TPS_SWCT_01613] Internal structure of mapped ImplementationDataType (cid:100) The attribute dynamicArraySizeProfile specifies which internal structure the ImplementationDataType shall follow. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01614] Profiles for internal structure of mapped ImplementationDataType (cid:100) For the structure of the ImplementationDataType the following profiles are defined for dynamicArraySizeProfile: VSA_LINEAR, VSA_SQUARE, VSA_RECTANGULAR and VSA_FULLY_FLEXIBLE. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01615] Custom profiles for internal structure of mapped ImplementationDataType (cid:100) Custom profiles can be added to dynamicArraySizeProfile. They shall have a company-specific prefix. (cid:99)(RS_SWCT_03181)

For reasons of readability and understandability the following constraints focus on the payload of the Variable-Size Array Data Type only. For the Size Indicator additional individual constraints do apply.

[constr_1318] Profile VSA_LINEAR for ImplementationDataType (cid:100) If the value of attribute ImplementationDataType.dynamicArraySizeProfile is set to VSA_LINEAR, the ImplementationDataType shall aggregate a VSA Payload ImplementationDataTypeElement that fulfills all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall not be defined.
• The attribute ImplementationDataTypeElement.category shall be set to ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall not be defined.
The VSA Payload ImplementationDataTypeElement shall immediately aggregate another ImplementationDataTypeElement that shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
(cid:99)()

Please note that the ImplementationDataTypeElement aggregated by the VSA Payload ImplementationDataTypeElement can basically have any possible value of the attribute category.

[constr_1319] Profile VSA_SQUARE for ImplementationDataType (cid:100) If the value of attribute ImplementationDataType.dynamicArraySizeProfile is set to VSA_SQUARE, the ImplementationDataType shall aggregate a VSA Payload ImplementationDataTypeElement that fulfills all of the the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall not be defined.
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall not be defined.
The VSA Payload ImplementationDataTypeElement shall immediately aggregate another ImplementationDataTypeElement (representing the first dimension) that shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value inheritedFromArrayElementTypeSize.
All intermediate ImplementationDataTypeElements in the aggregation chain that do not terminate the chain shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value inheritedFromArrayElementTypeSize.
The terminating ImplementationDataTypeElement in the aggregation chain shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
(cid:99)()

[constr_1320] Profile VSA_RECTANGULAR for ImplementationDataType (cid:100) If the value of attribute ImplementationDataType.dynamicArraySizeProfile is set to VSA_RECTANGULAR, the ImplementationDataType shall aggregate a VSA Payload ImplementationDataTypeElement that fulfills all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall not be defined.
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall not be defined.
The VSA Payload ImplementationDataTypeElement shall immediately aggregate another ImplementationDataTypeElement (representing the first dimension) that shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
All intermediate ImplementationDataTypeElements in the aggregation chain that do not terminate the chain shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
The terminating ImplementationDataTypeElement in the aggregation chain shall fulfill all of the following conditions:
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.
(cid:99)()

[constr_1321] Profile VSA_FULLY_FLEXIBLE for ImplementationDataType (cid:100) If the value of attribute ImplementationDataType.dynamicArraySizeProfile is set to the value VSA_FULLY_FLEXIBLE, the ImplementationDataType shall aggregate a VSA Payload ImplementationDataTypeElement that fulfills all of the following conditions:

• The attribute ImplementationDataTypeElement.arraySizeSemantics shall not be defined.
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall not be defined.

The VSA Payload ImplementationDataTypeElement shall immediately aggregate another ImplementationDataTypeElement (representing the first dimension) that shall fulfill all of the following conditions:

• The attribute ImplementationDataTypeElement.category shall be set to STRUCTURE.
• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesDifferentArraySize.

The ImplementationDataTypeElement shall aggregate another ImplementationDataTypeElement that fulfills the following conditions:

• The attribute ImplementationDataTypeElement.arraySizeSemantics shall not be defined.
• The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
• The attribute ImplementationDataTypeElement.arraySize shall not be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall not be defined.

The aggregation chain is continued by a (possible empty) sequence of a pair of ImplementationDataTypeElements with the following characteristics:

• The first ImplementationDataTypeElement in the pair shall fulfill all of the following conditions:
  - The attribute ImplementationDataTypeElement.category shall be set to STRUCTURE.
  - The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
  - The attribute ImplementationDataTypeElement.arraySize shall be defined.
  - The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesDifferentArraySize.

• The second ImplementationDataTypeElement in the pair shall fulfill all of the following conditions:
  - The attribute ImplementationDataTypeElement.arraySizeSemantics shall not be defined.
  - The attribute ImplementationDataTypeElement.category shall be set to the value ARRAY.
  - The attribute ImplementationDataTypeElement.arraySize shall not be defined.
  - The attribute ImplementationDataTypeElement.arraySizeHandling shall not be defined.

The terminating ImplementationDataTypeElement in the aggregation chain shall fulfill all of the following conditions:

• The attribute ImplementationDataTypeElement.arraySizeSemantics shall be set to the value variableSize.
• The attribute ImplementationDataTypeElement.arraySize shall be defined.
• The attribute ImplementationDataTypeElement.arraySizeHandling shall be set to the value allIndicesSameArraySize.

(cid:99)()

[constr_1396] Restriction for the value of attribute category for non-terminating ImplementationDataTypeElements taken to model a Variable-Size Array Data Type (cid:100) The value of attribute category for non-terminating ImplementationDataTypeElements taken to model a Variable-Size Array Data Type shall not be set to TYPE_REFERENCE. (cid:99)()

[constr_1322] Size Indicator for undefined dynamicArraySizeProfile (cid:100) If the ImplementationDataType.dynamicArraySizeProfile does not exists but the ImplementationDataType is mapped to an ApplicationArrayDataType where the attribute ApplicationArrayDataType.dynamicArraySizeProfile exists, then the ImplementationDataType shall have the category STRUCTURE, representing a Variable-Size Array Data Type with Size Indicator enabled. (cid:99)()

[TPS_SWCT_01617] Structure of an ImplementationDataType that represents a variable-sized array data type (cid:100) The ImplementationDataType that represents a Variable-Size Array Data Type shall have the category STRUCTURE that has two subElements.
The role of the subElements with the definition of a Variable-Size Array Data Type is defined by [TPS_SWCT_01618], [TPS_SWCT_01619], [TPS_SWCT_01620], and [TPS_SWCT_01621]. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01618] Size Indicator for dynamicArraySizeProfile set to VSA_LINEAR, VSA_SQUARE, or VSA_FULLY_FLEXIBLE (cid:100) If an ImplementationDataType is mapped to an ApplicationArrayDataType which has attribute dynamicArraySizeProfile set to the value VSA_LINEAR, VSA_SQUARE or VSA_FULLY_FLEXIBLE, the first ImplementationDataType.subElement shall be an integer large enough to hold the maximum number of valid elements of the variable size array (according to maxArraySize).

This is the Size Indicator which holds the current number of valid elements of the variable size array. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01647] Size Indicator for dynamicArraySizeProfile set to VSA_LINEAR, VSA_SQUARE, or VSA_FULLY_FLEXIBLE if only ImplementationDataType is present (cid:100) For each ImplementationDataType which has attribute dynamicArraySizeProfile set to the value VSA_LINEAR, VSA_SQUARE, or VSA_FULLY_FLEXIBLE, the first ImplementationDataType.subElement shall be an integer large enough to hold the maximum number of valid elements of the variable size array (according to maxArraySize).

This is the Size Indicator which holds the current number of valid elements of the Variable-Size Array Data Type. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01619] Size Indicator for dynamicArraySizeProfile set to VSA_RECTANGULAR (cid:100) If an ImplementationDataType is mapped to an ApplicationArrayDataType where the attribute ApplicationArrayDataType.dynamicArraySizeProfile exists and is set to the value VSA_RECTANGULAR, the first ImplementationDataType.subElement shall be a ImplementationDataTypeElement with the category set to ARRAY and the attribute arraySize set to a value equal to the number of the according dimension of the corresponding ApplicationDataType. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01648] Size Indicator for dynamicArraySizeProfile set to VSA_RECTANGULAR if only ImplementationDataType is present (cid:100) For each ImplementationDataType where the attribute ImplementationDataType.dynamicArraySizeProfile exists and is set to the value VSA_RECTANGULAR, the first ImplementationDataType.subElement shall be a ImplementationDataTypeElement with the category set to ARRAY and the attribute arraySize set to a value equal to the size of the according dimension of the rectangular array. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01620] Size Indicator for dynamicArraySizeProfile set to VSA_RECTANGULAR (cid:100) The elements of this Size Indicator array shall consist of integers large enough to hold the maximum number of valid elements (according to maxArraySize). (cid:99)(RS_SWCT_03181)

This array holds the Size Indicators of all dimensions.

[TPS_SWCT_01621] Payload for dynamicArraySizeProfile (cid:100) If an ImplementationDataType is mapped to an ApplicationArrayDataType where the attribute dynamicArraySizeProfile exists, the second ImplementationDataType.subElement shall be an array which can hold the data of the variable size array with all dimensions defined for the ApplicationDataType.

The category shall be set to ARRAY and arraySize shall be set to maxArraySize of the corresponding ApplicationArrayDataType. (cid:99)(RS_SWCT_03181)

[TPS_SWCT_01649] Payload for dynamicArraySizeProfile if only ImplementationDataType is present (cid:100) Each ImplementationDataType where the attribute dynamicArraySizeProfile exists shall aggregate a second ImplementationDataType.subElement with the category set to ARRAY. (cid:99)(RS_SWCT_03181)

For examples, see Appendix E.1.

An ImplementationDataType is also allowed to have SwDataDefProps (this feature is inherited from AutosarDataType), i.e. it can define various specific structural and semantical attributes. Table 5.39 shows which SwDataDefProps will be typically used here.

[TPS_SWCT_01257] ImplementationDataType or the aggregated ImplementationDataTypeElements do not form closed sets (cid:100) As figures 5.11 shows, an ImplementationDataType or the aggregated ImplementationDataTypeElements do not form closed sets but refer to further type definitions in one of four distinctive ways, depending on whether the type is implemented via a base type, a data or function pointer, or a reference to another implementation data type:

1. Reference to an underlying SwBaseType corresponds to category VALUE.
2. Reference to BswModuleEntry in SwPointerTargetProps corresponds to category FUNCTION_REFERENCE.
3. SwDataDefProps in SwPointerTargetProps corresponds to category DATA_REFERENCE.
4. Reference to another ImplementationDataType corresponds to category TYPE_REFERENCE.

(cid:99)(RS_SWCT_03217)

At the end, all the "leafs" of the complete tree formed by these references shall end up in SwBaseTypes. Figures 5.12, 5.13, and Figure 5.14 illustrate more examples about Typedefs and references.

Figure 5.12: Example (1) for TypeDefs

[TPS_SWCT_01258] Definition of a pointer to data (cid:100) The definition of a data pointer requires a special meta-class SwPointerTargetProps which aggregates another SwDataDefProps. This mechanism allows to describe the category and properties of the pointer object itself as well as the category and properties of its target data type. (cid:99)(RS_SWCT_03217)

[constr_1177] Allowed targetCategory for SwPointerTargetProps (cid:100) The value of targetCategory for SwPointerTargetProps can only be one of TYPE_REFERENCE or FUNCTION_REFERENCE. The only exception from this rule applies if the swDataDefProps owned by the SwPointerTargetProps refers to a SwBaseType with native type declaration void, in this case the value VALUE is also permitted. (cid:99)()

Figure 5.13: Example (2) for TypeDefs

As far as the AUTOSAR meta-model is concerned, a pointer to a pointer could in principle be implemented in two ways:

1. by defining an ImplementationDataType of category DATA_REFERENCE that aggregates SwDataDefProps in the role swDataDefProps that in turn aggregate SwPointerTargetProps in the role swPointerTargetProps with attribute targetCategory set to TYPE_REFERENCE that aggregates SwDataDefProps in the role swDataDefProps that references an ImplementationDataType of category DATA_REFERENCE.

2. by defining an ImplementationDataType of category DATA_REFERENCE that aggregates SwDataDefProps in the role swDataDefProps that in turn aggregate SwPointerTargetProps in the role swPointerTargetProps with attribute targetCategory set to DATA_REFERENCE (which is not allowed according to [constr_1177]) that in turn aggregates SwDataDefProps in the role swDataDefProps that aggregates SwPointerTargetProps in the role swPointerTargetProps that references an ImplementationDataType of category e.g. VALUE.

[constr_1254] Definition of a pointer to a pointer (cid:100) AUTOSAR does not support the definition of a pointer to a pointer by defining an ImplementationDataType of category DATA_REFERENCE that aggregates SwDataDefProps in the role swDataDefProps that in turn aggregate SwPointerTargetProps in the role swPointerTargetProps with attribute targetCategory set to DATA_REFERENCE that in turn aggregates SwDataDefProps in the role swDataDefProps that aggregates SwPointerTargetProps in the role swPointerTargetProps that references an ImplementationDataType of category e.g. VALUE. (cid:99)()

For clarification, The AUTOSAR RTE does not support a definition of a pointer to a pointer by way of option 2 anyway. For all intents and purposes, [constr_1254] merely reflects this restriction on the level of AUTOSAR models. Option 1 (which is also featured in Figure 5.14) is the only viable way that is positively supported by the AUTOSAR RTE [2].

Figure 5.14: Example (3) for TypeDefs

[TPS_SWCT_01259] Definition of a pointer to a function (cid:100) An ImplementationDataType or one of its sub-elements can also describe a function pointer. This completes its ability to declare all kinds of local data and of possible arguments used in library calls.

A function pointer is defined by the category FUNCTION_REFERENCE and the association SwPointerTargetProps.functionPointerSignature that refers to a BswModuleEntry. The latter essentially describes the signature of a function as explained in [7]. (cid:99)(RS_SWCT_03217)

Table 5.21: SwPointerTargetProps

The allowed existence and multiplicity of all the attributes of SwDataDefProps and other properties depend on the category of the ImplementationDataType.

Figure 5.15: SwDataDefProps used in the context of ImplementationDataType

[constr_1178] Existence of attributes of SwDataDefProps in the context of ImplementationDataType (cid:100) For the sake of removing possible sources of ambiguity, SwDataDefProps used in the context of ImplementationDataType can only have one of 
• baseType 
• swPointerTargetProps 
• implementationDataType 
(cid:99)()

Please note that an ImplementationDataType manifests itself in the source code of an RTE into which a DataPrototype typed by the ImplementationDataType is deployed. This implies potential naming conflicts if ImplementationDataTypes that have identical shortNames are deployed into a specific RTE.

[TPS_SWCT_01194] Symbolic name of an ImplementationDataType (cid:100) To mitigate this potential hazard it is possible to provide the ImplementationDataType along with an accompanying symbolic name that can be used for resolving the name clash. The symbolic name is provided by means of the attribute symbol of the meta-class SymbolProps owned by ImplementationDataType in the role symbolProps (for more information, please refer to Figure 5.11). (cid:99)()

[TPS_SWCT_01441] Nature of a TYPE_REFERENCE (cid:100) A type reference (formally represented by an ImplementationDataType of category TYPE_REFERENCE) implements a redirection to common ImplementationDataTypes. (cid:99)()

[TPS_SWCT_01442] ImplementationDataType of category TYPE_REFERENCE does not define own properties (cid:100) As long as an ImplementationDataType of category TYPE_REFERENCE does not define own properties the properties of the refined ImplementationDataType apply. (cid:99)()

[TPS_SWCT_01443] ImplementationDataType of category TYPE_REFERENCE overwrites properties of refined ImplementationDataType (cid:100) If an implementation data types of category TYPE_REFERENCE defines own properties (e.g. CompuMethod) this properties overwrite the properties of the refined ImplementationDataType. (cid:99)()

As explained by [constr_1050], Compatibility checks of ImplementationDataType require a prior resolution of possible type references, i.e. the compatibility shall be checked on the resolved ImplementationDataType.

Figure 5.16: ImplementationProps and its subclasses

ImplementationProps (abstract)
Table 5.22: ImplementationProps
Table 5.23: SymbolProps

#@SECTION: 5.2.6 Base Type
#@CLASS: BaseType
#@CLASS: BaseTypeDefinition
#@CLASS: BaseTypeDirectDefinition
#@CLASS: SwBaseType
#@CLASS: DataPrototype
#@CLASS: ImplementationDataType

[TPS_SWCT_01260] SwBaseType (cid:100) BaseType is used to specify the basic level mentioned in chapter 5.1. In AUTOSAR, we use the meta-class SwBaseType which is derived from the abstract class BaseType due to other use cases for BaseType in ASAM HDO. (cid:99)()

[TPS_SWCT_01261] Use case for SwBaseType (cid:100) One use case for SwBaseType is to serve as input for the RTE generator. It will always appear at the "leaves" of the types definitions which are relevant for RTE generation. It is used to generate the corresponding C-code typedef's in case the attribute BaseTypeDirectDefinition.nativeDeclaration exists. (cid:99)()

[constr_1010] If nativeDeclaration does not exist (cid:100) If nativeDeclaration does not exist in the SwBaseType it is required that the shortName (e.g. "uint8") of the corresponding ImplementationDataType is equal to a name of one of the Platform or Standard Types predefined in AUTOSAR code. (cid:99)()

The consequence of [constr_1010] is that if the nativeDeclaration does not exist the RTE generator will not consider the ImplementationDataType for the generation of data type definitions. Still, the compiler will positively be able to resolve the data type because it can fall back to the data type definitions contained in the header file for platform and standard data types that has to be included by regulation of the AUTOSAR standard.

Please note that nativeDeclaration shall yield a valid C data type symbol, whether this is done by a typedef or a by using the symbol of an integral data type is principally all the same. Of course, using the symbol of an integral data type as the value of nativeDeclaration increases the odds that the enclosing SwBaseType can be used independently of the availability of the definition of a typedef that may or may not be available in a given context. The symbol does not necessarily have to consist of a single token, i.e. for all intents and purposes (for example) unsigned char is also considered the symbol of an integral C data type.

[TPS_SWCT_01563] Applicable values for nativeDeclaration (cid:100) For the purpose of avoiding portability issues the value nativeDeclaration should only consist of the symbol of an integral C data type. (cid:99)()

For more information on this refer to [22].

[TPS_SWCT_01263] Further use cases for SwBaseType (cid:100) Within the basic software description, SwBaseType can be used (together with ImplementationDataTypes) for documentation or to specify variables for debugging. Furthermore, SwBaseTypes are required in the generation of support data for measurement and calibration tools. Please refer to [7] for details on these use cases. (cid:99)()

A more detailed description of BaseTypes can also be found in ASAM MCD 2 Harmonized Data Objects.

Table 5.24: BaseType
Table 5.25: SwBaseType
Table 5.26: BaseTypeDefinition
Table 5.27: BaseTypeDirectDefinition
Figure 5.17: BaseType

Some additional hints to the properties of SwBaseType:
#@Hierarchical
• [constr_1011] category of SwBaseType (cid:100) For the attribute SwBaseType.category only the values FIXED_LENGTH and VARIABLE_LENGTH are supported. (cid:99)()
• [constr_1012] Value of category is FIXED_LENGTH (cid:100) If the value of the attribute SwBaseType.category is set to FIXED_LENGTH then the attribute baseTypeSize shall be filled with content and attribute maxBaseTypeSize shall not exist. (cid:99)()
• [constr_1013] Value of category is VARIABLE_LENGTH (cid:100) If the value of the attribute SwBaseType.category is set to VARIABLE_LENGTH then the attribute maxBaseTypeSize shall be filled with content and attribute baseTypeSize shall not exist. (cid:99)()
• [TPS_SWCT_01444] Size of SwBaseType is specified in bits (cid:100) In both cases (mentioned in [constr_1012] and [constr_1013]) the size of SwBaseType is specified in bits. (cid:99)()
• The attribute baseTypeEncoding specifies how the values of the base type are encoded.

[constr_1014] Supported value encodings for SwBaseType (cid:100) The supported values for attribute BaseTypeDirectDefinition.baseTypeEncoding are:
- 1C: One's complement
- 2C: Two's complement
- BCD-P: Packed Binary Coded Decimals
- BCD-UP: Unpacked Binary Coded Decimals
- DSP-FRACTIONAL: Digital Signal Processor
- SM: Sign Magnitude
- IEEE754: floating point numbers
- ISO-8859-1: ASCII-Strings
- ISO-8859-2: ASCII-Strings
- WINDOWS-1252: ASCII-Strings
- UTF-8: UCS Transformation Format 8
- UTF-16: Character encoding for Unicode code points based on 16 bit code units [16]
- UCS-2: Universal Character Set 2
- NONE: Unsigned Integer
- VOID: corresponds to a void in C. The encoding is not formally specified here.
- BOOLEAN: This represents an unsigned integer to be interpreted as boolean. The value shall be interpreted as true if the value of the unsigned integer is 1 and it shall be interpreted as false if the value of the unsigned integer is 0. A CompuMethod shall be referenced by the corresponding Autosar DataType that implements the common sense behind the boolean concept, i.e. define a TEXTTABLE with two CompuScales: e.g. true --> 1, false --> 0. (cid:99)()

• [TPS_SWCT_01262] memAlignment and byteOrder are platform-specific (cid:100) The value of attributes BaseTypeDirectDefinition.memAlignment and BaseTypeDirectDefinition.byteOrder is platform-specific and therefore should be set only in use cases where this is really needed. These attributes shall be considered as optional. If a SwBaseType is platform-specific then also the ImplementationDataType and software-component descriptions build on top of it become platform-specific. (cid:99)()

However, there are use cases for SwBaseType where this does not matter: especially the calibration support format which is generated in ECU-specific scope (and also contains SwBaseType, see [7]) could well be platform-specific.
/#@Hierarchical

Further regulations apply for the case that the value UTF-16 is used for setting the attribute BaseTypeDirectDefinition.baseTypeEncoding:

[constr_1398] Existence of attributes of BaseTypeDirectDefinition (cid:100) If the value of attribute BaseTypeDirectDefinition.baseTypeEncoding is set to UTF-16 then the attribute BaseTypeDirectDefinition.byteOrder shall exist. The only allowed values of BaseTypeDirectDefinition.byteOrder in this case are mostSignificantByteFirst and mostSignificantByteLast (cid:99)()

There is already predefined terminology (see [16]) existing that describes the two possible cases of byte orientation in a UTF-16-encoded string. The connection to this terminology is defined by [TPS_SWCT_01651] and [TPS_SWCT_01652].

[TPS_SWCT_01651] UTF-16BE (cid:100) If the value of attribute BaseTypeDirectDefinition.baseTypeEncoding is set to UTF-16 and the attribute BaseTypeDirectDefinition.byteOrder in this case are mostSignificantByteFirst then the SwBaseType corresponds to the definition of UTF-16BE according to the Unicode standard [16]. (cid:99)()

[TPS_SWCT_01652] UTF-16LE (cid:100) If the value of attribute BaseTypeDirectDefinition.baseTypeEncoding is set to UTF-16 and the attribute BaseTypeDirectDefinition.byteOrder in this case are mostSignificantByteLast then the SwBaseType corresponds to the definition of UTF-16LE according to the Unicode standard [16]. (cid:99)()

A further question that needs clarification is the usage of the so-called Byte Order Mark which allows (at run-time) for determining the actual byte order directly from the payload of a unicode string. As AUTOSAR has means to formally and comprehensively define the byte order of any given DataPrototype that can hold a string at run time it is not necessary to support a further instrument that pretty much takes care of the same purpose.

[TPS_SWCT_01653] UTF-16-encoded strings are not allowed to start with a BOM (cid:100) If the value of attribute BaseTypeDirectDefinition.baseTypeEncoding is set to UTF-16 then the value of a DataPrototype (which is effectively representing a string) is not allowed to start with a Byte Order Mark (BOM). (cid:99)()

Please note that [TPS_SWCT_01653] removes a possible redundancy in the definition and execution of UTF-16-encoded strings. The redundancy is not only regarded unnecessary but also potentially dangerous because it is not possible to check whether the definition is consistent with the execution at configuration time. From the formal point of view, [TPS_SWCT_01653] does not represent an actual constraint although it is formulated as such. However, an AUTOSAR tool would not be able to properly check the condition at configuration time and therefore this rule is published as a specification item.

#@SECTION: 5.2.7 Data Type Terminology
#@CLASS: ApplicationDataType

There are uses of data types that on the one hand need a handy term (because this kind of data type is used a lot) but on the other hand cannot easily be expressed in simple terms of meta-model elements (like ApplicationDataType). Therefore, it is not an option to fully describe the characteristics of these kinds of data types precisely every time one of these is used. A definition of terminology is supposed to associate the mentioned kinds of data types with the term under which their use shall be paraphrased.

#@SECTION: 5.2.7.1 Primitive Type
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: AutosarDataType
#@CLASS: ImplementationDataType

In some cases it is necessary to constrain that applicability of data types to primitive C data types. It would be possible to describe the characteristics of eligible Autosar DataTypes at every single place in an AUTOSAR specification where this specific limitation applies.

However, this may end up in lengthy and potentially inconsistent descriptions at different places within AUTOSAR specifications. Therefore, this chapter provides a canonical definition of a primitive data type that can be referred to from other places.

[TPS_SWCT_01564] Non-recursive definition of a primitive data type (cid:100) An AutosarDataType is considered a primitive data type if the following conditions apply:
• it is an ApplicationPrimitiveDataType of category VALUE or BOOLEAN
• it is an ImplementationDataType of category VALUE
(cid:99)()

[TPS_SWCT_01565] Recursive definition of a primitive data type (cid:100) An AutosarDataType is considered a primitive data type if the following conditions apply:
• it is an AutosarDataType according to [TPS_SWCT_01564]
• it is an AutosarDataType of category TYPE_REFERENCE that, after all type references have been resolved, boils down an AutosarDataType according to [TPS_SWCT_01564].
(cid:99)()

#@SECTION: 5.2.7.2 Compound Primitive Data Type
#@CLASS: ApplicationPrimitiveDataType

[TPS_SWCT_01179] Compound Primitive Data Type (cid:100) For clarification, a "compound primitive data type" is an ApplicationPrimitiveDataType of category STRING, CURVE, MAP, CUBOID, CUBE_4, CUBE_5, COM_AXIS, RES_AXIS, and VAL_BLK.

This implies the existence of a swRecordLayout owned by the swDataDefProps of the ApplicationPrimitiveDataType that defines the mapping to a corresponding ImplementationDataType.

The main characteristic of the "compound primitive data type" is that with respect to the application data type layer its data type is considered a primitive data type but when it comes to the implementation data type layer the type is implemented as a composite data type according to the applicable SwRecordLayout. (cid:99)(RS_SWCT_03216)

[TPS_SWCT_01486] ApplicationPrimitiveDataType of category STRING may have invalidValue (cid:100) The only kind of Compound Primitive Data Type that is allowed to define an invalidValue is an ApplicationPrimitiveDataType of category STRING. (cid:99)(RS_SWCT_03216)

[constr_1241] Compound Primitive Data Types and invalidValue (cid:100) Compound Primitive Data Types that have set the value of of category other than STRING shall not define invalidValue. (cid:99)()

#@SECTION: 5.2.7.3 Integral Primitive Type
#@CLASS: ApplicationDataType
#@CLASS: DataTypeMap
#@CLASS: ImplementationDataType
#@CLASS: SenderReceiverToSignalMapping
#@CLASS: SwBaseType

The SenderReceiverToSignalMapping (see [11]) allows for the integral mapping of a piece of data to a single SystemSignal. The specification of AUTOSAR COM [21] imposes certain requirements on the characteristics of data that apply for the integral mapping.

[TPS_SWCT_01477] Integral Primitive Types (cid:100) Data types that qualify for being used in the context of a The SenderReceiverToSignalMapping shall be called Integral Primitive Types. (cid:99)(RS_SWCT_03218)

[constr_1229] category of ImplementationDataType boils down to VALUE (cid:100) An ImplementationDataType qualifies as an Integral Primitive Type if and only if either
• its category is VALUE or TYPE_REFERENCE that eventually boils down to VALUE or
• its category is ARRAY and it has only one subElement and one of the following conditions applies:
  – subElement.category is set to VALUE or TYPE_REFERENCE that eventually boils down to VALUE and the subElement refers to a SwBaseType where baseTypeSize or maxBaseTypeSize is set to the value 8 and the baseTypeEncoding is set to NONE.
  – subElement.category is set to TYPE_REFERENCE and the swDataDefProps.implementationDataType literally represents the Platform Data Type named “uint8”.
  – subElement.category is set to TYPE_REFERENCE and the attribute swDataDefProps.implementationDataType.shortName is set to “uint8” and swDataDefProps.baseType.baseTypeDefinition.nativeDeclaration does not exist. (cid:99)()

[constr_1230] ApplicationDataType that qualifies for Integral Primitive Type (cid:100) An ApplicationDataType qualifies as an Integral Primitive Type if and only if all of the following conditions apply:
• ApplicationDataType.category is set to BOOLEAN, VALUE, STRING, or ARRAY
• in the applicable scope a DataTypeMap is available that refers to the given ApplicationDataType
• the found DataTypeMap refers to an ImplementationDataType that fulfills the requirements of [constr_1229] (cid:99)()

#@SECTION: 5.2.7.4 Variable-Size Array Data Type
The definition of and further explanation regarding the term Variable-Size Array Data Type can be found in chapter 2.8.

#@SECTION: 5.3 Data Prototypes
#@SECTION: 5.3.1 Overview

#@CLASS: ApplicationArrayElement
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ApplicationRecordElement
#@CLASS: ArgumentDataPrototype
#@CLASS: AutosarDataPrototype
#@CLASS: DataPrototype
#@CLASS: ParameterDataPrototype
#@CLASS: VariableDataPrototype
#@CLASS: PortInterface
#@CLASS: ApplicationDataType
#@CLASS: SwDataDefProps
#@CLASS: ApplicationDataType
#@CLASS: ImplementationDataType
[TPS_SWCT_01264] Data prototypes implement a role of a data type (cid:100) Generally speaking, a data prototype represents the implementation of a role of a data type within the definition of another data type, e.g. a "typed" data object declared within a software component or a port interface. This means formally that it has an is-of-type relation to a data type and is usually aggregated by another element, e.g. the internal behavior or a port interface. (cid:99)()

In the meta-model, various kinds of data prototypes are derived from the abstract DataPrototype as shown in figure 5.18. The reason for the introduction of this hierarchy was the distinction between AutosarDataPrototype (which can be used for the application and implementation types as well) and ApplicationCompositeElementDataPrototype (which is restricted to be used within the application types).

Figure 5.18: Data Prototypes Overview

Table 5.28: DataPrototype

Table 5.29: AutosarDataPrototype

Table 5.30: ApplicationCompositeElementDataPrototype

Because these DataPrototypes are modeled as own meta-classes it is possible to define own attributes for them (on M2) which (in the M1 model) could extend or constrain the attribute values already set via the corresponding data type.

[TPS_SWCT_01265] DataPrototype aggregates an own set of SwDataDefProps (cid:100) This mechanism is used here in the way that DataPrototype aggregates an own set of SwDataDefProps. Thus each kind of DataPrototype has the ability to extend or even overwrite the SwDataDefProps already defined by its ApplicationDataType or ImplementationDataType. This mechanism, if carefully applied, allows for a better reuse of data types because they can be kept free of the properties which vary according to the context or are defined in later project phases. Chapter 5.4 describes more details on this. (cid:99)()

[TPS_SWCT_01445] Applicability of SwDataDefProps for DataPrototypes (cid:100) The applicability of SwDataDefProps for DataPrototypes shall follow the same rules as for the categorys of the corresponding AutosarDataTypes (see table 5.8). (cid:99)()

Further information can be found in table 5.31 and table 5.32.

Please note that table 5.31 does not include the ApplicationRecordElement and
ApplicationArrayElement because these specializations of ApplicationCompositeElementDataPrototype are already part of table 5.8. The same applies for
table 5.32 which does not include the ImplementationDataTypeElement.

Table 5.31: Allowed Attributes vs. category for DataPrototypes typed by Application Data Types

<-------------- multimodal context 


### Attributes of SwDataDefProps

| Attributes | RootElem. |  |  | AttributeExistenceperCategory |  |  |  |  |  |  |  |  |  |  |  |  |
|------------|-----------|--|--|-------------------------------|---------|-----------|-------|--------|----------|----------|----------|-------|-----|--------|--------|--------|
|  | DataPrototype | InstantiationDataDefProps | ParameterAccess | VALUE | VAL_BLK | STRUCTURE | ARRAY | STRING | BOOLEAN | COM_AXIS | RES_AXIS | CURVE | MAP | CUBOID | CUBE_4 | CUBE_5 |
| additionalNativeTypeQualifier |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| annotation | x | x | x | * | * | * | * | * | * | * | * | * | * | * | * | * |
| baseType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| compuMethod |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| dataConstr | x | x |  | 0..1 | 0..1 |  |  |  | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| displayFormat | x | x |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| implementationDataType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| invalidValue |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| stepSize | x | x | x | 0..1 | 0..1 |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swAddrMethod | x | x |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swAlignment | x | x |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swBitRepresentation |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swCalibrationAccess | x | x |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swCalprmAxisSet |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swCalprmAxisSet.swCalprmAxis/SwAxisGrouped.swCalprmRef |  | x | x |  |  |  |  |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swCalprmAxisSet.swCalprmAxis/SwAxisIndividual.swVariableRef |  | x | x |  |  |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swCalprmAxisSet.swCalprmAxis/SwAxisGrouped.sharedAxisType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swCalprmAxisSet.swCalprmAxis/SwAxisIndividual.inputVariableType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swCalprmAxisSet.swCalprmAxis/SwAxisIndividual.unit |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swCalprmAxisSet.swCalprmAxis.baseType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swComparisonVariable |  |  | x |  |  |  |  |  |  |  |  | 0..* | 0..* | 0..* | 0..* | 0..* |
| swDataDependency | x | x |  | 0..1 |  |  |  |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swHostVariable |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swImplPolicy | x |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swIntendedResolution |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swInterpolationMethod | x | x | x | 0..1 |  |  |  |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swIsVirtual | x | x |  | 0..1 |  |  |  |  | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swPointerTargetProps |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swRecordLayout |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swRefreshTiming | x | x |  | 0..1 | 0..1 |  |  | 0..1 | 0..1 |  |  |  |  |  |  |  |
| swTextProps |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| swValueBlockSize |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| unit |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| valueAxisDataType |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
------------------------>
[constr_1289] Allowed Attributes vs. category for DataPrototypes typed by ApplicationDataTypes (cid:100) The allowed values of Attributes per category for DataPrototypes typed by ApplicationDataTypes are documented in table 5.31. (cid:99)()

Table 5.32: Allowed Attributes vs. category for DataPrototypes typed by ImplementationDataTypes
<-------------- multimodal context 


### Attributes of SwDataDefProps

| Attributes | RootElement |  |  | Attribute Existence per Category |  |  |  |  |  |  |
|------------|-------------|--|--|------------------------------|-----------------|---------------------|-----------------|----------|-------|-------|
|  | DataPrototype | InstantiationDataDefProps | ParameterAccess | VALUE | DATA_REFERENCE | FUNCTION_REFERENCE | TYPE_REFERENCE | STRUCTURE | UNION | ARRAY |
| additionalNativeTypeQualifier |  |  |  |  |  |  |  |  |  |  |
| annotation | x | x | x | * | * | * | * | * | * | * |
| baseType |  |  |  |  |  |  |  |  |  |  |
| compuMethod |  |  |  |  |  |  |  |  |  |  |
| dataConstr | x | x |  | 0..1 |  |  | 0..1 |  |  |  |
| displayFormat | x | x |  | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 |
| implementationDataType |  |  |  |  |  |  |  |  |  |  |
| invalidValue |  |  |  | 0..1 |  |  |  |  |  |  |
| stepSize | x | x |  | 0..1 |  |  |  |  |  |  |
| swAddrMethod | x | x |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swAlignment | x | x |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swBitRepresentation |  |  |  |  |  |  |  |  |  |  |
| swCalibrationAccess | x | x |  | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 |
| swCalprmAxisSet |  |  |  |  |  |  |  |  |  |  |
| swComparisonVariable |  |  |  |  |  |  |  |  |  |  |
| swDataDependency |  |  |  |  |  |  |  |  |  |  |
| swHostVariable |  |  |  |  |  |  |  |  |  |  |
| swImplPolicy | x |  |  | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 | 0..1 |
| swIntendedResolution |  |  |  |  |  |  |  |  |  |  |
| swInterpolationMethod |  |  |  |  |  |  |  |  |  |  |
| swIsVirtual |  |  |  |  |  |  |  |  |  |  |
| swPointerTargetProps |  |  |  |  |  |  |  |  |  |  |
| swPointerTargetProps.swDataDefProps |  |  |  |  |  |  |  |  |  |  |
| swPointerTargetProps.functionPointerSignature |  |  |  |  |  |  |  |  |  |  |
| swRecordLayout |  |  |  |  |  |  |  |  |  |  |
| swRefreshTiming | x | x |  | 0..1 |  |  | 0..1 | 0..1 | 0..1 | 0..1 |
| swTextProps |  |  |  |  |  |  |  |  |  |  |
| swValueBlockSize |  |  |  |  |  |  |  |  |  |  |
| unit |  |  |  |  |  |  |  |  |  |  |
| valueAxisDataType |  |  |  |  |  |  |  |  |  |  |
------------------------>

[constr_1288] Allowed Attributes vs. category for DataPrototypes typed by ImplementationDataTypes (cid:100) The allowed values per category for DataPrototypes typed by ImplementationDataTypes are documented in table 5.32. (cid:99)()

[TPS_SWCT_01266] Three non-abstract classes derived from AutosarDataPrototype (cid:100) There are three non-abstract classes derived from AutosarDataPrototype which reflect the main use cases in the SWC-Template:
• Operation arguments (ArgumentDataPrototype) in a client-server interface.
• Variables (VariableDataPrototype) which are changed by the application software at runtime.
• Parameters (ParameterDataPrototype) which are constant (except for calibration access) from the application point of view. (cid:99)()

Table 5.33: ArgumentDataPrototype

Table 5.34: VariableDataPrototype

Table 5.35: ParameterDataPrototype

[TPS_SWCT_01267] DataPrototype can be aggregated in different roles (cid:100) Note that even though the meta-classes VariableDataPrototype and ParameterDataPrototype already express specific use cases of the underlying data type the same DataPrototype can still be aggregated in different roles, e.g. in the SwcInternalBehavior to express different methods how to access it. (cid:99)()

An example is the aggregation of VariableDataPrototype by SwcInternalBehavior in the roles of either implicitInterRunnableVariable or explicitInterRunnableVariable. Find more information concerning these use cases in chapter 7.

[TPS_SWCT_01268] Definition of initValue for a VariableDataPrototype or a ParameterDataPrototype (cid:100) It is possible to assign an initValue for both a VariableDataPrototype and a ParameterDataPrototype. This aspect is sketched in Figure 5.19. (cid:99)()

[TPS_SWCT_01269] In PortInterfaces, initial values defined for DataPrototypes are ignored (cid:100) These initValues have no meaning for DataPrototypes within PortInterfaces because in this case a more specific definition of initial values via the so-called ComSpec is required, see chapter 4.5. (cid:99)()

Figure 5.19: Initial value for AutosarDataPrototypes

Find more information about the interpretation of initValue in section 5.7.

#@SECTION: 5.3.2 Reference to Data Prototypes
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ArVariableInImplementationDataInstanceRef
#@CLASS: AutosarDataPrototype
#@CLASS: AutosarParameterRef
#@CLASS: AutosarVariableRef
#@CLASS: DataPrototype
#@CLASS: ParameterDataPrototype
#@CLASS: VariableDataPrototype
#@CLASS: AutosarDataType
#@CLASS: AtpInstanceRef
#@CLASS: FlatInstanceDescriptor
#@CLASS: AnyInstanceRef
#@CLASS: McDataInstance

This chapter explains the various patterns for referencing DataPrototypes.

[TPS_SWCT_01446] References to a DataPrototype may or may not imply the necessity for using an instanceRef (cid:100) As references to a DataPrototype may or may not imply the necessity for using an instanceRef this would mean that in some places the meta-model would have to implement both variants depending on the use case. To avoid this, AUTOSAR defines a unified reference implementation for VariableDataPrototypes and ParameterDataPrototypes. (cid:99)()

[TPS_SWCT_01270] AutosarVariableRef (cid:100) With the advent of AutosarVariableRef it is possible to implement a uniform reference to a VariableDataPrototype that covers all foreseen use cases:
• Reference to a localVariable, no AtpInstanceRef required.
• Reference to an autosarVariable (which involves an AtpInstanceRef).
• Reference to the internal structure of a VariableDataPrototype implemented using a composite ImplementationDataType.
(cid:99)()

Table 5.36: AutosarVariableRef

Figure 5.20: Implementation of AutosarVariableRef

Table 5.37: ArVariableInImplementationDataInstanceRef

Figure 5.21: Implementation of ArVariableInImplementationDataInstanceRef

[constr_2536] Target of an autosarVariable in AutosarVariableRef shall refer to a variable (cid:100) The target of autosarVariable (which in fact is an instance ref) in AutosarVariableRef shall either be or be nested in VariableDataPrototype. This means that the target shall either be a VariableDataPrototype or an ApplicationCompositeElementDataPrototype that in turn is owned by a VariableDataPrototype. (cid:99)()

[TPS_SWCT_01271] AutosarParameterRef (cid:100) With the advent of AutosarParameterRef it is possible to implement a uniform reference to a ParameterDataPrototype that covers all foreseen use cases:
• Reference to a localParameter, no AtpInstanceRef required.
• Reference to an autosarParameter (which involves an AtpInstanceRef).
(cid:99)()

Please note that there is a very limited amount of use-cases available where the AutosarParameterRef can (with the active consent of the AUTOSAR standard) reference a VariableDataPrototype.

[constr_1173] Applicability of AutosarParameterRef referencing a VariableDataPrototype (cid:100) A reference from AutosarParameterRef to VariableDataPrototype is only applicable if the AutosarParameterRef is used in the context of SwAxisGrouped. (cid:99)()

For example, the use case referenced in [constr_1173] applies if it is required to store a grouped axis in a variable in order to adapt the axis during run-time of the ECU by a dedicated algorithm. Note that in all cases where [constr_1173] does not apply [constr_2535] shall be fulfilled.

Table 5.38: AutosarParameterRef

[constr_2535] Target of an autosarParameter in AutosarParameterRef shall refer to a parameter (cid:100) Except for the specifically described cases where [constr_1173] applies the target of autosarParameter (which in fact is an instance ref) in AutosarParameterRef shall either be or be nested in ParameterDataPrototype. This means that the target shall either be a ParameterDataPrototype or an ApplicationCompositeElementDataPrototype that in turn is owned by a ParameterDataPrototype. (cid:99)()

[constr_1161] Applicability of the index attribute of Ref (cid:100) The index attribute of Ref is limited to a given set if use cases as there are:
• McDataInstance.instanceInMemory
• AutosarVariableRef
• AutosarParameterRef
• FlatInstanceDescriptor / AnyInstanceRef
(cid:99)()

The implementation of the AtpInstanceRefs for AutosarVariableRef and AutosarParameterRef probably needs some clarification regarding the references to DataPrototypes.

[TPS_SWCT_01374] Implementation of AutosarParameterRef (cid:100) The reference to rootParameterDataPrototype is not redundant. It is required for identifying the autosarParameter itself in a ParameterInterface if and only if the AutosarDataType of the autosarParameter is a composite data type. If the AutosarDataType was a primitive data type the targetDataPrototype reference is the only reference required. (cid:99)()

As explained before, the implementation of AutosarParameterRef in a specific case is subject to [constr_1173].

Figure 5.22: Implementation of the InstanceRef for AutosarParameterRef

[TPS_SWCT_01375] Implementation of AutosarVariableRef (cid:100) The reference to rootVariableDataPrototype is not redundant. It is required for identifying the autosarVariable itself in a SenderReceiverInterface or NvDataInterface if and only if the AutosarDataType of the autosarVariable is a composite data type. If the AutosarDataType was a primitive data type the targetDataPrototype reference is the only reference required. (cid:99)()

Figure 5.23: Implementation of the InstanceRef for AutosarVariableRef

#@SECTION: 5.4 Properties of Data Deﬁnitions
#@SECTION: 5.4.1 Overview
#@CLASS: SwDataDefProps
#@CLASS: ApplicationDataType
#@CLASS: CompuMethod
#@CLASS: ImplementationDataType
#@CLASS: NativeDeclarationString
#@CLASS: SwBitRepresentation
#@CLASS: DisplayFormatString
#@CLASS: Annotation
#@CLASS: DataPrototype
#@CLASS: AtomicSwComponentType
#@ENUM: SwCalibrationAccessEnum
#@CLASS: InstantiationDataDefProps
#@CLASS: ParameterAccess
#@CLASS: FlatInstanceDescriptor
#@CLASS: McDataInstance
#@CLASS: McSupportData
#@ENUM: SwImplPolicyEnum
#@CLASS: VariableDataPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: ArgumentDataPrototype
#@CLASS: SwServiceArg

As it has already been shown in the previous chapters, various properties and associations can be attached to the definition of data types as well as prototypes. These are described by the meta-class SwDataDefProps which covers all properties of a particular data object under various aspects.

In general, the properties specified within SwDataDefProps may apply to all kind of data declared within the software-component template and within the basic software module description template as well, e.g. component local data, data used for communication, data used for measurement as well as for calibration.

However, there are constraints for the attributes depending on the role of the data:

[constr_1015] Prioritization of SwDataDefProps (cid:100) The prioritization and usage of attributes of meta-class SwDataDefProps shall follow the restrictions given in table 5.39. (cid:99)()

Table 5.39: Usage of Attributes of SwDataDefProps
<-------------- multimodal context 


| Attribute of **SwDataDefProps** | Usage For RTE | Usage For A2L | Usage For Other | ApplicationDataType | ImplementationDataType | DataPrototype | InstantiationDataProps | ParameterAccess | ComSpec | SwServiceArg | FlatInstanceDescriptor |McDataInatance| SwSystemconst | PerInstanceMemory |
|---------------------------------|:------------------:|:------------------:|:---------------:|:--------------------:|:-----------------------:|:--------------:|:------------------------:|:----------------:|:------:|:-----------:|:-------------------------:|:----------------:|:----------------:|:----------------:|:----------------:|
| additionalNativeTypeQualifier                                     |  x  |   | x | NA | D  | I  | NA | NA | NA | D  | NA | I  | NA  | NA  |
| annotation                                                        |     |   | x | D  | A  | A  | A  | A  | A  | D  | NA |  A | D   | NA  |
| baseType                                                          |  x  | x | x | NA | D  | I  | I  | I  | R  | D  | NA |  A | M   | NA  |
| compuMethod                                                       |  x  | x | x | D | AI  | I  | I  |NA  | R  | I  | AI | AI | D   | NA  |
| dataConstr                                                        |  x  | x | x | D  | C  | R  | R  | I  |NA  | R  | NA | I  | D   | NA  |
| displayFormat                                                     |   |  x  |   | D  | A  | R  | R  | I  | NA | R  | NA |  I | D   | NA  |
| implementationDataType                                            |  x  |   | x | NA | D  | I  | I  | I  | NA | D  | NA | NA |NA   | NA  |
| invalidValue                                                      |  x  | x |   | D  | A  | I  | I  | NA | D  | NA | NA | I  | NA  | NA  |
| stepSize                                                          |   |  x  |   | D  | A  | A  | A  | A  | NA | NA | A  | I  |  NA | NA  |
| swAddrMethod                                                      | x |  x  | x | D  | R  | R  | R  |NA  | NA | NA | R  | NA | NA  | D   |
| swAlignment                                                       | x |   |  x  | NA | D  | R  | R  |NA  | NA | NA |NA  | NA | NA  | NA  |
| swBitRepresentation                                               |   |  x | x  | NA |NA  | NA | NA |NA  | NA | NA | NA | D  | NA  | NA  |
| swCalibrationAccess                                               | x |  x  |   | D  | R  | R  | R  | NA | NA | R  | R  | I  | D   | NA  |
| swCalprmAxisSet                                                   |  x  | x |   | D  | NA | I  | I  | I  | NA | NA | NA | I   | NA | NA  |
| swCalprmAxisSet.swCalprmAxis / SwAxisGrouped.swCalprmRef          |   |  x  |   | NA | NA | NA | D  | R  | NA | NA | NA | I   | NA | NA  |
| swCalprmAxisSet.swCalprmAxis / SwAxisIndividual.swVariableRef     |   |  x  |   | NA | NA | NA | D  | R  | NA | NA | NA | I   | NA | NA  |
| swCalprmAxisSet.swCalprmAxis / SwAxisGrouped.sharedAxisType       |   |  x  |   | D  | NA | NA | NA | NA | NA | NA | NA | I   | NA | NA  |
| swCalprmAxisSet.swCalprmAxis / SwAxisIndividual.inputVariableType |   |  x  |   | D  | NA | NA | NA | NA | NA | NA | NA | I   | NA | NA  |
| swCalprmAxisSet / SwAxisIndividual.unit                           |   | opt.|   | D  | NA | I  | I  | I  | NA | I  | NA | I  | NA   | NA  |
| swComparisonVariable                                              |    |  x |   | NA | NA | NA | NA | D  | NA | NA | NA | I   | NA | NA  |
| swDataDependency                                                  |   |  x |  x | NA | NA | D  | R  | NA | NA | NA | NA | I   | NA | NA  |
| swHostVariable                                                    |   |  x  | x | NA |NA  | NA | NA |NA  | NA | NA | NA | D  | NA  | NA  |
| swImplPolicy                                                      |  x  |   | x | D  | A  | A  | NA | NA | NA | D  | NA | NA  | NA  | NA  |
| swIntendedResolution                                              |   |    |  x | D(NOTE) | NA | NA | NA | NA | NA | NA | NA  | NA | NA  | NA |
| swInterpolationMethod                                             |    |   |  x | D  | I  | R  | R  | R  | NA | NA | NA | I  | NA  | NA  |
| swIsVirtual                                                       |    | x  |   | NA | NA | D  | R  | NA | NA | NA | NA | I  | NA  | NA  |
| swPointerTargetProps                                              |    |   |  x | NA | D  | I  | NA | NA | NA | D  | NA | NA |NA   | NA  |
| swRecordLayout                                                    |  x  |  x  |  x  | D | NA | I | I | I | NA | NA |NA | I | NA |NA |
| swRefreshTiming                                                   |   |  x  |   | D | R | R | R | NA |NA | R | NA | R | NA |NA |
| swTextProps                                                       |    |  x  | x | D | I | I | I | I | NA | NA | NA | I |NA |NA |
| swValueBlockSize                                                  |    |  x  | x | D | I | I | I | I | NA | NA | NA | I |NA |NA |
| unit                                                              |    |  x  | x | D | I | I | I | NA| NA | I |  NA | I |NA |NA |
| valueAxisDataTypeType                                             |    |  x  | x | D | I | I | I | I | NA | NA | NA | I |NA |NA |

NOTE:swIntendedResolution is used only in an early phase of the definition of data types, namely in the context of the definition of so-called blueprints. To that extent, swIntendedResolution represents a non-binding requirement that shall later be considered for the definition of an appropriate CompuMethod.
---------------------->

The following settings apply in table 5.39:


D Define the attribute independent from settings to the left.

R Use or re-define definition from the left in the scope of this element.

A Add attribute if not defined on the left, or as an additional information.

If the attribute has an upper multiplicity > 1 and the attribute is defined on the left then the attribute is added to the attribute defined on the left.

If the attribute has a upper multiplicity of 1 and the attribute is not defined on the left then the attribute is defined.

If the attribute has an upper multiplicity of 1 and the attribute is already defined on the left then the attribute is not redefined but this is considered as invalid configuration.

I Inherit the definition from the left for usage in the scope of this element.

NA Attribute is not applicable for usage in the scope of this element.

M Attribute is meaningless in the scope of this element. As it was allowed in previous versions, declaring it as Not Applicable (NA) would break compatibility. Tools shall ignore such an attribute without a warning.

C This means that the left element constrains right element.

AI If the attribute is already defined on the left then the attribute is not redefined but adds implementation-related information.

Example: an ApplicationDataType of category BOOLEAN supports the definition of an own CompuMethod to define the semantics of e.g. (ON, OFF) or (HIGH, LOW) or (PASSED , FAILED) as long as the number of values match and matching pairs of values on application level and implementation level exist. In contrast, the corresponding ImplementationDataType uses (true, false) as the applicable literals in any of the above mentioned cases.

Some of the property names contain the term "variable" or "calprm", this comes from historical reasons and can be taken as some hint where the property most likely applies to.

Table 5.40: SwDataDefProps

Table 5.41: NativeDeclarationString

Table 5.42: SwBitRepresentation

Table 5.43: DisplayFormatString

Table 5.44: Annotation

[constr_1244] DataPrototypes used in application software shall not be typed by C enums (cid:100) A DataPrototype that is used in an AtomicSwComponentType shall not set swDataDefProps.additionalNativeTypeQualifier to enum. (cid:99)()

[TPS_SWCT_01272] Semantics of swComparisonVariable (cid:100) Please note that swComparisonVariables shall be displayed in the MCD system on the ordinate in a curve. By showing the input value and the comparison value the calibration engineer can see if the current working point is above or below a curve provident thresholds. For example in a curve specifying a temperature depending gear shift threshold engine speed the engine speed can be shown as "comparisonVariable".
These variables can be used to display the value of a variable on the value axis of a calibration parameter (characteristic), that is currently displayed in the MCD-System. The purpose is to compare the appropriate result from the calibration parameter in question, with a value being calculated or taken from a sensor (the comparison variable).
The sole purpose of this comparison-variable is therefore to serve the calibration process. (cid:99)()


<-------------- multimodal context 
The provided figure is not an AUTOSAR SW-Component architecture at all but rather a time-response plot of a variable called swComparisonVariable (measured voltage Vs rising toward and oscillating about a threshold V until a motor-start time tmot). To summarize its intent:

– It shows how Vs climbs to V (at tx) and then settles around V before the motor-enable instant tmot.  
– “swComparisonVariable” is the internal signal being compared against threshold V.  
– The plot illustrates damping/overshoot behavior when Vs reaches its set value.  
– Use-case: trigger a downstream action (e.g. motor start) when the monitored voltage crosses and stabilizes at the threshold.  
– No SW-Components, ports, interfaces or AUTOSAR prototypes are depicted—this is purely a timing/behavioral graph, not an SWC architecture. ---------------------->
Figure 5.24: Explanation of swComparisonVariable

Table 5.45: SwCalibrationAccessEnum

[TPS_SWCT_01273] Precedence rules for the application of SwDataDefProps (cid:100) SwDataDefProps can be specified on various levels, from type over prototype to instantiation, finally data access and calibration support after RTE generation. In general, properties specified on prototype level override the ones specified on type level.

More formally, the precedence of such properties is:

1. attributes of SwDataDefProps defined on ApplicationDataType which may be overwritten by

2. attributes of SwDataDefProps defined on ImplementationDataType which may be overwritten by

3. attributes of SwDataDefProps defined on DataPrototype which may be overwritten by

4. attributes of SwDataDefProps defined on InstantiationDataDefProps which may be overwritten by

5. attributes of SwDataDefProps defined on ParameterAccess respectively Argument which may be overwritten by

6. attributes of SwDataDefProps defined on FlatInstanceDescriptor which may be overwritten by

7. attributes of SwDataDefProps defined on McDataInstance (cid:99)()

Note that details about applicable attributes of SwDataDefProps can be found in Table 5.39.

[TPS_SWCT_01274] SwDataDefProps used to support calibration and measurement (cid:100) The last item in the list of use cases contained in [TPS_SWCT_01273] denotes that SwDataDefProps are also used as part of McSupportData which is a direct input to the generation of measurement and calibration configuration formats (so-called A2L-files). This use case is further explained in [7]. Since these data are generated by the RTE, they will use a copy of the properties according to the precedence given above.

However, even in this use case which comes after RTE generation it is possible that properties relevant for the MCD system are added which had been undefined so far.

This for example, applies to the attribute swRefreshTiming which denotes a timing information relevant for the measurement system; this information may be set rather late in the process chain. (cid:99)()

Obviously such an override is not applicable in all cases. In particular, the properties covering the structure shall not be redefined on DataPrototype. Implementation policy, semantics and code generation policy may be changed under consideration of compatibility rules.

Access policy for the MCD system is the most likely subject to be redefined on the DataPrototype of even on an instantiation level.

Section 5.4.3 describes how SwDataDefProps are used for measuring purposes while Section 5.4.4 describes the construction of characteristics based on the combination of SwDataDefProps with DataPrototypes.

Section 2.2.2 describes in which context calibration parameters can be defined. Finally, sections 2.2.3, 7.5.4, and 5.5.4 show how calibration parameters are used in RunnableEntitys and show the link to an actual ECU implementation.

Table 5.46: SwImplPolicyEnum

[TPS_SWCT_01275] values of the attribute swImplPolicy are restricted depending on the context (cid:100) The values of the attribute swImplPolicy are restricted depending on the context. This restriction reflects the fact that not all possible implementation strategies are useful or supported for all kinds of DataPrototypes. (cid:99)()

These restrictions are summarized in table 5.47 and formalized in the following constraints. Please note that the usage of swImplPolicy is further constraint in the
combination with the attribute value swCalibrationAccess as described in [constr_1017].

Table 5.47: Allowed attributes values for SwImplPolicy vs. DataPrototypes and their roles
<-------------- multimodal context 


| AttributeofSwImplPolicyEnum | VariableDataPrototype |  |  |  |  |  |  | ParameterDataPrototype |  |  |  |  | Misc. |  |
|----------------------------|----------------------|--|--|--|--|--|--|------------------------|--|--|--|--|-------|--|
|  | VariableDataPrototype in SenderReceiverInterface | VariableDataPrototype in NvDataInterface | VariableDataPrototype in role ramBlock | VariableDataPrototype in role implicitInterRunnableVariable | VariableDataPrototype in role explicitInterRunnableVariable | VariableDataPrototype in role arTypedPerInstanceMemory | VariableDataPrototype in role staticMemory | ParameterDataPrototype in ParameterInterface | ParameterDataPrototype in role romBlock | ParameterDataPrototype in role sharedParameter | ParameterDataPrototype in role perInstanceParameter | ParameterDataPrototype in role constantMemory | ArgumentDataPrototype | SwServiceArg |
| const | NA | NA | NA | NA | NA | NA | NA | x | NA | NA | NA | x | NA | x |
| fixed | NA | NA | NA | NA | NA | NA | NA | x | NA | NA | NA | x | NA | NA |
| measurementPoint | x | NA | NA | NA | NA | x | x | NA | NA | NA | NA | NA | NA | NA |
| queued | x | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| standard | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| message | NA | NA | NA | NA | NA | NA | x | NA | NA | NA | NA | NA | NA | NA |
------------------------>

The following settings apply in table 5.47:

x Attribute is applicable for usage in the scope of this element.

NA Attribute is not applicable for usage in the scope of this element.

[constr_2035] swImplPolicy for VariableDataPrototype in SenderReceiverInterface (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in SenderReceiverInterface shall be standard, queued or measurementPoint. (cid:99)()

[constr_2036] swImplPolicy for VariableDataPrototype in NvDataInterface (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in NvDataInterface shall be standard. (cid:99)()

[constr_2037] swImplPolicy for VariableDataPrototype in the role ramBlock (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in the role ramBlock shall be standard. (cid:99)()

[constr_2038] swImplPolicy for VariableDataPrototype in the role implicitInterRunnableVariable (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in the role implicitInterRunnableVariable shall be standard. (cid:99)()

[constr_2039] swImplPolicy for VariableDataPrototype in the role explicitInterRunnableVariable (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in the role explicitInterRunnableVariable shall be standard. (cid:99)()

[constr_2040] swImplPolicy for VariableDataPrototype in the role arTypedPerInstanceMemory (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in the role arTypedPerInstanceMemory shall be standard or measurementPoint.(cid:99)()
[constr_2041] swImplPolicy for VariableDataPrototype in the role staticMemory (cid:100) The overriding swImplPolicy attribute value of a VariableDataPrototype in the role staticMemory shall be standard, measurementPoint or message.(cid:99)()
[constr_2042] swImplPolicy for ParameterDataPrototype in ParameterInterface (cid:100) The overriding swImplPolicy attribute value of a ParameterDataPrototype in ParameterInterface shall be standard, const or fixed.(cid:99)()
[constr_2043] swImplPolicy for ParameterDataPrototype in the role staticMemory (cid:100) The overriding swImplPolicy attribute value of a ParameterDataPrototype in the role romBlock shall be standard.(cid:99)()
[constr_2044] swImplPolicy for ParameterDataPrototype in the role sharedParameter (cid:100) The overriding swImplPolicy attribute value of a ParameterDataPrototype in the role sharedParameter shall be standard.(cid:99)()
[constr_2045] swImplPolicy for ParameterDataPrototype in the role perInstanceParameter (cid:100) The overriding swImplPolicy attribute value of a ParameterDataPrototype in the role sharedParameter shall be standard.(cid:99)()
[constr_2046] swImplPolicy for ParameterDataPrototype in the role constantMemory (cid:100) The overriding swImplPolicy attribute value of a ParameterDataPrototype in the role sharedParameter shall be standard, const or fixed.(cid:99)()
[constr_2047] swImplPolicy for ArgumentDataPrototype (cid:100) The overriding
swImplPolicy attribute value of a ArgumentDataPrototype shall be standard. (cid:99)()
[constr_2048] swImplPolicy for SwServiceArg (cid:100) The overriding swImplPolicy
attribute value of a SwServiceArg shall be standard or const. (cid:99)()
[TPS_SWCT_02000] Default value for attribute swImplPolicy (cid:100) If the attribute
swImplPolicy is not explicitly set at any of the locations listed in "‘Place of Setting"’for SwDataDefProps mentioned in table 5.39 the default value standard applies.(cid:99)()

#@SECTION: 5.4.2 Invalid Value
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: DataPrototype
#@CLASS: ImplementationDataType
#@CLASS: InvalidationPolicy
#@CLASS: NonqueuedReceiverComSpec
#@CLASS: RPortPrototype
#@CLASS: ReceiverComSpec
#@CLASS: SenderReceiverInterface
#@CLASS: SwDataDefProps
#@CLASS: VariableDataPrototype
#@CLASS: ValueSpecification
#@CLASS: AutosarDataType
#@CLASS: DataPrototype
#@CLASS: RuleBasedValueSpecification
#@CLASS: ReferenceValueSpecification
#@CLASS: SwBaseType
#@CLASS: CompuScales
#@CLASS: TextValueSpecification
#@CLASS: CompuMethod
#@CLASS: ImplementationDataTypeElement
#@CLASS: BaseType
#@CLASS: ApplicationDataType
#@CLASS: NumericalValueSpecification
#@ENUM: HandleInvalidEnum

The diagram 5.5 shows that in addition to the semantics defined through the compuMethod (explained below in chapter 5.5.1), also an invalidValue can be specified. This is a requirement of the VFB [3], allowing to express which specific value is used to indicate invalidation.

Figure 5.25: Invalid value


<-------------- multimodal context 
This diagram illustrates the layered mapping of an AUTOSAR ApplicationDataType into an ECU’s raw BaseType representation, showing how physical values are constrained, converted via a CompuMethod, and how invalid values are handled at each layer.

- Component hierarchy  
  • ApplicationDataType at the top level  
  • CompuMethod mediating value conversion  
  • ImplementationDataType intermediate layer  
  • BaseType providing the underlying numeric range  

- Ports & interfaces  
  • physConstrs of ApplicationDataType (upper/lower bounds)  
  • limits of CompuMethod (mapping domain)  
  • internalConstrs of ApplicationDataType and ImplementationDataType  
  • range by BaseType  

- Data flow  
  • Physical value enters ApplicationDataType  
  • Mapped through CompuMethod to an internal scale  
  • Constrained by ImplementationDataType  
  • Finally represented within the BaseType range  

- Key AUTOSAR concepts  
  • CompuMethod for scaling/calibration  
  • physConstrs/internalConstrs for validity checks  
  • InvalidValue (transparent vs. known)  
  • Layered DataType definitions  

- Scenario  
  • Converting a sensor’s physical measurement into a validated, ECU-compatible integer signal, while managing out-of-range and invalid values. ---------------------->
The invalidValue can be used in different flavors (also illustrated in Figure 5.6:
#@Hierarchical
• [TPS_SWCT_01432] Keep the invalidValue transparent to the sending and receiving software components (cid:100) On the one hand it is possible to keep the invalidValue transparent to the sending and receiving software components. In this case the invalidation API of the RTE on the sender side has to be used. The receiving software component can either use the data receive status or the DataReceiveErrorEvent respectively DataReceivedEvent to decide about the validity of the received data or the receiving software component can rely on the reception of an initValue as a default value in case of data invalidation. In this case the invalid value should (and usually will) be outside of the range limits defined by the compuMethod. (cid:99)()

• [TPS_SWCT_01434] Sender and receiver have knowledge of invalid value (cid:100) On the other hand it is possible that the communicating software components do have knowledge about the invalidValue and the invalidValue is visible for them. This is in particular the case if the sender and receiver are calculating a checksum over a larger data structure to implement an end to end communication protection. To ensure the integrity of the checksums it is required to set invalid values by the sending component directly and to receive invalid values unchanged. In this case the invalid value should (and usually will) be inside of the range limits defined by the compuMethod. (cid:99)()

• [TPS_SWCT_01436] Different receivers require different handling of data invalidation (cid:100) It is possible that in case of 1:n communication different receivers requiring a different handling of data invalidation depending on the criticality of its functionality. For instance, one receiver applies the checksum based end to end communication protection and another receiver relies on the substitution of invalid values by invalidValues. (cid:99)()
/#@Hierarchical

A typical use case for putting the invalidValue inside the boundaries of the applicable CompuMethod is a composite data type that contains the values of all individual wheel speeds. If one of the sensors fails and starts to send invalidValue it would probably not make sense to consider the whole composite data element invalid. It may very likely still be possible to make sense of the remaining intact wheel speed values and carry on with whatever business the receiving software-component has with that data. From this perspective, it would obviously be OK for the sending software-component to actively send the invalidValue that is then processed as a "regular" value without applying additional semantics by the RTE/Com.

[TPS_SWCT_01646] Sending invalidValue without invalidation applied by intentionally sending invalidValue without RTE/Com (cid:100) For invalidation applied by RTE/Com the SenderReceiverInterface.invalidationPolicy.handleInvalid shall be set to the value HandleInvalidEnum.dontInvalidate. (cid:99)()

[constr_1390] Restriction to the value of SenderReceiverInterface.invalidationPolicy.handleInvalid (cid:100) If the value of SenderReceiverInterface.invalidationPolicy.handleInvalid is set to any value other than HandleInvalidEnum.dontInvalidate then the invalidValue shall not be within the interval defined by the CompuMethod of the applicable dataElement. (cid:99)()

Please note that ApplicationPrimitiveDataTypes of category VALUE in principle can have an invalidValue provided by a NumericalValueSpecification because the value of the attribute invalidValue can be outside the range of the applicable CompuMethod (see [TPS_SWCT_01432]).

[TPS_SWCT_01437] invalidValue can also be specified without setting a compuMethod (cid:100) An invalidValue can also be specified without setting a compuMethod. (cid:99)()

Figure 5.6 illustrates the relationship between ApplicationDataType, CompuMethod, ImplementationDataType, invalidValue, BaseType.

[constr_2545] invalidValue shall fit in the specified ranges (cid:100) The invalidValue shall be in the range of the ImplementationDataType. (cid:99)()

Please note that the invalidValue is a ValueSpecification. Of course, it would technically be possible to use any subclass of ValueSpecification at this place.

[constr_1016] Restriction of invalidValue for ImplementationDataType and ImplementationDataTypeElement (cid:100) invalidValue for ImplementationDataType and ImplementationDataTypeElement is restricted to to be either a compatible NumericalValueSpecification, TextValueSpecification (caution, [constr_1284] applies) or a ConstantReference that in turn points to a compatible ValueSpecification. (cid:99)()

[constr_1384] Definition of invalidValue for DataPrototype typed by ApplicationPrimitiveDataType of category CURVE, MAP, CUBOID, CUBE_4, CUBE_5, COM_AXIS, RES_AXIS, and VAL_BLK (cid:100) An invalidValue shall not be specified for a DataPrototype typed by ApplicationPrimitiveDataType of category CURVE, MAP, CUBOID, CUBE_4, CUBE_5, COM_AXIS, RES_AXIS, and VAL_BLK (cid:99)()

Rationale for [constr_1384]: there is no use case for sending a DataPrototype typed by ApplicationPrimitiveDataType of category CURVE, MAP, CUBOID, CUBE_4, CUBE_5, COM_AXIS, RES_AXIS, and VAL_BLK over a communication bus.

[constr_1242] Restriction of invalidValue for ApplicationPrimitiveDataType of category STRING (cid:100) invalidValue for ApplicationPrimitiveDataType of category STRING ([constr_1241] applies) is restricted to be either a compatible ApplicationValueSpecification or a ConstantReference that in turn points to a compatible ApplicationValueSpecification. (cid:99)()

[TPS_SWCT_01487] Correspondence of invalidValue for ApplicationPrimitiveDataType and ImplementationDataType (cid:100) The invalidValue specified on the level of an ApplicationPrimitiveDataType shall correspond to the invalidValue specified on the level of a compatible ImplementationDataType. The terms "corresponds" boils down to: 
• category VALUE or BOOLEAN: application of CompuMethod 
• category STRING: mapping of the encoding on the ApplicationPrimitiveDataType side to the numerical values on the level of the ImplementationDataType (shall reference SwBaseType with baseTypeEncoding set to NONE). There is no formal support defined to check that the values of invalidValue really correspond to each other. (cid:99)()

[constr_1225] DataPrototype is typed by an ImplementationDataType that references a CompuMethod of category TEXTTABLE or BITFIELD_TEXTTABLE (cid:100) If a DataPrototype is typed by an ImplementationDataType that references a CompuMethod of category TEXTTABLE or BITFIELD_TEXTTABLE the applicable ValueSpecification shall be a TextValueSpecification. In this case the value provided shall match to one of the applicable text values (vt, shortLabel, symbol) defined by the applicable CompuScales. (cid:99)()

[TPS_SWCT_01467] ImplementationDataType references an SwBaseType with a string encoding (cid:100) If an ImplementationDataType references an SwBaseType with a string encoding the initValue shall still be provided as numerical values according to the string encoding. (cid:99)()

[constr_1302] Restriction of data invalidation (cid:100) Data invalidation is only applicable for one of the following cases applicable on the receiving side: 1. VariableDataPrototypes typed by either an ApplicationPrimitiveDataType or an ImplementationDataType of category VALUE or TYPE_REFERENCE that boils down to category VALUE that have defined an invalidValue. 2. VariableDataPrototypes typed by either an ApplicationCompositeDataType or an ImplementationDataType of category STRUCTURE, or ARRAY or of category TYPE_REFERENCE that boils down to category STRUCTURE, or ARRAY that have at least one primitive element with an invalidValue. 3. VariableDataPrototypes typed by an ImplementationDataType of category UNION or of category TYPE_REFERENCE that boils down to category UNION where all primitive elements define an invalidValue. (cid:99)()

[constr_1140] Combination of invalidValue with the attribute handleInvalid (cid:100) The combination of setting the attribute handleInvalid of the meta-class InvalidationPolicy owned by SenderReceiverInterface to value replace and of setting the value of the attribute initValue owned by a corresponding NonqueuedReceiverComSpec effectively to the value of the invalidValue (owned by a corresponding SwDataDefProps) is not supported. (cid:99)()

The term "corresponding" (as utilized in [constr_1140]) refers to the fact that information regarding the fulfillment of [constr_1140] is factually distributed over different areas of the meta-model. For clarification, the following relationship should be considered: The SenderReceiverInterface defines how to deal with an invalid value by means of the attribute handleInvalid on the basis of individual dataElements. The SenderReceiverInterface is taken for typing a RPortPrototype that in turn owns a ReceiverComSpec. [constr_1140] applies if the particular ReceiverComSpec is actually a NonqueuedReceiverComSpec that refers to the same dataElement. In this case the invalidValue owned by the SwDataDefProps that in turn is owned by the respective dataElement is relevant for the fulfillment of [constr_1140]. The "big picture" of this relationship is sketched in Figure 5.26.

[constr_1219] Invalidation depends on the value of swImplPolicy (cid:100) Invalidation of dataElements is only supported for dataElements where the value of swImplPolicy is not set to queued. (cid:99)()

Figure 5.26: Relationships required to consider the invalidValue

[constr_1282] Restriction concerning the usage of RuleBasedValueSpecification or a ReferenceValueSpecification for the specification of an invalidValue (cid:100) The aggregation of a RuleBasedValueSpecification or a ReferenceValueSpecification for the definition of a ApplicationPrimitiveDataType.swDataDefProps.invalidValue is not supported. (cid:99)()

#@SECTION: 5.4.3 Properties for Measurement
#@CLASS: ArgumentDataPrototype
#@CLASS: DataPrototype
#@CLASS: NvDataInterface
#@CLASS: PortPrototype
#@CLASS: RunnableEntity
#@CLASS: SenderReceiverInterface
#@CLASS: SwComponentPrototype
#@CLASS: SwcInternalBehavior
#@CLASS: VariableAccess
#@CLASS: VariableDataPrototype
#@CLASS: SwDataDefProps
#@CLASS: VariableAccess
#@ENUM: SwCalibrationAccessEnum
#@CLASS: ArgumentDataPrototype
#@CLASS: ClientServerOperation

In embedded automotive software design, measurement means access to memory locations in an ECU and transferring its contents to the measurement & calibration system. While in classical software design, variables abstract the memory locations in the code, AUTOSAR provides for this purpose the DataPrototype with its various specializations:

• VariableDataPrototype of a SenderReceiverInterface or NvDataInterface used in a PortPrototype (of a SwComponentPrototype), to capture sender-receiver and non volatile data communication between SwComponentPrototypes

• ArgumentDataPrototype of a ClientServerInterface to capture client-server communication between SwComponentPrototypes.

• VariableDataPrototype in the context of an SwcInternalBehavior to
  – capture communication between RunnableEntitys within a SwComponentPrototype
  – handle data in a non volatile memory block
  – provide pure software component internal memory which has to be accessible for a MCD system

[TPS_SWCT_01440] Measurement is not limited to primitive objects (cid:100) The ability of being measured is not restricted to primitive data (category VALUE) but can also be applied to composite data (category STRUCTURE or ARRAY). (cid:99)()

The following semantical and structural features from SwDataDefProps are relevant (among other purposes) for the measurement system:
• swCalibrationAccess
• swImplPolicy
• compuMethod
• unit (if not specified by compuMethod)
• baseType
• swAddrMethod

[TPS_SWCT_01130] Measurement and calibration access to model elements is defined by swCalibrationAccess (cid:100) The ability to be accessed by e.g. a calibration tool is given by setting the swCalibrationAccess attribute. (cid:99)(RS_SWCT_03152)

The following table shows all valid settings of swCalibrationAccess:

Table 5.48: SwCalibrationAccessEnum

[TPS_SWCT_01559] Default value for attribute SwDataDefProps.swCalibrationAccess (cid:100) The default value for the attribute SwDataDefProps.swCalibrationAccess is SwCalibrationAccessEnum.notAccessible. (cid:99)()

[constr_1017] Supported combinations of swImplPolicy and swCalibrationAccess (cid:100) The table 5.49 defines the supported combinations of swImplPolicy and swCalibrationAccess attribute setting. (cid:99)()


<-------------- multimodal context 
```markdown
| swImplPolicy     | swCalibrationAccess |                |             |
|------------------|---------------------|----------------|-------------|
|                  | notAccessible       | readOnly       | readWrite   |
| fixed            | yes                 | not supported  | not supported |
| const            | yes                 | yes            | not supported |
| standard         | yes                 | yes            | yes           |
| queued           | yes                 | not supported  | not supported |
| measurementPoint | not supported       | yes            | not supported |
``` ---------------------->
Table 5.49: Supported combinations of swImplPolicy and swCalibrationAccess

[constr_1018] measurementPoint shall not be referenced by a VariableAccess aggregated by RunnableEntity in the role dataReadAccess (cid:100) Due to the nature of data elements characterized by setting the swImplPolicy to measurementPoint, such data elements shall not be referenced by a VariableAccess aggregated by RunnableEntity in the role dataReadAccess. (cid:99)()

#@SECTION: 5.4.4 Properties of Curves and Maps
#@CLASS: ApplicationDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: CompuMethod
#@CLASS: DataConstr
#@CLASS: SwAddrMethod
#@CLASS: SwAxisGeneric
#@CLASS: SwAxisGrouped
#@CLASS: SwAxisIndividual
#@CLASS: SwAxisType
#@CLASS: SwBaseType
#@CLASS: SwCalprmAxis
#@CLASS: SwCalprmAxisSet
#@CLASS: SwCalprmAxisTypeProps
#@CLASS: SwCalprmRefProxy
#@CLASS: SwDataDefProps
#@CLASS: SwGenericAxisParam
#@CLASS: SwRecordLayout
#@CLASS: SwVariableRefProxy
#@CLASS: Unit
#@CLASS: SwGenericAxisParamType
#@ENUM: CalprmAxisCategoryEnum
#@CLASS: CompuMethod
#@CLASS: BaseType
#@CLASS: AutosarDataType

A characteristic table is defined by setting the category of the corresponding AutosarDataType or DataPrototype to CURVE respectively MAP, CUBOID, CUBE_4, and CUBE_5. Its SwDataDefProps determine an axis description. The type of the functional values is given by the attached SwBaseType and the CompuMethod.

The axis description itself is defined by the meta-model element SwCalprmAxisSet aggregating the appropriate number of SwCalprmAxisTypeProps. This is the base class for a so called "individual axis" (formalized by meta-class SwAxisIndividual) or a "grouped axis" (formalized by meta-class SwAxisGrouped). The latter is used to share axis points by several characteristic tables. Figure 5.27 shows an overview on the relevant meta-model elements.

The type of the functional values is given by the attached SwBaseType and the CompuMethod or by the referenced ApplicationDataType. If an ApplicationDataType is referenced (via valueAxisDataType) this supersedes CompuMethod, Unit, and BaseType if these are defined in parallel.

Figure 5.27: Overview on the Meta-Model for Axis Description

Figure 5.28: Overview on a Generic Axis

Figure 5.29 shows how an individual axis is represented by the meta-model. The corresponding M1 Model is illustrated in Figure 5.30. The SwAxisIndividual references value-models to account the minimum and the maximum number of axis values as well as the number of axis points. Hence, the size of the structure to hold the functional values is determined by the number of axis values for all axes. The type of the axis values is determined when the type of the referenced input value (swVariableRef) has been set. For further details see 5.4.5.

[TPS_SWCT_01107] swMinAxisPoints and swMaxAxisPoints represent variation points (cid:100) The value of attributes swMinAxisPoints and swMaxAxisPoints is subject to variant handling. (cid:99)(RS_SWCT_03148)

Figure 5.29: Meta-Model Elements used for a Curve
Figure 5.30: Illustration of a Curve in M1
Table 5.50: SwCalprmAxisSet
Table 5.51: SwCalprmAxis
Table 5.52: CalprmAxisCategoryEnum
Table 5.53: SwCalprmAxisTypeProps
Table 5.54: SwAxisIndividual
Table 5.55: SwAxisGeneric
Table 5.56: SwAxisGrouped

#@SECTION: 5.4.5 Setting an Axis Input Value
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ArgumentDataPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarParameterRef
#@CLASS: AutosarVariableRef
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: DataPrototype
#@CLASS: InstantiationDataDefProps
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: PortPrototype
#@CLASS: RunnableEntity
#@CLASS: SenderReceiverInterface
#@CLASS: SwAxisGrouped
#@CLASS: SwAxisIndividual
#@CLASS: SwCalprmRefProxy
#@CLASS: SwDataDefProps
#@CLASS: SwcInternalBehavior
#@CLASS: SwVariableRefProxy
#@CLASS: VariableDataPrototype

When an interpolation routine is called, an input value has to be provided to find the appropriate axis entry in the implementation of a RunnableEntity. However, this input value cannot be arbitrarily chosen but only be selected from available VariableDataPrototype assigned to it.

In an axis definition attached to an ApplicationPrimitiveDataType, it is possible to specify the inputVariableType for the input values.

[constr_1019] Compatibility of input value and axis (cid:100) The SwDataDefProps the input variable shall be compatible to the datatype resp. compuMethod resp. unit of the SwAxisIndividual. (cid:99)()

Every ParameterDataPrototype then allows to specify zero or more input values (being type compatible to inputVariableType) in its axis description.

This means that at the specification time of an SwcInternalBehavior a list of input values has to be specified where the implementer of a RunnableEntity can choose of. The input values are DataPrototype entities either being:

• a VariableDataPrototype in a SenderReceiverInterface or NvDataInterface of a PortPrototype, of the AtomicSwComponentType where the SwcInternalBehavior is associated to, or an ArgumentDataPrototype in a ClientServerOperation of a ClientServerInterface in a PortPrototype of the AtomicSwComponentType where the InternalBehavior is associated to, or
• an VariableDataPrototype within the SwcInternalBehavior.

To achieve this, SwAxisIndividual is aggregating a SwVariableRefProxy.

Originally, MSRSW uses a AutosarVariableRef to set the input value of an axis appropriately. In AUTOSAR, this has been extended by first introducing a SwVariableRefProxy.

Note that this is a specific use case for the role SwVariableRefProxy.autosarVariable.

Note further that the use cases for the existence of the attributes SwVariableRefProxy.autosarVariable and SwVariableRefProxy.mcDataInstanceVar are entirely disjoint and therefore the simultaneous existence of these two attributes would not make any sense at all.

Therefore, [constr_1382] has been introduced to clarify this aspect.

[constr_1382] Mutually exclusive existence of attributes SwVariableRefProxy.autosarVariable vs. SwVariableRefProxy.mcDataInstanceVar (cid:100) In the aggregations SwVariableRefProxy.autosarVariable and SwVariableRefProxy.mcDataInstanceVar shall never exist at the same time in any given AUTOSAR model. (cid:99)()

As shown in Figure 5.31, this approach is also used to represent a AutosarVariableRef in all roles, e.g. the result of an interpolation routine applied to an axis, the input value determination, a list of dependent parameters, and swDataDependency.

Figure 5.31: Extended Axis Elements and Input Variable Reference

Grouped curves share the same axis definition. In MSRSW, this is shown by referencing the SwCalprm, representing an individual curve, from a SwAxisGrouped.

Note that this does not describe which axis shall be taken from a reference swCalprmRef acting as a shared axis. This would be done in SwAxisGrouped.swAxisIndex.

AUTOSAR applies a similar proxy approach for parameters as for the variables. Therefore, an SwCalprmRefProxy has been introduced in MSRSW, and is aggregated by the SwAxisGrouped element.

The SwCalprmRefProxy aggregates an AutosarParameterRef providing an association to a ParameterDataPrototype, representing a curve with an axis. When defining the data type of a parameter the type of the shared axis is defined in sharedAxisType.

[constr_1020] ParameterDataPrototype needs to be of compatible data type as referenced in sharedAxisType (cid:100) Finally, the ParameterDataPrototype assigned in swCalprmRef shall be typed by data type compatible to sharedAxisType. (cid:99)()

The AUTOSAR-style is shown in the upper left part of Figure 5.31, while in the upper middle the MSRSW style is shown, referencing the SwCalprm.

Figure 5.32: Applying Proxy Variable Reference Mechanism

Figure 5.33: Applying Proxy Parameter Reference Mechanism

Table 5.57: SwCalprmRefProxy

Table 5.58: SwVariableRefProxy

Figure 5.34: Proxy reference classes

The basic patterns for referencing DataPrototypes are explained in section 5.3.2. In the context of this chapter it is worth to remark that the definition of access to calibration parameters is implemented in the context of a RunnableEntity (see Figure 7.3).

As the definition of a calibration parameter may involve the definition of several axes the necessity to provide this amount of information might become cumbersome and (to some extent) redundant and difficult to maintain if the same calibration parameter is accessed from within several RunnableEntitys. In this case it would be necessary to repeat the more or less complex set of information for each RunnableEntity.

In other words: To avoid this unnecessary level of complexity for the definition of access to calibration parameters, it is possible to define the access to the calibration parameter on the level of InstantiationDataDefProps which have been defined to facilitate this kind of re-use (for more information please refer to section 7.5.4). This ability is also documented in Table 5.39.

#@SECTION: 5.4.6 Specifying Data Dependencies
#@CLASS: ParameterDataPrototype
#@CLASS: SwDataDependency
#@CLASS: SwDataDependencyArgs
#@CLASS: SwVariableRefProxy

SwDataDependency allows dependent data elements to be specified. For example, other ParameterDataPrototypes can be combined into one ParameterDataPrototype whose consistent value is automatically derived by the measurement and calibration system. Upon adjusting one of the parameters, the dependent parameter is then also automatically adjusted according to the chosen formula.

Consider for example a rectangular triangle with a hypotenuse of length 1, where the length of the other sides are the parameter A and B. When adjusting A the parameter B has to be adjusted accordingly to B = √(1 − A ∗ A). Also other parameters might depend on B, e.g. B_AREA = B ∗ B or TRIANGULAR_AREA = (A ∗ B)/2. This example is shown in listing 5.6.

A dependent parameter should not be adjustable by itself. The only way to influence its value is through the adjustment of a parameter it depends on.

Listing 5.6: Data Dependency
<PER-INSTANCE-PARAMETERS>
<PARAMETER-DATA-PROTOTYPE>
<SHORT-NAME>A</SHORT-NAME>
<DESC>
<L-2 L="DE">The independent Parameter</L-2>
</DESC>
<CATEGORY>VALUE</CATEGORY>
</PARAMETER-DATA-PROTOTYPE>
<PARAMETER-DATA-PROTOTYPE>
<SHORT-NAME>B</SHORT-NAME>
<DESC>
<L-2 L="DE">The dependent Parameter</L-2>
</DESC>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<SW-DATA-DEPENDENCY>
<SW-DATA-DEPENDENCY-FORMULA>SQRT( X1 * X1)</SW-DATA-DEPENDENCY-FORMULA>
<SW-DATA-DEPENDENCY-ARGS>
<AR-PARAMETER>
<LOCAL-PARAMETER-REF DEST="PARAMETER-DATA-PROTOTYPE">/DataDependency/foo/bar/A</LOCAL-PARAMETER-REF>
</AR-PARAMETER>
</SW-DATA-DEPENDENCY-ARGS>
</SW-DATA-DEPENDENCY>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</PARAMETER-DATA-PROTOTYPE>
<PARAMETER-DATA-PROTOTYPE>
<SHORT-NAME>B_AREA</SHORT-NAME>
<DESC>
<L-2 L="DE">The dependent Parameter</L-2>
</DESC>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<SW-DATA-DEPENDENCY>
<SW-DATA-DEPENDENCY-FORMULA>X1 * X1</SW-DATA-DEPENDENCY-FORMULA>
<SW-DATA-DEPENDENCY-ARGS>
<AR-PARAMETER>
<LOCAL-PARAMETER-REF DEST="PARAMETER-DATA-PROTOTYPE">/DataDependency/foo/bar/B</LOCAL-PARAMETER-REF>
</AR-PARAMETER>
</SW-DATA-DEPENDENCY-ARGS>
</SW-DATA-DEPENDENCY>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</PARAMETER-DATA-PROTOTYPE>
<PARAMETER-DATA-PROTOTYPE>
<SHORT-NAME>TRIANGULAR_AREA</SHORT-NAME>
<DESC>
<L-2 L="DE">The dependent Parameter</L-2>
</DESC>
<SW-DATA-DEF-PROPS>
<SW-DATA-DEF-PROPS-VARIANTS>
<SW-DATA-DEF-PROPS-CONDITIONAL>
<SW-DATA-DEPENDENCY>
<SW-DATA-DEPENDENCY-FORMULA>(X1 * X2) / 2</SW-DATA-DEPENDENCY-FORMULA>
<SW-DATA-DEPENDENCY-ARGS>
<AR-PARAMETER>
<LOCAL-PARAMETER-REF DEST="PARAMETER-DATA-PROTOTYPE">/DataDependency/foo/bar/A</LOCAL-PARAMETER-REF>
</AR-PARAMETER>
<AR-PARAMETER>
<LOCAL-PARAMETER-REF DEST="PARAMETER-DATA-PROTOTYPE">/DataDependency/foo/bar/B</LOCAL-PARAMETER-REF>
</AR-PARAMETER>
</SW-DATA-DEPENDENCY-ARGS>
</SW-DATA-DEPENDENCY>
</SW-DATA-DEF-PROPS-CONDITIONAL>
</SW-DATA-DEF-PROPS-VARIANTS>
</SW-DATA-DEF-PROPS>
</PARAMETER-DATA-PROTOTYPE>
</PER-INSTANCE-PARAMETERS>


Table 5.59: SwDataDependency
Table 5.60: SwDataDependencyArgs

#@SECTION: 5.4.7 Precedence of data properties with respect to data elements, axis elements, computation methods, units
#@CLASS: ApplicationDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: AutosarDataType
#@CLASS: SwAxisIndividual
#@CLASS: SwCalprmAxis
#@CLASS: SwCalprmAxisSet
#@CLASS: SwCalprmAxisTypeProps
#@CLASS: SwDataDefProps
#@ENUM: SwCalibrationAccessEnum
#@CLASS: DataConstr
#@CLASS: CompuMethod


There are similar attributes defined in SwDataDefProps as well as in SwCalprmAxis as well as in CompuMethod. Therefore we need to define which attribute value wins in the overall process from SWC-Description to MC-Support to ASAM-A2L.

Figure 5.35 illustrates the fact that some attributes in SwDataDefProps can also be expressed in subelements respectively in referenced elements.

[TPS_SWCT_01496] General precedence rule for attributes of SwDataDefProps (cid:100) The general precedence rule is that
• SwDataDefProps wins over valueAxisDataType (exception: compuMethod and unit).
• SwDataDefProps wins over compuMethod.
• SwDataDefProps wins over swCalprmAxisSet.
• SwDataDefProps.swCalprmAxisSet wins over swCalprmAxisSet.swCalprmAxis.swCalprmAxisTypeProps.compuMethod resp. SwAxisIndividual.inputVariableType.
• SwAxisIndividual.inputVariableType wins over SwAxisIndividual.compuMethod, SwAxisIndividual.unit, but not over SwAxisIndividual.dataConstr.
(cid:99)()

Figure 5.35: Various Attributes in the Context of SwDataDefProps

The following examples illustrate particular cases (the highest precedence comes first):
#@Hierarchical
• [TPS_SWCT_01497] Precedence of the unit of value axis (cid:100) For the usage of unit of value axis the following precedence rule is defined:
  - SwDataDefProps.valueAxisDataType.swDataDefProps.unit
  - SwDataDefProps.valueAxisDataType.swDataDefProps.compuMethod.unit
  - SwDataDefProps.unit
  - SwDataDefProps.compuMethod.unit
(cid:99)()

[constr_2550] Units of value axis shall be consistent (cid:100) The units specified in the context of value axis shall be the same, even if there is a precedence rule. (cid:99)()

In particular, [constr_2550] reflects the fact that unit may be specified in different phases of the development process but finally need to be consistent.

• [TPS_SWCT_01498] Precedence of the DataConstr of value axis (cid:100) For the usage of DataConstr of value axis the following precedence rule is defined:
  - SwDataDefProps.dataConstr
  - SwDataDefProps.valueAxisDataType.swDataDefProps.dataConstr
(cid:99)()

[constr_2548] Data constraint of value axis shall match (cid:100) The values compliant to SwDataDefProps.dataConstr shall be also be compliant to SwDataDefProps.valueAxisDataType.swDataDefProps.dataConstr. In other words SwDataDefProps.dataConstr win over but are not allowed to relax SwDataDefProps.valueAxisDataType.swDataDefProps.dataConstr but are not allowed (cid:99)()

• [TPS_SWCT_01499] Precedence of the CompuMethod of value axis (cid:100) For the usage of CompuMethod of value axis the following precedence rule is defined:
  - SwDataDefProps.valueAxisDataType.swDataDefProps.compuMethod
  - SwDataDefProps.compuMethod
(cid:99)()

• [TPS_SWCT_01500] Precedence of the display format of value axis (cid:100) For the usage of display format of value axis the following precedence rule is defined:
  - SwDataDefProps.displayFormat
  - SwDataDefProps.valueAxisDataType.swDataDefProps.displayFormat
  - SwDataDefProps.valueAxisDataType.swDataDefProps.compuMethod.displayFormat
  - SwDataDefProps.compuMethod.displayFormat
(cid:99)()

Note that this deviates from the general rule since displayFormat is not an essential property. The last item in the list above is the consequence of the fact that if there is a valueAxisDataType it supersedes the compuMethod

• [TPS_SWCT_01501] Precedence of the calibration access of value axis (cid:100) For the usage of calibration access of value axis the following precedence rule is defined:
  - SwDataDefProps.swCalibrationAccess
  - SwDataDefProps.valueAxisDataType.swDataDefProps.swCalibrationAccess
(cid:99)()

Note that this deviates from the general rule since swCalibrationAccess is not such an essential property.

• [TPS_SWCT_01502] Precedence of the Unit of the input axis (cid:100) For the usage of Unit of the input axis the following precedence rule is defined:
  - SwAxisIndividual.unit
  - SwAxisIndividual.compuMethod.unit
  - SwAxisIndividual.inputVariableType.swDataDefProps.unit
  - SwAxisIndividual.swVariableRef.autosarVariable.autosarVariable.type.swDataDefProps.compuMethod.unit
  - SwAxisIndividual.swVariableRef.autosarVariable.autosarVariable.type.swDataDefProps.unit
(cid:99)()

[constr_2549] Units of input axis shall be consistent (cid:100) The units specified in the context of an input axis shall be compatible, even if there is a precedence rule. (cid:99)()

[constr_2549] reflects the fact that unit may be specified in different phases of the development process but finally need to be consistent.

• [TPS_SWCT_01503] Precedence of the DataConstr of the input axis (cid:100) For the usage of DataConstr of the input axis the following precedence rule is defined:
  - SwAxisIndividual.dataConstr
  - SwAxisIndividual.inputVariableType.swDataDefProps.dataConstr
  - SwAxisIndividual.swVariableRef.type.swDataDefProps.dataConstr
(cid:99)()

Note that SwAxisIndividual.inputVariableType.swDataDefProps.dataConstr represent the input value, not the axis itself. For this reason there is no specific constraint that the dataConstr need to match.

• [TPS_SWCT_01504] Precedence of the display format of the input axis (cid:100) For the usage of display format of the input axis the following precedence rule is defined:
  - SwCalprmAxis.displayFormat
  - SwCalprmAxis.swCalprmAxisTypeProps.compuMethod.displayFormat
  - SwCalprmAxis.swCalprmAxisTypeProps.inputVariableType.swDataDefProps.displayFormat
  - SwCalprmAxis.swCalprmAxisTypeProps.inputVariableType.swDataDefProps.compuMethod.displayFormat
  - SwCalprmAxis.swCalprmAxisTypeProps.swVariableRef.type.swDataDefProps.displayFormat
  - SwCalprmAxis.swCalprmAxisTypeProps.swVariableRef.type.swDataDefProps.compumethod.displayFormat
(cid:99)()

Please note that SwAxisIndividual.inputVariableType.swDataDefProps.dataConstr represent the input value and not the axis itself. For this reason there is no specific constraint that displayFormat needs to match.

• [TPS_SWCT_01505] Precedence of calibration access along structure hierarchies in complex types (cid:100) For the usage of calibration access along structure hierarchies in complex types the precedence rule is defined in table 5.61. (cid:99)()
[
  {
    "outer": "notAccessible",
    "inner": "*",
    "result": "notAccessible"
  },
  {
    "outer": "readOnly",
    "inner": "readOnly",
    "result": "readOnly"
  },
  {
    "outer": "readOnly",
    "inner": "readWrite",
    "result": "readOnly"
  },
  {
    "outer": "readOnly",
    "inner": "notAccessible",
    "result": "notAccessible"
  },
  {
    "outer": "readWrite",
    "inner": "notAccessible",
    "result": "notAccessible"
  },
  {
    "outer": "readWrite",
    "inner": "readOnly",
    "result": "readOnly"
  },
  {
    "outer": "readWrite",
    "inner": "readWrite",
    "result": "readWrite"
  }
]
Table 5.61: Precedence of swCalibrationAccess along structure hierarchies

The interpretation of table 5.61 is it lists possible combinations of values of SwCalibrationAccessEnum for outer and inner elements of a complex data type and the (in the column "result") indicates value of SwCalibrationAccessEnum applicable for this specific combination.

• [TPS_SWCT_01506] Precedence of the calibration access of input axis (cid:100) For the usage of calibration access of input axis the following precedence rule is defined:
  - SwDataDefProps.swCalibrationAccess
  - SwCalprmAxis.swCalibrationAccess
(cid:99)()

Note that the swCalibrationAccess defined on a Compound Primitive Data Type (see [TPS_SWCT_01179]) reflects the entire curve or map. Therefore, if the entire curve or map cannot be accessed by the measurement calibration diagnostic system (MCD-System), the axis can also not be accessed. On the other hand it might be that access is granted for the value axis only but not for the axis points.
/#@Hierarchical

#@SECTION: 5.5 Elements used in Properties of Data Deﬁnitions
This section describes further elements which are attached to SwDataDefProps via associations.

#@SECTION: 5.5.1 Computation Methods
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: CompuConst
#@CLASS: CompuContent
#@CLASS: CompuMethod
#@CLASS: CompuNominatorDenominator
#@CLASS: CompuRationalCoeffs
#@CLASS: CompuScale
#@CLASS: CompuScaleConstantContents
#@CLASS: CompuScaleContents
#@CLASS: CompuScaleRationalFormula
#@CLASS: CompuScales
#@CLASS: PhysicalDimension
#@CLASS: Unit
#@CLASS: CompuConstTextContent
#@CLASS: Compu

[TPS_SWCT_01276] Computation methods (cid:100) An important part of semantics is the specification of a so-called computation method which specifies the conversion between the physical and the internal representation of data. This usually makes sense only for primitive data types. (cid:99)()

An ApplicationCompositeDataType cannot be given a particular semantic meaning as a whole but it is obviously possible to specify the semantics of all or a part of the contained elements, i.e. the ApplicationPrimitiveDataTypes.

Table 5.62: CompuMethod

This meta-class CompuMethod was actually taken from the ASAM standard's harmonized data objects. This is also indicated by the green color of the meta-classes in the diagram.

[constr_1142] category of CompuMethod shall not be extended (cid:100) In contrast to the general rule that category can be extended by user-specific values it is not allowed to extend the meaning of the attribute category of meta-class CompuMethod (cid:99)()

[TPS_SWCT_01277] Computation methods are used for the conversion of internal values into their physical representation and vice versa (cid:100) CompuMethods (see Figure 5.36) are used for the conversion of internal values into their physical representation and vice versa. The direction of the conversion depends on the origin of the value to be converted:

• If the value is provided by the ECU then the conversion direction is from internal to physical.
• If a physical value is provided by the tester it is converted to internal values before being sent to the ECU (cid:99)()

[TPS_SWCT_01548] Limits of a CompuMethod (cid:100) In case CompuScale.lowerLimit and CompuScale.upperLimit are used to constrain the applicable range of the conversion of a CompuMethod, they logically represent the limiting values before the conversion is applied. (cid:99)()

In other words, the limits are applied on the source end of the conversion rather than to the result that comes out at the other end of the conversion. This is obviously a lot safer than the opposite approach where a given physical/internal value would first be converted to its internal/physical equivalent and then, after the conversion is finished there would be (as a second step) the obligation to check whether the result of the conversion is actually valid in terms of the applicable limits.

[TPS_SWCT_01278] CompuMethods can also be used to assign symbolic names to internal values (cid:100) CompuMethods can also be used to assign symbolic names to internal values (like an enumeration in C) or to ranges of internal values or to single bits (like a bitfield in C). This is also considered as a conversion between internal numbers and a semantical representation. Some examples are given below. (cid:99)()

Figure 5.36: A CompuMethod and its attributes define data semantics

Figure 5.37: A CompuScale and its attributes define data semantics

[TPS_SWCT_01279] Preferred conversion direction depends on the use case (cid:100) The preferred conversion direction depends on the use case. The physical-to-internal direction is suitable for calibration while the internal-to-physical direction is preferred for diagnostic purposes. (cid:99)()

In the following, the internal-to-physical conversion direction is used as the default. Usually a CompuMethod is defined for one conversion direction only even if it is used in both directions.

For simple functions like identical (1:1 conversion) or linear functions this is sufficient because the inverse function can be derived quite easily from the defined function. In this case also the limits for the reverse direction can be gained by applying the forward function to the forward limits.

For more complex functions (e.g. rational functions) it is usually not possible to compute the inverse function automatically. More seriously, the inversion yields ambiguous results if the function is not monotonic. To deal with such possible ambiguities in a direct way an inverse value can be provided explicitly for the function or for each of its parts respectively.

[constr_1021] A CompuMethod shall specify instructions for both directions (cid:100) The forward and inverse direction shall always be clearly determined either by
• explicitly specifying both directions
• automatically inverting the CompuMethod if applicable (cid:99)()

[constr_1022] Limits shall be defined for each direction of CompuMethod (cid:100) In case that both domains are specified in the CompuMethod both shall have explicitly defined limits. (cid:99)()

[TPS_SWCT_01280] CompuMethod applied to values outside of its limits (cid:100) If a CompuMethod is applied to values outside of its limits, it is up to the MCD-tool (Measurement, Calibration, Diagnostic tool) to indicate this to the user. In this case the CompuMethod shall not be applied at all. (cid:99)()

[constr_1175] Depending on its category, CompuMethod shall refer to a unit (cid:100) As a CompuMethod specifies the conversion between the physical world and the numerical values they shall refer to a unit unless the CompuMethod's category is one of TEXTTABLE, BITFIELD_TEXTTABLE, or IDENTICAL. (cid:99)()

[constr_1175] does not imply that CompuMethods where the category is one of TEXTTABLE, BITFIELD_TEXTTABLE, or IDENTICAL are not allowed to refer to a unit. They may still refer to a unit, but according to [constr_1175] this relation is not mandated.

A further implication is that the unit itself may not have a dimension, i.e. all exponents of SI units are 0.

Figure 5.36 sketches a conceptual overview of CompuMethod. It consists of the following attributes:
#@Hierarchical
• [TPS_SWCT_01281] Unit associated with a PhysicalDimension (cid:100) A unit (described in next section) can be associated with a PhysicalDimension. (cid:99)()

Note that quantities like "%" are not derived from SI units. However, they have a meaning in the physical world and need to be represented in form of data types. Therefore, a CompuMethod also applies in those cases.

• [TPS_SWCT_01430] Conversion specification from internal to physical values as well as the reverse conversion (cid:100) A conversion specification from internal to physical values, as well as the reverse conversion. Both of them in turn consist of an abstract CompuContent. Derived classes allow the specification of a conversion formula in two different ways. (cid:99)()

[constr_1024] Stepwise definition of CompuMethods (cid:100) Within AUTOSAR only the stepwise definition (CompuScales) is used. (cid:99)()

• [TPS_SWCT_01282] Number of intervals in which a given conversion applies (cid:100)CompuScales is a number of intervals (called CompuScale) within which a certain conversion applies. The respective interval is given in terms of upper and lower limit. Limits are explained in more detail in chapter 5.2.4.1.

Within each CompuScale we have the abstract CompuScaleContents. To deal with possible ambiguities in a direct way an inverse value can be provided explicitly for that particular scale (compuInverseValue). (cid:99)()

• As the diagram shows, CompuScaleContents is an abstract meta-class. A number of derived meta-classes allow the specification of a conversion formula in a variety of ways, including:
  - mapping the whole interval to a constant (CompuConst)
  - providing rational coefficients of the conversion formula (CompuRationalCoeffs)

• [TPS_SWCT_01283] Rational function (cid:100)The rational function is specified as rational coefficients for the numerator (compuNumerator) and the denominator (compuDenominator). CompuNominatorDenominator can have as many V elements as needed for the rational function.

The sequence of the values V carries the information for the exponents, that means the first V is the coefficient for x0, the second V is the coefficient for x1, etc. With this sequence the values of the exponents can be entirely represented. (cid:99)()

[constr_1025] Avoid division by zero in rational formula (cid:100) The rational formula shall not yield any division by zero. (cid:99)()
/#@Hierarchical

[TPS_SWCT_01284] CompuScale might require a representation in the generated RTE C code (cid:100) A CompuScale might require a representation in the generated RTE C code. For this purpose it is necessary to identify a property that controls how to symbol used for the CompuScale in the C code is created. The symbol itself can be created out of different sources according to a standardized precedence schema. (cid:99)()

[TPS_SWCT_01569] Definition of CompuScale Symbolic Name (cid:100) In C code, a CompuScale is represented by an identifier that is, as far as AUTOSAR modeling is concerned, called a CompuScale Symbolic Name. The CompuScale Symbolic Name may be taken from CompuScale.symbol, CompuConstTextContent.vt, or CompuScale.shortLabel. The details are explained in [TPS_SWCT_01431]. (cid:99)()

[TPS_SWCT_01431] Finding the symbol for the representation of a CompuScale with a point-range in C code (cid:100) In general, the value of the attributes symbol, vt, and shortLabel can be taken as a the source for naming the symbol that represents the CompuScale in the C code. The following rule applies (lower values indicate higher priority) for all CompuScales with a point-range:
 1. Take the value of symbol if this attribute exists.
 2. Take the value of vt if it makes a valid C identifier.
 3. Take the value of shortLabel if it exists.
 Fail if none of the possible options apply. (cid:99)()

[constr_1133] Identical CompuScale Symbolic Names shall have the same range (cid:100) In a CompuMethod that is subject to [constr_1146], all CompuScales that yield identical CompuScale Symbolic Names shall have the same range defined by CompuScale.lowerLimit and CompuScale.upperLimit. (cid:99)()

[constr_1146] Applicability of a symbol for a CompuScale in C code (cid:100) The symbol attribute shall only be provided for CompuScales where the category of the enclosing CompuMethod is one of the following:
 • SCALE_LINEAR_AND_TEXTTABLE
 • SCALE_RATIONAL_AND_TEXTTABLE
 • TEXTTABLE
 • BITFIELD_TEXTTABLE (cid:99)()
Table 5.63: Compu
Table 5.64: CompuContent
Table 5.65: CompuScale
Table 5.66: CompuScales
Table 5.67: CompuScaleContents
Table 5.68: CompuRationalCoeffs
Table 5.69: CompuConst

[TPS_SWCT_01429] [constr_1135] only applies for BITFIELD_TEXTTABLE (cid:100) Note that [constr_1135] only applies for BITFIELD_TEXTTABLE. It does not apply to the definition of vt in the context of an ApplicationValueSpecification. (cid:99)()
Table 5.70: CompuScaleRationalFormula
Table 5.71: CompuScaleConstantContents
Table 5.72: CompuNominatorDenominator
Please note that the values of coefficients within a rational formula are not restricted
to integer values. It is possible to use floating point values as well.
The values of exponents cannot be set arbitrarily but are implicitly defined by the
appearance of coefficients in CompuNominatorDenominator.v, i.e. the first value in
the ordered list of CompuNominatorDenominator.v represents the exponent 0, the
second CompuNominatorDenominator.v represents the exponent 1, and so on.

#@SECTION: 5.5.1.1 Category Values in the context of a CompuMethod
#@CLASS: CompuMethod
#@CLASS: CompuScale
#@CLASS: CompuConst

For a detailed description of CompuMethods, please refer to the ASAM MCD 2 Harmonized Data Objects [23].

Table 5.73 contains a definition of possible values for the attribute category.
<--------------note:以下表格中有[constr_1134][constr_1135]两个约束>
Table 5.73: ASAM compuMethod
<-------------- multimodal context 


| ASAMCategory | Meaning | Specific properties |
|--------------|---------|-------------------|
| IDENTICAL | This CompuMethod just hands over the internal value with an optional unit. | Only the base elements are allowed and unit, physConstr and internalConstr are optional. This is the simplest type of a CompuMethod. |
| LINEAR | A linear conversion can be performed in two steps: The internal value is multiplied with a factor; after that, an offset is added to the result of the multiplication. | Exactly one CompuScale, with two v in compuNumerator and one v in compuDenominator. |
| SCALE_LINEAR | Used for a piecewise linear conversion | More than one compuScale can be defined. Additionally there have to be the upperLimit and lowerLimit elements which define the region of validity for the linear function. The boundaries of the regions shall not overlap. |
| SCALE_LINEAR_AND_TEXTTABLE | Used for piecewise definition of one linear and several text table scales. | Properties depend on the used scale function. For details see definition of SCALE_LINEAR and TEXTTABLE. The scales shall each provide lowerLimit and upperLimit definitions. |
| RAT_FUNC | The rational function type is similar to the linear type without the restrictions for the compuNumerators and compuDenominators. | It can have as many v elements as needed for the rational function. The sequence of the values v carries the information for the exponents, that means the first v is the coefficient for x⁰, the second v is the coefficient for x¹, etc. With this sequence the values of the exponents can be entirely represented. A rational function is only applicable for conversions in the direction that it is defined for, i.e. the automatic calculation of the inverse function is not supported by the MCD system. |
| SCALE_RAT_FUNC | Used for piecewise defined rational conversion. | |
| SCALE_RATIONAL_AND_TEXTTABLE | Used for piecewise definition of one rational and several text table scales. | Properties depend on the used scale function. For details see definition of SCALE_RAT_FUNC and TEXTTABLE. The scales shall each provide lowerLimit and upperLimit definitions. |
| TEXTTABLE | The type TEXTTABLE is used for transformations of the internal value into textual elements. | [constr_1134] Allowed structure of TEXTTABLE  (cid:100) physConstr is not allowed. compuInternalToPhys  shall exist with compuScales consisting of upperLimit and lowerLimit.(cid:99)() The result is placed in the vt member of CompuConst. The compuDefaultValue is optional. If the reverse calculation is needed then for each scale the compuInverseValue can be used to define the reverse calculation result. If no inverse value is explicitly defined then the smallest possible value of the scale will be used as result of the reverse calculation. |
| TAB_NOINTP | Similar to TEXTTABLE, but for numerical values. | The values per scale are defined in CompuConst. |
| BITFIELD_TEXTTABLE | Similar to TEXTTABLE but for bitfields | BITFIELD_TEXTTABLE is derived from TEXTTABLE. The main difference is that TEXTTABLE results to a single value while BITFIELD_TEXTTABLE results to a concatenated value set. [constr_1135] Limit of vt in BITFIELD_TEXTTABLE (cid:100) The separator is “|” and is forbidden in vt therefore.(cid:99)() In difference to all the other computational methods every CompuScale will be applied including the bit mask specified in mask. Therefore it is allowed for this type of CompuMethod, that CompuScales overlap. To calculate the string reverse to a value, the string has to be split and the according value for each substring has to be summed up. The sum is finally transmitted.The processing has to be done in order of the CompuScale elements. |
------------------------>

#@SECTION: 5.5.1.2 Applicability of Attributes in the context of a CompuMethod
#@CLASS: CompuConst
#@CLASS: CompuMethod
#@CLASS: CompuRationalCoeffs
#@CLASS: CompuScale

This section summarizes the applicability of CompuMethod in terms of which attributes of CompuMethod and related meta-classes (e.g. CompuScale, CompuConst) shall be used depending on the nature of the CompuMethod, expressed by means of the value of attribute category.

[constr_1375] Existence of attributes of CompuMethod and related meta-classes (cid:100) The existence of attributes of CompuMethod and related meta-classes depending on the value of the category shall follow the restrictions documented in Table 5.74. (cid:99)()

For clarification, the first two rows of Table 5.74 define the applicability of the immediate attributes of meta-class CompuMethod, the remainder of the table then goes into further detail regarding the usage of the attributes of related meta-classes (e.g. CompuScale, CompuConst).

Please note that annotations apply to the individual cell values. These annotations are formulated by means of a numerical value in parentheses, e.g. (1). The legend for the individual annotations can be found below Table 5.74.

Table 5.74: Allowed Attributes vs. category for CompuMethods
<-------------- multimodal context 

### Attributes of CompuMethod

| Attributes | Attribute Existence per Category |  |  |  |  |  |  |  |  |  |
|------------|------------------------------|--|--|--|--|--|--|--|--|--|
|  | IDENTICAL | LINEAR | SCALE_LINEAR | RAT_FUNC | SCALE_RAT_FUNC | TEXTTABLE | BITFIELD_TEXTTABLE | SCALE_LINEAR_AND_TEXTTABLE | SCALE_RATIONAL_AND_TEXTTABLE | TAB_NOINTP |
| compuInternalToPhys | N/A | D(1) | D(1) | D(2) | D(2) | D | D | D(8) | D(2) | D |
| compuPhysToInternal | N/A | D | D | D(2) | D(2) | N/A | N/A | N/A | D(2,3) | N/A |

### Attributesofmeta-classesrelatedtoCompuMethod

| Attributes | AttributeExistenceperCategory |  |  |  |  |  |  |  |  |  |
|------------|------------------------------|--|--|--|--|--|--|--|--|--|
|  | IDENTICAL | LINEAR | SCALE_LINEAR | RAT_FUNC | SCALE_RAT_FUNC | TEXTTABLE | BITFIELD_TEXTTABLE | SCALE_LINEAR_AND_TEXTTABLE | SCALE_RATIONAL_AND_TEXTTABLE | TAB_NOINTP |
| compuDefaultValue | N/A | O(6) | O(6) | O(6) | O(6) | O(6) | O(6) | O(6) | O(6) | O(6) |
| CompuScale | N/A | D/1..1 | D/1..n | D/1..1 | D/1..n | D/1..n | D/1..n | D/1..n | D/1..n | D/1..n |
| CompuScale.compuInverseValue | N/A | N/A | N/A | O(2) | O(2) | O(5) | N/A | O(2,5) | O(2,5) | O(5) |
| CompuScale.lowerLimit | N/A | O | D | D(4) | D(4) | D | D | D | D(4) | D |
| CompuScale.mask | N/A | N/A | N/A | N/A | N/A | N/A | D | N/A | N/A | N/A |
| CompuScale.shortLabel | N/A | N/A | N/A | N/A | N/A | O(7) | O(7) | O(7) | O(7) | N/A |
| CompuScale.symbol | N/A | N/A | N/A | N/A | N/A | O(7) | O(7) | O(7) | O(7) | N/A |
| CompuScale.upperLimit | N/A | O | D | D(4) | D(4) | D | D | D | D(4) | D |
| CompuConst | N/A | N/A | N/A | N/A | N/A | D/vt | D/vt | D/vt | D/vt | D/vt or vf |
| CompuRationalCoeffs | N/A | D | D | D | D | N/A | N/A | D | D | N/A |
| CompuRationalCoeffs.compuDenominator | N/A | D/1v | D/1v | D | D | N/A | N/A | D/1v | D | N/A |
| CompuRationalCoeffs.compuDenominator | N/A | D/2v | D/2v | D | D | N/A | N/A | D/2v | D | N/A |
------------------------>

The following legend applies to the cells in table 5.74: 
D Define the attribute. 
N/A Attribute is not applicable for usage in the scope of this element. 
O Optionally define the attribute.

In addition to the primary cell legend the following annotations apply to the cells in table 5.74:
(1) This applies if not already defined by compuPhysToInternal. 
(2) In this case both compuPhysToInternal and compuInternalToPhys shall be defined (according to [constr_1021]) unless compuInverseValue exists (see [TPS_SWCT_01282]). In other words, if the explicit definition of a compuInverseValue exists then there is no need to define conversions from internal to physical and vice versa. 
(3) Not applicable for CompuScales where attribute compuScaleContents.compuConst exists. 
(4) Limits shall be defined according to [constr_1022]. 
(5) Restrictions on the structure of the CompuMethod according to [constr_1134] apply. 
(6) Specify an output value for a conversion formula if the value to be converted yields outside the plausibility limit (for more information, please refer to the class table of Compu). 
(7) Restricted applicability for the attribute CompuScale.symbol, see [constr_1146]). 
(8) Mandatory for CompuConst; enforced for CompuRationalCoeffs.

#@SECTION: 5.5.1.3 Example for Enumeration
#@CLASS: CompuMethod

The following example illustrates how an enumeration is specified using CompuMethod.

Listing 5.7: example for enumeration

<COMPU-METHOD>
<SHORT-NAME>boolean</SHORT-NAME>
<CATEGORY>TEXTTABLE</CATEGORY>
<COMPU-INTERNAL-TO-PHYS>
<COMPU-SCALES>
<COMPU-SCALE>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0</UPPER-LIMIT>
<COMPU-CONST>
<VT>false</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">1</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">1</UPPER-LIMIT>
<COMPU-CONST>
<VT>true</VT>
</COMPU-CONST>
</COMPU-SCALE>
</COMPU-SCALES>
</COMPU-INTERNAL-TO-PHYS>
</COMPU-METHOD>

#@SECTION: 5.5.1.4 Example for Linear Conversion
#@CLASS: CompuMethod

The following examples illustrates how a linear conversion is specified using CompuMethod.

F[kmh] = 30[kmh] + 2[kmh] ∗ x

Listing 5.8: example for linear CompuMethod

<COMPU-METHOD>
<SHORT-NAME>linear</SHORT-NAME>
<CATEGORY>LINEAR</CATEGORY>
<UNIT-REF DEST="UNIT">kmh</UNIT-REF>
<COMPU-INTERNAL-TO-PHYS>
<COMPU-SCALES>
<COMPU-SCALE>
<COMPU-RATIONAL-COEFFS>
<COMPU-NUMERATOR>
<V>30</V>
<V>2</V>
</COMPU-NUMERATOR>
<COMPU-DENOMINATOR>
<V>1</V>
</COMPU-DENOMINATOR>
</COMPU-RATIONAL-COEFFS>
</COMPU-SCALE>
</COMPU-SCALES>
</COMPU-INTERNAL-TO-PHYS>
</COMPU-METHOD>

#@SECTION: 5.5.1.5 Example for Linear Conversion with texttable
#@CLASS: CompuMethod

The following example illustrates how a linear conversion with a texttable is specified using CompuMethod.

Listing 5.9: example for linear and texttable CompuMethod

<COMPU-METHOD>
<SHORT-NAME>linear</SHORT-NAME>
<CATEGORY>SCALE_LINEAR_AND_TEXTTABLE</CATEGORY>
<UNIT-REF DEST="UNIT">kmh</UNIT-REF>
<COMPU-INTERNAL-TO-PHYS>
<COMPU-SCALES>
<COMPU-SCALE>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">300</UPPER-LIMIT>
<COMPU-RATIONAL-COEFFS>
<COMPU-NUMERATOR>
<V>30</V>
<V>2</V>
</COMPU-NUMERATOR>
<COMPU-DENOMINATOR>
<V>1</V>
</COMPU-DENOMINATOR>
</COMPU-RATIONAL-COEFFS>
</COMPU-SCALE>
<COMPU-SCALE>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">350</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">350</UPPER-LIMIT>
<COMPU-CONST>
<VT>SensorError</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">351</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">351</UPPER-LIMIT>
<COMPU-CONST>
<VT>SignalNotAvailable</VT>
</COMPU-CONST>
</COMPU-SCALE>
</COMPU-SCALES>
</COMPU-INTERNAL-TO-PHYS>
</COMPU-METHOD>

#@SECTION: 5.5.1.6 Example for conversion speciﬁed by a rational function
The semantics of rational function is: 
Internal = (v0*phys0+v1*phys1+v2*phys2+...)/(v0*phys0+v1*phys1+v2*phys2+...)

The following example illustrates a reciprocal conversion. 
I = 1000 /(60+2[K-1]*P[K])

Listing 5.10: example for rational CompuMethod
<COMPU-METHOD>
<SHORT-NAME>rational</SHORT-NAME>
<CATEGORY>RAT_FUNC</CATEGORY>
<UNIT-REF DEST="UNIT">Kelvin</UNIT-REF>
<COMPU-PHYS-TO-INTERNAL>
<COMPU-SCALES>
<COMPU-SCALE>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">-29</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="OPEN">INF</UPPER-LIMIT>
<COMPU-RATIONAL-COEFFS>
<COMPU-NUMERATOR>
<V>1000</V>
</COMPU-NUMERATOR>
<COMPU-DENOMINATOR>
<V>60</V>
<V>2</V>
</COMPU-DENOMINATOR>
</COMPU-RATIONAL-COEFFS>
</COMPU-SCALE>
</COMPU-SCALES>
</COMPU-PHYS-TO-INTERNAL>
</COMPU-METHOD>

#@SECTION: 5.5.1.7 Example for BITFIELD_TEXTTABLE
#@CLASS: CompuConstNumericContent
#@CLASS: CompuConstTextContent
#@CLASS: CompuScaleContents
#@CLASS: CompuMethod
#@CLASS: CompuScale

The following example shows how a CompuMethod of category BITFIELD_TEXTTABLE can be used to assign a special meaning to each bit of an AutosarDataType of category VALUE:


<-------------- multimodal context 
```markdown
| Bit      | Description  | Encoding                                                                 |
|----------|--------------|--------------------------------------------------------------------------|
| Bit 0    | front left   | 0(0) = no, 1(1) = yes                                                    |
| Bit 2    | rear left    | 0(0) = no, 1(4) = yes                                                    |
| Bit 3    | rear right   | 0(0) = no, 1(8) = yes                                                    |
| Bit 4-5  | problem      | 00(0) = flat tire  <br> 01(16) = low pressure  <br> 10(32) = unbalanced  <br> 11(48) = unknown |
| All Bits | error        | 11111111 = invalid value                                                 |
``` ---------------------->
Table 5.75: Example Bitfield

Note that this example is somehow tricky. Bit 6+7 are not used for valid data, but are part of the mask. By this the error can safely be masked out.

Internal: 28
28 = 0b0001_1100
Bit  7654 3210

Physical: "problem = low pressure | rear right = yes | rear left = yes | front right = no | front left = no"

Listing 5.11: example for bit field text table CompuMethod

<COMPU-METHOD>
<SHORT-NAME>Texttable</SHORT-NAME>
<CATEGORY>BITFIELD_TEXTTABLE</CATEGORY>
<COMPU-INTERNAL-TO-PHYS>
<COMPU-SCALES>
<!-- problem -->
<COMPU-SCALE>
<SHORT-LABEL>problem</SHORT-LABEL>
<SYMBOL>problem_flat_tire</SYMBOL>
<MASK>0b11110000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</UPPER-LIMIT>
<COMPU-CONST>
<VT>flat tire</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>problem</SHORT-LABEL>
<SYMBOL>problem_low_pressure</SYMBOL>
<MASK>0b11110000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00010000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00010000</UPPER-LIMIT>
<COMPU-CONST>
<VT>low pressure</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>problem</SHORT-LABEL>
<SYMBOL>problem_unbalanced</SYMBOL>
<MASK>0b11110000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00100000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00100000</UPPER-LIMIT>
<COMPU-CONST>
<VT>unbalanced</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>problem</SHORT-LABEL>
<SYMBOL>problem_unknown</SYMBOL>
<MASK>0b11110000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00110000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00110000</UPPER-LIMIT>
<COMPU-CONST>
<VT>unknown</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>problem</SHORT-LABEL>
<SYMBOL>problem_invalid</SYMBOL>
<MASK>0b11110000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b11110000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b11110000</UPPER-LIMIT>
<COMPU-CONST>
<VT>invalid</VT>
</COMPU-CONST>
</COMPU-SCALE>
<!-- rear right -->
<COMPU-SCALE>
<SHORT-LABEL>rearRight</SHORT-LABEL>
<SYMBOL>rearRight_no</SYMBOL>
<MASK>0b11001000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</UPPER-LIMIT>
<COMPU-CONST>
<VT>no</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>rearRight</SHORT-LABEL>
<SYMBOL>rearRight_yes</SYMBOL>
<MASK>0b11001000</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00001000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00001000</UPPER-LIMIT>
<COMPU-CONST>
<VT>yes</VT>
</COMPU-CONST>
</COMPU-SCALE>
<!-- rear left -->
<COMPU-SCALE>
<SHORT-LABEL>rearLeft</SHORT-LABEL>
<SYMBOL>rearLeft_no</SYMBOL>
<MASK>0b11000100</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</UPPER-LIMIT>
<COMPU-CONST>
<VT>no</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>rearLeft</SHORT-LABEL>
<SYMBOL>rearLeft_yes</SYMBOL>
<MASK>0b11000100</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000100</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000100</UPPER-LIMIT>
<COMPU-CONST>
<VT>yes</VT>
</COMPU-CONST>
</COMPU-SCALE>
<!-- front right -->
<COMPU-SCALE>
<SHORT-LABEL>frontRight</SHORT-LABEL>
<SYMBOL>frontRight_no</SYMBOL>
<MASK>0b11000010</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</UPPER-LIMIT>
<COMPU-CONST>
<VT>no</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>frontRight</SHORT-LABEL>
<SYMBOL>frontRight_yes</SYMBOL>
<MASK>0b11000010</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000010</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000010</UPPER-LIMIT>
<COMPU-CONST>
<VT>yes</VT>
</COMPU-CONST>
</COMPU-SCALE>
<!-- front left -->
<COMPU-SCALE>
<SHORT-LABEL>frontLeft</SHORT-LABEL>
<SYMBOL>frontLeft_no</SYMBOL>
<MASK>0b11000001</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000000</UPPER-LIMIT>
<COMPU-CONST>
<VT>no</VT>
</COMPU-CONST>
</COMPU-SCALE>
<COMPU-SCALE>
<SHORT-LABEL>frontLeft</SHORT-LABEL>
<SYMBOL>frontLeft_yes</SYMBOL>
<MASK>0b11000001</MASK>
<LOWER-LIMIT INTERVAL-TYPE="CLOSED">0b00000001</LOWER-LIMIT>
<UPPER-LIMIT INTERVAL-TYPE="CLOSED">0b00000001</UPPER-LIMIT>
<COMPU-CONST>
<VT>yes</VT>
</COMPU-CONST>
</COMPU-SCALE>
</COMPU-SCALES>
</COMPU-INTERNAL-TO-PHYS>
</COMPU-METHOD>

Note that a constraint applies concerning the values within a CompuMethod that is subject to [constr_1146]. According to [constr_1133], it is (as exemplified in the example) required that if a specific CompuScale Symbolic Name appears more than once in the context of the CompuMethod then the values of CompuScale.lowerLimit shall be identical for all affected CompuScales and the values of CompuScale.upperLimit shall also be identical for all affected CompuScales.

Table 5.76: CompuScaleContents

Table 5.77: CompuConstTextContent

Table 5.78: CompuConstNumericContent

#@SECTION: 5.5.2 Physical Units, Physical Dimensions and Unit Groups
#@CLASS: PhysicalDimension
#@CLASS: PhysicalDimensionMapping
#@CLASS: PhysicalDimensionMappingSet
#@CLASS: Unit
#@CLASS: UnitGroup
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: SwDataDefProps
#@CLASS: PhysConstrs
#@CLASS: PhysConstrs

[TPS_SWCT_01285] Physical dimension (cid:100) Another important part of the semantics associated with a data type is its physical dimension. Units are used to augment the value with additional information like m/s or liter. This is necessary for a correct interpretation of the physical value for input and output processes. The conversion of values into other units like km/h into miles/h is also possible. Therefore the unit involves information about its physical dimensions. (cid:99)()

[TPS_SWCT_01056] Physical dimension (cid:100) The substructure of physical dimensions defines all used quantities in the SI-System (e.g. velocity as length/time corresponds to m/s). (cid:99)(RS_SWCT_02100)

For the deﬁnition of what SI units are, see http://physics.nist.gov/cuu/Units/

[TPS_SWCT_01057] Unit references one physical dimension (cid:100) The unit references one physical dimension. If the physical dimensions of two units are identical, a conversion between them is basically possible. (cid:99)(RS_SWCT_02100)

[TPS_SWCT_01058] UnitGroup (cid:100) The UnitGroups determine if such a conversion is appropriate. (cid:99)(RS_SWCT_02100)

Figure 5.38: Definition of SI based units

For a detailed description of these elements please refer to the [23]. Standard units are already predeﬁned for AUTOSAR in form of a description ﬁle.

Table 5.79: Unit

[TPS_SWCT_01059] Exponent for each of the seven fundamental dimensions (cid:100) For basing a new unit directly upon SI units an exponent for each of the seven fundamental dimensions and its corresponding SI unit needs to be speciﬁed. (cid:99)(RS_SWCT_02100)

[TPS_SWCT_01060] Negative exponents (cid:100) Negative exponents are allowed. (cid:99)(RS_SWCT_02100) Note that quantities like "%" are not derived from SI units and therefore have no association to a physical dimension.

Note that quantities like "%" are not derived from SI units and therefore have no association to a physical dimension.

Table 5.80: PhysicalDimension

AUTOSAR provides the ability to map two PhysicalDimensions onto each others with the implication that the two mapped PhysicalDimensions shall be considered compatible (for more explanation please refer to [constr_1053]). PhysicalDimensionMappings are aggregated in form of PhysicalDimensionMappingSets. This allows for gathering semantically related PhysicalDimensionMappings into the same PhysicalDimensionMappingSet.

Figure 5.39: Modeling of PhysicalDimensionMapping
Table 5.81: PhysicalDimensionMappingSet
Table 5.82: PhysicalDimensionMapping

[constr_1026] Compatibility of Units (cid:100) For data types or prototypes, units should be referenced from within the associated CompuMethod. But if it is referenced from within SwDataDefProps and/or PhysConstrs (for exceptional use cases) it shall be compatible (for more details please refer to [constr_1052]) to the ones referenced from the referred CompuMethod. (cid:99)()

Please note that for the sake of model consistency, it is also possible to deﬁne a meaningless Unit for all the pieces of data that conceptually do not really have a Unit attached to them (e.g. ApplicationPrimitiveDataTypes of category BOOLEAN). By looking at the model, it becomes clear that the subject of whether or not to assign a Unit has been given a thought and the lack of a Unit is not simply the result of an oversight. For example, the AUTOSAR Application Interfaces [24] deﬁne the Unit NoUnit for exactly this purpose.

[constr_1255] ApplicationPrimitiveDataTypes of category BOOLEAN and STRING (cid:100) If a Unit is referenced from within SwDataDefProps and/or PhysConstrs owned by an ApplicationPrimitiveDataTypes of category BOOLEAN and STRING it is required that this Unit represents a meaningless unit, i.e. the referenced physicalDimension shall not deﬁne any exponent value other than 0. (cid:99)()

Table 5.83: UnitGroup

[TPS_SWCT_01068] Units can be grouped with the help of UnitGroup (cid:100) Units can be grouped with the help of UnitGroup. This grouping is intended as a logical grouping which allows for example an MCD (Measurement Calibration Diagnostic) device to present different unit systems to the user such that he can chose the most appropriate one. (cid:99)(RS_SWCT_02100)

Figure 5.40: Relation of SwComponentType to UnitGroup

The association from SwComponentType to UnitGroup (beside the obvious use case to allow for the speciﬁcation of unitGroups relevant for the enclosing SwComponentType in particular) is supposed to support the identiﬁcation of UnitGroups relevant for the enclosing System. This aspect facilitates the creation of ASAM MCD2 ﬁles for a concrete ECU. 
According to [23] the following three values for categorys are recommended in the context of UnitGroup: • COUNTRY collects units which are common in a particular country, denoted by the shortName / longName of the UnitGroup • CALCULATION refers to speciﬁc units intended for the creation of data types. In this category of UnitGroup, several Units may refer to the same PhysicalDimension as well as to different PhysicalDimension. • EQUIV_UNITS deﬁne a group of equivalent units, which are used for example in different countries. Additional values for category may be mutually agreed between the stakeholders. In the example shown in Figure 5.41, Units are classiﬁed by country and use.

[TPS_SWCT_01061] Conversion of units (cid:100) If a unit has to be converted according to the chosen country code the physicalDimension of both units shall be the same. If another unit shares the same UnitGroup with a category of EQUIV_UNITS it is preferred as target of the conversion. (cid:99)(RS_SWCT_02100) 

Assume "MilesPerHour" should be converted to a European unit: Based on the physicalDimension a conversion to "MeterPerSec" as well as "MilesPerHour" is possible. In this case "KmPerHour" is preferred because "MilesPerHour" and "KmPerHour" are both members of the UnitGroup named "VehicleSpeed". In contrast to this "MeterPerSec" is not considered as appropriate for "VehicleSpeed".


<-------------- multimodal context 
This diagram defines an AUTOSAR‐style unit conversion scheme by grouping country identifiers and equivalent measurement units, and binding a VehicleSpeed data prototype to one of those units. It shows how base “units” (Eu, USA) map to metric/imperial units, and how a signal’s DataPrototype refers to a specific unit via these groups.

- Component hierarchy  
  • UnitGroup(Category=“COUNTRY”) contains Units Eu and USA  
  • UnitGroup(Category=“EQUIV_UNITS”) contains Units Km, KmPerHour, MilesPerHour, MeterPerSec  
  • ApplicationDataPrototype VehicleSpeed linked to a Unit  

- Ports & interfaces  
  • No explicit RPort/PPort; units act as DataType elements  
  • DataPrototype VehicleSpeed uses the DataInterface defined by KmPerHour  

- Data flow  
  • Arrows denote derivation/mapping relationships:  
    – Eu → Km, KmPerHour, MeterPerSec  
    – USA → MilesPerHour  
  • VehicleSpeed ← KmPerHour  

- Key AUTOSAR concepts  
  • UnitGroup and Unit as specializations of ApplicationDataType  
  • ApplicationDataPrototype referencing a Unit  
  • Implicit DataTypeMapping between country identifiers and equivalent units  

- Scenario  
  • Enable multi-region support by converting country‐specific units into a common set of equivalent measurement units and binding physical signals (e.g., VehicleSpeed) to those units. ---------------------->
Figure 5.41: Example for units and unit groups

#@SECTION: 5.5.3 Data Constraints
#@CLASS: DataConstr
#@CLASS: DataConstrRule
#@CLASS: InternalConstrs
#@CLASS: PhysConstrs
#@CLASS: ScaleConstr
#@ENUM: ScaleConstrValidityEnum
#@CLASS: Limit
#@ENUM: MonotonyEnum
#@ENUM: IntervalTypeEnum
#@CLASS: ARElement
#@CLASS: ImplementationDataType
#@CLASS: ApplicationDataType
#@CLASS: AbstractNumericalVariationPoint


Section 5.2.4.1 already shows an example on how to define constraints for the physical range of a data type, see Figure 5.4.

[TPS_SWCT_01286] DataConstr (cid:100) In general, the meta-class DataConstr can be aggregated (via SwDataDefProps.dataConstr) to define various constraints for the possible values of a data type. This includes limits for the physical and internal range, as well as special constraints (monotony) for the setup of axis definition. (cid:99)()

Figure 5.42 and the following class tables show the meta-classes involved in the definition of constraints.

A more detailed documentation of these meta-classes can be found in in [23]. As refinement of these definitions, the following values apply for constrLevel:

[constr_2561] Application of DataConstrRule.constrLevel (cid:100) DataConstrRule.constrLevel is limited to 
0: This represents so called "hard limits". They shall always be specified. 
1: This represents so called "soft limits". Soft limits may be violated after confirmation by the user of an MCD-System. 
Other values may exist, but the semantics is outside of the AUTOSAR scope. (cid:99)()

[TPS_SWCT_01287] Standard limits and extended limits in the ASAM-MCD2 (ASAP2) specification (cid:100) The ASAM-MCD2 (ASAP2) specification [25] defines standard limits and extended limits. If extended limits exist, the standard limits may be violated upon user confirmation. Note that in consequence, of this definition, the following approach applies for A2L generation:
• If only one DataConstrRule with constrLevel set to 0 is specified, it represents the standard limits in A2L. No extended limits are generated.
• If two DataConstrRule exist, then:
  - the one with constrLevel set to 0 represents to the extended limits
  - the one with constrLevel set to 1 represents to the standard limits
Note that even if this is somehow counterintuitive (since the one with constrLevel set to 0 changes its role), it matches the best to the definitions in ASAM-MCD2. (cid:99)()

Figure 5.42: Meta-model for defining Data Constraints
Table 5.84: DataConstr
Table 5.85: DataConstrRule
Table 5.86: PhysConstrs
Table 5.87: InternalConstrs
Table 5.88: ScaleConstr
Table 5.89: ScaleConstrValidityEnum
Table 5.90: Limit
Table 5.91: MonotonyEnum

[TPS_SWCT_01288] Interpretation of PhysConstrs and InternalConstrs by tools (cid:100) DataConstr is an ARElement which can be reused by several data type specifications. Especially an ImplementationDataType and an ApplicationDataType which are mapped to each other, can refer to the same constraints or they can define their own constraints. To avoid conflicts, in both cases PhysConstrs shall be interpreted by tools only with respect to application data types while InternalConstrs shall be interpreted only with respect to implementation data types. If either a physical or internal constraint is missing an existing CompuMethod can be used to calculate the missing information. (cid:99)()

[TPS_SWCT_01289] Semantics of Limit (cid:100) Technically, a Limit specifies a boundary of the interval of valid values for a given context (i.e. a data type). Please note that the boundary might or might not be part of the interval itself, i.e. the interval might be open or closed. From the formal point of view, the range represents all real numbers defined by: 
range = {𝑥 ∈ ℝ || lowerLimit.value < 𝑥 < upperLimit.value}
        ∪ {lowerLimit.value || lowerLimit.intervalType == "CLOSED"}
        ∪ {upperLimit.value || upperLimit.intervalType == "CLOSED"}
(cid:99)()

Please note that Limit inherits from AbstractNumericalVariationPoint. This means it is a number which may be subject to variability. For this reason, it is not possible to constrain the content already in the xml schema.

[constr_1191] Value of Limit shall yield a numerical value (cid:100) After all variability is bound, the content obtained from a limit shall yield a numerical value. (cid:99)()

Nevertheless it is not possible to distinguish on this level between float and integer values. Consequently [constr_1191] will not take the burden from an AUTOSAR tool to decide whether or not the value provided as a limit actually makes sense in any of the given contexts.
Table 5.92: IntervalTypeEnum

#@SECTION: 5.5.4 Addressing Methods
#@CLASS: DataPrototype
#@CLASS: MemoryAllocationKeywordPolicyType
#@CLASS: MemorySectionType
#@CLASS: RunnableEntity
#@CLASS: SectionInitializationPolicyType
#@CLASS: SwAddrMethod
#@CLASS: SwComponentPrototype
#@CLASS: VariableDataPrototype
#@CLASS: MemorySection
#@CLASS: Implementation
#@CLASS: BswSchedulableEntity
#@CLASS: AlignmentType

In an ECU there might be various methods to access a particular object (e.g measurement or calibration parameter) according to a given address. This variety might come from different kind of memory (near, far, . . .) but also from indirections which are introduced by the compiler.

[TPS_SWCT_01290] SwAddrMethod (cid:100) In order to allow a measurement and calibration system to access such objects SwAddrMethods are specified. Another purpose of this feature is to support the definition of abstract memory sections, i.e. to specify which variables shall be put together in the same sections in case of generated code (especially for data allocated by the RTE).

SwAddrMethod will be used to group data, for example, to cover the fact that sometimes it is required that one or more calibration parameters out of the overall collection of calibration parameters of a SwComponentPrototype respectively an AUTOSAR software component shall be placed in another memory location than the other parameters of the SwComponentPrototype respectively the AUTOSAR software component. (cid:99)()

[TPS_SWCT_01291] Association of MemorySection with SwAddrMethod (cid:100) In Implementation the particular MemorySection is associated with the SwAddrMethod. This association indicates that all objects of the associated addressing method shall be placed in the given memory section. (cid:99)()

[TPS_SWCT_01456] Predefined values for MemorySection.option and SwAddrMethod.option (cid:100) The following values of MemorySection.option and SwAddrMethod.option are predefined by AUTOSAR:

resetSafe This corresponds to variables of ECU-functions which values shall endure a ECU reset.

protected This corresponds to variables, constants, and code which shall not be accessible and modifiable from the outside without a security mechanism.

offline This corresponds to calibration parameters which shall not be modifiable during ECU operation.

coreGlobal This corresponds to variables, constants, and code which have to be accessible by any core in case of multi-core ECUs.

coreLocal This corresponds to variables, constants, and code which have to be accessible by one core in case of multi-core ECUs.

nvData This corresponds to variables of ECU-functions which shall be stored in non-volatile data. This option is applicable for memory used as a RAM Block managed by the NvM.

safetyQM This corresponds to variables, constants, and code without any safety integrity level and therefore having a QM rating.

safetyAsilA This corresponds to variables, constants, and code with the safety integrity level A.

safetyAsilB This corresponds to variables, constants, and code with the safety integrity level B.

safetyAsilC This corresponds to variables, constants, and code with the safety integrity level C.

safetyAsilD This corresponds to variables, constants, and code with the safety integrity level D.

(cid:99)()

Obviously, the multiplicity of both the attribute MemorySection.option and SwAddrMethod.option allows for the appearance of more than one value. For example, a combination of the values resetSafe, protected, and safetyAsilC makes perfect sense on a particular list and can be used to express a meaning that combines the semantics of both values with each other.

However, this combination of values is not arbitrarily possible. It is therefore necessary to formulate a constraint that regulates the appearance of the safety-related values mentioned in [TPS_SWCT_01456].

In other words, it would not make any sense to attribute a given memory object with two different ASIL [26] values appearing on the same list.

If these values were combined on a particular list, the intended semantics would be ambiguous and could not clearly be determined. Therefore, [constr_1311] applies.

[constr_1311] Appearance of safety-related possible values of MemorySection.option or SwAddrMethod.option according to [TPS_SWCT_01456] (cid:100) Any given list of values stored in the attributes MemorySection.option or SwAddrMethod.option shall at most include a single value out of the following list:

• safetyQM
• safetyAsilA
• safetyAsilB
• safetyAsilC
• safetyAsilD

(cid:99)()

[constr_1381] Appearance of core-related possible values of MemorySection.option or SwAddrMethod.option according to [TPS_SWCT_01456] (cid:100) Any given list of values stored in the attributes MemorySection.option or SwAddrMethod.option shall at most include a single value out of the following list:

• coreGlobal
• coreLocal

(cid:99)()

[TPS_SWCT_01294] Missing SwDataDefProps.swAddrMethod (cid:100) If the association SwDataDefProps.swAddrMethod is missing the object can be placed anywhere without restriction, e.g. using a default behavior of the RTE generator. Contradicting two different component types request different associations for specifications (e.g. one particular SwAddrMethod) shall be flagged as an error. (cid:99)()

[TPS_SWCT_01292] Usage of SwAddrMethod in the context of a DataPrototype (cid:100) Figure 5.43 illustrates the usage of SwAddrMethod in the context of a DataPrototype. Note that the software component which defines the DataPrototype will in general not be the same to which the Implementation that actually contains the description of the MemorySection belongs.

The reason for this is that the resources for data allocated by the RTE will be described in the Implementation of the RTE. The indirection via SwAddrMethod makes this possible. (cid:99)()

[TPS_SWCT_01293] RTE Generator has to derive the Memory Allocation Keyword (cid:100) Please note that the RTE Generator has to derive the Memory Allocation Keyword used for RunnableEntitys and BswSchedulableEntitys from the shortName of the SwAddrMethod only because the alignment defined in MemorySection is not known at contract phase. (cid:99)()

[constr_2034] SwAddrMethod referenced by RunnableEntitys or BswSchedulableEntitys (cid:100) RunnableEntitys and BswSchedulableEntitys shall not reference a SwAddrMethod which attribute memoryAllocationKeywordPolicy is set to addrMethodShortNameAndAlignment. (cid:99)()

[constr_1402] Applicability of core-related possible values of MemorySection.option or SwAddrMethod.option related to SwAddrMethod.sectionInitializationPolicy (cid:100) If the attribute SwAddrMethod.option or MemorySection.option is set to coreLocal then the attribute SwAddrMethod.sectionInitializationPolicy of the same SwAddrMethod respectively the MemorySection.swAddrMethod shall be either set to INIT or CLEARED. (cid:99)()

The purpose of [constr_1402] is a reduction of the complexity of memory layouts and reduce the amount of memory gaps due to allocation restrictions.

Table 5.93: SwAddrMethod

Table 5.94: SectionInitializationPolicyType

Table 5.95: MemorySectionType

Table 5.96: MemoryAllocationKeywordPolicyType

Table 5.97: AlignmentType

For more information on the specification of the MemorySection refer to [7].

Figure 5.43: Assigning an address method to a memory section

#@SECTION: 5.5.5 Record Layouts
#@CLASS: ApplicationDataType
#@CLASS: SwDataDefProps
#@CLASS: SwRecordLayout

[TPS_SWCT_01295] SwRecordLayout (cid:100) The SwRecordLayout describes how data is serialized in the memory of an ECU. This information is important with respect to the following aspects:

• to inform a measurement and calibration system how the data is serialized in the memory of an ECU
• to make sure that the software development results in the intended data structures
• to identify the proper interpolation routines

Via the SwDataDefProps a record-layout can be associated to a data entity. If the very same serialization approach is used for multiple ApplicationDataTypes all of these may refer to the same SwRecordLayout even if the size of the data is different. (cid:99)()

#@SECTION: 5.5.5.1 Specifying Record Layouts
#@CLASS: AsamRecordLayoutSemantics
#@CLASS: AxisIndexType
#@CLASS: RecordLayoutIteratorPoint
#@CLASS: SwRecordLayout
#@CLASS: SwRecordLayoutGroup
#@CLASS: SwRecordLayoutGroupContent
#@CLASS: SwRecordLayoutV
#@CLASS: ImplementationDataType


As mentioned above, the purpose of record layout is to specify how an object (e.g. a calibration parameter) is serialized in memory of an ECU. The canonical approach for this is to define nested groups (SwRecordLayoutGroup). These groups indicate the structure of the corresponding ImplementationDataType. The serialization is then executed by iterating over the axes of a curve, a map, or iterating along a string. The contents of such a record layout group (SwRecordLayoutGroupContent) is a mixture of (thus nested) groups and values (SwRecordLayoutV).

These values refer to particular properties of the object (e.g. value, count, . . .). By application of this pattern, the serialization of any complex object can be specified.

Figure 5.44: Specification of a record layout
Table 5.98: SwRecordLayout
Table 5.99: SwRecordLayoutV
Table 5.100: SwRecordLayoutGroup
Table 5.101: SwRecordLayoutGroupContent

[constr_1264] Iteration along output axis is only supported for VALUE and VAL_BLK (cid:100) swRecordLayoutVIndex in SwRecordLayoutV cannot be 0 for any value of SwRecordLayoutV.category other than VALUE and VAL_BLK. (cid:99)()

For CURVE, MAP, etc. the iteration shall be performed along the input axis.
#@Hierarchical
This meta-class specifies an axis in a curve/map data object. The index satisfies the following convention:
• 0 output "axis"
• 1 input axis 1 (X input axis e.g. of a CURVE)
• 2 input axis 2 (Y input axis e.g. of a MAP)
• 3 input axis 3 (Z input axis e.g. of a CUBOID)
• 4 input axis 3 (Z4 input axis e.g. of a CUBE_4)
• 5 input axis 3 (Z5 input axis e.g. of a CUBE_5)
• 6..9 etc.
Table 5.102: AxisIndexType
/#@Hierarchical

Table 5.103: RecordLayoutIteratorPoint

[TPS_SWCT_01489] Standardized values of SwRecordLayoutV.swRecordLayoutVProp (cid:100) SwRecordLayoutV.swRecordLayoutVProp describes the type of values to be stored. The standardized values for SwRecordLayoutV.swRecordLayoutVProp are listed in Table 5.104. (cid:99)()

Table 5.104: swRecordLayoutVProp

Figure 5.45 and Figure 5.46 illustrate most of these properties.


<-------------- multimodal context 
The diagram defines the in-memory record layout (swRecordLayoutVProp) for a single axis, partitioning four slots (COUNT = 4) into VALUE, LEFTDIFF, RIGHTDIFF and padding. It shows how LEFTDIFF and RIGHTDIFF offsets are derived dynamically at runtime, while FIXLEFTDIFF and FIXRIGHTDIFF provide static byte spans over the first two and last two slots respectively, guiding RTE marshalling for axis data.

- Component hierarchy: a single AtomicSwComponentType “swRecordLayoutVProp” (or part of a CompositionSwComponentType) handling one axis’s record packing.
- Ports & interfaces: one AbstractProvidedPortPrototype (e.g. AxisRecordPort) of a ClientServerInterface or DataInterface carrying an ApplicationCompositeDataType with element prototypes VALUE, LEFTDIFF, RIGHTDIFF.
- Data flow: the SWC writes axis raw value then computes left/right differentials into the composite record; RTE transmits the packed record to consumers.
- Key AUTOSAR concepts: ApplicationCompositeDataType and ApplicationCompositeElementDataPrototype, swRecordLayoutVProp mapping, COUNT property, AbstractProvidedPortPrototype, fixed vs. dynamic offsets.
- Scenario: packaging sensor or actuator axis data (current point and deviations) into a standardized record for communication, diagnostics or logging. ---------------------->
Figure 5.45: Values for swRecordLayoutVProp for individual axis


<-------------- multimodal context 
This diagram illustrates how the swRecordLayoutVProp for a fixed axis is computed in AUTOSAR. It defines a starting OFFSET and a constant interval DIST (or equivalently 2^SHIFT) to calculate the position of each record element via the formula Value = OFFSET + n * DIST (or + n * 2^SHIFT). This ensures uniform spacing of sub-elements in memory or communication records.

• Component hierarchy – No SW-Components or compositions are depicted; it concerns a single property prototype (swRecordLayoutVProp).  
• Ports & interfaces – No PPorts/RPorts or interfaces are shown.  
• Data flow – A mathematical pattern: each element index n maps to a position value by adding OFFSET plus n times DIST (or 2^SHIFT).  
• Key AUTOSAR concepts – swRecordLayoutVProp, fixed axis, OFFSET, DIST, SHIFT (power-of-two spacing).  
• Scenario – Specifies linear layout of record or array elements with uniform spacing for data mapping. ---------------------->
Figure 5.46: Values for swRecordLayoutVProp for fixed axis

[TPS_SWCT_01296] Different approaches of ASAM MCD-2MC and AUTOSAR with respect to SwRecordLayout (cid:100) ASAM MCD-2D specification (also known as A2L, resp. ASAP) uses keywords in record layouts where MSR/AUTOSAR uses the more generic approach specified here. It may happen that this generic approach cannot always be safely mapped to the A2L keywords. Therefore SwRecordLayoutV.category as well as SwRecordLayoutGroup.category can assist the conversion to the current A2L format. (cid:99)()

Table 5.105: AsamRecordLayoutSemantics

The values of SwRecordLayoutV.category resp. SwRecordLayoutGroup.category can, for example, be taken from the ASAM MCD 2D specification provided in [25]. Examples are such as INDEX_INCR, INDEX_DECR, COLUMN_DIR, ROW_DIR, ALTERNATE_WITH_X, ALTERNATE_WITH_Y, ALTERNATE_CURVES. 
The consistency of these values of SwRecordLayoutV.category resp. SwRecordLayoutGroup.category with the structure of the SwRecordLayout shall be ensured by the author of the SwRecord Layout. 
Note that there are keywords in A2L bound to a calibration parameter which in MSR/AUTOSAR are represented by the SwRecordLayout (DEPOSIT etc.).

The following XML fragment provides an example for a SwRecordLayout for a curve. Note that in this case recognizing the patterns represented by the A2LKeywords (shown in XML-Comment) is pretty straight forward, even if the keywords were not provided in the SwRecordLayoutV.category as well as SwRecordLayoutGroup.category.

Listing 5.12: Example for RecordLayout of a curve
<SW-RECORD-LAYOUT>
<SHORT-NAME>RecordLayoutCurve</SHORT-NAME>
<SW-RECORD-LAYOUT-GROUP>
<SW-RECORD-LAYOUT-V><!-- SRC_ADDR_X -->
<SHORT-LABEL>srcAdr</SHORT-LABEL>
<SW-RECORD-LAYOUT-V-PROP>SOURCE-ADR</SW-RECORD-LAYOUT-V-PROP>
</SW-RECORD-LAYOUT-V>
<SW-RECORD-LAYOUT-V><!-- NO_AXIS_PTS_X -->
<SHORT-LABEL>noOfAxisPts</SHORT-LABEL>
<SW-RECORD-LAYOUT-V-PROP>COUNT</SW-RECORD-LAYOUT-V-PROP>
<SW-RECORD-LAYOUT-V-INDEX>1</SW-RECORD-LAYOUT-V-INDEX>
</SW-RECORD-LAYOUT-V>
<SW-RECORD-LAYOUT-GROUP><!-- AXIS_PTS_X -->
<SHORT-LABEL>xPts</SHORT-LABEL>
<CATEGORY>INDEX_INCR</CATEGORY>
<SW-RECORD-LAYOUT-GROUP-AXIS>1</SW-RECORD-LAYOUT-GROUP-AXIS>
<SW-RECORD-LAYOUT-GROUP-FROM>1</SW-RECORD-LAYOUT-GROUP-FROM>
<SW-RECORD-LAYOUT-GROUP-TO>-1</SW-RECORD-LAYOUT-GROUP-TO>
<SW-RECORD-LAYOUT-V>
<SHORT-LABEL>xPt</SHORT-LABEL>
<SW-RECORD-LAYOUT-V-AXIS>1</SW-RECORD-LAYOUT-V-AXIS> <!--
AXIS_PTS_X -->
<SW-RECORD-LAYOUT-V-PROP>VALUE</SW-RECORD-LAYOUT-V-PROP>
</SW-RECORD-LAYOUT-V>
</SW-RECORD-LAYOUT-GROUP>
<SW-RECORD-LAYOUT-GROUP>
<SHORT-LABEL>values</SHORT-LABEL><!-- FNC_VALUES -->
<CATEGORY>COLUMN_DIR</CATEGORY>
<SW-RECORD-LAYOUT-GROUP-AXIS>0</SW-RECORD-LAYOUT-GROUP-AXIS>
<SW-RECORD-LAYOUT-GROUP-FROM>1</SW-RECORD-LAYOUT-GROUP-FROM>
<SW-RECORD-LAYOUT-GROUP-TO>-1</SW-RECORD-LAYOUT-GROUP-TO>
<SW-RECORD-LAYOUT-V>
<SHORT-LABEL>value</SHORT-LABEL>
<SW-RECORD-LAYOUT-V-AXIS>0</SW-RECORD-LAYOUT-V-AXIS><!--
FNC_VALUES -->
<SW-RECORD-LAYOUT-V-PROP>VALUE</SW-RECORD-LAYOUT-V-PROP>
</SW-RECORD-LAYOUT-V>
</SW-RECORD-LAYOUT-GROUP>
</SW-RECORD-LAYOUT-GROUP>
</SW-RECORD-LAYOUT>

#@SECTION: 5.5.5.2 RecordLayouts and DataTypes
#@CLASS: ApplicationDataType
#@CLASS: ImplementationDataType
#@CLASS: ParameterDataPrototype
#@CLASS: SwRecordLayout
#@CLASS: AutosarDataType
#@CLASS: ImplementationDataTypeElement



[constr_1027] Types for record layouts (cid:100) Because ParameterDataPrototypes have a (cid:28)isOfType(cid:29)-relation to ApplicationDataTypes or ImplementationDataTypes the related data types shall properly match to the details as speciﬁed in swDataDefProps. (cid:99)()

This is exempliﬁed in ﬁgure 5.47.

Figure 5.47: Dependency of AutosarDataTypes and SwRecordLayouts

[TPS_SWCT_01297] Compliance of ApplicationDataTypes or ImplementationDataTypes to swDataDefProps (cid:100) In order to maintain this compliance the following options exist:
• Manually create ImplementationDataTypes from corresponding ApplicationDataTypes and the referenced SwRecordLayouts
• Automatically create ImplementationDataTypes according to the existing deﬁnition of SwRecordLayouts. This could be performed by a model transformation according to the algorithm shown below. (cid:99)()

[TPS_SWCT_01298] Computing SwRecordLayout from ImplementationDataTypes is not possible (cid:100) Note that computing SwRecordLayouts from ImplementationDataTypes is not really possible because the particular semantics of the components is not available (swRecordLayoutVProp). (cid:99)()

Figure 5.48 and ﬁgure 5.49 illustrate how data types can be derived from SwRecordLayouts.

The "blue" data types are derived from the record layout. These diagrams illustrate in particular the fact that on the level of ApplicationDataType even complex entities such as curves and maps appear as somehow primitive. The inner details of such entities are handled e.g. by service libraries.

Figure 5.48: Curve implemented as two consecutive arrays

Figure 5.49: Curve implemented as array of value pairs

Figure 5.50: Record layout and data type for a map

The algorithm to generate the desired data types is illustrated in the following two diagrams.

We create an ImplementationDataType for each ApplicationDataType. Figure 5.51 illustrates how to map the details.


<-------------- multimodal context 
This diagram defines an AUTOSAR SW-Component that implements an algorithmic mapping from application-level data types to their corresponding implementation records. It shows two runnables that iteratively consume each ApplicationDataType, break it into sub-elements based on a RecordLayout, and emit ImplementationDataTypeElement instances. A single data flow chain connects an input RPort (“ApplicationDataType”) through the CreateType and create subElement runnables to an output PPort (“TypeContentFromRecordLayout”). This design encapsulates the transformation logic needed by an RTE or code-generator module to reconcile abstract data prototypes with concrete ECU memory layouts.

• Component hierarchy  
  – One AtomicSwComponentType (“DataTypeMapper”)  
  – Two runnables: CreateType, create subElement  
  – No nested compositions or delegated sub-components  

• Ports & interfaces  
  – RPort: ApplicationDataType (data interface carrying ApplicationDataType prototypes)  
  – PPort: TypeContentFromRecordLayout (data interface for ImplementationDataTypeElement)  
  – One AssemblySwConnector linking ports to Runnables  

• Data flow  
  – Iterative loop («iterative») over all ApplicationDataTypes  
  – ApplicationDataType → CreateType → create subElement → ImplementationDataTypeElement → TypeContentFromRecordLayout  

• Key AUTOSAR concepts  
  – Runnable entities with explicit triggering via iterative scheduling  
  – AbstractProvidedPortPrototype (PPort) and AbstractRequiredPortPrototype (RPort)  
  – ApplicationDataType, ApplicationCompositeDataTypeSubElementRef  
  – ImplementationDataTypeElement as AutosarDataPrototype  
  – RecordLayout-based mapping  

• Scenario  
  – Code‐generation or RTE‐configuration step that transforms abstract application data definitions into concrete memory layouts for ECU software. ---------------------->
Figure 5.51: algorithm to map the details of an application data type to the corresponding implementation data type according to the record layout

[TPS_SWCT_01299] Relation of swRecordLayoutGroup to subElement (cid:100) For each swRecordLayoutGroup an appropriate subElement shall be created. This sub element is then reﬁned according to the approach sketched in ﬁgure 5.52. The algorithm shall be recursively applied applied to the newly created ImplementationDataTypeElements. As the record layout groups are nested, this recursion yields the complete structure in the ImplementationDataType. (cid:99)()

Figure 5.52: reﬁning subElements

#@SECTION: 5.5.5.3 Record Layouts and Interpolation Routines
#@CLASS: InterpolationRoutine
#@CLASS: InterpolationRoutineMapping
#@CLASS: InterpolationRoutineMappingSet
#@CLASS: BswModuleEntry
#@CLASS: InterpolationRoutine
#@CLASS: SwDataDefProps

[TPS_SWCT_01300] Relationship between record layouts and interpolation routines (cid:100) The relationship between record layouts and interpolation routines can be specified in InterpolationRoutineMappingSet.

The interpolation routine is represented as BswModuleEntry and implements a particular interpolation method which is denoted in the value of InterpolationRoutine.shortLabel.

The intended interpolation method is denoted in the value of attribute SwDataDefProps.swInterpolationMethod. (cid:99)()

Figure 5.53: Mapping of Record Layouts and Interpolation Routines

Table 5.106: InterpolationRoutineMappingSet

Table 5.107: InterpolationRoutineMapping

Table 5.108: InterpolationRoutine

#@SECTION: 5.6 Speciﬁcation of Constant Values
#@SECTION: 5.6.1 Overview
#@CLASS: ApplicationArrayDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: ArrayValueSpecification
#@CLASS: AutosarDataType
#@CLASS: ConstantReference
#@CLASS: ConstantSpecification
#@CLASS: DataPrototype
#@CLASS: ImplementationDataType
#@CLASS: NumericalValueSpecification
#@CLASS: RecordValueSpecification
#@CLASS: TextValueSpecification
#@CLASS: ValueSpecification
#@CLASS: ReferenceValueSpecification
#@CLASS: ApplicationValueSpecification
#@CLASS: ApplicationDataType


[TPS_SWCT_01177] Assignment of constant values (cid:100) Constant values can be assigned to a meta-class by aggregating the meta-class ValueSpecification. This aggregation can be used in two ways:
1. by referencing to a reusable ConstantSpecification which contains another ValueSpecification
2. or through an inline aggregation of a value specification of various kind. (cid:99)(RS_SWCT_03175)

Table 5.109: ConstantSpecification

Table 5.110: ValueSpecification

Table 5.111: ArrayValueSpecification

Table 5.112: RecordValueSpecification

Table 5.113: TextValueSpecification

Table 5.114: NumericalValueSpecification

Table 5.115: ReferenceValueSpecification

[TPS_SWCT_01178] Specialized subclasses of ValueSpecification (cid:100) Figure 5.54 shows the specialized subclasses of ValueSpecification which allow to define values for different use cases:
• Reference to a constant (which is actually a reusable value specification) by means of a ConstantReference
• TextValueSpecification
• NumericalValueSpecification
• ArrayValueSpecification
• RecordValueSpecification
• ApplicationValueSpecification: this can be used to specify the value of Compound Primitive Data Types (see [TPS_SWCT_01179]) such as curves and maps. It is also possible to use this in general (e.g. for a primitive calibration value) for the speciﬁcation of a value of a DataPrototype typed by an ApplicationDataType (see section 5.7.4). Note that ApplicationValueSpecification is modeled along the example of ASAM CDF (for more information please refer to [27]).
• reference to a DataPrototype: this can be used to describe initial values for pointer variables in the basic software. One use case is the exchange of data descriptions used to access calibration data for software emulation methods (see [7] for details).
• ApplicationRuleBasedValueSpecification
• NumericalRuleBasedValueSpecification 
(cid:99)(RS_SWCT_03175)

Figure 5.54: Summary of ValueSpecification

It's important to understand that although the name of the meta-class TextValueSpecification suggests that it is the preferred way for the definition of an invalidValue of initValue of an ApplicationPrimitiveDataType of category STRING the TextValueSpecification actually has a different purpose (as defined by [constr_1284]).

[constr_1284] Limitation of the use of TextValueSpecification (cid:100) TextValueSpecification shall only be used in the context of an AutosarDataType that references a CompuMethod in the role ImplementationDataType.sw DataDefPropos.compuMethod of category TEXTTABLE, BITFIELD_TEXTTABLE, SCALE_LINEAR_AND_TEXTTABLE, and SCALE_RATIONAL_AND_TEXTTABLE. (cid:99)()

In other words, the purpose of TextValueSpecification is to define the labels that correspond to enumeration values. The constraints [constr_1225] and [constr_1284] correspond to each other such that [constr_1225] demands the usage of TextValueSpecification for the definition of labels for enumeration values while [constr_1284] says that the definition of labels for enumeration values is the only use case for TextValueSpecification.

Note that ValueSpecification does not inherit from any data type. This would cause a redundancy in the meta-model since the intended data type of a ValueSpecification is already determined by the context in which it is aggregated. 
For example, “1” can be taken as a constant value for many data types. If the ValueSpecification would refer to a speciﬁc AutosarDataType it would be necessary to deﬁne a “1” for every single AutosarDataType this value is supposed to be used in combination with.
Nonetheless the intended data type imposes a certain constraint on the content of a ValueSpecification:

[constr_4035] ValueSpecification shall fit into data type (cid:100) An instance of ValueSpecification which is used to assign a value to a software object typed by an AutosarDataType shall fit into this AutosarDataType without losing information. (cid:99)()

For example, it is not allowed to assign the numerical value "1.5" as initial value to a data prototype typed by an ImplementationDataType which has an integer base type.

[constr_1271] RecordValueSpecification.elements shall be identical to the number of ApplicationRecordDataType.element (cid:100) The initialization of an DataPrototype typed by an ApplicationRecordDataType by means of a RecordValueSpecification shall exactly match the structure of the ApplicationRecordDataType. For this means, it is required that the number of RecordValueSpecification.elements shall be identical to the number of ApplicationRecordDataType.elements. (cid:99)()

[constr_1272] RecordValueSpecification.elements shall be identical to the number of subElements of ImplementationDataType of category STRUCTURE (cid:100) The initialization of an DataPrototype typed by an ImplementationDataType of category STRUCTURE by means of a RecordValueSpecification shall exactly match the structure of the ImplementationDataType of category STRUCTURE. For this means, it is required that the number of RecordValueSpecification.elements shall be identical to the number of ImplementationDataType.subElements. (cid:99)()

[constr_1273] ArrayValueSpecification.elements shall be identical to the value of ApplicationArrayDataType.element.maxNumberOfElements (cid:100) The initialization of DataPrototype typed by an ApplicationArrayDataType by means of an ArrayValueSpecification shall exactly match the structure of the ApplicationArrayDataType regardless of the setting of the attribute ApplicationArrayDataType.element.arraySizeSemantics. This means that the number of ArrayValueSpecification.elements shall be identical to the value of ApplicationArrayDataType.element.maxNumberOfElements. (cid:99)()

The consequence of [constr_1273] is that for e.g. an ApplicationArrayDataType that has the attribute element.maxNumberOfElements set to the value 10 a ArrayValueSpecification shall be provided that contains 10 elements.

[constr_1274] ArrayValueSpecification.elements shall be identical to the value of ImplementationDataType.subElement.arraySize of category ARRAY (cid:100) The initialization of a DataPrototype typed by an ImplementationDataType of category ARRAY by means of an ArrayValueSpecification shall exactly match the structure of the ImplementationDataType regardless of the setting of the attribute ImplementationDataType.subElement.arraySizeSemantics. This means that the number of ArrayValueSpecification.elements shall be identical to the value of ImplementationDataType.subElement.arraySize. (cid:99)()

For deeply nested composite data types (including ImplementationDataTypes created in response to the existence of a Compound Primitive Data Type) [constr_1271], [constr_1272], and [constr_1273] shall be applied recursively according to the nature of the given nesting levels. For the "leaf" elements [constr_4035] applies.

#@SECTION: 5.6.2 Speciﬁcation of Values based on Rules
#@CLASS: AbstractRuleBasedValueSpecification
#@CLASS: ApplicationRuleBasedValueSpecification
#@CLASS: NumericalRuleBasedValueSpecification
#@CLASS: RuleBasedAxisCont
#@CLASS: RuleBasedValueCont
#@CLASS: RuleBasedValueSpecification
#@CLASS: RuleArguments
#@CLASS: CompuMethod

[TPS_SWCT_01484] Meaning of ApplicationRuleBasedValueSpecification (cid:100) The purpose of the ApplicationRuleBasedValueSpecification is to provide means for a compact provision of values for DataPrototypes that otherwise would require a high volume (in terms of serialized ARXML) of e.g. initialization data. ApplicationRuleBasedValueSpecification may used for ApplicationArrayDataType, and also (if applicable) to the so-called Compound Primitive Data Types. (cid:99)(RS_SWCT_03260)

For example, an ApplicationArrayDataType that has 100 elements would need to be initialized such that for each element a dedicated initial value is provided. In the most prominent cases the majority of these elements are initialized with an identical value (e.g. 0) and only the first few elements differ in terms of initialization values.

Table 5.116: AbstractRuleBasedValueSpecification

Table 5.117: ApplicationRuleBasedValueSpecification

Table 5.118: RuleBasedAxisCont

Table 5.119: RuleBasedValueCont

In case the ApplicationRuleBasedValueSpecification is applied to Compound Primitive Data Types basically the same rules apply for ApplicationRuleBasedValueSpecification as defined for ApplicationValueSpecification.

[constr_2057] Mandatory information of a RuleBasedAxisCont (cid:100) If the attribute swAxisCont is defined for an ApplicationRuleBasedValueSpecification the RuleBasedAxisCont shall define one swAxisIndex value and one swArraysize value per dimension, even in the case when the owning ApplicationRuleBasedValueSpecification defines only the content of a single dimensional object like a CURVE. (cid:99)()

[constr_2058] Mandatory information of a RuleBasedValueCont (cid:100) If the attribute swValueCont is defined for an ApplicationRuleBasedValueSpecification the RuleBasedValueCont shall define always the attribute swArraysize if the ApplicationRuleBasedValueSpecification is of category CURVE, MAP, CUBOID, CUBE_4, CUBE_5, COM_AXIS, RES_AXIS, CURVE_AXIS, VAL_BLK or ARRAY. (cid:99)()

Please note that for multidimensional Compound Primitive Data Types (e.g. MAP) it is necessary to know the dimensions in order to be able to process the SwValues. [constr_2057] and [constr_2058] shall support a consistent handling of single and multidimensional Compound Primitive Data Types.

If the ApplicationRuleBasedValueSpecification defines values for a Compound Primitive Data Type with more than one input axis the swArraySize gets mandatory to ensure the correct processing of the values calculated by rule.

[TPS_SWCT_02053] Values of RuleBasedAxisCont with the category CURVE_AXIS, COM_AXIS, RES_AXIS are for display only (cid:100) In case of ApplicationRuleBasedValueSpecifications of category MAP, CUBOID, CUBE_4, CUBE_5 or CURVE it is possible that the RuleBasedAxisCont of axes can be omitted if the axis is of category COM_AXIS or RES_AXIS or CURVE_AXIS. If RuleBasedAxisCont values exists in such cases for the axes these are for display purpose only because the related DataPrototype of the MAP or CURVE does not hold the values of such axes. These are properties of the DataPrototype of the COM_AXIS or RES_AXIS or CURVE_AXIS. (cid:99)()

Hence, values of the COM_AXIS itself are described by RuleBasedValueCont.

Figure 5.55: Definition of an ApplicationRuleBasedValueSpecification

[TPS_SWCT_01528] Meaning of NumericalRuleBasedValueSpecification (cid:100) The purpose of the NumericalRuleBasedValueSpecification is to provide means for a compact provision of values for DataPrototypes that otherwise would require a high volume (in terms of serialized ARXML) of e.g. initialization data. NumericalRuleBasedValueSpecification may used for DataPrototypes typed by ImplementationDataTypes of category ARRAY or Compound Primitive Data Types mapped to ImplementationDataTypes of category ARRAY. (cid:99)(RS_SWCT_03260)

Concerning initValues for Compound Primitive Data Types please note as well [TPS_SWCT_01185].

Table 5.120: NumericalRuleBasedValueSpecification

Figure 5.56: Definition of an NumericalRuleBasedValueSpecification

[TPS_SWCT_01495] Standardized value of RuleBasedValueSpecification.rule (cid:100) AUTOSAR reserves a dedicated value of RuleBasedValueSpecification.rule in a standardized semantics: • FILL_UNTIL_END • FILL_UNTIL_MAX_SIZE The meaning of this value of rule is explained in [TPS_SWCT_01494] and [TPS_SWCT_01609]. (cid:99)(RS_SWCT_03260, RS_SWCT_03181)

[TPS_SWCT_01485] The order of RuleArguments arguments shall be respected (cid:100) The order of arguments in RuleArguments corresponds to the order of elements in the array, i.e. the first argument corresponds to the first element of the array, the second argument corresponds to the second element of the array, and so on. (cid:99)(RS_SWCT_03260)

Please note that a single argument can be defined by the attributes • RuleArguments.v • RuleArguments.vf • RuleArguments.vt • RuleArguments.vtf.vf • RuleArguments.vtf.vt

[TPS_SWCT_01493] The number of RuleArguments.arguments shall not exceed the array size (cid:100) If the number of RuleArguments.arguments exceeds the number of elements of an array that it is applied to then the RuleArguments.arguments that go beyond the last element of the array shall be ignored. (cid:99)(RS_SWCT_03260)

[TPS_SWCT_01494] A RuleBasedValueSpecification of rule FILL_UNTIL_END shall fill the value of the last RuleArguments.argument until the last element of the array (cid:100) The following rule applies to RuleBasedValueSpecifications of rule FILL_UNTIL_END: If the number of RuleArguments.arguments is smaller than the number of elements of the array it is applied to then the value of the last RuleArguments.argument shall be applied to any following element of the array until the last element of the array. (cid:99)(RS_SWCT_03260)

[TPS_SWCT_01609] A RuleBasedValueSpecification of rule FILL_UNTIL_MAX_SIZE shall fill the value of the last RuleArguments.argument until the number of elements specified in maxSizeToFill (cid:100) The following rule applies to RuleBasedValueSpecifications of rule FILL_UNTIL_MAX_SIZE: If the number of RuleArguments.arguments is smaller than the number of elements of the array it is applied to and smaller than maxSizeToFill, then the value of the last RuleArguments.argument shall be applied to so many of the following elements that the first maxSizeToFill elements of the array are filled. (cid:99)(RS_SWCT_03260)

Table 5.121: RuleBasedValueSpecification

Table 5.122: RuleArguments

#@SECTION: 5.6.3 Reference to Constant
#@CLASS: ConstantReference

Note the specific meaning of ConstantReference: it passes the definition of the value on to a ConstantSpecification that is defined as part of an AUTOSAR ARPackage.
Table 5.123: ConstantReference

#@SECTION: 5.6.4 Values for Compound Primitive Data Types
#@CLASS: ApplicationValueSpecification
#@CLASS: NumericalOrText
#@CLASS: SwAxisCont
#@CLASS: SwValueCont
#@CLASS: SwValues
#@CLASS: ValueGroup
#@CLASS: ValueList
#@CLASS: AttributeValueVariationPoint
#@CLASS: SwSystemconst

[TPS_SWCT_01180] Maximum possible size of Compound Primitive Data Type (cid:100) Note that if the size of the Compound Primitive Data Type (see [TPS_SWCT_01179]) (curve/map) is defined using an AttributeValueVariationPoint (in other words swMaxAxisPoints, swValueBlockSize dependent on the value of SwSystemconst) the initValue shall provide the maximum possible amount of values. (cid:99)(RS_SWCT_03216)

In this case it is the responsibility of model author to ensure that the size of the specified init values matches the range of the involved system constants.

[constr_1160] Size of Compound Primitive Data Type is variant (cid:100) For Compound Primitive Data Types (see [TPS_SWCT_01179]) where the size is subject to variation the size of the specified initValues shall match the range of the involved SwSystemconst. (cid:99)()

Figure 5.57: Explanation of swMaxAxisPoints

[TPS_SWCT_01181] Bound model specifies a primitive which is smaller than the maximum defined by the range of the involved SwSystemconst (cid:100) The processing tools shall take the lower part of the initValues in case the bound model specifies a primitive which is smaller than the maximum defined by the range of the involved SwSystemconst. (cid:99)(RS_SWCT_03216, RS_SWCT_03148)

The consequences of [TPS_SWCT_01181] are exemplified by Figure 5.57.

[constr_2050] Mandatory information of a SwAxisCont (cid:100) If the attribute swAxisCont is defined for an ApplicationValueSpecification the SwAxisCont shall define one swAxisIndex value and one swArraysize value per dimension, even in the case when the owning ApplicationValueSpecification defines only the content of a single dimensional object like a CURVE. (cid:99)()

[constr_2051] Mandatory information of a SwValueCont (cid:100) If the attribute swValueCont is defined for an ApplicationValueSpecification the SwValueCont shall always define the attribute swArraysize if the ApplicationValueSpecification is of category CURVE, MAP, CUBOID, CUBE_4, CUBE_5, COM_AXIS, RES_AXIS, or VAL_BLK. (cid:99)()

Please note that for multidimensional Compound Primitive Types (e.g. MAP) it is necessary to know the dimensions in order to be able to process the SwValues. [constr_2050] and [constr_2051] shall support a consistent handling of single and multidimensional Compound Primitive Data Types.

[constr_2052] Values of swArraySize and the number of values provided by swValuesPhys shall be consistent. (cid:100) swValuesPhys shall define as many numbers of values as the swArraysize defines. In other words, in the bound model the number of descendants (v, or vf, or vt, or vtf) shall be identical to the number of elements of the related DataPrototype typed by an ApplicationPrimitiveDataType.

If several swArraySize values are provided these have to be multiplied in order to get the total number of swValuesPhys values. (cid:99)()

Please note that case of Compound Primitive Data Types typically the attribute swValuesPhys defines more than one value. [constr_2051] and [constr_2052] shall enable a consistent handling of the swValuesPhys values regardless how many dimensions the related Compound Primitive Type defines.

If the ApplicationValueSpecification defines values for a Compound Primitive Data Type with more than one input axis the swArraySize gets mandatory to ensure the correct processing of the swValuesPhys values independent of the existence of SwValues.vg.

[TPS_SWCT_02001] Values of SwAxisCont with the category CURVE_AXIS, COM_AXIS, RES_AXIS are for display only (cid:100) In case of ApplicationValueSpecifications of category MAP, CUBOID, CUBE_4, CUBE_5, and CURVE it is possible that the SwAxisCont of axes can be omitted if the axis is of category COM_AXIS or RES_AXIS or CURVE_AXIS.

If SwAxisCont values exists in such cases for the axes these are for display purpose only because the related DataPrototype of the MAP, CUBOID, CUBE_4, CUBE_5, or CURVE does not hold the values of such axes. These are properties of the DataPrototype of the COM_AXIS or RES_AXIS or CURVE_AXIS. (cid:99)()

Hence values of the COM_AXIS itself are described by SwValueCont.

[constr_1243] NumericalOrText shall either define vf or vt (cid:100) Within the context of one NumericalOrText, either the attribute vf or the attribute vt shall be defined. The existence of both attributes at the same time is not permitted. (cid:99)()

Figure 5.58: Definition of an ApplicationValueSpecification
Table 5.124: ApplicationValueSpecification
Table 5.125: SwAxisCont
Table 5.126: SwValueCont
Table 5.127: SwValues
Table 5.128: ValueGroup
Table 5.129: ValueList
Table 5.130: NumericalOrText

#@SECTION: 5.6.5 Examples
#@SECTION: 5.6.5.1 Example for Constant Speciﬁcation for CURVE
#@CLASS: ConstantSpecification

The following example illustrates how a ConstantSpecification is specified for a CURVE. Please note, that in this example the vf attribute is used for the swArraysize as well as for the swValuesPhys. The basic intention of vf is the usage for variant rich models but it is valid as well if vf contains invariant values.

Listing 5.13: Example for Constant Specification for CURVE

<CONSTANT-SPECIFICATION>
<SHORT-NAME>PhysInitValuesOfCurve</SHORT-NAME>
<DESC>
<L-2 L="EN">This example shows a ConstantSpecification for a CURVE where the axis is a STD_AXIS</L-2>
</DESC>
<VALUE-SPEC>
<APPLICATION-VALUE-SPECIFICATION>
<CATEGORY>CURVE</CATEGORY>
<SW-AXIS-CONTS>
<SW-AXIS-CONT>
<CATEGORY>STD_AXIS</CATEGORY>
<SW-AXIS-INDEX>1</SW-AXIS-INDEX>
<SW-ARRAYSIZE>
<VF>4</VF>
</SW-ARRAYSIZE>
<SW-VALUES-PHYS>
<VF>0</VF>
<VF>1</VF>
<VF>2</VF>
<VF>3</VF>
</SW-VALUES-PHYS>
</SW-AXIS-CONT>
</SW-AXIS-CONTS>
<SW-VALUE-CONT>
<UNIT-REF DEST="UNIT">/AUTOSAR/AISpecification/Units/NwtMtr</UNIT-REF>
<SW-ARRAYSIZE>
<VF>4</VF>
</SW-ARRAYSIZE>
<SW-VALUES-PHYS>
<VF>00.000</VF>
<VF>10.000</VF>
<VF>20.000</VF>
<VF>30.000</VF>
</SW-VALUES-PHYS>
</SW-VALUE-CONT>
</APPLICATION-VALUE-SPECIFICATION>
</VALUE-SPEC>
</CONSTANT-SPECIFICATION>

#@SECTION: 5.6.5.2 Example for Constant Speciﬁcation for MAP
#@CLASS: ConstantSpecification
#@CLASS: MAP

The following example illustrates how an ConstantSpecification is specified for a MAP. In this case one axis of the MAP is a STD_AXIS and the second one is a COM_AXIS. Please note that in this example the v attribute is used for the swArraysize as well as for the swValuesPhys. This is possible because the example contains only invariant values.

Listing 5.14: Example for Constant Specification for MAP

<CONSTANT-SPECIFICATION>
<SHORT-NAME>PhysInitValuesOfMap</SHORT-NAME>
<DESC>
<L-2 L="EN">This example shows a ConstantSpecification for a MAP where the first axis is a STD_AXIS and the second axis is a COM_AXIS</L-2>
</DESC>
<VALUE-SPEC>
<APPLICATION-VALUE-SPECIFICATION>
<CATEGORY>MAP</CATEGORY>
<SW-AXIS-CONTS>
<SW-AXIS-CONT>
<CATEGORY>STD_AXIS</CATEGORY>
<SW-AXIS-INDEX>1</SW-AXIS-INDEX>
<SW-ARRAYSIZE>
<V>4</V>
</SW-ARRAYSIZE>
<SW-VALUES-PHYS>
<V>0</V>
<V>1</V>
<V>2</V>
<V>3</V>
</SW-VALUES-PHYS>
</SW-AXIS-CONT>
</SW-AXIS-CONTS>
<SW-VALUE-CONT>
<UNIT-REF DEST="UNIT">/AUTOSAR/AISpecification/Units/NwtMtr</UNIT-REF>
<SW-ARRAYSIZE>
<V>4</V>
<V>2</V>
</SW-ARRAYSIZE>
<SW-VALUES-PHYS>
<VG>
<LABEL>
<L-4 L="EN">Values for axis index 2 equals 0</L-4>
</LABEL>
<V>00</V>
<V>10</V>
<V>20</V>
<V>30</V>
</VG>
<VG>
<LABEL>
<L-4 L="EN">Values for axis index 2 equals 1</L-4>
</LABEL>
<V>01</V>
<V>11</V>
<V>21</V>
<V>31</V>
</VG>
</SW-VALUES-PHYS>
</SW-VALUE-CONT>
</APPLICATION-VALUE-SPECIFICATION>
</VALUE-SPEC>
</CONSTANT-SPECIFICATION>

#@SECTION: 5.6.5.3 Example for Constant Speciﬁcation for COM_AXIS
#@CLASS: ConstantSpecification

The following example illustrates how an ConstantSpecification is specified for a COM_AXIS.

Listing 5.15: Example for Constant Specification for COM_AXIS

<CONSTANT-SPECIFICATION>
<SHORT-NAME>PhysInitValuesOfComAxis</SHORT-NAME>
<DESC>
<L-2 L="EN">This example shows a ConstantSpecification for a COM_AXIS</L-2>
</DESC>
<VALUE-SPEC>
<APPLICATION-VALUE-SPECIFICATION>
<CATEGORY>COM_AXIS</CATEGORY>
<SW-VALUE-CONT>
<UNIT-REF DEST="UNIT">/AUTOSAR/AISpecification/Units/Rpm</UNIT-REF>
<SW-ARRAYSIZE>
<V>6</V>
</SW-ARRAYSIZE>
<SW-VALUES-PHYS>
<V>0</V>
<V>500</V>
<V>1000</V>
<V>1500</V>
<V>3000</V>
<V>5000</V>
</SW-VALUES-PHYS>
</SW-VALUE-CONT>
</APPLICATION-VALUE-SPECIFICATION>
</VALUE-SPEC>
</CONSTANT-SPECIFICATION>

#@SECTION: 5.7 Initial Values
#@SECTION: 5.7.1 Overview
#@CLASS: CalibrationParameterValue
#@CLASS: NonqueuedReceiverComSpec
#@CLASS: NonqueuedSenderComSpec
#@CLASS: NvRequireComSpec
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterProvideComSpec
#@CLASS: ParameterRequireComSpec
#@CLASS: VariableDataPrototype

[TPS_SWCT_01301] Importance of initial values (cid:100) If the value of a VariableDataPrototype/ParameterDataPrototype has not properly been set by a piece of software it can still happen that another piece of software tries to access the value of the VariableDataPrototype/ParameterDataPrototype.

For various reasons it is therefore advised to be able to specify an initial value for a VariableDataPrototype/ParameterDataPrototype in case the value has not been assigned in a controlled manner. However, the definition of an initial value in many cases depends on a context in which the value is accessed. (cid:99)()

Therefore, the AUTOSAR standard foresees means for defining initial values for VariableDataPrototypes/ParameterDataPrototypes on different conceptual levels. That is, although defined for the same VariableDataPrototype/ParameterDataPrototype, an initial value defined on one conceptual level can "supersede" the definition of another initial value on a different conceptual level provided that the priority of the first is higher than the priority of the latter.

The meaning of "supersede" in this context is that that the definition of an initial value on a specific conceptual level is the only relevant definition of an initial value on that level.

[TPS_SWCT_01518] Priority of initial value definition with respect to conceptual levels (cid:100) Any initial value defined in the context of a conceptual level of lower priority is ignored! (cid:99)()

[TPS_SWCT_01182] Conceptual levels for the definition of initial values (cid:100) The following conceptual levels for the definition of initial values exist:

1. It is possible to aggregate an initValue directly at the definition of any VariableDataPrototype/ParameterDataPrototype.

2. It is possible to aggregate an initValue at the level of a ComSpec, namely:
   • NonqueuedSenderComSpec
   • NonqueuedReceiverComSpec
   • ParameterProvideComSpec
   • ParameterRequireComSpec
   • NvRequireComSpec

3. It is possible to aggregate a implInitValue and an appInitValue at the definition of a CalibrationParameterValue.

The priority of one definition of an initial value over another is reflected by the numerical order of the above enumeration, e.g. a definition on level 2 supersedes a definition on level 1. (cid:99)()

#@SECTION: 5.7.2 Initial Value Representation
#@CLASS: ApplicationArrayDataType
#@CLASS: ApplicationDataType
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: AutosarDataType
#@CLASS: DataPrototype
#@CLASS: ImplementationDataType
#@CLASS: CompuMethod
#@CLASS: RecordValueSpecification
#@CLASS: ArrayValueSpecification
#@CLASS: NumericalRuleBasedValueSpecification
#@CLASS: ConstantSpecificationMapping
#@CLASS: CompuScale
#@CLASS: ApplicationValueSpecification

[TPS_SWCT_01183] Actual value of an initValue shall be interpreted according to the AutosarDataType (cid:100) A DataPrototype can be typed by either an ApplicationDataType or else an ImplementationDataType. Therefore, the actual value of an initValue shall be interpreted according to the AutosarDataType that types the DataPrototype. 
That is, if the DataPrototype is typed by an ApplicationDataType the value shall be interpreted as a physical value while if the DataPrototype is typed by an ImplementationDataType the value is to be interpreted as the direct numerical representation. (cid:99)(RS_SWCT_03216, RS_SWCT_03217)

[TPS_SWCT_01184] ApplicationPrimitiveDataTypes with category VALUE (cid:100) In case of ApplicationPrimitiveDataTypes with category VALUE it is the initValues are provided as physical values only because the sufficient RTE Generator should be able to evaluate the related CompuMethod appropriately. (cid:99)(RS_SWCT_03216, RS_SWCT_03217) 

Please note that DataPrototypes that refer to CompuMethods of category SCALE_LINEAR_AND_TEXTTABLE (or similar) shall be initialized by means of the definition of several ApplicationValueSpecification.swValueCont.swValues Phys.vtf. 
Depending on the evaluation of the binding expression either a numerical value or a string is taken to initialize the DataPrototype.

[TPS_SWCT_01185] initValues for Compound Primitive Data Types (cid:100) The definition of initValues in the numerical representation for Compound Primitive Data Type (see section 5.6) is done such that the initValues have to be provided as a RecordValueSpecification respectively an ArrayValueSpecification or NumericalRuleBasedValueSpecification matching to the related ImplementationDataType. The additional representation can be provided and associated by means of a ConstantSpecificationMapping. (cid:99)(RS_SWCT_03216)

[constr_1221] DataPrototype is typed by an ApplicationPrimitive DataType (cid:100) If a DataPrototype is typed by an ApplicationPrimitive DataType its initValue shall be provided by an ApplicationValueSpecification. If the underlying ApplicationPrimitiveDataType represents an enumeration, the value provided shall match to one of the applicable text values (vt, short Label, symbol) defined by the applicable CompuScales. (cid:99)()

[constr_1385] DataPrototype is typed by an ImplementationDataType (cid:100) If a DataPrototype is typed by an ImplementationDataType its initValue shall not be provided by an ApplicationValueSpecification. (cid:99)()

[constr_1222] category of an AutosarDataType used to type a DataPrototype is set to STRING (cid:100) If the category of an AutosarDataType used to type a DataPrototype is set to STRING the ApplicationValueSpecification used to initialize the DataPrototype shall be of category STRING. (cid:99)()

[constr_1223] DataPrototype is typed by an ApplicationRecordDataType (cid:100) If a DataPrototype is typed by an ApplicationRecordDataType the corresponding initValue shall be provided by a RecordValueSpecification. (cid:99)()

[constr_1224] DataPrototype is typed by an ApplicationArrayDataType (cid:100) If a DataPrototype is typed by an ApplicationArrayDataType the corresponding initValue shall be provided by an ArrayValueSpecification or ApplicationRuleBasedValueSpecification. (cid:99)()

#@SECTION: 5.7.3 Constant Speciﬁcation Mapping
#@CLASS: ConstantSpecificationMapping
#@CLASS: ConstantSpecificationMappingSet
#@CLASS: InternalBehavior
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: ParameterSwComponentType
#@CLASS: ValueSpecification
#@CLASS: ConstantReference
#@CLASS: ConstantSpecification

[TPS_SWCT_01186] ConstantSpecificationMapping (cid:100) The ConstantSpecificationMapping is used to associate ValueSpecifications defined in the implementation domain with corresponding ValueSpecifications defined in the application domain. To make this possible the ValueSpecification actually needs to be a ConstantReference. The ConstantSpecification referenced by the ConstantReference is also the target of the references owned by ConstantSpecificationMapping. (cid:99)()

[constr_1029] ConstantSpecificationMapping and ConstantSpecification (cid:100) It is required that one ConstantSpecification referenced from a ConstantSpecificationMapping needs to be defined in the application domain (applConstant) and the other referenced ConstantSpecification needs to be defined in the implementation domain (implConstant). (cid:99)()

[TPS_SWCT_01187] ConstantSpecificationMappingSet referenced by the InternalBehavior (cid:100) In most cases the meta-class ConstantSpecificationMappingSet will be referenced by the InternalBehavior. This ConstantSpecificationMappingSet contains the applicable ConstantSpecificationMappings. (cid:99)()

However, in some specializations the software-components will not have an InternalBehavior:
#@Hierarchical
• [constr_1030] ParameterSwComponentType references ConstantSpecificationMappingSet (cid:100) ParameterSwComponentType: here the ConstantSpecificationMappingSet is directly associated by the ParameterSwComponentType. (cid:99)()
• [constr_1031] NvBlockSwComponentType references ConstantSpecificationMappingSet (cid:100) NvBlockSwComponentType: in this case the ConstantSpecificationMappingSet is associated with the aggregated NvBlockDescriptor. (cid:99)()
/#@Hierarchical

Figure 5.59: Constant Mapping
Table 5.131: ConstantSpecificationMapping
Table 5.132: ConstantSpecificationMappingSet
Figure 5.60: Aggregation of ConstantSpecificationMappingSet

#@SECTION: 5.7.4 Initial Values For CalibrationParameters
#@CLASS: CalibrationParameterValue
#@CLASS: CalibrationParameterValueSet
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterProvideComSpec
#@CLASS: ParameterRequireComSpec
#@CLASS: ValueSpecification
#@CLASS: ApplicationDataType
#@CLASS: ImplementationDataType

[TPS_SWCT_01188] Definition of calibration data sets through RTE-generator and compiler (cid:100) It is possible to provide sets of initial values for calibration parameters which are instance specific, thus overriding any initial values predefined by a ParameterDataPrototype, ParameterRequireComSpec or a ParameterProvideComSpec.
This allows to create the calibration data sets through RTE-generator and compiler. These initial values are specified in CalibrationParameterValueSet and CalibrationParameterValue. The latter aggregates a ValueSpecification in two different roles:
• applInitValue for data structured according to ApplicationDataType. In this case the values are defined in the physical domain.
• implInitValue for data structured according to ImplementationDataType. In this case the values are defined in the numerical domain.
(cid:99)(RS_SWCT_03175) 

Anyhow, these initial values can be imported from e.g. an ASAM CDF file.

Figure 5.61: Calibration Parameter Values
Table 5.133: CalibrationParameterValueSet
Table 5.134: CalibrationParameterValue

#@SECTION: 6 Compatibility
#@SECTION: 6.1 Introduction
#@CLASS: ApplicationDataType
#@CLASS: ImplementationDataType
#@CLASS: PortInterface
#@CLASS: PortInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: SwComponentType

In order to connect PortPrototypes of SwComponentTypes, the compatibility of PortPrototypes needs to be verified. This section defines the basic rules for formal compatibility of PortPrototypes.

Compatibility will be defined bottom-up, i.e. first the rules for compatible Autosar DataTypes are set up, then the rules for the different types of PortInterfaces are derived.

Another aspect of compatibility is the question whether two model-elements (e.g. ApplicationDataType vs. ImplementationDataType) can be mapped to each other.

For the compatibility of PortInterfaces basically two options apply:
1. finding of matching pairs of elements of PortInterfaces is based on matching shortName plus the application of compatibility rules for their attributes.
2. a PortInterfaceMapping can be taken to declare two elements of PortPrototypes as compatible without applying further formal checks.

#@SECTION: 6.2 Compatibility of Data Types
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: AutosarDataType

The AUTOSAR meta model defines a number of meta-classes (e.g. ApplicationPrimitiveDataType) that eventually refer to a set of attributes (e.g. a lower boundary for its values) relevant for compatibility checking.

Instantiating a data-type related meta-class defines a data type on M1 level (e.g. temperatureType). In other words: ApplicationPrimitiveDataType is an M2 artifact; it is taken as the template for creating a corresponding M1 artifact temperatureType.

In this context, the issue of compatibility refers to the M1 objects, i.e. the instances of sub-classes of AutosarDataType need to be considered. For this purpose the relevant part of the AUTOSAR meta-model need to be fully explored with respect to compatibility.

#@SECTION: 6.2.1 ApplicationDataType
#@SECTION: 6.2.1.1 ApplicationPrimitiveDataType
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationCompositeDataTypeSubElementRef
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: DataPrototype
#@CLASS: DataPrototypeMapping

[constr_1047] Compatibility of ApplicationPrimitiveDataTypes (cid:100) Instances of ApplicationPrimitiveDataType are compatible if and only if one of the following conditions applies:

1. All of the following subconditions apply: (a) They have the same category (see table in figure 5.8). (b) The swDataDefProps attached to the M1 data types are compatible. The meaning of this statement is explained in section 6.2.4.

2. In the context of using the ApplicationPrimitiveDataType, a DataPrototypeMapping exists that refers to a DataPrototype typed by one of the ApplicationPrimitiveDataTypes in the role firstDataPrototype and to another DataPrototype typed by the other ApplicationPrimitiveDataType in the role secondDataPrototype.

3. In the context of using the ApplicationPrimitiveDataType, a DataPrototypeMapping exists that refers to a DataPrototype typed by the ApplicationPrimitiveDataType in the role secondDataPrototype and to another DataPrototype typed by an ApplicationCompositeDataType in the role firstDataPrototype and additionally for the side of the ApplicationCompositeDataType a corresponding ApplicationCompositeDataTypeSubElementRef exists in the role firstElement that in turn references an ApplicationCompositeElementDataPrototype.

(cid:99)()

Please note that it is not required that the shortNames of two data types shall be identical in order to consider the two data types as compatible.

#@SECTION: 6.2.1.2 ApplicationCompositeDataType
#@CLASS: ApplicationArrayDataType
#@CLASS: ApplicationArrayElement
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationCompositeDataTypeSubElementRef
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: ApplicationRecordDataType
#@CLASS: ApplicationRecordElement
#@CLASS: AutosarDataTypes
#@CLASS: DataPrototypeMapping
#@CLASS: PortInterfaceMapping
#@CLASS: SubElementMapping

An instance of an ApplicationRecordDataType is never compatible to an instance of an ApplicationArrayDataType unless a PortInterfaceMapping exists that details the terms of compatibility (see [TPS_SWCT_01543]).

[constr_1048] Compatibility of ApplicationRecordDataTypes (cid:100) Instances of ApplicationRecordDataTypes are compatible if and only if one of the following conditions applies:
1. All elements at the same record position are of compatible Autosar DataTypes either ApplicationCompositeDataTypes or ApplicationPrimitiveDataTypes).
2. In the context of a DataPrototypeMapping, for each ApplicationRecordElement of the required ApplicationRecordDataType a SubElementMapping exists such that a ApplicationCompositeDataTypeSubElementRef in the role firstElement or secondElement exists that references the required ApplicationRecordElement and a corresponding ApplicationCompositeDataTypeSubElementRef exists in the other role (i.e. secondElement or firstElement) that in turn references an ApplicationRecordElement of the provided ApplicationRecordDataType. (cid:99)()

[constr_1049] Compatibility of ApplicationArrayDataTypes (cid:100) Instances of ApplicationArrayDataType are compatible if and only if one of the following conditions applies:
1. All of the following subconditions apply:
(a) Their elements are of a compatible AutosarDataTypes (either ApplicationPrimitive or ApplicationCompositeDataTypes DataTypes).
(b) The attributes maxNumberOfElements and arraySizeSemantics (given the existence) have identical values.
2. In the context of a DataPrototypeMapping, for the ApplicationArrayElement of the required ApplicationArrayDataType a SubElementMapping exists such that a ApplicationCompositeDataTypeSubElementRef in the role firstElement or secondElement exists that references the required ApplicationArrayElement and a corresponding ApplicationCompositeDataTypeSubElementRef exists in the other role (i.e. secondElement or firstElement) that in turn references an ApplicationArrayElement of the provided ApplicationArrayDataType. (cid:99)()

#@SECTION: 6.2.2 ImplementationDataType
#@CLASS: DataPrototype
#@CLASS: DataPrototypeMapping
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeElement
#@CLASS: ImplementationDataTypeSubElementRef
#@CLASS: ModeDeclaration

[constr_1050] Compatibility of ImplementationDataTypes (cid:100) Instances of ImplementationDataType are compatible if and only if after all type-references are resolved one of the following rules apply:

1. All of the following subconditions apply:
(a) They have the same category (see table 5.18)
(b) They have the identical structure (this refers to ImplementationDataTypeElement and their subElements).
(c) The attributes arraySize and arraySizeSemantics have (given the existence) identical values.
(d) The swDataDefProps attached to the M1 data types are compatible. The meaning of this statement is explained in section 6.2.4.

2. In the context of using the ImplementationDataType, a DataPrototypeMapping exists that refers to a DataPrototype typed by one of the ImplementationDataTypes in the role firstDataPrototype and to another DataPrototype typed by the other ImplementationDataType in the role secondDataPrototype.

3. In the context of using the ImplementationDataType, a DataPrototypeMapping exists that refers to a DataPrototype typed by the ImplementationDataTypes in the role secondDataPrototype and to another DataPrototype typed by an ImplementationDataType with a subElement in the role firstDataPrototype and additionally for the side of the ImplementationDataType with a subElement a corresponding ImplementationDataTypeSubElementRef exists in the role firstElement that in turn references an ImplementationDataTypeElement.
(cid:99)()

Please note that it is not required that the shortNames of two data types shall be identical in order to consider the two data types as compatible.

The following constraint applies for the case that mode manager and mode user are using different ImplementationDataTypes. From the point of view of the RTE there is only the necessity that all possible numbers used to represent ModeDeclarations of the mode manager has to fit into the range of the data type used for the mode user.

[constr_1168] Compatibility of ImplementationDataTypes used used in the ModeRequestTypeMap (cid:100) Both ImplementationDataTypes shall fulfill [constr_1167]. In addition to that, the possible numbers used for representing ModeDeclarations on the side of the mode manager shall match the supported range of the ImplementationDataType used for representing ModeDeclarations on the side of the mode user (see [constr_1075]). (cid:99)()

#@SECTION: 6.2.3 Compatibility of SwBaseType
#@CLASS: SwBaseType

[constr_1220] Compatibility of SwBaseType (cid:100) Two SwBaseTypes are compatible if and only if attributes baseTypeSize respectively maxBaseTypeSize, byteOrder, memAlignment, baseTypeEncoding, and nativeDeclaration have identical values. (cid:99)()

#@SECTION: 6.2.4 Compatibility of SwDataDefProps
#@CLASS: ApplicationValueSpecification
#@CLASS: NumericalValueSpecification
#@CLASS: RecordValueSpecification
#@CLASS: TextValueSpecification
#@CLASS: SwDataDefProps
#@CLASS: Unit
#@CLASS: ValueSpecification
#@CLASS: ConstantReference
#@CLASS: ArrayValueSpecification
#@CLASS: CompuMethod

[constr_1051] Compatibility of SwDataDefProps (cid:100) SwDataDefProps are compatible if and only if:

1. They refer to compatible Unit definitions, or neither of them has an associated Unit.
2. They refer to compatible conversion methods (see chapter 6.2.4.5) or neither of them associates such a method.
3. One of the following conditions apply to ValueSpecifications aggregated in the role invalidValue for being considered compatible (after following and resolving indirections created by ConstantReference):
   (a) both are ApplicationValueSpecifications and the values are compatible according to [TPS_GST_02501].
   (b) both are NumericalValueSpecifications and the values are compatible according to [TPS_GST_02501].
   (c) both are TextValueSpecifications and the values are identical.
   (d) both are ArrayValueSpecifications and the values are identical.
   (e) both are RecordValueSpecifications and the values are identical.
   (f) if one is a NumericalValueSpecification and the other one is an ApplicationValueSpecification then the check for compatibility shall apply the CompuMethod on the physical value such that a comparison on the implementation level becomes possible. [TPS_GST_02501] applies.
4. They refer to compatible data constraints dataConstr.
5. They refer to compatible swRecordLayouts

All other attributes (e.g. swCalibrationAccess do not affect compatibility). (cid:99)()

if one is a NumericalValueSpecification and the other one is an ApplicationValueSpecification and the application of the CompuMethod on the side of the ApplicationValueSpecification does not yield a valid number a comparison is not possible.


#@SECTION: 6.2.4.1 Compatibility of Units
#@CLASS: AutosarDataPrototype
#@CLASS: AutosarDataType
#@CLASS: AutosarDataPrototype
#@CLASS: ValueSpecification
#@CLASS: PhysicalDimension
#@CLASS: Unit
#@CLASS: ApplicationValueSpecification
#@CLASS: ApplicationRuleBasedValueSpecification
#@CLASS: RuleBasedValueCont
#@CLASS: SwValueCont

[constr_1052] Compatibility of Units (cid:100) Two Unit definitions are compatible if and only if:
1. They have compatible (see [TPS_GST_02501]) values of attributes factorSiToUnit and offsetSiToUnit.
2. They either refer to identical definitions of PhysicalDimension or neither of them associates a PhysicalDimension.
(cid:99)()

Please note that it is not required that the shortNames of two Units shall be identical in order to consider the two units as compatible.

[TPS_SWCT_01492] Default values for factorSiToUnit and offsetSiToUnit (cid:100) The default value of attribute Unit.factorSiToUnit is 1. The default value of attribute Unit.offsetSiToUnit is 0. (cid:99)()

Further constraints apply specifically for the handling of Units in the context of assigning a ValueSpecification to a given AutosarDataPrototype:

[constr_1391] Compatibility of Units in the context of assignment using an ApplicationValueSpecification (cid:100) If an ApplicationValueSpecification is used in the context of an assignment to an AutosarDataPrototype then the ApplicationValueSpecification.swValueCont.unit shall be compatible to the Unit used in the definition of the given AutosarDataPrototype, i.e. AutosarDataType.swDataDefProps.unit. (cid:99)()

[constr_1392] Compatibility of Units in the context of assignment using an ApplicationRuleBasedValueSpecification (cid:100) If an ApplicationRuleBasedValueSpecification is used in the context of an assignment to an AutosarDataPrototype then the ApplicationRuleBasedValueSpecification.swValueCont.unit shall be compatible to the Unit used in the definition of the given AutosarDataPrototype, i.e. AutosarDataType.swDataDefProps.unit. (cid:99)()

[constr_1393] Existence of RuleBasedValueCont.unit (cid:100) For every RuleBasedValueCont the attribute unit shall exist. (cid:99)()

Please note that the multiplicity of RuleBasedValueCont.unit is set to 0..1 while the multiplicity of the corresponding SwValueCont.unit is set to 1. This inconsistency cannot be resolved by increasing the lower multiplicity of RuleBasedValueCont.unit because this would create an incompatible XML Schema. However, the creation of [constr_1393] effectively yields the same result.

#@SECTION: 6.2.4.2 Compatibility of PhysicalDimensions
#@CLASS: PhysicalDimension
#@CLASS: PhysicalDimensionMapping

[constr_1053] Compatibility of PhysicalDimensions (cid:100) Two PhysicalDimension definitions are compatible if and only if the values of
• lengthExp
• massExp
• timeExp
• currentExp
• temperatureExp
• molarAmountExp
• luminousIntensityExp
are identical and either the shortNames are identical or a PhysicalDimension Mapping exists that maps one of the PhysicalDimensions in the role first PhysicalDimension and the other PhysicalDimension in the role secondPhysicalDimension. (cid:99)()

For clarification, there are some physical dimensions around that share the identical values for the exponents but still have a completely different meaning and shall therefore not be considered compatible. For precisely this reason [constr_1053] requires the shortNames of two PhysicalDimensions to be identical as a prerequisite for compatibility.

For example, there are at least two physical dimensions that share the values of
• lengthExp = 2
• massExp = 1
• timeExp = -2
• currentExp = 0
• temperatureExp = 0
• molarAmountExp = 0
• luminousIntensityExp = 0
The unit described by this set of exponents is usually referred to as "Nm" for newton meter and it can be used for torque just as well as for energy. Obviously, two Units shall never be considered compatible if one refers to torque and the other one refers to energy.

#@SECTION: 6.2.4.3 Compatibility of Data Constraints
#@CLASS: DataConstr
#@CLASS: PhysConstrs

The compatibility of two DataConstrs depends on the context in which the owning data elements are connected:

[constr_1126] Compatibility of DataConstrs (cid:100) The DataConstr (e.g. the limits) defined by the type of the providing data element shall be within the constraints defined by the type of the requiring data element. (cid:99)()

In addition, it is always allowed if the requiring element defines no constraints.

[constr_1278] PhysConstrs references a Unit (cid:100) DataConstrs are only compatible if the DataConstr.dataConstrRule.physConstrs.unit are compatible or neither DataConstr.dataConstrRule.physConstrs.unit exist. (cid:99)()

[constr_1054] No DataConstr available at the provider (cid:100) If the provider defines no constraints it is only compatible with a receiver which also defines no constraints at all. (cid:99)()

In other words, this is not a compatibility rule for the types but for the data prototypes.

#@SECTION: 6.2.4.4 Compatibility in case of ImplementationDataType
#@CLASS: ImplementationDataType
#@CLASS: SwBaseType
#@CLASS: SwDataDefProps
#@CLASS: BswModuleEntry
#@CLASS: ApplicationDataType
If the SwDataDefProps are owned by an ImplementationDataType further conditions shall be met to ensure compatibility.

Note that depending on the category of the ImplementationDataType, at most one of these four constraints is actually relevant:

1. category [constr_1055] ImplementationDataType has category VALUE (cid:100) The attributes baseType shall refer to a compatible SwBaseType (cid:99)() (see explanation in the following rule). The rules regarding the compatibility of SwBaseTypes are covered by [constr_1220].

2. category TYPE_REFERENCE: [constr_1056] ImplementationDataType has category TYPE_REFERENCE (cid:100) The ImplementationDataTypes referenced by the attributes SwDataDefProps.implementationDataType shall be compatible. (cid:99)()

3. category DATA_REFERENCE: [constr_1057] ImplementationDataType has category DATA_REFERENCE (cid:100) The attributes SwDataDefProps.swPointerTargetProps shall have identical targetCategory and shall refer to SwDataDefProps where all attributes are identical (cid:99)() (in other words, the target types of the pointers shall be identical, not only compatible).

4. category FUNCTION_REFERENCE: [constr_1058] ImplementationDataType has category FUNCTION_REFERENCE (cid:100) The attributes SwDataDefProps.swPointerTargetProps.functionPointerSignature shall refer to BswModuleEntrys which each resolve to the same function signature. (cid:99)()

Please note that the term "same signature" refers to the following predicates:
• same number of arguments
• return values and arguments shall have identical - not only compatible data types

Two SwBaseTypes are compatible (in the sense of allowing a connection of ports via the RTE) if a simple conversion rule exists between the two types in the underlying programming language. Admittedly, this is a rather weak condition. But because the deﬁnition of SwBaseTypes can contain a nativeDeclaration it is not possible to state this rule more speciﬁcally. However, conversion between base types is considered as a less common use case than the simple case that the connected types just contain two identical SwBaseTypes (which is of course included in the rule).

Please note, that in addition the existence of ApplicationDataTypes also constraints the possible SwBaseTypes via the compatibility rules for the mapping between ApplicationDataTypes and ImplementationDataType as will be explained in more detail in chapter 6.2.5.

#@SECTION: 6.2.4.5 Compatibility of CompuMethods
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: TextTableMapping
#@CLASS: CompuScale
#@CLASS: CompuMethod
[constr_1163] Compatibility of CompuMethods (cid:100) Two CompuMethod definitions are compatible if and only if all attributes except • shortName • desc • introduction • longName • adminData • annotation • displayFormat are identical and the compuScales and units are compatible. (cid:99)()

[constr_1153] Applicability of compatibility requirements for CompuScales (cid:100) Compatibility requirements for CompuScales shall only apply for CompuScales where the category of the enclosing CompuMethod is one of the following: • SCALE_LINEAR_AND_TEXTTABLE • SCALE_RATIONAL_AND_TEXTTABLE • TEXTTABLE • TAB_NOINTP • BITFIELD_TEXTTABLE • LINEAR • RAT_FUNC • IDENTICAL (cid:99)()

[constr_1154] Compatibility of CompuScales for sender-receiver communication and similar use cases (cid:100) For sender-receiver communication and similar use cases, it is required that the set of CompuScales defined in the CompuMethod of the provider of the communication (i.e. on the side of the PPortPrototype) shall be a subset of the set of CompuScales defined in the CompuMethod on the required side (i.e. on the side of the RPortPrototype). (cid:99)()

[constr_1155] Compatibility of CompuScales for client-server communication (cid:100) For client-server communication, the following rules apply: 
For arguments of direction IN the CompuScales defined in the CompuMethod of the client (i.e. on the side of the RPortPrototype) shall be a subset of the set of CompuScales defined in the CompuMethod supported at the server (i.e. on the side of the PPortPrototype). 
For arguments of the direction OUT the set of CompuScales defined in the CompuMethod of the server (i.e. on the side of the PPortPrototype) shall be a subset of the set of CompuScales defined in the CompuMethod supported at the client (i.e. on the side of the RPortPrototype). For arguments of direction INOUT the set of CompuScales defined in the CompuMethod of server and client shall be identical. (cid:99)()

[constr_1156] Relevance of "names" of CompuScales (cid:100) CompuScales which contribute to tabular conversion by having a compuConst are compatible if and only if the "names" of the compuScales, (namely shortLabel, compuConst and symbol) are equal. If the scale has no compuConst, "names" of CompuScales are not relevant for compatibility. (cid:99)()

[constr_1157] Applicability of constraints of CompuScales (cid:100) The constraints [constr_1154], [constr_1155], and [constr_1156] shall only apply in the absence of a TextTableMapping which shall take precedence regarding the compatibility if it exists. (cid:99)()

[constr_1176] Compatibility of CompuScales of category LINEAR and RAT_FUNC (cid:100) CompuScales of category LINEAR and RAT_FUNC are considered compatible if they yield the same conversion. (cid:99)() 

In other words, `n₀+n₁*phys` / `d₀+d₁*phys` is compatible to `N₀+N₁*phys` / `D₀` if `n₀ ~ N₀ && n₁ ~ N₁ && d₀ ~ D₀ && d₁ ~ 0`.

Note that ~ indicates compatibility of numerical values according to [TPS_GST_02501]

[constr_1192] Compatibility of "IDENTICAL" to "RAT_FUNC" or "LINEAR" (cid:100) Similar to [constr_1176], a CompuScale where the category of the enclosing CompuMethod is set to IDENTICAL is considered compatible to a CompuScale where the category of the enclosing CompuMethod is set to RAT_FUNC or LINEAR if the following rule applies: 
int = (N0+N1*phys+Ni*physi) / (D0+D1*phys+Di*physi) = phys 
(cid:99)() 

This is the case for N0 ~ 0 && D0 ~ 1 && N1 ~ 1 && D1 ~ 0 && Ni ~ Di ~ 0 ∀i > 1.

#@SECTION: 6.2.4.6 Compatibility of Record Layouts
[constr_1162] Compatibility of SwRecordLayouts (cid:100) Two SwRecordLayout definitions are compatible if and only if all attributes except
• shortName
• desc
• introduction
• longName
• adminData
• annotation
are identical. (cid:99)()

#@SECTION: 6.2.5 Compatibility of ApplicationDataType and ImplementationDataType
#@CLASS: ApplicationDataType
#@CLASS: ImplementationDataType
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SwBaseType
#@CLASS: DataTypeMap
#@CLASS: DataPrototype
#@CLASS: PortInterface
#@CLASS: CompuMethod

The usage of ApplicationDataTypes implies that also a corresponding ImplementationDataType exists at a certain point in time. The ImplementationDataType is required as the basis for configuring and generating the RTE and/or contract phase header files.

[TPS_SWCT_01461] Existence of ImplementationDataType (cid:100) The existence of ImplementationDataTypes is not required until the methodology step of generating an RTE or executing the RTE contract phase. Before arriving at this step in the methodology, it is perfectly feasible to use only ApplicationDataTypes for describing the semantics of software-components. (cid:99)()

As a consequence, it is necessary to define compatibility rules that unambiguously clarify the conformance of an ApplicationDataType with an ImplementationDataType and vice versa.

Please note that this kind of compatibility also supports situations where e.g. a dataElement typed by an ApplicationDataType without a corresponding ImplementationDataType in a PPortPrototype should be connected to a dataElement typed by an ImplementationDataType in an RPortPrototype.

In general, the compatibility rules for allowing a data type mapping are the same as the rules for connections. Exceptions are explicitly stated in the rules below.

Several rules depend on the category of the data types:
#@Hierarchical
1. As a general rule, if an ImplementationDataType of category TYPE_REFERENCE is targeted by a type mapping or port connection all the rules given below apply to the ImplementationDataType which is finally valid after resolving all such references. This is not repeated in all rules. As an example, if we say that something can be mapped/connected to an ImplementationDataType of category VALUE this shall include the possibility of mapping/connecting to an ImplementationDataType of category TYPE_REFERENCE which refers to another ImplementationDataType of category VALUE.

2. [constr_1059] Compatibility of data types with category VALUE (cid:100) An ApplicationDataType of category VALUE can only be mapped/connected to an ImplementationDataType which also has category VALUE. (cid:99)() 

In this case, the ImplementationDataType.baseType shall be able to express all the numerical values required by the ApplicationDataType, see Figure 5.6. This condition is fulfilled if the numerical range which can be expressed by the SwBaseType at least covers the range defined by the limits in ApplicationDataType.swDataDefProps.dataConstr (which are either internal limits or physical limits to be converted via the CompuMethod which also has to be provided by the ApplicationDataType). The condition is also fulfilled if the SwBaseType covers the range defined in the CompuMethod for an enumeration (see 5.5.1.3). Note that for sender-receiver communication of a data element via a network there is the possibility to reduce the numerical range against what has been defined via the corresponding data type. However, this is not achieved via mapping to another ImplementationDataType at the data element itself but via the networkRepresentation of the ComSpec (for further explanation of this aspect see section 4.5.1).

3. [constr_1060] Compatibility of data types with category ARRAY, VAL_BLK (cid:100) An ApplicationDataType of category ARRAY, VAL_BLK can only be mapped/connected to 
• an ImplementationDataType of category ARRAY or 
• an ImplementationDataType that represents a Variable-Size Array Data Type (see [TPS_SWCT_01610]). (cid:99)() 

In this case, the array size, the arraySizeSemantics (given that it exists) and the type of the array elements of the ImplementationDataType shall be such that they can be mapped resp. transferred 1:1 by order to the corresponding application data and vice versa. Note that in case of mapping between arrays it is not required that a DataTypeMap exists between the data types of the array elements or that the respective ShortNames are identical.

4. [constr_1061] Compatibility of data types with category STRUCTURE (cid:100) An ApplicationDataType of category STRUCTURE can only be mapped/connected to an ImplementationDataType of category STRUCTURE. (cid:99)() 

This means, that the corresponding pairs of elements shall also have compatible types. Note that it is not required that the data types of the single elements have identical ShortNames or that a DataTypeMap exists for each pair of single element.

5. [constr_1063] Compatibility of data types with category BOOLEAN (cid:100) An ApplicationDataType of category BOOLEAN can only be mapped/connected to an ImplementationDataType of category VALUE. (cid:99)()

6. [constr_1064] Compatibility of data types with category COM_AXIS, RES_AXIS, CURVE, MAP, CUBOID, CUBE_4, or CUBE_5 (cid:100) An ApplicationDataType of category COM_AXIS, RES_AXIS, CURVE, MAP, CUBOID, CUBE_4, or CUBE_5 can only be mapped/connected to an ImplementationDataType of category STRUCTURE or ARRAY. (cid:99)() 

There are several possibilities how to express these types via plain or nested arrays and/or structures on implementation level. Some examples are given in 5.4.4. In any case, the primitive elements of the implementation type shall fit (by their order in memory) to the corresponding RecordLayout. It is not required, to define DataTypeMaps for the sub-elements or both representations.

7. [constr_1066] Forbidden mappings to ImplementationDataType (cid:100) An ApplicationDataType shall never be mapped to an ImplementationDataType of of category UNION, DATA_REFERENCE, or FUNCTION_REFERENCE. (cid:99)()
/#@Hierarchical

Concerning the SwDataDefProps of an ApplicationDataType instance resp. an ImplementationDataType instance which shall be mapped/connected on M1, we refer to the table shown in figure 5.39. The following rules apply:
#@Hierarchical
1. The cases where the ImplementationDataType is not allowed to set a property but only "inherits" it from the ApplicationDataType are not relevant for compatibility. These attributes are simply not allowed in the ImplementationDataType.

2. In case that only the ImplementationDataType may "define" the property this definition shall fit into the semantical requirements given by the ApplicationDataType in order to make the two types compatible. This is namely important for the attribute baseType and is explained above in the rule for types of category VALUE.

3. In case the ImplementationDataType may "add" a property it may only add but not change a property defined by the ApplicationDataType (namely note, displayFormat, and swImplPolicy) in order to be compatible. This means that the respective computation methods can be defined in only one of the types in order to be compatible. In all other cases, only the ApplicationDataType may define the computation method.

4. For the compatibility with respect to connectors there are some additional rules for the values of the attribute swImplPolicy which are considered general rules on the level of DataPrototypes and PortInterfaces. Therefore these additional rules are explained in chapter 6.3 and chapter 6.4.4.

5. The case that an ImplementationDataType may "redefine" a property which is already set by the ApplicationDataType is not considered as relevant for the compatibility with respect to mapping of the types in general but of course there may be project specific rules as to which redefinition is allowed (e.g. for swAddrMethod or dataConstr). See also 5.5.3 about data constraints.

6. For the compatibility with respect to connectors the attribute dataConstr shall be treated in the same way as for compatibility of data types in general, for more details please refer to 6.2.4.
/#@Hierarchical

#@SECTION: 6.3 Compatibility of Variable Data Prototypes and Parameter Data Prototypes
#@CLASS: ApplicationCompositeDataType
#@CLASS: ApplicationCompositeDataTypeSubElementRef
#@CLASS: ApplicationCompositeElementDataPrototype
#@CLASS: ApplicationPrimitiveDataType
#@CLASS: AutosarDataType
#@CLASS: DataPrototype
#@CLASS: DataPrototypeMapping
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeSubElementRef
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: SenderReceiverInterface
#@CLASS: SubElementMapping
#@CLASS: VariableDataPrototype

[constr_1068] Compatibility of VariableDataPrototypes or ParameterDataPrototypes typed by primitive data types (cid:100) Two VariableDataPrototypes or ParameterDataPrototypes of ApplicationPrimitiveDataTypes or ImplementationDataTypes of category VALUE, BOOLEAN, or STRING are compatible if and only if one of the following conditions applies:

1. All of the following subconditions apply:
(a) They are typed by (read “refer to”) compatible AutosarDataTypes
(b) The two VariableDataPrototypes or ParameterDataPrototypes have identical shortNames This is required to map VariableDataPrototypes in unordered SenderReceiverInterfaces, NvDataInterfaces and ParameterInterfaces.
(c) The attribute swImplPolicy is either set to queued for both or none of the VariableDataPrototypes.

2. In the context of a DataPrototypeMapping, one of the applicable VariableDataPrototypes or ParameterDataPrototypes is referenced by the DataPrototypeMapping in the role firstDataPrototype and the other VariableDataPrototypes or ParameterDataPrototypes is referenced by the same DataPrototypeMapping in the role secondDataPrototype.

(cid:99)()

[constr_1187] Compatibility of VariableDataPrototypes or ParameterDataPrototypes typed by composite data types (cid:100)

DataPrototypes of ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY are compatible if one of the following conditions evaluates to true:

1. The underlying ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY are identical

2. The underlying ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY fulfill the following condition:
• They consist of the same number of elements and
• They are composed of compatible AutosarDataTypes (either ApplicationCompositeDataTypes or ImplementationDataTypes of category STRUCTURE or ARRAY OR ApplicationPrimitiveDataTypes or ImplementationDataTypes of category VALUE, BOOLEAN, or STRING) in the same order and
• All attributes match exactly, with the exception of the shortName of the M1 AutosarDataType.

3. In the context of a DataPrototypeMapping, for each ApplicationCompositeElementDataPrototype of the required DataPrototype a SubElementMapping exists such that a ApplicationCompositeDataTypeSubElementRef in the role firstElement or secondElement exists that references the required ApplicationCompositeElementDataPrototype and a corresponding ApplicationCompositeDataTypeSubElementRef exists in the other role (i.e. secondElement or firstElement) that in turn references an ApplicationCompositeElementDataPrototype of the provided ApplicationCompositeDataType.

4. If and only if the DataPrototype is not typed by an ApplicationDataType but by an ImplementationDataType: in the context of a DataPrototypeMapping, for each ImplementationDataTypeElement of the required DataPrototype a SubElementMapping exists such that a ImplementationDataTypeSubElementRef in the role firstElement or secondElement exists that references the required ImplementationDataTypeElement and a corresponding ImplementationDataTypeSubElementRef exists in the other role (i.e. secondElement or firstElement) that in turn references an ImplementationDataTypeElement of the provided ImplementationDataType.

(cid:99)()

#@SECTION: 6.4 Compatibility of Sender Receiver Interfaces, Parameter Interfaces and Non Volatile Data Interfaces

Please note that this compatibility requirement only satisfies static correctness which means that a receiver shall process a certain data value to correctly interpret the following values.

#@SECTION: 6.4.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
#@CLASS: DataInterface
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: SwConnector
#@CLASS: VariableAndParameterInterfaceMapping
#@CLASS: VariableDataPrototype

The compatibility of SenderReceiverInterfaces, NvDataInterfaces and ParameterInterfaces are considered for connecting of PortPrototypes with an AssemblySwConnector.

[constr_1069] Compatibility of PortPrototypes of different DataInterfaces in the context of AssemblySwConnectors (cid:100) PortPrototypes of different DataInterfaces are compatible if and only if

1. One of the following conditions applies:
(a) For each VariableDataPrototype or ParameterDataPrototype defined in the context of the DataInterface of the required PortPrototype a compatible (see [constr_1068]) VariableDataPrototype or ParameterDataPrototype exists in the DataInterface of the provided PortPrototype. The shortNames of VariableDataPrototypes and ParameterDataPrototypes are used to identify the pair.
(b) A VariableAndParameterInterfaceMapping.dataMapping exists for which the following conditions apply:
i. It is referenced by the corresponding SwConnector.
ii. It references one of the two VariableDataPrototypes or ParameterDataPrototypes in the role firstDataPrototype and the other in the role secondDataPrototype.

2. For each such pair, the values of their isService attributes are identical.

(cid:99)()

The table 6.1 defines which PortInterface elements are compatible depending on the PortInterface type and the swImplPolicy attributes of the PortInterface elements.

#@SECTION: 6.4.2 Connection of Inner and Outer Port via DelegationSwConnector
#@CLASS: DataInterface
#@CLASS: DelegationSwConnector
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: SwConnector
#@CLASS: VariableAndParameterInterfaceMapping
#@CLASS: VariableDataPrototype

The compatibility of SenderReceiverInterfaces, NvDataInterfaces and ParameterInterfaces is considered for connecting of PortPrototypes with a DelegationSwConnector.

[constr_1070] Compatibility of PortPrototypes of different DataInterfaces in the context of DelegationSwConnectors (cid:100) PortPrototypes of different DataInterfaces are compatible if and only if

1. One of the following conditions applies:
   (a) For each VariableDataPrototype or ParameterDataPrototype defined in the context of the DataInterface of the required inner PortPrototype a compatible VariableDataPrototype or ParameterDataPrototype exists in the DataInterface of the required outer PortPrototype. The shortName of VariableDataPrototypes and ParameterDataPrototypes are used to identify the pair. [constr_1071] defines which PortInterface elements are compatible depending on the PortInterface type and the swImplPolicy attributes of the PortInterface elements.
   (b) A VariableAndParameterInterfaceMapping.dataMapping exists for which the following conditions apply:
      i. It is referenced by the corresponding SwConnector.
      ii. It references one of the two VariableDataPrototypes or ParameterDataPrototypes in the role firstDataPrototype and the other in the role secondDataPrototype.

2. One of the following conditions applies:
   (a) For at least one VariableDataPrototype or ParameterDataPrototype defined in the context of the SenderReceiverInterface, NvDataInterface or ParameterInterface of the provided inner PortPrototype a compatible VariableDataPrototype or ParameterDataPrototype exists in the SenderReceiverInterface, NvDataInterface or ParameterInterface of the provided outer PortPrototype. The shortNames of VariableDataPrototypes and ParameterDataPrototypes are used to identify the pair. [constr_1071] defines which PortInterface elements are compatible depending on the PortInterface type and the swImplPolicy attributes of the PortInterface elements.
   (b) A VariableAndParameterInterfaceMapping.dataMapping exists for which the following conditions apply:
      i. It is (if a corresponding SwConnector already exists) referenced by the corresponding SwConnector.
      ii. It references one of the two VariableDataPrototypes or ParameterDataPrototypes in the role firstDataPrototype and the other in the role secondDataPrototype.

3. For each such pair, the values of their isService attributes are identical.

(cid:99)()

#@SECTION: 6.4.3 Connection of Required and Provided Port via PassThroughSwConnector
#@CLASS: DataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: PassThroughSwConnector
#@CLASS: PortInterface
#@CLASS: PortInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: VariableDataPrototype

[constr_1248] Compatibility of PortPrototypes of different DataInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different DataInterfaces are considered compatible if and only if

1. For at least one VariableDataPrototype or ParameterDataPrototype defined in the context of the DataInterface of the required outer PortPrototype a compatible VariableDataPrototype or ParameterDataPrototype exists in the DataInterface of the provided outer PortPrototype.

The table 6.1 defines which elements of PortInterface are considered compatible depending on the type of PortInterface as well as the attribute swImplPolicy of the elements of PortInterfaces.

Either the shortName of VariableDataPrototypes and ParameterDataPrototypes are used to identify the pair or a PortInterfaceMapping exists that defines which differently named elements of PortInterfaces correlate with each other.

2. For each such pair, the values of the PortInterface.isService attributes are identical.

(cid:99)()

#@SECTION: 6.4.4 Compatibility of ParameterDataPrototype and VariableDataPrototype depending on PortInterface Type
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: VariableDataPrototype

Table 6.1 contains a comprehensive description of which combinations of Parameter DataPrototype and VariableDataPrototype used in PortPrototypes typed by various kinds of PortInterfaces are considered compatible.

[constr_1071] compatibility of ParameterDataPrototype and VariableDataPrototype (cid:100) Combinations of ParameterDataPrototype and VariableDataPrototype used in PortPrototypes typed by various kinds of PortInterfaces shall only be allowed where Table 6.1 contains the value “yes”. (cid:99)()

The following legend applies for the abbreviations used in table 6.1:

Interface Element i.e. elements of PortInterface

PDP ParameterDataPrototype

VDP VariableDataPrototype

Port Interface i.e. kind of PortInterface

Prm ParameterInterface

S/R SenderReceiverInterface

NvD NvDataInterface

Table 6.1: Overview of compatibility of ParameterDataPrototype and VariableDataPrototype
<-------------- multimodal context 

| ProvidedPort | | | RequiredPort | | | | |
| RequiredOuterPort | | | RequiredInnerPort | | | | |
| ProvidedInnerPort | | | ProvidedOuterPort | | | | |
| RequiredOuterPort | | | ProvidedOuterPort | | | | |
| **PortInterface** | | | **Prm** | | | **S/R** | | **NvD** |
| **Interface Element** | | | **PDP** | | | **VDP** | | **VDP** |
| **SwImplPolicyEnum** | | | **fixed** | **const** | **standard** | **standard** | **queued** | **standard** |
| **Prm** | **PDP** | **fixed** | yes | yes | yes | yes | no | yes |
| | | **const** | no | yes | yes | yes | no | yes |
| | | **standard** | no | no | yes | yes | no | yes |
| **S/R** | **VDP** | **standard** | no | no | no | yes | no | yes |
| | | **queued** | no | no | no | no | yes | no |
| **NvD** | **VDP** | **standard** | no | no | no | yes | no | yes |
------------------------>

[constr_1071] defines which PortInterface elements are compatible depending on the kind of PortInterface and the swImplPolicy attributes of the PortInterface elements.

[constr_1287] Compatibility of SenderReceiverInterfaces with respect to invalidationPolicy (cid:100) VariableDataPrototypes defined in the context of the SenderReceiverInterface are only compatible if the invalidationPolicys have the same value. (cid:99)()

[TPS_SWCT_01567] Default behavior for invalidationPolicy (cid:100) For Variable DataPrototypes and ParameterDataPrototypes in the context of NvDataInterface respectively ParameterInterface, the invalidationPolicy is treated like “Invalidation is switched off” (dontInvalidate). (cid:99)(RS_SWCT_00200)

#@SECTION: 6.5 Compatibility of Mode Switch Interfaces
#@CLASS: AssemblySwConnector  
#@CLASS: DelegationSwConnector  
#@CLASS: ModeSwitchInterfaces  
#@CLASS: PassThroughSwConnector  

Please note that this compatibility requirement only satisfies static correctness which means that logical consistency is not assured (e.g. that a receiver shall process a certain data value to correctly interpret the following values).  

Note that concerning the compatibility of ModeSwitchInterfaces it is necessary to distinguish between the context of an AssemblySwConnector, the context of an DelegationSwConnector, and the context of a PassThroughSwConnector.

#@SECTION: 6.5.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeInterfaceMapping
#@CLASS: ModeSwitchInterface
#@CLASS: PortPrototype
#@CLASS: SwConnector

Here, the compatibility of ModeSwitchInterfaces is considered for the context of an AssemblySwConnector.

[constr_1072] Compatibility of ModeSwitchInterfaces in the context of an AssemblySwConnector (cid:100) PortPrototypes of different ModeSwitchInterfaces are compatible if and only if

1. One of the following conditions applies:
   (a) For the ModeDeclarationGroupPrototype defined in the context of the ModeSwitchInterface of the required PortPrototype a compatible ModeDeclarationGroupPrototype exists in the ModeSwitchInterface of the provided PortPrototype.
   (b) A ModeInterfaceMapping.modeMapping exists for which the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two ModeDeclarationGroupPrototypes in the role firstModeGroup and the other in the role secondModeGroup.

2. For each such pair, the values of their isService attributes are identical.

(cid:99)()

#@SECTION: 6.5.2 Connection of Inner and Outer Port via DelegationSwConnector
#@CLASS: DelegationSwConnector
#@CLASS: ModeSwitchInterface
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: SwConnector

Here, the compatibility of ModeSwitchInterfaces is considered for the context of a DelegationSwConnector.

[constr_1073] Compatibility of ModeSwitchInterfaces in the context of an DelegationSwConnector (cid:100) PortPrototypes of different ModeSwitchInterfaces are compatible if and only if

1. One of the following conditions applies:
   (a) For the ModeDeclarationGroupPrototype defined in the context of the ModeSwitchInterface of the inner PortPrototype a compatible ModeDeclarationGroupPrototype exists in the ModeSwitchInterface of the outer PortPrototype.
   (b) A ModeInterfaceMapping.modeMapping exists for which the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two ModeDeclarationGroupPrototypes in the role firstModeGroup and the other in the role secondModeGroup.
2. For each such pair, the values of their isService attributes are identical.
(cid:99)()

#@SECTION: 6.5.3 Connection of Outer and Outer Port via PassThroughSwConnector
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeInterfaceMapping
#@CLASS: ModeSwitchInterface
#@CLASS: PassThroughSwConnector
#@CLASS: PortInterface
#@CLASS: PortPrototype

[constr_1249] Compatibility of ModeSwitchInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different ModeSwitchInterfaces are considered compatible if and only if

1. For the ModeDeclarationGroupPrototype defined in the context of the ModeSwitchInterface of the required outer PortPrototype a compatible ModeDeclarationGroupPrototype exists in the ModeSwitchInterface of the provided outer PortPrototype. Either the shortNames of the ModeDeclarationGroupPrototypes are used to identify the pair or a ModeInterfaceMapping exists that maps the corresponding ModeDeclarationGroupPrototypes.

2. For each such pair, the values of the PortInterface.isService attributes are identical.

(cid:99)()

#@SECTION: 6.6 Compatibility of Mode Declaration Group Prototypes
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeDeclarationGroupPrototypeMapping
#@CLASS: ModeDeclarationGroups

[constr_1074] Compatibility of ModeDeclarationGroupPrototypes (cid:100)
ModeDeclarationGroupPrototypes are compatible if and only if one of the following conditions applies:
1. They are typed by (read "refer to") compatible ModeDeclarationGroups.
2. A ModeDeclarationGroupPrototypeMapping exists that identifies the differently named ModeDeclarationGroupPrototypes that correlate with each other. [constr_1210] applies.
(cid:99)()

#@SECTION: 6.7 Compatibility of Mode Declaration Groups
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeDeclarationMapping
#@CLASS: ModeTransition

[constr_1075] Compatibility of ModeDeclarationGroups (cid:100) ModeDeclarationGroups are compatible if and only if one of the following conditions applies:
1. All of the following subconditions apply:
(a) They define an identical number of ModeDeclarations.
(b) Each ModeDeclaration on the required side corresponds to a ModeDeclaration on the provided side with an identical shortName.
(c) The initialModes on both sides refer to ModeDeclarations with identical shortNames.
(d) The attribute ModeDeclarationGroup.modeUserErrorBehavior.errorReactionPolicy has identical values on both sides.
(e) The attribute ModeDeclarationGroup.modeManagerErrorBehavior.errorReactionPolicy has identical values on both sides.
(f) The attribute ModeDeclarationGroup.modeUserErrorBehavior.defaultMode either does not exist on both sides or refers on both sides to ModeDeclarations with identical shortNames.
(g) The attribute ModeDeclarationGroup.modeManagerErrorBehavior.defaultMode either does not exist on both sides or refers on both sides to ModeDeclarations with identical shortNames.
(h) one of the following subconditions applies:
• the attribute category has the value ALPHABETIC_ORDER on both sides.
• the attribute category has the value EXPLICIT_ORDER on both sides and the matching ModeDeclarations according to 1(b) have the identical values of the attributes ModeDeclaration.value and also the value of ModeDeclarationGroup.onTransitionValue matches on both sides.
2. A ModeDeclarationMapping is applied which identifies the corresponding ModeDeclarations.
In addition, the compatibility of corresponding ModeTransitions shall be checked, i.e. [constr_1194] and [constr_1245] apply. (cid:99)()

[constr_1245] Consideration of ModeTransitions for the compatibility of ModeDeclarationGroups (cid:100) One of the following conditions for the consideration of ModeTransitions for the compatibility of ModeDeclarationGroups shall apply:
• Either the mode provider or the mode user define ModeTransitions.
• The ModeTransitions defined in the context of the mode provider are identical to the ModeTransitions defined in the context of the mode user or a ModeDeclarationMapping mapping is applied. (cid:99)()

[constr_1194] Identical ModeTransitions (cid:100) Two ModeDeclarationGroups contain identical modeTransitions if and only if
1. For each ModeTransition defined in the context of the mode provider one ModeTransition with the same shortName is defined in the context of the mode user.
2. Each pair of ModeTransitions in both ModeDeclarationGroups identified by their respective shortName have identical targets (in terms of the shortName of the referenced ModeDeclaration) of the references enteredMode and exitedMode. (cid:99)()

#@SECTION: 6.8 Compatibility of Argument Prototypes
#@CLASS: ArgumentDataPrototype
#@CLASS: AutosarDataType
#@CLASS: ClientServerOperationMapping

[constr_1076] Compatibility of ArgumentDataPrototypes (cid:100) Two ArgumentDataPrototypes are compatible if and only if

1. They are typed by compatible AutosarDataTypes or a ClientServerOperationMapping.argumentMapping exists that references one ArgumentDataPrototype in the role firstDataPrototype and the other ArgumentDataPrototype in the role secondDataPrototype.

2. They have the same value of the argument direction (in, out or inout), i.e. [constr_1268] applies.

(cid:99)()

#@SECTION: 6.9 Compatibility of Application Errors
#@CLASS: ApplicationError
#@CLASS: ClientServerInterfaceMapping

[constr_1077] Compatibility of ApplicationErrors (cid:100) Two ApplicationErrors are compatible if and only if one of the following conditions applies:

1. All of the following subconditions apply:
(a) They have the same shortName.
(b) They have the same attributes. Especially the errorCode shall be identical in both ApplicationErrors.

2. A ClientServerInterfaceMapping.errorMapping exists that references one of the ApplicationErrors in the role firstApplicationError and the other ApplicationErrors in the role secondApplicationError.

(cid:99)()

#@SECTION: 6.10 Compatibility of Client/Server Operations
#@CLASS: ArgumentDataPrototype
#@CLASS: ClientServerOperation

[constr_1078]Compatibility of ClientServerOperations (cid:100) Two ClientServerOperations are compatible if their signatures match. In particular, they are compatible if and only if:

1. They have the same number of ArgumentDataPrototypes.
2. The n-th arguments of both ClientServerOperations are compatible. This implies ordering of ArgumentDataPrototypes.
3. They have the same shortName (again allows for mapping in PortInterfaces).
4. The required ClientServerOperation specifies a compatible ApplicationError for each ApplicationError that is possibly raised by the provided ClientServerOperation, maybe more. Thereby, ClientServerOperations that refer to a possibleError that represents the value E_OK are compatible to ClientServerOperations that do refer to possibleErrors where none of them represents the value E_OK. (cid:99)()

#@SECTION: 6.11 Compatibility of Client Server Interfaces
Please note that this compatibility requirement only satisfies static correctness which means that a client shall call a certain operation to allow the server to work correctly.

#@SECTION: 6.11.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: ClientServerInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: SwConnector

[constr_1079] Compatibility of ClientServerInterfaces in the context of an AssemblySwConnector (cid:100) ClientServerInterfaces are compatible if and only if

1. One of the following conditions applies:
   (a) For each ClientServerOperation defined in the context of the ClientServerInterface of the required PortPrototype a compatible ClientServerOperation exists in the ClientServerInterface of the provided PortPrototype. The shortNames of ClientServerOperations are used to identify the pair.
   (b) A ClientServerInterfaceMapping.operationMapping exists for which the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two ClientServerOperations in the role firstOperation and the other in the role secondOperation.

2. For each such pair, the values of their isService attributes are identical.

(cid:99)()

#@SECTION: 6.11.2 Connection of Inner and Outer Port via DelegationSwConnector
#@CLASS: ClientServerInterface
#@CLASS: ClientServerInterfaceMapping
#@CLASS: ClientServerOperation
#@CLASS: DelegationSwConnector
#@CLASS: PortPrototype
#@CLASS: SwConnector

[constr_1080] Compatibility of ClientServerInterfaces in the context of an DelegationSwConnector (cid:100) ClientServerInterfaces are compatible if and only if

1. One of the following conditions applies:
   (a) For each ClientServerOperation defined in the context of the ClientServerInterface of the required inner PortPrototype a compatible ClientServerOperation exists in the ClientServerInterface of the required outer PortPrototype. The shortNames of ClientServerOperations are used to identify the pair.
   (b) A ClientServerInterfaceMapping.operationMapping exists for which the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two ClientServerOperations in the role firstOperation and the other in the role secondOperation.

2. One of the following conditions applies:
   (a) For at least one ClientServerOperation defined in the context of the ClientServerInterface of the provided inner PortPrototype a compatible ClientServerOperation exists in the ClientServerInterface of the provided outer PortPrototype. The shortNames of ClientServerOperations are used to identify the pair.
   (b) A ClientServerInterfaceMapping.operationMapping exists for which the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two ClientServerOperations in the role firstOperation and the other in the role secondOperation.

3. For each such pair, the values of their isService attributes are identical.

(cid:99)()

#@SECTION: 6.11.3 Connection of Outer and Outer Port via PassThroughSwConnector
#@CLASS: ClientServerInterface
#@CLASS: ClientServerInterfaceMapping
#@CLASS: ClientServerOperation
#@CLASS: PassThroughSwConnector
#@CLASS: PortPrototype

[constr_1250] Compatibility of ClientServerInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different ClientServerInterfaces are considered compatible if and only if:

1. For at least one ClientServerOperation defined in the context of the ClientServerInterface of the provided outer PortPrototype a compatible ClientServerOperation exists in the ClientServerInterface of the required outer PortPrototype. Either the shortNames of the ClientServerOperations are used to identify the pair or a ClientServerInterfaceMapping exists that maps the corresponding ClientServerOperations.

2. For each such pair, the values of the PortInterface.isService attributes are identical.
(cid:99)()

#@SECTION: 6.12 Compatibility of Trigger Interfaces
Please note that this compatibility requirement only satisfies static correctness which means that a client shall call a certain operation to allow the server to work correctly. Logical consistency is not assured (e.g. that a client shall call a certain operation to allow the server to work correctly).

#@SECTION: 6.12.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
#@CLASS: PortPrototype
#@CLASS: SwConnector
#@CLASS: TriggerInterface
#@CLASS: TriggerInterfaceMapping
#@CLASS: Trigger

[constr_1081] Compatibility of TriggerInterfaces in the context of an AssemblySwConnector (cid:100) TriggerInterfaces are compatible if and only if

1. One of the following conditions applies:
   (a) For each Trigger defined in the context of the TriggerInterface of the required PortPrototype a compatible Trigger exists in the TriggerInterface of the provided PortPrototype. The shortNames of Trigger are used to identify the pair.
   (b) A TriggerInterfaceMapping.triggerMapping exists for which the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two Triggers in the role firstTrigger and the other in the role secondTrigger.

2. For each such pair, the values of their isService attributes are identical.

(cid:99)()

#@SECTION: 6.12.2 Connection of Inner and Outer Port via DelegationSwConnector
#@CLASS: DelegationSwConnector
#@CLASS: PortPrototype
#@CLASS: SwConnector
#@CLASS: TriggerInterface
#@CLASS: TriggerInterfaceMapping

[constr_1082] Compatibility of TriggerInterfaces in the context of an DelegationSwConnector (cid:100) TriggerInterfaces are compatible if and only if all of the following conditions apply:

1. One of the following subconditions applies:
   (a) For each Trigger defined in the context of the TriggerInterface of the required inner PortPrototype a compatible Trigger exists in the TriggerInterface of the required outer PortPrototype. The shortNames of Trigger are used to identify the pair.
   (b) For at least one Trigger defined in the context of the TriggerInterface of the provided outer PortPrototype a compatible Trigger exists in the TriggerInterface of the provided inner PortPrototype. The shortNames of Trigger are used to identify the pair.
   (c) A TriggerInterfaceMapping.triggerMapping exists for which all of the following conditions apply:
       i. It is referenced by the corresponding SwConnector.
       ii. It references one of the two Triggers in the role firstTrigger and the other in the role secondTrigger.

2. For each such pair, the values of their isService attributes are identical.

(cid:99)()

#@SECTION: 6.12.3 Connection of Outer and Outer Port via PassThroughSwConnector
#@CLASS: PassThroughSwConnector
#@CLASS: PortPrototype
#@CLASS: TriggerInterface
#@CLASS: TriggerInterfaceMapping
#@CLASS: Trigger
#@CLASS: PortInterface

[constr_1251] Compatibility of PortPrototypes of TriggerInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different Trigger Interfaces are considered compatible if and only if

1. For at least one Trigger defined in the context of the TriggerInterface of the required outer PortPrototype a compatible Trigger exists in the TriggerInterface of the provided outer PortPrototype. Either the shortName of Triggers are used to identify the pair or a Trigger InterfaceMapping exists that refers to one of the Triggers in the role firstTrigger and to the other in the role secondTrigger.

2. For each such pair, the values of the PortInterface.isService attributes are identical.

(cid:99)()

#@SECTION: 6.13 Compatibility of Trigger
#@CLASS: Trigger
[constr_1083] Compatibility of Triggers (cid:100) Triggers are compatible if they have an identical shortName. (cid:99)()

#@SECTION: 6.14 Entire Delegation of a Provided Port Prototype
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: DelegationSwConnector
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeSwitchInterface
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PassThroughSwConnector
#@CLASS: PortInterface
#@CLASS: PortInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: PRPortPrototype
#@CLASS: PPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: Trigger
#@CLASS: TriggerInterface
#@CLASS: VariableDataPrototype


[constr_1084] delegation of a provided outer PortPrototype (cid:100) The delegation of a provided outer PortPrototype is properly defined if the following criteria are fulfilled:
#@Hierarchical
1. For each VariableDataPrototype or ParameterDataPrototype present in the SenderReceiverInterface, NvDataInterface, or Parameter Interface of the provided outer PortPrototype at least one connection via DelegationSwConnector to a provided inner PortPrototype or PassThroughSwConnector to a required outer PortPrototype with a compatible VariableDataPrototype or ParameterDataPrototype in the SenderReceiverInterface NvDataInterface or ParameterInterface of the provided inner PortPrototype or required outer PortPrototype exists. Either the shortNames of VariableDataPrototypes or ParameterDataPrototypes are used to identify the pair or a PortInterfaceMapping defines which differently named PortInterface elements correlate with each other. Table 6.1 defines which PortInterface elements are compatible depending on the kind of PortInterface and the swImplPolicy attributes of the Port Interface elements.

2. For each VariableDataPrototype provided by a PRPortPrototype that is typed by a SenderReceiverInterface or NvDataInterface and that is referenced in the role outerPort by a DelegationSwConnector a corresponding VariableDataPrototype owned by an innerPort shall be provided by either a PPortPrototype or a PRPortPrototype. Either the shortNames of VariableDataPrototypes are used to identify the pair or a PortInterfaceMapping defines which differently named PortInterface elements correlate with each other.

3. For the ModeDeclarationGroupPrototype present in the ModeSwitch Interface of the provided outer PortPrototype exactly one connection via DelegationSwConnector to a provided inner PortPrototype or PassThroughSwConnector to a required outer PortPrototype with a compatible ModeDeclarationGroupPrototype in the ModeSwitchInterface of the provided inner PortPrototype or required outer PortPrototype exists. Either the shortNames of ModeDeclarationGroupPrototypes are used to identify the pair or a PortInterfaceMapping defines which differently named PortInterface elements correlate with each other.

4. For each ClientServerOperation present in the ClientServerInterface of the provided outer PortPrototype exactly one connection via DelegationSwConnector to a provided inner PortPrototype or PassThroughSwConnector to a required outer PortPrototype with a compatible ClientServerOperation in the ClientServerInterface of the provided inner PortPrototype or required outer PortPrototype exists. Either the shortNames of ClientServerOperations are used to identify the pair or a PortInterfaceMapping defines which differently named PortInterface elements correlate with each other.

5. For each Trigger present in the TriggerInterface of the provided outer PortPrototype exactly one connection via DelegationSwConnector to a provided inner PortPrototype or PassThroughSwConnector to a required outer PortPrototype with a compatible Trigger in the TriggerInterface of the provided inner PortPrototype or required outer PortPrototype exists. Either the shortNames of Triggers are used to identify the pair or a PortInterfaceMapping defines which differently named PortInterface elements correlate with each other.
/#@Hierarchical
(cid:99)()

#@SECTION: 6.14.1 Split and Merge of PortInterface Elements
#@CLASS: PortInterface
#@CLASS: PortPrototype

With the definition of compatibility rules in chapter 6.4, 6.11, and 6.12 it is possible to split and distribute elements of a PortPrototype of type of a PortInterface containing a superset of PortInterface elements to PortPrototypes of type of PortInterfaces containing subsets of PortInterface elements.

Please find examples that explain the usage of splitting and merging in section 6.16.2.

#@SECTION: 6.15 Compatibility in Case of a Flat ECU Extract
#@CLASS: AssemblySwConnector
#@CLASS: CompositionSwComponentType
#@CLASS: DelegationSwConnector
#@CLASS: NvDataInterface
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PortInterface
#@CLASS: PortInterfaceMapping
#@CLASS: PortPrototype
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: VariableDataPrototype

Please note that in the case of a flat ECU extract of software-components specific compatibility rules apply. To some extent, these rules contradict the rules existing for the pure VFB approach (see chapter 6). That is, if the split-and-merge pattern has been applied on the creation of DelegationSwConnectors it might happen that compatibility rules defined in chapter 6 are violated.

However, given that the flattened ECU extract has been created out of a valid CompositionSwComponentType the flattened ECU extract does not become invalid in this case. In other words, the transformation does not create an invalid model out of a valid model.

However, to support this statement it is necessary to define additional compatibility rules that properly cover this case and allow for a successful validation of the flattened ECU extract.

For the flat ECU extract the compatibility of SenderReceiverInterfaces, NvDataInterfaces, and ParameterInterfaces is considered for connecting of PortPrototypes with a DelegationSwConnector.

[constr_1085] Compatibility in the case of a flat ECU extract (cid:100) PortPrototypes of different SenderReceiverInterfaces, NvDataInterfaces, and ParameterInterfaces are compatible if and only if for at least one VariableDataPrototype or ParameterDataPrototype defined in the context of the SenderReceiverInterface, NvDataInterface, or ParameterInterface of the RPortPrototype a compatible VariableDataPrototype or ParameterDataPrototype exists in the SenderReceiverInterface, NvDataInterface, or ParameterInterface of the provided PortPrototype.

The compatibility of PortInterface elements depends on the kind of PortInterface and the swImplPolicy attributes of the PortInterface elements. Either the shortNames of VariableDataPrototypes and ParameterDataPrototypes are used to identify the pair or a PortInterfaceMapping defines which differently named PortInterface elements correlate with each other. (cid:99)()

For clarification, table 6.1 defines which PortInterface elements are compatible depending on the kind of PortInterface and the swImplPolicy attributes of the PortInterface elements.

Please note that in case of the flat ECU extract it might happen that AssemblySwConnectors that connect to a specific RPortPrototype also connect to PPortPrototypes that do not fulfill the compatibility rule specified in 6.4.1. In particular, the dataElements might correspond to dataElements defined in the scope of different PPortPrototypes. In other words, in the flat ECU extract it is possible to merge dataElements from different providers.

#@SECTION: 6.16 Compatibility Examples
#@CLASS: PortPrototype

This section provides some examples that may explain the compatibility of PortPrototypes.

#@SECTION: 6.16.1 Compatibility on Assembly Level
#@CLASS: AssemblySwConnectors

The rules for compatibility with respect to the connection of dataElements by means of AssemblySwConnectors are perhaps easier to digest than the delegation case but nonetheless it seems appropriate to provide a set of examples that illustrate the compatibility issue.

#@SECTION: 6.16.1.1 Legal Use
#@CLASS: RPortPrototype

One of the less trivial examples of this kind is the case of sender/receiver n:1 communication. Figure 6.1 sketches a case where both sender software-components provide the dull set of dataElements that are required by the RPortPrototype of the receiving software-component.


<-------------- multimodal context 
This diagram illustrates a legal n:1 sender–receiver communication: two producer AtomicSwComponentTypes each expose data elements {A,B} via provided ports, and one consumer AtomicSwComponentType collects both through a single required port, all wired in a CompositionSwComponentType via AssemblySwConnectors.

- Component hierarchy  
  • Two source AtomicSwComponentTypes and one sink AtomicSwComponentType instantiated inside a CompositionSwComponentType.

- Ports & interfaces  
  • Each source has an AbstractProvidedPortPrototype (PPort) offering a sender–receiver DataInterface with elements {A,B}.  
  • The sink has one AbstractRequiredPortPrototype (RPort) requiring the same interface.  
  • Two AssemblySwConnectors link each PPort to the single RPort.

- Data flow  
  • Unidirectional, asynchronous transfer of ApplicationCompositeDataType elements A and B from both producers to the consumer.

- Key AUTOSAR concepts  
  • AtomicSwComponentType, CompositionSwComponentType, AbstractProvidedPortPrototype, AbstractRequiredPortPrototype, AssemblySwConnector, DataInterface, ApplicationCompositeDataType, PPort/RPort.

- Scenario  
  • A consumer SWC aggregates or arbitrates data A and B from two redundant or alternative producer SWCs. ---------------------->
Figure 6.1: legal n:1 communication

The next case (exemplified by Figure 6.2) implements a situation where one sender provides two dataElements {A,b} while the other sender provides only as subset of these, i.e. {B}. As the RPortPrototype of the receiving software-component requires only the dataElement {B} compatibility issues will not occur because for every required dataElement a compatible dataElement is provided.


<-------------- multimodal context 
This diagram illustrates a legal n:1 assembly communication in AUTOSAR, where two provider SW-components expose overlapping interface sets to a single consumer SW-component. It shows how multiple P-Ports can be connected to one R-Port without violating AUTOSAR’s interface-set rules.

• Component hierarchy  
  – Three AtomicSwComponentType instances (two providers on the left, one consumer on the right) hosted in a single CompositionSwComponentType.  
• Ports & interfaces  
  – Top provider: AbstractProvidedPortPrototype offering {A,B}  
  – Bottom provider: AbstractProvidedPortPrototype offering {B}  
  – Consumer: AbstractRequiredPortPrototype requiring {B}  
  – Two AssemblySwConnectors link each PPort to the single RPort.  
• Data flow  
  – Both providers may invoke operations or send data on interface B into the consumer’s RPort (n:1 communication).  
• Key AUTOSAR concepts  
  – Uses AbstractProvided/RequiredPortPrototypes, ClientServerInterface with multi-element sets, AssemblySwConnectors, and legal n:1 connector cardinality.  
• Scenario  
  – Demonstrates redundant or fallback provisioning of interface B to a consumer component, enabling fault tolerance or dynamic source selection. ---------------------->
Figure 6.2: legal n:1 communication

#@SECTION: 6.16.1.2 Illegal Use
#@CLASS: AssemblySwConnector

On possible example for an illegal configuration of a sender/receiver communication is the scenario sketched in Figure 6.3. Although the sender software-components in total provide the set of required dataElements the individual AssemblySwConnectors create incompatible connections between sender and receiver.


<-------------- multimodal context 
This diagram illustrates an illegal “many-to-one” port connection in an AUTOSAR composition, where two producers drive a single required port on a consumer, violating the n:1 communication rule.

- Component hierarchy  
  • Three SW-Component instances in a CompositionSwComponentType: two producer AtomicSwComponentTypes (top and bottom) and one consumer AtomicSwComponentType (right).  
  • Flat composition—no nested sub-compositions or further hierarchies.

- Ports & interfaces  
  • Producers each expose an AbstractProvidedPortPrototype (PPort) with a DataInterface carrying elements {B} (top) and {A} (bottom).  
  • Consumer has one AbstractRequiredPortPrototype (RPort) expecting the combined DataInterface {A, B}.  
  • Two AssemblySwConnectors both target the same consumer RPort.

- Data flow  
  • Producer SWCs asynchronously send signals A and B independently.  
  • Both signal streams merge at the single consumer port, implying conflation of two sources into one sink.

- Key AUTOSAR concepts  
  • AbstractProvided/RequiredPortPrototypes with DataInterfaces  
  • ApplicationCompositeElementDataPrototypes {A, B}  
  • AssemblySwConnectors  
  • Illegal n:1 communication constraint (no multi-producer to single consumer).

- Scenario  
  • Demonstrates an invalid design where two SW-Components feed one required port—used to highlight the need for intermediate merging SWC or bus communication to enforce 1:1 port connections. ---------------------->
Figure 6.3: illegal n:1 communication

#@SECTION: 6.16.2 Compatibility on Delegation Level
#@CLASS: CompositionSwComponentType
#@CLASS: DelegationSwConnectors
#@CLASS: RPortPrototype

The rules for compatibility with respect to the delegation of dataElements perhaps require some explanation in terms of examples. The first example 6.4 describes a legal situation where two DelegationSwConnectors split the dataElements contained in the RPortPrototype owned by a CompositionSwComponentType.

#@SECTION: 6.16.2.1 Legal Use
#@CLASS: CompositionSwComponentType
#@CLASS: DelegatedPortAnnotation
#@CLASS: DelegationSwConnector
#@CLASS: PPortPrototype
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@CLASS: SwComponentPrototype
#@CLASS: VariableDataPrototype

The examples explain the usage of DelegationSwConnectors in different configurations and different values of DelegatedPortAnnotation. Please note that the DelegatedPortAnnotation is usually defined before the internal structure of a CompositionSwComponentType is fully clarified.

At a later point in time it has to be consistent or can be removed. Decorating the example with applicable values of DelegatedPortAnnotation should facilitate the understanding of the meaning of the DelegatedPortAnnotation.


<-------------- multimodal context 
This diagram illustrates a Composition exposing an AbstractProvidedPortPrototype “infold” that aggregates four ApplicationDataPrototypes {A,B,C,D}. Two AtomicSwComponentTypes inside the Composition each have an AbstractRequiredPortPrototype: the top sub-component consumes {A,B}, the bottom consumes {B,C}, via DelegationSwConnectors. This arrangement demonstrates how a single provided port can legally be split to supply only the required subsets of data prototypes to different components.

- Component hierarchy:
  • One CompositionSwComponentType containing two AtomicSwComponentType instances (top and bottom).
- Ports & interfaces:
  • Composition: one AbstractProvidedPortPrototype (“infold”) carrying {A,B,C,D}.
  • Each AtomicSwComponentType: one AbstractRequiredPortPrototype with its own subset ({A,B} or {B,C}).
  • Two DelegationSwConnectors linking the provided port to the required ports.
- Data flow:
  • “infold” port collects A,B,C,D → delegates {A,B} to top component, {B,C} to bottom.
  • Prototype D is not forwarded; prototype B appears in both subsets.
- Key AUTOSAR concepts:
  • AbstractProvidedPortPrototype and AbstractRequiredPortPrototype
  • DelegationSwConnector and prototype grouping (“infold”)
  • ApplicationDataPrototype sets and legal splitting of delegation connectors
- Scenario:
  • Use-case: selective distribution of aggregated data prototypes from a single Composition port to multiple SW-components based on their individual interface requirements. ---------------------->
Figure 6.4: Legal split of delegation connector

All required dataElements are provided by the DelegationSwConnectors attached to the delegation RPortPrototype. The fact that dataElement D is not conveyed to any of the RPortPrototypes owned by the SwComponentPrototypes does not have any impact on the compatibility.

In other words: the RPortPrototype at the CompositionSwComponentType actually contains the superset of dataElements {A ,B, C, D}. The two required inner PortPrototypes of the SwComponentPrototypes contain the subsets of VariableDataPrototypes {A, B} and {B, C}. In this case the resulting communication pattern on the VFB for B would be 1:n.

This requires the value of the attribute signalFan of DelegatedPortAnnotation to be set to the value nfold.

In the next example the RPortPrototype of the CompositionSwComponentType contains the superset of dataElements {A ,B}. The two RPortPrototypes of the SwComponentPrototypes contain different subsets, i.e. {A} and {B}.


<-------------- multimodal context 
This diagram illustrates how a composition can legally split a single multi‐operation client/server port into two delegated connectors, each carrying a subset of the interface’s operations to two inner SW-components.

- Component hierarchy – One CompositionSwComponentType containing two AtomicSwComponentType instances (upper and lower gray SW-components).
- Ports & interfaces – The composition declares one RPort (or ProvidedPort) with ClientServerInterface {A,B} [single], which is delegated via two DelegationSwConnectors to inner ports: top port {A}, bottom port {B}.
- Data flow – Calls or requests tagged “A” route through the upper connector to the first component; those tagged “B” route to the second component.
- Key AUTOSAR concepts – AbstractRequiredPortPrototype/AbstractProvidedPortPrototype, DelegationSwConnector, interface partitioning, single port cardinality, ClientServerInterface operations.
- Scenario – Splitting a composite interface into two functional providers, each handling distinct operations of the same interface. ---------------------->
Figure 6.5: Legal split of delegation connector

In this case the resulting communication pattern on the VFB would be n:1. In this case the value of the attribute signalFan of DelegatedPortAnnotation should be set to single.

The next example is about the merge of DelegationSwConnectors. The PPortPrototype owned by the CompositionSwComponentType contains a superset of dataElements {A ,B}. The two PPortPrototypes of the SwComponentPrototypes contain a disjoint subset each, i.e. {A} and {B}.


<-------------- multimodal context 
The diagram shows a CompositionSwComponentType that merges two internal Provided ports—each offering a distinct DataInterface—into one external port, then connects it via an AssemblySwConnector to a consuming SWC. This legal merge bundles interface sets A and B into a single port, simplifying downstream connectivity.

- Component hierarchy  
  • CompositionSwComponentType with two AtomicSwComponentType instances as inner subcomponents  
- Ports & interfaces  
  • Inner subcomponents expose AbstractProvidedPortPrototype {A} and {B}  
  • Composition defines an AbstractProvidedPortPrototype {A,B} [single]  
  • AssemblySwConnector links the merged port to an external RequiredPortPrototype  
- Data flow  
  • Fan-in pattern: two provided streams (A, B) delegated upward, merged, then forwarded as one to the consumer  
- Key AUTOSAR concepts  
  • DelegationSwConnector merge of AbstractProvidedPortPrototype  
  • Interface sets ({A}, {B}, {A,B}) and multiplicity “single”  
  • AssemblySwConnector, AbstractRequiredPortPrototype/AbstractProvidedPortPrototype  
- Scenario  
  • Use-case: consolidate separate functional outputs into a unified port for a downstream SWC ---------------------->
Figure 6.6: Legal merge of delegation connector

In this case the resulting communication pattern on the VFB would be 1:x, with x taking values between 0 and n. In this case the value of the attribute signalFan of DelegatedPortAnnotation should be set to single. All VariableDataPrototypes of the provided outer PortPrototypes are provided by exactly one provided inner PortPrototype.

As a variation of this theme, the next example features a PPortPrototype owned by a CompositionSwComponentType that contains the superset of dataElements {A ,B, C}. The PPortPrototypes of the SwComponentPrototypes in turn contain subsets of dataElements, i.e. {A, B} and {B, C}. In this case the resulting communication pattern on the VFB for {B} would be n:1.


<-------------- multimodal context 
This diagram shows a legal merge of delegated data ports inside a CompositionSwComponentType: two inner atomic SW-components each export overlapping data sets which are infold-merged via a DelegationSwConnector into a single port that feeds an external consumer. It demonstrates how AUTOSAR allows union of data prototypes when delegating through a composition.

• Component hierarchy  
  – A top-level CompositionSwComponentType contains two AtomicSwComponentType instances and one external SW-component linked via delegation.  

• Ports & interfaces  
  – Inner SWCs expose AbstractProvidedPortPrototypes carrying {A,B} and {B,C}.  
  – A DelegationSwConnector merges those into an inner AbstractProvidedPortPrototype {A,B,C}[Infold].  
  – That port is further delegated to an external SWC’s AbstractRequiredPortPrototype.  

• Data flow  
  – Data elements A and B travel from SWC1; B and C from SWC2.  
  – At the infold port they union into {A,B,C}, which is then sent to the consumer.  

• Key AUTOSAR concepts  
  – Uses DelegationSwConnector, port prototype infolding, inner/outer ports, and DataInterface grouping.  

• Scenario  
  – Illustrates composing multiple data providers into one aggregated interface for an external client. ---------------------->
Figure 6.7: Legal merge of delegation connector

This would require the value of the attribute signalFan of DelegatedPortAnnotation to be set to nfold. All dataElements of the delegation PPortPrototype are provided by at least one PPortPrototype of the SwComponentPrototypes. Therefore the criteria of entire delegation defined in chapter 6.14 are fulfilled.

The next example looks very similar. However, the subtle difference is that the second SwComponentPrototype provides dataElements {C,D} rather than {B,C}.


<-------------- multimodal context 
This diagram illustrates a legal merge of two internal Provided ports into a single outside-facing Provided port within a CompositionSwComponentType, aggregating data sets {A,B} and {C,D} into {A,B,C}. It showcases how internal producers can safely delegate and combine data flows before exposing them to an external consumer SW-Component.

• Component hierarchy  
  – A CompositionSwComponentType contains two AtomicSwComponentType subcomponents.  
  – Each subcomponent hosts its own AbstractProvidedPortPrototype.  
  – The composition itself defines one merged AbstractProvidedPortPrototype.  
  – An external SW-ComponentType consumes the merged port.

• Ports & interfaces  
  – Two inner Provided ports with data sets {A,B} and {C,D}.  
  – One inner merge port with union {A,B,C} and multiplicity [single].  
  – One external Provided port {A,B,C}.  
  – AssemblySwConnector edges linking subcomponent ports to the merge port and outwards.

• Data flow  
  – Each subcomponent emits its data elements.  
  – Delegation connectors merge flows, filtering to {A,B,C}.  
  – External consumer receives the unified data stream.

• Key AUTOSAR concepts  
  – AbstractProvidedPortPrototype, AssemblySwConnector, delegation connectors.  
  – DataPrototype sets, multiplicity “[single]”.  
  – Legal merge rule ensures disjoint or compatible data subsets.

• Scenario  
  – Aggregate signals from two producers, filter and expose a consistent subset to a downstream SW-Component. ---------------------->
Figure 6.8: Legal merge of delegation connector

Although dataElement {D} does not appear in the delegation PPortPrototype the compatibility rules are fully satisfied with this scenario.

The next example shows a valid delegation of SwConnectors that goes end-to-end via CompositionSwComponentTypes to included SwComponentPrototypes.


<-------------- multimodal context 
This diagram shows two nested CompositionSwComponentTypes (“LeftComp” and “RightComp”) delegating client-server or data interfaces end-to-end between four AtomicSwComponentTypes, filtering interface sets at each delegation point to satisfy connectability rules.

• Component hierarchy  
  - LeftComp: CompositionSwComponentType containing AtomicSwComponentType SWC1 and SWC2  
  - RightComp: CompositionSwComponentType containing AtomicSwComponentType SWC3 and SWC4  

• Ports & interfaces  
  - SWC1 has an AbstractRequiredPortPrototype with interface set {A,B}  
  - SWC2 has an AbstractRequiredPortPrototype with {B,C}  
  - Both delegate to LeftComp’s inner RequiredPortPrototype (aggregated {A,B})  
  - LeftComp inner port connects via DelegationSwConnector to RightComp inner port ({A,B})  
  - RightComp inner port delegates to SWC3’s RPort {A} and SWC4’s RPort {B}  

• Data flow  
  - Interfaces A and B emitted by SWC1 are propagated through nested delegation to SWC3 (A) and SWC4 (B)  
  - SWC2’s C is dropped at LeftComp because no downstream port supports C  

• Key AUTOSAR concepts  
  - AbstractRequiredPortPrototype / AbstractProvidedPortPrototype  
  - CompositionSwComponentType nesting  
  - DelegationSwConnector chaining  
  - Interface subset connectability rules  

• Scenario  
  - Illustrates valid end-to-end delegation of SwConnectors across two compositions, demonstrating how interface sets are aggregated and filtered to satisfy each AtomicSwComponentType’s port requirements. ---------------------->
Figure 6.9: Valid delegation of SwConnectors that goes end-to-end

#@SECTION: 6.16.2.2 Illegal Use
#@CLASS: CompositionSwComponentType
#@CLASS: DelegationSwConnector
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SwComponentPrototype
#@CLASS: SwConnector

The ﬁrst example for an illegal use of splitting of dataElements suffers from the fact that not all dataElements owned by the RPortPrototypes of the SwComponentPrototypes are available from the connected RPortPrototypes owned by the CompositionSwComponentType.

Although dataElements the connections in total match ({A} and {B} are connected to a PortPrototype requiring {A,B}) the compatibility rules are not fulﬁlled because they apply separately for each SwConnector.

Figure 6.10: Illegal split of delegation connector

In the next example compatibility is also not fulﬁlled because the required dataElement {E} is not provided by the delegation RPortPrototype.


<-------------- multimodal context 
This diagram illustrates an illegal split of a delegation connector in an AUTOSAR CompositionSwComponentType: a single inner port carrying data {A,B,C,D} is delegated to two sub-components’ ports whose data sets overlap and don’t match the original, violating AUTOSAR port grouping rules.

• Component hierarchy  
  – One CompositionSwComponentType containing two AtomicSwComponentType instances.  

• Ports & interfaces  
  – Composition has an AbstractProvidedPortPrototype (or RPortPrototype) with data elements {A,B,C,D}.  
  – Each sub-component has an AbstractRequiredPortPrototype (or PPortPrototype): one with {A,B}, the other with {B,C,E}.  

• Data flow  
  – A single delegation connector is split into two DelegationSwConnectors to the two inner ports.  
  – Overlap on B and inclusion of E (not in {A,B,C,D}) cause mismatched partitioning.  

• Key AUTOSAR concepts  
  – DelegationSwConnector, InnerPortPrototype, DataPrototypeGroup partitioning, port exact-match rule.  

• Scenario  
  – Demonstrates a modeling error: you cannot split one port’s data set into two sub-ports unless they form an exact, non-overlapping partition of the original. ---------------------->
Figure 6.11: Illegal split of delegation connector

An incompatible merge of DelegationSwConnectors is sketched in Figure 6.12. In this case the dataElement {E} is not provided by one of the PPortPrototypes owned by the SwComponentPrototypes inside the CompositionSwComponentType.


<-------------- multimodal context 
This diagram illustrates an illegal merge of multiple AssemblySwConnectors into a single DelegationSwConnector within a CompositionSwComponentType, leading to incompatible interface sets at the composition port.

- Component hierarchy  
  • A CompositionSwComponentType containing two AtomicSwComponentType inner components.  
  • One external AtomicSwComponentType connected via delegation.

- Ports & interfaces  
  • Inner Component 1 has an AbstractProvidedPortPrototype ({A,B}).  
  • Inner Component 2 has an AbstractProvidedPortPrototype ({B,C}).  
  • The composition’s inner port (merge point) is an AbstractRequiredPortPrototype ({A,C,E}).  
  • An outer DelegationSwConnector links that to an external AbstractRequiredPortPrototype ({A,C,E}).

- Data flow  
  • Two AssemblySwConnectors feed interfaces {A,B} and {B,C} into a merge node.  
  • The merged signal then travels through a DelegationSwConnector to the external port.

- Key AUTOSAR concepts  
  • AssemblySwConnector merging, DelegationSwConnector, AbstractProvidedPortPrototype/AbstractRequiredPortPrototype.  
  • Interface compatibility rules prevent merging ports with disjoint interface sets.  
  • Demonstrates illegal merge semantics (no InterfaceMapping to reconcile {A,B,C} vs. {A,C,E}).

- Scenario  
  • Validates connector compatibility in a composition: merging two provided ports before delegation.  
  • Shows an error case where interface sets do not match, violating AUTOSAR port merging rules. ---------------------->
Figure 6.12: Illegal merge of delegation connector

The next example shows an invalid delegation of SwConnectors that goes end-to-end via CompositionSwComponentTypes to included SwComponentPrototypes.

Similar to the example sketched in Figure 6.12, the dataElement {E} is not provided by one of the PPortPrototypes owned by the SwComponentPrototypes inside the CompositionSwComponentType.


<-------------- multimodal context 
This diagram illustrates an invalid end-to-end delegation of SwConnectors between two CompositionSwComponentTypes, where required interfaces from inner AtomicSwComponents are improperly forwarded across composition boundaries to provided ports without using proper assembly connectors.

• Component hierarchy  
  – Two CompositionSwComponentType blocks, each containing two AtomicSwComponentType instances.  
  – Inner components in the left composition both have RPorts; inner components in the right composition both have PPorts.

• Ports & interfaces  
  – Left inner RPorts require {A,B} and {B,C}.  
  – Left composition’s outer RPort (delegated) exposes {A,C,E}.  
  – Right composition’s outer PPort (delegated) exposes {A,C,E}.  
  – Right inner PPorts provide {A} and {C,E}.

• Data flow  
  – Interfaces A, B, C are required by left inners, aggregated to the outer RPort.  
  – The outer RPort is directly delegated to the right outer PPort, which splits to inner PPorts.  
  – This bypasses an intermediate assembly, causing an illegal end-to-end delegation.

• Key AUTOSAR concepts  
  – AbstractRequiredPortPrototype (RPort) and AbstractProvidedPortPrototype (PPort).  
  – DelegationSwConnector used instead of AssemblySwConnector.  
  – Interface sets must match exactly; partial mappings and chaining across compositions violate connector rules.

• Scenario  
  – Intended to demonstrate a misuse of SwConnector delegation where required interfaces are improperly forwarded and split across compositions, highlighting AUTOSAR’s prohibition of direct end-to-end delegation. ---------------------->
Figure 6.13: Invalid delegation of SwConnectors that goes end-to-end

#@SECTION: 7 Internal Behavior
#@SECTION: 7.1 Introduction
#@CLASS: AtomicSwComponentType
#@CLASS: InternalBehavior
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: SwcInternalBehavior
#@CLASS: SwcImplementation
#@CLASS: VariableDataPrototype
#@CLASS: ParameterDataPrototype
#@CLASS: PerInstanceMemory
#@CLASS: IncludedDataTypeSet
#@CLASS: IncludedModeDeclarationGroupSet
#@CLASS: InstantiationDataDefProps
#@CLASS: PortAPIOption
#@CLASS: SwcServiceDependency
#@CLASS: VariationPointProxy
#@ENUM: HandleTerminationAndRestartEnum

[TPS_SWCT_01075] SwcInternalBehavior (cid:100) SwcInternalBehavior provides means for formally defining the behavior of an AtomicSwComponentType. (cid:99)(RS_SWCT_03040)

This chapter focuses on the description of the SwcInternalBehavior meta-class and the various meta-classes it aggregates. An overview of the meta-class is sketched in Figure 7.2. Please note that SwcInternalBehavior inherits from InternalBehavior.

The role of SwcInternalBehavior in the context of an AUTOSAR software component is depicted in Figure 7.1. As mentioned in section 3.2, the reason to make the aggregation of SwcInternalBehavior to AtomicSwComponentType (cid:28)atpSplitable(cid:29) is to allow for the development of SwcInternalBehavior in a later process step (e.g. after the VFB view has been completed).

Figure 7.1: The "big picture" of SwcInternalBehavior

Table 7.1: SwcInternalBehavior

Table 7.2: HandleTerminationAndRestartEnum

Figure 7.2: SwcInternalBehavior

#@SECTION: 7.2 Runnable Entity
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: ExecutableEntity
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior
#@CLASS: SwComponentPrototype
#@CLASS: SwComponentType
#@CLASS: EcuInstance

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
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior
#@CLASS: RTEEvent

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
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: PPortPrototype
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior

This section applies to the case that the value of the attribute canBeInvokedConcurrently is set to true. In this case, it is allowed that the same RunnableEntity is running several times concurrently in different AUTOSAR OS tasks. This implies that the state machine defined in [2] is not the state of the RunnableEntity any more, but can be cloned an arbitrary number of times.

[TPS_SWCT_01306] Software-component description itself does not put any bounds on the number of concurrent invocations of a RunnableEntity (cid:100) The software-component description itself does not put any bounds on the number of concurrent invocations of the RunnableEntity that are allowed. The software-component description only specifies whether the RunnableEntity can be invoked concurrently or not. Allowing concurrent invocation of a RunnableEntity implies that the implementation of the AtomicSwComponentType needs to take care of this additional form of concurrency. (cid:99)()

For example: The SwcInternalBehavior of a component-type MyComponentType describes a RunnableEntity R1 which should be enabled when a ClientServer Operation on a PPortPrototype typed by a ClientServerInterface of the AtomicSwComponentType is invoked. The AtomicSwComponentType specifies that the RunnableEntity R1 can be invoked concurrently. The AtomicSwComponentType MyComponentType is instantiated on an ECU. When a call of the ClientServerOperation is received the corresponding instance of the RunnableEntity R1 is enabled and the RTE will start executing the RunnableEntity (the RunnableEntity is in state running) in a task eventually managed by the AUTOSAR OS. If another call of the ClientServerOperation is received, it is allowed that the same RunnableEntity is started again in a different task.

A typical use-case of concurrent RunnableEntitys is the implementation of AUTOSAR services. The AUTOSAR services will typically take care of concurrency internally: several software-components can directly use the services in parallel. The ECU-integrator could then decide that the RunnableEntity implementing the AUTOSAR service runs directly in the context (in the task) of the AtomicSwComponentType invoking the service. This is a very efficient and direct coupling between the client and the server: the connector between the client and the server is reduced to a local function-call.

#@SECTION: 7.2.3 Timed Activation of Runnable Entities
#@CLASS: AtomicSwComponentType
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: SwcInternalBehavior
#@CLASS: TimingEvent

In many cases, RunnableEntitys need to be activated in response to timing events rather than related to communication (e.g. the reception of a response to an asynchronous operation invocation). Many RunnableEntitys will need to run cyclically with a fixed rate.

The approach taken in the software-component description is to define so-called TimingEvents (please find more details in Figure 7.5) as special kinds of RTEEvents.

So far, only one kind of timing-related RTEEvent has been defined: a simple periodic TimingEvent.

Figure 7.5: Periodic activation of RunnableEntities

[TPS_SWCT_01519] RTE executes certain RunnableEntity periodically (cid:100) If the SwcInternalBehavior of an AtomicSwComponentType requires that the RTE executes certain RunnableEntitys periodically, the description needs to define a TimingEvent with the desired period. This TimingEvent then contains a reference to the Runnable that needs to be executed with this period. (cid:99)()

#@SECTION: 7.2.4 Additional Remarks and Clariﬁcations
#@SECTION: 7.2.4.1 Reentrancy and Multiple Instantiation
#@CLASS: AtomicSwComponentType
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior
#@CLASS: TimingEvent

This chapter is emphasizing on the specific meanings of combinations of the attributes SwcInternalBehavior.supportsMultipleInstantiation and RunnableEntity.canBeInvokedConcurrently.

[TPS_SWCT_01307] supportsMultipleInstantiation vs. canBeInvokedConcurrently (cid:100) The semantics of combining the attributes supportsMultipleInstantiation and canBeInvokedConcurrently is summarized in Table 7.4. (cid:99)()

Table 7.4: supportsMultipleInstantiation vs. canBeInvokedConcurrently

In case the implementation of a AtomicSwComponentType decides to map several RunnableEntitys to the same symbol there are reentrancy problems to be sorted out. However, this scenario is not supported by RTE [2] anyway and shall therefore be avoided.

#@SECTION: 7.2.4.2 Reentrancy and “Library Functions”
Note that all code that is called by different RunnableEntitys (like e.g. library routines, etc.) shall obviously be reentrant. A filter algorithm implemented in C, for example, is not allowed to store values from previous runs by means of static variables or variables with external binding.

#@SECTION: 7.2.4.3 Compatibility of ClientServerOperations triggering the same RunnableEntity
#@CLASS: ArgumentDataPrototype
#@CLASS: ClientServerOperation
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeElement
#@CLASS: PortDefinedArgumentValue
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: OperationInvokedEvent

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
#@CLASS: WaitPoint

[TPS_SWCT_01310] Categories of RunnableEntitys (cid:100) RunnableEntitys are subdivided into the following categories:

Category 1 Category 1 RunnableEntitys do not have WaitPoints and are required to terminate in a finite amount of time. Category 1 is divided into two subcategories: Category 1A and Category 1B. Category 1A RunnableEntitys are only allowed to use implicit API’s. Category 1B RunnableEntitys are additionally allowed to invoke a server and use explicit API’s.

Category 2 In contrast to Category 1 RunnableEntitys, RunnableEntitys of category 2 always aggregate at least one WaitPoint, for more details see Figure 7.31. Typically, such a RunnableEntity implements an internal loop where one iteration through the loop is triggered whenever a WaitPoint is resolved. (cid:99)()

1Category 2 RunnableEntitys usually have to be mapped to Extended Tasks, because only extended tasks provide the task state WAITING.

#@SECTION: 7.2.4.5 Arguments of a Runnable Entity
#@CLASS: ArgumentDataPrototype
#@CLASS: ClientServerOperation
#@CLASS: OperationInvokedEvent
#@CLASS: PortAPIOption
#@CLASS: PortPrototype
#@CLASS: RunnableEntity
#@CLASS: RunnableEntityArgument
#@CLASS: BswModuleEntry
#@CLASS: SwServiceArg

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
#@CLASS: ExecutableEntityActivationReason
#@CLASS: RTEEvent
#@CLASS: RunnableEntity
#@CLASS: TimingEvent
#@CLASS: DataReceivedEvent
#@CLASS: WaitPoint

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
#@CLASS: AsynchronousServerCallResultPoint
#@CLASS: InitEvent
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: RunnableEntity
#@CLASS: SynchronousServerCallPoint
#@CLASS: WaitPoint
#@CLASS: RTEEvent
#@CLASS: ExecutableEntity

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
#@CLASS: AsynchronousServerCallReturnsEvent
#@CLASS: BackgroundEvent
#@CLASS: ClientServerOperation
#@CLASS: DataReceivedEvent
#@CLASS: DataReceiveErrorEvent
#@CLASS: DataSendCompletedEvent
#@CLASS: DataWriteCompletedEvent
#@CLASS: ExternalTriggerOccurredEvent
#@CLASS: InitEvent
#@CLASS: InternalTriggerOccurredEvent
#@CLASS: ModeSwitchedAckEvent
#@CLASS: OperationInvokedEvent
#@CLASS: PPortPrototype
#@CLASS: RTEEvent
#@CLASS: RPortPrototype
#@CLASS: SwcModeSwitchEvent
#@CLASS: TimingEvent
#@CLASS: TransformerHardErrorEvent
#@CLASS: VariableDataPrototype

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
#@CLASS: AsynchronousServerCallResultPoint
#@CLASS: AsynchronousServerCallReturnsEvent
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarDataPrototype
#@CLASS: ClientServerOperation
#@CLASS: DataReceiveErrorEvent
#@CLASS: DataReceivedEvent
#@CLASS: DataSendCompletedEvent
#@CLASS: DataWriteCompletedEvent
#@CLASS: ModeActivationKindAtpStructureElement
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeErrorBehavior
#@ENUM: ModeErrorReactionPolicyEnum
#@CLASS: ModeSwitchPoint
#@CLASS: ModeSwitchedAckEvent
#@CLASS: OperationInvokedEvent
#@CLASS: RTEEvent
#@CLASS: SwcInternalBehavior
#@CLASS: SwcModeManagerErrorEvent
#@CLASS: SwcModeSwitchEvent
#@CLASS: TimingEvent
#@CLASS: VariableAccess
#@CLASS: VariableDataPrototype
#@CLASS: WaitPoint

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
#@CLASS: AsynchronousServerCallReturnsEvent
#@CLASS: DataReceivedEvent
#@CLASS: DataSendCompletedEvent
#@CLASS: ExternalTriggerOccurredEvent
#@CLASS: InitEvent
#@CLASS: InternalTriggerOccurredEvent
#@CLASS: InternalTriggeringPoint
#@CLASS: ModeSwitchedAckEvent
#@CLASS: RTEEvent
#@CLASS: RunnableEntity
#@CLASS: SwcModeSwitchEvent
#@CLASS: TimingEvent
#@CLASS: WaitPoint

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
#@CLASS: PortPrototype
#@CLASS: RunnableEntity

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
#@CLASS: InternalBehavior
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior
#@CLASS: SynchronousServerCallPoint
#@CLASS: ExclusiveArea
#@CLASS: ExclusiveAreaNestingOrder

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
#@CLASS: ExclusiveArea

[TPS_SWCT_01050] RunnableEntity always runs inside an ExclusiveArea (cid:100) In the ﬁrst approach, the formal description speciﬁes that certain RunnableEntitys always run inside an ExclusiveArea. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

For example, if the formal description speciﬁes that both RunnableEntity ’r1’ and RunnableEntity ’r2’ run within ExclusiveArea ’s1’, the RTE shall make sure that RunnableEntitys ’r1’ and ’r2’ never run concurrently; the scheduler should never preempt ’r1’ to run ’r2’.

Note that this pattern does not force the RTE to implement this by using semaphores or mutexes that are taken before the RunnableEntity starts and given when the RunnableEntity returns. It only obliges the RTE to make sure that both RunnableEntitys are never running concurrently.

This requirement could be implemented by several of the implementation strategies described above. For example:

1. Scheduling strategy: if, for example, RunnableEntitys ’r1’ and ’r2’ are mapped to the same task, the criterion is automatically satisﬁed. For this purpose it is necessary to make sure that the OS can only execute a single instance of the task into which the RunnableEntitys are put.

2. Mutual exclusion semaphores: in case ’r1’ and ’r2’ are mapped to different tasks is executing (’T1’, respectively ’T2’), the OS shall make sure that while ’T1’ ’r1’, ’T2’ running ’r2’ can never preempt it and vice-versa. This could be implemented by taking a mutual-exclusion semaphore before executing ’r1’ (resp. ’r2’) in the context of ’t1’ (resp. ’t2’) and returning the semaphore on exiting the RunnableEntity.

#@SECTION: 7.4.1.2 Runnable would Dynamically Enter and Leave the Exclusive Area
#@CLASS: RunnableEntity

[TPS_SWCT_01051] RunnableEntity explicitly enters and leaves a specific ExclusiveArea (cid:100) In the second approach, the RunnableEntity would explicitly make API-calls to the RTE within the implementation of the RunnableEntity to enter and leave a specific ExclusiveArea. (cid:99)(RS_SWCT_00120, RS_SWCT_02090)

This could, for example, be implemented by means of the priority ceiling concept described in chapter 2.3.1.3.

Additionally it is possible to define the execution time the RunnableEntity will spend in this ExclusiveArea segment. Please note that although this aspect is described in [7] the concept can be applied to software-components as well.

#@SECTION: 7.4.2 Description Possibility 2: Inter-Runnable Variable
#@CLASS: AutosarVariableRef
#@CLASS: DataPrototype
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior
#@CLASS: VariableAccess
#@CLASS: VariableDataPrototype
#@CLASS: ExclusiveArea
#@CLASS: ImplementationDataType

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
#@CLASS: InternalTriggerOccurredEvent
#@CLASS: InternalTriggeringPoint
#@CLASS: RunnableEntity

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
#@CLASS: PortPrototype
#@CLASS: RunnableEntity

This section describes the communication properties of an AtomicSwComponentType. This is done mainly from the point of view of a RunnableEntity (the concept of a RunnableEntity is introduced in chapter 7.2).

However, the usage of a PortPrototype in a specific role within an AtomicSwComponentType also has an impact on communication behavior.

#@SECTION: 7.5.1 RunnableEntities and Sender Receiver Communication
#@CLASS: DataReceivedEvent
#@CLASS: DataReceiveErrorEvent
#@CLASS: DataSendCompletedEvent
#@CLASS: RunnableEntity
#@CLASS: SenderReceiverInterface

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
#@CLASS: AutosarVariableRef
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RunnableEntity
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: SwcInternalBehavior
#@CLASS: VariableAccess
#@ENUM: VariableAccessScopeEnum
#@CLASS: VariableDataPrototype

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
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarVariableRef
#@CLASS: DataPrototype
#@CLASS: DataReceivedEvent
#@CLASS: NvDataInterface
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RPortPrototype
#@CLASS: RunnableEntity
#@CLASS: SenderReceiverInterface
#@CLASS: SwcInternalBehavior
#@CLASS: VariableAccess
#@CLASS: VariableDataPrototype
#@CLASS: WaitPoint

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
#@CLASS: DataSendCompletedEvent
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RTEEvent
#@CLASS: SenderComSpec
#@CLASS: TransmissionAcknowledgementRequest
#@CLASS: WaitPoint

[TPS_SWCT_01336] dataSendPoint also allows for the deﬁnition of a DataSendCompletedEvent (cid:100) The dataSendPoint also allows for the deﬁnition of a DataSendCompletedEvent, as shown in Figure 7.20. This RTEEvent occurs when the data has been successfully sent or when an error has occurred during sending. (cid:99)(RS_SWCT_00200)

Please note that this feature can only be used if the AtomicSwComponentType describes the meaning of success or failure of the send operation.

In particular, via a SenderComSpec class different acknowledgement requests (in this case: successful transmission) can be attached to a PPortPrototype or PRPortPrototype, as is shown in Figure 4.33.

This will conﬁgure the RTE such that when data is sent the RTE will try to obtain the speciﬁed acknowledgement; possibly by waiting a certain timeout period.
Table 7.30: DataSendCompletedEvent

[constr_2033] Timeout of DataSendCompletedEvent (cid:100) The timeout value of a WaitPoint associated with a DataSendCompletedEvent shall have the same value as the corresponding value of TransmissionAcknowledgementRequest.timeout. (cid:99)()

#@SECTION: 7.5.1.5 DataWriteCompletedEvent
#@CLASS: AtomicSwComponentType
#@CLASS: DataWriteCompletedEvent
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RTEEvent
#@CLASS: SenderComSpec
#@CLASS: WaitPoint

[TPS_SWCT_01557] dataWriteAccess also allows for the definition of a DataWriteCompletedEvent (cid:100) The dataWriteAccess also allows for the definition of a DataWriteCompletedEvent, as shown in Figure 7.22. This RTEEvent occurs when the data has been successfully sent or when an error has occurred during sending. (cid:99)(RS_SWCT_00200)

Please note that this feature can only be used if the AtomicSwComponentType describes the meaning of success or failure of the send operation.

In particular, via a SenderComSpec class different acknowledgement requests (in this case: successful transmission) can be attached to a PPortPrototype or PRPortPrototype, as is shown in Figure 4.33.

[TPS_SWCT_01558] DataWriteCompletedEvent cannot be combined with a WaitPoint (cid:100) Please note that a DataWriteCompletedEvent cannot be associated with a WaitPoint, see [constr_1091]. (cid:99)(RS_SWCT_00200)

However, it is possible to configure the RTE such that when data is sent, the RTE will try to obtain the specified acknowledgement; possibly by waiting a certain timeout period.

Table 7.31: DataWriteCompletedEvent

Figure 7.22: dataWriteAccess

#@SECTION: 7.5.1.6 DataReceivedEvent

#@CLASS: DataReceivedEvent
#@CLASS: VariableDataPrototype

[TPS_SWCT_01337] DataReceivedEvent (cid:100) A receiver is notified through the same event mechanism when a VariableDataPrototype is received. As shown in Figure 7.23, the DataReceivedEvent is directly associated with the corresponding VariableDataPrototype. (cid:99)(RS_SWCT_00200)

Figure 7.23: Receiver is notified by an event when new data has arrived

Table 7.32: DataReceivedEvent

#@SECTION: 7.5.1.7 DataReceiveErrorEvent
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: DataReceiveErrorEvent
#@CLASS: ReceiverComSpec
#@CLASS: RunnableEntity
#@CLASS: SenderReceiverInterface
#@CLASS: SwcInternalBehavior
#@CLASS: VariableDataPrototype

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
#@CLASS: AsynchronousServerCallPoint
#@CLASS: AsynchronousServerCallResultPoint
#@CLASS: AsynchronousServerCallReturnsEvent
#@CLASS: AtomicSwComponentType
#@CLASS: ClientServerOperation
#@CLASS: RTEEvent
#@CLASS: RunnableEntity
#@CLASS: ServerCallPoint
#@CLASS: SwComponentPrototype
#@CLASS: SwcInternalBehavior
#@CLASS: SynchronousServerCallPoint
#@CLASS: WaitPoint
#@CLASS: RPortPrototype

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
#@CLASS: OperationInvokedEvent
#@CLASS: RunnableEntity

A software-component can define an OperationInvokedEvent for each operation inside one of the server AbstractProvidedPortPrototypes. This way a RunnableEntity may respond to such an invocation through the generic event handling mechanisms described above (as formally expressed in Figure 7.26).

Figure 7.26: The OperationInvokedEvent references the operation that was called by a client.

Table 7.39: OperationInvokedEvent

#@SECTION: 7.5.2.3 Reacting on Data Transformation Errors
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: RunnableEntity
#@CLASS: TransformerHardErrorEvent
#@CLASS: TriggerInterface

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
#@CLASS: AtomicSwComponentType
#@CLASS: ExternalTriggeringPoint
#@CLASS: PPortPrototype
#@CLASS: RunnableEntity
#@CLASS: SwComponentPrototype
#@CLASS: SwcInternalBehavior

[TPS_SWCT_01348] Trigger source (cid:100) A RunnableEntity of the triggering software-component raises an external trigger event via an AbstractProvidedPortPrototype of the enclosing SwComponentPrototype typed by a particular AtomicSwComponentType. For this purpose the particular RunnableEntity needs an ExternalTriggeringPoint that references the particular instance of the trigger in a PPortPrototype. (cid:99)(RS_SWCT_00200)

Figure 7.27: Model structure of a trigger source.

Table 7.41: ExternalTriggeringPoint

#@SECTION: 7.5.3.2 Trigger Sink
#@CLASS: ExternalTriggerOccurredEvent
#@CLASS: RPortPrototype
#@CLASS: RunnableEntity

The activation of RunnableEntitys in the trigger sink is effected through the generic event handling mechanism.

[TPS_SWCT_01349] Trigger sink (cid:100) The fact that a RunnableEntity shall be activated on occurrence of an external trigger event is formally defined by means of ExternalTriggerOccurredEvent that references a particular instance of the trigger in a RPortPrototype and additionally the RunnableEntity to be executed in response to the event. (cid:99)(RS_SWCT_00200)

Figure 7.28: Model structure of a trigger sink

Table 7.42: ExternalTriggerOccurredEvent

#@SECTION: 7.5.4 RunnableEntities and Parameter Access
#@CLASS: ArgumentDataPrototype
#@CLASS: ClientServerInterface
#@CLASS: DataPrototype
#@CLASS: NvDataInterface
#@CLASS: ParameterAccess
#@CLASS: ParameterDataPrototype
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@CLASS: RunnableEntity
#@CLASS: SenderReceiverInterface
#@CLASS: SwComponentPrototype
#@CLASS: SwComponentType
#@CLASS: SwDataDefProps
#@CLASS: SwcInternalBehavior
#@CLASS: VariableDataPrototype

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
#@CLASS: DataPrototype
#@CLASS: InstantiationDataDefProps
#@CLASS: ParameterDataPrototype
#@CLASS: PortPrototype
#@CLASS: SwDataDefProps
#@CLASS: VariableDataPrototype

Typically, the accessibility and further information like alias names for a particular piece of data is modeled on the level of DataPrototypes (especially VariableDataPrototypes, ParameterDataPrototypes).

But due to the recursive structure of the meta-model concerning data types (an ApplicationCompositeDataType consists of DataPrototypes), a part of the relevant MCD information is described directly in the data type (in case of a ApplicationCompositeDataType).

This is a strong restriction in the reuse of data types because the ApplicationCompositeDataType should be re-used for different VariableDataPrototypes and ParameterDataPrototypes to guarantee type compatibility on C-implementation level (e.g. data of a PortPrototype is stored in a PIM or a ParameterDataPrototype used as ROM Block and shall be typed by the same data type as NVRAM Block).

This restriction is overcome by InstantiationDataDefProps as shown in figure 7.30.

Figure 7.30: applying instantiation specific data definition properties

Table 7.44: InstantiationDataDefProps

#@SECTION: 7.5.5 RunnableEntities and Mode Communication
#@CLASS: RunnableEntity
#@CLASS: RTEEvent
#@CLASS: ImplementationDataType
#@CLASS: ModeDeclarationGroupPrototype

For the communication of modes between RunnableEntitys we have to distinguish between two use cases.

[TPS_SWCT_01352] Requested mode is just sent and received as an ordinary data value (cid:100) In the ﬁrst case, a requested mode is just sent and received as an ordinary data value without specifying the details of mode switching in the corresponding port interface. This mechanism is used if the receiving RunnableEntity is not directly implementing a mode switch but does further processing of the mode request. This is especially needed to transfer mode requests between ECUs. In this case, the mode is transferred via sender-receiver communication so that the involved RunnableEntitys just need the same type of APIs against the RTE as for sender-receiver communication.

This is possible, because ModeDeclarationGroupPrototypes can be mapped to an ImplementationDataTypes. This concept and the meta-classes needed for the mapping are further explained in chapter 4.2.5. (cid:99)(RS_SWCT_00200)

[TPS_SWCT_01353] RunnableEntitys react on a mode request via a corresponding RTEEvent (cid:100) In the second case, one RunnableEntity "sends" a mode request and one or more other RunnableEntitys react on the request via a corresponding RTEEvent or by being suppressed from being triggered any longer by other RTEEvents. In this case, special APIs against the RTE are required and the RTE has to implement the actual mode switch. This kind of communication is only possible between software components on the same ECU. For further explanation of the general concept refer to chapter 4.2.5 and for the details of the meta-model for mode switches refer to chapter 9. (cid:99)(RS_SWCT_00200, RS_SWCT_03202)

#@SECTION: 7.6 Port API Options
#@CLASS: AtomicSwComponentType
#@ENUM: DataTransformationErrorHandlingEnum
#@CLASS: PortAPIOption
#@CLASS: PortDefinedArgumentValue
#@CLASS: PortPrototype
#@CLASS: RunnableEntity

[TPS_SWCT_01354] PortAPIOption (cid:100) The RTE Generator needs additional options per PortPrototype to choose the proper generation schema. These are subsumed in the PortAPIOption element which is shown in Figure 7.31. (cid:99)()

Figure 7.31: Port API Options.

Table 7.45: PortAPIOption

[TPS_SWCT_01626] Error notification of data transformer errors (cid:100) If the attribute PortAPIOption.errorHandling is set to transformerErrorHandling then all RunnableEntitys accessing the PortPrototype referenced by port shall handle the extended transformer error notification. (cid:99)(RS_SWCT_03222)

Enumeration DataTransformationErrorHandlingEnum Package M2::AUTOSARTemplates::SWComponentTemplate::SwcInternalBehavior::PortAPI Options This enumeration defines different ways how runnables shall handle transformer errors. Description A runnable does not handle transformer errors.

Note Literal noTransformerErrorHandling transformerErrorHandling The runnable implements the handling of transformer errors.

Table 7.46: DataTransformationErrorHandlingEnum

#@SECTION: 7.6.1 Enable to Take Address
#@CLASS: PortAPIOption
#@CLASS: PortPrototype
#@CLASS: SwcInternalBehavior

[TPS_SWCT_01355] enableTakeAddress = true (cid:100) If the attribute enableTakeAddress = true the generated API related to this PortPrototype is provided in a way that the software-component is able to use the API reference for deriving a pointer to an object. (cid:99)()

The main focus of the feature is support for configuration of AUTOSAR Services which are limited to single instances.

[constr_2024] enableTakeAddress is restricted to single instantiation (cid:100) The definition of a PortAPIOption with enableTakeAddress set to true is only permitted for software-components where the attribute SwcInternalBehavior.supportsMultipleInstantiation is set to false. (cid:99)()

#@SECTION: 7.6.2 Indirect API Generation
#@CLASS: PortPrototype

[TPS_SWCT_01356] indirectAPI option switches the generation of the RTE’s indirect API functionality (cid:100) The indirectAPI option switches the generation of the RTE’s indirect API functionality for a certain PortPrototype. The generated indirect API does allow to iterate over ports within the SW-Component. (cid:99)()

#@SECTION: 7.6.3 Port Deﬁned Argument Value
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: ClientServerInterface
#@CLASS: PPortPrototype
#@CLASS: PortAPIOption
#@CLASS: PortDefinedArgumentValue
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@CLASS: PortInterface

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
#@CLASS: PerInstanceMemory
#@CLASS: SwcInternalBehavior
#@CLASS: VariableDataPrototype

[TPS_SWCT_01359] Private memory per instance (cid:100) AtomicSwComponentTypes that support multiple instantiation (attribute supportsMultipleInstantiation == true) will typically need a given amount of private memory per instance. It is the responsibility of the RTE to provide a mechanisms with which each instance of an AtomicSwComponentType can access its own instance-specific memory. (cid:99)()

[TPS_SWCT_01360] Arbitrary number of per-instance memory blocks (cid:100) An AtomicSwComponentType can define an arbitrary number of per-instance memory blocks. (cid:99)()

Figure 7.32: PerInstanceMemory

[TPS_SWCT_01361] attribute supportsMultipleInstantiation == false (cid:100) AtomicSwComponentTypes that do not support multiple instantiation (attribute supportsMultipleInstantiation == false) do not necessarily need to use the PerInstanceMemory: because there will only be a single instance of the AtomicSwComponentType on an ECU, the AtomicSwComponentType can use static variables to store the AtomicSwComponentType's internal state. However, the usage of PerInstanceMemory is also allowed in this case. (cid:99)()

[TPS_SWCT_01362] Initialization of PerInstanceMemory (cid:100) Note that the PerInstanceMemory is not initialized by the RTE if no initValue is defined. In this case, it is the responsibility of the AtomicSwComponentType to initialize the PerInstanceMemory. (cid:99)()

#@SECTION: 7.7.1 PerInstanceMemory typed by “C” Data Types
#@CLASS: PerInstanceMemory
#@CLASS: SwcInternalBehavior

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
#@CLASS: DataPrototype
#@CLASS: PerInstanceMemory
#@CLASS: VariableDataPrototype
#@CLASS: ValueSpecification
#@CLASS: SwDataDefProps

[TPS_SWCT_01365] PerInstanceMemory typed by AUTOSAR Data Types (cid:100) A PerInstanceMemory typed with AUTOSAR data types is defined by a VariableDataPrototype in the role arTypedPerInstanceMemory. VariableDataPrototype is derived from DataPrototype which has an association to an AutosarDataType. (cid:99)() 
This defines the data type of the AUTOSAR-typed PerInstanceMemory.

[TPS_SWCT_01366] Initial value of a PerInstanceMemory typed by AUTOSAR Data Types (cid:100) The initValue is described with a ValueSpecification (cid:99)()

typed by C data type (cid:100)
[TPS_SWCT_01367] Typed by AUTOSAR data type vs. In difference to the "C" typed PerInstanceMemory the AUTOSAR-typed PerInstanceMemory is able to define information controlling the visibility in a MCD system via a SwDataDefProps for the purpose of measurement (see chapter 5.4.3) or defining an input value of an axis (see chapter 5.4.5). (cid:99)()

Note: Due to the use of AutosarDataType the AUTOSAR-typed PerInstanceMemory can not support C++ specific types or pointer types directly.

#@SECTION: 7.8 Static Memory and Constant Memory
#@CLASS: AtomicSwComponentType
#@CLASS: InternalBehavior
#@CLASS: ParameterDataPrototype
#@CLASS: SwcInternalBehavior
#@CLASS: VariableDataPrototype
#@CLASS: PerInstanceMemory

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
#@CLASS: DataPrototype
#@CLASS: IncludedDataTypeSet
#@CLASS: SwcInternalBehavior

[TPS_SWCT_01155] IncludedDataTypeSet (cid:100) An IncludedDataTypeSet declares that a set of AutosarDataTypes are used for the C / C++ implementation of the software component. The AutosarDataTypes become part of the contract. (cid:99)()

[TPS_SWCT_01156] Required if the AutosarDataType is not used for any DataPrototype (cid:100) This information is required if the AutosarDataType is not used for any DataPrototype owned by this software component or if a prefix for C language identifiers belonging to AutosarDataTypes shall be defined. (cid:99)()

Figure 7.34: Included AUTOSAR Data Types

Table 7.49: IncludedDataTypeSet

This supports the common usage of the AUTOSAR data type system for RTE provided memory objects and memory objects declared by the software component implementation.

Further on, this enables the generation of the RTE Application Types Header File for AUTOSAR services containing the required data types for the C-API before the data type usage in dedicated ports for an ECU is known.

[TPS_SWCT_01157] Attribute literalPrefix of IncludedDataTypeSet (cid:100) In addition the literalPrefix might be used to separate the namespace of C language identifiers belonging to equally named AutosarDataTypes used for the same software component C implementation. (cid:99)()

#@SECTION: 7.10 Included Mode Declaration Groups
#@CLASS: AtomicSwComponentType
#@CLASS: IncludedModeDeclarationGroupSet
#@CLASS: ModeDeclarationGroup
#@CLASS: SwcInternalBehavior

[TPS_SWCT_01153] IncludedModeDeclarationGroupSet (cid:100) Similar to the consideration of data types using IncludedDataTypeSet, SwcInternalBehavior aggregates IncludedModeDeclarationGroupSet that in turn allows for referencing ModeDeclarationGroups with the intent to express that the referenced ModeDeclarationGroups are used in the context of the enclosing AtomicSwComponentType. (cid:99)()

Figure 7.35: Included ModeDeclarationGroups

Table 7.50: IncludedModeDeclarationGroupSet

[TPS_SWCT_01154] Attribute prefix of IncludedModeDeclarationGroupSet (cid:100) The optional attribute prefix of IncludedModeDeclarationGroupSet can be used to define a prefix that the RTE generator shall use to define symbols related to the included ModeDeclarationGroups with the intent to avoid potential name clashes. (cid:99)()

Rationale: If the attribute prefix is required, changes to software-component source code may be necessary.

#@SECTION: 7.11 Service Needs
#@SECTION: 7.11.1 Overview
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: NvBlockSwComponentType
#@CLASS: ServiceNeeds
#@CLASS: SwcServiceDependency

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
#@CLASS: SymbolicNameProps
#@CLASS: ApplicationSwComponentType
#@CLASS: AtomicSwComponentType
#@CLASS: AutosarDataPrototype
#@CLASS: AutosarParameterRef
#@CLASS: AutosarVariableRef
#@CLASS: DataPrototype
#@CLASS: ImplementationDataType
#@CLASS: NvBlockSwComponentType
#@CLASS: ParameterDataPrototype
#@CLASS: ParameterInterface
#@CLASS: PerInstanceMemory
#@CLASS: PortGroup
#@CLASS: PortInterface
#@CLASS: PortPrototype
#@CLASS: PPortPrototype
#@CLASS: RoleBasedDataAssignment
#@CLASS: RoleBasedDataTypeAssignment
#@CLASS: RoleBasedPortAssignment
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: ServiceDependency
#@CLASS: ServiceNeeds
#@CLASS: SwcInternalBehavior
#@CLASS: SwcServiceDependency
#@CLASS: VariableDataPrototype

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
#@CLASS: NvBlockNeeds
#@CLASS: NvBlockSwComponentType
#@CLASS: SwcInternalBehavior
#@CLASS: SwcServiceDependency

This chapter describes the usage of the specific meta-classes derived from Service Needs within an AtomicSwComponentType.

The meta-class NvBlockNeeds is used to define requirements to configure the NVRAM Manager Service. In addition, it may define requirements how the RTE shall implement writing strategies of an NvBlockSwComponentType.

An SwcInternalBehavior may provide several SwcServiceDependencys that in turn aggregate an NvBlockNeeds element where each defines the requirements from one NVRAM Block (for more information on the AUTOSAR NVRAM Manager see [31]).

There are several use cases how a software-component can interact with the NVRAM Manager service. Each use case is discussed in a separate sub-chapter.

Table 7.58: NvBlockNeeds

Table 7.59: RamBlockStatusControlEnum

#@SECTION: 7.11.3.1.1 Nvm Use Case: Permanent RAM Block
#@CLASS: AtomicSwComponentType
#@CLASS: ClientServerInterface
#@CLASS: NvBlockSwComponentType
#@CLASS: ParameterDataPrototype
#@CLASS: PerInstanceMemory
#@CLASS: RoleBasedDataAssignment
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency
#@CLASS: VariableDataPrototype

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
#@CLASS: ClientServerInterface
#@CLASS: RoleBasedDataAssignment
#@CLASS: RoleBasedDataTypeAssignment
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency

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
#@CLASS: ClientServerInterface
#@CLASS: NvBlockDescriptor
#@CLASS: NvBlockSwComponentType
#@CLASS: NvDataInterface
#@CLASS: NvDataPortAnnotation
#@CLASS: NvMAdmin
#@CLASS: NvMMirror
#@CLASS: NvMNotifyInitBlock
#@CLASS: NvMNotifyJobFinished
#@CLASS: NvMService
#@CLASS: ParameterDataPrototype
#@CLASS: PerInstanceMemory
#@CLASS: RoleBasedDataAssignment
#@CLASS: RoleBasedDataTypeAssignment
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcInternalBehavior
#@CLASS: VariableDataPrototype

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
#@CLASS: ClientServerInterface
#@CLASS: NvBlockSwComponentType
#@CLASS: NvDataInterface
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: ServiceSwComponentType
#@CLASS: SwcServiceDependency

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

The meta-class SupervisedEntityNeeds is used to define requirements to configure the Watchdog Service. For the terms related to the AUTOSAR Watchdog Manager see [32].

#@SECTION: 7.11.3.2.1 Watchdog Service use Case: Supervision
#@CLASS: AtomicSwComponentType
#@CLASS: SwcInternalBehavior
#@CLASS: SupervisedEntityNeeds

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
#@CLASS: SwcInternalBehavior
#@CLASS: PortGroup

The meta-class ComMgrUserNeeds is used to define requirements to configure the ComM Service. An SwcInternalBehavior may provide several ComMgrUserNeeds elements where each defines the requirements from one "user" of the ComM Service. Especially, it defines which PortGroup is associated with this "user".

Table 7.61: ComMgrUserNeeds

#@SECTION: 7.11.3.3.1 ComM Use Case: read current ComM Mode
#@CLASS: AtomicSwComponentType

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
#@CLASS: PortGroup

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
#@CLASS: SwcInternalBehavior

The meta-class EcuStateMgrUserNeeds is used to define the requirements to configure the ECU State Manager Service. There are actually two variants of AUTOSAR ECU management: flexible and fixed. An SwcInternalBehavior may provide several EcuStateMgrUserNeeds elements where each defines the requirements from one "user" of the EcuM Service (for the terms related to the AUTOSAR ECU State Manager see [33]).

Table 7.62: EcuStateMgrUserNeeds

#@SECTION: 7.11.3.4.1 EcuM Fixed Use Case: read current ECU Mode
#@CLASS: AtomicSwComponentType

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
#@CLASS: RoleBasedPortAssignment

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
#@CLASS: RoleBasedPortAssignment

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
#@CLASS: RoleBasedPortAssignment

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
#@CLASS: ServiceNeeds
#@CLASS: SwcServiceDependency

All use cases for interaction of an application software-component with the BswM require the aggregation in the role serviceNeeds of BswMgrNeeds, a subclass of ServiceNeeds, at SwcServiceDependency.

Table 7.63: BswMgrNeeds

#@SECTION: 7.11.3.5.1 Partial Networking
#@CLASS: PortGroup
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency

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
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ApplicationSwComponentType
#@CLASS: ModeSwitchInterface
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface
#@CLASS: ServiceSwComponentType
#@CLASS: SwComponentPrototype

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
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: RoleBasedPortAssignment

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
#@CLASS: RPortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface

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
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcInternalBehavior

The meta-class CryptoServiceNeeds is used to define the requirements to configure the CryptoServiceManager.

An SwcInternalBehavior may provide several CryptoServiceNeeds elements where each relates to one ConfigID (see [34] for details). In this context it is of special importance to note which PortPrototypes belong to this ConfigID in order to be able to properly generate the callbacks.

Table 7.64: CryptoServiceNeeds

Please note that for all described use cases of the Crypto Service following rule applies: For every used ClientServerInterface it is necessary to create a RoleBasedPortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServer Interface. The possible role attribute values and the multiplicity of the related Port Prototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment.

#@SECTION: 7.11.3.6.1 Crypto Service Service Use Case: Hash calculation
#@CLASS: AtomicSwComponentType

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
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment

This chapter describes the usage of the specific diagnostic meta-classes derived from ServiceNeeds within an atomic software-component. An overview of common diagnostic service needs has already been introduced in figure 7.36 and can be divided into four main parts: Function Inhibition Needs 7.11.3.7.1, Diagnostic Event Needs 7.11.3.7.2, Diagnostic Communication Needs 7.11.3.7.3, and needs to fulfill the OBD related requirements 7.11.3.7.4.

Please note that for the described use cases of the Diagnostic Services the following rule applies:

[TPS_SWCT_01129] Express diagnostic capabilities (cid:100) For every used ClientServerInterface it is necessary to create a RoleBasedPortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServerInterface.

The possible role attribute values and the multiplicity of the related PortPrototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment. (cid:99)(RS_SWCT_03190)

#@SECTION: 7.11.3.7.1 Function Inhibition Needs
#@CLASS: FunctionInhibitionNeeds
#@CLASS: SwcInternalBehavior

The meta-class FunctionInhibitionNeeds is used to define requirements in order to configure the Diagnostic Event Manager Service.

An SwcInternalBehavior may provide several FunctionInhibitionNeeds elements, each defines the requirements related to one function inhibition ID (for the terms related to the AUTOSAR Function Inhibition Manager, see [35]).

Table 7.65: FunctionInhibitionNeeds

#@SECTION: 7.11.3.7.1.1 Function Inhibition Manager Service use Case: read function permission
#@CLASS: AtomicSwComponentType

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
#@CLASS: DiagnosticEnableConditionNeeds
#@CLASS: DiagnosticEventInfoNeeds
#@CLASS: DiagnosticEventManagerNeeds
#@CLASS: DiagnosticEventNeeds
#@CLASS: DiagnosticOperationCycleNeeds
#@CLASS: DiagnosticStorageConditionNeeds
#@ENUM: DtcKindEnum
#@CLASS: DtcStatusChangeNotificationNeeds
#@ENUM: DtcFormatTypeEnum
#@ENUM: EventAcceptanceStatusEnum
#@CLASS: FunctionInhibitionNeeds
#@CLASS: ObdRatioServiceNeeds
#@ENUM: OperationCycleTypeEnum
#@CLASS: PortPrototype
#@CLASS: RPortPrototype
#@ENUM: ReportBehaviorEnum
#@ENUM: StorageConditionStatusEnum
#@CLASS: SwcInternalBehavior
#@CLASS: SwcServiceDependency
#@ENUM: DiagnosticAudienceEnum
#@CLASS: ObdPidServiceNeeds
#@CLASS: DiagEventDebounceAlgorithm
#@CLASS: DiagEventDebounceCounterBased
#@CLASS: DiagEventDebounceTimeBased
#@CLASS: DiagEventDebounceMonitorInternal
#@CLASS: RoleBasedPortAssignment


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
#@CLASS: DiagnosticEventNeeds
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
#@CLASS: DiagnosticEventNeeds

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
#@CLASS: DiagnosticOperationCycleNeeds

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
#@CLASS: RoleBasedPortAssignment
#@CLASS: DiagnosticEventManagerNeeds
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
#@CLASS: DiagnosticEnableConditionNeeds

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
#@CLASS: DiagnosticStorageConditionNeeds

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
#@CLASS: ServiceNeeds

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
#@CLASS: ServiceNeeds

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
#@CLASS: DiagnosticEventManagerNeeds

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
#@CLASS: RoleBasedPortAssignment
#@CLASS: DiagnosticEventManagerNeeds

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
#@CLASS: SwcServiceDependency
#@CLASS: DtcStatusChangeNotificationNeeds
#@ENUM: DtcFormatTypeEnum

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
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: PPortPrototype
#@CLASS: DiagnosticEventInfoNeeds
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
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: DiagnosticEventManagerNeeds

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
#@CLASS: ClientServerInterface
#@CLASS: PPortPrototype
#@CLASS: PortInterface
#@CLASS: SenderReceiverInterface
#@CLASS: SwcServiceDependency

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
#@CLASS: ServiceSwComponentType
#@CLASS: ServiceNeeds
#@CLASS: ApplicationSwComponentType

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
#@CLASS: DiagnosticEventInfoNeeds
#@CLASS: RoleBasedPortAssignment
#@CLASS: RoleBasedDataAssignment

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
#@CLASS: DiagnosticIoControlNeeds
#@CLASS: DiagnosticRoutineNeeds
#@CLASS: DiagnosticValueNeeds
#@CLASS: PPortPrototype
#@CLASS: SwcInternalBehavior
#@CLASS: SwcServiceDependency
#@ENUM: DiagnosticServiceRequestCallbackTypeEnum
#@CLASS: ClientServerInterface
#@CLASS: ClientServerOperation
#@CLASS: RunnableEntity
#@ENUM: DiagnosticRoutineTypeEnum
#@CLASS: SenderReceiverInterface
#@CLASS: InternalBehavior
#@CLASS: BswServiceDependency
#@ENUM: DiagnosticValueAccessEnum
#@ENUM: DiagnosticProcessingStyleEnum
#@CLASS: DiagnosticsCommunicationSecurityNeeds

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
#@CLASS: ClientServerInterface
#@CLASS: PPortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency

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
#@CLASS: ClientServerInterface
#@CLASS: PPortPrototype
#@CLASS: PortInterface
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency
#@CLASS: DiagnosticValueNeeds
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
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: PortPrototype
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface
#@CLASS: SwcServiceDependency
#@CLASS: DiagnosticValueNeeds
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
#@CLASS: ClientServerInterface
#@CLASS: PortPrototype
#@CLASS: SwcServiceDependency
#@CLASS: DiagnosticRoutineNeeds
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
#@CLASS: ClientServerInterface
#@CLASS: PortPrototype
#@CLASS: SwcServiceDependency
#@CLASS: DiagnosticIoControlNeeds

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
#@CLASS: AtomicSwComponentType
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: PortPrototype
#@CLASS: RoleBasedDataAssignment
#@CLASS: RoleBasedPortAssignment
#@CLASS: SenderReceiverInterface
#@CLASS: ServiceSwComponentType
#@CLASS: SwComponentPrototype
#@CLASS: SwcServiceDependency
#@CLASS: DiagnosticIoControlNeeds

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
#@CLASS: DiagnosticCommunicationManagerNeeds

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
#@CLASS: PortInterface
#@CLASS: SwcServiceDependency
#@CLASS: DiagnosticsCommunicationSecurityNeeds

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
#@CLASS: DiagnosticCommunicationManagerNeeds

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
#@CLASS: DiagnosticCommunicationManagerNeeds

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
#@CLASS: ObdControlServiceNeeds
#@CLASS: ObdPidServiceNeeds
#@CLASS: ObdInfoServiceNeeds
#@CLASS: ObdMonitorServiceNeeds
#@CLASS: ObdRatioServiceNeeds

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
#@CLASS: ObdRatioServiceNeeds
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency

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
#@CLASS: ClientServerInterface
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency
#@CLASS: ObdPidServiceNeeds
#@CLASS: PortInterface

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
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: ObdPidServiceNeeds

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
#@CLASS: PortInterface
#@CLASS: SwcServiceDependency
#@CLASS: ObdInfoServiceNeeds

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
#@CLASS: ObdMonitorServiceNeeds

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
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency
#@CLASS: ObdControlServiceNeeds
#@CLASS: PortInterface
#@CLASS: SwcServiceDependency

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
#@CLASS: ServiceNeeds

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
#@CLASS: DoIpGidNeeds
#@CLASS: DoIpGidSynchronizationNeeds
#@CLASS: DoIpPowerModeStatusNeeds
#@CLASS: DoIpRoutingActivationAuthenticationNeeds
#@CLASS: DoIpRoutingActivationConfirmationNeeds
#@CLASS: DoIpServiceNeeds


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
#@CLASS: DoIpRoutingActivationAuthenticationNeeds
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
#@CLASS: DoIpGidNeeds

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
#@CLASS: RoleBasedPortAssignment

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
#@CLASS: SwcServiceDependency
#@CLASS: DoIpRoutingActivationAuthenticationNeeds
#@CLASS: DoIpRoutingActivationConfirmationNeeds

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
#@CLASS: ServiceSwComponentType
#@CLASS: ModeSwitchInterface
#@CLASS: DoIpActivationLineNeeds

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
#@CLASS: PPortPrototype
#@CLASS: ServiceSwComponentType
#@CLASS: WarningIndicatorRequestedBitNeeds

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
#@CLASS: RoleBasedPortAssignment
#@CLASS: SwcServiceDependency

The meta-class DltUserNeeds is used together with the SwcServiceDependency to define requirements in order to configure the Diagnostic Log and Trace module (for the terms related to the AUTOSAR Specification of Module DLT see [40]).

Table 7.108: DltUserNeeds

Please note that for the described use case of the Dlt Service the following rule applies: For every used ClientServerInterface it is necessary to create a RoleBased PortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServerInterface. The possible role attribute values and the multiplicity of the related PortPrototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment.

#@SECTION: 7.11.3.8.1 Dlt use Case: Application software component accesses the Synchronized Time-Base Manager
#@CLASS: AtomicSwComponentType

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
#@CLASS: SyncTimeBaseMgrUserNeeds

The meta-class SyncTimeBaseMgrUserNeeds is used together with the SwcServiceDependency to define requirements in order to configure the Synchronized Time-Base Manager module (for the terms related to the AUTOSAR Specification of Module StbM see [41]).

Table 7.109: SyncTimeBaseMgrUserNeeds

Please note that for the described use cases of the StbM Service following rule applies: For every used ClientServerInterface it is necessary to create a RoleBasedPortAssignment. Thereby the value of the attribute role of the RoleBasedPortAssignment has to be set to the name of the used standardized ClientServerInterface. The possible role attribute values and the multiplicity of the related PortPrototypes are listed at the use case descriptions in the paragraph RoleBasedPortAssignment.

#@SECTION: 7.11.3.9.1 StbM use Case: Application software component accesses the Synchronized Time-Base Manager
#@CLASS: AtomicSwComponentType

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
#@CLASS: RoleBasedPortAssignment

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
#@CLASS: VariationPoint
#@CLASS: SwSystemconstantValueSet
#@CLASS: PostBuildVariantCriterionValueSet
#@CLASS: SwSystemconstDependentFormula

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

#@SECTION: 8 Implementation
#@CLASS: PerInstanceMemorySize
#@CLASS: SwcImplementation
#@CLASS: Implementation
Previous versions of this document contained a comprehensive description of the meta-class Implementation. This meta-class still exists but the description of most of its content has been moved to another document, in particular the specification of the Basic Software Module Description Template [7].

Please note that the Software Component Template and the Basic Software Module Description Template share the content of Implementation. However, the semantics of Implementation is closer to the Basic Software Module Description Template.

Nevertheless, there is still content strictly related to the Software Component Template. This part of Implementation consisting of SwcImplementation (see Figure 8.1) remains in this document.

Figure 8.1: Implementation part specific to the Software Component Template

Table 8.1: SwcImplementation

Table 8.2: PerInstanceMemorySize

#@SECTION: 9 Mode Management
#@CLASS: ModeSwitchInterface
#@CLASS: RPortPrototype
#@CLASS: SwComponentType
#@CLASS: SwConnector
#@CLASS: PortInterface

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
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeTransition

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
#@CLASS: AtomicSwComponentType
#@CLASS: ModeAccessPoint
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeSwitchPoint
#@CLASS: ModeSwitchedAckEvent
#@CLASS: ModeSwitchedAckRequest
#@CLASS: RTEEvent
#@CLASS: RunnableEntity
#@CLASS: SwcInternalBehavior
#@CLASS: SwcModeSwitchEvent
#@CLASS: ModeTransition

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
#@CLASS: ModeDeclarationGroup
The AUTOSAR standard shall support the execution of initialization code for every AtomicSwComponentType.

[TPS_SWCT_01384] Execution of initialization code for software-components (cid:100) Most AtomicSwComponentTypes will need to initialize by executing specific code; this code shall complete before any other code in the component is executed. Data will be initializing to specific values before the "normal" application software is running. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01385] Execution of finalization code for software-components (cid:100) Most AtomicSwComponentTypes will need to finalize by calling specific code; this code shall complete before the functionality of the application software shut down (e.g. a motor drive in a start or end position). (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01388] Initial modes of AtomicSwComponentTypes are defined by the initialMode (cid:100) The initial modes of AtomicSwComponentTypes are defined by the initialMode references of the required ModeDeclarationGroups. These modes are activated before any other mode activation has occurred. It is the responsibility of the RTE to activate all initial modes on a certain ECU. (cid:99)(RS_SWCT_03110)

For more details please refer to the specification of the SWS RTE [2].

#@SECTION: 9.4 Mode Error Behavior
#@CLASS: AbstractProvidedPortPrototype
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeErrorBehavior
#@ENUM: ModeErrorReactionPolicyEnum
#@CLASS: ModeSwitchInterface
#@CLASS: PortInterfaceMapping
#@CLASS: SwcModeManagerErrorEvent
#@CLASS: SwConnector

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
#@CLASS: AbstractRequiredPortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: ModeSwitchedAckEvent
#@CLASS: ModeSwitchInterface
#@CLASS: PortInterface
#@CLASS: PRPortPrototype
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: RunnableEntity
#@CLASS: ServiceProxySwComponentType
#@CLASS: SwcInternalBehavior
#@CLASS: SwComponentType
#@CLASS: SwcModeSwitchEvent
#@CLASS: PortGroup

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
#@CLASS: SoftwareComponentTemplate

During the design of embedded systems there is one crucial point where the hardware and software have to be related. In AUTOSAR the ECU Resource Template describes the provided hardware resources.

On the other hand, the Software Component Template describes software generally without specific hardware in mind. But there are some places where both have to meet and fit.

One interface between hardware and software is discussed in the memory and execution time section of [7]. In this chapter the overall system view of the interface between sensors/actuators and software is described and the consequences for the Software Component Template are derived.

#@SECTION: 10.2 High Level Hardware and Software Architecture
#@CLASS: SensorActuatorSwComponentType

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
#@CLASS: SensorActuatorSwComponentType

Two fundamentally different interfaces are involved when converting from sensors/actuators to software components, see markers “4” and “5” in Figure 10.2.

The interface between the Microcontroller Abstraction and the ECU Abstraction is a Standardized Interface (see AUTOSAR Glossary [42]). This interface is not visible on the Virtual Function Bus and therefore the MCAL and ECU Abstraction have to be present on the same ECU.

For further description of this interface please refer to the ECU Resource Template documentation.

The interface to the SensorActuatorSwComponentTypes is visible on the Virtual Function Bus. In general the SensorActuatorSwComponentType should be on the same ECU as the ECU hardware abstraction.

Also the interface between the SensorActuatorSwComponentTypes and the actual AtomicSwComponentTypes representing the application is visible on the VFB. To describe the data that is going to be exchanged via this interface the standard AUTOSAR Interface description mechanisms are used (see chapter 3.4).

#@SECTION: 10.3.1 ECU Abstraction and its AUTOSAR Interfaces
#@CLASS: AtomicSwComponentType
#@CLASS: PortPrototype
#@CLASS: SensorActuatorSwComponentType

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
#@CLASS: ComplexDeviceDriverSwComponentType
#@CLASS: EcuAbstractionSwComponentType
#@CLASS: SensorActuatorSwComponentType
#@CLASS: SwComponentPrototype
#@CLASS: HwType
#@CLASS: HwDescriptionEntity
#@CLASS: HwElement
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
#@CLASS: HwElement
#@CLASS: BswModuleDescription
#@CLASS: SwcBswMapping
#@CLASS: InternalBehavior

[TPS_SWCT_01389] I/O Hardware Abstraction interfaces MCAL drivers (cid:100) The I/O Hardware Abstraction interfaces on one side the MCAL drivers via Standardized Interfaces and on the other side the Sensor Actuator Software Component via AUTOSAR Interfaces. On the VFB[3] the I/O Hardware Abstraction is represented by the EcuAbstractionSwComponentType. (cid:99)()

[TPS_SWCT_01390] I/O Hardware Abstraction might have sub-structures (cid:100) Depending on the complexity of an ECU, the I/O Hardware Abstraction might have sub-structures. In this case the I/O Hardware Abstraction Layer is described by several different EcuAbstractionSwComponentTypes on M1. (cid:99)()

Table 10.2: EcuAbstractionSwComponentType

[TPS_SWCT_01391] I/O Hardware Abstraction abstracts from the location of peripheral I/O devices (cid:100) The I/O Hardware Abstraction abstracts from the location of peripheral I/O devices (on-chip or on-board) and the ECU hardware layout and has therefore dependencies to ECU Hardware described by HwElements. In addition, the EcuAbstractionSwComponentType is a hybrid concept sharing features of both software-components and basic software modules. (cid:99)()

[TPS_SWCT_01392] Mapping between the EcuAbstractionSwComponentType and the corresponding BswModuleDescription (cid:100) The BSW part is described by the means of the Basic Software Module Template. The mapping between the EcuAbstractionSwComponentType and the corresponding BswModuleDescription is provided by the class SwcBswMapping which in addition also maps the two corresponding InternalBehaviors. This mechanism is further explained in [7]. (cid:99)()

Figure 10.7: EcuAbstractionSwComponentType

#@SECTION: 10.6 Complex Driver
#@CLASS: AtomicSwComponentType
#@CLASS: ComplexDeviceDriverSwComponentType
#@CLASS: EcuAbstractionSwComponentType
#@CLASS: SwcBswMapping
#@CLASS: SwcInternalBehavior
#@CLASS: HwElement
#@CLASS: BswModuleDescription
#@CLASS: SwcBswMapping
#@CLASS: InternalBehavior

[TPS_SWCT_01393] Complex Driver (cid:100) A Complex Driver implements complex sensor evaluation and actuator control with direct access to the Microcontroller using specific interrupts and/or complex Microcontroller peripherals to fulfill the special functional and timing requirements. In addition it might be used to implement enhanced services / protocols or encapsulates legacy functionality of a non-AUTOSAR system. (cid:99)() 
See also document [3].

[TPS_SWCT_01394] Complex Driver is represented by the ComplexDeviceDriverSwComponentType (cid:100) On the VFB the Complex Driver is represented by the ComplexDeviceDriverSwComponentType. An ECU might have zero to many different ComplexDeviceDriverSwComponentTypes. (cid:99)()

Table 10.3: ComplexDeviceDriverSwComponentType

[TPS_SWCT_01395] ComplexDeviceDriverSwComponentType has dependencies to ECU Hardware (cid:100) Similar to EcuAbstractionSwComponentType the ComplexDeviceDriverSwComponentType has dependencies to ECU Hardware described by HwElements and is a hybrid between Software Component and Basic Software Module. (cid:99)()

[TPS_SWCT_01396] Mapping between the ComplexDeviceDriverSwComponentType and the corresponding BswModuleDescription (cid:100) The BSW part is described by the means of the Basic Software Module Template. The mapping between the ComplexDeviceDriverSwComponentType and the corresponding BswModuleDescription is provided by the class SwcBswMapping which in addition also maps the two corresponding InternalBehaviors. This mechanism is further explained in [7]. (cid:99)()

Figure 10.8: ComplexDeviceDriverSwComponentType

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