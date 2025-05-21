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
Figure 3.9: Use case for PassThroughSwConnector (I)
Table 3.16: PassThroughSwConnector
Figure 3.10: Connectors
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