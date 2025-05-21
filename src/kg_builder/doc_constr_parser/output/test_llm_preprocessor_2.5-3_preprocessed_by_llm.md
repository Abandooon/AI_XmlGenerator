#@SECTION: 2.5 Communication Speciﬁcation of Composition Component Types
#@CLASS: CompositionSwComponentType
#@CLASS: PortPrototype
#@CLASS: AtomicSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: ConstantSpecificationMappingSet
#@CLASS: DataTypeMappingSet
#@CLASS: DelegationSwConnector
#@CLASS: ParameterSwComponentType
#@CLASS: PortInterface
#@CLASS: PPortComSpec
#@CLASS: RPortComSpec
#@CLASS: SwComponentPrototype

[TPS_SWCT_01088] ComSpecs defined by CompositionSwComponentTypes (cid:100) It shall be possible to attach ComSpecs to PortPrototypes owned by CompositionSwComponentTypes. (cid:99)(RS_SWCT_03220)

#@SECTION: 2.5.1 Rationale

ComSpecs attached to a PortPrototype owned by an AtomicSwComponentType have a direct impact on the generation of the RTE. The RTE Generator, on the other hand, does not consider the existence of CompositionSwComponentTypes.

Nevertheless, there are some cases where the definition of a ComSpec attached to a PortPrototype owned by a CompositionSwComponentType does make sense. That is, in case an OEM wants to submit the definition of a CompositionSwComponentType to a supplier for adding more details and implementing the behavior the OEM might want to point out that from the OEM’s point of view sender initValues and receiver initValues apply for the elements of PortInterfaces used to type the delegation PortPrototypes.

The idea is that the supplier takes over the initValues attached to the delegation PortPrototypes and copies them to the PortPrototypes owned by SwComponentPrototypes of the CompositionSwComponentType.

[TPS_SWCT_01568] Consideration of RPortComSpec or PPortComSpec depending on the ownership (cid:100) The RTE Generator shall take the attributes of the RPortComSpec or PPortComSpec of the PortPrototypes owned by AtomicSwComponentTypes or ParameterSwComponentType and ignore the attributes of the RPortComSpec or PPortComSpec attached to PortPrototypes owed by CompositionSwComponentType. (cid:99)(RS_SWCT_03220)

Therefore, the initValues of the delegation PortPrototype would be taken as mere templates for the detailing of PortPrototypes connected to the delegation PortPrototypes. It is not required that the initValues of delegated PortPrototype and a PortPrototype connected by means of a DelegationSwConnector match. Although this would certainly make sense in many cases it is eventually still left to the supplier to decide on the specific initValues applicable inside the CompositionSwComponentType.

On the other hand, a requirement that the initValues defined on the surface of CompositionSwComponentType and the inside of the CompositionSwComponentType shall be consistent in any case might effectively prevent the reuse of existing AtomicSwComponentTypes.

Please note that the ability to define a ComSpec in the context of a CompositionSwComponentType implies that it shall be possible to define mappings of ApplicationDataTypes used in a PortInterface to their corresponding ImplementationDataTypes. For this purpose the CompositionSwComponentType owns a DataTypeMappingSet in the role dataTypeMapping and a ConstantSpecificationMappingSet in the role constantValueMapping.

Figure 2.6: Specification of data type mapping for CompositionSwComponentType

#@SECTION: 2.6 PRPortPrototype
#@CLASS: NvBlockSwComponentType
#@CLASS: PortPrototype
#@CLASS: SwComponentType
#@CLASS: ApplicationSwComponentType
#@CLASS: PPortPrototype
#@CLASS: PRPortPrototype
#@CLASS: RPortPrototype
#@CLASS: ApplicationSwComponentType
#@CLASS: CompositionSwComponentType
#@CLASS: RunnableEntity

In some cases SwComponentTypes need to read and write the same piece of data. One of the most prominent examples for this use case is the NvBlockSwComponentType that factually ready and writes blocks of NvRAM. Without the ability to combine read and write semantics in a kind of PortPrototype that supports both read and write semantics work-arounds have to be implemented that come with a certain footprint on memory and processing time.

