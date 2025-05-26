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

Figure 6.1: legal n:1 communication

The next case (exemplified by Figure 6.2) implements a situation where one sender provides two dataElements {A,b} while the other sender provides only as subset of these, i.e. {B}. As the RPortPrototype of the receiving software-component requires only the dataElement {B} compatibility issues will not occur because for every required dataElement a compatible dataElement is provided.

Figure 6.2: legal n:1 communication

#@SECTION: 6.16.1.2 Illegal Use
#@CLASS: AssemblySwConnector

On possible example for an illegal configuration of a sender/receiver communication is the scenario sketched in Figure 6.3. Although the sender software-components in total provide the set of required dataElements the individual AssemblySwConnectors create incompatible connections between sender and receiver.

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

Figure 6.4: Legal split of delegation connector

All required dataElements are provided by the DelegationSwConnectors attached to the delegation RPortPrototype. The fact that dataElement D is not conveyed to any of the RPortPrototypes owned by the SwComponentPrototypes does not have any impact on the compatibility.

In other words: the RPortPrototype at the CompositionSwComponentType actually contains the superset of dataElements {A ,B, C, D}. The two required inner PortPrototypes of the SwComponentPrototypes contain the subsets of VariableDataPrototypes {A, B} and {B, C}. In this case the resulting communication pattern on the VFB for B would be 1:n.

This requires the value of the attribute signalFan of DelegatedPortAnnotation to be set to the value nfold.

In the next example the RPortPrototype of the CompositionSwComponentType contains the superset of dataElements {A ,B}. The two RPortPrototypes of the SwComponentPrototypes contain different subsets, i.e. {A} and {B}.

Figure 6.5: Legal split of delegation connector

In this case the resulting communication pattern on the VFB would be n:1. In this case the value of the attribute signalFan of DelegatedPortAnnotation should be set to single.

The next example is about the merge of DelegationSwConnectors. The PPortPrototype owned by the CompositionSwComponentType contains a superset of dataElements {A ,B}. The two PPortPrototypes of the SwComponentPrototypes contain a disjoint subset each, i.e. {A} and {B}.

Figure 6.6: Legal merge of delegation connector

In this case the resulting communication pattern on the VFB would be 1:x, with x taking values between 0 and n. In this case the value of the attribute signalFan of DelegatedPortAnnotation should be set to single. All VariableDataPrototypes of the provided outer PortPrototypes are provided by exactly one provided inner PortPrototype.

As a variation of this theme, the next example features a PPortPrototype owned by a CompositionSwComponentType that contains the superset of dataElements {A ,B, C}. The PPortPrototypes of the SwComponentPrototypes in turn contain subsets of dataElements, i.e. {A, B} and {B, C}. In this case the resulting communication pattern on the VFB for {B} would be n:1.

Figure 6.7: Legal merge of delegation connector

This would require the value of the attribute signalFan of DelegatedPortAnnotation to be set to nfold. All dataElements of the delegation PPortPrototype are provided by at least one PPortPrototype of the SwComponentPrototypes. Therefore the criteria of entire delegation defined in chapter 6.14 are fulfilled.

The next example looks very similar. However, the subtle difference is that the second SwComponentPrototype provides dataElements {C,D} rather than {B,C}.

Figure 6.8: Legal merge of delegation connector

Although dataElement {D} does not appear in the delegation PPortPrototype the compatibility rules are fully satisfied with this scenario.

The next example shows a valid delegation of SwConnectors that goes end-to-end via CompositionSwComponentTypes to included SwComponentPrototypes.

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

Figure 6.11: Illegal split of delegation connector

An incompatible merge of DelegationSwConnectors is sketched in Figure 6.12. In this case the dataElement {E} is not provided by one of the PPortPrototypes owned by the SwComponentPrototypes inside the CompositionSwComponentType.

Figure 6.12: Illegal merge of delegation connector

The next example shows an invalid delegation of SwConnectors that goes end-to-end via CompositionSwComponentTypes to included SwComponentPrototypes.

Similar to the example sketched in Figure 6.12, the dataElement {E} is not provided by one of the PPortPrototypes owned by the SwComponentPrototypes inside the CompositionSwComponentType.

Figure 6.13: Invalid delegation of SwConnectors that goes end-to-end