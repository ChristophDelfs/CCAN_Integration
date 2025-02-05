from collections import namedtuple
from enum import Enum

CompilerMode     = Enum("value","text xml binary binary_config")
#MapperType       = Enum("value","SimpleMapper FixedDataEventMapper")
MapperTypeList   = ["SimpleMapper" ,"FixedDataEventMapper","VariableDataEventMapper"]
ProtocolMapperTypeList = ["HCAN"]
ProtocolAdapterDeviceIDs = {}
ProtocolAdapterDeviceIDs["HCANProtocolMapper"] = [10,11]
                         

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    ORANGE = '\033[210m'
    MAGENTA = '\033[1;35;40m'
    FAT_WHITE = '\033[1;44;40m'
    RED = '\033[91m'
    END = '\033[0m'
    ALERT = '\033[1,37;41m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class NoColors:
    HEADER = ''
    BLUE = ''
    GREEN = ''
    YELLOW = ''
    ORANGE = ''
    MAGENTA = ''
    FAT_WHITE = ''
    RED = ''
    END = ''
    ALERT = ''
    BOLD = ''
    UNDERLINE = ''



#RawEvent    = namedtuple("RawEvent", "time_stamp addressing_type payload")
#DeviceEvent = namedtuple("DeviceEvent","time_stamp addressing_type event_descriptor") 
#ApplicationEvent = namedtuple("ApplicationEvent","time_stamp addressing_type service_name service_id event_name event_type from_address from_instance to_address to_instance parameters")
#ExternalProtocolEvent    = namedtuple("ExternalProtocolEvent","time_stamp addressing_type protocol_name protocol_type path_name path_id event_name event_type parameter_list")
EventDescriptor = namedtuple("EventDescriptor","name id parameters")

#######################################################  PARSER ###########################

LocationInfo      = namedtuple("LocationInfo","file line column")

ParsedAutomation = namedtuple("ParsedAutomation","list")
ParsedSensorDriverDescriptionList = namedtuple("ParsedSensorDriverDescriptionList","list")
ParsedCommunicationDriverDescriptionList = namedtuple("ParsedCommunicationDriverDescriptionList","list")
ParsedTransportAdapterDescriptionList = namedtuple("ParsedTransportAdapterDescriptionList","list")
ParsedProtocolAdapterDescriptionList = namedtuple("ParsedProtocolAdapterDescriptionList","list")
ParsedProtocolAdapterTypeList = namedtuple("ParsedProtocolAdapterTypeList","list")

ParsedPinList = namedtuple("ParsedPinList","list")
ParsedAdapterList = namedtuple("ParsedAdapterList","list")

#ParsedControllerDescription = namedtuple("ParsedControllerDescription","name parameter_description_list offered_connection_usage offered_communication_usage offered_adapter_usage degradation_description_list location_info")
ParsedGeneralAppDescription = namedtuple("ParsedAppDescription","type name parameter_description_list connection_description_list offered_connection_usage offered_communication_usage offered_adapter_usage degradation_description_list  location_info")

#ParsedTemplateDescription = namedtuple("ParsedTemplateDescription","name parameter_description_list connection_description_list event_description_list automation location_info")
ParsedDeviceDescription = namedtuple("ParsedDeviceDescription","name type attribute_list parameter_description_list connection_description_list event_description_list status_variable_description_list degradation_description_list automation location_info")

ParsedAliasDefinition = namedtuple("ParsedAliasDefinition","name expression location_info")
ParsedExportList = namedtuple("ParsedExportList","event_list location_info")

ParsedControllerInstance = namedtuple("ParsedControllerInstance","type name uuid parameter_list sensor_usage_list communication_usage_list adapter_usage_list location_info ")
ParsedAppInstance = namedtuple("ParsedAppInstance","type name uuid parameter_list connected_to sensor_usage_list location_info ")
ParsedDeviceInstance = namedtuple("ParsedDeviceInstance","type name parameter_list connected_to location_info")
ParsedHADeviceInstance = namedtuple("ParsedHADeviceInstance","type name parameter_list equivalent_list location_info")

ParsedConnectedPin    = namedtuple("ParsedConnectedPin","name driver_type location_info")
ParsedOfferedConnectionUsage = namedtuple("ParsedOfferedConnectionUsage","name driver_list location_info")
ParsedUsagePin = namedtuple("ParsedUsagePin","name usage_pin_entry_list location_info")
ParsedUsagePinEntry = namedtuple("ParsedUsagePinEntry","driver_name alias_name parameter_list connected_to location_info")

ParsedDegradationCode      =  namedtuple("ParsedDegradationCode","name explanation location_info")
ParsedTransportAdapterUsage = namedtuple("ParsedTransportAdapterUsage","name alias_name driver_name parameter_list connected_to supported_protocol location_info")
ParsedOfferedTransportAdapterUsage = namedtuple("ParsedOfferedTransportAdapterUsage","name driver_list supported_protocols location_info")


