#@SECTION: 8 Implementation

Previous versions of this document contained a comprehensive description of the
meta-class Implementation. This meta-class still exists but the description of most
of its content has been moved to another document, in particular the speciﬁcation of
the Basic Software Module Description Template [7].

Please note that the Software Component Template and the Basic Software
Module Description Template share the content of Implementation. How
ever, the semantics of Implementation is closer to the Basic Software Module
Description Template.

Nevertheless, there is still content strictly related to the Software Component Tem
plate. This part of Implementation consisting of SwcImplementation (see Fig
ure 8.1) remains in this document.

Figure 8.1: Implementation part speciﬁc to the Software Component Template




ARElementImplementation+ programmingLanguage  :ProgramminglanguageEnum+ swVersion  :RevisionLabelString+ usedCodeGenerator  :String [0..1]+ vendorId  :PositiveIntegerSwcImplementation+ requiredRTEVendor  :String [0..1]InternalBehaviorSwcInternalBehaviorPerInstanceMemorySize+ alignment  :PositiveInteger«atpVariation»+ size  :PositiveIntegerIdentifiableCodeIdentifiableDependencyOnArtifactIdentifiableCompiler+ name  :String+ options  :String+ vendor  :String+ version  :StringIdentifiableResourceConsumption«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTimesize: <> Tags: vh.latestBindingTime = preCompileTime+codeDescriptor1..*+resourceConsumption1«atpSplitable»«atpVariation»+requiredGeneratorTool0..*«atpVariation»+requiredArtifact0..*«atpVariation»+generatedArtifact0..*+behavior1+perInstanceMemorySize*«atpVariation»+compiler*

SwcImplementation

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SwcImplementation
Note

This meta-class represents a specialization of the general Implementation meta-class
with respect to the usage in application software.

Base

Attribute
behavior

perInstanc
eMemoryS
ize

Tags: atp.recommendedPackage=SwcImplementations
ARElement,ARObject,CollectableElement,Identiﬁable,Implementation,Multilanguage
Referrable,PackageableElement,Referrable
Datatype
SwcInternalBeh
avior
PerInstanceMe
morySize

ref The internal behavior implemented by this

Mul. Kind Note

Implementation.

1

*

aggr Allows a deﬁnition of the size of the per-instance
memory for this implementation. The aggregation
of PerInstanceMemorySize is subject to variability
with the purpose to support variability in the
software components implementations. Typically
different algorithms in the implementation are
requiring different number of memory objects, in
this case PerInstanceMemory.

requiredRT
EVendor

String

0..1

attr

Stereotypes: atpVariation
Tags: vh.latestBindingTime=preCompileTime
Identify a speciﬁc RTE vendor. This information is
potentially important at the time of integrating (in
particular: linking) the application code with the
RTE. The semantics is that (if the association
exists) the corresponding code has been created
to ﬁt to the vendor-mode RTE provided by this
speciﬁc vendor. Attempting to integrate the code
with another RTE generated in vendor mode is in
general not possible.

Table 8.1: SwcImplementation

PerInstanceMemorySize

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SwcImplementation
Note

Resources needed by the allocation of PerInstanceMemory for each SWC instance.
Note that these resources are not covered by an ObjectFileSection, because they are
supposed to be allocated by the RTE.
ARObject
Datatype

Mul. Kind Note

Base
Attribute
alignment PositiveInteger

1

1

attr Required alignment (1,2,4,...) of the referenced

PerInstanceMemory. Unit: byte.
ref This represents the referenced

PerInstanceMemory.

perInstanc
eMemory

PerInstanceMe
mory



Attribute
size

Datatype
PositiveInteger

Mul. Kind Note

1

attr Size (in bytes) of the reference

perInstanceMemory. The aggregation of
PerInstanceMemorySize is subject to variability
with the purpose to support variability in the
software components implementations. Different
algorithms in the implementation might require a
different PerInstanceMemorySize.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=preCompileTime

Table 8.2: PerInstanceMemorySize



#@SECTION: 9 Mode Management

In general, the Software Component Template doesn’t deﬁne the kind of modes
that shall be supported by State Managers or software-components explicitly. How
ever the Software Component Template provides generic mechanisms for describing
modes.

In this section the general relationship between modes,
components is discussed.

interfaces, and software

The assumption from the software-component point of view is that State Managers are
using a Standardized AUTOSAR PortInterface1 to inﬂuence the SwComponent
Type and also provide a PortInterface to get requests and conﬁrmations from the
SwComponentType.

They will be implemented as AUTOSAR services and be part of the Basic Software
on each ECU. The actual modes a State Manager provides will have to be standardized
as well to allow compatibility between software-components.

It is also possible to deﬁne a mode manager in the Application Software and the same
functionality is supported as for mode managers implemented in the Basic Software.

[TPS_SWCT_01581] Communication patterns for mode-related communication
(cid:100) Mode-related communication shall
implement a 1:1 or 1:n scenario but the cre(
cid:99)(RS_SWCT_03200,
ation of an n:1 conﬁguration shall be considered invalid.
RS_SWCT_03110)

As a consequence of [TPS_SWCT_01581], [constr_1101] is formulated.

[constr_1101] Mode-related communication (cid:100) An RPortPrototype typed by Mod
eSwitchInterface shall not be referenced by more than one SwConnector. (cid:99)()

#@SECTION: 9.1 Declaration of Modes

The SW-Component Template provides some simple means to deﬁne collections of
modes.

[TPS_SWCT_01071] ModeDeclaration (cid:100) The name of
the mode is the most
important attribute that has to be provided for each ModeDeclaration.
The
ModeDeclarations are grouped together within the ModeDeclarationGroup.
(cid:99)(RS_SWCT_03200, RS_SWCT_03110)

[TPS_SWCT_01067] Initial mode (cid:100) The initialMode is active before any mode
switches occurred. (cid:99)(RS_SWCT_03200)

This is shown in Figure 9.1

1See also AUTOSAR Glossary for “Standardized AUTOSAR Interface”.



Figure 9.1: ModeDeclaration

The class ModeDeclarationGroup has been introduced to support the grouping of
modes and (on M1 level) to provide predeﬁned sets of modes that could be standard
ized and re-used. The set of modes eventually deﬁnes a ﬂat (i.e. no hierarchical states)
state-machine where only one mode can be active at a given point in time.

Again, please note that the actual deﬁnition of modes and their relationship is not in
the responsibility of this document. In other words: the deﬁnition of modes represents
M1 artifacts whereas this document is limited to describing M2 model elements.

Both ModeDeclaration and ModeDeclarationGroup own attributes that facilitate
the generation of C source code from the formal deﬁnition.

[TPS_SWCT_01008] Deﬁnition of positive integer values that are directly taken
over by the RTE generator for creating the programmatic representations of the
ModeDeclaration (cid:100) The attributes ModeDeclaration.value and ModeDeclara
tionGroup.onTransitionValue allow for the deﬁnition of positive integer values
that are directly taken over by the RTE generator for creating the programmatic rep
resentations of the ModeDeclaration and ModeDeclarationGroup in the source
code. (cid:99)(RS_SWCT_03200)

[constr_1399] Standardized values of ModeDeclarationGroup.category (cid:100) The
AUTOSAR standard deﬁnes the following values of the attribute ModeDeclara
tionGroup.category with a standardized meaning:

• EXPLICIT_ORDER

• ALPHABETIC_ORDER




ARElementAtpBlueprintAtpBlueprintableAtpTypeModeDeclarationGroup+ onTransitionValue  :PositiveInteger [0..1]AtpStructureElementIdentifiableModeDeclaration+ value  :PositiveInteger [0..1]AtpPrototypeModeDeclarationGroupPrototype+ swCalibrationAccess  :SwCalibrationAccessEnum [0..1]«enumeration»SwCalibrationAccessEnum readOnly notAccessible readWrite«atpVariation» Tags:vh.latestBindingTime = blueprintDerivationTime«enumeration»ModeErrorReactionPolicyEnum lastMode defaultMode«isOfType»+type1{redefinesatpType}+modeDeclaration1..*«atpVariation»+initialMode1

[TPS_SWCT_01010] deﬁnes the meaning of these values.

It is not allowed to deﬁne any custom or project-speciﬁc value of the attribute Mod
eDeclarationGroup.category. (cid:99)()

As the attributes ModeDeclaration.value and ModeDeclarationGroup.on
TransitionValue are optional the following rule applies:

[constr_1298] Existence of attributes if category of a ModeDeclarationGroup
is set to EXPLICIT_ORDER (cid:100) The attributes ModeDeclarationGroup.onTransi
tionValue and ModeDeclaration.value (for each ModeDeclaration) shall be
set if the category of a ModeDeclarationGroup is set to EXPLICIT_ORDER. (cid:99)()

[constr_1299] Existence of attributes if category of a ModeDeclara
tionGroup is set to other than EXPLICIT_ORDER (cid:100) The attributes ModeDecla
rationGroup.onTransitionValue or ModeDeclaration.value (for any Mod
eDeclaration) shall not be set if the category of a ModeDeclarationGroup
is set to any value other than EXPLICIT_ORDER. (cid:99)()

[constr_1181] Numerical values used in ModeDeclaration.value and Mod
eDeclarationGroup.onTransitionValue (cid:100) The numerical values used to deﬁne
the value attributes and the onTransitionValue attribute of a ModeDeclara
tionGroup shall not overlap. (cid:99)()

In other words, it is not allowed that the values of two value attributes within one
ModeDeclarationGroup have the same numerical value. Neither is it allowed that
the numerical value of the ModeDeclarationGroup.onTransitionValue attribute
and the numerical value of one of the corresponding value attributes are identical.

[TPS_SWCT_01009] The numerical values used to deﬁne the values of ModeDec
laration.value and ModeDeclarationGroup.onTransitionValue can be ar
bitrarily deﬁned (cid:100) As long as the constraints [constr_1181], [constr_1298], and [con
str_1299] are fulﬁlled, the numerical values used to deﬁne the values of ModeDec
laration.value and ModeDeclarationGroup.onTransitionValue can be ar
bitrarily deﬁned. The numerical values are not required to be consecutive. Gaps are
positively allowed. (cid:99)(RS_SWCT_03200)

Example: the following example of a set of numerical values fulﬁlls all requirements on
the deﬁnition of ModeDeclaration.value and ModeDeclarationGroup.onTran
sitionValue: {1,2, 5, 100}.

Please note that the ability to deﬁne ModeDeclaration.value and ModeDeclara
tionGroup.onTransitionValue introduces a second heuristics for “ordering” Mod
eDeclarations. If ModeDeclaration.value and ModeDeclarationGroup.on
TransitionValue are not deﬁned the assignment of numerical values to the repre
sentations of individual ModeDeclarations it is up to the RTE generator to come up
with the applicable numerical values.

[TPS_SWCT_01010] categorys for the deﬁnition of a ModeDeclarationGroup
(cid:100) In order to support a clear separation between the two possible ways to inﬂuence the



deﬁnition of the programmatic representation of ModeDeclarations two categorys
shall be deﬁned for the deﬁnition of a ModeDeclarationGroup.

• The value of category of a ModeDeclarationGroup shall be set to EX
PLICIT_ORDER if it is intended to control the source code generation by means
of the values of the attributes ModeDeclaration.value and ModeDeclara
tionGroup.onTransitionValue.

• The value of category of a ModeDeclarationGroup shall be set to ALPHA
BETIC_ORDER if it is intended to let the RTE generator control the source code
generation according to the alphabetical sorting.

(cid:99)(RS_SWCT_03200)

More information regarding this aspect can be found in [SWS_Rte_02568].

[TPS_SWCT_01011] Default category of a ModeDeclarationGroup (cid:100) For rea
sons of backwards-compatibility with previous releases of AUTOSAR the default value
the category of a ModeDeclarationGroup shall be ALPHABETIC_ORDER.
of
(cid:99)(RS_SWCT_03200)

ModeDeclaration

Class#@CLASS: 
Package M2::AUTOSARTemplates::CommonStructure::ModeDeclaration
Note

Declaration of one Mode. The name and semantics of a speciﬁc mode is not deﬁned
in the meta-model.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
PositiveInteger

attr The RTE shall take the value of this attribute for

Mul. Kind Note
0..1

Base

Attribute
value

generating the source code representation of this
ModeDeclaration.

Table 9.1: ModeDeclaration

ModeDeclarationGroup

Class#@CLASS: 
Package M2::AUTOSARTemplates::CommonStructure::ModeDeclaration
Note

A collection of Mode Declarations. Also, the initial mode is explicitly identiﬁed.

Base

Tags: atp.recommendedPackage=ModeDeclarationGroups
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,Identiﬁable,MultilanguageReferrable,Packageable
Element,Referrable
Datatype

Mul. Kind Note

Attribute
initialMode ModeDeclaratio
n

1

ref The initial mode of the ModeDeclarationGroup.
This mode is active before any mode switches
occurred.



Attribute
modeDecl
aration

Datatype
ModeDeclaratio
n

Mul. Kind Note
1..*

aggr The ModeDeclarations collected in this

ModeDeclarationGroup.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=blueprintDerivation
Time

modeMana
gerErrorBe
havior

modeTran
sition
modeUser
ErrorBeha
vior

onTransitio
nValue

ModeErrorBeha
vior

0..1 aggr This represents the ability to deﬁne the error

behavior expected by the mode manager in case
of errors on the mode user side (e.g. terminated
mode user).

ModeTransition

*

aggr This represents the avaliable ModeTransitions of

ModeErrorBeha
vior

the ModeDeclarationGroup

0..1 aggr This represents the deﬁnition of the error behavior

expected by the mode user in case of errors on
the mode manager side (e.g. terminated mode
manager).

PositiveInteger

0..1

attr The value of this attribute shall be taken into

account by the RTE generator for
programmatically representing a value used for
the transition between two statuses.

Table 9.2: ModeDeclarationGroup

[TPS_SWCT_01450] Semantics of a ModeTransition (cid:100) In addition to the ability to
specify ModeDeclarations within a ModeDeclarationGroup it is also feasible to
deﬁne possible transitions between ModeDeclarations within the given ModeDec
larationGroup. This can be done by means of aggregation ModeTransition at
ModeDeclarationGroup in the role modeTransition. More details are explained
in Figure 9.2. (cid:99)(RS_SWCT_03200)

[TPS_SWCT_01451] Relations between ModeTransition and ModeDeclara
tion (cid:100) ModeTransition has two associations with the multiplicity 1 to ModeDec
laration:

• The reference enteredMode denotes a ModeDeclaration that can be entered

as part of the enclosing ModeTransition.

• The reference exitedMode denotes a ModeDeclaration that can be exited as

part of the enclosing ModeTransition.

(cid:99)(RS_SWCT_03200)



Figure 9.2: ModeTransition

[constr_1193] ModeDeclaration shall be referenced by at least one ModeTran
sition in the role enteredMode (cid:100) For each ModeDeclaration at least one Mode
Transition shall reference the ModeDeclaration in the role enteredMode. This
constraint shall apply only if there is at least one ModeTransition deﬁned in the
context of the enclosing ModeDeclarationGroup and it shall not apply to the ini
tialMode. (cid:99)()

For clariﬁcation, the ModeDeclarationGroup.initialMode does not need to be
referenced by an enteredMode because by identifying this ModeDeclaration in
the role initialMode it is clear that the ModeDeclaration will be entered at least
once.

ModeTransition

Class#@CLASS: 
Package M2::AUTOSARTemplates::CommonStructure::ModeDeclaration
Note

This meta-class represents the ability to describe possible ModeTransitions in the
context of a ModeDeclarationGroup.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
ModeDeclaratio
n
ModeDeclaratio
n

ref This represents the entered model of the

ref This represents the exited mode of the

Mul. Kind Note

ModeTransition.

ModeTransition

1

1

Base

Attribute
enteredMo
de
exitedMod
e

Table 9.3: ModeTransition

#@SECTION: 9.2 Modes and Events

[TPS_SWCT_01376] Software-components need to be capable of reacting to
state changes (cid:100) Software-components need to be capable of reacting to state




ARElementAtpBlueprintAtpBlueprintableAtpTypeModeDeclarationGroup+ onTransitionValue  :PositiveInteger [0..1]AtpStructureElementIdentifiableModeDeclaration+ value  :PositiveInteger [0..1]AtpStructureElementReferrableModeTransition«atpVariation» Tags:vh.latestBindingTime = blueprintDerivationTime+exitedMode1+enteredMode1+modeDeclaration1..*«atpVariation»+initialMode1+modeTransition0..*

changes issued by some Mode Manager and adopt their behavior to the new situ
ation. (cid:99)(RS_SWCT_03110)

Such a mode dependent software-component is shown in Figure 9.3.

[TPS_SWCT_01077] Conﬁgure the response to mode changes (cid:100) Since the behav
ior of AtomicSwComponentTypes is mainly determined by the RunnableEntitys
contained in the SwcInternalBehavior it is necessary to conﬁgure the response to
mode changes on the level of RunnableEntitys. (cid:99)(RS_SWCT_03120)

Figure 9.3: State Managers and software-components

Figure 9.4 shows an excerpt of the meta-model illustrating how the relationship be
tween the current mode and the SwcInternalBehavior of the AtomicSwCompo
nentType can be described.

Figure 9.4: Modes and events




AtpStructureElementIdentifiableModeDeclaration+ value  :PositiveInteger [0..1]AbstractEventAtpStructureElementRTEEventSwcModeSwitchEvent+ activation  :ModeActivationKindAtpStructureElementExecutableEntityRunnableEntity+ canBeInvokedConcurrently  :Boolean+ symbol  :CIdentifier«enumeration»ModeActivationKind onEntry onExit onTransition«instanceRef»+mode1..2{ordered}«instanceRef»+disabledMode0..*+startOnEvent0..1

[TPS_SWCT_01377] Two mechanisms to deﬁne how SwcInternalBehavior
should interact with the mode management (cid:100) A AtomicSwComponentType
can use two mechanisms to deﬁne how its SwcInternalBehavior should in
teract with the mode management. Both mechanisms are visible in Figure 9.4.
(cid:99)(RS_SWCT_03110)

