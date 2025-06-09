import json
import re
import tiktoken
import google.generativeai as genai
import os  # Added for directory and file operations

from openai import OpenAI
from config import (
    LLM_API_BASE, LLM_API_KEY, LLM_MODEL_NAME,
    CONSTRAINT_SCHEMA, CLASS_ANNOTATION_PATTERN, ENUM_ANNOTATION_PATTERN,
    SECTION_ANNOTATION_PATTERN, SECTION_SPLIT_PATTERN, PARENT_SECTION_CONTEXT_TAG,
    CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR,
    MAX_CONTEXT_TOKENS, MAX_OUTPUT_TOKENS, TOKEN_BUFFER, SAFE_INPUT_CONTENT_MAX_TOKENS
)

try:
    tokenizer = tiktoken.encoding_for_model(f"{LLM_MODEL_NAME}")
except KeyError:
    print(f"Warning: Model {LLM_MODEL_NAME} not found for tiktoken. Using cl100k_base.")
    tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text):
    if not text:
        return 0
    return len(tokenizer.encode(text))


class LlmExtractor:
    def __init__(self):
        if not LLM_API_KEY:
            raise ValueError("环境变量中未找到 LLM_API_KEY。")
        # Configure Gemini
        genai.configure(api_key=LLM_API_KEY, transport="rest",
                        client_options={"api_endpoint": "https://api.openai-proxy.org/google"})
        self.model = genai.GenerativeModel(LLM_MODEL_NAME)
        self.constraint_schema_str = json.dumps(CONSTRAINT_SCHEMA)
        # Initialize self.metadata to prevent errors in the f-string in _build_llm_metadata_prompt
        self.metadata =f"""{{
  "schema_definitions": {{
    "SwcInternalBehavior": {{
      "qualifiedName": "SwcInternalBehavior",
      "description": "The SwcInternalBehavior of an AtomicSwComponentType describes the relevant aspects of the software-component with respect to the RTE, i.e. the RunnableEntities and the RTEEvents they respond to.",
      "elements": [
      {{
          "name": "shortName",
          "qualifiedName": "shortName",
          "document_name": "Referrable.shortName",
          "type": "Identifier",
          "annotation": "@XmlElement(name=\"SHORT-NAME\")",
          "xml_tag": "SHORT-NAME",
          "xml_wrapper_tag": null,
          "is_xml_attribute": false,
          "minOccurs": "1",
          "maxOccurs": "1",
          "description": "This specifies an identifying shortName for the object. It needs to be unique within its context and is intended for humans but even more for technical reference.",
          "stereotypes": [],
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1,
          "latestBindingTime": "",
          "splitkey": ""
        }},
        {{
          "qualifiedName": "constantMemory",
          "type": "ParameterDataPrototype",
          "xml_tag": "PARAMETER-DATA-PROTOTYPE",
          "xml_wrapper_tag": "CONSTANT-MEMORYS",
          "description": "Describes a read only memory object containing characteristic value(s)  implemented by this InternalBehavior. The shortName of ParameterDataPrototype has to be equal to the ''C' identifier of the described constant.\nThe characteristic value(s) might be shared between\nSwComponentPrototypes of the same SwComponentType.\nThe aggregation of constantMemory is subject to variability with the purpose to support variability in the software component or module implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "constantValueMapping",
          "type": "ConstantValueMappingRef",
          "xml_tag": "CONSTANT-VALUE-MAPPING-REF",
          "xml_wrapper_tag": "CONSTANT-VALUE-MAPPING-REFS",
          "description": "Reference to the ConstanSpecificationMapping to be applied for the particular InternalBehavior",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "dataTypeMapping",
          "type": "DataTypeMappingRef",
          "xml_tag": "DATA-TYPE-MAPPING-REF",
          "xml_wrapper_tag": "DATA-TYPE-MAPPING-REFS",
          "description": "Reference to the DataTypeMapping to be applied for the particular InternalBehavior",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "exclusiveArea",
          "type": "ExclusiveArea",
          "xml_tag": "EXCLUSIVE-AREA",
          "xml_wrapper_tag": "EXCLUSIVE-AREAS",
          "description": "This specifies an ExclusiveArea for this InternalBehavior. The exclusiveArea is local to the component resp. module.\nThe aggregation of ExclusiveAreas is subject to variability.\nNote: the number of ExclusiveAreas might vary due to the conditional existence of RunnableEntities or BswModuleEntities.\n\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "exclusiveAreaNestingOrder",
          "type": "ExclusiveAreaNestingOrder",
          "xml_tag": "EXCLUSIVE-AREA-NESTING-ORDER",
          "xml_wrapper_tag": "EXCLUSIVE-AREA-NESTING-ORDERS",
          "description": "This represents the set of ExclusiveAreaNestingOrder owned by the InternalBehavior.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "staticMemory",
          "type": "VariableDataPrototype",
          "xml_tag": "VARIABLE-DATA-PROTOTYPE",
          "xml_wrapper_tag": "STATIC-MEMORYS",
          "description": "Describes a read and writeable static memory object representing measurment variables implemented by this software component. Static is used in the meaning of non temporary and does not necessarily specify a linker encapsulation. This kind of memory is only supported if supportsMultipleInstantiation is FALSE.\nThe shortName of the VariableDataPrototype has to be equal with the ''C' identifier of the described variable.\nThe aggregation of staticMemory is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }}
{{
          "qualifiedName": "arTypedPerInstanceMemory",
          "type": "VariableDataPrototype",
          "xml_tag": "VARIABLE-DATA-PROTOTYPE",
          "xml_wrapper_tag": "AR-TYPED-PER-INSTANCE-MEMORYS",
          "description": "Defines an AUTOSAR typed memory-block that needs to be available for each instance of the SW-component. This is typically only useful if supportsMultipleInstantiation is set to \"true\" or if the component defines NVRAM access via permanent blocks.\nThe aggregation of arTypedPerInstanceMemory is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "event",
          "type": "Events_SwcInternalBehavior",
          "xml_tag": "EVENTS",
          "xml_wrapper_tag": null,
          "description": "This is a RTEEvent specified for the particular SwcInternalBehavior.\n\nThe aggregation of RTEEvent is subject to variability with the purpose to support the conditional existence of RTE events. Note: the number of RTE events might vary due to the conditional existence of PortPrototypes using DataReceivedEvents or due to different scheduling needs of algorithms.\n\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "explicitInterRunnableVariable",
          "type": "VariableDataPrototype",
          "xml_tag": "VARIABLE-DATA-PROTOTYPE",
          "xml_wrapper_tag": "EXPLICIT-INTER-RUNNABLE-VARIABLES",
          "description": "Implement state message semantics for establishing communication among runnables of the same component.\nThe aggregation of explicitInterRunnableVariable is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "handleTerminationAndRestart",
          "type": "HandleTerminationAndRestartEnum",
          "xml_tag": "HANDLE-TERMINATION-AND-RESTART",
          "xml_wrapper_tag": null,
          "description": "This attribute controls the behavior with respect to stopping and restarting. The corresponding AtomicSwComponentType may either not support stop and restart, or support only stop, or support both stop and restart.",
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1
        }},
        {{
          "qualifiedName": "implicitInterRunnableVariable",
          "type": "VariableDataPrototype",
          "xml_tag": "VARIABLE-DATA-PROTOTYPE",
          "xml_wrapper_tag": "IMPLICIT-INTER-RUNNABLE-VARIABLES",
          "description": "Implement state message semantics for establishing communication among runnables of the same component.\nThe aggregation of implicitInterRunnableVariable is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "includedDataTypeSet",
          "type": "IncludedDataTypeSet",
          "xml_tag": "INCLUDED-DATA-TYPE-SET",
          "xml_wrapper_tag": "INCLUDED-DATA-TYPE-SETS",
          "description": "The includedDataTypeSet is used by a software component for its implementation.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "includedModeDeclarationGroupSet",
          "type": "IncludedModeDeclarationGroupSet",
          "xml_tag": "INCLUDED-MODE-DECLARATION-GROUP-SET",
          "xml_wrapper_tag": "INCLUDED-MODE-DECLARATION-GROUP-SETS",
          "description": "This aggregation represents the included ModeDeclarationGroups",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "instantiationDataDefProps",
          "type": "InstantiationDataDefProps",
          "xml_tag": "INSTANTIATION-DATA-DEF-PROPS",
          "xml_wrapper_tag": "INSTANTIATION-DATA-DEF-PROPSS",
          "description": "The purpose of this is that within the context  of a given SwComponentType some data def properties of individual instantiations can be  modified. \nThe aggregation of InstantiationDataDefProps is subject to variability with the purpose to support the conditional existence of PortPrototypes and component local memories like \"perInstanceParameter\" or \"arTypedPerInstanceMemory\".\n\n\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "perInstanceMemory",
          "type": "PerInstanceMemory",
          "xml_tag": "PER-INSTANCE-MEMORY",
          "xml_wrapper_tag": "PER-INSTANCE-MEMORYS",
          "description": "Defines a per-instance memory object needed by this software component.\nThe aggregation of PerInstanceMemory is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "perInstanceParameter",
          "type": "ParameterDataPrototype",
          "xml_tag": "PARAMETER-DATA-PROTOTYPE",
          "xml_wrapper_tag": "PER-INSTANCE-PARAMETERS",
          "description": "Defines parameter(s) or characteristic value(s) that needs to be available for each instance of the software-component. This is typically only useful if supportsMultipleInstantiation is set to \"true\".\nThe aggregation of perInstanceParameter is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "portAPIOption",
          "type": "PortAPIOption",
          "xml_tag": "PORT-API-OPTION",
          "xml_wrapper_tag": "PORT-API-OPTIONS",
          "description": "Options for generating the signature of port-related calls from a runnable to the RTE and vice versa.\nThe aggregation of PortPrototypes is subject to variability with the purpose to support the conditional existence of ports. \nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "runnable",
          "type": "RunnableEntity",
          "xml_tag": "RUNNABLE-ENTITY",
          "xml_wrapper_tag": "RUNNABLES",
          "description": "This is a RunnableEntity specified for the particular SwcInternalBehavior.\n\nThe aggregation of RunnableEntity is subject to variability with the purpose to support the conditional existence of RunnableEntities. Note: the number of RunnableEntities might vary due to the conditional existence of PortPrototypes using DataReceivedEvents or due to different scheduling needs of algorithms.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 1,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "serviceDependency",
          "type": "SwcServiceDependency",
          "xml_tag": "SWC-SERVICE-DEPENDENCY",
          "xml_wrapper_tag": "SERVICE-DEPENDENCYS",
          "description": "Defines the requirements on AUTOSAR Services for a particular item.\n\nThe aggregation of SwcServiceDependency is subject to variability with the purpose to support the conditional existence of ports as well as the conditional existence of ServiceNeeds.\n\nThe SwcServiceDependency owned by an SwcInternalBehavior can be located in a different physical file in order to support that SwcServiceDependency might be provided in later development \nsteps or even by different expert domain (e.g OBD expert for Obd related  Service Needs) tools. Therefore the aggregation is <<atpSplitable>>.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "sharedParameter",
          "type": "ParameterDataPrototype",
          "xml_tag": "PARAMETER-DATA-PROTOTYPE",
          "xml_wrapper_tag": "SHARED-PARAMETERS",
          "description": "Defines parameter(s) or characteristic value(s) shared between SwComponentPrototypes of the same SwComponentType\nThe aggregation of sharedParameter is subject to variability with the purpose to support variability in the software components implementations. Typically different algorithms in the implementation are requiring different number of memory objects.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "supportsMultipleInstantiation",
          "type": "Boolean",
          "xml_tag": "SUPPORTS-MULTIPLE-INSTANTIATION",
          "xml_wrapper_tag": null,
          "description": "Indicate whether the corresponding software-component can be multiply instantiated on one ECU. In this case the attribute will result in an appropriate component API on programming language level (with or without instance handle).",
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1
        }},
        {{
          "qualifiedName": "variationPointProxy",
          "type": "VariationPointProxy",
          "xml_tag": "VARIATION-POINT-PROXY",
          "xml_wrapper_tag": "VARIATION-POINT-PROXYS",
          "description": "Proxy of a variation points in the C/C++ implementation.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "variationPoint",
          "type": "VariationPoint",
          "xml_tag": "VARIATION-POINT",
          "xml_wrapper_tag": null,
          "description": "This element was generated/modified due to an atpVariation stereotype.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": 1
        }}
      ]
    }},
    "RunnableEntity": {{
      "qualifiedName": "RunnableEntity",
      "description": "A RunnableEntity represents the smallest code-fragment that is provided by an AtomicSwComponentType and are executed under control of the RTE. RunnableEntities are for instance set up to respond to data reception or operation invocation on a server.",
      "elements": [
        {{
          "qualifiedName": "argument",
          "type": "RunnableEntityArgument",
          "xml_tag": "RUNNABLE-ENTITY-ARGUMENT",
          "xml_wrapper_tag": "ARGUMENTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "This represents the formal definition of a an argument to a RunnableEntity.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "asynchronousServerCallResultPoint",
          "type": "AsynchronousServerCallResultPoint",
          "xml_tag": "ASYNCHRONOUS-SERVER-CALL-RESULT-POINT",
          "xml_wrapper_tag": "ASYNCHRONOUS-SERVER-CALL-RESULT-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The server call result point admits a runnable to fetch the result of an asynchronous server call.\n\nThe aggregation of AsynchronousServerCallResultPoint is subject to variability with the purpose to support the conditional existence of client server PortPrototypes and the variant existence of server call result points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "canBeInvokedConcurrently",
          "type": "Boolean",
          "xml_tag": "CAN-BE-INVOKED-CONCURRENTLY",
          "xml_wrapper_tag": null,
          "minOccurs": "0",
          "maxOccurs": "1",
          "description": "If the value of this attribute is set to \"true\" the enclosing RunnableEntity can be invoked concurrently (even for one instance of the corresponding AtomicSwComponentType). This implies that it is the responsibility of the implementation of the RunnableEntity to take care of this form of concurrency. Note that the default value of this attribute is set to \"false\".",
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1
        }},
        {{
          "qualifiedName": "dataReadAccess",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "DATA-READ-ACCESSS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "RunnableEntity has implicit read access to dataElement of a sender-receiver PortPrototype or nv data of a nv data PortPrototype.\n\nThe aggregation of dataReadAccess is subject to variability with the purpose to support the conditional existence of sender receiver ports or the variant existence of dataReadAccess in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "dataReceivePointByArgument",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "DATA-RECEIVE-POINT-BY-ARGUMENTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "RunnableEntity has explicit read access to dataElement of a sender-receiver PortPrototype or nv data of a nv data PortPrototype.\nThe result is passed back to the application by means of an argument in the function signature.\n\nThe aggregation of dataReceivePointByArgument is subject to variability with the purpose to support the conditional existence of sender receiver PortPrototype or the variant existence of data receive points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "dataReceivePointByValue",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "DATA-RECEIVE-POINT-BY-VALUES",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "RunnableEntity has explicit read access to dataElement of a sender-receiver PortPrototype or nv data of a nv data PortPrototype.\n\nThe result is passed back to the application by means of the return value.\nThe aggregation of dataReceivePointByValue is subject to variability with the purpose to support the conditional existence of sender receiver ports or the variant existence of data receive points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "dataSendPoint",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "DATA-SEND-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "RunnableEntity has explicit write access to dataElement of a sender-receiver PortPrototype or nv data of a nv data PortPrototype.\n\nThe aggregation of dataSendPoint is subject to variability with the purpose to support the conditional existence of sender receiver PortPrototype or the variant existence of data send points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "dataWriteAccess",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "DATA-WRITE-ACCESSS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "RunnableEntity has implicit write access to dataElement of a sender-receiver PortPrototype or nv data of a nv data PortPrototype.\n\nThe aggregation of dataWriteAccess is subject to variability with the purpose to support the conditional existence of sender receiver ports or the variant existence of dataWriteAccess in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "externalTriggeringPoint",
          "type": "ExternalTriggeringPoint",
          "xml_tag": "EXTERNAL-TRIGGERING-POINT",
          "xml_wrapper_tag": "EXTERNAL-TRIGGERING-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The aggregation of ExternalTriggeringPoint is subject to variability with the purpose to support the conditional existence of trigger ports or the variant existence of external triggering points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "internalTriggeringPoint",
          "type": "InternalTriggeringPoint",
          "xml_tag": "INTERNAL-TRIGGERING-POINT",
          "xml_wrapper_tag": "INTERNAL-TRIGGERING-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The aggregation of InternalTriggeringPoint is subject to variability with the purpose to support the variant existence of internal triggering points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "modeAccessPoint",
          "type": "ModeAccessPoint",
          "xml_tag": "MODE-ACCESS-POINT",
          "xml_wrapper_tag": "MODE-ACCESS-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The runnable has a mode access point.\nThe aggregation of ModeAccessPoint is subject to variability with the purpose to support the conditional existence of mode ports or the variant existence of mode access points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "modeSwitchPoint",
          "type": "ModeSwitchPoint",
          "xml_tag": "MODE-SWITCH-POINT",
          "xml_wrapper_tag": "MODE-SWITCH-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The runnable has a mode switch point.\nThe aggregation of ModeSwitchPoint is subject to variability with the purpose to support the conditional existence of mode ports or the variant existence of mode switch points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "parameterAccess",
          "type": "ParameterAccess",
          "xml_tag": "PARAMETER-ACCESS",
          "xml_wrapper_tag": "PARAMETER-ACCESSS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The presence of a ParameterAccess implies that a RunnableEntity needs read only access to a ParameterDataPrototype which may either be local or within a PortPrototype.\n\nThe aggregation of ParameterAccess is subject to variability with the purpose to support the conditional existence of parameter ports and component local parameters as well as the variant existence of ParameterAccess (points) in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "readLocalVariable",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "READ-LOCAL-VARIABLES",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The presence of a readLocalVariable implies that a RunnableEntity needs read access to a VariableDataPrototype in the role of implicitInterRunnableVariable or explicitInterRunnableVariable.\n\nThe aggregation of readLocalVariable is subject to variability with the purpose to support the conditional existence of implicitInterRunnableVariable and explicitInterRunnableVariable or the variant existence of readLocalVariable (points) in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "serverCallPoint",
          "type": "ServerCallPoints",
          "xml_tag": "SERVER-CALL-POINTS",
          "xml_wrapper_tag": null,
          "minOccurs": "0",
          "maxOccurs": "1",
          "description": "The RunnableEntity has a ServerCallPoint.\nThe aggregation of ServerCallPoint is subject to variability with the purpose to support the conditional existence of client server PortPrototypes or the variant existence of server call points in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "symbol",
          "type": "String",
          "xml_tag": "SYMBOL",
          "xml_wrapper_tag": null,
          "minOccurs": "0",
          "maxOccurs": "1",
          "description": "The symbol describing this RunnableEntity's entry point. This is considered the API of the RunnableEntity and is required during the RTE contract phase.",
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1
        }},
        {{
          "qualifiedName": "waitPoint",
          "type": "WaitPoint",
          "xml_tag": "WAIT-POINT",
          "xml_wrapper_tag": "WAIT-POINTS",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The WaitPoint associated with the RunnableEntity.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "writtenLocalVariable",
          "type": "VariableAccess",
          "xml_tag": "VARIABLE-ACCESS",
          "xml_wrapper_tag": "WRITTEN-LOCAL-VARIABLES",
          "minOccurs": "0",
          "maxOccurs": null,
          "description": "The presence of a writtenLocalVariable implies that a RunnableEntity needs write access to a VariableDataPrototype in the role of implicitInterRunnableVariable or explicitInterRunnableVariable.\n\nThe aggregation of writtenLocalVariable is subject to variability with the purpose to support the conditional existence of implicitInterRunnableVariable and explicitInterRunnableVariable or the variant existence of writtenLocalVariable (points) in the implementation.\nThe upper multiplicity of this role has been increased to * due to resolving an atpVariation stereotype. The previous value was -1.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "variationPoint",
          "type": "VariationPoint",
          "xml_tag": "VARIATION-POINT",
          "xml_wrapper_tag": null,
          "minOccurs": "0",
          "maxOccurs": "1",
          "description": "This element was generated/modified due to an atpVariation stereotype.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": 1
        }}
      ]
    }},
    "Events_SwcInternalBehavior": {{
      "attributes": [
        {{
          "type": "AsynchronousServerCallReturnsEventWrapper",
          "xml_tag": "ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "BackgroundEvent",
          "xml_tag": "BACKGROUND-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "DataReceiveErrorEvent",
          "xml_tag": "DATA-RECEIVE-ERROR-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "DataReceivedEvent",
          "xml_tag": "DATA-RECEIVED-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "DataSendCompletedEvent",
          "xml_tag": "DATA-SEND-COMPLETED-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "DataWriteCompletedEvent",
          "xml_tag": "DATA-WRITE-COMPLETED-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "ExternalTriggerOccurredEvent",
          "xml_tag": "EXTERNAL-TRIGGER-OCCURRED-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "InitEvent",
          "xml_tag": "INIT-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "InternalTriggerOccurredEvent",
          "xml_tag": "INTERNAL-TRIGGER-OCCURRED-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "ModeSwitchedAckEvent",
          "xml_tag": "MODE-SWITCHED-ACK-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "OperationInvokedEvent",
          "xml_tag": "OPERATION-INVOKED-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "SwcModeManagerErrorEvent",
          "xml_tag": "SWC-MODE-MANAGER-ERROR-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "SwcModeSwitchEvent",
          "xml_tag": "SWC-MODE-SWITCH-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "TimingEvent",
          "xml_tag": "TIMING-EVENT",
          "xml_wrapper_tag": null
        }},
        {{
          "type": "TransformerHardErrorEvent",
          "xml_tag": "TRANSFORMER-HARD-ERROR-EVENT",
          "xml_wrapper_tag": null
        }}
      ]
    }},
    "TimingEvent": {{
      "qualifiedName": "TimingEvent",
      "elements": [
        {{
          "qualifiedName": "disabledMode",
          "type": "RModeInAtomicSwcInstanceRef",
          "annotation": "@XmlElementWrapper(name=\"DISABLED-MODE-IREFS\")\n@XmlElement(name=\"DISABLED-MODE-IREF\")",
          "xml_tag": "DISABLED-MODE-IREF",
          "xml_wrapper_tag": "DISABLED-MODE-IREFS",
          "description": "Reference to the Modes that disable the Event.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": -1
        }},
        {{
          "qualifiedName": "startOnEvent",
          "type": "StartOnEventRef",
          "xml_tag": "START-ON-EVENT-REF",
          "xml_wrapper_tag": null,
          "description": "RunnableEntity starts when the corresponding RTEEvent occurs.",
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1
        }},
        {{
          "qualifiedName": "variationPoint",
          "type": "VariationPoint",
          "xml_tag": "VARIATION-POINT",
          "xml_wrapper_tag": null,
          "description": "This element was generated/modified due to an atpVariation stereotype.",
          "pure_minOccurs": 0,
          "pure_maxOccurs": 1
        }},
        {{
          "qualifiedName": "period",
          "type": "S",
          "xml_tag": "PERIOD",
          "xml_wrapper_tag": null,
          "description": "Period of timing event in seconds. The value of this attribute shall be greater than zero.",
          "pure_minOccurs": 1,
          "pure_maxOccurs": 1
        }}
      ]
    }},
    "StartOnEventRef": {{
      "name": "StartOnEventRef",
      "attributes": [
        {{
          "name": "dest",
          "type": "RunnableEntitySubtypesEnum",
          "annotation": "@XmlAttribute(name=\"DEST\")",
          "xml_tag": "DEST",
          "xml_wrapper_tag": null,
          "is_xml_attribute": true,
          "enumerations": [
            "RUNNABLE-ENTITY"
          ]
        }}
      ]
    }}
  }}
}}"""

    def _build_llm_prompt(self, text_block_for_llm):
        """Builds the first type of prompt for the LLM."""
        prompt = f"""
"You are a senior AUTOSAR systems engineer. I need you to create the XML definition for the internal behavior of a software component. Here's what it needs to do:
System Behavior & Constraints:
The component's core logic is a single, periodic task that we'll call RE_Periodic_10ms. This task must be designed to be re-entrant, meaning it can be invoked concurrently without causing issues. It also has a specific C function name, let's say Rte_Task_Periodic_10ms.
The activation of this task is handled by a precise timer that fires every 10 milliseconds. This timer is what triggers the periodic task to run.
For safety, the component needs to explicitly state its policy on termination and restart; it should support both. It also needs to declare that it does not support being instantiated multiple times on the same ECU.
Based on this functional description, please generate the complete and compliant AUTOSAR XML for the SWC-INTERNAL-BEHAVIOR."""
        return prompt

    def _build_llm_metadata_prompt(self, text_block_for_llm):
        """Builds the second type of prompt for the LLM."""
        prompt = f"""
    You are a precise XML generation engine. Your task is to generate an XML instance based on a specific scenario and a set of strict schema definitions.
Instructions:
Start with the SwcInternalBehavior definition.
For each element, if pure_minOccurs is 1, you MUST generate it.
When an element's type points to another definition (e.g., type: 'RunnableEntity'), recursively apply these instructions.
If a definition is_reference: true, construct the tag with its specified attributes and use the target name from the scenario as its content.
Schema Definitions:
{self.metadata}
Scenario to Instantiate:
Create a root SwcInternalBehavior instance with all its mandatory elements.
Inside <RUNNABLES>, create one RunnableEntity instance named RE_Periodic_10ms. Fulfill its mandatory sub-elements.
Inside <EVENTS>, create one TimingEvent instance named TE_Periodic_10ms with a <PERIOD> of 0.01.
For this TimingEvent, its <START-ON-EVENT-REF> must point to the RunnableEntity named RE_Periodic_10ms.
Generate only the XML code block."""
        return prompt

    def generate_xml(self, prompt: str):
        """
        New method to call the LLM with a given prompt and get a raw text/XML response.
        This replaces the old extract_constraints_from_block method.
        """
        total_input_tokens = count_tokens(prompt)
        print(f"\n--- Sending request to LLM (Total input tokens: {total_input_tokens}) ---")

        try:
            # Configure the model to return plain text, which is suitable for XML.
            generation_config = genai.types.GenerationConfig(
                response_mime_type="text/plain",
                temperature=0.0,
                max_output_tokens=MAX_OUTPUT_TOKENS
            )

            # Call the model to generate content
            response = self.model.generate_content(
                contents=prompt,
                generation_config=generation_config
            )

            # Return the raw text from the response
            print("--- LLM call successful. Received response. ---")
            return response.text

        except Exception as e:
            print(f"An error occurred during the LLM API call: {e}")
            return f"<!-- Error generating XML: {e} -->"