ProtocolDescription    = namedtuple("ProtocolDescription","id type name parameter_set protocol_map location_info")
ParsedProtocol     = namedtuple("ParsedProtocolAdapter","name parameter_list location_info")

ParsedTransportAdapterDescription = namedtuple("TransportAdapterDescription","type name parameter_description_list connection_description_list location_info")
ParsedTransportAdapterInstance = namedtuple("ParsedTransportAdapterInstance","name parameter_list connected_to location_info")
ParsedOfferedTransportAdapterList = namedtuple("ParsedOfferedTransportAdapterList","list location_info")

#OBSO_ProtocolType      =  namedtuple("OBSO_ProtocolType","id name parameter_def_list location_info")


ParsedCommunicationList = namedtuple("ParsedCommunicationList","list")

ParsedMappingList    = namedtuple("ParsedMappingList","from_event to_events location_info")
#ParsedMapping        = namedtuple("ParsedMapping","from_event to_event location_info")
ParsedParameterDescriptionList     = namedtuple("ParsedParameterDescriptionList", "parameter_name_list parameter_type_list parameter_constraints_list parameter_defaults_list dimension_list location_info")
ParsedConstraints                  = namedtuple("ParsedConstraints", "constraint_type location_info")
 
#ParsedEvent       = namedtuple("Parsed_Event","protocol_type event")
ParsedEvent   = namedtuple("ParsedEvent","protocol_name device_path_name event_name parameter_list location_info")
ParsedEquivalent =  namedtuple("ParsedEquivalent","name equivalent location_info")

            
ParsedStatusVariable = namedtuple("ParsedStatusVariable","status_variable_name status_variable_type location_info")

ParsedTransportAdapterDescription =  namedtuple("ParsedTransportAdapterDescription","type name parameter_description_list connection_description_list degradation_description_list location_info")
ParsedSensorDriverDescription = namedtuple("ParsedSensorDriverDescription","type name parameter_description_list degradation_description_list location_info")
ParsedAdditionalProtocolType = namedtuple("ParsedAdditionalProtocolType","type name parameter_description_list degradation_description_list location_info")


ParsedEventDescription  = namedtuple("ParsedEventDescription", "in_out_type name parameter_description_list location_info")
UpperCaseParameter      = namedtuple("UpperCaseParameter","name parameter_description_list")

ParsedFunctionExpression    = namedtuple("ParsedFunctionExpression","text location_info")
ParsedFunction              = namedtuple("ParsedFunction","name operands location_info")
ParsedVariableName          = namedtuple("ParsedVariableName","name location_info")
ParsedVariableInstance      = namedtuple("ParsedVariableInstance","name expression connected_to location_info")
ParsedTemplateVariableInstance  = namedtuple("ParsedTemplateVariableInstance","name expression connected_to location_info")
################## ParameterStore Transformer  ###################


ParsedVariableInExpression  = namedtuple("ParsedVariableInExpression","name type")
#ParsedSymbol                = namedtuple("ParsedSymbol","prefix name")
ParsedSymbol                = namedtuple("ParsedSymbol","name")

################################################################################################################


#FunctionExpression = namedtuple("FunctionExpression","operator operand1 operand2")
#Operator           = namedtuple("Operator","name value")
#ExpressionElement           = namedtuple("ExpressionElement","value name type id format")

  
ElementTypeKey = {}
ElementTypeKey["CONSTANT"]        = 0
ElementTypeKey["DEVICE_VARIABLE"] = 2
ElementTypeKey["VARIABLE"]        = 3
ElementTypeKey["EVENT_PARAMETER"] = 4
ElementTypeKey["FUNCTION"]        = 5
ElementTypeKey["OPERATOR"]        = 10

#FunctionExpression          = namedtuple("FunctionExpression","name id expression connected_to location_info")
#ParsedSimpleExpression      = namedtuple("ParsedSimpleExpression","text location_info")
Operator                    = namedtuple("Operator","value id number_of_arguments")

Variable    = namedtuple("Variable", "name value id type connected_to location_info")
#ExpressionVariable = namedtuple("ExpressionVariable","name value type id format")    
DeviceVariable = namedtuple("DeviceVariable","name id type connected_to")

# generated code:
VariableTypeKey = {}
VariableTypeKey["DeviceVariable"] = 0
VariableTypeKey["Variable"] = 1


