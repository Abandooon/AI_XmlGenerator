#@SECTION: 5.2.5 Implementation Data Type
#@CLASS: ImplementationDataType
#@CLASS: ImplementationDataTypeElement
#@CLASS: SwPointerTargetProps
#@CLASS: SwDataDefProps
#@CLASS: SwBaseType
#@CLASS: BswModuleEntry
#@CLASS: ImplementationProps
#@CLASS: SymbolProps

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

SwPointerTargetProps

Class Package M2::AUTOSARTemplates::CommonStructure::DataDefProperties Note This element defines, that the data object (which is specified by the aggregating element) contains a reference to another data object or to a function in the CPU code. This corresponds to a pointer in the C-language.

Base Attribute functionPointerSignature The attributes of this element describe the category and the detailed properties of the target which is either a data description or a function signature. ARObject Datatype BswModuleEntry ref The referenced BswModuleEntry serves as the Mul. Kind Note 0..1 signature of a function pointer definition. Primary use case: function pointer passed as argument to other function.

swDataDefProps SwDataDefProps Tags: xml.sequenceOffset=40 0..1 aggr The properties of the target data type.

targetCategory Identifier 0..1 ref This specifies the category of the target: Tags: xml.sequenceOffset=30 • In case of a data pointer, it shall specify the category of the referenced data. • In case of a function pointer, it could be used to denote the category of the referenced BswModuleEntry. Since currently no categories for BswModuleEntry are defined it will be empty. Tags: xml.sequenceOffset=5

Table 5.21: SwPointerTargetProps

The allowed existence and multiplicity of all the attributes of SwDataDefProps and other properties depend on the category of the ImplementationDataType.

Figure 5.15: SwDataDefProps used in the context of ImplementationDataType

[constr_1178] Existence of attributes of SwDataDefProps in the context of ImplementationDataType (cid:100) For the sake of removing possible sources of ambiguity, SwDataDefProps used in the context of ImplementationDataType can only have one of • baseType • swPointerTargetProps • implementationDataType (cid:99)()

Please note that an ImplementationDataType manifests itself in the source code of an RTE into which a DataPrototype typed by the ImplementationDataType is deployed. This implies potential naming conflicts if ImplementationDataTypes that have identical shortNames are deployed into a specific RTE.

[TPS_SWCT_01194] Symbolic name of an ImplementationDataType (cid:100) To mitigate this potential hazard it is possible to provide the ImplementationDataType along with an accompanying symbolic name that can be used for resolving the name clash. The symbolic name is provided by means of the attribute symbol of the meta-class SymbolProps owned by ImplementationDataType in the role symbolProps (for more information, please refer to Figure 5.11). (cid:99)()

[TPS_SWCT_01441] Nature of a TYPE_REFERENCE (cid:100) A type reference (formally represented by an ImplementationDataType of category TYPE_REFERENCE) implements a redirection to common ImplementationDataTypes. (cid:99)()

[TPS_SWCT_01442] ImplementationDataType of category TYPE_REFERENCE does not define own properties (cid:100) As long as an ImplementationDataType of category TYPE_REFERENCE does not define own properties the properties of the refined ImplementationDataType apply. (cid:99)()

[TPS_SWCT_01443] ImplementationDataType of category TYPE_REFERENCE overwrites properties of refined ImplementationDataType (cid:100) If an implementation data types of category TYPE_REFERENCE defines own properties (e.g. CompuMethod) this properties overwrite the properties of the refined ImplementationDataType. (cid:99)()

As explained by [constr_1050], Compatibility checks of ImplementationDataType require a prior resolution of possible type references, i.e. the compatibility shall be checked on the resolved ImplementationDataType.

Figure 5.16: ImplementationProps and its subclasses

ImplementationProps (abstract)

Class Package M2::AUTOSARTemplates::CommonStructure::Implementation Note Defines a symbol to be used as (depending on the concrete case) either a complete replacement or a prefix when generating code artifacts. ARObject,Referrable Datatype CIdentifier ref The symbol to be used as (depending on the Mul. Kind Note 1 Base Attribute symbol concrete case) either a complete replacement or a prefix.

Table 5.22: ImplementationProps
Table 5.23: SymbolProps