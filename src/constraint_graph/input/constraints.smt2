(set-logic ALL)
; 4.3.1_Constr_SwConnector_PIMReference
(declare-sort SwConnector 0)
(declare-sort PortInterfaceMapping 0)

; SwConnector kinds (assembly / delegation / pass-through)
(declare-fun isAssemblySwConnector (SwConnector) Bool)
(declare-fun isDelegationSwConnector (SwConnector) Bool)
(declare-fun isPassThroughSwConnector (SwConnector) Bool)

; Reference from SwConnector to PortInterfaceMapping (optional)
(declare-fun mappingRef (SwConnector) PortInterfaceMapping)
(declare-fun hasMappingRef (SwConnector) Bool)

; Predicate: a given PortInterfaceMapping is applied by a SwConnector
(declare-fun appliesMapping (SwConnector PortInterfaceMapping) Bool)

; If a PortInterfaceMapping is applied by a SwConnector, then that SwConnector references it.
(assert
  (forall ((s SwConnector) (m PortInterfaceMapping))
    (=> (appliesMapping s m)
        (and (hasMappingRef s)
             (= (mappingRef s) m)))))

; ComMgrUserNeeds_PortGroupAssociation
(declare-sort ComMgrUserNeeds 0)
(declare-sort PortGroup 0)

; Optional association from ComMgrUserNeeds to PortGroup
(declare-fun representedPortGroup (ComMgrUserNeeds) PortGroup)
(declare-fun hasRepresentedPortGroup (ComMgrUserNeeds) Bool)

; Each ComMgrUserNeeds, if it has a representedPortGroup, is associated to exactly that PortGroup.
(assert
  (forall ((u ComMgrUserNeeds))
    (=> (hasRepresentedPortGroup u)
        (exists ((pg PortGroup))
          (and (= pg (representedPortGroup u))
               (forall ((pg2 PortGroup))
                 (=> (= pg2 (representedPortGroup u))
                     (= pg2 pg))))))))

; Constr_4.8_BSWInterfacingAlternatives
(declare-sort BswInterfaceUser 0)

; Three alternative standardized interfacing mechanisms
(declare-fun usesComM_UserRequest_GetCurrentComMode (BswInterfaceUser) Bool)
(declare-fun usesComM_CurrentMode_currentMode (BswInterfaceUser) Bool)
(declare-fun usesAppModeInterface_currentMode (BswInterfaceUser) Bool)

; Exactly one of the three alternatives shall be used
(assert
  (forall ((u BswInterfaceUser))
    (let ((a (usesComM_UserRequest_GetCurrentComMode u))
          (b (usesComM_CurrentMode_currentMode u))
          (c (usesAppModeInterface_currentMode u)))
      (and
        ; at least one
        (or a b c)
        ; pairwise exclusiveness
        (not (and a b))
        (not (and a c))
        (not (and b c))))))

; Constr_4.8_ComMRetrievalChoice
(declare-sort SwComponent 0)

; Two alternative retrieval mechanisms for ComM
(declare-fun usesClientServerInterfaceForComM (SwComponent) Bool)
(declare-fun usesSenderReceiverInterfaceForComM (SwComponent) Bool)

; The author may choose either alternative (or both); no hard structural constraint is enforced.
; We only capture that at least one mechanism is used if ComM is retrieved.
(declare-fun retrievesComM (SwComponent) Bool)

(assert
  (forall ((c SwComponent))
    (=> (retrievesComM c)
        (or (usesClientServerInterfaceForComM c)
            (usesSenderReceiverInterfaceForComM c)))))

; Constr_4.8_PartialNetworkStatusCheck
(declare-sort PartialNetwork 0)
(declare-sort PortPrototype 0)

; Relations
(declare-fun belongsToPartialNetwork (PortPrototype PartialNetwork) Bool)
(declare-fun isActivePartialNetwork (PartialNetwork) Bool)

