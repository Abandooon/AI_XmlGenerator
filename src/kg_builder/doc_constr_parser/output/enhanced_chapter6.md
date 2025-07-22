#@SECTION: 6 Compatibility
#@SECTION: 6.1 Introduction
#@CLASS: ApplicationDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类); Childs=[ApplicationCompositeDataType, ApplicationPrimitiveDataType] (直接子类) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS PortInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, Identifiable] (直接父类); Childs=[ClientServerInterfaceMapping, ModeInterfaceMapping, TriggerInterfaceMapping, VariableAndParameterInterfaceMapping] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwComponentType
<!-- LLM_CONTEXT FOR CLASS SwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, consistencyNeeds, desc, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[AtomicSwComponentType, CompositionSwComponentType, ParameterSwComponentType] (直接子类) -->

In order to connect PortPrototypes of SwComponentTypes, the compatibility of PortPrototypes needs to be verified. This section defines the basic rules for formal compatibility of PortPrototypes.

Compatibility will be defined bottom-up, i.e. first the rules for compatible Autosar DataTypes are set up, then the rules for the different types of PortInterfaces are derived.

Another aspect of compatibility is the question whether two model-elements (e.g. ApplicationDataType vs. ImplementationDataType) can be mapped to each other.

For the compatibility of PortInterfaces basically two options apply:
1. finding of matching pairs of elements of PortInterfaces is based on matching shortName plus the application of compatibility rules for their attributes.
2. a PortInterfaceMapping can be taken to declare two elements of PortPrototypes as compatible without applying further formal checks.

#@SECTION: 6.2 Compatibility of Data Types
#@CLASS: ApplicationPrimitiveDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationPrimitiveDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类) -->
#@CLASS: AutosarDataType
<!-- LLM_CONTEXT FOR CLASS AutosarDataType: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpType] (直接父类); Childs=[ApplicationDataType, ImplementationDataType] (直接子类) -->

The AUTOSAR meta model defines a number of meta-classes (e.g. ApplicationPrimitiveDataType) that eventually refer to a set of attributes (e.g. a lower boundary for its values) relevant for compatibility checking.

Instantiating a data-type related meta-class defines a data type on M1 level (e.g. temperatureType). In other words: ApplicationPrimitiveDataType is an M2 artifact; it is taken as the template for creating a corresponding M1 artifact temperatureType.

In this context, the issue of compatibility refers to the M1 objects, i.e. the instances of sub-classes of AutosarDataType need to be considered. For this purpose the relevant part of the AUTOSAR meta-model need to be fully explored with respect to compatibility.

#@SECTION: 6.2.1 ApplicationDataType
#@SECTION: 6.2.1.1 ApplicationPrimitiveDataType
#@CLASS: ApplicationCompositeDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类); Childs=[ApplicationArrayDataType, ApplicationRecordDataType] (直接子类) -->
#@CLASS: ApplicationCompositeDataTypeSubElementRef
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataTypeSubElementRef: Attributes=[applicationCompositeElement, variationPoint] (包含继承及相关属性); Generalization=[SubElementRef] (直接父类) -->
#@CLASS: ApplicationCompositeElementDataPrototype
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeElementDataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[DataPrototype] (直接父类); Childs=[ApplicationArrayElement, ApplicationRecordElement] (直接子类) -->
#@CLASS: ApplicationPrimitiveDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationPrimitiveDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: DataPrototypeMapping
<!-- LLM_CONTEXT FOR CLASS DataPrototypeMapping: Attributes=[firstDataPrototype, firstToSecondDataTransformation, secondDataPrototype, subElementMapping, textTableMapping] (包含继承及相关属性) -->

[constr_1047] Compatibility of ApplicationPrimitiveDataTypes (cid:100) Instances of ApplicationPrimitiveDataType are compatible if and only if one of the following conditions applies:

1. All of the following subconditions apply: (a) They have the same category (see table in figure 5.8). (b) The swDataDefProps attached to the M1 data types are compatible. The meaning of this statement is explained in section 6.2.4.

2. In the context of using the ApplicationPrimitiveDataType, a DataPrototypeMapping exists that refers to a DataPrototype typed by one of the ApplicationPrimitiveDataTypes in the role firstDataPrototype and to another DataPrototype typed by the other ApplicationPrimitiveDataType in the role secondDataPrototype.

3. In the context of using the ApplicationPrimitiveDataType, a DataPrototypeMapping exists that refers to a DataPrototype typed by the ApplicationPrimitiveDataType in the role secondDataPrototype and to another DataPrototype typed by an ApplicationCompositeDataType in the role firstDataPrototype and additionally for the side of the ApplicationCompositeDataType a corresponding ApplicationCompositeDataTypeSubElementRef exists in the role firstElement that in turn references an ApplicationCompositeElementDataPrototype.

(cid:99)()

Please note that it is not required that the shortNames of two data types shall be identical in order to consider the two data types as compatible.