[TPS_SWCT_01378] AtomicSwComponentType can deﬁne
an SwcMod
eSwitchEvent to execute RunnableEntity (cid:100) Using the ﬁrst mechanism, an
AtomicSwComponentType can deﬁne an SwcModeSwitchEvent to specify that a
particular RunnableEntity shall be started whenever a mode is entered, exited, or
a transition between two speciﬁed modes occurs. (cid:99)(RS_SWCT_03110)

[constr_4003] Semantics of SwcModeSwitchEvent (cid:100) If the value of SwcMod
eSwitchEvent.activation is onTransition then SwcModeSwitchEvent shall
refer to two different ModeDeclarations belonging to the same instance of Mod
eDeclarationGroup.

Their order deﬁnes the direction of the transition from one mode into another.
In all
other cases SwcModeSwitchEvent shall refer to exactly one ModeDeclaration.
(cid:99)()

[constr_1195] SwcModeSwitchEvent and the deﬁnition of ModeTransition (cid:100)
For each pair of ModeDeclarations referenced by a SwcModeSwitchEvent with
attribute activation set to onTransition a ModeTransition shall be deﬁned in
the corresponding direction (i.e. from exitedMode to enteredMode). This constraint
shall only apply if the respective ModeDeclarationGroup deﬁnes at least one mod
eTransition. (cid:99)()

[TPS_SWCT_01379] AtomicSwComponentType can indicate whether an
RTEEvent that starts an associated RunnableEntity is disabled in a cer
the AtomicSwComponentType can
tain mode (cid:100) Using the second mechanism,
indicate whether an RTEEvent that starts an associated RunnableEntity is
disabled in a certain mode.

That is, RTEEvents without an association in the role disabledMode are processed
regularly according to their deﬁnition.

RTEEvents with the optional association disabledMode have the additional limitation
that the associated RunnableEntity is not started when the ModeDeclaration
referenced as disabledMode is active. (cid:99)(RS_SWCT_03110)

The mechanisms discussed so far have to be applied for the SwcInternalBehav
ior on the receiver side of mode switches. Since mode switches are received via
PortPrototypes the following constraints apply:

[TPS_SWCT_01380] Mode management behavior on the sender side (cid:100) On the
sender side, a RunnableEntity shall have ModeSwitchPoints that eventually as
sociate a RunnableEntity with the speciﬁc ModeDeclarationGroups which it
manages, see Figure 9.5. (cid:99)(RS_SWCT_03110)



Figure 9.5: ModeSwitchPoint

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SwcInternalBehavior::Mode

ModeSwitchPoint

Note

Base

Attribute
modeGrou
p

DeclarationGroup
A ModeSwitchPoint is required by a RunnableEntity owned a Mode Manager. Its
semantics implies the ability to initiate a mode switch.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
ModeDeclaratio
nGroupPrototyp
e

iref The mode declaration group that is switched by

Mul. Kind Note
0..1

this runnable.

Table 9.4: ModeSwitchPoint

[TPS_SWCT_01383] ModeSwitchPoint (cid:100) The ModeSwitchPoint also allows for
the deﬁnition of a ModeSwitchedAckEvent if this is requested by the deﬁnition of the
PPortPrototype (see also 4.5.3). This RTEEvent is eventually owned by a mode
manager to allow for getting conﬁrmation of a mode change. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01555] ModeSwitchedAckEvent is triggered by the RTE regardless
(cid:100) The ModeSwitchedAckEvent is triggered by the RTE (for more details please refer
to [2]) regardless which RunnableEntity has requested the mode switch notiﬁca
tion, even if the Meta Model implies a reference from ModeSwitchedAckEvent to a
speciﬁc ModeSwitchPoint in the role eventSource. (cid:99)(RS_SWCT_03110)

[constr_4012] Timeout of ModeSwitchedAckEvent (cid:100) The timeout value of a Wait
Point associated with a ModeSwitchedAckEvent shall be equal to the correspond
ing ModeSwitchedAckRequest.timeout. (cid:99)()




AtpStructureElementExecutableEntityRunnableEntityAtpStructureElementIdentifiableModeSwitchPointAtpPrototypeModeDeclarationGroupPrototype+ swCalibrationAccess  :SwCalibrationAccessEnum [0..1]RTEEventModeSwitchedAckEvent«atpVariation» Tags:vh.latestBindingTime =preCompileTime+eventSource10..*«instanceRef»+modeGroup0..1+modeSwitchPoint*«atpVariation»

ModeSwitchedAckRequest

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Communication
Note
Base
Attribute
timeout

Requests acknowledgements that a mode switch has been proceeded successfully
ARObject
Datatype
TimeValue

attr Number of seconds before an error is reported or

Mul. Kind Note

1

in case of allowed redundancy, the value is sent
again.

Table 9.5: ModeSwitchedAckRequest

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SwcInternalBehavior::RTE

ModeSwitchedAckEvent

Note

Base

Attribute
eventSour
ce

Events
The event is raised when the referenced modes have been received or an error
occurs.
ARObject,AbstractEvent,AtpClassiﬁer,AtpFeature,AtpStructure
Element,Identiﬁable,MultilanguageReferrable,RTEEvent,Referrable
Datatype
ModeSwitchPoi
nt

ref Mode switch point that triggers the event.

Mul. Kind Note

1

Table 9.6: ModeSwitchedAckEvent

[TPS_SWCT_01381] Read the currently active mode (cid:100) For Mode Manager and
Mode User it might additionally be required to read the currently active mode. For
that purpose the a RunnableEntity that requires read access to the ModeDec
larationGroupPrototype’s current mode has to deﬁne a ModeAccessPoint.
(cid:99)(RS_SWCT_03110)

Figure 9.6: ModeAccessPoint




AtpStructureElementExecutableEntityRunnableEntityAtpPrototypeModeDeclarationGroupPrototype+ swCalibrationAccess  :SwCalibrationAccessEnum [0..1]ModeAccessPoint«atpVariation» Tags:vh.latestBindingTime = preCompileTime+modeAccessPoint*«atpVariation»0..*«instanceRef»+modeGroup1

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SwcInternalBehavior::Mode

ModeAccessPoint

Note

Base
Attribute
ident

DeclarationGroup
A ModeAccessPoint is required by a RunnableEntity owned by a Mode Manager or
Mode User. Its semantics implies the ability to access the current mode (provided by
the RTE) of a ModeDeclarationGroupPrototype’s ModeDeclarationGroup.
ARObject
Datatype
ModeAccessPoi
ntIdent

Mul. Kind Note
0..1 aggr The aggregation in the role ident provides the

ability to make the ModeAccessPoint identiﬁable.

From the semantical point of view, the
ModeAccessPoint is considered a ﬁrst-class
Identiﬁable and therefore the aggregation in the
role ident shall always exist (until it may be
possible to let ModeAccessPoint directly inherit
from Identiﬁable).

Tags: atp.Status=shallBecomeMandatory
xml.sequenceOffset=-100

0..1

iref The mode declaration group that is accessed by

this runnable.

Tags: xml.typeElement=true

Table 9.7: ModeAccessPoint

modeGrou
p

ModeDeclaratio
nGroupPrototyp
e

[TPS_SWCT_01382] Mode switch requests are handled asynchronously by the
RTE (cid:100) Mode switch requests are handled asynchronously by the RTE. Therefore,
Mode Manager s implementation might require to read back the current active mode
to synchronize internally to the RTE. A ModeSwitchPoint does not automatically
provide read access to the ModeDeclarationGroupPrototype’s current mode.
(cid:99)(RS_SWCT_03110)

[constr_1098] Mode switch and mode disabling (cid:100) A SwcModeSwitchEvent shall
not simultaneously reference to the same ModeDeclaration in both the roles mode
and disabledMode. (cid:99)()

If [constr_1098] would not apply it might happen that a RunnableEntity would be
triggered by a SwcModeSwitchEvent and on the same time it would be suppressed
by the mode disabling.

#@SECTION: 9.3 Initialization / Finalization

The AUTOSAR standard shall support the execution of initialization code for every
AtomicSwComponentType.

[TPS_SWCT_01384] Execution of initialization code for software-components (cid:100)
Most AtomicSwComponentTypes will need to initialize by executing speciﬁc code;



this code shall complete before any other code in the component is executed. Data
will be initializing to speciﬁc values before the "normal" application software is running.
(cid:99)(RS_SWCT_03110)

[TPS_SWCT_01385] Execution of ﬁnalization code for software-components (cid:100)
Most AtomicSwComponentTypes will need to ﬁnalize by calling speciﬁc code; this
code shall complete before the functionality of the application software shut down (e.g.
a motor drive in a start or end position). (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01388] Initial modes of AtomicSwComponentTypes are deﬁned by
the initialMode (cid:100) The initial modes of AtomicSwComponentTypes are deﬁned
by the initialMode references of the required ModeDeclarationGroups. These
modes are activated before any other mode activation has occurred. It is the responsi
bility of the RTE to activate all initial modes on a certain ECU. (cid:99)(RS_SWCT_03110)

For more details please refer to the speciﬁcation of the SWS RTE [2].

#@SECTION: 9.4 Mode Error Behavior

With the advent of partitions in the AUTOSAR standard, it is important to consider the
behavior of mode management with respect to the following scenarios:

• The partition of the mode manager is terminated.

• The partition of the mode user is terminated.

Whenever one of the two scenarios becomes reality, it is important to implement a
stable reaction of both mode manager and mode user to the event. In addition, mode
manager and mode user should be able to synchronize in terms of which mode shall
apply as fast and seamless as possible.

For this purpose, additional modeling support has been deﬁned such that the applica
ble ModeDeclarationGroup (which is part of the contract between mode manager
and mode user) becomes the place where the policy towards a reaction to e.g. a
partition restart is deﬁned.

[TPS_SWCT_01530] Error behavior of mode manager and mode user (cid:100) The be
havior in response to a mode manager getting out of sync with a mode user (be
cause the partition of the mode user has been terminated) or vice versa (because
the partition of the mode manager has been terminated) can be deﬁned for the
mode manager by means of the attribute ModeDeclarationGroup.modeManager
ErrorBehavior and for the mode user by means of the attribute ModeDeclara
tionGroup.modeUserErrorBehavior. (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01531] The semantics of ModeErrorReactionPolicyEnum (cid:100) The
attribute ModeErrorBehavior.errorReactionPolicy shall be used to specify the
behavior in the event of a mode error:

lastMode The last mode applicable before the event shall be assumed.



defaultMode This represents the ability to specify a dedicated mode that shall be
made applicable. The identiﬁed ModeDeclaration could be identical to the
ModeDeclarationGroup.initialMode but it can just as well be any other
ModeDeclaration deﬁned in the context of the enclosing ModeDeclara
tionGroup.

(cid:99)(RS_SWCT_03110)

[TPS_SWCT_01532] The role of ModeErrorBehavior.defaultMode (cid:100) The at
tribute ModeErrorBehavior.defaultMode shall be used to identify the particular
ModeDeclaration if ModeErrorBehavior.errorReactionPolicy is set to de
faultMode. (cid:99)(RS_SWCT_03110)

[constr_1263] Existence of ModeErrorBehavior.defaultMode (cid:100) The optional at
tribute ModeErrorBehavior.defaultMode shall exist if the value of the attribute
ModeErrorBehavior.errorReactionPolicy is set to defaultMode. (cid:99)()

[TPS_SWCT_01533] ModeDeclarationGroup.initialMode shall be assumed
in the absence of ModeDeclarationGroup.modeManagerErrorBehavior (cid:100) If the
attribute ModeDeclarationGroup.modeManagerErrorBehavior is not deﬁned it
shall be assumed that the ModeDeclarationGroup.initialMode becomes appli
cable in case of the mode manager getting out of sync with a mode user (because the
partition of the mode user has been terminated). (cid:99)(RS_SWCT_03110)

[TPS_SWCT_01534] ModeDeclarationGroup.initialMode shall be assumed
in the absence of ModeDeclarationGroup.modeUserErrorBehavior (cid:100) If the at
tribute ModeDeclarationGroup.modeUserErrorBehavior is not deﬁned it shall
be assumed that the ModeDeclarationGroup.initialMode becomes applicable
in case of the mode user getting out of sync with a mode manager (because the parti
tion of the mode manager has been terminated). (cid:99)(RS_SWCT_03110)



Figure 9.7: Mode Error Behavior

ModeErrorBehavior

Class#@CLASS: 
Package M2::AUTOSARTemplates::CommonStructure::ModeDeclaration
Note
Base
Attribute
defaultMod
e

This represents the ability to deﬁne the error behavior in the context of mode handling.
ARObject
Datatype
ModeDeclaratio
n

ref This represents the ModeDeclaration that is

Mul. Kind Note
0..1

considered the error mode in the context of the
enclosing ModeDeclarationGroup.

errorReacti
onPolicy

ModeErrorReac
tionPolicyEnum

1

attr This represents the ability to deﬁne the policy in
terms of which default model shall apply in case
an error occurs.

Table 9.8: ModeErrorBehavior




AbstractEventAtpStructureElementRTEEventSwcModeSwitchEvent+ activation  :ModeActivationKindAtpStructureElementIdentifiableModeDeclaration+ value  :PositiveInteger [0..1]ModeSwitchedAckEventAtpStructureElementIdentifiableModeSwitchPointAtpPrototypeModeDeclarationGroupPrototype+ swCalibrationAccess  :SwCalibrationAccessEnum [0..1]ARElementAtpBlueprintAtpBlueprintableAtpTypeModeDeclarationGroup+ onTransitionValue  :PositiveInteger [0..1]SwcModeManagerErrorEvent«enumeration»ModeErrorReactionPolicyEnum lastMode defaultModeModeErrorBehavior+ errorReactionPolicy  :ModeErrorReactionPolicyEnum«atpVariation» Tags:vh.latestBindingTime = blueprintDerivationTime+defaultMode0..1«instanceRef»+modeGroup1«isOfType»+type1{redefinesatpType}«instanceRef»+modeGroup0..1+eventSource1+modeUserErrorBehavior0..1+modeManagerErrorBehavior0..1+initialMode1+modeDeclaration1..*«atpVariation»«instanceRef»+mode1..2{ordered}«instanceRef»+disabledMode0..*

Enumeration ModeErrorReactionPolicyEnum
Package
Note
Literal
defaultMode
lastMode
#@CLASS: 
M2::AUTOSARTemplates::CommonStructure::ModeDeclaration
This represents the ability to specify the reaction on a mode error.
Description
This represents the ability to switch to the defaultMode in case of a mode error.
This represents the ability to keep the last mode in case of a mode error.

Table 9.9: ModeErrorReactionPolicyEnum

[TPS_SWCT_01535] Mode manager reacts on mode error (cid:100) If the mode manager
is getting out of sync with a mode user (because the partition of the mode user has
been terminated) or vice versa (because the partition of the mode manager has been
terminated) it shall be possible for the mode manager to react on such an event.

For this purpose the formal SwcModeManagerErrorEvent is deﬁned that can be
taken to e.g. trigger the execution of a RunnableEntity in response to an error with
respect to mode switch communication. (cid:99)(RS_SWCT_03110)

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SwcInternalBehavior::RTE

SwcModeManagerErrorEvent

Note
Base

Attribute
modeGrou
p

Events
This represents the ability to react on errors occurring during mode handling.
ARObject,AbstractEvent,AtpClassiﬁer,AtpFeature,AtpStructure
Element,Identiﬁable,MultilanguageReferrable,RTEEvent,Referrable
Datatype
ModeDeclaratio
nGroupPrototyp
e

ModeDeclarationGroupPrototype for which the
error behavior of the mode manager applies.

iref This represents the

Mul. Kind Note

1

Table 9.10: SwcModeManagerErrorEvent

As mentioned in [constr_1075], it is possible to overrule the default compatibility rules
by the deﬁnition of a PortInterfaceMapping.

In this case the demand for having identical deﬁnitions of ModeDeclara
tionGroup.modeUserErrorBehavior and ModeDeclarationGroup.modeMan
agerErrorBehavior is no longer valid.

However, there is one additional caveat to observe in this case. This affects the imple
mentation of error behavior in case that several mode users are connected to a mode
manager.

[TPS_SWCT_01536] Coherent behavior of all mode users in case of errors in the
mode switch communication (cid:100) The behavior in case of errors with the communica
tion of mode switches needs to be coherent for all connected mode users especially
if the individual SwConnectors are legitimized by the existence of a PortInter
faceMapping. (cid:99)(RS_SWCT_03110)



[TPS_SWCT_01541] Preferential selection of modeUserErrorBehavior (cid:100) The
deﬁnition of mode error behavior on the provided side of shall be considered dominant
over the deﬁnition of mode error behavior on the required side.

This means that a ModeSwitchInterface.modeGroup.type.modeUserError
Behavior used to type an AbstractProvidedPortPrototype shall be con
the deﬁnition of a corresponding modeUserErrorBe
sidered dominant over
havior and deﬁned in the context of an AbstractRequiredPortPrototype.
(cid:99)(RS_SWCT_03110)

[TPS_SWCT_01542] Preferential selection of modeManagerErrorBehavior (cid:100)
The deﬁnition of mode error behavior on the provided side of shall be considered dom
inant over the deﬁnition of mode error behavior on the required side.

This means that a ModeSwitchInterface.modeGroup.type.modeManager
ErrorBehavior used to type an AbstractProvidedPortPrototype shall be
considered dominant over the deﬁnition of a corresponding modeManagerError
Behavior deﬁned in the context of an AbstractRequiredPortPrototype.
(cid:99)(RS_SWCT_03110)

The consequence of [TPS_SWCT_01541] and [TPS_SWCT_01542] is that the mode
manager shall be considered the master of the deﬁnition of mode error behavior.

Please note that the statements made in [TPS_SWCT_01541] is further underlined by
[SWS_Rte_06795] and the statement made by [TPS_SWCT_01542] is further under
lined by [SWS_Rte_06795].

The details of how the run-time behavior of mode manager and mode user shall look
like in the event of the mode manager getting out of sync with a mode user (because the
partition of the mode user has been terminated) or vice versa (because the partition
of the mode manager has been terminated) as well as the applicable RTE APIs are
explained in [2].

#@SECTION: 9.5 Summary Meta-Model Excerpt Related to Modes

Figure 9.8 provides an overview of all meta-model elements that have a direct relation
ship to the meta-classes involved in the modelling of mode switches.