#@SECTION: 2.6.1 Use Case 1

Without the ability to define a combined read and write semantics the definition of an RPortPrototype and a PPortPrototype is required for reading and writing the applicable data.

Figure 2.7: Use Case 1 for the existence of PRPortPrototype

Technically, this read and write access is related to the same data item in an NVRAM Block. This requires a consistent connection of the PortPrototypes between an NvBlockSwComponentType and ApplicationSwComponentType as well as a consistent mapping of the corresponding RPortPrototype and a PPortPrototype of the NvBlockSwComponentType and the related element of the ramBlock.

#@SECTION: 2.6.2 Use Case 2

It may happen that a SwComponentType need to consume the same data that it produces. If the only way to achieve this was the connection of a PPortPrototype to an RPortPrototype of the same SwComponentType then the creator of the SwComponentType cannot enforce this connection as it is created on a higher level of abstraction in the context of a CompositionSwComponentType.

In other words, it is impossible to fully specify the semantics of the otherwise self contained SwComponentType.

Figure 2.8: Use Case 2 for the existence of PRPortPrototype

This means that only in the in best case one buffer for the data is needed. But depending on the mapping RunnableEntitys to OS tasks additional buffers may need to be allocated by the RTE to fully implement the implicit communication pattern.

As an alternative, the ApplicationSwComponentType could utilize inter-runnable variables but unfortunately this inhibits any optimization in the RTE and will consume additional RAM. In contrast to the previous approach at least two buffers are needed.

#@SECTION: 2.6.3 Use Case 3

In this scenario, several ApplicationSwComponentTypes are iterating over the same large set of data. This means each ApplicationSwComponentType implements one out of many steps of a complex data processing algorithm applied to the same piece of data.

Figure 2.9: Use Case 3 for the existence of PRPortPrototype

For example, this scenario may apply for video signal processing in camera applications. Typically, such applications will not be distributed over several ECUs. It is clear that in this case the allocation of several buffers in the RTE is required to implement the individual connections between the ApplicationSwComponentTypes. In most cases, the processing has to be executed at a certain point in time in a dedicated order.

#@SECTION: 2.6.4 Solution

The solution to the above-mentioned use cases is the ability to define a PortPrototype that can read and write the same piece of data. This solves both the described problem of resource consumption as well as the problem of having to define multiple PortPrototypes as outlets for same piece of data item.

The technical details of the definition of PRPortPrototype are explained in chapters 3.1 and 4.1.

#@SECTION: 2.7 Pretended Networking

#@CLASS: ModeDeclaration
#@CLASS: ModeDeclarationGroup
#@CLASS: ModeSwitchInterface
#@CLASS: PPortPrototype
#@CLASS: RPortPrototype
#@CLASS: SenderReceiverInterface
#@CLASS: SwComponentType
#@CLASS: AutosarDataType
#@CLASS: ModeDeclarationGroupPrototype
#@CLASS: VariableDataPrototype
#@CLASS: PortInterface
[TPS_SWCT_01510] The role of pretended networking (cid:100) Pretended networking is a feature to reduce energy consumption of an ECU by switching the ECU in a mode called Pretended Networking. In this mode the communication on communication networks is reduced and the ECU can go into power saving modes.
When communication via communication networks is required the mode Pretended Networking shall be left by request of a mode change to Normal Mode. (cid:99)()

[TPS_SWCT_01511] Configuration option is encoded into ModeDeclaration (cid:100) The identification of different configuration options for Pretended Networking shall be encoded into the definition of dedicated ModeDeclarations inside a ModeDeclarationGroup. (cid:99)(RS_SWCT_03110)

For example, assume that an implementation of pretended networking supports three configuration options:
• PRETENDED_NW_MODE_OFF
• PRETENDED_NW_MODE_ONE
• PRETENDED_NW_MODE_TWO

In this example case, a ModeDeclarationGroup consisting of three ModeDeclarations shall be defined where each ModeDeclaration shall represent one of the above-mentioned configuration options. The shortNames of the ModeDeclaration shall be taken from the above-mentioned list.