#@SECTION: 6.2.1.2 ApplicationCompositeDataType
#@CLASS: ApplicationArrayDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationArrayDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, element, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationCompositeDataType] (直接父类) -->
#@CLASS: ApplicationArrayElement
<!-- LLM_CONTEXT FOR CLASS ApplicationArrayElement: Attributes=[adminData, annotation, arraySizeHandling, arraySizeSemantics, category, desc, introduction, longName, maxNumberOfElements, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[ApplicationCompositeElementDataPrototype] (直接父类) -->
#@CLASS: ApplicationCompositeDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类); Childs=[ApplicationArrayDataType, ApplicationRecordDataType] (直接子类) -->
#@CLASS: ApplicationCompositeDataTypeSubElementRef
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataTypeSubElementRef: Attributes=[applicationCompositeElement, variationPoint] (包含继承及相关属性); Generalization=[SubElementRef] (直接父类) -->
#@CLASS: ApplicationPrimitiveDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationPrimitiveDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类) -->
#@CLASS: ApplicationRecordDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationRecordDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, element, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationCompositeDataType] (直接父类) -->
#@CLASS: ApplicationRecordElement
<!-- LLM_CONTEXT FOR CLASS ApplicationRecordElement: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[ApplicationCompositeElementDataPrototype] (直接父类) -->
#@CLASS: AutosarDataTypes
<!-- LLM_CONTEXT FOR CLASS AutosarDataTypes: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: DataPrototypeMapping
<!-- LLM_CONTEXT FOR CLASS DataPrototypeMapping: Attributes=[firstDataPrototype, firstToSecondDataTransformation, secondDataPrototype, subElementMapping, textTableMapping] (包含继承及相关属性) -->
#@CLASS: PortInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS PortInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, Identifiable] (直接父类); Childs=[ClientServerInterfaceMapping, ModeInterfaceMapping, TriggerInterfaceMapping, VariableAndParameterInterfaceMapping] (直接子类) -->
#@CLASS: SubElementMapping
<!-- LLM_CONTEXT FOR CLASS SubElementMapping: Attributes=[firstElement, secondElement, textTableMapping] (包含继承及相关属性) -->

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
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: DataPrototypeMapping
<!-- LLM_CONTEXT FOR CLASS DataPrototypeMapping: Attributes=[firstDataPrototype, firstToSecondDataTransformation, secondDataPrototype, subElementMapping, textTableMapping] (包含继承及相关属性) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: ImplementationDataTypeElement
<!-- LLM_CONTEXT FOR CLASS ImplementationDataTypeElement: Attributes=[adminData, annotation, arraySize, arraySizeHandling, arraySizeSemantics, category, desc, introduction, longName, shortName, shortNameFragment, subElement, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: ImplementationDataTypeSubElementRef
<!-- LLM_CONTEXT FOR CLASS ImplementationDataTypeSubElementRef: Attributes=[implementationDataTypeElement, variationPoint] (包含继承及相关属性); Generalization=[SubElementRef] (直接父类) -->
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->

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
<!-- LLM_CONTEXT FOR CLASS SwBaseType: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->

[constr_1220] Compatibility of SwBaseType (cid:100) Two SwBaseTypes are compatible if and only if attributes baseTypeSize respectively maxBaseTypeSize, byteOrder, memAlignment, baseTypeEncoding, and nativeDeclaration have identical values. (cid:99)()

#@SECTION: 6.2.4 Compatibility of SwDataDefProps
#@CLASS: ApplicationValueSpecification
<!-- LLM_CONTEXT FOR CLASS ApplicationValueSpecification: Attributes=[category, shortLabel, swAxisCont, swValueCont, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: NumericalValueSpecification
<!-- LLM_CONTEXT FOR CLASS NumericalValueSpecification: Attributes=[shortLabel, value, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: RecordValueSpecification
<!-- LLM_CONTEXT FOR CLASS RecordValueSpecification: Attributes=[field, shortLabel, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: TextValueSpecification
<!-- LLM_CONTEXT FOR CLASS TextValueSpecification: Attributes=[shortLabel, value, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: SwDataDefProps
<!-- LLM_CONTEXT FOR CLASS SwDataDefProps: Attributes=[SwDataDefPropsVariant, additionalNativeTypeQualifier, annotation, baseType, compuMethod, dataConstr, displayFormat, implementationDataType, invalidValue, mcFunction, stepSize, swAddrMethod, swAlignment, swBitRepresentation, swCalibrationAccess, swCalprmAxisSet, swComparisonVariable, swDataDependency, swHostVariable, swImplPolicy, swIntendedResolution, swInterpolationMethod, swIsVirtual, swPointerTargetProps, swRecordLayout, swRefreshTiming, swTextProps, swValueBlockSize, unit, valueAxisDataType] (包含继承及相关属性) -->
#@CLASS: Unit
<!-- LLM_CONTEXT FOR CLASS Unit: Attributes=[displayName, factorSiToUnit, offsetSiToUnit, physicalDimension] (包含继承及相关属性) -->
#@CLASS: ValueSpecification
<!-- LLM_CONTEXT FOR CLASS ValueSpecification: Attributes=[shortLabel, variationPoint] (包含继承及相关属性); Childs=[AbstractRuleBasedValueSpecification, ApplicationValueSpecification, ArrayValueSpecification, ConstantReference, NumericalValueSpecification, RecordValueSpecification, ReferenceValueSpecification, TextValueSpecification] (直接子类) -->
#@CLASS: ConstantReference
<!-- LLM_CONTEXT FOR CLASS ConstantReference: Attributes=[constant, shortLabel, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: ArrayValueSpecification
<!-- LLM_CONTEXT FOR CLASS ArrayValueSpecification: Attributes=[element, shortLabel, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: CompuMethod
<!-- LLM_CONTEXT FOR CLASS CompuMethod: Attributes=[compuInternalToPhys, compuPhysToInternal, displayFormat, unit] (包含继承及相关属性) -->

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
<!-- LLM_CONTEXT FOR CLASS AutosarDataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[DataPrototype] (直接父类); Childs=[ArgumentDataPrototype, ParameterDataPrototype, VariableDataPrototype] (直接子类) -->
#@CLASS: AutosarDataType
<!-- LLM_CONTEXT FOR CLASS AutosarDataType: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpType] (直接父类); Childs=[ApplicationDataType, ImplementationDataType] (直接子类) -->
#@CLASS: AutosarDataPrototype
<!-- LLM_CONTEXT FOR CLASS AutosarDataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[DataPrototype] (直接父类); Childs=[ArgumentDataPrototype, ParameterDataPrototype, VariableDataPrototype] (直接子类) -->
#@CLASS: ValueSpecification
<!-- LLM_CONTEXT FOR CLASS ValueSpecification: Attributes=[shortLabel, variationPoint] (包含继承及相关属性); Childs=[AbstractRuleBasedValueSpecification, ApplicationValueSpecification, ArrayValueSpecification, ConstantReference, NumericalValueSpecification, RecordValueSpecification, ReferenceValueSpecification, TextValueSpecification] (直接子类) -->
#@CLASS: PhysicalDimension
<!-- LLM_CONTEXT FOR CLASS PhysicalDimension: Attributes=[currentExp, lengthExp, luminousIntensityExp, massExp, molarAmountExp, temperatureExp, timeExp] (包含继承及相关属性) -->
#@CLASS: Unit
<!-- LLM_CONTEXT FOR CLASS Unit: Attributes=[displayName, factorSiToUnit, offsetSiToUnit, physicalDimension] (包含继承及相关属性) -->
#@CLASS: ApplicationValueSpecification
<!-- LLM_CONTEXT FOR CLASS ApplicationValueSpecification: Attributes=[category, shortLabel, swAxisCont, swValueCont, variationPoint] (包含继承及相关属性); Generalization=[ValueSpecification] (直接父类) -->
#@CLASS: ApplicationRuleBasedValueSpecification
<!-- LLM_CONTEXT FOR CLASS ApplicationRuleBasedValueSpecification: Attributes=[category, shortLabel, swAxisCont, swValueCont, variationPoint] (包含继承及相关属性); Generalization=[AbstractRuleBasedValueSpecification] (直接父类) -->
#@CLASS: RuleBasedValueCont
<!-- LLM_CONTEXT FOR CLASS RuleBasedValueCont: Attributes=[ruleBasedValues, swArraysize, unit] (包含继承及相关属性) -->
#@CLASS: SwValueCont
<!-- LLM_CONTEXT FOR CLASS SwValueCont: Attributes=[swArraysize, swValuesPhys, unit, unitDisplayName] (包含继承及相关属性) -->

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
<!-- LLM_CONTEXT FOR CLASS PhysicalDimension: Attributes=[currentExp, lengthExp, luminousIntensityExp, massExp, molarAmountExp, temperatureExp, timeExp] (包含继承及相关属性) -->
#@CLASS: PhysicalDimensionMapping
<!-- LLM_CONTEXT FOR CLASS PhysicalDimensionMapping: Attributes=[firstPhysicalDimension, secondPhysicalDimension] (包含继承及相关属性) -->

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
<!-- LLM_CONTEXT FOR CLASS DataConstr: Attributes=[dataConstrRule] (包含继承及相关属性) -->
#@CLASS: PhysConstrs
<!-- LLM_CONTEXT FOR CLASS PhysConstrs: Attributes=[lowerLimit, maxDiff, maxGradient, monotony, scaleConstr, unit, upperLimit] (包含继承及相关属性) -->

The compatibility of two DataConstrs depends on the context in which the owning data elements are connected:

[constr_1126] Compatibility of DataConstrs (cid:100) The DataConstr (e.g. the limits) defined by the type of the providing data element shall be within the constraints defined by the type of the requiring data element. (cid:99)()

In addition, it is always allowed if the requiring element defines no constraints.

[constr_1278] PhysConstrs references a Unit (cid:100) DataConstrs are only compatible if the DataConstr.dataConstrRule.physConstrs.unit are compatible or neither DataConstr.dataConstrRule.physConstrs.unit exist. (cid:99)()

[constr_1054] No DataConstr available at the provider (cid:100) If the provider defines no constraints it is only compatible with a receiver which also defines no constraints at all. (cid:99)()

In other words, this is not a compatibility rule for the types but for the data prototypes.

#@SECTION: 6.2.4.4 Compatibility in case of ImplementationDataType
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: SwBaseType
<!-- LLM_CONTEXT FOR CLASS SwBaseType: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: SwDataDefProps
<!-- LLM_CONTEXT FOR CLASS SwDataDefProps: Attributes=[SwDataDefPropsVariant, additionalNativeTypeQualifier, annotation, baseType, compuMethod, dataConstr, displayFormat, implementationDataType, invalidValue, mcFunction, stepSize, swAddrMethod, swAlignment, swBitRepresentation, swCalibrationAccess, swCalprmAxisSet, swComparisonVariable, swDataDependency, swHostVariable, swImplPolicy, swIntendedResolution, swInterpolationMethod, swIsVirtual, swPointerTargetProps, swRecordLayout, swRefreshTiming, swTextProps, swValueBlockSize, unit, valueAxisDataType] (包含继承及相关属性) -->
#@CLASS: BswModuleEntry
<!-- LLM_CONTEXT FOR CLASS BswModuleEntry: Attributes=[adminData, annotation, argument, blueprintPolicy, callType, category, desc, executionContext, introduction, isReentrant, isSynchronous, longName, returnType, role, serviceId, shortName, shortNameFragment, shortNamePattern, swServiceImplPolicy, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable] (直接父类) -->
#@CLASS: ApplicationDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类); Childs=[ApplicationCompositeDataType, ApplicationPrimitiveDataType] (直接子类) -->
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
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: TextTableMapping
<!-- LLM_CONTEXT FOR CLASS TextTableMapping: Attributes=[bitfieldTextTableMaskFirst, bitfieldTextTableMaskSecond, identicalMapping, mappingDirection, valuePair] (包含继承及相关属性) -->
#@CLASS: CompuScale
<!-- LLM_CONTEXT FOR CLASS CompuScale: Attributes=[compuConst, compuInverseValue, compuRationalCoeffs, desc, lowerLimit, mask, shortLabel, symbol, upperLimit, variationPoint] (包含继承及相关属性) -->
#@CLASS: CompuMethod
<!-- LLM_CONTEXT FOR CLASS CompuMethod: Attributes=[compuInternalToPhys, compuPhysToInternal, displayFormat, unit] (包含继承及相关属性) -->
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
<!-- LLM_CONTEXT FOR CLASS ApplicationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类); Childs=[ApplicationCompositeDataType, ApplicationPrimitiveDataType] (直接子类) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SwBaseType
<!-- LLM_CONTEXT FOR CLASS SwBaseType: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: DataTypeMap
<!-- LLM_CONTEXT FOR CLASS DataTypeMap: Attributes=[applicationDataType, implementationDataType] (包含继承及相关属性) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: CompuMethod
<!-- LLM_CONTEXT FOR CLASS CompuMethod: Attributes=[compuInternalToPhys, compuPhysToInternal, displayFormat, unit] (包含继承及相关属性) -->

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
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类); Childs=[ApplicationArrayDataType, ApplicationRecordDataType] (直接子类) -->
#@CLASS: ApplicationCompositeDataTypeSubElementRef
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeDataTypeSubElementRef: Attributes=[applicationCompositeElement, variationPoint] (包含继承及相关属性); Generalization=[SubElementRef] (直接父类) -->
#@CLASS: ApplicationCompositeElementDataPrototype
<!-- LLM_CONTEXT FOR CLASS ApplicationCompositeElementDataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, type] (包含继承及相关属性); Generalization=[DataPrototype] (直接父类); Childs=[ApplicationArrayElement, ApplicationRecordElement] (直接子类) -->
#@CLASS: ApplicationPrimitiveDataType
<!-- LLM_CONTEXT FOR CLASS ApplicationPrimitiveDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ApplicationDataType] (直接父类) -->
#@CLASS: AutosarDataType
<!-- LLM_CONTEXT FOR CLASS AutosarDataType: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpType] (直接父类); Childs=[ApplicationDataType, ImplementationDataType] (直接子类) -->
#@CLASS: DataPrototype
<!-- LLM_CONTEXT FOR CLASS DataPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类); Childs=[ApplicationCompositeElementDataPrototype, AutosarDataPrototype] (直接子类) -->
#@CLASS: DataPrototypeMapping
<!-- LLM_CONTEXT FOR CLASS DataPrototypeMapping: Attributes=[firstDataPrototype, firstToSecondDataTransformation, secondDataPrototype, subElementMapping, textTableMapping] (包含继承及相关属性) -->
#@CLASS: ImplementationDataType
<!-- LLM_CONTEXT FOR CLASS ImplementationDataType: Attributes=[adminData, annotation, blueprintPolicy, category, desc, dynamicArraySizeProfile, introduction, longName, shortName, shortNameFragment, shortNamePattern, subElement, swDataDefProps, symbolProps, typeEmitter, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, AutosarDataType] (直接父类) -->
#@CLASS: ImplementationDataTypeSubElementRef
<!-- LLM_CONTEXT FOR CLASS ImplementationDataTypeSubElementRef: Attributes=[implementationDataTypeElement, variationPoint] (包含继承及相关属性); Generalization=[SubElementRef] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SubElementMapping
<!-- LLM_CONTEXT FOR CLASS SubElementMapping: Attributes=[firstElement, secondElement, textTableMapping] (包含继承及相关属性) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: DataInterface
<!-- LLM_CONTEXT FOR CLASS DataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类); Childs=[NvDataInterface, ParameterInterface, SenderReceiverInterface] (直接子类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->
#@CLASS: VariableAndParameterInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS VariableAndParameterInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, dataMapping, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS DataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类); Childs=[NvDataInterface, ParameterInterface, SenderReceiverInterface] (直接子类) -->
#@CLASS: DelegationSwConnector
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->
#@CLASS: VariableAndParameterInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS VariableAndParameterInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, dataMapping, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS DataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类); Childs=[NvDataInterface, ParameterInterface, SenderReceiverInterface] (直接子类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: PassThroughSwConnector
<!-- LLM_CONTEXT FOR CLASS PassThroughSwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, providedOuterPort, requiredOuterPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS PortInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, Identifiable] (直接父类); Childs=[ClientServerInterfaceMapping, ModeInterfaceMapping, TriggerInterfaceMapping, VariableAndParameterInterfaceMapping] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