# Main execution block to run the script
if __name__ == "__main__":
    OUTPUT_DIR = "output"

    # Create the output directory if it doesn't exist
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Output directory '{OUTPUT_DIR}' is ready.")
    except OSError as e:
        print(f"Error creating directory {OUTPUT_DIR}: {e}")
        exit()

    try:
        # Initialize the extractor
        extractor = LlmExtractor()
    except ValueError as e:
        print(f"Initialization failed: {e}")
        exit()

    # Loop 5 times to call each prompt and save the output
    for i in range(1, 6):
        print(f"\n{'=' * 20} Starting Run {i}/5 {'=' * 20}")

        # --- Process the first prompt ---
        # print("\n--- Generating with the first prompt (_build_llm_prompt) ---")
        # prompt1 = extractor._build_llm_prompt(None)  # Argument is not used in the prompt function
        # xml_output1 = extractor.generate_xml(prompt1)
        #
        # # Save the result to a file
        # filename1 = os.path.join(OUTPUT_DIR, f"output_prompt1_run_{i}.xml")
        # try:
        #     with open(filename1, "w", encoding="utf-8") as f:
        #         f.write(xml_output1)
        #     print(f"--- Successfully saved output to {filename1} ---")
        # except IOError as e:
        #     print(f"--- Error writing to file {filename1}: {e} ---")

        # --- Process the second prompt ---
        print("\n--- Generating with the second prompt (_build_llm_metadata_prompt) ---")
        prompt2 = extractor._build_llm_metadata_prompt(None)  # Argument is not used
        xml_output2 = extractor.generate_xml(prompt2)

        # Save the result to a file
        filename2 = os.path.join(OUTPUT_DIR, f"output_prompt2_run_{i}.xml")
        try:
            with open(filename2, "w", encoding="utf-8") as f:
                f.write(xml_output2)
            print(f"--- Successfully saved output to {filename2} ---")
        except IOError as e:
            print(f"--- Error writing to file {filename2}: {e} ---")

    print(f"\n{'=' * 20} All runs completed. {'=' * 20}")