[TPS_SWCT_01512] Request change of Pretended Networking mode (cid:100) A SwComponentType that needs to be able to request a change in the operating mode of Pretended Networking shall provide a PPortPrototype typed by a SenderReceiverInterface (see [TPS_SWCT_01086]) for requesting a change (towards the BswM [15]) of the Pretended Networking mode.

It is out of the scope of this document to define the particular properties of the applicable SenderReceiverInterface. The details of this specific SenderReceiverInterface can be found in the specification of the BswM [15]. (cid:99)(RS_SWCT_03110)

More details about how a mode change is requested can be found in section 9.

[TPS_SWCT_01513] React on the change of Pretended Networking mode (cid:100) A SwComponentType that needs to be able to react on a change in the operating mode of Pretended Networking shall provide an RPortPrototype typed by a ModeSwitchInterface (see [TPS_SWCT_01087]) for reacting on a change (initiated by the BswM [15]) of the Pretended Networking mode.

It is out of the scope of this document to define the particular properties of the applicable ModeSwitchInterface. The details of this specific ModeSwitchInterface can be found in the specification of the BswM [15]. (cid:99)(RS_SWCT_03110)

#@SECTION: 2.8 Variable-size Array Data Types
#@CLASS: ApplicationArrayDataType
#@CLASS: ImplementationDataType
#@CLASS: ApplicationArrayElement
#@CLASS: ImplementationDataTypeElement
#@CLASS: ApplicationDataType
#@CLASS: DataTypeMap

#@SECTION: 2.8.1 Overview and Use cases

AUTOSAR supports the definition of array data types where the size of the actual payload varies at run-time. As far as the configuration is concerned, it is possible to specify a maximum number of array elements that shall not be exceeded at run-time.
In order to properly understand the approach, it is necessary to understand that the support for Variable-Size Array Data Types has been introduced in two waves that each had a different motivation.

#@SECTION: 2.8.1.1 “Old-world” dynamic-size Arrays

In the ﬁrst wave, the support for Variable-Size Array Data Types was limited to data types that basically boil down to an array where the base type is an unsigned integer data type with a length of exactly one byte.

The main use cases for this scenario are derived from diagnostics requirements as well as support for the J1939 communication protocol.

In both cases the actual length of a Variable-Size Array Data Type could be determined from the context, i.e. either by the diagnostic basic-software module or by the implementation of the J1939 TP.

For the lack of a better terminology, this speciﬁcation distinguishes between “old-world” dynamic-size arrays and “new-world” Variable-Size Array Data Types. It will be necessary to clearly deﬁne the characteristics that allow for an disambiguation between the “old-world” dynamic-size arrays and “new-world” Variable-Size Array Data Types.

[TPS_SWCT_01641] Deﬁnition of an “old-world” dynamic-size array data type by means of an ApplicationArrayDataType (cid:100) An ApplicationArrayDataType that doesn’t deﬁne attribute dynamicArraySizeProfile and that aggregates an ApplicationArrayElement where attribute arraySizeSemantics exists and is set to the value variableSize shall be considered an “old-world” dynamic-size array data type. (cid:99)(RS_SWCT_03181)

Please note that [TPS_SWCT_01641] can’t go any deeper into the speciﬁcs of the given data type because it is intentionally focused on ApplicationDataTypes. There are use cases where the distinction between “old-world” dynamic-size arrays and “new-world” Variable-Size Array Data Types must be done in the absence of a corresponding ImplementationDataType.

In general, the disambiguation becomes multi-faceted (but not necessarily easier) if the deﬁnition of a corresponding ImplementationDataType is available (see [TPS_SWCT_01642]).

[TPS_SWCT_01642] Deﬁnition of an “old-world” dynamic-size array data type by means of an ImplementationDataType (cid:100) An ImplementationDataType that (after all type references are resolved) fulﬁlls all of the following conditions shall be considered an “old-world” dynamic-size array data type:

• The value of attribute category is set to ARRAY
• The ImplementationDataType doesn’t deﬁne the attribute dynamicArraySizeProfile
• The ImplementationDataType aggregates a subElement where
  – attribute arraySizeSemantics exists and is set to the value variableSize
  – attribute arraySizeHandling does not exist
• The ImplementationDataType.swDataDefProps.baseType exists and the attribute
  – baseTypeEncoding exists and is set to the value NONE
  – baseTypeSize exists and is set to the value 8
(cid:99)(RS_SWCT_03181)

By and large, the deﬁning characteristics for “old-world” dynamic-size arrays is the absence of a deﬁnition of the attribute ApplicationArrayDataType.dynamicArraySizeProfile resp. ImplementationDataType.dynamicArraySizeProfile.

By regulation of [constr_1387], “old-world” dynamic-size arrays are not supported for transmission by means of a data transformer. The only supported kind of Variable Size Array Data Type that can be transmitted using a data transformer is the “new-world” variable-size arrays.

#@SECTION: 2.8.1.2 “New-world” variable-size Arrays

In contrast to this, the second wave of support for Variable-Size Array Data Types was motivated by the application software layer itself.

Here, the situation is entirely different because the actual size cannot be determined by any context software module. The application itself is responsible for maintaining the proper length of a Variable-Size Array Data Type at run-time.

As a consequence, the speciﬁcation of the actual array size at run-time needs to be reﬂected by the structure of the data types used for hosting the Variable-Size Array Data Type.

[TPS_SWCT_01644] Deﬁnition of a “new-world” variable-size array data type by means of an ApplicationArrayDataType (cid:100) An ApplicationArrayDataType that fulﬁlls all of the following conditions shall be considered an “new-world” dynamic size array data type.
• The ApplicationArrayDataType deﬁnes attribute ApplicationArrayDataType.dynamicArraySizeProfile.
• ApplicationArrayDataType aggregates an ApplicationArrayElement that deﬁnes attribute ApplicationArrayElement.arraySizeHandling.
(cid:99)(RS_SWCT_03181)

[TPS_SWCT_01645] Deﬁnition of a “new-world” variable-size array data type by means of an ImplementationDataType (cid:100) An ImplementationDataType that fulﬁlls all of the following conditions shall be considered an “new-world” dynamic-size array data type.
• The ImplementationDataType deﬁnes attribute ImplementationDataType.dynamicArraySizeProfile.
• ImplementationDataType aggregates an ImplementationDataTypeElement that deﬁnes attribute ImplementationDataTypeElement.arraySizeHandling.
(cid:99)(RS_SWCT_03181)

In contrast to the ﬁrst use case described above, the application-motivated Variable Size Array Data Type cannot be limited in terms of the base type of the array data type, i.e. limiting the underlying data type to an unsigned integer data type with a length of exactly one byte is not an option.

On top of that, several possible structures of Variable-Size Array Data Types have been required. This aspect is depicted in Figure 2.10.

[TPS_SWCT_01636] Deﬁnition of proﬁles for the deﬁnition of Variable-Size Array Data Types (cid:100) The possible variants for Variable-Size Array Data Types are:
Linear The data type of the elements of the Variable-Size Array Data Type itself does not consist of a Variable-Size Array Data Type. This case corresponds to the tag (a) in Figure 2.10. This case corresponds to the possible value VSA_LINEAR of attribute dynamicArraySizeProfile.
Square The data type of the elements of the Variable-Size Array Data Type itself consists of Variable-Size Array Data Types where the maximum number of elements in all “second order” arrays is identical to the maximum number of elements in the “ﬁrst order” array. This case corresponds to the tag (b) in Figure 2.10. This case corresponds to the possible value VSA_SQUARE of attribute dynamicArraySizeProfile.
Rectangular The data type of the elements of the Variable-Size Array Data Type itself consists of Variable-Size Array Data Types data types where the maximum number of elements in “second order” arrays is identical but this value is typically not identical3 to the maximum number of elements in the “ﬁrst order” array. This case corresponds to the tag (c) in Figure 2.10. This case corresponds to the possible value VSA_RECTANGULAR of attribute dynamicArraySizeProfile.
Fully Flexible The data type of the elements of the Variable-Size Array Data Type itself consists of Variable-Size Array Data Types where the maximum number of elements in “second order” arrays is not necessarily identical with each other and (obviously) not necessarily identical to the maximum number of elements in the “ﬁrst order” array. This case corresponds to the tag (d) in Figure 2.10. This case corresponds to the possible value VSA_FULLY_FLEXIBLE of attribute dynamicArraySizeProfile.
(cid:99)(RS_SWCT_03181)