; Software component using a port to communicate
(declare-fun usesPortForCommunication (SwComponent PortPrototype) Bool)

; Before communicating via a port that belongs to a partial network,
; the software component shall consider the status of that partial network and assert its activity.
(declare-fun considersPartialNetworkStatus (SwComponent PartialNetwork) Bool)

(assert
  (forall ((c SwComponent) (p PortPrototype) (pn PartialNetwork))
    (=> (and (usesPortForCommunication c p)
             (belongsToPartialNetwork p pn))
        (and (considersPartialNetworkStatus c pn)
             (isActivePartialNetwork pn)))))


; Constr_4.9_ConsistencyNeedsDefinitionContext
; The information (ConsistencyNeeds) can be defined for AtomicSwComponentType and also for CompositionSwComponentType.

(declare-sort AtomicSwComponentType 0)
(declare-sort CompositionSwComponentType 0)
(declare-sort ConsistencyNeeds 0)

; Whether a given AtomicSwComponentType / CompositionSwComponentType has ConsistencyNeeds defined
(declare-fun hasConsistencyNeeds_Atomic (AtomicSwComponentType ConsistencyNeeds) Bool)
(declare-fun hasConsistencyNeeds_Composition (CompositionSwComponentType ConsistencyNeeds) Bool)

; No additional logical restriction beyond allowing both contexts, so no further axioms.


; Constr_AppImplDataTypeMap_VSADT
; If a Variable-Size Array Data Type (VSADT) is modeled as an ApplicationDataType,
; then there must exist a companion ImplementationDataType and a DataTypeMap that refers to both.

(declare-sort ApplicationDataType 0)
(declare-sort ImplementationDataType 0)
(declare-sort DataTypeMap 0)

; Predicate: this ApplicationDataType is a Variable-Size Array Data Type
(declare-fun isVSADT (ApplicationDataType) Bool)

; Relations: mapping between ApplicationDataType, ImplementationDataType and DataTypeMap
(declare-fun hasCompanionImplType (ApplicationDataType ImplementationDataType) Bool)
(declare-fun dataTypeMapRefersTo (DataTypeMap ApplicationDataType ImplementationDataType) Bool)

; For every VSADT ApplicationDataType, there exists at least one companion ImplementationDataType
; and at least one DataTypeMap that refers to both.
(assert
  (forall ((a ApplicationDataType))
    (=> (isVSADT a)
        (exists ((i ImplementationDataType) (m DataTypeMap))
          (and (hasCompanionImplType a i)
               (dataTypeMapRefersTo m a i))))))


; Constr_AppRecord_AppArray_Compatibility
; An instance of ApplicationRecordDataType is never compatible to an instance of
; ApplicationArrayDataType unless a PortInterfaceMapping exists that details compatibility.

(declare-sort ApplicationRecordDataType 0)
(declare-sort ApplicationArrayDataType 0)

; Compatibility between a record and an array data type
(declare-fun compatible_Record_Array (ApplicationRecordDataType ApplicationArrayDataType) Bool)

; Existence of a PortInterfaceMapping that details compatibility between the two
(declare-fun hasPortInterfaceMapping
  (PortInterfaceMapping ApplicationRecordDataType ApplicationArrayDataType) Bool)

; If record/array are compatible, then there exists a PortInterfaceMapping that details this.
(assert
  (forall ((r ApplicationRecordDataType) (a ApplicationArrayDataType))
    (=> (compatible_Record_Array r a)
        (exists ((p PortInterfaceMapping))
          (hasPortInterfaceMapping p r a)))))

; Optional strengthening (never compatible without mapping)
(assert
  (forall ((r ApplicationRecordDataType) (a ApplicationArrayDataType))
    (=> (not (exists ((p PortInterfaceMapping)) (hasPortInterfaceMapping p r a)))
        (not (compatible_Record_Array r a)))))