To get the complete picture, it should be noted that also the concepts of PortGroups
(see 4.6) and ServiceProxySwComponentType (see 11.4) have a semantical rela
tionship to mode management, though this is not expressed via relations in the meta
model.



Figure 9.8: Summary meta-model excerpt related to modes




InterfaceModeDeclarationInternalBehavior and RunnablesComponent and PortAtpStructureElementIdentifiableModeDeclarationARElementAtpBlueprintAtpBlueprintableAtpTypeModeDeclarationGroupAtpPrototypeModeDeclarationGroupPrototypeAtpStructureElementExecutableEntityRunnableEntityPPortPrototypeRPortPrototypeAtomicSwComponentTypeInternalBehaviorSwcInternalBehaviorARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypeAbstractEventAtpStructureElementRTEEventSwcModeSwitchEventModeSwitchInterfaceARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface«atpVariation» Tags:vh.latestBindingTime = preCompileTimeAtpStructureElementReferrableModeTransitionAbstractProvidedPortPrototypeAbstractRequiredPortPrototypePRPortPrototypeModeSwitchedAckEvent«atpVariation» Tags:vh.latestBindingTime =preCompileTime+initialMode1+port0..*«atpVariation,atpSplitable»+component+modeDeclaration1..*«atpVariation»«atpVariation,atpSplitable»+internalBehavior0..1+modeGroup1«isOfType»+type1{redefines atpType}+startOnEvent0..1+event*«atpVariation,atpSplitable»«instanceRef»+disabledMode0..*0..*«instanceRef»+mode1..2{ordered}+modeTransition0..*+runnable1..*«atpVariation,atpSplitable»«isOfType»+requiredInterface1{redefinesatpType}«isOfType»+providedInterface1{redefinesatpType}+enteredMode1+exitedMode1«isOfType»+providedRequiredInterface1{redefinesatpType}


#@SECTION: 10 ECU Abstraction and Complex Drivers

#@SECTION: 10.1 Introduction

During the design of embedded systems there is one crucial point where the hard
ware and software have to be related. In AUTOSAR the ECU Resource Template
describes the provided hardware resources.

On the other hand, the Software Component Template describes software gen
erally without speciﬁc hardware in mind. But there are some places where both have
to meet and ﬁt.

One interface between hardware and software is discussed in the memory and execu
tion time section of [7]. In this chapter the overall system view of the interface between
sensors/actuators and software is described and the consequences for the Software
Component Template are derived.

#@SECTION: 10.2 High Level Hardware and Software Architecture

The AUTOSAR concept deﬁnes a software architecture (see Figure 10.1) and within
this layered architecture the interfaces between the hardware and the software are
explicitly modeled.



Figure 10.1: AUTOSAR ECU Software Architecture

The signal1 ﬂow from a hardware to software and vice versa will be described in the
following sections.

A sensor2 is converting a physical value (1) in Figure 10.2 (e.g.
light intensity) into an electrical signal (2) which can be either a current or a voltage.

temperature, force,

Inside the ECU generally there will be some electronics to enhance the electrical signal
provided by the sensor. In AUTOSAR this is called ECU Electronics. This electronics
is also responsible for the conversion of the electrical signal into a microcontroller com
patible form (3), usually a voltage.

After the electrical signal has been enhanced and converted it will be captured by the
microcontroller. This can either be done by a simple digital input, an analogue to digital
converter or maybe a pulse-width demodulation module. Now the electrical signal is
available as a software data value (4).

This signal ﬂow is sketched in the top part of Figure 10.2.

1The term “signal” is not going to be used here at its own but more speciﬁc terms will be used for the

different abstractions of signals at the different stages of the signal ﬂow.

2For the sake of simplicity this discussion is limited to the sensor aspects. Nevertheless, the same

applies also for actuators.



Figure 10.2: Interfaces between hardware and software

This signal chain is represented one to one in the AUTOSAR software architecture and
depicted in the lower part of Figure 10.2.

In an implementation of AUTOSAR only the Microcontroller Abstraction (MCAL) has
direct access to the peripheral hardware. This layer is going to be standardized and all
hardware access should go through this layer. The idea of the AUTOSAR signal ﬂow
is to map the hardware to the corresponding software modules.

So if an electrical current is the input to the microcontroller peripheral, the MCAL will
deliver a data value that represents this current. As the ECU Electronics has enhanced
and converted the electrical signal prior to the microcontroller, the corresponding soft
ware entity is reversing this conversion. This is performed in the ECU Abstraction layer.

So if the input to the ECU is an electrical current and the ECU Electronics has con
verted this current into a voltage (from 2 to 3), the ECU Abstraction will convert the
data value voltage into an AUTOSAR signal representing a current (from 4 to 5). This
AUTOSAR signal represents the actual current that was provided by the sensor (2).

Now the ﬁrst step in the conversion has to be reversed: the sensor has converted a
physical value into an electrical signal. And so the Sensor Software Component has
to reverse this again. The Sensor Software Component will read the AUTOSAR signal
representing the electrical value and transform it into an AUTOSAR signal representa
tion of the physical value (from 5 to 6).

Now this physical value is available on the RTE and can be consumed or read by other
SW-Components. Although the interface between the ECU Abstraction and the Sen
sor Software Component is also an AUTOSAR interface and could be routed through
some communication bus, it will not be practical to separate the ECU Abstraction and
the corresponding SensorActuatorSwComponentType due to potentially high com
munication effort.




SensorECUElectronicsµCPeripheralsPhysical Interface:car velocityElectrical Interface:Isensor[0..200mA]Electrical Interface:UECU[0..5V]SensorSW-CApplicationSW-Cget_v()get_I_sensor()DIO_set()Car environment123ECUAbstractionMCAL546ADC_get()

In Figure 10.3 a complete signal ﬂow from a sensor input to an actuator output is
shown.

Figure 10.3: Sensor and Actuator Signal Flow

In the next section the interfaces between the involved software modules are dis
cussed.

#@SECTION: 10.3 Interfaces and APIs

Two fundamentally different interfaces are involved when converting from sensors/ac
tuators to software components, see markers “4” and “5” in Figure 10.2.

The interface between the Microcontroller Abstraction and the ECU Abstraction is a
Standardized Interface (see AUTOSAR Glossary [42]). This interface is not visible on
the Virtual Function Bus and therefore the MCAL and ECU Abstraction have to be
present on the same ECU.

For further description of this interface please refer to the ECU Resource Template
documentation.

The interface to the SensorActuatorSwComponentTypes is visible on the Virtual
Function Bus. In general the SensorActuatorSwComponentType should be on
the same ECU as the ECU hardware abstraction.

Also the interface between the SensorActuatorSwComponentTypes and the actual
AtomicSwComponentTypes representing the application is visible on the VFB. To de
scribe the data that is going to be exchanged via this interface the standard AUTOSAR
Interface description mechanisms are used (see chapter 3.4).




SensorECUElectronicsµCPeripheralsPhysical InterfaceElectrical InterfaceIsensor[0..200mA]Electrical InterfaceUECU[0..5V]SensorSW-CECUAbstractionµCAL(MCAL Driver)ApplicationSW-C 1get_v()get_I_ECU(velocity_sensor)DIO_get()e.g. Car velocityActuatorSW-CApplicationSW-C 2set_lamp()set_I_ECU(light_actuator)DIO_set()ActuatorECUElectronicsµCPeripheralse.g. Car lightIECU[0..2A]UµC[0..5V]HardwareSoftwareHardware

#@SECTION: 10.3.1 ECU Abstraction and its AUTOSAR Interfaces

Since the AUTOSAR standard is designed with the focus on the integration of software
components coming from different contractors, the interfaces between the different
software-components obviously have to be compatible.

In the case of the sensors and actuators the interface is gathered in the ECU Abstrac
tion. For each sensor and actuator there is one AUTOSAR PortPrototype that rep
resents the AUTOSAR Signal that is delivered by the sensor or the AUTOSAR Signal
that is consumed by the actuator. This relationship is depicted in Figure 10.4

Figure 10.4: Interfaces of signals in software

Each sensor and actuator has an AUTOSAR PortPrototype at the ECU Abstrac
tion. Connected to this port is the SensorActuatorSwComponentType. The Sen
sorActuatorSwComponentType has one PortPrototype (i.e. IF_2) to the ECU
Abstraction (which provides the values via IF_1) where it gets the AUTOSAR signals
from the hardware, and one PortPrototype (i.e.
IF_3) to AtomicSwComponent
Types where it provides the actual physical value to the rest of AUTOSAR on the RTE.

In addition, the Interfaces between the ECU Abstraction and the SensorActuator
SwComponentType have to be compatible like deﬁned in chapter 6.

#@SECTION: 10.4 Sensors/Actuators

In the layered software architecture described in [6] each hardware sensor/actuator is
coupled to a SensorActuatorSwComponentType (see Figure 10.5).

[TPS_SWCT_01047] Reference from the software representation of a sensor/ac
tuator to the actual hardware element (cid:100) Since the Software Component Tem
plate is going to be used to describe the SensorActuatorSwComponentType as
well, there is also a reference needed from the software representation of a sensor/ac
tuator to the actual hardware element described in the ECU Resource description.
(cid:99)(RS_SWCT_02080, RS_SWCT_03090)



Figure 10.5: Shipment of a sensor

So each time a sensor/actuator is selected to be connected to an ECU also the corre
sponding SensorActuatorSwComponentType is available.

[constr_1144] SensorActuatorSwComponentType, EcuAbstractionSwCompo
nentType, and ComplexDeviceDriverSwComponentType may only reference a
HwType (cid:100) The attribute sensorActuator of SensorActuatorSwComponentType,
the attribute hardwareElement of EcuAbstractionSwComponentType, and the
attribute hardwareElement of ComplexDeviceDriverSwComponentType may
only reference a HwType. References to other subclasses of HwDescriptionEn
tity are not allowed. (cid:99)()

Figure 10.6: Sensor/actuator to Hardware Relationship

Figure 10.6 depicts the reference of SensorActuatorSwComponentType designed
as a specialization of an AtomicSwComponentType with an additional reference to a
HwType.

[constr_1109] Mapping of SwComponentPrototypes typed by a SensorActua
torSwComponentType (cid:100) A SwComponentPrototype typed by a SensorActua
torSwComponentType needs to be mapped and run on exactly that ECU that con
tains the HwElement corresponding to the HwType that its SensorActuatorSwCom
ponentType refers to in case it accesses the hardware via the I/O hardware abstrac
tion layer. (cid:99)()




AtomicSwComponentTypeSensorActuatorSwComponentTypeReferrableHwDescriptionEntityARElementHwType+sensorActuator1+hwType0..1

[TPS_SWCT_01048] SensorActuatorSwComponentType may use the I/O hard
ware abstraction directly (cid:100) In contrast to an ApplicationSwComponentType, a
SensorActuatorSwComponentType may use the I/O hardware abstraction directly
(via ports/connectors). (cid:99)(RS_SWCT_02080, RS_SWCT_03090)

In case the sensor/actuator hardware is accessed via bus communication, e.g. is lo
cated on a LIN slave, no such mapping constraints apply (note that this is not handled
via the IO hardware abstraction layer).

SensorActuatorSwComponentType

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Components
Note

The SensorActuatorSwComponentType introduces the possibility to link from the
software representation of a sensor/actuator to its hardware description provided by
the ECU Resource Template.

Base

Attribute
sensorActu
ator

Tags: atp.recommendedPackage=SwComponentTypes
ARElement,ARObject,AtomicSwComponentType,AtpBlueprint,AtpBlueprintable,Atp
Classiﬁer,AtpType,CollectableElement,Identiﬁable,Multilanguage
Referrable,PackageableElement,Referrable,SwComponentType
Datatype
HwDescriptionE
ntity

ref Reference from the Sensor Actuator Software

Mul. Kind Note

Component Type to the description of the actual
hardware.

1

Table 10.1: SensorActuatorSwComponentType

#@SECTION: 10.5 I/O Hardware Abstraction

[TPS_SWCT_01389] I/O Hardware Abstraction interfaces MCAL drivers (cid:100)
The I/O Hardware Abstraction interfaces on one side the MCAL drivers via
Standardized Interfaces and on the other side the Sensor Actuator Software
Component via AUTOSAR Interfaces. On the VFB[3] the I/O Hardware Ab
straction is represented by the EcuAbstractionSwComponentType. (cid:99)()

[TPS_SWCT_01390] I/O Hardware Abstraction might have sub-structures (cid:100)
Depending on the complexity of an ECU, the I/O Hardware Abstraction might
In this case the I/O Hardware Abstraction Layer is de
have sub-structures.
scribed by several different EcuAbstractionSwComponentTypes on M1. (cid:99)()



EcuAbstractionSwComponentType

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Components
Note

The ECUAbstraction is a special AtomicSwComponentType that resides between a
software-component that wants to access ECU periphery and the Microcontroller
Abstraction. The EcuAbstractionSwComponentType introduces the possibility to link
from the software representation to its hardware description provided by the ECU
Resource Template.

Base

Attribute
hardwareE
lement

Tags: atp.recommendedPackage=SwComponentTypes
ARElement,ARObject,AtomicSwComponentType,AtpBlueprint,AtpBlueprintable,Atp
Classiﬁer,AtpType,CollectableElement,Identiﬁable,Multilanguage
Referrable,PackageableElement,Referrable,SwComponentType
Datatype
HwDescriptionE
ntity

ref Reference from the

Mul. Kind Note

EcuAbstractionComponentType to the description
of the used HwElements.

*

Table 10.2: EcuAbstractionSwComponentType

[TPS_SWCT_01391] I/O Hardware Abstraction abstracts from the location
of peripheral I/O devices (cid:100) The I/O Hardware Abstraction abstracts from the
location of peripheral I/O devices (on-chip or on- board) and the ECU hardware layout
and has therefore dependencies to ECU Hardware described by HwElements. In ad
dition, the EcuAbstractionSwComponentType is a hybrid concept sharing features
of both software-components and basic software modules. (cid:99)()

[TPS_SWCT_01392] Mapping between the EcuAbstractionSwComponentType
and the corresponding BswModuleDescription (cid:100) The BSW part is described by
the means of the Basic Software Module Template. The mapping between the
EcuAbstractionSwComponentType and the corresponding BswModuleDescrip
tion is provided by the class SwcBswMapping which in addition also maps the two
corresponding InternalBehaviors. This mechanism is further explained in [7]. (cid:99)()



Figure 10.7: EcuAbstractionSwComponentType

#@SECTION: 10.6 Complex Driver

[TPS_SWCT_01393] Complex Driver (cid:100) A Complex Driver implements complex
sensor evaluation and actuator control with direct access to the Microcontroller using
speciﬁc interrupts and/or complex Microcontroller peripherals to fulﬁll the special func
tional and timing requirements.

In addition it might be used to implement enhanced services / protocols or encapsu
lates legacy functionality of a non-AUTOSAR system. (cid:99)()

See also document [3].

[TPS_SWCT_01394] Complex Driver is represented by the ComplexDe
viceDriverSwComponentType (cid:100) On the VFB the Complex Driver is represented
by the ComplexDeviceDriverSwComponentType. An ECU might have zero to
many different ComplexDeviceDriverSwComponentTypes. (cid:99)()




EcuAbstractionSwComponentTypeARElementAtpStructureElementSwcBswMappingSwComponentTypeAtomicSwComponentTypeInternalBehaviorSwcInternalBehaviorInternalBehaviorBswInternalBehaviorARElementAtpBlueprintAtpBlueprintableAtpStructureElementBswModuleDescription+ moduleId  :PositiveInteger [0..1]«atpVariation» Tags:vh.latestBindingTime =preCompileTimeReferrableHwDescriptionEntityARElementHwType+hardwareElement0..*+swcBehavior1+bswBehavior1«atpSplitable»+internalBehavior0..*+hwType0..1«atpVariation,atpSplitable»+internalBehavior0..1

ComplexDeviceDriverSwComponentType

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Components
Note

The ComplexDeviceDriverSwComponentType is a special AtomicSwComponentType
that has direct access to hardware on an ECU and which is therefore linked to a
speciﬁc ECU or speciﬁc hardware. The ComplexDeviceDriverSwComponentType
introduces the possibility to link from the software representation to its hardware
description provided by the ECU Resource Template.

Base

Attribute
hardwareE
lement

Tags: atp.recommendedPackage=SwComponentTypes
ARElement,ARObject,AtomicSwComponentType,AtpBlueprint,AtpBlueprintable,Atp
Classiﬁer,AtpType,CollectableElement,Identiﬁable,Multilanguage
Referrable,PackageableElement,Referrable,SwComponentType
Datatype
HwDescriptionE
ntity

ref Reference from the

Mul. Kind Note

ComplexDeviceDriverSwComponentType to the
description of the used HwElements.

*

Table 10.3: ComplexDeviceDriverSwComponentType

[TPS_SWCT_01395] ComplexDeviceDriverSwComponentType has dependen
cies to ECU Hardware (cid:100) Similar to EcuAbstractionSwComponentType the Com
plexDeviceDriverSwComponentType has dependencies to ECU Hardware de
scribed by HwElements and is a hybrid between Software Component and Basic
Software Module. (cid:99)()

[TPS_SWCT_01396] Mapping between the ComplexDeviceDriverSwCompo
nentType and the corresponding BswModuleDescription (cid:100) The BSW part is
described by the means of the Basic Software Module Template. The map
ping between the ComplexDeviceDriverSwComponentType and the correspond
ing BswModuleDescription is provided by the class SwcBswMapping which in ad
dition also maps the two corresponding InternalBehaviors. This mechanism is
further explained in [7]. (cid:99)()



Figure 10.8: ComplexDeviceDriverSwComponentType




ComplexDeviceDriverSwComponentTypeARElementAtpStructureElementSwcBswMappingSwComponentTypeAtomicSwComponentTypeInternalBehaviorSwcInternalBehaviorInternalBehaviorBswInternalBehaviorARElementAtpBlueprintAtpBlueprintableAtpStructureElementBswModuleDescription+ moduleId  :PositiveInteger [0..1]«atpVariation» Tags:vh.latestBindingTime =preCompileTimeReferrableHwDescriptionEntityARElementHwType+hwType0..1«atpVariation,atpSplitable»+internalBehavior0..1«atpSplitable»+internalBehavior0..*+swcBehavior1+bswBehavior1+hardwareElement0..*


