# AUTOSAR Software Component Requirements

## Requirements Tracing

Requirements against this document are exclusively stated in the corresponding requirements document [13].

The following table references the requirements specified in [13] and provides information about individual specification items that fulfill a given requirement.

[RS_SWCT_00010]
AUTOSAR shall support inter- and intra-ECU-communication mechanisms with high reliability

[RS_SWCT_00020]
AUTOSAR shall provide open and standardized software interfaces for intra-ECU and inter-ECU communication

[RS_SWCT_00030]
AUTOSAR shall provide complete interfaces to application software and basic software modules

[RS_SWCT_00070]
AUTOSAR shall provide an abstraction of the application software from hardware

[RS_SWCT_00080]
AUTOSAR shall provide an independence of application software from in-vehicle communication technologies

[RS_SWCT_00090]
AUTOSAR should provide an independence of application software from operating systems

[RS_SWCT_00110]
AUTOSAR shall provide a functional interface view of the entire system

[RS_SWCT_00120]
AUTOSAR shall provide protection/unlock mechanisms for software through appropriate services in the infrastructure

[RS_SWCT_00150]
AUTOSAR shall provide means to protect SW-Components from malicious SW-Components

[RS_SWCT_00160]
AUTOSAR shall provide means to achieve compositionality

[RS_SWCT_00170]
AUTOSAR shall provide diagnostics means during runtime, for production and services purposes

[RS_SWCT_00190]
AUTOSAR shall support hierarchical design methods

[RS_SWCT_00200]
Definitions of relations between SW components are exhaustive and formal

[RS_SWCT_00210]
SW components are protected from illegal access

[RS_SWCT_00220]
Management of vehicle diversity is supported by AUTOSAR

[RS_SWCT_00230]
The Software Component Template shall provide the ability to define naming conventions for public symbols

[RS_SWCT_02000]
AUTOSAR shall support a top-down hierarchical design

[RS_SWCT_02010]
Interfaces of atomic software-components shall be supported

[RS_SWCT_02020]
Bottom-up design of CompositionTypes shall be supported

[RS_SWCT_02030]
Specification of Communications shall be supported

[RS_SWCT_02060]
Interaction with basic software shall be considered

[RS_SWCT_02080]
Designing a Sensor Actuator Component shall be supported

[RS_SWCT_02090]
Data-consistency for communication among RunnableEntities shall be supported

[RS_SWCT_02100]
Definition of physical units shall be supported

[RS_SWCT_02110]
Definition of comments shall be supported

[RS_SWCT_03000]
The SW-Component template shall support compositions

[RS_SWCT_03010]
The SW-Component template shall support interfaces

[RS_SWCT_03040]
The SW-Component template shall support description of the behavior

[RS_SWCT_03045]
The SW-Component template shall allow enabling of RTE-Feature to get the activating RTE-Event of Runnable Entity

[RS_SWCT_03046]
The SW-Component template shall support instance specific RTE-Events

[RS_SWCT_03050]
The SW-Component template shall support the definition of schedulability

[RS_SWCT_03055]
The SW-Component template shall support optional configuration of ExclusiveArea usage within RunnableEntities

[RS_SWCT_03065]
The SW-Component template shall support the definition of implicit communication behavior

[RS_SWCT_03090]
The SW-Component template shall support the definition of needed and usable sensors and actuators

[RS_SWCT_03100]
The SW-Component template shall support variant handling

[RS_SWCT_03110]
The SW-Component template shall support modes

[RS_SWCT_03115]
The SW-Component template shall support mapping of mode declarations

[RS_SWCT_03120]
The SW-Component template shall support composition of modes

[RS_SWCT_03130]
The SW-Component template shall support connections between PortInterfaces

[RS_SWCT_03135]
The SW-Component template shall support record type subsetting

[RS_SWCT_03136]
The SW-Component template shall support record type subsetting with primitive types

[RS_SWCT_03140]
The SW-Component template shall support conditional existence of PortPrototypes

[RS_SWCT_03141]
The SW-Component template shall support the conditional existence of data element prototypes, operation prototypes, parameter prototypes in an interface

[RS_SWCT_03142]
The SW-Component template shall support the conditional existence of Component Prototypes

[RS_SWCT_03143]
The SW-Component template shall support the conditional existence of Connector Prototypes

[RS_SWCT_03144]
The SW-Component template shall support a configurable size of arrays

[RS_SWCT_03148]
Attributes swMinAxisPoints and swMaxAxisPoints shall be adjustable by a System Constant Definition

[RS_SWCT_03149]
The SW-Component template shall support the conditional existence of RunnableEntitys

[RS_SWCT_03150]
The SW-Component template shall support the conditional existence of RTEEvents

[RS_SWCT_03151]
The SW-Component template shall support the conditional existence of InterRunnable Variables

[RS_SWCT_03152]
The SW-Component template shall support conditional accessibility for measurement

[RS_SWCT_03153]
The SW-Component template shall support the conditional existence of parameter prototypes

[RS_SWCT_03154]
The SW-Component template shall support conditional ports for software components

[RS_SWCT_03155]
The SW-Component template shall support interfaces with different resolutions

[RS_SWCT_03170]
The SW-Component template shall support fixed data exchange

[RS_SWCT_03175]
The SW-Component template shall support the definition of calibration datasets

[RS_SWCT_03180]
The SW-Component template shall support SAE J1939 Protocol Features

[RS_SWCT_03181]
The SW-Component template shall support arrays of variable number of elements with the maximum size

[RS_SWCT_03182]
The SW-Component template shall support byte arrays of variable number of elements

[RS_SWCT_03190]
The SW-Component template shall support the ability to publish/specify the diagnostic capabilities and its resources of an SWC

[RS_SWCT_03200]
The SW-Component template shall support vehicle and application mode management

[RS_SWCT_03201]
The SW-Component template shall support Portgroups

[RS_SWCT_03202]
The SW-Component template shall support enabling SWCs to request dedicated modes

[RS_SWCT_03203]
The SW-Component template shall support propagation of mode information

[RS_SWCT_03210]
The SW-Component template shall support integrity and timing at ports

[RS_SWCT_03215]
The SW-Component template shall define the need to add application data type on top of implementation data type

[RS_SWCT_03216]
The SW-Component template shall support application data type

[RS_SWCT_03217]
The SW-Component template shall support implementation data type

[RS_SWCT_03218]
The SW-Component template shall support data types for primitive data mapping

[RS_SWCT_03220]
The SW-Component template shall allow communication attributes on compositions

[RS_SWCT_03221]
The SW-Component template shall allow port specific configuration of data transformation properties

[RS_SWCT_03222]
The SW-Component template shall support error notification for transformed data communication

[RS_SWCT_03225]
The SW-Component template shall support an enhanced non-volatile (NV) memory interface

[RS_SWCT_03230]
The SW-Component template shall support documentation of M1 artifacts

[RS_SWCT_03240]
The SW-Component template shall support end-to-end communication protection

[RS_SWCT_03241]
The SW-Component template shall support partial networking

[RS_SWCT_03250]
The SW-Component template shall support bidirectional communication

[RS_SWCT_03260]
The SW-Component template shall support rule-based initialization of arrays

[RS_SWCT_03270]
The SW-Component template shall support overriding the activation period time on instance level

[RS_SWCT_03280]
The SW-Component template shall support the description of bypass points and bypass scenarios

[RS_SWCT_03290]
The SW-Component template shall support the initialization of runnables without usage of mode management

[RS_SWCT_03310]
The SW-Component template shall support Diagnostics over IP