OperatorTypeKey= {}
OperatorTypeKey["+"] = 0
OperatorTypeKey["-"] = 1
OperatorTypeKey["*"] = 2
OperatorTypeKey["/"] = 3
OperatorTypeKey["BINARY"] = 10
OperatorTypeKey["AND"]    = 20
OperatorTypeKey["OR"]     = 21
OperatorTypeKey["NOT"]    = 22
OperatorTypeKey["NAND"]   = 23
OperatorTypeKey["NOR"]    = 24

OperandTypeKey = {}
OperandTypeKey["UINT8"]  = 0
OperandTypeKey["UINT16"] = 1
OperandTypeKey["UINT32"] = 2
OperandTypeKey["UIN64"]  = 3
OperandTypeKey["FLOAT"]  = 4
OperandTypeKey["STRING"] =  10



####################################################   STORE ##################################

DriverDescription   = namedtuple("DriverDescription","key type parsed_element")
#CommunicationDriverDescription   = namedtuple("CommunicationDriverDescription","key type parsed_element")
#DriverListEntry       = namedtuple("DriverListEntry","id driver_instance parameter_set alias_name connection_set")


DeviceDescription     = namedtuple("DeviceDescription","key is_template parsed_element")
TemplateDescription   = namedtuple("TemplateDescription","is_template parsed_element")
BoardDescription      = namedtuple("BoardDescription","is_expander sensor_map communication_map adapter_map number_of_pins board_key parsed_element")
OfferedConnection     = namedtuple("OfferedConnection","id name driver_list")

BoardInstance         = namedtuple("BoardInstance","name controller_name type_name board_key connection_set local_id parameter_set used_sensor_map sensor_map used_communication_map communication_map used_adapter_map adapter_map number_of_pins degradation_description_list  parsed_element")
DeviceInstance        = namedtuple("DeviceInstance","id key controller_name name type_name connection_set parameter_set event_alias_map variable_list description parsed_element") 
ConnectionSet         = namedtuple("ConnectionSet","board_id driver_id pin_id board_name driver_name pin_name board_id_type driver_id_type pin_id_type")
ParameterSet          = namedtuple("ParameterSet","value name type")
#VariableParameterSet  = namedtuple("VariableParameterSet","value name type variable_flag")
UsedConnection        = namedtuple("UsedConnection","id name driver_type driver_key driver_id driver_name parameter_set connected_to")
MappingDescription    = namedtuple("MappingDescription","id key parameter_set device_name event_name controller_instance")
MappingDescriptionSet = namedtuple("MappingDescriptionSet","from_mapping_description to_mapping_description_list")

ExternalMappingDescription =  namedtuple("ExternalMappingDescription","protocol_name path_set event_set parameter_set")
MixedMappingDescriptionSet =  namedtuple("MixedMappingDescriptionSet","protocol_name from_mapping_description to_mapping_description_list")

#EventDescription      = namedtuple("EventDescription","name parameter_description_list")

###############################################################################################

## ControllerStore:

BoardDriver = namedtuple("BoardDriver","id board_name board_key board_type parameter_set connection_set sensor_list communication_list adapter_list")



############# HCAN ##########################
#HCAN_MappingDescription =  namedtuple("HCAN_MappingDescription","id parameter_set") 
#HCAN_Mapping = namedtuple("HCAN_Mapping","protocol_id protocol_name id parameter_")
HCAN_Message =  namedtuple("HCAN_Message","id name parameter_description_list")
HCAN_ProtocolEntry =  namedtuple("HCAN_ProtocolEntry","protocol_id protocol_name service_id service_name message_map") 

###################################################



BinaryConfig = namedtuple("BinaryConfig","controller_name type binary_config controller_crc")

ParamListInfo     = namedtuple("ParamListInfo", "parameter_name_list parameter_type_list dimension_list")
#ParamListInfoNew     = namedtuple("ParamListInfo", "parameter_name_list parameter_type_list dimension_list")

Parameter         = namedtuple("Parameter", "value name type")
#LocationInfo      = namedtuple("LocationInfo","file line")
EventInfo         = namedtuple("EventInfo", "event_type in_out_type param_list")
EventAlias        = namedtuple("EventAlias", "device_id event_type param_list")


#EventDescriptor = namedtuple("EventDescriptor","controller_name device_name event_name device_id event_type parameter_list parameter_type_list")
MappingDescriptorSet = namedtuple("MappingDescriptorSet","from_event_descriptor to_event_descriptor_list")

SimpleEventEntry  = namedtuple("SimpleEventInfo", "device_id event_type")
SimpleMappingInfo = namedtuple("SimpleMappingInfo","from_event_info to_event_info")
FixedDataEventInfo  = namedtuple("FixedDataEventInfo", "device_id type_name type param_list")

