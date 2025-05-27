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

Figure 10.1: AUTOSAR ECU Software Architecture

The signal flow from a hardware to software and vice versa will be described in the following sections. A sensor is converting a physical value (1) in Figure 10.2 (e.g. light intensity) into an electrical signal (2) which can be either a current or a voltage. temperature, force, Inside the ECU generally there will be some electronics to enhance the electrical signal provided by the sensor. In AUTOSAR this is called ECU Electronics. This electronics is also responsible for the conversion of the electrical signal into a microcontroller compatible form (3), usually a voltage.

After the electrical signal has been enhanced and converted it will be captured by the microcontroller. This can either be done by a simple digital input, an analogue to digital converter or maybe a pulse-width demodulation module. Now the electrical signal is available as a software data value (4). This signal flow is sketched in the top part of Figure 10.2.

1The term "signal" is not going to be used here at its own but more specific terms will be used for the different abstractions of signals at the different stages of the signal flow.

2For the sake of simplicity this discussion is limited to the sensor aspects. Nevertheless, the same applies also for actuators.

Figure 10.2: Interfaces between hardware and software

This signal chain is represented one to one in the AUTOSAR software architecture and depicted in the lower part of Figure 10.2.

In an implementation of AUTOSAR only the Microcontroller Abstraction (MCAL) has direct access to the peripheral hardware. This layer is going to be standardized and all hardware access should go through this layer. The idea of the AUTOSAR signal flow is to map the hardware to the corresponding software modules.

So if an electrical current is the input to the microcontroller peripheral, the MCAL will deliver a data value that represents this current. As the ECU Electronics has enhanced and converted the electrical signal prior to the microcontroller, the corresponding software entity is reversing this conversion. This is performed in the ECU Abstraction layer.

So if the input to the ECU is an electrical current and the ECU Electronics has converted this current into a voltage (from 2 to 3), the ECU Abstraction will convert the data value voltage into an AUTOSAR signal representing a current (from 4 to 5). This AUTOSAR signal represents the actual current that was provided by the sensor (2).

Now the first step in the conversion has to be reversed: the sensor has converted a physical value into an electrical signal. And so the Sensor Software Component has to reverse this again. The Sensor Software Component will read the AUTOSAR signal representing the electrical value and transform it into an AUTOSAR signal representation of the physical value (from 5 to 6).

Now this physical value is available on the RTE and can be consumed or read by other SW-Components. Although the interface between the ECU Abstraction and the Sensor Software Component is also an AUTOSAR interface and could be routed through some communication bus, it will not be practical to separate the ECU Abstraction and the corresponding SensorActuatorSwComponentType due to potentially high communication effort.

In Figure 10.3 a complete signal flow from a sensor input to an actuator output is shown.

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

Figure 11.10: Example NvBlockDataMapping to explain [TPS_SWCT_01659]

[constr_1395] NvBlockDataMapping shall be complete (cid:100) If an NvBlockDataMapping refers to sub-elements or leaf elements of the NvDataInterface.nvData in the context of a particular PortPrototype then all remaining sub-elements or leaf elements shall effectively be mapped according to [TPS_SWCT_01659] by means of a collection of NvBlockDataMappings. (cid:99)()

[constr_1403] NvBlockDataMappings to a given nvData shall be unambiguous (cid:100) If an NvBlockDataMapping exists that directly and completely maps a speciﬁc NvDataInterface.nvData in the context of a particular PortPrototype then no other NvBlockDataMapping which maps sub-elements of the NvDataInterface.nvData shall exist. (cid:99)()

The interaction with AUTOSAR services is centrally deﬁned in the context of the SwcServiceDependency. The latter gathers a collection of PortPrototypes by means of RoleBasedPortAssignments that implement a closely related service functionality.

In the speciﬁc case of interaction between AtomicSwComponentType and NvBlockSwComponentType (as described by [TPS_SWCT_02503]), there are PortPrototypes referenced by a RoleBasedPortAssignment with attribute RoleBasedPortAssignment.role set to NvDataPort. These PortPrototypes contain the collected Nv Data of the service use case.

Furthermore, there is the possibility to receive notiﬁcations when the writing of the mapped NV Block to the NvRam is ﬁnished.

In order to be able to properly assign such a notiﬁcation to the content of the related Nv Data PortPrototypes in the scope of the same SwcServiceDependency it is necessary that the Nv Data of all these PortPrototypes is mapped to the same Nv Block (because the notiﬁcations are created per block).

This motivates the existence of [constr_1404]:
[constr_1404] All NvDataInterface.nvData of PortPrototypes in the context of a speciﬁc SwcServiceDependency shall be mapped to the same NvBlockDescriptor (cid:100) In the context of a given SwcServiceDependency (which, in turn, is owned by an AtomicSwComponentType), all NvDataInterface.nvData of PortPrototypes referenced by a RoleBasedPortAssignment with attribute RoleBasedPortAssignment.role set to NvDataPort shall be connected (either directly or via the deﬁnition of suitable PortInterfaceMappings) to NvDataInterface.nvData (on the side of the NvBlockSwComponentType) that are completely mapped (via NvBlockDataMappings) to the identical NvBlockDescriptor.ramBlock. (cid:99)()

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

Table 13.7: ExternalTriggeringPointIdent

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