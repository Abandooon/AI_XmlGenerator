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

Application software within AUTOSAR is organized in self-contained units called Atom
icSwComponentTypes. Such AtomicSwComponentTypes encapsulate the imple
mentation of their functionality and behavior and merely expose well-deﬁned connec
tion points, called PortPrototypes, to the outside world.



Figure 3.1: Graphical representation of software-components in AUTOSAR

The graphical appearance of AUTOSAR software-components according to [3] is de
picted in Figure 3.1.

Class
Package
Note
Base

Attribute
consistenc
yNeeds

SwComponentType (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Components
Base class for AUTOSAR software components.
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,Identiﬁable,MultilanguageReferrable,Packageable
Element,Referrable
Datatype
ConsistencyNee
ds

Mul. Kind Note
aggr

This represents the colelction of
ConsistencyNeeds owned by the enclosing
SwComponentType.

*

port

PortPrototype

*

aggr

portGroup

PortGroup

*

aggr

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=preCompileTime
The ports through which this component can
communicate. The aggregation of PortPrototype is
subject to variability with the purpose to support
the conditional existence of PortPrototypes.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=preCompileTime
A port group being part of this component.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=preCompileTime



Attribute
swCompon
entDocum
entation

Datatype
SwComponentD
ocumentation

Mul. Kind Note
aggr
0..1

This adds a documentation to the
SwComponentType.

unitGroup

UnitGroup

*

ref

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=swComponentDocumentation,
variationPoint.shortLabel
vh.latestBindingTime=preCompileTime
xml.sequenceOffset=-10
This allows for the speciﬁcation of which
UnitGroups are relevant in the context of
referencing SwComponentType.

Table 3.1: SwComponentType

#@SECTION: 3.2.2 PortPrototype

Please note that PortPrototypes of a SwComponentType are supposed to be used
for attaching SwConnectors that establish an actual connection between SwCompo
nentPrototypes (see chapter 3.3).

[TPS_SWCT_01002] SwComponentTypes may only interact by means of their
PortPrototypes (cid:100) AtomicSwComponentTypes (and also the more general
SwComponentTypes may only interact by means of their PortPrototypes). Hidden
communication dependencies that are not expressed by means of PortPrototypes
(cid:99)(RS_SWCT_00020, RS_SWCT_00030, RS_SWCT_00150,
are strictly forbidden.
RS_SWCT_00160, RS_SWCT_00200, RS_SWCT_00210, RS_SWCT_02010,
RS_SWCT_02030)

Therefore, software-components are in theory exchangeable as long as they implement
the same functionality and provide the same public communication interface to the
remaining system.

Class
Package
Note

PortPrototype (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Components
Base class for the ports of an AUTOSAR software component.

The aggregation of PortPrototypes is subject to variability with the purpose to support
the conditional existence of ports.
ARObject,AtpBlueprintable,AtpFeature,AtpPrototype,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
ClientServerAnn
otation

Annotation of this PortPrototype with respect to
client/server communication.

Mul. Kind Note
aggr

*

DelegatedPortA
nnotation

0..1

aggr

Annotations on this delegated port.

Base

Attribute
clientServe
rAnnotatio
n
delegated
PortAnnota
tion




Attribute
ioHwAbstr
actionServ
erAnnotati
on
modePortA
nnotation
nvDataPort
Annotation
parameter
PortAnnota
tion
senderRec
eiverAnnot
ation
triggerPort
Annotation

Datatype
IoHwAbstraction
ServerAnnotatio
n

ModePortAnnot
ation
NvDataPortAnn
otation
ParameterPortA
nnotation

SenderReceiver
Annotation

TriggerPortAnn
otation



Mul. Kind Note
aggr

*

Annotations on this IO Hardware Abstraction port.

*

*

*

*

*

aggr

Annotations on this mode port.

aggr

Annotations on this non voilatile data port.

aggr

Annotations on this parameter port.

aggr Collection of annotations of this ports

sender/receiver communication.

aggr

Annotations on this trigger port.

Table 3.2: PortPrototype

Figure 3.2: Overview of PortPrototype

[TPS_SWCT_01111] PortPrototypes need an additional model artifact, the
PortInterface (cid:100) Please note that PortPrototypes actually need an additional
model artifact, the PortInterface, for fully describing the details of the PortPro
totype. The concept of the PortInterface as another means for establishing a
high degree of re-usability is described in chapter 3.4. (cid:99)(RS_SWCT_00010)

[TPS_SWCT_01112] Semantics of PortPrototypes (cid:100) As depicted in Figure 3.2,
PortPrototypes can have the following semantics:

• A require-port (in technical terms: RPortPrototype) requires certain services

or data.




PPortPrototypeAtpBlueprintableAtpPrototypePortPrototypeRPortPrototypePRPortPrototypeAbstractRequiredPortPrototypeAbstractProvidedPortPrototype

• A provide-port (or PPortPrototype) on the other hand provides services or

data.

• A provide-require-port (or PRPortPrototype) combines the ability to provide

and require services or data in one entity.

(cid:99)(RS_SWCT_03250)

[TPS_SWCT_01573] A PRPortPrototype is never considered unconnected
(cid:100) A PRPortPrototype is never considered unconnected, even if
there are no
SwConnectors actually referring to it.
(cid:99)(RS_SWCT_00010, RS_SWCT_03250,
RS_SWCT_03130)

Please note that [TPS_SWCT_01573] represents the immediate consequence of the
semantics deﬁned in [TPS_SWCT_01112].

[TPS_SWCT_01113] Connecting two PortPrototypes (cid:100) Two SwComponentPro
totypes are eventually connected by hooking up a PPortPrototype or PRPort
Prototype of one SwComponentPrototype to a compatible RPortPrototype or
PRPortPrototype of the other SwComponentPrototypes. Please ﬁnd more infor
mation concerning the deﬁnition of “compatibility” in section 6. (cid:99)(RS_SWCT_03130,
RS_SWCT_03250)

Class
Package
Note
Base

Attribute
requiredCo
mSpec

Class
Package
Note
Base

Attribute
providedC
omSpec

AbstractRequiredPortPrototype (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Components
This abstract class provides the ability to become a required PortPrototype.
ARObject,AtpBlueprintable,AtpFeature,AtpPrototype,Identiﬁable,Multilanguage
Referrable,PortPrototype,Referrable
Datatype
RPortComSpec

Mul. Kind Note

aggr Required communication attributes, one for each

*

interface element.

Table 3.3: AbstractRequiredPortPrototype

AbstractProvidedPortPrototype (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Components
This abstract class provides the ability to become a provided PortPrototype.
ARObject,AtpBlueprintable,AtpFeature,AtpPrototype,Identiﬁable,Multilanguage
Referrable,PortPrototype,Referrable
Datatype
PPortComSpec

Mul. Kind Note
aggr

*

Provided communication attributes per interface
element (data element or operation).

Table 3.4: AbstractProvidedPortPrototype



RPortPrototype
M2::AUTOSARTemplates::SWComponentTemplate::Components
Component port requiring a certain port interface.
ARObject,AbstractRequiredPortPrototype,AtpBlueprintable,AtpFeature,Atp
Prototype,Identiﬁable,MultilanguageReferrable,PortPrototype,Referrable
Datatype
PortInterface

Mul. Kind Note
tref

1

The interface that this port requires, i.e. the port
depends on another port providing the speciﬁed
interface.

Stereotypes: isOfType

Table 3.5: RPortPrototype

PPortPrototype
M2::AUTOSARTemplates::SWComponentTemplate::Components
Component port providing a certain port interface.
ARObject,AbstractProvidedPortPrototype,AtpBlueprintable,AtpFeature,Atp
Prototype,Identiﬁable,MultilanguageReferrable,PortPrototype,Referrable
Datatype
PortInterface

Mul. Kind Note
tref

The interface that this port provides.

1

Stereotypes: isOfType

Table 3.6: PPortPrototype

PRPortPrototype
M2::AUTOSARTemplates::SWComponentTemplate::Components
This kind of PortPrototype can take the role of both a required and a provided
PortPrototype.
ARObject,AbstractProvidedPortPrototype,AbstractRequiredPortPrototype,Atp
Blueprintable,AtpFeature,AtpPrototype,Identiﬁable,MultilanguageReferrable,Port
Prototype,Referrable
Datatype
PortInterface

Mul. Kind Note
tref

1

This represents the PortInterface used to type the
PRPortPrototype

Class
Package
Note
Base

Attribute
requiredInt
erface

Class
Package
Note
Base

Attribute
providedInt
erface

Class
Package
Note

Base

Attribute
providedR
equiredInte
rface

Stereotypes: isOfType

Table 3.7: PRPortPrototype



Figure 3.3: Components and Ports

[TPS_SWCT_01096] PortGroup (cid:100) PortPrototypes can be logically grouped into
PortGroups. This mechanism is used for implementing mode management features
and further explained in chapter 4.6. (cid:99)(RS_SWCT_03201)
#@SECTION: AtomicSwComponentType

[TPS_SWCT_01108] Added value of an AtomicSwComponentType (cid:100) As mentioned
before, the term AtomicSwComponentType is a speciﬁc form of the general concept
of the SwComponentType. The added value of an AtomicSwComponentType is that
it can aggregate an InternalBehavior (see chapter 7). (cid:99)(RS_SWCT_03040)

[TPS_SWCT_01109] Adding the SwcInternalBehavior in a later process step
(cid:100) The aggregation of SwcInternalBehavior is stereotyped (cid:28)atpSplitable(cid:29) to
allow for adding the SwcInternalBehavior in a later process step. In other words, it
is possible to completely develop the VFB view of a software-component and later add
more details like InternalBehavior. (cid:99)()




ARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypeRPortPrototypePPortPrototype«atpVariation» Tags:vh.latestBindingTime =preCompileTimeARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]PRPortPrototypeAbstractProvidedPortPrototypeAbstractRequiredPortPrototype+port0..*«atpVariation,atpSplitable»«isOfType»+providedInterface1{redefinesatpType}«isOfType»+requiredInterface1{redefinesatpType}«isOfType»+providedRequiredInterface1{redefinesatpType}

Class
Package
Note

Base

Attribute
internalBe
havior

AtomicSwComponentType (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Components
An atomic software component is atomic in the sense that it cannot be further
decomposed and distributed across multiple ECUs.
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,Identiﬁable,MultilanguageReferrable,Packageable
Element,Referrable,SwComponentType
Mul. Kind Note
Datatype
aggr
0..1
SwcInternalBeh
avior

The SwcInternalBehaviors owned by an
AtomicSwComponentType can be located in a
different physical ﬁle. Therefore the aggregation is
«atpSplitable».

symbolPro
ps

SymbolProps

0..1

aggr

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=internalBehavior, variation
Point.shortLabel
vh.latestBindingTime=preCompileTime
This represents the SymbolProps for the
AtomicSwComponentType.

Stereotypes: atpSplitable
Tags: atp.Splitkey=shortName

Table 3.8: AtomicSwComponentType

There are several specialized SwComponentTypes to describe speciﬁc software
components used in the different parts of the AUTOSAR Layered Architecture [6]. Fur
ther details are mentioned in chapter 10 and 11.

Figure 3.4: Overview of Component Types




ARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtomicSwComponentTypeCompositionSwComponentTypeAtpPrototypeSwComponentPrototypeSensorActuatorSwComponentTypeParameterSwComponentTypeApplicationSwComponentTypeEcuAbstractionSwComponentTypeComplexDeviceDriverSwComponentTypeNvBlockSwComponentTypeServiceProxySwComponentTypeServiceSwComponentType«atpVariation» Tags:vh.latestBindingTime =postBuild+component0..*«atpVariation,atpSplitable»«isOfType»+type1{redefinesatpType}

The ApplicationSwComponentType is a specialization of AtomicSwComponent
Type for representing hardware-independent application software. The Parameter
SwComponentType is a specialization of SwComponentType that can - in contrast to
AtomicSwComponentType - not aggregate SwcInternalBehavior.

the NvBlockSwComponentType is described in detail

in sec
The purpose of
tion 11.5.2. The ServiceSwComponentType is described in section 11.3. Further on,
the EcuAbstractionSwComponentType and the ComplexDeviceDriverSwCom
ponentType are discussed in detail in section 10.

A description of the ServiceProxySwComponentType can be found in section 11.4
while the SensorActuatorSwComponentType is described in section 10.4.

Class
Package
Note

ApplicationSwComponentType
M2::AUTOSARTemplates::SWComponentTemplate::Components
The ApplicationSwComponentType is used to represent the application software.

Base

Attribute
–

Tags: atp.recommendedPackage=SwComponentTypes
ARElement,ARObject,AtomicSwComponentType,AtpBlueprint,AtpBlueprintable,Atp
Classiﬁer,AtpType,CollectableElement,Identiﬁable,Multilanguage
Referrable,PackageableElement,Referrable,SwComponentType
Datatype
–

Mul. Kind Note
–

–

–

Table 3.9: ApplicationSwComponentType
#@SECTION: 3.2.4 ParameterSwComponentType

[constr_1092] ParameterSwComponentType (cid:100) A ParameterSwComponentType
shall never aggregate a SwcInternalBehavior and also owns exclusively PPort
Prototypes of type ParameterInterface. (cid:99)()

However, a ParameterSwComponentType shall have the ability to aggregate In
stantiationDataDefProps. By this means it is possible to deﬁne role-speciﬁc
data properties of elements of composite data types used for the deﬁnition of calibra
tion parameters in the scope of a ParameterSwComponentType.

For more information about this aspect please refer to section 7.5.4.



Figure 3.5: Details of ParameterSwComponentType
#@SECTION: 3.2.5 Symbolic Name of a Software-Component

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

Class
Package
Note

Base
Attribute
–

SymbolProps
M2::AUTOSARTemplates::SWComponentTemplate::Components
This meta-class represents the ability to attach with the symbol attribute a symbolic
name that is conform to C language requirements to another meta-class, e.g.
AtomicSwComponentType, that is a potential subject to a name clash on the level of
RTE source code.
ARObject,ImplementationProps,Referrable
Datatype
–

Mul. Kind Note
–

–

–

Table 3.10: SymbolProps

For more detailed information about how SymbolProps can be used to mitigate name
clashes occurring during the integration of software-components on an AUTOSAR
ECU, please refer to [4].

[TPS_SWCT_01000] Usage of attribute symbol of the symbolProps (cid:100) In par
the attribute symbol of
ticular,
the symbolProps owned by a given AtomicSwComponentType.
If and only if
symbolProps is not deﬁned the RTE generator shall take the shortName of the

the RTE generator shall

take over the value of




SwComponentTypeParameterSwComponentTypeInstantiationDataDefPropsARElementConstantSpecificationMappingSetARElementAtpBlueprintAtpBlueprintableDataTypeMappingSet«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpSplitable»+dataTypeMapping0..*«atpVariation»+instantiationDataDefProps0..*«atpSplitable»+constantMapping0..*

AtomicSwComponentType. For the generation of symbols for RunnableEntitys
[TPS_SWCT_01001] shall be observed. (cid:99)()

[TPS_SWCT_01001] Preﬁx symbols generated for the RunnableEntity (cid:100) If and
only if the attribute symbol of a symbolProps owned by an AtomicSwComponent
Type exists, its value shall also be taken for preﬁxing the symbols generated for the
RunnableEntitys owned by the AtomicSwComponentType. (cid:99)()

Note: if symbolProps is not deﬁned the behavior of the RTE generator is fully back
wards compatible, i.e. existing implementations of RunnableEntitys do not have to
be touched in order to conform with this version of the AUTOSAR standard.

This is a further measure to mitigate the risk of potential name clashes in the RTE
code.

[TPS_SWCT_01635] Naming conventions may support the effectiveness of Sym
bolProps (cid:100) Of course, there is a residual risk that even in the presence of Symbol
Props name clashes may occur. Therefore, the deﬁnition of naming conventions may
facilitate the avoidance of name clashes to the further degree.

However, these naming conventions can (with the support of the meta-model, e.g. by
utilizing SymbolProps or shortNamePattern) still only be deﬁned on the model
level. (cid:99)(RS_SWCT_00230)

Figure 3.6: Overview of AtomicSwComponentType




SwComponentTypeAtomicSwComponentTypeSymbolPropsSensorActuatorSwComponentTypeApplicationSwComponentTypeEcuAbstractionSwComponentTypeComplexDeviceDriverSwComponentTypeNvBlockSwComponentTypeServiceProxySwComponentTypeServiceSwComponentTypeReferrableImplementationProps+ symbol  :CIdentifier«atpSplitable»+symbolProps0..1

#@SECTION: 3.3 Composition
#@SECTION: 3.3.1 Overview

[TPS_SWCT_01032] CompositionSwComponentType (cid:100) The purpose of an
AUTOSAR CompositionSwComponentType is to allow the encapsulation of spe
ciﬁc functionality by aggregating existing software-components. (cid:99)(RS_SWCT_00190,
RS_SWCT_02000, RS_SWCT_02020, RS_SWCT_03000)

[TPS_SWCT_01033] Nested deﬁnition of CompositionSwComponentTypes (cid:100)
Since a CompositionSwComponentType is also a SwComponentType, it again may
be aggregated in further CompositionSwComponentTypes. (cid:99)(RS_SWCT_00190,
RS_SWCT_02000, RS_SWCT_02020, RS_SWCT_03000)

This recursive relation is formally expressed in Figure 3.7.

It is important to understand that while compositions allow for (sub-) system abstrac
tion, they are solely an architectural element for the implementation of model scalabil
ity. They simply group existing software-components and thereby take away complexity
when viewing or designing logical software architecture.

Figure 3.7: The recursive relation of software-components and compositions

Therefore, the deﬁnition of CompositionSwComponentTypes has no effect on how
software-components interact with the Virtual Functional Bus (VFB). Composition
SwComponentTypes do not add any new functionality to what is already provided by
the software-components they aggregate.

[TPS_SWCT_01034] CompositionSwComponentTypes do not have any bi
nary footprint (cid:100) As the main consequence, CompositionSwComponentTypes
(cid:99)(RS_SWCT_00190,
do not have any binary footprint
RS_SWCT_02000, RS_SWCT_02020, RS_SWCT_03000)

in the ECU software.




ARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpPrototypeSwComponentPrototype«atpVariation» Tags:vh.latestBindingTime = postBuildCompositionSwComponentType+component0..*«atpVariation,atpSplitable»*«isOfType»+type1{redefinesatpType}
#@SECTION: 3.3.2 SwComponentPrototype

[TPS_SWCT_01035] CompositionSwComponentType aggregates SwCompo
nentPrototypes (cid:100) In terms of the AUTOSAR meta-model, a composition of software
components realized by the meta-class CompositionSwComponentType aggre
gates SwComponentPrototypes which in turn are typed by a SwComponentType.
(cid:99)(RS_SWCT_00190, RS_SWCT_02000, RS_SWCT_02020, RS_SWCT_03000)

Please note that a CompositionSwComponentType is also a SwComponentType.

CompositionSwComponentType
M2::AUTOSARTemplates::SWComponentTemplate::Composition
A CompositionSwComponentType aggregates SwComponentPrototypes (that in turn
are typed by SwComponentTypes) as well as SwConnectors for primarily connecting
SwComponentPrototypes among each others and towards the surface of the
CompositionSwComponentType. By this means hierarchical structures of
software-components can be created.

Tags: atp.recommendedPackage=SwComponentTypes
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,Identiﬁable,MultilanguageReferrable,Packageable
Element,Referrable,SwComponentType
Mul. Kind Note
Datatype
aggr

*

Attribute
component SwComponentP

rototype

Class
Package
Note

Base

The instantiated components that are part of this
composition. The aggregation of
SwComponentPrototype is subject to variability
with the purpose to support the conditional
existence of a SwComponentPrototype. Please be
aware: if the conditional existence of
SwComponentPrototypes is resolved post-build
the deselected SwComponentPrototypes are still
contained in the ECUs build but the instances are
inactive in in that they are not scheduled by the
RTE.

The aggregation is marked as atpSplitable in order
to allow the addition of service components to the
ECU extract during the ECU integration.

The use case for having 0 components owned by
the CompositionSwComponentType could be to
deliver an empty CompositionSwComponentType
to e.g. a supplier for ﬁlling the internal structure.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=postBuild



Attribute
connector

Datatype
SwConnector

Mul. Kind Note
aggr

*

SwConnectors have the principal ability to
establish a connection among PortPrototypes.
They can have many roles in the context of a
CompositionSwComponentType. Details are
reﬁned by subclasses.

constantVa
lueMappin
g

ConstantSpecifi
cationMappingS
et

dataTypeM
apping

DataTypeMappi
ngSet

*

*

ref

ref

The aggregation of SwConnectors is subject to
variability with the purpose to support variant data
ﬂow.

The aggregation is marked as atpSplitable in order
to allow the extension of the ECU extract with
AssemblySwConnectors between
ApplicationSwComponentTypes and
ServiceSwComponentTypes during the ECU
integration.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=postBuild
Reference to the ConstantSpeciﬁcationMapping to
be applied for initValues of PPortComSpecs and
RPortComSpec.

Stereotypes: atpSplitable
Tags: atp.Splitkey=constantValueMapping
Reference to the DataTypeMapping to be applied
for the used ApplicationDataTypes in
PortInterfaces.

Background: when developing subsystems it may
happen that ApplicationDataTypes are used on
the surface of CompositionSwComponentTypes.
In this case it would be reasonable to be able to
also provide the intended mapping to the
ImplementationDataTypes. However, this mapping
shall be informal and not technically binding for
the implementers mainly because the RTE
generator is not concerned about the
CompositionSwComponentTypes.

Rationale: if the mapping of ApplicationDataTypes
on the delegated and inner PortPrototype matches
then the mapping to ImplementationDataTypes is
not impacting compatibility.

Stereotypes: atpSplitable
Tags: atp.Splitkey=dataTypeMapping



Attribute
instantiatio
nRTEEven
tProps

Datatype
InstantiationRT
EEventProps

Mul. Kind Note
aggr

*

This allows to deﬁne instantiation speciﬁc
properties for RTE Events, in particular for
instance speciﬁc scheduling.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortLabel, variation
Point.shortLabel
vh.latestBindingTime=codeGenerationTime

Table 3.11: CompositionSwComponentType

Class
Package
Note
Base
Attribute
type

SwComponentPrototype
M2::AUTOSARTemplates::SWComponentTemplate::Composition
Role of a software component within a composition.
ARObject,AtpFeature,AtpPrototype,Identiﬁable,MultilanguageReferrable,Referrable
Datatype
SwComponentT
ype

Mul. Kind Note
tref

Type of the instance.

1

Stereotypes: isOfType

Table 3.12: SwComponentPrototype



Figure 3.8: Composition and the meta-classes aggregated

[TPS_SWCT_01036] SwComponentPrototype implements a speciﬁc role (cid:100)
Therefore, a SwComponentPrototype implements the usage of a SwComponent
Type in a speciﬁc role. (cid:99)(RS_SWCT_00190, RS_SWCT_02000, RS_SWCT_02020,
RS_SWCT_03000)

[TPS_SWCT_01037] arbitrary numbers of SwComponentPrototypes can be cre
ated (cid:100) In general, arbitrary numbers of SwComponentPrototypes that refer to spe
ciﬁc SwComponentTypes can be created. (cid:99)(RS_SWCT_00190, RS_SWCT_02000,
RS_SWCT_02020, RS_SWCT_03000)

Example: a SwComponentPrototype “LeftDoorControl” fulﬁlls the role of implement
ing the SwComponentType “DoorControl” for the left door of a vehicle while the
SwComponentPrototype “RightDoorControl” fulﬁlls the role of the SwComponent
Type “DoorControl” for the right door.

[TPS_SWCT_01080] Delegation ports (cid:100) Note that being a SwComponentType,
a CompositionSwComponentType also exposes PortPrototypes to the out




ARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypeCompositionSwComponentTypeAtpStructureElementSwConnectorAtpPrototypeSwComponentPrototype«atpVariation» Tags:vh.latestBindingTime = postBuild«atpVariation» Tags:vh.latestBindingTime = postBuild«atpVariation» Tags:vh.latestBindingTime = preCompileTimeAtpStructureElementIdentifiablePortGroup«atpVariation» Tags:vh.latestBindingTime = preCompileTime«atpVariation» Tags:vh.latestBindingTime = codeGenerationTimeInstantiationRTEEventProps+ shortLabel  :Identifier«atpVariation»+portGroup0..*+port0..*«atpVariation,atpSplitable»+connector*«atpVariation,atpSplitable»«atpVariation,atpSplitable»+instantiationRTEEventProps0..*+component0..*«atpVariation,atpSplitable»

However,

the PortPrototypes are only delegated and do not
side world.
play the same role as PortPrototypes attached to AtomicSwComponentTypes.
(cid:99)(RS_SWCT_03130)

[TPS_SWCT_01081] Implications of being a delegation port (cid:100) Being a PortPro
totype attached to a CompositionSwComponentType has the following implica
tions:

• The delegation has to follow the rules deﬁned in chapter 6.

• By creating PortPrototypes on the surface of a speciﬁc Composition
SwComponentType it is explicitly decided whether or not the contents of an “in
ner” port contained in the CompositionSwComponentType is exposed to the
outside world.

(cid:99)(RS_SWCT_03130)

Please note that the semantics of the delegation of PortPrototypes are similar to en
capsulation mechanisms like public and private members in object-oriented program
ming languages.

One implication of the concept of CompositionSwComponentType is that the appli
cation software of an entire vehicle eventually is represented by one Composition
SwComponentType. This so-called top-level composition has a special role in the
context of the AUTOSAR System Template [11].

However, please note that a top-level composition might have (unconnected) Port
Prototypes in order to allow for reuse as part of another system.

[constr_1035] Recursive deﬁnition of CompositionSwComponentType (cid:100) The re
cursive deﬁnition of a CompositionSwComponentType that eventually contains
a SwComponentPrototype typed by the same CompositionSwComponentType
shall not be feasible. (cid:99)()
#@SECTION: 3.3.3 Connectors

[TPS_SWCT_01079] SwConnector (cid:100) Note that CompositionSwComponent
Type also aggregates the abstract meta-class SwConnector for connecting
the SwComponentPrototypes contained among each other
(see Figure 3.8).
(cid:99)(RS_SWCT_03130)

CompositionSwComponentTypes contain two kinds of SwConnectors:

• [TPS_SWCT_01082] AssemblySwConnector (cid:100) AssemblySwConnectors in
terconnect PortPrototypes of SwComponentPrototypes that are part of the
CompositionSwComponentType. (cid:99)(RS_SWCT_03130)

• [TPS_SWCT_01083] DelegationSwConnector (cid:100) DelegationSwConnec
tors connect from “inner” PortPrototypes to delegated “outer” PortProto
types. (cid:99)(RS_SWCT_03130)



[constr_1032] DelegationSwConnector can only connect PortProto
types of the same kind (cid:100) A DelegationSwConnector can only connect
PortPrototypes of the same kind, i.e. PPortPrototype to PPortProto
type and RPortPrototype to RPortPrototype. (cid:99)()

[TPS_SWCT_01084] Outer PortPrototype is referenced by multiple Del
egationSwConnectors (cid:100) In the case that an outer PortPrototype is ref
erenced by multiple DelegationSwConnectors the semantic is the multi
plication of the AssemblySwConnectors referencing the outer PortProto
types.(cid:99)(RS_SWCT_03130)

[constr_1086] SwConnector between two speciﬁc PortPrototypes (cid:100) Each pair
of PortPrototypes can only be connected by one and only one SwConnector. (cid:99)()

In other words, it is not supported to create two different SwConnectors that connect
the same pair of PortPrototypes.

[TPS_SWCT_01638] Existence of SwConnector between two PRPortProto
types (cid:100) [constr_1086] applies also in the case that two PRPortPrototypes are con
nected with each other. In particular, the roles

• AssemblySwConnector.requester

• AssemblySwConnector.provider

• PassThroughSwConnector.providedOuterPort

• PassThroughSwConnector.requiredOuterPort

do not establish a direction in this case. (cid:99)()

For clariﬁcation, [TPS_SWCT_01638] means that the SwConnector represents the
ability for bi-directional communication between the two PRPortPrototypes.

[constr_1087] AssemblySwConnector inside CompositionSwComponentType (cid:100)
An AssemblySwConnector can only connect PortPrototypes of SwComponent
Prototypes that are owned by the same CompositionSwComponentType (cid:99)()

[constr_1088] DelegationSwConnector inside CompositionSwComponent
Type (cid:100) A DelegationSwConnector can only connect a PortPrototype of a
SwComponentPrototype that is owned by the same CompositionSwComponent
Type that also owns the connected delegation PortPrototype. (cid:99)()

In the context of attaching a DelegationSwConnector to an inner PRPortProto
type there is some ambiguity to be considered. In particular, from the formal point of
view it would be feasible to use either a PPortInCompositionInstanceRef or a
RPortInCompositionInstanceRef.

The ability to use one or the other meta-class arbitrarily is considered confusing. There
fore, [TPS_SWCT_01515] has been deﬁned to remove the unnecessary degree of
freedom.



[TPS_SWCT_01515] PPortInCompositionInstanceRef shall be used for at
taching DelegationSwConnector to an inner PRPortPrototype (cid:100) For the im
plementation of the attachment of a DelegationSwConnector to an inner PRPort
Prototype the meta-class PPortInCompositionInstanceRef shall be used. (cid:99)()

[constr_1100] Unconnected RPortPrototype typed by a DataInterface (cid:100) For
any element in an unconnected RPortPrototype typed by a DataInterface there
shall be a requiredComSpec that deﬁnes an initValue. (cid:99)()

Class
Package
Note

Base

Attribute
mapping

Class
Package
Note

Base

Attribute
provider

requester

SwConnector (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Composition
The base class for connectors between ports. Connectors have to be identiﬁable to
allow references from the system constraint template.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
PortInterfaceMa
pping

Mul. Kind Note
ref
0..1

Reference to a PortInterfaceMapping specifying
the mapping of unequal named PortInterface
elements of the two different PortInterfaces typing
the two PortPrototypes which are referenced by
the ConnectorPrototype.

Table 3.13: SwConnector

AssemblySwConnector
M2::AUTOSARTemplates::SWComponentTemplate::Composition
AssemblySwConnectors are exclusively used to connect SwComponentPrototypes in
the context of a CompositionSwComponentType.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable,SwConnector
Datatype
AbstractProvide
dPortPrototype
AbstractRequire
dPortPrototype

Mul. Kind Note
iref
0..1

Instance of providing port.

Instance of requiring port.

0..1

iref

Table 3.14: AssemblySwConnector

Class
Package
Note

Base

Attribute

DelegationSwConnector
M2::AUTOSARTemplates::SWComponentTemplate::Composition
A delegation connector delegates one inner PortPrototype (a port of a component
that is used inside the composition) to a outer PortPrototype of compatible type that
belongs directly to the composition (a port that is owned by the composition).
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable,SwConnector
Datatype

Mul. Kind Note



Attribute
innerPort

Datatype
PortPrototype

Mul. Kind Note
iref

1

The port that belongs to the ComponentPrototype
in the composition

outerPort

PortPrototype

1

ref

Tags: xml.typeElement=true
The port that is located on the outside of the
CompositionType

Table 3.15: DelegationSwConnector

One speciﬁc use case for the application of SwConnectors is exempliﬁed by the ﬁg
ures 3.9 and 3.11. A speciﬁc CompositionSwComponentType exists in two variants
where one (more complex) variant foresees the existence of a SwComponentPro
totype inside the CompositionSwComponentType (depicted by 3.9) and the other
(because it is implementing a simpler semantics) does not need the SwComponent
Prototype.

Figure 3.9: Use case for PassThroughSwConnector (I)

Class
Package
Note

Base

Attribute
providedO
uterPort
requiredOu
terPort

PassThroughSwConnector
M2::AUTOSARTemplates::SWComponentTemplate::Composition
This kind of SwConnector can be used inside a CompositionSwComponentType to
connect two delegation PortPrototypes.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable,SwConnector
Datatype
AbstractProvide
dPortPrototype
AbstractRequire
dPortPrototype

This represents the provided outer delegation
PortPrototype of the PassThroughSwConnector.
This represents the required outer delegation
PortPrototype of the PassThroughSwConnector.

Mul. Kind Note
ref

ref

1

1

Table 3.16: PassThroughSwConnector




TriggerRunA1Application SW ComponentRTOComposition SW Component

Figure 3.10: Connectors

Without the ability to deﬁne a PassThroughSwConnector the second variant could
only be implemented by deﬁning a dummy SwComponentPrototype inside the
CompositionSwComponentType. However, the dummy SwComponentPrototype
would need to deﬁne RunnableEntitys that are created for the sole purpose of being
able to shovel the data from (e.g. for sender-receiver communication) RPortProto
types to PPortPrototypes.

This would not only be cumbersome it would also obviously require additional re
sources (memory and code) at run-time. Plus, the existence of addition RunnableEn
titys also unnecessarily increases the propagation delay of information ﬂowing
around inside the ECU.

Figure 3.11: Use case for PassThroughSwConnector (II)




AtpStructureElementSwConnectorAssemblySwConnectorDelegationSwConnectorAtpBlueprintableAtpPrototypePortPrototypeAbstractProvidedPortPrototypeAbstractRequiredPortPrototypePassThroughSwConnector+requiredOuterPort1+providedOuterPort1«instanceRef»+provider0..1«instanceRef»+requester0..1+outerPort1«instanceRef»+innerPort1Application SW ComponentComposition SW ComponentPortInterfaceMapping

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

[TPS_SWCT_02507] Instantiation-speciﬁc RTEEvents (cid:100) It is possible to specify
instantiation speciﬁc properties of an RTEEvent by applying InstantiationR
TEEventProps in the role instantiationRteEventProps.

This allows to use the same ApplicationSwComponentType in different timing sce
narios. Even if the scheduling is an issue of the SwcInternalBehavior, the instance
speciﬁc deﬁnition of timing needs to be speciﬁed on the level of a Composition
SwComponentType. (cid:99)(RS_SWCT_03046, RS_SWCT_03270)

As an example for [TPS_SWCT_02507], please consider a software-component that
implements a closed-loop control algorithm.

This software-component can potentially be deployed to “slow” and “fast” control sce
narios. As the actual time-base of the control algorithm is derived from the scheduling
implemented in the RTE it obviously facilitates the overall design if the timing can be
deﬁned on “instance” level.



Figure 3.12: Instantiation speciﬁc Properties of RTEEvents

Class
Package
Note

Base
Attribute
refinedEve
nt

InstantiationRTEEventProps (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::Composition
This meta class represents the ability to reﬁne the properties of RTEEvents for
particular instances of a software component.
ARObject
Datatype
RTEEvent

Mul. Kind Note
iref

1

shortLabel

Identifier

1

ref

This instance ref denotes the Timing Event for
which the period shall be reﬁned on an instance
level.
The main purpose of the shortLabel is to
contribute to the splitkey of aggregations that are
«atpSplitable».

Table 3.17: InstantiationRTEEventProps




AbstractEventAtpStructureElementRTEEventInternalBehaviorSwcInternalBehavior+ handleTerminationAndRestart  :HandleTerminationAndRestartEnum+ supportsMultipleInstantiation  :BooleanIdentifiableWaitPoint+ timeout  :TimeValueAtpStructureElementExecutableEntityRunnableEntity+ canBeInvokedConcurrently  :Boolean+ symbol  :CIdentifier«atpVariation» Tags:vh.latestBindingTime =preCompileTimeARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtomicSwComponentTypeInstantiationTimingEventProps+ period  :TimeValueTimingEvent+ period  :TimeValueCompositionSwComponentTypeInstantiationRTEEventProps+ shortLabel  :Identifier«atpVariation» Tags:vh.latestBindingTime =codeGenerationTime«instanceRef»+refinedEvent1«atpVariation,atpSplitable»+instantiationRTEEventProps0..*+event*«atpVariation,atpSplitable»+startOnEvent0..1+trigger1+waitPoint*+runnable1..*«atpVariation,atpSplitable»«atpVariation,atpSplitable»+internalBehavior0..1

InstantiationTimingEventProps

[constr_1233]
reference
TimingEvent (cid:100) An InstantiationTimingEventProps shall only reference
TimingEvent in the role refinedEvent. A reference to other kinds of RTEEvents
is not supported. (cid:99)()

shall

only
#@SECTION: 3.4 Port Interface

[TPS_SWCT_01025] The role of PortPrototypes in the AUTOSAR architecture
(cid:100) A PortPrototype mainly contributes the functionality of being a connection point
to the AUTOSAR concept.

The details, i.e. with respect to what kind of information is actually transported between
two PortPrototypes is deﬁned by the PortInterface.
(cid:99)(RS_SWCT_00010,
RS_SWCT_00080, RS_SWCT_00110, RS_SWCT_02030, RS_SWCT_03010)

[TPS_SWCT_01026] The role of PortInterfaces in the AUTOSAR architecture
(cid:100) PortInterfaces (see Figure 3.14) are used to support a design-by-contract work
ﬂow, i.e. a PortInterface provides means to formally verify structural and dynamic
compatibility between software-components. (cid:99)(RS_SWCT_00010, RS_SWCT_00080,
RS_SWCT_00110, RS_SWCT_02030, RS_SWCT_03010)

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
Please note that the conceptual relationship of SenderReceiverInterface, Nv
DataInterface, and ParameterInterface is expressed by the deﬁnition of
the abstract base class DataInterface. (cid:99)(RS_SWCT_00010, RS_SWCT_00080,
RS_SWCT_00110, RS_SWCT_03010)



Figure 3.13: DataInterface as an abstract base class

Please ﬁnd more details about the specialization of the PortInterface concept in
chapter 4.2.3 and 4.2.2.

Class
Package
Note

Base

Attribute
isService

PortInterface (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::PortInterface
Abstract base class for an interface that is either provided or required by a port of a
software component.
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,Identiﬁable,MultilanguageReferrable,Packageable
Element,Referrable
Datatype
Boolean

Mul. Kind Note
attr

1

This ﬂag is set if the PortInterface is to be used for
communication between an

• ApplicationSwComponentType or

• ServiceProxySwComponentType or

• SensorActuatorSwComponentType or

• ComplexDeviceDriverSwComponentType

• ServiceSwComponentType

• EcuAbstractionSwComponentType

serviceKin
d

ServiceProvider
Enum

0..1

attr

and a ServiceSwComponentType (namely an
AUTOSAR Service) located on the same ECU.
Otherwise the ﬂag is not set.
This attribute provides further details about the
nature of the applied service.

Table 3.18: PortInterface




SenderReceiverInterfaceNvDataInterfaceParameterInterfaceDataInterfaceARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]

Class
Package
Note

Base

Attribute
–

DataInterface (abstract)
M2::AUTOSARTemplates::SWComponentTemplate::PortInterface
The purpose of this meta-class is to act as an abstract base class for subclasses that
share the semantics of being concerned about data (as opposed to e.g. operations).
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,Identiﬁable,MultilanguageReferrable,Packageable
Element,PortInterface,Referrable
Datatype
–

Mul. Kind Note
–

–

–

Table 3.19: DataInterface

[TPS_SWCT_01070] PortInterface acts as a type for a PortPrototype (cid:100) From
an abstract point of view, a PortInterface acts as a type for a PortProto
type. This means in particular that several PortPrototypes can be typed by the
same PortInterface. (cid:99)(RS_SWCT_00010, RS_SWCT_00080, RS_SWCT_00110,
RS_SWCT_03010)

Of course, this aspect facilitates the creation of valid connections between software
components dramatically. By using a speciﬁc PortInterface for typing particular
PortPrototypes the latter are eligible for being connected to each other by deﬁnition.



Figure 3.14: PortInterfaces in the AUTOSAR meta-model

However, the creation of a valid connection does not need to be based on the usage of
identical PortInterfaces. It is also possible to use different, but compatible Port
Interfaces. The details about compatibility of PortInterfaces are described in
chapter 6.

[constr_1036] Connect kinds of PortInterfaces (cid:100) It shall not be possible to con
nect PortPrototypes typed by PortInterfaces of different kinds. Subclasses of
DataInterface make an exception from this rule and can be used for creating con
nections to each other. (cid:99)()

For clariﬁcation, a connection between a PortPrototype typed by a Sender
ReceiverInterface and a PortPrototype typed by a ClientServerInter
face shall not be possible. However, the creation of a connection between a Port
Prototype typed by a SenderReceiverInterface and a PortPrototype typed
by a ParameterInterface is supported.




SenderReceiverInterfaceClientServerInterfaceAutosarDataPrototypeVariableDataPrototypeAtpStructureElementIdentifiableClientServerOperationAutosarDataPrototypeArgumentDataPrototypeAtpPrototypeModeDeclarationGroupPrototypeParameterInterfaceAutosarDataPrototypeParameterDataPrototypeARElementAtpBlueprintAtpBlueprintableAtpTypePortInterfaceTriggerInterfaceAtpStructureElementIdentifiableTriggerModeSwitchInterfaceNvDataInterfaceDataInterface«atpVariation» Tags:vh.latestBindingTime =blueprintDerivationTime+dataElement1..*+nvData1..*+trigger1..*+operation1..*«atpVariation»+modeGroup1+argument*{ordered}«atpVariation»+parameter1..*

[constr_1137] Applicability of ParameterInterface (cid:100) A PPortPrototype typed
by a ParameterInterface can only be owned by a ParameterSwComponent
Type. (cid:99)()

Please note that PortInterfaces also play an important role in the context of deﬁn
ing so-called AUTOSAR services. In particular, by means of the attribute isService
a PortInterface can deﬁne whether or not it is supposed to be used in the context
of an AUTOSAR service and in addition to this it may deﬁne (by means of the attribute
serviceKind) what kind of service is intended.

Figure 3.15: PortInterfaces and AUTOSAR services

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
between the value of serviceKind and the actual implementation of the PortIn
terface the implementation of the PortInterface wins over the value of attribute
PortInterface.serviceKind (which, for the intended purpose shall be considered
an annotation rather than a semantically binding information). (cid:99)()

[TPS_SWCT_01004] Default value if serviceKind is not deﬁned (cid:100) if the attribute
serviceKind is not deﬁned in the context of a speciﬁc PortInterface the default
value anyStandardized shall be assumed. (cid:99)()

[constr_1174] PortInterfaces used in the context of CompositionSwCompo
nentTypes cannot refer to AUTOSAR services (cid:100) CompositionSwComponent
Types shall not own PortPrototypes typed by PortInterfaces where the at
tribute isService is set to true. (cid:99)()




ARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]«enumeration»ServiceProviderEnum basicSoftwareModeManager comManager cryptoServiceManager diagnosticCommunicationManager diagnosticEventManager diagnosticLogAndTrace ecuManager functionInhibitionManager nonVolatileRamManager syncBaseTimeManager watchDogManager anyStandardized vendorSpecific developmentErrorTracer operatingSystem

Enumeration ServiceProviderEnum
Package
Note
Literal
anyStandard
ized

M2::AUTOSARTemplates::CommonStructure::ServiceNeeds
This represents a list of possible service providers
Description
This value means that the speciﬁc nature is either unknown or it is not important for
the given purpose. This is also the default value for any attribute of type
ServiceProviderEnum
The service relates to the Basic Software Mode Manager (BswM)

basicSoft
wareMode
Manager
comManager
cryptoService
Manager
development
ErrorTracer
diagnostic
Communica
tionManager
diagnostic
EventMan
ager
diagnostic
LogAndTrace
ecuManager
function
Inhibition
Manager
nonVolatile
RamManager
operating
System
syncBase
TimeMan
ager
vendorSpe
ciﬁc
watchDog
Manager

The service relates to the COM Manager (ComM).
The service relates to the Crypto Service Manager (CsM).

The service relates to the Development Error Tracer (DET).

The service relates to the Diagnostic Communication Manager (DCM).

The service relates to the Diagnostic Event Manager (DEM).

The service relates to the Diagnostic Log and Trace (DLT).

The service relates to the ECU Manager (EcuM).
The service relates to the Function Inhibition Manager (FIM).

The service relates to the Non-Volatile RAM Manager (NvM).

The service relates to the Operating System (OS).

The service relates to the Sync Time Base Manager (StbM).

This value denotes a vendor-speciﬁc service.

The service relates to the Watchdog Manager (WdgM).

Table 3.20: ServiceProviderEnum

[TPS_SWCT_01005] Usage of SwcServiceDependencys for vendor-speciﬁc ser
vices (cid:100) SwcServiceDependencys can also be used for vendor-speciﬁc services.
In this case the SwcServiceDependency shall not contain any of the standardized
ServiceNeeds. (cid:99)()

Please ﬁnd more details about the relation of PortInterfaces to AUTOSAR services
in chapter 11.