; Constr_App_SizeIndicatorConsistency
; The number of valid elements and the Size Indicator have to be kept consistent by the application.

; Abstract element container with a size indicator
(declare-sort ElementContainer 0)

; Number of valid elements in the container
(declare-fun numValidElements (ElementContainer) Int)

; Size indicator value stored by the application
(declare-fun sizeIndicator (ElementContainer) Int)

; Consistency requirement: they must be equal (whenever both are defined in the model).
(assert
  (forall ((c ElementContainer))
    (= (numValidElements c) (sizeIndicator c))))


; Constr_ApplicationCompositeDataType_SemanticMeaning
; An ApplicationCompositeDataType cannot be given a particular semantic meaning as a whole,
; but semantics can be specified for contained ApplicationPrimitiveDataTypes.

(declare-sort ApplicationCompositeDataType 0)
(declare-sort ApplicationPrimitiveDataType 0)
(declare-sort SemanticConcept 0)

; Part-of relation: primitive is contained in composite
(declare-fun containsPrimitive
  (ApplicationCompositeDataType ApplicationPrimitiveDataType) Bool)

; Semantic annotations
(declare-fun hasSemanticMeaning_Composite
  (ApplicationCompositeDataType SemanticConcept) Bool)
(declare-fun hasSemanticMeaning_Primitive
  (ApplicationPrimitiveDataType SemanticConcept) Bool)

; A composite must not have a semantic meaning as a whole.
(assert
  (forall ((c ApplicationCompositeDataType) (s SemanticConcept))
    (not (hasSemanticMeaning_Composite c s))))

; Semantics may be attached to contained primitives (allowed, not enforced).
; No additional axioms needed.


; Constr_ApplicationDataType_Precedence
; If an ApplicationDataType is referenced via valueAxisDataType, this supersedes
; CompuMethod, Unit, and BaseType if these are defined in parallel.

(declare-sort SW-DATA-DEF-PROPS-CONTENT 0)
(declare-sort APPLICATION-DATA-TYPE 0)
(declare-sort COMPU-METHOD 0)
(declare-sort UNIT 0)
(declare-sort SW-BASE-TYPE 0)