[constr_1248] Compatibility of PortPrototypes of different DataInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different DataInterfaces are considered compatible if and only if

1. For at least one VariableDataPrototype or ParameterDataPrototype defined in the context of the DataInterface of the required outer PortPrototype a compatible VariableDataPrototype or ParameterDataPrototype exists in the DataInterface of the provided outer PortPrototype.

The table 6.1 defines which elements of PortInterface are considered compatible depending on the type of PortInterface as well as the attribute swImplPolicy of the elements of PortInterfaces.

Either the shortName of VariableDataPrototypes and ParameterDataPrototypes are used to identify the pair or a PortInterfaceMapping exists that defines which differently named elements of PortInterfaces correlate with each other.

2. For each such pair, the values of the PortInterface.isService attributes are identical.

(cid:99)()

#@SECTION: 6.4.4 Compatibility of ParameterDataPrototype and VariableDataPrototype depending on PortInterface Type
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: DelegationSwConnector  
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: ModeSwitchInterfaces  
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterfaces: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: PassThroughSwConnector  
<!-- LLM_CONTEXT FOR CLASS PassThroughSwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, providedOuterPort, requiredOuterPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->

Please note that this compatibility requirement only satisfies static correctness which means that logical consistency is not assured (e.g. that a receiver shall process a certain data value to correctly interpret the following values).  

