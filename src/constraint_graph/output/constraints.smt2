(set-logic ALL)

;; --- 唯一的简单声明 (Sorts, Funs, Consts) --- ;;
(declare-fun applicationDataTypeSupersedesLocalSettings (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun appliesMapping (SwConnector PortInterfaceMapping) Bool)
(declare-fun baseType (SW-DATA-DEF-PROPS-CONTENT) SW-BASE-TYPE)
(declare-fun belongsToPartialNetwork (PortPrototype PartialNetwork) Bool)
(declare-fun compatible_APDT (APPLICATION-PRIMITIVE-DATA-TYPE APPLICATION-PRIMITIVE-DATA-TYPE) Bool)
(declare-fun compatible_Record_Array (ApplicationRecordDataType ApplicationArrayDataType) Bool)
(declare-fun compuMethod (SW-DATA-DEF-PROPS-CONTENT) COMPU-METHOD)
(declare-fun considersPartialNetworkStatus (SwComponent PartialNetwork) Bool)
(declare-fun containsPrimitive (ApplicationCompositeDataType ApplicationPrimitiveDataType) Bool)
(declare-fun dataTypeMapRefersTo (DataTypeMap ApplicationDataType ImplementationDataType) Bool)
(declare-fun hasBaseType (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun hasCompanionImplType (ApplicationDataType ImplementationDataType) Bool)
(declare-fun hasCompuMethod (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun hasConsistencyNeeds_Atomic (AtomicSwComponentType ConsistencyNeeds) Bool)
(declare-fun hasConsistencyNeeds_Composition (CompositionSwComponentType ConsistencyNeeds) Bool)
(declare-fun hasMappingRef (SwConnector) Bool)
(declare-fun hasPortInterfaceMapping (PortInterfaceMapping ApplicationRecordDataType ApplicationArrayDataType) Bool)
(declare-fun hasRepresentedPortGroup (ComMgrUserNeeds) Bool)
(declare-fun hasSemanticMeaning_Composite (ApplicationCompositeDataType SemanticConcept) Bool)
(declare-fun hasSemanticMeaning_Primitive (ApplicationPrimitiveDataType SemanticConcept) Bool)
(declare-fun hasUnit (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun hasValueAxisDataType (SW-DATA-DEF-PROPS-CONTENT) Bool)
(declare-fun isActivePartialNetwork (PartialNetwork) Bool)
(declare-fun isAssemblySwConnector (SwConnector) Bool)
(declare-fun isDelegationSwConnector (SwConnector) Bool)
(declare-fun isPassThroughSwConnector (SwConnector) Bool)
(declare-fun isVSADT (ApplicationDataType) Bool)
(declare-fun mappingRef (SwConnector) PortInterfaceMapping)
(declare-fun numValidElements (ElementContainer) Int)
(declare-fun representedPortGroup (ComMgrUserNeeds) PortGroup)
(declare-fun retrievesComM (SwComponent) Bool)
(declare-fun shortName (APPLICATION-PRIMITIVE-DATA-TYPE) String)
(declare-fun sizeIndicator (ElementContainer) Int)
(declare-fun unit (SW-DATA-DEF-PROPS-CONTENT) UNIT)
(declare-fun usesAppModeInterface_currentMode (BswInterfaceUser) Bool)
(declare-fun usesClientServerInterfaceForComM (SwComponent) Bool)
(declare-fun usesComM_CurrentMode_currentMode (BswInterfaceUser) Bool)
(declare-fun usesComM_UserRequest_GetCurrentComMode (BswInterfaceUser) Bool)
(declare-fun usesPortForCommunication (SwComponent PortPrototype) Bool)
(declare-fun usesSenderReceiverInterfaceForComM (SwComponent) Bool)
(declare-fun valueAxisDataType (SW-DATA-DEF-PROPS-CONTENT) APPLICATION-DATA-TYPE)
(declare-sort APPLICATION-DATA-TYPE 0)
(declare-sort APPLICATION-PRIMITIVE-DATA-TYPE 0)
(declare-sort ApplicationArrayDataType 0)
(declare-sort ApplicationCompositeDataType 0)
(declare-sort ApplicationDataType 0)
(declare-sort ApplicationPrimitiveDataType 0)
(declare-sort ApplicationRecordDataType 0)
(declare-sort AtomicSwComponentType 0)
(declare-sort BswInterfaceUser 0)
(declare-sort COMPU-METHOD 0)
(declare-sort ComMgrUserNeeds 0)
(declare-sort CompositionSwComponentType 0)
(declare-sort ConsistencyNeeds 0)
(declare-sort DataTypeMap 0)
(declare-sort ElementContainer 0)
(declare-sort ImplementationDataType 0)
(declare-sort PartialNetwork 0)
(declare-sort PortGroup 0)
(declare-sort PortInterfaceMapping 0)
(declare-sort PortPrototype 0)
(declare-sort SW-BASE-TYPE 0)
(declare-sort SW-DATA-DEF-PROPS-CONTENT 0)
(declare-sort SemanticConcept 0)
(declare-sort SwComponent 0)
(declare-sort SwConnector 0)
(declare-sort UNIT 0)

;; --- 唯一的数据类型声明 (Datatypes) --- ;;
;; --- 其他语句 (Assertions, etc.) --- ;;
(assert
  (forall ((s SwConnector) (m PortInterfaceMapping))
    (=> (appliesMapping s m)
        (and (hasMappingRef s)
             (= (mappingRef s) m)))))

(assert
  (forall ((u ComMgrUserNeeds))
    (=> (hasRepresentedPortGroup u)
        (exists ((pg PortGroup))
          (and (= pg (representedPortGroup u))
               (forall ((pg2 PortGroup))
                 (=> (= pg2 (representedPortGroup u))
                     (= pg2 pg))))))))

(assert
  (forall ((u BswInterfaceUser))
    (let ((a (usesComM_UserRequest_GetCurrentComMode u))
          (b (usesComM_CurrentMode_currentMode u))
          (c (usesAppModeInterface_currentMode u)))
      (and
        
        (or a b c)
        
        (not (and a b))
        (not (and a c))
        (not (and b c))))))

(assert
  (forall ((c SwComponent))
    (=> (retrievesComM c)
        (or (usesClientServerInterfaceForComM c)
            (usesSenderReceiverInterfaceForComM c)))))

(assert
  (forall ((c SwComponent) (p PortPrototype) (pn PartialNetwork))
    (=> (and (usesPortForCommunication c p)
             (belongsToPartialNetwork p pn))
        (and (considersPartialNetworkStatus c pn)
             (isActivePartialNetwork pn)))))

(assert
  (forall ((a ApplicationDataType))
    (=> (isVSADT a)
        (exists ((i ImplementationDataType) (m DataTypeMap))
          (and (hasCompanionImplType a i)
               (dataTypeMapRefersTo m a i))))))

(assert
  (forall ((r ApplicationRecordDataType) (a ApplicationArrayDataType))
    (=> (compatible_Record_Array r a)
        (exists ((p PortInterfaceMapping))
          (hasPortInterfaceMapping p r a)))))

(assert
  (forall ((r ApplicationRecordDataType) (a ApplicationArrayDataType))
    (=> (not (exists ((p PortInterfaceMapping)) (hasPortInterfaceMapping p r a)))
        (not (compatible_Record_Array r a)))))

(assert
  (forall ((c ElementContainer))
    (= (numValidElements c) (sizeIndicator c))))

(assert
  (forall ((c ApplicationCompositeDataType) (s SemanticConcept))
    (not (hasSemanticMeaning_Composite c s))))

(assert
  (forall ((p SW-DATA-DEF-PROPS-CONTENT))
    (=> (hasValueAxisDataType p)
        (applicationDataTypeSupersedesLocalSettings p))))