#@SECTION: 11 Services

#@SECTION: 11.1 Overview: Generation of Service-related Model Elements

This chapter covers the description and handling of AUTOSAR Service conﬁguration.

[TPS_SWCT_01397] Hybrid concept between Basic Software Modules and a
SwComponentType (cid:100) AUTOSAR Services can be seen as a hybrid concept between
Basic Software Modules and a SwComponentType. AUTOSAR Services ac
tually provide access to low-level and ECU-wide “standard functionalities” commonly
referred to as “service”.

AtomicSwComponentTypes that require AUTOSAR Services use Standardized
AUTOSAR Interfaces to communicate with these. The connection of PortProto
types of the ServiceSwComponentTypes and PortPrototypes of the Atomic
SwComponentTypes implement several communication patterns. (cid:99)()

I

A

II

III

IV

1:n PPort : RPort

distribution of data or modes to n SW-Cs, e.g. used for ECU mode

A*

1:n RPort : PPort

currently not used, not supported for client-server communication

B

B

C*

C

1:1 PPort : RPort

SW-C acts as Server, used for so called “call-backs”

1:1 RPort : PPort

n:1 PPort : RPort

Service acts as Server, typical Service usage
conceptually not used to support index abstraction via PortDefinedArgumentValues

n:1 RPort:PPort

SW-C acts as Server, used for so called “call-backs” invoked by more than one Service

Table 11.1: ServiceConnectorPattern

Legend for Table 11.1:

I Pattern name

II Communication pattern (client/server, sender/receiver)

III Kind of PortPrototype at service : software-component

IV Description, use case

[TPS_SWCT_01398] Communication patterns for AUTOSAR services (cid:100) The com
munication patterns for AUTOSAR services are summarized in Table 11.1. (cid:99)()

[TPS_SWCT_01403] Impact of AUTOSAR services on the methodology (cid:100) Due to
this special nature, such AUTOSAR Services need to be handled with particular at
tention in the methodology [4]. That is, a number of elements need to be generated
during ECU integration. (cid:99)()

The following list of paragraphs presents a short overview over the steps required for
the conﬁguration of AUTOSAR Services.

Note that most of these steps are performed by tools and the model elements being
created in these steps are rather speciﬁc to Service conﬁguration and are not to be
modeled manually within AUTOSAR authoring tools.



In particular, the following requirements apply:

• [TPS_SWCT_01399] Dependency is modeled by aggregating required and
provided PortPrototypes (cid:100) The dependency of an AtomicSwComponent
Type (or more precisely, one of its non-abstract derived meta-classes) from an
AUTOSAR Service is modeled by aggregating required and provided Port
Prototypes. (cid:99)()

[TPS_SWCT_01400] PortInterface selected from the set of standard
ized Service Interfaces (cid:100) The PortInterface being implemented by the
PortPrototypes needs to be one of a number of standardized Service In
terfaces which is indicated by having its isService attribute set to true and
is (via several levels of indirection) ﬁnally referenced by ServiceNeeds. (cid:99)()

Additionally, the software components and Basic Software Modules shall
specify ServiceNeeds containing further input information for the later Service
conﬁguration step.

• [TPS_SWCT_01401] Form a top-level RootSwCompositionPrototype (cid:100)
When deﬁning a software system, the AtomicSwComponentType is used in the
form of SwComponentPrototypes within a CompositionSwComponentType.
In this step, the non-service ports of all required interfaces are being connected
using AssemblySwConnectors and DelegationSwConnectors in order to
eventually form a top-level RootSwCompositionPrototype which can be ref
erenced in an AUTOSAR System. (cid:99)()

• [TPS_SWCT_01402] Mapping of all AtomicSwComponentType instances
to EcuInstances (cid:100) In System Configuration Phase, the mapping of all
AtomicSwComponentType instances to EcuInstances is done (for the speci
ﬁcation of EcuInstance see [11]). The ServiceNeeds may be used by tools
to check for available resources on the targeted ECUs. (cid:99)()

• [TPS_SWCT_01404] Creation of the Ecu Extract (cid:100) The ECU Extract is
extracted from the System Configuration for each ECU. As explained in the
AUTOSAR System Template [11], this contains an ECU-centric view onto the
system description.

This includes a reduced version of the system’s RootSwCompositionProto
type where SwComponentPrototypes not being mapped to the ECU are being
left out and all Compositions are stripped off, so that in the ECU Extract only
one instance of CompositionSwComponentType remains which aggregates all
SwComponentPrototypes on the ECU in a ﬂat manner. (cid:99)()

• [TPS_SWCT_01405] Creation of the ServiceSwComponentTypes (cid:100) In ECU
for each Service required on the ECU exactly one Ser
Conﬁguration,
viceSwComponentType is created based on the needs from the Atomic
SwComponentTypes: An adequate number of PortPrototypes are created on
this ServiceSwComponentType for each needed port at the AtomicSwCom
ponentType.



Thereby the speciﬁed communication pattern A, B or C for a speciﬁc kind of
ServicePort has to be considered. See also chapter 11.3 and table 11.1. (cid:99)()

• [TPS_SWCT_01406] Creation of SwComponentPrototype typed by a Ser
viceSwComponentType (cid:100) Per Service exactly one SwComponentProto
type typed by a ServiceSwComponentType is created based on the Ser
viceSwComponentType. Additionally, the connectors are constructed that con
nect the pairs of PortPrototypes belonging to the SwComponentPrototypes
requiring services and those belonging to the actual services. (cid:99)()

• [TPS_SWCT_01407] Creation of InternalBehavior typed by a Ser
viceSwComponentType (cid:100) For each ServiceSwComponentType an SwcIn
ternalBehavior is created or extended providing the information about Port
DefinedArgumentValues, RunnableEntitys and RTEEvents necessary for
RTE generation. (cid:99)()

Further detailing of the service ports by ﬁlling in these PortDefinedArgument
Values is also done in ECU Conﬁguration phase. See also chapter 7.6.3.

• [TPS_SWCT_01408] Creation of SwcBswMapping (cid:100) For the RTE module con
ﬁguration an implementation of the AUTOSAR Service described by a Basic
Software Module Description needs to be selected. The SwcBswMap
ping to the corresponding SwComponentPrototype needs to be created ac
cordingly.

For each SwcInternalBehavior one SwcImplementation is being created.
The information for SwcImplementation should be generated based on the
available information of BswImplementation1. (cid:99)()

• [TPS_SWCT_01409] Update of PortDefinedArgumentValues (cid:100) Depending
of the conﬁguration of the Service BSW it might be necessary to update the Val
ueSpecifications belonging to the PortDefinedArgumentValues gener
ated in a previous step. (cid:99)()

ServiceNeeds (abstract)

Class#@CLASS: 
Package M2::AUTOSARTemplates::CommonStructure::ServiceNeeds
Note

This expresses the abstract needs that a Software Component or Basic Software
Module has on the conﬁguration of an AUTOSAR Service to which it will be
connected. "Abstract needs" means that the model abstracts from the Conﬁguration
Parameters of the underlying Basic Software.
ARObject,Identiﬁable,MultilanguageReferrable,Referrable
Datatype
–

Mul. Kind Note
–

–

–

Base
Attribute
–

Table 11.2: ServiceNeeds

1This step does in general not require copying any attributes or elements aggregated in BswImple
mentation into the generated instance of SwcImplementation since the only mandatory information
for the RTE conﬁguration is the reference from SwcImplementation to the selected SwcInternal
Behavior.



#@SECTION: 11.2 Extending the ECU Software Composition

As explained in chapter 11.1, Service Configuration takes place in ECU Conﬁg
uration phase. In the ECU extract of the System, the Software Components and their
ECU-internal connectors are represented as a ﬂat set aggregated by RootSwCompo
sitionPrototype as indicated in Figure 11.1.

ECU Conﬁguration extends this aggregation by adding SwComponentPrototypes
(each typed by a speciﬁc ServiceSwComponentType) and the required Assem
blySwConnectors to the RootSwCompositionPrototype. This is possible with
out changing the initial artifacts of the ECU extract, because these aggregations are
stereotyped as (cid:28)atpSplitable(cid:29) in the meta-model.

After this step, the RootSwCompositionPrototype (denoted by EcucValueCollec
tion.ecuExtract.rootSoftwareComposition) represents the whole Software
Composition on the given ECU. This collection includes both the software compo
nents mapped to the ECU and the necessary service components represented as one
SwComponentPrototype for each AUTOSAR Service utilized on the given ECU.



Figure 11.1: Usage of RootSwCompositionPrototype on an ECU

#@SECTION: 11.3 Service Software Component Type

As mentioned in [TPS_SWCT_01405], AUTOSAR Services are represented by a
meta model class of their own, the ServiceSwComponentType. As can be seen




CompositionSwComponentTypeAtpPrototypeIdentifiableRootSwCompositionPrototypeARElementAtpStructureElementSystem+ containerIPduHeaderByteOrder  :ByteOrderEnum [0..1]+ ecuExtractVersion  :RevisionLabelString [0..1]+ pncVectorLength  :PositiveInteger [0..1]+ pncVectorOffset  :PositiveInteger [0..1]+ systemVersion  :RevisionLabelStringServiceSwComponentTypeAtomicSwComponentTypeAtpPrototypeSwComponentPrototypeARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypeAtpStructureElementSwConnectorARElementEcucValueCollection«atpVariation» Tags:vh.latestBindingTime =systemDesignTime«atpVariation» Tags:vh.latestBindingTime =postBuild«atpVariation» Tags:vh.latestBindingTime =preCompileTimeAssemblySwConnectorAbstractProvidedPortPrototypeAbstractRequiredPortPrototype+connector*«atpVariation,atpSplitable»+ecuExtract10..*«instanceRef»+provider0..10..*«instanceRef»+requester0..1+component0..*«atpVariation,atpSplitable»«isOfType»+type1{redefinesatpType}+rootSoftwareComposition0..1«atpVariation,atpSplitable»«isOfType»+softwareComposition1{redefinesatpType}+port0..*«atpVariation,atpSplitable»

in Figure 11.2 ServiceSwComponentType is a specialization of AtomicSwCompo
nentType.

Like any other SwComponentType they can aggregate PortPrototypes.

[constr_2019] ServiceSwComponentType shall have service ports only (cid:100) In
the case of ServiceSwComponentType, all aggregated PortPrototypes need
to have an (cid:28)isOfType(cid:29) relationship to a PortInterface which has its is
Service attribute set to true. The exceptions described in [TPS_SWCT_01572],
[TPS_SWCT_01579] and [TPS_SWCT_01580] apply. (cid:99)()

[TPS_SWCT_01579] Dcm can directly access dataElements in PPortProto
types typed by a SenderReceiverInterface (cid:100) An exception from the rule de
scribed in [constr_2019] applies: the Dcm can directly access dataElements in Port
Prototypes (that is both AbstractProvidedPortPrototype and AbstractRe
quiredPortPrototype) typed by a SenderReceiverInterface.

For this purpose, the ServiceSwComponentType that represents the Dcm function
ality can have AbstractProvidedPortPrototypes and AbstractRequired
PortPrototypes typed by a compatible SenderReceiverInterface that may set
isService to FALSE. (cid:99)()

[TPS_SWCT_01580] Dem can directly access dataElements in PPortProto
types typed by a SenderReceiverInterface (cid:100) An exception from the rule de
scribed in [constr_2019] applies: the Dem can directly access dataElements in Ab
stractProvidedPortPrototypes typed by a SenderReceiverInterface.

For this purpose, the ServiceSwComponentType that represents the Dem function
ality can have RPortPrototypes typed by a compatible SenderReceiverInter
face that may set isService to FALSE. (cid:99)()

[TPS_SWCT_01411] Use cases for a ServiceSwComponentType to express Ser
viceNeeds (cid:100) There are valid use cases for a ServiceSwComponentType to ex
press ServiceNeeds2. This leads to a situation where ServiceSwComponent
Types are iteratively created in response to ServiceNeeds expressed by other Ser
viceSwComponentTypes. Please refer to the AUTOSAR methodology [4] for more
details about how this shall be implemented into the workﬂow. (cid:99)()

Similar to an EcuAbstractionSwComponentType and a ComplexDeviceDriver
SwComponentType, the ServiceSwComponentType represents a hybrid concept
between Software Component and Basic Software Module. The BSW part is
described by the means of the BSW Module Description Template [7].