Figure 2.10: Structural variety of array data types with variable size

Please note that the leaf elements in a Variable-Size Array Data Type doesn’t have to be primitive data types. As mentioned before, it is possible to deﬁne multiple dimension Variable-Size Array Data Types. The “terminal” elements can be recognized as such in that they don’t establish further Variable-Size Array Data Types.

#@SECTION: 2.8.2 Modeling Aspects regarding Application Data Types

In the context of the AUTOSAR layered data type concept, the level of ApplicationDataTypes is not concerned about the structure of how the Variable-Size Array Data Types. If it was, the case boils down to the rectangular scenario tagged (b).

In other words, aspects of the implementation of this kind of data type is intentionally abstracted as much as possible in order to support the idea behind the definition of ApplicationDataTypes as a concept that is independent from an implementation to the applicable degree.

Consequently, the support for Variable-Size Array Data Types on the level of ApplicationDataTypes requires the addition of a couple of additional attributes. Details can be found in chapter 5.2.4.2.

If a Variable-Size Array Data Type is modeled on the level of ApplicationDataType it is necessary to also provide a companion ImplementationDataType as well as a DataTypeMap that refers to both the ApplicationDataType and the ImplementationDataType.

The contrary is not applicable, i.e. it is possible to define a Variable-Size Array Data Type with only an ImplementationDataType, see [TPS_SWCT_01622].

#@SECTION: 2.8.3 Modeling Aspects regarding Implementation Data Types

On the other hand, the data type used for the actual hosting of the Variable Size Array Data Type corresponds directly to the level of the Implementation DataType. Here, it is possible to define how an ImplementationDataType can be used to define a Variable-Size Array Data Type. The definition of ImplementationDataType in the AUTOSAR meta-model comes with a certain level of generic nature the support for Variable-Size Array Data Types on this level comes as a mixture of dedicated attributes in the meta-model and a set of recipes how to support different use cases of Variable-Size Array Data Types. This means that the definition of ImplementationDataTypes for the purpose of creating Variable-Size Array Data Types only has a chance to take off if the structure of these data types is replicated in different implementations of AUTOSAR software. Therefore, AUTOSAR defines a common way of how ImplementationDataTypes for the purpose of creating Variable-Size Array Data Types shall be defined such that the ImplementationDataType shall be of category STRUCTURE with the following sub-elements:
1. A numerical value that determines the actual size. This element shall be called the Size Indicator throughout this document.
2. An array of the base-type of the Variable-Size Array Data Type that implements the payload of the Variable-Size Array Data Type. The dimension of the array shall be defined such that the intended maximum number of elements fits in.

A Size Indicator of a Variable-Size Array Data Type holds the number of valid elements of the array. This information is necessary for the RTE to handle the array efficiently.

On the sender-side this indicator is actively updated by the software-component which is the only instance that knows how many elements of the array are valid. So the number of valid elements and the Size Indicator have to be kept consistent by the application. When the software-component sends the data over the RTE the RTE hands the data over to the transformer.

The transformer may evaluate the Size Indicator (depends on the transformer) and only work on the valid array elements. The output of the transformer can vary in length and only contain necessary data. Therefore it can be more resource saving.

On the receiver side, the last transformer in the execution order restores the data elements of the array and the value of the Size Indicator. This output is handed over by the RTE to the software-component. The application now is aware of the number of valid elements in the array.

The details of how ImplementationDataTypes need to be modeled for the implementation of Variable-Size Array Data Types can be found in chapter 5.2.5 and a couple of examples is available in the appendix E.1.