Note that concerning the compatibility of ModeSwitchInterfaces it is necessary to distinguish between the context of an AssemblySwConnector, the context of an DelegationSwConnector, and the context of a PassThroughSwConnector.

#@SECTION: 6.5.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ModeInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, modeMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->

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
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ModeInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, modeMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->

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
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ModeInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, modeMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: PassThroughSwConnector
<!-- LLM_CONTEXT FOR CLASS PassThroughSwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, providedOuterPort, requiredOuterPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->

[constr_1249] Compatibility of ModeSwitchInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different ModeSwitchInterfaces are considered compatible if and only if

1. For the ModeDeclarationGroupPrototype defined in the context of the ModeSwitchInterface of the required outer PortPrototype a compatible ModeDeclarationGroupPrototype exists in the ModeSwitchInterface of the provided outer PortPrototype. Either the shortNames of the ModeDeclarationGroupPrototypes are used to identify the pair or a ModeInterfaceMapping exists that maps the corresponding ModeDeclarationGroupPrototypes.

2. For each such pair, the values of the PortInterface.isService attributes are identical.

(cid:99)()

#@SECTION: 6.6 Compatibility of Mode Declaration Group Prototypes
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototypeMapping
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototypeMapping: Attributes=[firstModeGroup, modeDeclarationMappingSet, secondModeGroup] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroups
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroups: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->

