4 Details: Software Components, Ports, and

Interfaces

4.1 Introduction

The speciﬁcation of the Virtual Functional Bus (VFB) [3] explains the main commu
nication paradigms for communication among software-components: client/server for
operation-based communication, and sender/receiver for data-based communication.

The nature of the two communication paradigms is quite different, and so is the mod
eling of SenderReceiverInterfaces and ClientServerInterfaces and their
related meta-classes.

[TPS_SWCT_01516] PortInterface describes the static structure of informa
tion interchange (cid:100) PortInterfaces are limited to the description of the static struc
ture of the exchanged information; the dynamic attributes (please refer to chapter 4.5)
relevant for communication are attached to PortPrototypes. (cid:99)(RS_SWCT_00010,
RS_SWCT_00080, RS_SWCT_00110, RS_SWCT_02030, RS_SWCT_03010)

4.2 Port Interface Details

4.2.1 Introduction

The usage of value encodings (for more information please refer to section 5.2.6) is
limited within the context of PortInterfaces.

[constr_1045] Supported value encodings for SwBaseType in the context of
PortInterfaces (cid:100) The supported value encodings for the usage within a Port
Interface are:

• 2C: Two’s complement

• IEEE754: ﬂoating point numbers

• ISO-8859-1: ASCII-Strings

• ISO-8859-2: ASCII-Strings

• WINDOWS-1252: ASCII-Strings

• UTF-8: UCS Transformation Format 8

• UTF-16: Character encoding for Unicode code points based on 16 bit code

units [16]

• UCS-2: Universal Character Set 2

• NONE: Unsigned Integer

88 of 905

Document ID 062: AUTOSAR_TPS_SoftwareComponentTemplate

— AUTOSAR CONFIDENTIAL —

Software Component Template
AUTOSAR Release 4.2.2

• BOOLEAN: This represents an integer to be interpreted as boolean.

(cid:99)()

[constr_1046] Applicability of [constr_1045] (cid:100) [constr_1045] applies only if the
value of the attribute isService is set to false. (cid:99)()

[constr_1295] PortInterfaces and category DATA_REFERENCE (cid:100) A DataPro
totype deﬁned in the context of a PortInterface used by an Application
SwComponentType or SensorActuatorSwComponentType that is (after potential
indirections via TYPE_REFERENCE are resolved) either typed by or mapped to an Im
plementationDataType of category DATA_REFERENCE shall only be used if ei
ther the provider or the requester of the information represents a ServiceSwCompo
nentType, a ComplexDeviceDriverSwComponentType, a ParameterSwCom
ponentType, or an NvBlockSwComponentType, or the EcuAbstractionSwCom
ponentType. (cid:99)()

Note: [constr_1295] corresponds to [SWS_RTE_07670].

4.2.2 Sender Receiver Communication

[TPS_SWCT_01114] SenderReceiverInterface (cid:100) SenderReceiverInter
faces allow for the speciﬁcation of the typically asynchronous communication pattern
where a sender provides data that is required by one or more receivers.

While the actual communication takes place via the respective PortPrototypes, a
SenderReceiverInterface allows for formally describing what kind of information
is sent and received. (cid:99)()

Class
Package
Note

SenderReceiverInterface
M2::AUTOSARTemplates::SWComponentTemplate::PortInterface
A sender/receiver interface declares a number of data elements to be sent and
received.

Base

Attribute
dataEleme
nt
invalidation
Policy

Tags: atp.recommendedPackage=PortInterfaces
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,DataInterface,Identiﬁable,Multilanguage
Referrable,PackageableElement,PortInterface,Referrable
Datatype
VariableDataPr
ototype
InvalidationPolic
y