The mapping between the ServiceSwComponentType and the corresponding
BswModuleDescription is provided by the class SwcBswMapping which in addition
also maps the two corresponding InternalBehaviors (see [TPS_SWCT_01408].
This mechanism is further explained in [7].

2Thereby the previously existing constraint 1127 becomes invalid.



Figure 11.2: ServiceSwComponentType

ServiceSwComponentType

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Components
Note

ServiceSwComponentType is used for conﬁguring services for a given ECU.
Instances of this class are only to be created in ECU Conﬁguration phase for the
speciﬁc purpose of the service conﬁguration.

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

Table 11.3: ServiceSwComponentType

[TPS_SWCT_01412] ServiceSwComponentType shall be added in ECU Conﬁg
uration phase (cid:100) ServiceSwComponentType shall not be used when modeling ap
plication software using CompositionSwComponentType; they are only added in
ECU Conﬁguration phase where exactly one SwComponentPrototype per Ser
viceSwComponentType per ECU is added to the ECU Description model.

The Base ECU Config Generator tool needs to take care that for all service ports
of SwComponentPrototypes mapped to the ECU service ports at the appropriate
ServiceSwComponentTypes are created. In the process the speciﬁed communica
tion pattern A, B, or C for a speciﬁc kind of service port has to be considered, see
table 11.1.




ServiceSwComponentTypeARElementAtpStructureElementSwcBswMappingSwComponentTypeAtomicSwComponentTypeInternalBehaviorSwcInternalBehaviorInternalBehaviorBswInternalBehaviorARElementAtpBlueprintAtpBlueprintableAtpStructureElementBswModuleDescription+ moduleId  :PositiveInteger [0..1]«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpSplitable»+internalBehavior0..*«atpVariation,atpSplitable»+internalBehavior0..1+swcBehavior1+bswBehavior1

In case of pattern A for each different type of service port one port on the Ser
viceSwComponentType is created.

In case of pattern B and C for each service port of a SwComponentPrototype one
port on the ServiceSwComponentType is created.

More explicitly, all instances of AtomicSwComponentType need to be checked for
PortPrototypes of PortInterfaces with isService attribute set to true and
referenced by ServiceNeeds and for each of these PortInterface instances be
longing to the AUTOSAR Service to be conﬁgured one PortPrototype implement
ing the same or a compatible PortInterface needs to be created on the Ser
viceSwComponentType. (cid:99)()

[TPS_SWCT_02500] Roles on Application/Service Components need to Match
(cid:100) The roles of the PortPrototypes (required/provided) on the Application Compo
nent and the Service Component side obviously need to match. For example an
RPortPrototype attached to an application AtomicSwComponentType matches
a PPortPrototype attached to a ServiceSwComponentType. (cid:99)()

#@SECTION: 11.4 Service Proxy Component Type

[TPS_SWCT_01413] Local communication with services (cid:100) Application software
components may communicate with an instance of a ServiceSwComponentType
only locally on an ECU. (cid:99)()

[TPS_SWCT_01414] Mode manager needs to communicate with application soft
ware components located on other ECUs (cid:100) There are however use cases for the
application and vehicle mode management, where a mode manager (namely the Ba
sic Software Mode Manager, see [15]) is part of the basic software but conceptu
ally still needs to communicate with application software components located on other
ECUs (as exempliﬁed by Figure 11.3).

In order to make this communication possible, the ServiceProxySwComponentType
is used.

For the application software and the RTE it behaves like a “normal” AtomicSwCompo
nentType, but it is actually a proxy for an AUTOSAR Service. (cid:99)()



Figure 11.3: Mode request over the network [3]

[TPS_SWCT_01415] Interfaces of ServiceProxySwComponentType (cid:100) This means
that on the one side it has to communicate over service ports with the ECU-local Ser
viceSwComponentType it represents. On the other side it has to offer the corre
sponding PortPrototypes to the ApplicationSwComponentTypes. (cid:99)()

In the meta-model, the ServiceProxySwComponentType does not differ from an
ApplicationSwComponentType except by its class. It is up to the implementer to
meet the restrictions imposed by the semantics as a proxy.

[TPS_SWCT_01416] Difference between a ServiceProxySwComponentType and
an ApplicationSwComponentType (cid:100) The main difference between a Service
ProxySwComponentType and an ApplicationSwComponentType is on system
level:

A prototype of a ServiceProxySwComponentType can be mapped to several ECUs
even if it appears only once in the VFB system, because such a prototype is required
on each ECU, where it has to address a local ServiceSwComponentType.

As a result of this, a ServiceProxySwComponentType can only receive but not send
signals over the network. More details are explained in the class table below. (cid:99)()




VFBRTE1BSW1ECU1VCC:VehicleClampControlVCP: VehicleClampProxyVCC:VehicleClampControlVCP: VehicleClampProxyBswMServiceRTE2BSW2ECU2VCP: VehicleClampProxyBswMServiceApp1:Application1App2:Application2App1:Application1App2:Application2

ServiceProxySwComponentType

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Components
Note

This class provides the ability to express a software-component which provides
access to an internal service for remote ECUs. It acts as a proxy for the service
providing access to the service.

An important use case is the request of vehicle mode switches: Such requests can be
communicated via sender-receiver interfaces across ECU boundaries, but the mode
manager being responsible to perform the mode switches is an AUTOSAR Service
which is located in the Basic Software and is not visible in the VFB view. To handle
this situation, a ServiceProxySwComponentType will act as proxy for the mode
manager. It will have R-Ports to be connected with the mode requestors on VFB level
and Service-Ports to be connected with the local mode manager at ECU integration
time.

Apart from the semantics, a ServiceProxySwComponentType has these speciﬁc
properties:

• A prototype of it can be mapped to more than one ECUs in the system

description.

• Exactly one additional instance of it will be created in the ECU-Extract per ECU

to which the prototype has been mapped.

• For remote communication, it can have only R-Ports with sender-receiver

interfaces and 1:n semantics.

• There shall be no connectors between two prototypes of any

ServiceProxySwComponentType.

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

Table 11.4: ServiceProxySwComponentType

[constr_2016] Connections between SwComponentPrototypes of type Servi
ceProxySwComponentType (cid:100) A connection between PortPrototypes belonging
to SwComponentPrototypes where both are typed by ServiceProxySwCompo
nentType is not permitted. (cid:99)()

[constr_2017] Ports of ServiceProxySwComponentTypes (cid:100) ServiceProx
ySwComponentType is only permitted to deﬁne

• RPortPrototypes that are typed by SenderReceiverInterface or

• PortPrototypes that are typed by a PortInterface where the isService

attribute is set to true.

(cid:99)()



[constr_2018] Supported remote communication of a ServiceProxySwCompo
nentType (cid:100) For remote communication, ServiceProxySwComponentType can
have only RPortPrototypes typed by SenderReceiverInterfaces in a 1:n com
munication scenario. (cid:99)()

#@SECTION: 11.5 Non Volatile Memory

#@SECTION: 11.5.1 Introduction

The AUTOSAR Architecture deﬁnes two alternatives how a software component can
access non volatile memory.

• The ﬁrst option is that the software component deﬁnes in its InternalBehavior
a PerInstanceMemory and a NvBlockNeeds referring to the PerInstance
Memory via a RoleBasedDataAssignment.

In this case the NVRAM Block is exclusively accessed by this software compo
nent and the NvM [31]. Therefore the nv data is encapsulated inside the software
component and can not be accessed directly by other software components.

The PerInstanceMemory can be typed with AutosarDataTypes in the case
of arTypedPerInstanceMemory or with C data types in the case of perIn
stanceMemory. For further information see section 7.7 and 7.11.3.

• The second option is that the software component uses communication based
on PortPrototypes to access nv data provided by a NvBlockSwComponent
Type.

In this case it is possible that nv data used by different AtomicSwComponent
Types is packed in one larger NVRAM Block to reduce the NVRAM Block man
agement overhead or that the same nv data used by several software compo
nents with a reduced RAM overhead. The nv data of a NvBlockSwComponent
Type is typed with AutosarDataTypes.

More details regarding particular scenarios of interacting with the NvM [31] can be
found in section 7.11.3.1.

#@SECTION: 11.5.2 NvBlockComponent

[TPS_SWCT_01142] non-volatile data are provided by a specialized Atomic
SwComponentType (cid:100) On the VFB [3], the non-volatile data are provided by a spe
cialized AtomicSwComponentType, the NvBlockSwComponentType.

An NvBlockSwComponentType can represent one or more NVRAM Blocks
The nv data PortPrototypes of
managed by the NVRAM Manager.
the NvBlockSwComponentType are exclusively typed by NvDataInterfaces.
(cid:99)(RS_SWCT_03225)



[TPS_SWCT_01143] Non-volatile data represented by an NvBlockSwComponent
Type can be read and written (cid:100) The non-volatile data represented by an NvBlock
SwComponentType can be read and written.
For this purpose the NvBlock
SwComponentType is allowed to have PPortPrototypes and RPortPrototypes.
(cid:99)(RS_SWCT_03225)

Additionally, the NvBlockSwComponentType might have client server PortProto
types to offer the block-related services, administrative services or notiﬁcations.

[constr_2009] Supported kinds of PortPrototypes of a NvBlockSwComponent
Type (cid:100) With respect to external communication, NvBlockSwComponentType is lim
ited to the deﬁnition of the following kinds of PortPrototype:

• PortPrototypes typed by either NvDataInterfaces or ClientServerIn

terfaces

• RPortPrototypes typed by ModeSwitchInterfaces

(cid:99)()

[constr_2010] Connections between SwComponentPrototypes of
type
NvBlockSwComponentType (cid:100) The existence of SwConnectors that
to
PortPrototypes belonging to SwComponentPrototypes where both are typed by
NvBlockSwComponentType is not permitted. (cid:99)()

refer

NvBlockSwComponentType

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::Components
Note

The NvBlockSwComponentType deﬁnes non volatile data which data can be shared
between SwComponentPrototypes. The non volatile data of the
NvBlockSwComponentType are accessible via provided and required ports.

Base

Attribute
nvBlockDe
scriptor

Tags: atp.recommendedPackage=SwComponentTypes
ARElement,ARObject,AtomicSwComponentType,AtpBlueprint,AtpBlueprintable,Atp
Classiﬁer,AtpType,CollectableElement,Identiﬁable,Multilanguage
Referrable,PackageableElement,Referrable,SwComponentType
Datatype
NvBlockDescrip
tor

aggr Speciﬁcation of the properties of exactly one

Mul. Kind Note

NVRAM Block.

*

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=preCompileTime

Table 11.5: NvBlockSwComponentType



NvDataInterface

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::PortInterface
Note

A non volatile data interface declares a number of VariableDataPrototypes to be
exchanged between non volatile block components and atomic software components.

Base

Attribute
nvData

Tags: atp.recommendedPackage=PortInterfaces
ARElement,ARObject,AtpBlueprint,AtpBlueprintable,AtpClassiﬁer,Atp
Type,CollectableElement,DataInterface,Identiﬁable,Multilanguage
Referrable,PackageableElement,PortInterface,Referrable
Datatype
VariableDataPr
ototype

Mul. Kind Note
1..*

aggr The VariableDataPrototype of this nv data

interface.

Table 11.6: NvDataInterface

Figure 11.4: NvDataInterface

#@SECTION: 11.5.3 Software-Components using NVRAM data of NvBlockComponents

[constr_2011] Connections between SwComponentPrototypes typed by
NvBlockSwComponentType and SwComponentPrototypes typed by other
AtomicSwComponentTypes (cid:100) The nv data PortPrototypes of the SwCompo
nentPrototype typed by an NvBlockSwComponentType are either connected with
PortPrototypes typed by NvDataInterfaces or SenderReceiverInterfaces
of other AtomicSwComponentType. (cid:99)()

[constr_1148] PortInterfaces of PortPrototypes used to connect
to
NvBlockSwComponentTypes (cid:100) PortInterfaces of PortPrototypes used to
connect to NvBlockSwComponentTypes as well as the PortInterfaces used in
the context of NvBlockSwComponentTypes shall always set the value of the attribute
isService to false. (cid:99)()




VariableDataPrototypeDataPrototypeAutosarDataPrototypeARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]NvDataInterfaceDataInterface+nvData1..*

[constr_1149] PortPrototypes used for NV data management (cid:100) A PortPro
totype typed by a ClientServerInterface used for NV data management, i.e.
the interaction of ApplicationSwComponentTypes with NvBlockSwComponent
Types, shall be typed by ClientServerInterfaces that are compatible to the par
ticular ClientServerInterfaces derived from MOD_GeneralBlueprints [30]. [con
str_1148] applies. (cid:99)()

For details see chapter 6.4.4.

Note: In case of nv data which is read and written and shared between several SwCom
ponentPrototypes the NvBlockSwComponentType establishes a not directly obvi
ous kind of communication. Nevertheless this is intentionally supported and it is under
responsibility of the VFB designer to take care that only nv data is shared where the
functionality of the software components is not impaired.

To determine for an VFB designer which nv data can be potentially by mapped into the
same NVRAM Block a software-component can specify further attributes for its nv data
PortPrototypes by the deﬁnition of SwcServiceDependency(s) with NvBlock
Needs. In this case the role attribute of the assignedPort has to be set to the value
NvDataPort. This aspect is also explained in section 7.11.3.1.4.



Figure 11.5: NvBlockNeeds for nv data PortPrototypes

In contrast to the NvBlockNeeds that describe the expected conﬁguration of a whole
NVRAM Block, the NvBlockNeeds for nv data PortPrototypes deﬁnes only the
attributes which are required from the point of view of a software-component to ensure
its functionality.

This means an empty attribute has the semantic of “don’t care”.

Further on the VFB designer has got the freedom to specify how the requested NVRAM
Block attributes are fulﬁlled by the created NvBlockDescriptor.

For instance, nv data with different writingFrequency might be mapped to one
NVRAM Block. In this case the NvBlockNeeds of the NvBlockDescriptor has to
indicate the worst case which is the higher frequency.




ARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypeDataInterfaceNvDataInterfaceInternalBehaviorSwcInternalBehaviorAtpStructureElementIdentifiableServiceDependencySwcServiceDependencyIdentifiableServiceNeedsNvBlockNeeds+ calcRamBlockCrc  :Boolean [0..1]+ checkStaticBlockId  :Boolean [0..1]+ cyclicWritingPeriod  :TimeValue [0..1]+ nDataSets  :PositiveInteger [0..1]+ nRomBlocks  :PositiveInteger [0..1]+ ramBlockStatusControl  :RamBlockStatusControlEnum [0..1]+ readonly  :Boolean [0..1]+ reliability  :NvBlockNeedsReliabilityEnum [0..1]+ resistantToChangedSw  :Boolean [0..1]+ restoreAtStart  :Boolean [0..1]+ storeAtShutdown  :Boolean [0..1]+ storeCyclic  :Boolean [0..1]+ storeEmergency  :Boolean [0..1]+ storeImmediate  :Boolean [0..1]+ useAutoValidationAtShutDown  :Boolean [0..1]+ useCRCCompMechanism  :Boolean [0..1]+ writeOnlyOnce  :Boolean [0..1]+ writeVerification  :Boolean [0..1]+ writingFrequency  :PositiveInteger [0..1]+ writingPriority  :NvBlockNeedsWritingPriorityEnum [0..1]AtomicSwComponentTypeRoleBasedPortAssignment+ role  :Identifier«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTimeShall be typed by NvDataInterface if the data is provided by an NvBlockSwComponentType. In a different context the PortPrototype shall be typed by a ClientServerInterface if the data is provided by NVRAM Manager.«atpVariation,atpSplitable»+internalBehavior0..1+portPrototype1«atpVariation,atpSplitable»+serviceDependency0..*+port0..*«atpVariation,atpSplitable»«atpVariation,atpSplitable»+assignedPort0..*+serviceNeeds1

The recommended relationship is shown in table 11.7. But please note that this table
does not represent a binding constraint.

readonly

Attribute of NvBlockNeeds NvBlockNeeds of different
nv data PortPrototypes
of software-components
Recommended to match for
all connected nv data Port
Prototypes if speciﬁed.
Can be different.

reliability

restoreAtStart

storeAtShutdown

resistantToChangedSw Recommended to match for
all connected nv data Port
Prototypes if speciﬁed.
Recommended to match for
all connected nv data Port
Prototypes if speciﬁed.
Recommended to match for
all connected nv data ports if
speciﬁed.
Recommended to match for
all connected nv data Port
Prototypes if speciﬁed.
Can be different.

writingFrequency

writeOnlyOnce

writingPriority

Can be different.

writeVerification

Can be different.

calcRamBlockCrc

Can be different.

checkStaticBlockId

Can be different.

ramBlockStatusControl Can be different.

storeAtShutdown

Can be different.

storeCyclic

Can be different.

storeEmergency

Can be different.

storeImmediate

Can be different.

NvBlockNeeds of NvBlockDescrip
tor

Recommended to be identical as re
quested by nv data PortPrototypes.

Recommended to be set to the highest
reliability class request by any mapped nv
data PortPrototypes.
Recommended to be identical as re
quested by nv data PortPrototypes.

Recommended to be identical as re
quested by nv data PortPrototypes.

Recommended to set to true if any of the
nv data PortPrototypes requests writ
ing at shutdown.
Recommended to be identical as re
quested by nv data PortPrototypes.

Recommended to be set to the highest
requested frequency of the mapped nv
data PortPrototypes.
Recommended to be set to the highest
requested frequency of the mapped nv
data PortPrototypes.
Recommended to set to true if any of
the nv data PortPrototypes requests
a write veriﬁcation.
Recommended to set to true if any of
the nv data PortPrototypes requests
a CRC calculation.
Recommended to set to true if any of
the nv data PortPrototypes requests
a check of the static block ID.
Recommended to set to true if any of
the nv data PortPrototypes requests
a use of the API for accessing the block.
Recommended to set to true if any of the
nv data PortPrototypes requests writ
ing at shutdown.
Recommended to set to true if any of
the nv data PortPrototypes requests
cyclic writing.
Recommended to set to true if any of
the nv data PortPrototypes requests
emergency writing.
Recommended to set to true if any of the
nv data PortPrototypes requests im
mediate writing.

Table 11.7: NvBlockNeeds dependencies



With respect to the completeness of table 11.7 (which intentionally doesn’t contain
a remark regarding the value of cyclicWritingPeriod), it should be noted that
(according to [TPS_SWCT_01585]) the value of NvBlockDescriptor.nvBlock
Needs.cyclicWritingPeriod shall be ignored in favor of NvBlockDescrip
tor.timingEvent.period.

Therefore, the missing statement for cyclicWritingPeriod in the spirit of table 11.7
is that the values of SwcServiceDependency.serviceNeeds.cyclicWritingPe
riod can be different from the value of NvBlockDescriptor.timingEvent.pe
riod.

It is recommended that the value of NvBlockDescriptor.timingEvent.period
shall be set to the lowest requested time value of the mapped nv data PortProto
types (implemented by SwcServiceDependency.serviceNeeds.cyclicWrit
ingPeriod).

#@SECTION: 11.5.4 NvBlockDescriptor

[TPS_SWCT_01144] NvBlockDescriptor speciﬁes the properties of exactly one
NVRAM Block (cid:100) A NvBlockDescriptor speciﬁes the properties of exactly one
NVRAM Block of a NvBlockSwComponentType.

It contains information about the requested NVRAM Block conﬁguration of the NVRAM
Manager, ramBlock and romBlock, the mapping between the PortPrototypes of
the NvBlockSwComponentType and the data inside a ramBlock as well as the role
of the clientServerPorts expressed in terms of RoleBasedPortAssignment.
(cid:99)()

NvBlockDescriptor

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::NvBlockComponent
Note
Base

Speciﬁes the properties of exactly on NVRAM Block.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
RoleBasedPort
Assignment

aggr The RoleBasedPortAssignement deﬁnes which

Attribute
clientServe
rPort

Mul. Kind Note

*

client server port of the
NvBlockSwComponentType serves for which kind
of service or notiﬁcation. In case of notiﬁcations
one common callback function is provided by the
RTE for each individual kind of notiﬁcation deﬁned
by the "role".

The aggregation of RoleBasedPortAssignment is
subject to variability with the purpose to support
the conditional existence of ports.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=preCompileTime



Attribute
constantVa
lueMappin
g

Datatype
ConstantSpecifi
cationMappingS
et

dataTypeM
apping

DataTypeMappi
ngSet

Mul. Kind Note

*

*

ref Reference to the ConstanSpeciﬁcationMapping to
be applied for the particular NVRAM Block

Stereotypes: atpSplitable
Tags: atp.Splitkey=constantValueMapping
ref Reference to the DataTypeMapping to be applied

for the particular NVRAM Block.

Stereotypes: atpSplitable
Tags: atp.Splitkey=dataTypeMapping

instantiatio
nDataDefP
rops

InstantiationDat
aDefProps

*

aggr The purpose of InstantiationDataDefProps are the

reﬁnement of some data def properties of
individual instantiations within the context of a
NvBlockSwComponentType.

nvBlockDa
taMapping

NvBlockDataMa
pping

The aggregation of InstantiationDataDefProps is
subject to variability with the purpose to support
the conditional existence of ports, component
internal memory objects and those attributes.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=preCompileTime

1..*

aggr Deﬁnes the mapping between the

VariableDataPrototypes in the
NvBlockComponents ports and the
VariableDataPrototypes of the RAM Block.

The aggregation of NvBlockDataMapping is
subject to variability with the purpose to support
the conditional existence of nv data ports.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=preCompileTime

nvBlockNe
eds

NvBlockNeeds

1

aggr Speciﬁes the abstract needs on the conﬁguration

of the NVRAM Manager for the single NVRAM
Block described by this NvBlockDescriptor.

In addition, it may deﬁne requirements for writing
strategies in an implementation of an
NvBlockSwComponentType by the RTE.

Please note that the attributes nDataSets and
nRomBlocks are not relevant for this aggregation
because the RTE will allocate just one block
anyway. In a different context, however, they do
make sense.

ramBlock

romBlock

VariableDataPr
ototype
ParameterData
Prototype

1

aggr Deﬁnes the RAM Block of the NVRAM Block

provided by NvBlockSwComponentType.

0..1 aggr Deﬁnes the ROM Block of the NVRAM Block

provided by NvBlockSwComponentType.




Attribute
supportDirt
yFlag

Datatype
Boolean

timingEven
t

TimingEvent

0..1

ref



Mul. Kind Note
0..1

attr Speciﬁes whether calling of NvM functions for

writing and/or status control of potentially modiﬁed
RAM Blocks to NV memory shall be controlled by
the RTE.
this reference can be taken to identify the
TimingEvent to be used by the RTE for
implementing a cyclic writing strategy for this block

Table 11.8: NvBlockDescriptor

For more explanation about the semantics of the attribute NvBlockDescriptor.sup
portDirtyFlag please refer to the SWS RTE [2].

Figure 11.6: NvBlockSwComponentType and NvBlockDescriptor