[constr_1074] Compatibility of ModeDeclarationGroupPrototypes (cid:100)
ModeDeclarationGroupPrototypes are compatible if and only if one of the following conditions applies:
1. They are typed by (read "refer to") compatible ModeDeclarationGroups.
2. A ModeDeclarationGroupPrototypeMapping exists that identifies the differently named ModeDeclarationGroupPrototypes that correlate with each other. [constr_1210] applies.
(cid:99)()

#@SECTION: 6.7 Compatibility of Mode Declaration Groups
#@CLASS: ModeDeclaration
<!-- LLM_CONTEXT FOR CLASS ModeDeclaration: Attributes=[value, variationPoint] (包含继承及相关属性) -->
#@CLASS: ModeDeclarationGroup
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroup: Attributes=[adminData, annotation, blueprintPolicy, category, desc, initialMode, introduction, longName, modeDeclaration, modeManagerErrorBehavior, modeTransition, modeUserErrorBehavior, onTransitionValue, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类) -->
#@CLASS: ModeDeclarationMapping
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationMapping: Attributes=[adminData, annotation, category, desc, firstMode, introduction, longName, secondMode, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ModeTransition
<!-- LLM_CONTEXT FOR CLASS ModeTransition: Attributes=[adminData, annotation, category, desc, enteredMode, exitedMode, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[AtpStructureElement, Referrable] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS ArgumentDataPrototype: Attributes=[adminData, annotation, category, desc, direction, introduction, longName, serverArgumentImplPolicy, shortName, shortNameFragment, swDataDefProps, type, typeBlueprint, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: AutosarDataType
<!-- LLM_CONTEXT FOR CLASS AutosarDataType: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swDataDefProps, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpType] (直接父类); Childs=[ApplicationDataType, ImplementationDataType] (直接子类) -->
#@CLASS: ClientServerOperationMapping
<!-- LLM_CONTEXT FOR CLASS ClientServerOperationMapping: Attributes=[argumentMapping, firstOperation, secondOperation] (包含继承及相关属性) -->

[constr_1076] Compatibility of ArgumentDataPrototypes (cid:100) Two ArgumentDataPrototypes are compatible if and only if

1. They are typed by compatible AutosarDataTypes or a ClientServerOperationMapping.argumentMapping exists that references one ArgumentDataPrototype in the role firstDataPrototype and the other ArgumentDataPrototype in the role secondDataPrototype.

2. They have the same value of the argument direction (in, out or inout), i.e. [constr_1268] applies.

(cid:99)()

#@SECTION: 6.9 Compatibility of Application Errors
#@CLASS: ApplicationError
<!-- LLM_CONTEXT FOR CLASS ApplicationError: Attributes=[adminData, annotation, category, desc, errorCode, introduction, longName, shortName, shortNameFragment] (包含继承及相关属性); Generalization=[Identifiable] (直接父类) -->
#@CLASS: ClientServerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ClientServerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, errorMapping, introduction, longName, operationMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->

[constr_1077] Compatibility of ApplicationErrors (cid:100) Two ApplicationErrors are compatible if and only if one of the following conditions applies:

1. All of the following subconditions apply:
(a) They have the same shortName.
(b) They have the same attributes. Especially the errorCode shall be identical in both ApplicationErrors.

2. A ClientServerInterfaceMapping.errorMapping exists that references one of the ApplicationErrors in the role firstApplicationError and the other ApplicationErrors in the role secondApplicationError.

(cid:99)()

#@SECTION: 6.10 Compatibility of Client/Server Operations
#@CLASS: ArgumentDataPrototype
<!-- LLM_CONTEXT FOR CLASS ArgumentDataPrototype: Attributes=[adminData, annotation, category, desc, direction, introduction, longName, serverArgumentImplPolicy, shortName, shortNameFragment, swDataDefProps, type, typeBlueprint, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->

[constr_1078]Compatibility of ClientServerOperations (cid:100) Two ClientServerOperations are compatible if their signatures match. In particular, they are compatible if and only if:

1. They have the same number of ArgumentDataPrototypes.
2. The n-th arguments of both ClientServerOperations are compatible. This implies ordering of ArgumentDataPrototypes.
3. They have the same shortName (again allows for mapping in PortInterfaces).
4. The required ClientServerOperation specifies a compatible ApplicationError for each ApplicationError that is possibly raised by the provided ClientServerOperation, maybe more. Thereby, ClientServerOperations that refer to a possibleError that represents the value E_OK are compatible to ClientServerOperations that do refer to possibleErrors where none of them represents the value E_OK. (cid:99)()

#@SECTION: 6.11 Compatibility of Client Server Interfaces
Please note that this compatibility requirement only satisfies static correctness which means that a client shall call a certain operation to allow the server to work correctly.

#@SECTION: 6.11.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: ClientServerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ClientServerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, errorMapping, introduction, longName, operationMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->

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
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ClientServerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, errorMapping, introduction, longName, operationMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: DelegationSwConnector
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->

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
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS ClientServerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, errorMapping, introduction, longName, operationMapping, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PassThroughSwConnector
<!-- LLM_CONTEXT FOR CLASS PassThroughSwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, providedOuterPort, requiredOuterPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->

[constr_1250] Compatibility of ClientServerInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different ClientServerInterfaces are considered compatible if and only if:

1. For at least one ClientServerOperation defined in the context of the ClientServerInterface of the provided outer PortPrototype a compatible ClientServerOperation exists in the ClientServerInterface of the required outer PortPrototype. Either the shortNames of the ClientServerOperations are used to identify the pair or a ClientServerInterfaceMapping exists that maps the corresponding ClientServerOperations.

2. For each such pair, the values of the PortInterface.isService attributes are identical.
(cid:99)()

#@SECTION: 6.12 Compatibility of Trigger Interfaces
Please note that this compatibility requirement only satisfies static correctness which means that a client shall call a certain operation to allow the server to work correctly. Logical consistency is not assured (e.g. that a client shall call a certain operation to allow the server to work correctly).

#@SECTION: 6.12.1 Connection of Required and Provided Port via AssemblySwConnector
#@CLASS: AssemblySwConnector
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->
#@CLASS: TriggerInterface
<!-- LLM_CONTEXT FOR CLASS TriggerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, trigger, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: TriggerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS TriggerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, triggerMapping, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: Trigger
<!-- LLM_CONTEXT FOR CLASS Trigger: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swImplPolicy, triggerPeriod, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->
#@CLASS: TriggerInterface
<!-- LLM_CONTEXT FOR CLASS TriggerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, trigger, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: TriggerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS TriggerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, triggerMapping, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS PassThroughSwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, providedOuterPort, requiredOuterPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: TriggerInterface
<!-- LLM_CONTEXT FOR CLASS TriggerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, trigger, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: TriggerInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS TriggerInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, triggerMapping, variationPoint] (包含继承及相关属性); Generalization=[PortInterfaceMapping] (直接父类) -->
#@CLASS: Trigger
<!-- LLM_CONTEXT FOR CLASS Trigger: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swImplPolicy, triggerPeriod, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->

[constr_1251] Compatibility of PortPrototypes of TriggerInterfaces in the context of a PassThroughSwConnector (cid:100) PortPrototypes of different Trigger Interfaces are considered compatible if and only if

1. For at least one Trigger defined in the context of the TriggerInterface of the required outer PortPrototype a compatible Trigger exists in the TriggerInterface of the provided outer PortPrototype. Either the shortName of Triggers are used to identify the pair or a Trigger InterfaceMapping exists that refers to one of the Triggers in the role firstTrigger and to the other in the role secondTrigger.

2. For each such pair, the values of the PortInterface.isService attributes are identical.

(cid:99)()

#@SECTION: 6.13 Compatibility of Trigger
#@CLASS: Trigger
<!-- LLM_CONTEXT FOR CLASS Trigger: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swImplPolicy, triggerPeriod, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
[constr_1083] Compatibility of Triggers (cid:100) Triggers are compatible if they have an identical shortName. (cid:99)()

#@SECTION: 6.14 Entire Delegation of a Provided Port Prototype
#@CLASS: ClientServerInterface
<!-- LLM_CONTEXT FOR CLASS ClientServerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, operation, possibleError, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: ClientServerOperation
<!-- LLM_CONTEXT FOR CLASS ClientServerOperation: Attributes=[adminData, annotation, argument, category, desc, introduction, longName, possibleError, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: DelegationSwConnector
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: ModeDeclarationGroupPrototype
<!-- LLM_CONTEXT FOR CLASS ModeDeclarationGroupPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swCalibrationAccess, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: ModeSwitchInterface
<!-- LLM_CONTEXT FOR CLASS ModeSwitchInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, modeGroup, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PassThroughSwConnector
<!-- LLM_CONTEXT FOR CLASS PassThroughSwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, providedOuterPort, requiredOuterPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS PortInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, Identifiable] (直接父类); Childs=[ClientServerInterfaceMapping, ModeInterfaceMapping, TriggerInterfaceMapping, VariableAndParameterInterfaceMapping] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: PRPortPrototype
<!-- LLM_CONTEXT FOR CLASS PRPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedRequiredInterface, requiredComSpec, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: Trigger
<!-- LLM_CONTEXT FOR CLASS Trigger: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, swImplPolicy, triggerPeriod, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement, Identifiable] (直接父类) -->
#@CLASS: TriggerInterface
<!-- LLM_CONTEXT FOR CLASS TriggerInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, trigger, variationPoint] (包含继承及相关属性); Generalization=[PortInterface] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->


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
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->