(declare-fun hasValueAxisDataType (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun valueAxisDataType (SW-DATA-DEF-PROPS-CONTENT) APPLICATION-DATA-TYPE)

(declare-fun hasCompuMethod (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun compuMethod (SW-DATA-DEF-PROPS-CONTENT) COMPU-METHOD)

(declare-fun hasUnit (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun unit (SW-DATA-DEF-PROPS-CONTENT) UNIT)

(declare-fun hasBaseType (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun baseType (SW-DATA-DEF-PROPS-CONTENT) SW-BASE-TYPE)

; Semantic predicate capturing that the ApplicationDataType governs the functional value typing.
(declare-fun applicationDataTypeSupersedesLocalSettings (SW-DATA-DEF-PROPS-CONTENT) Bool)

; If an ApplicationDataType is referenced, then it supersedes CompuMethod, Unit, and BaseType.
(assert
  (forall ((p SW-DATA-DEF-PROPS-CONTENT))
    (=> (hasValueAxisDataType p)
        (applicationDataTypeSupersedesLocalSettings p))))

; Constr_ApplicationPrimitiveDataType_ShortNameNotRequiredForCompatibility
; ShortName identity is NOT required for compatibility of ApplicationPrimitiveDataTypes.

(declare-sort APPLICATION-PRIMITIVE-DATA-TYPE 0)
(declare-fun shortName (APPLICATION-PRIMITIVE-DATA-TYPE) String)

; Abstract compatibility predicate between two ApplicationPrimitiveDataTypes.
(declare-fun compatible_APDT (APPLICATION-PRIMITIVE-DATA-TYPE APPLICATION-PRIMITIVE-DATA-TYPE) Bool)

; It is not required that shortNames are identical for compatibility:
; compatibility does not imply equality of shortNames.
(assert
  (forall ((a APPLICATION-PRIMITIVE-DATA-TYPE)
           (b APPLICATION-PRIMITIVE-DATA-TYPE))
    (=> (compatible_APDT a b)
        (or (not (= (shortName a) (shortName b)))
            true))))

; Constr_AutosarTypedPIM_NoCppOrPointerTypes
; AUTOSAR-typed PerInstanceMemory cannot support C++-specific types or pointer types directly.

(declare-sort AUTOSAR-DATA-TYPE 0)
(declare-sort VARIABLE-DATA-PROTOTYPE 0)

(declare-fun isPerInstanceMemory (VARIABLE-DATA-PROTOTYPE) Bool)
(declare-fun typeOf (VARIABLE-DATA-PROTOTYPE) AUTOSAR-DATA-TYPE)

; Semantic classifiers for forbidden kinds of AUTOSAR-DATA-TYPE.
(declare-fun isCppSpecificType (AUTOSAR-DATA-TYPE) Bool)
(declare-fun isPointerType (AUTOSAR-DATA-TYPE) Bool)

; If a VariableDataPrototype is a PerInstanceMemory and is AUTOSAR-typed,
; then its AUTOSAR-DATA-TYPE shall not be a C++-specific type nor a pointer type.
(assert
  (forall ((v VARIABLE-DATA-PROTOTYPE))
    (=> (isPerInstanceMemory v)
        (and (not (isCppSpecificType (typeOf v)))
             (not (isPointerType (typeOf v)))))))

; Constr_AvoidMultipleRunnableEntitysSameSymbol_7_2_4
; Mapping several RunnableEntitys to the same symbol for an AtomicSwComponentType shall be avoided.

(declare-sort ATOMIC-SW-COMPONENT-TYPE 0)
(declare-sort RUNNABLE-ENTITY 0)

(declare-fun runnableOf (ATOMIC-SW-COMPONENT-TYPE Int) RUNNABLE-ENTITY)
(declare-fun runnableCount (ATOMIC-SW-COMPONENT-TYPE) Int)
(declare-fun symbolOf (RUNNABLE-ENTITY) String)

; Advisory predicate: indicates that an AtomicSwComponentType uses unique symbols per RunnableEntity.
(declare-fun usesUniqueRunnableSymbols (ATOMIC-SW-COMPONENT-TYPE) Bool)

; If usesUniqueRunnableSymbols is required, then all RunnableEntitys mapped to the same
; AtomicSwComponentType shall have pairwise distinct symbols.
(assert
  (forall ((c ATOMIC-SW-COMPONENT-TYPE))
    (=> (usesUniqueRunnableSymbols c)
        (forall ((i Int) (j Int))
          (=> (and (<= 0 i) (< i (runnableCount c))
                   (<= 0 j) (< j (runnableCount c))
                   (not (= i j)))
              (not (= (symbolOf (runnableOf c i))
                      (symbolOf (runnableOf c j)))))))))

; Constr_AxisDescription_Determination
; SwDataDefProps determine an axis description.

(declare-sort SW-DATA-DEF-PROPS 0)
(declare-sort AXIS-DESCRIPTION 0)

; Relation between SwDataDefProps and the axis description it determines.
(declare-fun determinesAxisDescription (SW-DATA-DEF-PROPS AXIS-DESCRIPTION) Bool)

; Each SwDataDefProps that is used for axis description determines at most one axis description.
(assert
  (forall ((p SW-DATA-DEF-PROPS) (a1 AXIS-DESCRIPTION) (a2 AXIS-DESCRIPTION))
    (=> (and (determinesAxisDescription p a1)
             (determinesAxisDescription p a2))
        (= a1 a2))))


; Constr_AxisValuesType_Determination
; The type of the axis values is determined when the type of the referenced input value (swVariableRef) has been set.

(declare-sort SwAxisIndividual 0)
(declare-sort SwVariable 0)
(declare-sort DataType 0)

; swVariableRef association (0..*)
(declare-fun swVariableRef (SwAxisIndividual SwVariable) Bool)

; typing of variables and axis values
(declare-fun varType (SwVariable) DataType)
(declare-fun axisValuesType (SwAxisIndividual) DataType)

; hasType predicates (optional presence of a type)
(declare-fun hasVarType (SwVariable) Bool)
(declare-fun hasAxisValuesType (SwAxisIndividual) Bool)

; If the referenced input variable has a type, then the axis values type is determined
(assert
  (forall ((a SwAxisIndividual) (v SwVariable))
    (=> (and (swVariableRef a v)
             (hasVarType v))
        (and (hasAxisValuesType a)
             (= (axisValuesType a) (varType v))))))

; Constr_BehavioralVariability_BindingTime_PreCompile
; For existence variability of RunnableEntitys, RTEEvents, inter-runnable variables and parameters,
; the latest binding time is preCompileTime.

(declare-sort SwcInternalBehavior 0)
(declare-sort RunnableEntity 0)
(declare-sort RTEEvent 0)
(declare-sort VariableDataPrototype 0)
(declare-sort ParameterDataPrototype 0)
(declare-sort BindingTime 0)

(declare-const preCompileTime BindingTime)

; membership relations
(declare-fun hasRunnable (SwcInternalBehavior RunnableEntity) Bool)
(declare-fun hasRTEEvent (SwcInternalBehavior RTEEvent) Bool)
(declare-fun implicitInterRunnableVariable (SwcInternalBehavior VariableDataPrototype) Bool)
(declare-fun explicitInterRunnableVariable (SwcInternalBehavior VariableDataPrototype) Bool)
(declare-fun perInstanceParameter (SwcInternalBehavior ParameterDataPrototype) Bool)
(declare-fun sharedParameter (SwcInternalBehavior ParameterDataPrototype) Bool)
(declare-fun constantMemory (SwcInternalBehavior ParameterDataPrototype) Bool)

; binding time of existence variability
(declare-fun existenceBindingTime_Runnable (RunnableEntity) BindingTime)
(declare-fun existenceBindingTime_RTEEvent (RTEEvent) BindingTime)
(declare-fun existenceBindingTime_Var (VariableDataPrototype) BindingTime)
(declare-fun existenceBindingTime_Param (ParameterDataPrototype) BindingTime)

(assert
  (forall ((b SwcInternalBehavior) (r RunnableEntity))
    (=> (hasRunnable b r)
        (= (existenceBindingTime_Runnable r) preCompileTime))))

(assert
  (forall ((b SwcInternalBehavior) (e RTEEvent))
    (=> (hasRTEEvent b e)
        (= (existenceBindingTime_RTEEvent e) preCompileTime))))

(assert
  (forall ((b SwcInternalBehavior) (v VariableDataPrototype))
    (=> (or (implicitInterRunnableVariable b v)
            (explicitInterRunnableVariable b v))
        (= (existenceBindingTime_Var v) preCompileTime))))

(assert
  (forall ((b SwcInternalBehavior) (p ParameterDataPrototype))
    (=> (or (perInstanceParameter b p)
            (sharedParameter b p)
            (constantMemory b p))
        (= (existenceBindingTime_Param p) preCompileTime))))

; Constr_BitfieldMask_SenderValueMappingCompleteness
; Within a single mask (for BITFIELD_TEXTTABLE category on sender side),
; all values on the sender side shall have a mapping to the receiver side.

(declare-sort CompuMethod 0)
(declare-sort BitfieldMask 0)
(declare-sort SenderValue 0)
(declare-sort ReceiverValue 0)

; category of a CompuMethod
(declare-datatypes () ((CompuCategory BITFIELD_TEXTTABLE OTHER_CATEGORY)))
(declare-fun compuCategory (CompuMethod) CompuCategory)

; masks and values
(declare-fun hasMask (CompuMethod BitfieldMask) Bool)
(declare-fun senderValueInMask (BitfieldMask SenderValue) Bool)
(declare-fun mappedTo (BitfieldMask SenderValue ReceiverValue) Bool)

; For BITFIELD_TEXTTABLE on sender side, every sender value in a mask has some mapping
(assert
  (forall ((cm CompuMethod) (m BitfieldMask) (sv SenderValue))
    (=> (and (= (compuCategory cm) BITFIELD_TEXTTABLE)
             (hasMask cm m)
             (senderValueInMask m sv))
        (exists ((rv ReceiverValue))
          (mappedTo m sv rv))))

)

; Constr_CalibParamAccess_InstantiationDataDefProps
; It is possible (not mandatory) to define access to calibration parameters on InstantiationDataDefProps level.

(declare-sort InstantiationDataDefProps 0)
(declare-sort CalibrationParameter 0)
(declare-sort AccessRight 0)

(declare-fun definesAccess (InstantiationDataDefProps CalibrationParameter AccessRight) Bool)

; No hard constraint: possibility only, so no universal axiom is imposed.

; Constr_CategoryConsistency_AuthorResponsibility
; Consistency of SwRecordLayoutV.category / SwRecordLayoutGroup.category with SwRecordLayout structure
; is delegated to the author; no formal constraint imposed here.

(declare-sort SwRecordLayout 0)
(declare-sort SwRecordLayoutV 0)
(declare-sort SwRecordLayoutGroup 0)
(declare-sort AsamRecordLayoutSemantics 0)

(declare-fun categoryV (SwRecordLayoutV) AsamRecordLayoutSemantics)
(declare-fun categoryG (SwRecordLayoutGroup) AsamRecordLayoutSemantics)

; No additional axioms: responsibility is outside formal verification scope.


; Constr_Chapter_atpVariation
(declare-sort Chapter 0)
(declare-sort VariationPoint 0)

; whether a chapter has a variation point
(declare-fun hasVariationPoint (Chapter) Bool)
; the variation point associated to a chapter (if any)
(declare-fun variationPointOf (Chapter) VariationPoint)

; stereotype and binding time of a variation point
(declare-fun isAtpVariation (VariationPoint) Bool)
(declare-fun bindingTimePostBuild (VariationPoint) Bool)

; if a chapter has a variation point, then it follows the atpVariation stereotype
; and has post-build as latest binding time
(assert
  (forall ((c Chapter))
    (=> (hasVariationPoint c)
        (and (isAtpVariation (variationPointOf c))
             (bindingTimePostBuild (variationPointOf c))))))

; Constr_ClientServerOperation_SyncAsyncExclusivity
(declare-sort ClientServerOperation 0)

; predicates indicating invocation styles used for a given operation instance
(declare-fun usesSyncInvocation (ClientServerOperation) Bool)
(declare-fun usesAsyncInvocation (ClientServerOperation) Bool)

; it is not supported to invoke the same operation both synchronously and asynchronously
(assert
  (forall ((op ClientServerOperation))
    (not (and (usesSyncInvocation op)
              (usesAsyncInvocation op)))))

; Constr_ClientServer_StaticCorrectness_Rationale
(declare-sort Client 0)
(declare-sort Server 0)
(declare-sort Operation 0)

; compatibility and required-call relations
(declare-fun compatibleClientServer (Client Server) Bool)
(declare-fun requiresOperationForCorrectness (Server Operation) Bool)
(declare-fun clientCallsOperation (Client Operation) Bool)

; static correctness rationale:
; if a client/server pair is considered compatible and the server requires
; a certain operation for correct work, then the client shall call it
(assert
  (forall ((cl Client) (sv Server) (op Operation))
    (=> (and (compatibleClientServer cl sv)
             (requiresOperationForCorrectness sv op))
        (clientCallsOperation cl op))))

(check-sat)