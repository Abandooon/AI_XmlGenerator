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

[constr_1289] Allowed Attributes vs. category for DataPrototypes typed by ApplicationDataTypes (cid:100) The allowed values of Attributes per category for DataPrototypes typed by ApplicationDataTypes are documented in table 5.31. (cid:99)()

Table 5.32: Allowed Attributes vs. category for DataPrototypes typed by ImplementationDataTypes

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

Table 5.73: ASAM compuMethod

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

Figure 5.45: Values for swRecordLayoutVProp for individual axis

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