With the definition of compatibility rules in chapter 6.4, 6.11, and 6.12 it is possible to split and distribute elements of a PortPrototype of type of a PortInterface containing a superset of PortInterface elements to PortPrototypes of type of PortInterfaces containing subsets of PortInterface elements.

Please find examples that explain the usage of splitting and merging in section 6.16.2.

#@SECTION: 6.15 Compatibility in Case of a Flat ECU Extract
#@CLASS: AssemblySwConnector
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: CompositionSwComponentType
<!-- LLM_CONTEXT FOR CLASS CompositionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, component, connector, consistencyNeeds, constantValueMapping, dataTypeMapping, desc, instantiationRTEEventProps, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类) -->
#@CLASS: DelegationSwConnector
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: NvDataInterface
<!-- LLM_CONTEXT FOR CLASS NvDataInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, nvData, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: ParameterDataPrototype
<!-- LLM_CONTEXT FOR CLASS ParameterDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->
#@CLASS: ParameterInterface
<!-- LLM_CONTEXT FOR CLASS ParameterInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, parameter, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: PortInterface
<!-- LLM_CONTEXT FOR CLASS PortInterface: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[ARElement, AtpBlueprint, AtpBlueprintable, AtpType] (直接父类); Childs=[ClientServerInterface, DataInterface, ModeSwitchInterface, TriggerInterface] (直接子类) -->
#@CLASS: PortInterfaceMapping
<!-- LLM_CONTEXT FOR CLASS PortInterfaceMapping: Attributes=[adminData, annotation, blueprintPolicy, category, desc, introduction, longName, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprint, AtpBlueprintable, Identifiable] (直接父类); Childs=[ClientServerInterfaceMapping, ModeInterfaceMapping, TriggerInterfaceMapping, VariableAndParameterInterfaceMapping] (直接子类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SenderReceiverInterface
<!-- LLM_CONTEXT FOR CLASS SenderReceiverInterface: Attributes=[adminData, annotation, blueprintPolicy, category, dataElement, desc, introduction, invalidationPolicy, isService, longName, serviceKind, shortName, shortNameFragment, shortNamePattern, variationPoint] (包含继承及相关属性); Generalization=[DataInterface] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->

This section provides some examples that may explain the compatibility of PortPrototypes.

#@SECTION: 6.16.1 Compatibility on Assembly Level
#@CLASS: AssemblySwConnectors
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnectors: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->

The rules for compatibility with respect to the connection of dataElements by means of AssemblySwConnectors are perhaps easier to digest than the delegation case but nonetheless it seems appropriate to provide a set of examples that illustrate the compatibility issue.

#@SECTION: 6.16.1.1 Legal Use
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS AssemblySwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, provider, requester, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS CompositionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, component, connector, consistencyNeeds, constantValueMapping, dataTypeMapping, desc, instantiationRTEEventProps, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类) -->
#@CLASS: DelegationSwConnectors
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnectors: Attributes=[] (元数据中未找到该类、其父类或相关Content类的任何属性) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->