AtomicSwComponentTypeNvBlockSwComponentTypeAtpStructureElementIdentifiableNvBlockDescriptor+ supportDirtyFlag  :Boolean [0..1]ServiceNeedsNvBlockNeeds+ calcRamBlockCrc  :Boolean [0..1]+ checkStaticBlockId  :Boolean [0..1]+ cyclicWritingPeriod  :TimeValue [0..1]+ nDataSets  :PositiveInteger [0..1]+ nRomBlocks  :PositiveInteger [0..1]+ ramBlockStatusControl  :RamBlockStatusControlEnum [0..1]+ readonly  :Boolean [0..1]+ reliability  :NvBlockNeedsReliabilityEnum [0..1]+ resistantToChangedSw  :Boolean [0..1]+ restoreAtStart  :Boolean [0..1]+ storeAtShutdown  :Boolean [0..1]+ storeCyclic  :Boolean [0..1]+ storeEmergency  :Boolean [0..1]+ storeImmediate  :Boolean [0..1]+ useAutoValidationAtShutDown  :Boolean [0..1]+ useCRCCompMechanism  :Boolean [0..1]+ writeOnlyOnce  :Boolean [0..1]+ writeVerification  :Boolean [0..1]+ writingFrequency  :PositiveInteger [0..1]+ writingPriority  :NvBlockNeedsWritingPriorityEnum [0..1]«enumeration»NvBlockNeedsReliabilityEnum noProtection errorDetection errorCorrectionValueSpecification+ shortLabel  :Identifier [0..1]AutosarDataPrototypeParameterDataPrototypeAutosarDataPrototypeVariableDataPrototype«atpVariation» Tags:vh.latestBindingTime =preCompileTime«enumeration»RamBlockStatusControlEnum api nvRamManager«enumeration»NvBlockNeedsWritingPriorityEnum low medium highRTEEventTimingEvent+ period  :TimeValue+initValue0..1+romBlock0..1+initValue0..1+ramBlock1«atpVariation,atpSplitable»+nvBlockDescriptor0..*+timingEvent0..1+nvBlockNeeds1

[constr_1095] Values of nDataSets vs. reliability (cid:100) If the value of nDataSets
is greater than 0 the value of reliability shall not be set to errorCorrection.
(cid:99)()

The reason for the existence of [constr_1095] is that the AUTOSAR NvM [31] does not
support error correction for NV data sets.

If the value of nDataSets is equal to 0 the value of reliability can take any value
out of NvBlockNeedsReliabilityEnum.

#@SECTION: 11.5.4.1 Writing Strategies

[TPS_SWCT_01586] Writing strategies for nv data (cid:100) By setting certain attributes in
the meta-class NvBlockDescriptor it is possible to conﬁgure different writing strate
gies for the values of an RAM Block to the NVRAM storage. [constr_1310] applies.

The following use cases are supported:

• Write data cyclically. This use case requires the existence of attribute NvBlock
Descriptor.nvBlockNeeds.storeCyclic with the value true and also at
tribute NvBlockDescriptor.cyclicWritingPeriod needs to exist and have
a reasonable value.

In the context of using the attribute NvBlockDescriptor.cyclicWritingPe
riod the constraints [constr_1308] and [constr_1309] apply.

Please refer to [TPS_SWCT_01587] and Figure 11.7 for more information about
how this aspect can be conﬁgured.

• Write data immediately. This means that data send to the NvBlockSwCompo

nentType will be written immediately to NVRAM storage.

This use case corresponds to setting the value of attribute NvBlockDescrip
tor.nvBlockNeeds.storeImmediate to the value true.

Please refer to [TPS_SWCT_01588] and Figure 11.8 for more information about
how this aspect can be conﬁgured.

• Write on emergency. With this setting, data shall be written to NVRAM storage

if the ECU fails in some way.

This use case corresponds to setting the value of attribute NvBlockDescrip
tor.nvBlockNeeds.storeEmergency to true.

As explained in [TPS_SWCT_01589], setting the value of this attribute is not
sufﬁcient to achieve the intended semantics.

• Write at shutdown. Here, the data are written to NVRAM storage when the ECU

shuts down.



This use case corresponds to setting the value of attribute NvBlockDescrip
tor.nvBlockNeeds.storeAtShutdown to true.

(cid:99)(RS_SWCT_03225)

Of course, the actual implementation of the different writing strategies goes beyond
setting the value of attributes and requires the existence of dedicated RunnableEn
titys in the SwcInternalBehavior of the enclosing NvBlockSwComponentType
that are triggered in response to RTEEvents applicable for the particular use case.

[TPS_SWCT_01587] The cyclic writing of nv data requires the existence of a
TimingEvent (cid:100) The implementation of cyclic writing of nv data requires the exis
tence of a TimingEvent that can be taken to trigger a corresponding RunnableEn
tity that in turn takes care of calling the respective APIs for writing the data.
(cid:99)(RS_SWCT_03225)

This aspect is depicted in Figure 11.7.

Figure 11.7: How to model a cyclic writing strategy for nv data

[TPS_SWCT_01588] DataReceivedEvent for storing nv data immediately (cid:100) The
approach to store data immediately after reception by an NvBlockSwComponent
Type requires the activation of a RunnableEntity by a DataReceivedEvent.
(cid:99)(RS_SWCT_03225)




NvBlockSwComponentTypeAtpStructureElementIdentifiableNvBlockDescriptor+ supportDirtyFlag  :Boolean [0..1]TimingEvent+ period  :TimeValueSwComponentTypeAtomicSwComponentTypeInternalBehaviorSwcInternalBehavior+ handleTerminationAndRestart  :HandleTerminationAndRestartEnum+ supportsMultipleInstantiation  :BooleanAtpStructureElementExecutableEntityRunnableEntity+ canBeInvokedConcurrently  :Boolean+ symbol  :CIdentifierAbstractEventAtpStructureElementRTEEvent«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTime+event*«atpVariation,atpSplitable»+startOnEvent0..1+runnable1..*«atpVariation,atpSplitable»«atpVariation,atpSplitable»+internalBehavior0..1+timingEvent0..1«atpVariation,atpSplitable»+nvBlockDescriptor0..*

This approach is depicted in Figure 11.8.

Figure 11.8: How to model an immediate writing strategy for nv data

[TPS_SWCT_01589] Implementation of emergency storing of nv data (cid:100) The
use case for storeEmergency can only be implemented by means of a Complex
Driver.

In particular, the Complex Driver is responsible for the detection of an ECU failure. If
a relevant error occurs the Complex Driver should call the NvM write block operation
for the emergency blocks directly. (cid:99)(RS_SWCT_03225)

This consequently means that the NvM shall react to write operations coming from the
Complex Driver by giving them the highest priority (re-queuing of NvM write block
requests).

Please note that the behavior described in [TPS_SWCT_01587] in general is sup
ported by AUTOSAR by requiring that NVRAM Blocks shall have to be conﬁgured




NvBlockSwComponentTypeSwComponentTypeAtomicSwComponentTypeInternalBehaviorSwcInternalBehavior+ handleTerminationAndRestart  :HandleTerminationAndRestartEnum+ supportsMultipleInstantiation  :BooleanAtpStructureElementExecutableEntityRunnableEntity+ canBeInvokedConcurrently  :Boolean+ symbol  :CIdentifierAbstractEventAtpStructureElementRTEEventDataReceivedEventAutosarDataPrototypeVariableDataPrototypeSenderReceiverInterfaceDataInterfaceARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]AbstractRequiredPortPrototypeRPortPrototype«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTime+rPort«isOfType»+requiredInterface1{redefines atpType}+dataElement1..*+interface1+event«instanceRef»+data0..1+event*«atpVariation,atpSplitable»+startOnEvent0..1+runnable1..*«atpVariation,atpSplitable»«atpVariation,atpSplitable»+internalBehavior0..1

with “immediate priority”. The technical implications are explained in the respective
SWS [31], e.g. in [SWS_NvM_00182] and [SWS_NvM_00300].

[TPS_SWCT_01590] Combination of writing strategies for nv data is possible (cid:100)
AUTOSAR positively supports the conﬁguration of a combination of writing strategies
for nv data. (cid:99)(RS_SWCT_03225)

In other words, in consequence of [TPS_SWCT_01590] it is possible that (for exam
ple) both NvBlockDescriptor.storeImmediate as well as NvBlockDescrip
tor.storeCyclic may exist and set to true in the context of the same NvBlock
Needs.

#@SECTION: 11.5.4.2 NvBlockNeeds

The requested NVRAM Block conﬁguration of the NVRAM Manager is described by
the NvBlockNeeds of the NvBlockDescriptor.

This information can be evaluated during ECU conﬁguration similar to the NvBlock
Needs of an atomic software component or a BSW module. For further details see
section 7.11.3.

Figure 11.9: NvBlockNeeds

[constr_1308] Existence of NvBlockNeeds.cyclicWritingPeriod (cid:100) The at
tribute NvBlockNeeds.cyclicWritingPeriod shall exist if and only if the attribute
NvBlockNeeds.storeCyclic exists and its value is set to true. (cid:99)()




IdentifiableServiceNeedsNvBlockNeeds+ calcRamBlockCrc  :Boolean [0..1]+ checkStaticBlockId  :Boolean [0..1]+ cyclicWritingPeriod  :TimeValue [0..1]+ nDataSets  :PositiveInteger [0..1]+ nRomBlocks  :PositiveInteger [0..1]+ ramBlockStatusControl  :RamBlockStatusControlEnum [0..1]+ readonly  :Boolean [0..1]+ reliability  :NvBlockNeedsReliabilityEnum [0..1]+ resistantToChangedSw  :Boolean [0..1]+ restoreAtStart  :Boolean [0..1]+ storeAtShutdown  :Boolean [0..1]+ storeCyclic  :Boolean [0..1]+ storeEmergency  :Boolean [0..1]+ storeImmediate  :Boolean [0..1]+ useAutoValidationAtShutDown  :Boolean [0..1]+ useCRCCompMechanism  :Boolean [0..1]+ writeOnlyOnce  :Boolean [0..1]+ writeVerification  :Boolean [0..1]+ writingFrequency  :PositiveInteger [0..1]+ writingPriority  :NvBlockNeedsWritingPriorityEnum [0..1]«enumeration»NvBlockNeedsReliabilityEnum noProtection errorDetection errorCorrection«enumeration»NvBlockNeedsWritingPriorityEnum low medium high«enumeration»NvBlockComponent::RamBlockStatusControlEnum api nvRamManager

NvBlockNeeds

Speciﬁes the abstract needs on the conﬁguration of a single NVRAM Block.
ARObject,Identiﬁable,MultilanguageReferrable,Referrable,ServiceNeeds
Datatype
Boolean

Class#@CLASS: 
Package M2::AUTOSARTemplates::CommonStructure::ServiceNeeds
Note
Base
Attribute
calcRamBl
ockCrc
checkStati
cBlockId
cyclicWritin
gPeriod
nDataSets PositiveInteger

attr Deﬁnes if the Static Block Id check shall be

attr Number of data sets to be provided by the

NvData to store the associated RAM Block.

Mul. Kind Note
0..1

attr This represents the period for cyclic writing of

RAM Block is required.

TimeValue

enabled.

Boolean

attr Deﬁnes if CRC (re)calculation for the permanent

0..1

0..1

0..1

nRomBloc
ks

PositiveInteger

0..1

NVRAM manager for this block. This is the total
number of ROM Blocks and RAM Blocks.
attr Number of ROM Blocks to be provided by the

NVRAM manager for this block. Please note that
these multiple ROM Blocks are given in a
contiguous area.

ramBlockS
tatusContr
ol
readonly

reliability

resistantTo
ChangedS
w

restoreAtSt
art

storeAtShu
tdown

RamBlockStatu
sControlEnum

0..1

attr This attribute deﬁnes how the management of the

RAM Block status is controlled.

Boolean

0..1

attr True: data of this NVRAM Block are write

NvBlockNeedsR
eliabilityEnum
Boolean

0..1

Boolean

0..1

protected for normal operation (but protection can
be disabled) false: no restriction

0..1

attr Reliability against data loss on the non-volatile

medium.

attr Deﬁnes whether an NVRAM Block shall be treated
resistant to conﬁguration changes (true) or not
(false). For details how to handle initialization in
the latter case, please refer to the NVRAM
speciﬁcation.

attr Deﬁnes whether the associated RAM Block shall
be implicitly restored during startup by the basic
software.

Boolean

0..1

attr Deﬁnes whether or not the associated RAM Block

shall be implicitly stored during shutdown by the
basic software.

storeCyclic Boolean

0..1

attr Deﬁnes whether or not the associated RAM Block

storeEmer
gency

Boolean

0..1

storeImme
diate

Boolean

0..1

shall be implicitly stored periodically by the basic
software.

attr Deﬁnes whether or not the associated RAM Block
shall be implicitly stored in case of ECU failure
(e.g. loss of power) by the basic software. If the
attribute storeEmergency is set to true the
associated RAM Block shall be conﬁgured to have
immediate priority.

attr Deﬁnes whether or not the associated RAM Block
shall be implicitly stored immediately during or
after execution of the according SW-C
RunnableEntity by the basic software.



Attribute
useAutoVa
lidationAtS
hutDown
useCRCC
ompMecha
nism

Datatype
Boolean

Mul. Kind Note
attr
0..1

If set to true the RAM Block shall be auto validated
during shutdown phase.

Boolean

0..1

attr

If set to true the CRC of the RAM Block shall be
compared during a write job with the CRC which
was calculated during the last successful read or
write job in order to skip unnecessary NVRAM
writings.

writeOnlyO
nce

Boolean

0..1

attr Deﬁnes write protection after ﬁrst write: true: This
block is prevented from being changed/erased or
being replaced with the default ROM data after
ﬁrst initialization by the software-component. false:
No such restriction.

writeVerific
ation
writingFreq
uency

Boolean

0..1

attr Deﬁnes if Write Veriﬁcation shall be enabled for

PositiveInteger

0..1

this NVRAM Block.

attr Provides the amount of updates to this block from
the application point of view. It has to be provided
in "number of write access per year".

writingPrior
ity

NvBlockNeeds
WritingPriorityE
num

0..1

attr Requires the priority of writing this block in case of

concurrent requests to write other blocks.

Table 11.9: NvBlockNeeds

Enumeration NvBlockNeedsReliabilityEnum
Package
Note
#@CLASS: 
M2::AUTOSARTemplates::CommonStructure::ServiceNeeds
Reliability against data loss on the non-volatile medium. These requirements give
only a relative indication, for example on the required degree of redundancy for
storage.

They do, however, not specify by which means (e.g. software or hardware) the
reliability is actually achieved.
Description
Errors shall be corrected

Literal
errorCorrec
tion
errorDetec
tion
noProtection Data need not to be handled with protection

Errors shall be detected

Table 11.10: NvBlockNeedsReliabilityEnum

[constr_1310] Existence of attributes of meta-class NvBlockNeeds (cid:100) If in the
context of an ApplicationSwComponentType the attribute SwcServiceDepen
dency.serviceNeeds is implemented by an NvBlockNeeds then the following at
tributes

• NvBlockNeeds.storeCyclic

• NvBlockNeeds.cyclicWritingPeriod



• NvBlockNeeds.storeEmergency

• NvBlockNeeds.storeImmediate

shall only exist if in the context of the same SwcServiceDependency a SwcSer
viceDependency.assignedPort exists that has the attribute role set to the value
NvDataPort. (cid:99)()

#@SECTION: 11.5.4.3 RAM Block and ROM Block

[TPS_SWCT_01145] ramBlock and the romBlock are described by a Vari
ableDataPrototype and a ParameterDataPrototype (cid:100) The ramBlock and the
romBlock are described by a VariableDataPrototype and a ParameterDat
aPrototype which are typed by an AutosarDataType. (cid:99)()

[TPS_SWCT_01146] romBlock is optional (cid:100) The romBlock is optional.
If a
romBlock is conﬁgured the RTE copies the romBlock constants into the RAM Block
in case of a block initialization notiﬁcation (NvMNotifyInitBlock ). (cid:99)()

[TPS_SWCT_01147] No romBlock is conﬁgured (cid:100) If there is no romBlock conﬁg
ured the connected software components are either required to offer this functionality
by a proper implementation of block initialization notiﬁcation or the NVRAM Block has
to be conﬁgured, that no ROM Block is needed. (cid:99)()

As a mitigation against a failed read operation from NV memory it is recommended to
always deﬁne a romBlock with suitable initial values to ensure the proper initialization
of the corresponding ramBlock.

In particular, for software-components that don’t deﬁne a PortPrototype typed by
the ClientServerInterface with the standardized shortName NotifyInit
Block [31] it may happen that the ramBlock might not be properly initialized in case
of failure.

[constr_2012] Compatibility of ImplementationDataTypes used for ramBlock
and romBlock (cid:100)

The ramBlock and the romBlock shall have compatible Implementation
DataTypes to ensure, that the NVRAM Block default values in the ROM Block can
be copied into the RAM Block.

(cid:99)()

Additionally it is possible that RAM Block and ROM Block are deﬁned to be able
to calibrate or measurable. Preceding SwDataDefProps might be deﬁned with the
means of an InstantiationDataDefProps.



#@SECTION: 11.5.4.4 NvBlockDataMapping

[TPS_SWCT_01148] NvBlockDataMapping (cid:100) The meta-class NvBlockDataMap
ping speciﬁes the mapping of VariableDataPrototypes of the NvBlockSwCom
ponentType’s ports (PPortPrototypes / RPortPrototypes) to VariableDat
aPrototypes inside the RAM Block. (cid:99)()

This ensures a ﬂexible but deterministic NVRAM Block memory structure given by the
ImplementationDataType of the ramBlock and romBlock and its association to
the PortPrototypes of the NvBlockSwComponentType.

[constr_2013] Compatibility of ImplementationDataTypes for NvBlock
DataMapping (cid:100) The NvBlockDataMapping is only valid if
the Implementa
tionDataType of the referenced VariableDataPrototype or Implementation
DataTypeElement in the role nvRamBlockElement is compatible to the Im
plementationDataType used to type the VariableDataPrototype aggregated
by NvBlockDataMapping in the role writtenNvData, writtenReadNvData, or
readNvData. (cid:99)()

[constr_1285] Applicability of roles vs. PortPrototypes (cid:100) The aggregation of Au
tosarVariableRef aggregated by NvBlockDataMapping in the roles written
NvData, writtenReadNvData, or readNvData is subject to limitation depending on
the applicable subclass of PortPrototype:

• The role writtenNvData shall only be used if the corresponding PortProto

type is a RPortPrototype

• The role writtenReadNvData shall only be used if the corresponding Port

Prototype is a PRPortPrototype

• The role readNvData shall only be used if the corresponding PortPrototype

is a PPortPrototype

(cid:99)()

But nevertheless it is valid, that not all ImplementationDataTypeElements within
the VariableDataPrototype aggregated by NvBlockDescriptor in the role
ramBlock are mapped to a VariableDataPrototype located in a PortProto
type.

This enables to have ﬁll elements or logistic data in the NVRAM Block which are
not accessed by software components. This is exempliﬁed by the element x in Fig
ure 11.10.