#DeviceInstance    = namedtuple("DeviceInstance"," controller_instance name device_type_descriptor id param_values pinning location_info event_alias_map") 
#DeviceDefinition  = namedtuple("DeviceDefinition", " dev_type key param_list_info extras location_info")
DeviceTypeDescriptor  = namedtuple("DeviceTypeDescriptor", "type_name key param_list_info pinning_description extras location_info")

#ProtocolAdapters     = {}
#ProtocolAdapters ["CCAN"] = 0

SensorDriverTypeKeys = {}
SensorDriverTypeKeys["BINARY_INPUT"] = 0
SensorDriverTypeKeys["MOTION"]       = 1
SensorDriverTypeKeys["TEMPERATURE"]  = 2
SensorDriverTypeKeys["BRIGHTNESS"]   = 3
SensorDriverTypeKeys["WIND"]         = 4
SensorDriverTypeKeys["TIME"]         = 5
SensorDriverTypeKeys["BINARY_OUTPUT"]= 6


CommunicationDriverTypeKeys = {}
CommunicationDriverTypeKeys["CAN_DRIVER"]       = 0
CommunicationDriverTypeKeys["ETHERNET_DRIVER"]   = 1
CommunicationDriverTypeKeys["I2C_DRIVER"]       = 2

#TransportAdapterTypeKeys = {}
#TransportAdapterTypeKeys["ETHERNET"]  = 0
#TransportAdapterTypeKeys["CAN"]       = 1

ElementTypes = []
ElementTypes.append("DRIVER")
ElementTypes.append("APPLICATION")
ElementTypes.append("TRANSPORT_ADAPTER")
ElementTypes.append("COMMUNICATION_DRIVER")
ElementTypes.append("DEVICE")

DegradationStatus = []
DegradationStatus.append("NOT DEGRADED")
DegradationStatus.append("DEGRADATION SOURCE")
DegradationStatus.append("DEGRADED")


#SupportedVariableTypes = ["UINT8","UINT16","UINT32","UINT64","FLOAT","STRING","NAME","IPV4_ADDRESS","CCAN_ADDRESS","BUS"]


HwDriverType                     = namedtuple("HwDriverType","name key")
HwDriverImplementationDescriptor = namedtuple("HwDriverImplementationDescriptor","name key implemented_driver_type param_list_info location_info")
HwDriverInstance                 = namedtuple("HwDriverInstance","type_descriptor param_values")

ControllerTypeDescriptor         = namedtuple("ControllerTypeDescriptor","name pin_map param_list_info location_info")
#ControllerInstance               = namedtuple("ControllerInstance","name type_descriptor driver_list param_values pin_usage pin_alias location_info")
ControllerPin                    = namedtuple("ControllerPin","controller pin")

PinUsage               = namedtuple("PinUsage","name pin_index type param_values alias description")
#DevicePinUsage       = namedtuple("DevicePinUsage","name pin_index driver_instance hw_instance alias description")

ConvertedDeviceBody    = namedtuple("ConvertedBody","name type_name type id")
ConvertedMappingBody      = namedtuple("ConvertedMappingBody","controller_instance mapper_type")

ConvertedMappingParameter = namedtuple("ConvertedMappingParameter","device_id event_type device_name event_name parameter_list")
ConvertedMapping       =  namedtuple("ConvertedMapping","body from_mapping_parameter to_mapping_parameter_list")
ConvertedParameterList = namedtuple("ConvertedParameter","names values")
ConvertedDevice          = namedtuple("ConvertedItem","converted_device_body converted_parameter_list")

# General Descriptions:
ConvertedDeviceDefinition = namedtuple("ConvertedDeviceDefinition","type_name key param_list_info")
ConvertedEventDefinition  = namedtuple("ConvertedEventDefinition","type_name event_info")

ControllerConfiguation = namedtuple("ControllerConfiguration","device_instances internal_mappings_descriptor_sets inbound_mappings_descriptor_sets outbound_mappings_descriptor_sets")
ControllerMappingSet   = namedtuple("ControllerMappingSet","simple_mapper fixed_data_event_mapper")

PinningListInfo = namedtuple("PinningListInfo","pin_name_list pin_type_list" )
Pinning         = namedtuple("Pinning","controller_list pin_name_list")


#ConvertedConfiguration = namedtuple("ConvertedControllerConfiguration")
Version = namedtuple("Version","major minor patch")
TextParameterSet = namedtuple("TextParameterSet","names values types")
TextWriterDevice = namedtuple("TextWriterDevice", "controller name type type_key id parameter_set")
TextMappingRuleDescriptor = namedtuple("MappingRuleDescriptor","from_event to_event_list")
TextEventDescriptor = namedtuple("TextEventDescriptor","device_name event_name device_id event_type parameter_set")
TextMappingDescriptor = namedtuple("TextMappingDescriptor","name id mappings")

TextWriterOutput = namedtuple("TextWriterOutput","version device_list")