The rules for compatibility with respect to the delegation of dataElements perhaps require some explanation in terms of examples. The first example 6.4 describes a legal situation where two DelegationSwConnectors split the dataElements contained in the RPortPrototype owned by a CompositionSwComponentType.

#@SECTION: 6.16.2.1 Legal Use
#@CLASS: CompositionSwComponentType
<!-- LLM_CONTEXT FOR CLASS CompositionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, component, connector, consistencyNeeds, constantValueMapping, dataTypeMapping, desc, instantiationRTEEventProps, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类) -->
#@CLASS: DelegatedPortAnnotation
<!-- LLM_CONTEXT FOR CLASS DelegatedPortAnnotation: Attributes=[annotationOrigin, annotationText, label, signalFan] (包含继承及相关属性); Generalization=[GeneralAnnotation] (直接父类) -->
#@CLASS: DelegationSwConnector
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: PortPrototype
<!-- LLM_CONTEXT FOR CLASS PortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AtpBlueprintable, AtpPrototype] (直接父类); Childs=[AbstractProvidedPortPrototype, AbstractRequiredPortPrototype] (直接子类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: VariableDataPrototype
<!-- LLM_CONTEXT FOR CLASS VariableDataPrototype: Attributes=[adminData, annotation, category, desc, initValue, introduction, longName, shortName, shortNameFragment, swDataDefProps, type, variationPoint] (包含继承及相关属性); Generalization=[AutosarDataPrototype] (直接父类) -->

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
<!-- LLM_CONTEXT FOR CLASS CompositionSwComponentType: Attributes=[adminData, annotation, blueprintPolicy, category, component, connector, consistencyNeeds, constantValueMapping, dataTypeMapping, desc, instantiationRTEEventProps, introduction, longName, port, portGroup, shortName, shortNameFragment, shortNamePattern, swComponentDocumentation, unitGroup, variationPoint] (包含继承及相关属性); Generalization=[SwComponentType] (直接父类) -->
#@CLASS: DelegationSwConnector
<!-- LLM_CONTEXT FOR CLASS DelegationSwConnector: Attributes=[adminData, annotation, category, desc, innerPort, introduction, longName, mapping, outerPort, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[SwConnector] (直接父类) -->
#@CLASS: PPortPrototype
<!-- LLM_CONTEXT FOR CLASS PPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, providedComSpec, providedInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractProvidedPortPrototype] (直接父类) -->
#@CLASS: RPortPrototype
<!-- LLM_CONTEXT FOR CLASS RPortPrototype: Attributes=[adminData, annotation, category, clientServerAnnotation, delegatedPortAnnotation, desc, introduction, ioHwAbstractionServerAnnotation, longName, modePortAnnotation, nvDataPortAnnotation, parameterPortAnnotation, requiredComSpec, requiredInterface, senderReceiverAnnotation, shortName, shortNameFragment, triggerPortAnnotation, variationPoint] (包含继承及相关属性); Generalization=[AbstractRequiredPortPrototype] (直接父类) -->
#@CLASS: SwComponentPrototype
<!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[adminData, annotation, category, desc, introduction, longName, shortName, shortNameFragment, type, variationPoint] (包含继承及相关属性); Generalization=[AtpPrototype] (直接父类) -->
#@CLASS: SwConnector
<!-- LLM_CONTEXT FOR CLASS SwConnector: Attributes=[adminData, annotation, category, desc, introduction, longName, mapping, shortName, shortNameFragment, variationPoint] (包含继承及相关属性); Generalization=[AtpStructureElement] (直接父类); Childs=[AssemblySwConnector, DelegationSwConnector, PassThroughSwConnector] (直接子类) -->

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