Please note that the VariableDataPrototype located in the PortPrototype, in
the vast majority of cases, will be typed by an ApplicationDataType which in turn
(at least before the actual code generation starts) ﬁnally shall have a mapping to an
ImplementationDataType. This aspect is explained in chapter 5.2.2.

[TPS_SWCT_01659] Mapping of VariableDataPrototype to a NvBlockDe
scriptor (cid:100) There are three ways to map a VariableDataPrototype (i.e. Nv



DataInterface.nvData in the context of a speciﬁc PortPrototype) to either an
NvBlockDescriptor.ramBlock or a sub-element thereof:

• NvDataInterface.nvData is directly and completely mapped, i.e. Autosar
VariableRef.autosarVariable shall exist and autosarVariable.tar
getDataPrototype shall refer to the NvDataInterface.nvData.

• Every leaf element of NvDataInterface.nvData is mapped individually. This

means that either

– AutosarVariableRef.autosarVariableInImplDatatype shall exist
and autosarVariableInImplDatatype.targetDataPrototype shall
refer to the respective leaf element of NvDataInterface.nvData.

– AutosarVariableRef.autosarVariable shall exist and autosar
Variable.targetDataPrototype shall refer to the respective leaf ele
ment of NvDataInterface.nvData.

In other words: the mapping shall be deﬁned either via the used Implementa
tionDataType or else via the used ApplicationDataType.

• A sub-element of NvDataInterface.nvData - which is not a leaf element 
may be directly mapped and consequently all the leaf elements of the respec
tive sub-element of NvDataInterface.nvData are indirectly mapped as well.
This means that

– AutosarVariableRef.autosarVariableInImplDatatype shall exist
and autosarVariableInImplDatatype.targetDataPrototype shall
refer to the sub-element element of NvDataInterface.nvData.

– AutosarVariableRef.autosarVariable shall exist and autosar
Variable.targetDataPrototype shall refer to the sub-element element
of NvDataInterface.nvData.

In other words: the mapping shall be deﬁned either via the used Implementa
tionDataType or else via the used ApplicationDataType.

(cid:99)()

Please note that a mixing of mutually exclusive mappings for entire sub-elements
or leaf elements as described by [TPS_SWCT_01659] is positively supported (see
Figure 11.10).



Figure 11.10: Example NvBlockDataMapping to explain [TPS_SWCT_01659]

[constr_1395] NvBlockDataMapping shall be complete (cid:100) If an NvBlock
DataMapping refers to sub-elements or leaf elements of the NvDataInterface.nv
Data in the context of a particular PortPrototype then all remaining sub-elements
or leaf elements shall effectively be mapped according to [TPS_SWCT_01659] by
means of a collection of NvBlockDataMappings. (cid:99)()

[constr_1403] NvBlockDataMappings to a given nvData shall be unambigu
ous (cid:100) If an NvBlockDataMapping exists that directly and completely maps a spe
ciﬁc NvDataInterface.nvData in the context of a particular PortPrototype then
no other NvBlockDataMapping which maps sub-elements of the NvDataInter
face.nvData shall exist. (cid:99)()

The interaction with AUTOSAR services is centrally deﬁned in the context of the Swc
ServiceDependency. The latter gathers a collection of PortPrototypes by means
of RoleBasedPortAssignments that implement a closely related service functional
ity.

In the speciﬁc case of interaction between AtomicSwComponentType and NvBlock
SwComponentType (as described by [TPS_SWCT_02503]), there are PortProto
types referenced by a RoleBasedPortAssignment with attribute RoleBasedPor
tAssignment.role set to NvDataPort. These PortPrototypes contain the col
lected Nv Data of the service use case.

Furthermore, there is the possibility to receive notiﬁcations when the writing of the
mapped NV Block to the NvRam is ﬁnished.




NvBlockSwComponent <<NvDataInterface>>  nvData:  a : uint8 b : uint32 g : {      - h : uint16      - j : uint8      - s : {             - u : uint32             - w : uint8      }  nvData root element: -a, b, g  leaf element: -a, b, h, j, u, w  sub-element which is not a leaf element: -s NvBlockDescriptor ramBlock: { b : uint32 s : {      - u : uint32      - w : uint8      } x : uint8 h : uint16 a : uint8 j : uint8 }  Example NvDataMapping nvData ramBlock mapping kind a a nvData root b b nvData root h h leaf element j j leaf element s s sub-element 

In order to be able to properly assign such a notiﬁcation to the content of the related
Nv Data PortPrototypes in the scope of the same SwcServiceDependency it is
necessary that the Nv Data of all these PortPrototypes is mapped to the same Nv
Block (because the notiﬁcations are created per block).

This motivates the existence of [constr_1404]:

[constr_1404] All NvDataInterface.nvData of PortPrototypes in the context
of a speciﬁc SwcServiceDependency shall be mapped to the same NvBlock
Descriptor (cid:100) In the context of a given SwcServiceDependency (which, in turn, is
owned by an AtomicSwComponentType), all NvDataInterface.nvData of Port
Prototypes referenced by a RoleBasedPortAssignment with attribute Role
BasedPortAssignment.role set to NvDataPort shall be connected (either di
rectly or via the deﬁnition of suitable PortInterfaceMappings) to NvDataInter
face.nvData (on the side of the NvBlockSwComponentType) that are completely
mapped (via NvBlockDataMappings) to the identical NvBlockDescriptor.ram
Block. (cid:99)()

Figure 11.11: Visualization of the statement made by [constr_1404]

The statement made by [constr_1404] is visualized in Figure 11.11. The context
deﬁning model elements, i.e. SwcServiceDependency owned by the Atomic



SwComponentType as well as NvBlockDescriptor owned by the NvBlockSwCom
ponentType, are colored in light orange.

The diagram is focused on the NvBlockDescriptor.ramBlock. As stressed by
[constr_1404], all Nv Data provided by the PortPrototypes referenced by the spe
ciﬁc SwcServiceDependency ﬁnally ends up in the one depicted ramBlock (colored
in blue).

Please note that the graphical representation of the NvBlockDataMapping in Fig
ure 11.11 has been simpliﬁed for the sake of clarity.

NvBlockDataMapping

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::NvBlockComponent
Note

Deﬁnes the mapping between the VariableDataPrototypes in the
NvBlockComponents ports and the VariableDataPrototypes of the RAM Block.

Base
Attribute
nvRamBlo
ckElement
readNvDat
a

Mul. Kind Note

The data types of the referenced VariableDataPrototypes in the ports and the
referenced sub-element (inside a CompositeDataType) of the VariableDataPrototype
representing the RAM Block shall be compatible.
ARObject
Datatype
AutosarVariable
Ref
AutosarVariable
Ref

aggr Reference to a VariableDataPrototype of a RAM

0..1 aggr Reference to a VariableDataPrototype of a pPort
of the NvBlockComponent providing read access
to the RAM Block.If there is no PortPrototype
providing read access (write-only) the reference
can be omitted.

Block.

1

writtenNvD
ata

AutosarVariable
Ref

writtenRea
dNvData

AutosarVariable
Ref

0..1 aggr Reference to a VariableDataPrototype of a rPort of

the NvBlockComponent providing write access to
the RAM Block. If there is no port providing write
access (read-only) the reference can be omitted.

0..1 aggr Reference to a VariableDataPrototype of a

PRPortPrototype of the
NvBlockSwComponentType providing write and
read access to the RAM Block.

Table 11.11: NvBlockDataMapping



Figure 11.12: NvBlockToPortMapping and InstantiationDataDefProps

#@SECTION: 11.5.4.5 Client Server Ports

[TPS_SWCT_01149] RoleBasedPortAssignment of NvBlockDescriptor (cid:100) The
clientServerPort of
the NvBlockDescriptor describes which client/server
PortPrototype of the NvBlockSwComponentType serves for which purpose. The




AtomicSwComponentTypeNvBlockSwComponentTypeDataInterfaceNvDataInterfaceAtpStructureElementIdentifiableNvBlockDescriptorNvBlockDataMappingInstantiationDataDefPropsVariableDataPrototypeAutosarVariableRef«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTimeArVariableInImplementationDataInstanceRefIdentifiableImplementationDataTypeElementAtpBlueprintAtpBlueprintableImplementationDataTypeARElementAtpTypeAutosarDataTypeDataPrototypeAutosarDataPrototypeAtpInstanceRefVariableInAtomicSWCTypeInstanceRef«atpVariation» Tags:vh.latestBindingTime =preCompileTime+autosarVariable0..1+variableInstance0..1«atpVariation,atpSplitable»+nvBlockDescriptor0..*+nvBlockDataMapping1..*«atpVariation»+writtenReadNvData0..1+nvData1..*+ramBlock1+instantiationDataDefProps0..*«atpVariation»+readNvData0..1+rootVariableDataPrototype0..1{subsets atpContextElement}+autosarVariableInImplDatatype0..1+nvRamBlockElement1+targetDataPrototype1+contextDataPrototype0..*{ordered}+rootVariableDataPrototype0..1«atpVariation»+subElement0..* {ordered}«isOfType»+type1{redefines atpType}+writtenNvData0..1

role speciﬁes if the port serves for block-related services, administrative services or
notiﬁcation. (cid:99)()

[constr_2014] Limitation of RoleBasedPortAssignment.role in NvBlockDe
scriptors (cid:100) The role has to be set to a valid name of the Standardized AUTOSAR
Interface used for the NVRAM Manager e.g. NvMNotifyJobFinished or NvMNotifyInit
Block. (cid:99)()

In case of notiﬁcations one common callback function is provided by the RTE for each
individual kind of notiﬁcation deﬁned by the role.

Figure 11.13: NvBlockNotiﬁcation




NvBlockSwComponentTypeARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypePPortPrototypeRPortPrototypeARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]RoleBasedPortAssignment+ role  :IdentifierAtpStructureElementIdentifiableNvBlockDescriptor+ supportDirtyFlag  :Boolean [0..1]ClientServerInterfaceAtpStructureElementIdentifiableClientServerOperation«atpVariation» Tags:vh.latestBindingTime =preCompileTimeAtomicSwComponentType«atpVariation» Tags:vh.latestBindingTime =preCompileTimeAbstractProvidedPortPrototypeAbstractRequiredPortPrototypePRPortPrototype+port0..*«atpVariation,atpSplitable»+clientServerPort0..*«atpVariation»+portPrototype1«isOfType»+requiredInterface1{redefines atpType}«atpVariation,atpSplitable»+nvBlockDescriptor0..*+operation1..*«atpVariation»«isOfType»+providedInterface1{redefines atpType}«isOfType»+providedRequiredInterface1{redefines atpType}

#@SECTION: 11.5.5 SwcInternalBehavior of an NvBlockSwComponentType

[TPS_SWCT_01150] InternalBehavior of a NvBlockSwComponentType to en
able access to the NVRAM Block management API (cid:100) In general, the InternalBe
havior of a NvBlockSwComponentType is only used for a limited scope.

The main use case is that the NvBlockSwComponentType deﬁnes PPortProto
types typed by a ClientServerInterface to enable access to the NVRAM Block
management API.

To enable the conﬁguration of the server invocation in the RTE’s ECU conﬁguration,
the NvBlockSwComponentType needs to provide the following model elements:

• OperationInvokedEvents

• server RunnableEntity

• PortDefinedArgumentValues to deﬁne the NVRAM Block ID which has to

be passed to the NvM

In addition to the above list further model elements may qualify; the details are ex
plained in [TPS_SWCT_01584]. (cid:99)()

[TPS_SWCT_01584] InternalBehavior of a NvBlockSwComponentType for im
plementing a writing strategy (cid:100) For the use case that NvBlockDescriptors ex
ists that aggregate NvBlockNeeds which, in turn, deﬁne particular NV data writ
ing strategies (by deﬁning any of the attributes storeAtShutdown, storeImmedi
ate, storeEmergency, or storeCyclic) the InternalBehavior of a NvBlock
SwComponentType needs to support further model elements.

Particularly, In addition to the model elements listed in [TPS_SWCT_01150], the fol
lowing list of model elements can be used in the InternalBehavior of a NvBlock
SwComponentType for implementing writing strategies:

• TimingEvents (which may include references to ModeDeclarations in the

role disabledMode)

• DataReceivedEvents (which may include references to ModeDeclarations

in the role disabledMode)

• SwcModeSwitchEvents

• RunnableEntitys

(cid:99)(RS_SWCT_03225)



Figure 11.14: NvBlockSwComponentType and SwcInternalBehavior

[TPS_SWCT_01152] InternalBehavior does not have further attributes (cid:100) It is
not expected, that such InternalBehavior do have further attributes like Exclu
siveAreas, per-instance memory or inter-runnable variables, etc. (cid:99)()

[TPS_SWCT_01151] RunnableEntitys do not have further attributes (cid:100) The same
condition exists for the RunnableEntitys of such InternalBehavior which shall




NvBlockSwComponentTypeARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeAtpBlueprintableAtpPrototypePortPrototypeARElementAtpBlueprintAtpBlueprintableAtpTypePortInterface+ isService  :Boolean+ serviceKind  :ServiceProviderEnum [0..1]RoleBasedPortAssignment+ role  :IdentifierAtpStructureElementIdentifiableNvBlockDescriptor+ supportDirtyFlag  :Boolean [0..1]ClientServerInterfaceAtpStructureElementIdentifiableClientServerOperationInternalBehaviorSwcInternalBehaviorAtpStructureElementExecutableEntityRunnableEntityOperationInvokedEventAbstractEventAtpStructureElementRTEEventAtomicSwComponentTypePortDefinedArgumentValuePortAPIOption«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTimeRelation of PortPrototype to PortInterface is documented elsewhere.«atpVariation» Tags:vh.latestBindingTime =blueprintDerivationTime«atpVariation» Tags:vh.latestBindingTime =preCompileTime«instanceRef»+operation+clientServerPort0..*«atpVariation»+portPrototype1+portArgValue0..*{ordered}+portAPIOption0..*«atpVariation,atpSplitable»0..1+port1«atpVariation,atpSplitable»+internalBehavior0..1+operation1..*«atpVariation»+runnable1..*«atpVariation,atpSplitable»+startOnEvent0..1+event*«atpVariation,atpSplitable»«atpVariation,atpSplitable»+nvBlockDescriptor0..*+port0..*«atpVariation,atpSplitable»+component

not deﬁne further attributes, e.g. data access points (implemented by means of refer
ences from SwcInternalBehavior to VariableAccess) or ServerCallPoints.
(cid:99)()

[constr_1234] Value of RunnableEntity.symbol (cid:100) The value of a RunnableEn
tity.symbol owned by an NvBlockSwComponentType that is triggered by an Op
erationInvokedEvent shall only be taken from the set of API names associated
with the NvM. (cid:99)()

For example, RunnableEntity.symbol owned by an NvBlockSwComponentType
could rightfully be set to NvM_ReadBlock [31] but an arbitrary value like ReadThis
Block is not permitted.

The rationale for [constr_1234] is that the RunnableEntitys that are triggered by an
OperationInvokedEvent are not existing as such but are mapped to the respective
function calls of the NvM. For more details of how this mapping can be achieved please
refer to [7].

Please note that no restriction applies for the value of attribute RunnableEn
tity.symbol of any RunnableEntity owned by an NvBlockSwComponentType
that is triggered by an RTEEvent other than OperationInvokedEvent.

[constr_2015] Limitation of SwcInternalBehavior of a NvBlockSwComponent
Type (cid:100) The SwcInternalBehavior of a NvBlockSwComponentType is only per
mitted to deﬁne

• OperationInvokedEvents

• RunnableEntitys
RunnableEntitys)

triggered

by

OperationInvokedEvents

(server

• RunnableEntitys which deﬁnes only the mandatory attributes symbol and

canBeInvokedConcurrently

• PortAPIOptions deﬁning PortDefinedArgumentValues

• TimingEvents (which may include references to ModeDeclarations in the

role disabledMode)

• DataReceivedEvents (which may include references to ModeDeclarations

in the role disabledMode)

• SwcModeSwitchEvents

• RunnableEntitys triggered by TimingEvents

• RunnableEntitys triggered by DataReceivedEvents

• RunnableEntitys triggered by SwcModeSwitchEvents

(cid:99)()



[constr_1309] Existence of NvBlockDescriptor.timingEvent (cid:100) The attribute
NvBlockDescriptor.timingEvent shall exist if and only if the NvBlockDescrip
tor.nvBlockNeeds.storeCyclic exists and is set to the value true. (cid:99)()

Note that there is a conceptual connection between the values of the two attributes
NvBlockDescriptor.timingEvent.period and SwcServiceDependency.ser
viceNeeds.cyclicWritingPeriod.

the SwcServiceDependency.serviceNeeds.cyclicWritingPe
Speciﬁcally,
riod represents a requirement and the NvBlockDescriptor.timingEvent.pe
riod is supposed to fulﬁll the requirement.

[TPS_SWCT_01585] Relevance of NvBlockDescriptor.timingEvent.period (cid:100)
For any given NvBlockDescriptor, the value of the attribute NvBlockDescrip
tor.nvBlockNeeds.cyclicWritingPeriod shall be ignored and the value of
NvBlockDescriptor.timingEvent.period shall be taken to specify the effective
writing frequency for cyclic storage. (cid:99)(RS_SWCT_03225)



#@SECTION: 12 Software Component Documentation

AUTOSAR supports documentation of software component types by adopting the prin
ciples of ASAM-FSX [43] Standard to AUTOSAR. With AUTOSAR Release 4.0 the
AUTOSAR XML schema provides support for integrated and well structured documen
tation. More details about the AUTOSAR Documentation Support Concept can be
found in the AUTOSAR Generic Structure Template [12].

[TPS_SWCT_01062] Documentation of software-components (cid:100) As shown in ﬁg
the documentation of a software component is composed of sev
ure 12.1,
eral chapters.
from
Some chapters are predeﬁned, describing the component
the perspective of different activities performed on the component
like testing it
(swTestDesc), maintaining it (swMaintenanceNotes), calibrating it (swCalibra
tionNotes) or performing diagnostic (swDiagnosticsNotes) on the component.
(cid:99)(RS_SWCT_02110, RS_SWCT_03230)

Two other predeﬁned chapters describe the component (swFeatureDesc) and deﬁne
its physical functionality (swFeatureDef). In order to describe additional aspects of a
software component, an arbitrary number of free chapters can be deﬁned.

The predeﬁned chapters typically provide informal guideline (e.g., recommendation) or
documentation. Formal information can be captured using special data groups [12] or
annotating documentation construct with semantic information. This could be used to
extend the predeﬁned chapters or in separate free chapters.

Note that the documentation of a software component can be stored in a different ﬁle
than the component itself (i.e., it is (cid:28)atpSplitable(cid:29) from the component).

Each of the predeﬁned and free chapters follows the (cid:28)atpVariation(cid:29) stereotype
to support variant handling (see [12]) on the documentation at the chapter level. These
variation points have a post-build as latest binding time, because the decision to include
or exclude a chapter as well as the decision which variant of this chapter should be
included can be made when the component has been built.



Figure 12.1: Software component documentation

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::SoftwareComponent

SwComponentDocumentation

Note

Base
Attribute

Documentation
This class speciﬁes the ability to write dedicated documentation to a component type
according to ASAM FSX.
ARObject
Datatype

Mul. Kind Note




SwComponentDocumentationAARElementAtpBlueprintAtpBlueprintableAtpTypeSwComponentTypeIdentifiablePaginateableChapter+ helpEntry  :String [0..1]«atpSplitable» Tags:vh.latestBindingTime = preCompileTime«atpVariation» Tags:vh.latestBindingTime =postBuild+swMaintenanceNotes0..1«atpVariation»+chapter0..*+swDiagnosticsNotes0..1+swTestDesc0..1+swFeatureDef0..1+swCarbDoc0..1+swFeatureDesc0..1+swCalibrationNotes0..1«atpSplitable,atpVariation»+swComponentDocumentation0..1

Attribute
chapter

Datatype
Chapter

Mul. Kind Note

*

aggr These chapters provide additional information

about the software component that do not ﬁt in the
other chapters.

Note that this is subject to variation because
Chapter aggregations in the role chapter are
variant within the documentation in general.

Stereotypes: atpVariation
Tags: vh.latestBindingTime=postBuild
xml.roleElement=true; xml.roleWrapper
Element=false; xml.sequenceOffset=100; xml.type
Element=false

swCalibrati
onNotes

swCarbDo
c

Chapter

0..1 aggr This element contains calibration instructions and

hints for a calibration engineer.

Tags: xml.roleElement=true; xml.sequence
Offset=60; xml.typeElement=false

Chapter

0..1 aggr This element records the documentation

requested by CARB.

swDiagnos
ticsNotes

Chapter

Tags: xml.roleElement=true; xml.sequence
Offset=80; xml.typeElement=false
0..1 aggr This element contains general information about

diagnostics issues within the component.

swFeature
Def

Chapter

0..1 aggr This element contains the deﬁnition of the physical

Tags: xml.roleElement=true; xml.sequence
Offset=75; xml.typeElement=false

functionality of this software component. This
deﬁnition is more or less formal and is intended to
be delivered from modeling tools.

swFeature
Desc

Chapter

swMainten
anceNotes

Chapter

swTestDes
c

Chapter

Tags: xml.roleElement=true; xml.sequence
Offset=20; xml.typeElement=false
0..1 aggr This element contains the textual description of

the software functionality of this software
component. Expert should write this description.

Tags: xml.roleElement=true; xml.sequence
Offset=30; xml.typeElement=false
0..1 aggr This element contains information regarding the

software maintenance of the component.

Tags: xml.roleElement=true; xml.sequence
Offset=70; xml.typeElement=false
0..1 aggr This element contains suggestions and hints for

the test of the software functionality of this
software component.

Tags: xml.roleElement=true; xml.sequence
Offset=50; xml.typeElement=false



Attribute

Datatype

Mul. Kind Note

Table 12.1: SwComponentDocumentation



#@SECTION: 13 Rapid Prototyping Scenarios

#@SECTION: 13.1 Deﬁnition of Rapid Prototyping Scenario

A Rapid Prototyping Scenario consist out of two main aspects: The description of
the byPassPoints and the relation to a rptHook. A Rapid Prototyping Scenario
is structured by means of RptContainers. The correct usage of RptContainer
structure is described in 13.2.

Figure 13.1: Rapid Prototyping Scenario




ARElementAtpStructureElementSystem+ containerIPduHeaderByteOrder  :ByteOrderEnum [0..1]+ ecuExtractVersion  :RevisionLabelString [0..1]+ pncVectorLength  :PositiveInteger [0..1]+ pncVectorOffset  :PositiveInteger [0..1]+ systemVersion  :RevisionLabelStringARElementRapidPrototypingScenarioIdentifiableRptContainerAtpInstanceRefAnyInstanceRefRptHook+ codeLabel  :CIdentifier [0..1]+ mcdIdentifier  :NameToken [0..1]Sdg+ gid  :NameToken«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation,atpSplitable»+rptContainer1..*«atpSplitable»+rptSystem0..1+hostSystem1«atpVariation,atpSplitable»+rptHook0..1«atpVariation,atpSplitable»+byPassPoint1«atpVariation,atpSplitable»+rptContainer 0..*+sdg0..*+rptArHook0..1

RapidPrototypingScenario

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::RPTScenario
Note

This meta class provides the ability to describe a Rapid Prototyping Scenario. Such a
Rapid Prototyping Scenario consist out of two main aspects, the description of the
byPassPoints and the relation to an rptHook.

Base

Attribute
hostSyste
m
rptContain
er

Tags: atp.recommendedPackage=RapidPrototypingScenarios
ARElement,ARObject,CollectableElement,Identiﬁable,Multilanguage
Referrable,PackageableElement,Referrable
Datatype
System

Mul. Kind Note

1

ref System which describes the software components

RptContainer

1..*

aggr Top-level rptContainer deﬁnitions of this speciﬁc

rapid prototyping scenario.

of the host ECU.

rptSystem System

0..1

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=preCompileTime
ref System which describes the rapid prototyping
algorithm in the format of AUTOSAR Software
Components.

Stereotypes: atpSplitable
Tags: atp.Splitkey=rptSystem

Table 13.1: RapidPrototypingScenario

RptContainer

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::RPTScenario
Note

This meta class deﬁnes a byPassPoint and the relation to a rptHook.

Additionally it may contain further rptContainers if the byPassPoint is not atomic. For
example a byPassPoint refereing to a RunnableEntity may contain rptContainers
referring to the data access points of the RunnableEntity.

Base
Attribute
byPassPoi
nt

The RptContainer structure on M1 shall follow the M1 structure of the Software
Component Descriptions. The category attribute denotes which level of the Software
Component Description is annotated.
ARObject,Identiﬁable,MultilanguageReferrable,Referrable
Datatype
AtpFeature

iref byPassPoint desribes the required preparation of

Mul. Kind Note

1

the host ECU. At a byPassPoint the host ECU
shall be capable to communicate with a RPT
System in order to support the execution of the
rapid prototyping algorithms with the original data
calculated by the host system and to replace
dedicated results of the host system by the results
of the rapid prototyping algorithm.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=byPassPoint
vh.latestBindingTime=preCompileTime



Attribute
rptContain
er

Datatype
RptContainer

Mul. Kind Note

*

aggr Sub-level rptContainer deﬁnitions of this speciﬁc

rapid prototyping scenario.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=shortName, variation
Point.shortLabel
vh.latestBindingTime=preCompileTime

rptHook

RptHook

0..1 aggr The rptHook describes the link between a

byPassPoint and the rapid prototyping algorithm.

Stereotypes: atpSplitable; atpVariation
Tags: atp.Splitkey=rptHook, variationPoint.short
Label
vh.latestBindingTime=preCompileTime

Table 13.2: RptContainer

RptHook

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::RPTScenario
Note

This meta class provide the ability to describe a rapid prototyping hook. This can
either be described by an other AUTOSAR system with the category RPT_SYSTEM
or as a non AUTOSAR software.
ARObject
Base
Datatype
Attribute
codeLabel CIdentifier

ref This attribute provides a code label which is used

Mul. Kind Note
0..1

in the implementation of the hook. For example
this can be an C function name or the name of
data deﬁnition.

NameToken

mcdIdentifi
er
rptArHook AtpFeature

0..1

attr This attribute provides an identiﬁer which shall be

used in a MCD System to display the Rpt Hook.

0..1

iref This describes the hook with the means of another

sdg

Sdg

AUTOSAR system.

*

aggr This property allows to keep special data which is
not represented by the standard model. It can be
utilized to keep e.g. tool speciﬁc data.

Table 13.3: RptHook

[TPS_SWCT_02046] byPassPoint speciﬁes the rapid prototyping capability (cid:100)
The byPassPoints are used to describe the preparation of the host ECU. At the
byPassPoints the host ECU shall be capable to communicate with a RPT System in
order to support the execution of the rapid prototyping algorithms with the original data
calculated by the host system and to replace dedicated results of the host system by
the results of the rapid prototyping algorithm. (cid:99)(RS_SWCT_03280)

[TPS_SWCT_02047] rptHook speciﬁes the link to rapid prototyping algorithm (cid:100)
The rptHook describes the link between the byPassPoint and the rapid prototyp
If the rapid prototyping algorithm is described as an AUTOSAR Soft
ing algorithm.



ware Component the rptArHook reference is applicable. Otherwise the deﬁnition of
a codeLabel and optionally mcdIdentifier shall be used. (cid:99)(RS_SWCT_03280)

In order to describe an RPT system as AUTOSAR software component a System with
the category RPT_SYSTEM shall be deﬁned.

[constr_2054] Valid targets of rptSystem (cid:100) The System referenced in the role rpt
System shall be of category RPT_SYSTEM. (cid:99)()

#@SECTION: 13.2 Usage of RptContainers on M1

The RptContainer structure on M1 shall follow the M1 structure of the Software
Component Descriptions. The category attribute denotes which level of the Software
Component Description is annotated.

The following values of the attribute category are predeﬁned by the AUTOSAR stan
dard:

Category
SW_COMPO
NENT_PROTOTYPE

Meaning
Adds one SwComponentPrototype
to an Rapid Prototyping Scenario.

DATA_PROTOTYPE

Adds one instance of a DataProto
type to an Rapid Prototyping Sce
nario.

RUNNABLE_ENTITY Adds one RunnableEntity to an

Rapid Prototyping Scenario.

ACCESS_POINTS

one

VariableAccess,
Adds
ParameterAccess, ServerCall
AsynchronousServer
Point,
CallResultPoint,
Internal
TriggeringPoint, ModeSwitch
Point,
or
ExternalTriggeringPoint to an
Rapid Prototyping Scenario.

ModeAccessPoint

Speciﬁc properties
The byPassPoint and rptArHook
shall reference a SwComponentPro
totypes.
The byPassPoint and rptArHook
shall reference a DataPrototype in
stances in PortPrototypes
The byPassPoint and rptArHook
shall reference a RunnableEntity
instances.
The byPassPoint and rptArHook
shall reference a VariableAccess,
ParameterAccess, ServerCall
Point,
AsynchronousServer
Internal
CallResultPoint,
TriggeringPoint, ModeSwitch
Point,
or
ExternalTriggeringPoint
in
stances.

ModeAccessPoint

Table 13.4: Category of RptContainers

[constr_2055] Valid targets of byPassPoint and rptHook reference (cid:100) Depending
on the category value the targets of byPassPoint and rptHook references are
restricted according table 13.4. (cid:99)()

Hereby, the following semantic applies:

[TPS_SWCT_02048] Implicit SwComponentPrototype selection for Rapid Proto
typing Scenario (cid:100) If a SwComponentPrototype is referenced in the role byPass
Point by a RptContainer without further “Sub” rptContainer all RTE Interfaces
of the AtomicSwComponentType shall be able to support a connection to a rptHook.
(cid:99)(RS_SWCT_03280)



[TPS_SWCT_02049] Implicit RunnableEntity selection for Rapid Prototyp
ing Scenario (cid:100) If a RunnableEntity is referenced in the role byPassPoint
by a RptContainer without
“Sub” rptContainer all RTE Interfaces
the RunnableEntity shall be able to support a connection to a rptHook.
of
(cid:99)(RS_SWCT_03280)

further

[TPS_SWCT_02050] Explicit access point selection for Rapid Prototyping
Scenario (cid:100) If a VariableAccess, ParameterAccess, ServerCallPoint,
AsynchronousServerCallResultPoint, InternalTriggeringPoint, Mod
eSwitchPoint, ModeAccessPoint or ExternalTriggeringPoint is referenced
in the role byPassPoint by a RptContainer only RTE Interfaces related to the
speciﬁc access point are required be able to support a connection to a rptHook.
(cid:99)(RS_SWCT_03280)

[TPS_SWCT_02051] Explicit DataPrototype selection for Rapid Prototyping
Scenario (cid:100) If a DataPrototype instances in a PortPrototypes is referenced in
the role byPassPoint by a RptContainer only RTE Interfaces related to the spe
ciﬁc DataPrototype are required be able to support a connection to a rptHook.
(cid:99)(RS_SWCT_03280)

[constr_2056] Consistency of RapidPrototypingScenario with respect to
rptSystem and rptArHook references (cid:100) Within one RapidPrototypingSce
nario all rptSystem references shall point to instances in one and only one System
and if existent all rptArHook shall point to instances in one other and only one other
System. (cid:99)()

#@SECTION: 13.3 Usage of atpSplitable for RptContainers on M1

In order to support the later deﬁnition of the RptHooks, which may require as well
the detailed speciﬁcation byPassPoints, the aggregation of RptContainer and
RptHook is (cid:28)atpSplitable(cid:29).

[TPS_SWCT_02052] Deﬁnition of Rapid Prototyping Scenario is splittable (cid:100)
Aggregation of RptContainer, byPassPoint and rptHook using stereotype
(cid:28)atpSplitable(cid:29). By this means it is possible to generally specify the deﬁnition
the RptHooks in a later process step. (cid:99)(RS_SWCT_03280)

Please note that the later speciﬁcation of RptHooks may require additional byPass
Points as well to show their relation ship to lower level elements in a component
description, such as VariableAccess where in contrast the byPassPoints may
only speciﬁed on higher level elements such as SwComponentPrototypes in a ﬁrst
step.



#@SECTION: 13.4 Modiﬁcations of the Meta-Model for supporting the RPT sce

nario

The implementation of the rapid-pro typing scenario implies the deﬁnition of access
points (see table 13.4). To be able to fulﬁll this role, the access points shall be repre
sented by meta-classes derived from Referrable.

Most candidates for becoming access points are already inheriting from Referrable
and therefore do not require further treatment (see Figure 13.2). Two meta-classes in
this collection, however, are not derived from Referrable:

• ExternalTriggeringPoint

• ModeAccessPoint

It is not feasible to ﬁx this issue by simply letting the two meta-classes inherit from
Referrable because this would break the backwards compatibility of the AUTOSAR
XML Schema1. Therefore, a different approach (as sketched in Figure 13.2) has been
implemented.

1Because in this case the shortName becomes mandatory.



Figure 13.2: Access Points used in the context of the Rapid Prototyping Scenario

A new meta-class IdentCaption is created that introduces the capabilities of the
meta-class Identifiable (that, in turn, inherits from Referrable) to its subclasses,
ModeAccessPointIdent and ExternalTriggeringPointIdent.

These, in turn, are optionally2 aggregated in the role ident by ModeAccessPoint,
resp. in the role ident by meta-class ExternalTriggeringPoint.

2Again, this is necessary to not break the backwards compatibility




AtpStructureElementExecutableEntityRunnableEntityAtpStructureElementIdentifiableParameterAccessAtpStructureElementIdentifiableVariableAccessExternalTriggeringPointAtpStructureElementIdentifiableInternalTriggeringPointAtpStructureElementIdentifiableServerCallPointAtpStructureElementIdentifiableAsynchronousServerCallResultPointModeAccessPointAtpStructureElementIdentifiableModeSwitchPointAtpStructureElementIdentifiableIdentCaptionModeAccessPointIdentExternalTriggeringPointIdentAggregation Tags:atp.Status = shallBecomeMandatory«atpVariation» Tags:vh.latestBindingTime =preCompileTime«atpVariation»+dataReceivePointByArgument0..*+ident0..1«atpVariation»+parameterAccess0..*«atpVariation»+writtenLocalVariable0..*«atpVariation»+dataReceivePointByValue0..*«atpVariation»+readLocalVariable0..*«atpVariation»+dataSendPoint0..*+externalTriggeringPoint0..*«atpVariation»«atpVariation»+dataWriteAccess0..*+modeSwitchPoint*«atpVariation»+modeAccessPoint*«atpVariation»+ident0..1+asynchronousServerCallResultPoint0..*«atpVariation»+serverCallPoint*«atpVariation»+internalTriggeringPoint0..*«atpVariation»«atpVariation»+dataReadAccess0..*

IdentCaption (abstract)

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::RPTScenario
Note

This meta-class represents the caption. This allows having some meta classes
optionally identiﬁable.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Identiﬁable,Multilanguage
Referrable,Referrable
Datatype
–

Mul. Kind Note
–

–

–

Base

Attribute
–

Table 13.5: IdentCaption

ModeAccessPointIdent

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::RPTScenario
Note

This meta-class has been created to introduce the ability to become referenced into
the meta-class ModeAccessPoint without breaking backwards compatibility.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Ident
Caption,Identiﬁable,MultilanguageReferrable,Referrable
Mul. Kind Note
Datatype
–
–

–

–

Base

Attribute
–

Table 13.6: ModeAccessPointIdent

ExternalTriggeringPointIdent

Class#@CLASS: 
Package M2::AUTOSARTemplates::SWComponentTemplate::RPTScenario
Note

This meta-class has been created to introduce the ability to become referenced into
the meta-class ExternalTriggeringPoint without breaking backwards compatibility.
ARObject,AtpClassiﬁer,AtpFeature,AtpStructureElement,Ident
Caption,Identiﬁable,MultilanguageReferrable,Referrable
Mul. Kind Note
Datatype

Base

Attribute
–

Table 13.7: ExternalTriggeringPointIdent

The following (simpliﬁed) listing 13.1 sketches the usage of the meta-class Ident
Caption for the purpose of effectively allowing references to a ModeAccessPoint.

Listing 13.1: Example for the deﬁnition of a RPT scenario
