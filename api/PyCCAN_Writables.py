

from src.resolver.ResolverElements import ResolvedParameter, ParameterFormat
    
class Writeable():
    def __init__(self):
        raise NotImplementedError
    
    def write(self,writer):
        raise NotImplementedError

class WriteableConfig(Writeable):
    def __init__(self):
        self.__controller_crc = None
        self.__version  = None
        
        self.__adapter_list          = []
        self.__communication_drivers = []
        self.__sensor_driver_list    = []
        self.__variable_list         = []
        self.__device_list           = []
        self.__app_list              = []
        
        
        self.__configuration_sections = {}
        self.__configuration_sections["HEADER"]                 = 0
        self.__configuration_sections["COMMUNICATION_DRIVERS" ] = 1
        self.__configuration_sections["TRANSPORT_ADAPTERS"]     = 2
        self.__configuration_sections["APPLICATIONS"]           = 3
        self.__configuration_sections["SENSOR_DRIVERS"]         = 4
        self.__configuration_sections["VARIABLES"]              = 5
        self.__configuration_sections["DEVICES"]                = 6
        

    def set_controller_crc(self,my_controller_crc):
        self.__controller_crc = WriteableParameter(my_controller_crc,"CONTROLLER_CRC")
                    
    def set_version(self, my_resolved_version):
        self.__version = WriteableParameterSet(my_resolved_version)
        
    def set_transport_adapters(self,my_adapter_list):
        self.__adapter_list = my_adapter_list
        
    def set_communication_drivers(self,my_communication_driver_list):
        self.__communication_drivers = my_communication_driver_list
    
    def set_sensor_drivers(self,my_sensor_driver_list):
        self.__sensor_driver_list = my_sensor_driver_list
        [driver.set_no_connection_information() for driver in self.__sensor_driver_list] 
    
    def set_apps(self,my_app_list):
        self.__app_list = my_app_list
    
    def set_variables(self,my_variable_list):
        self.__variable_list = my_variable_list
    
    def set_devices(self,my_device_list):
        self.__device_list = my_device_list    
        
        

    def write(self,my_writer):
        my_writer.open()
        my_writer.open_configuration_section("HEADER",self.__configuration_sections["HEADER"])    
        my_writer.write_cookie()        
        self.__controller_crc.write(my_writer)        
        self.__version.write(my_writer)
        
        #######################
        
        number_of_communication_drivers = ResolvedParameter("NumberOfCommunicationDrivers",len(self.__communication_drivers),ParameterFormat("UINT16"),None)
        number_of_transport_adapters    = ResolvedParameter("NumberOfTransportAdapters",len( self.__adapter_list),ParameterFormat("UINT16"),None)
        number_of_apps                  = ResolvedParameter("NumberOfApps",len(self.__app_list),ParameterFormat("UINT16"),None)
        number_of_sensor_drivers        = ResolvedParameter("NumberOfSensorDrivers",len(self.__sensor_driver_list),ParameterFormat("UINT16"),None)
        number_of_variables             = ResolvedParameter("NumberOfVariables",len( self.__variable_list),ParameterFormat("UINT16"),None)
        number_of_devices               = ResolvedParameter("NumberOfDevices",len( self.__device_list),ParameterFormat("UINT16"),None)        
        
        initial_parameter_list          = [ number_of_communication_drivers,
                                            number_of_transport_adapters,
                                            number_of_apps,
                                            number_of_sensor_drivers,
                                            number_of_variables,
                                            number_of_devices
                                          ]

        WriteableParameterSet(initial_parameter_list).write(my_writer)
        my_writer.close_configuration_section()
  
        ######################## Write tables:
        
        my_writer.open_configuration_section("COMMUNICATION_DRIVERS",self.__configuration_sections["COMMUNICATION_DRIVERS"])
        for driver in self.__communication_drivers:
            driver.write(my_writer)
        my_writer.close_configuration_section()


        my_writer.open_configuration_section("TRANSPORT_ADAPTERS",self.__configuration_sections["TRANSPORT_ADAPTERS"])
        for driver in self.__adapter_list:
            driver.write(my_writer)
        my_writer.close_configuration_section()

        my_writer.open_configuration_section("APPLICATIONS",self.__configuration_sections["APPLICATIONS"])
        for driver in self.__app_list:
            driver.write(my_writer)
        my_writer.close_configuration_section()

        my_writer.open_configuration_section("SENSOR_DRIVERS",self.__configuration_sections["SENSOR_DRIVERS"])
        for driver in self.__sensor_driver_list:
            driver.write(my_writer)            
        my_writer.close_configuration_section()
        
        my_writer.open_configuration_section("VARIABLES",self.__configuration_sections["VARIABLES"])                   
        for variable in self.__variable_list:
            variable.write(my_writer)
        my_writer.close_configuration_section()
        
        my_writer.open_configuration_section("DEVICES",self.__configuration_sections["DEVICES"])
        for device in self.__device_list:
            device.write(my_writer)  
        my_writer.close_configuration_section()
            
        my_writer.close()

class WriteableDevice(Writeable):
    
    def __init__(self, resolved_device):
        self.__device_name         = resolved_device.get_name()     
        self.__id_set              = WriteableParameterSet(resolved_device.get_description_list("ID"))
        self.__status_variable_set = WriteableParameterSet(resolved_device.get_description_list("VARIABLE"))
        self.__connection_set      = WriteableParameterSet(resolved_device.get_description_list("CONNECTION"))
        self.__parameter_set       = WriteableParameterSet(resolved_device.get_description_list("PARAMETER"))
        self.__add_connection_info = True     
        self.__resolved_device = resolved_device      
                   
    def set_no_connection_information(self):
        self.__add_connection_info = False
                   
    def write(self,my_writer):
        
        my_writer.open_length_encoded_section(self.__device_name + "(KEY = " +  str(self.__resolved_device.get_type_key()) + ", ID = " + str(self.__resolved_device.get_id())+ ")")
        self.__id_set.write(my_writer)       
         
        #my_writer.open_length_encoded_section("PARAMETER_SET")  
        if (self.__connection_set.is_empty() is False) and  (self.__add_connection_info == True):
            my_writer.open_section("CONNECTION")
            self.__connection_set.write(my_writer)
            my_writer.close_section()
        
        if self.__status_variable_set.is_empty() is False:
            my_writer.open_section("VARIABLE")
            self.__status_variable_set.write(my_writer)
            my_writer.close_section()

        if self.__parameter_set.is_empty() is False:         
            my_writer.open_section("PARAMETER")
            self.__parameter_set.write(my_writer)
            my_writer.close_section()
        
        my_writer.close_length_encoded_section(ParameterFormat("UINT16"))
        #my_writer.close_section()

class WriteableParameterSet(Writeable):
    def __init__(self,resolved_parameter_set):
        self.__parameter_names       = []
        self.__parameter_values      = []
        self.__parameter_formattings = []
        
        for item in resolved_parameter_set:
            self.__parameter_names.append(item.get_name())
            self.__parameter_values.append(item.get_value())
            self.__parameter_formattings.append(item.get_format())            
    
    def write(self,writer):
        for name,value,parameter_format in  zip(self.__parameter_names, self.__parameter_values,self.__parameter_formattings):
            writer.write_item(name,value,parameter_format)     
            
    def is_empty(self):
        if len(self.__parameter_names) == 0:
            return True
        return False
            
class WriteableParameter(Writeable):
    def __init__(self,my_resolved_parameter, my_comment):
        self.__name      = my_resolved_parameter.get_name()
        self.__value     = my_resolved_parameter.get_value()
        self.__format    = my_resolved_parameter.get_format()
        self.__comment   = my_comment
                  
    
    def write(self,my_writer):       
        my_writer.write_item(self.__name, self.__value, self.__format, self.__comment)     



class WriteableMapperDevice(Writeable):
    def __init__(self,mapper_type,protocol_type,source_key_length,target_key_length):
       self.__mapper_type = mapper_type
       self.__protocol_type = protocol_type
       self.__source_key_length = source_key_length
       self.__target_key_length = target_key_length
       self.__mapping_type_list = []
       
    def insert_mapping_type(self, my_mapping_type_set):
        self.__mapping_type_list.append(my_mapping_type_set)

    def set_name_id_and_type(self,my_name, my_id, my_type_key):
        self.__device_name         = my_name
        self.__id                  = my_id
        self.__type_key            = my_type_key
    
    def write(self,my_writer):
        #my_writer.open_section(self.__device_name)
        my_writer.open_length_encoded_section(self.__device_name)


        # write initial parameter set describing the kind of mapper:
        id_set            = ResolvedParameter("ID_SET",(self.__type_key) + (self.__id << 16)  ,ParameterFormat("UINT32"), None)
        number_of_mappers = ResolvedParameter("NUMBER_OF_MAPPERS", len(self.__mapping_type_list), ParameterFormat("UINT8"), None)    
        protocol_type     = ResolvedParameter("PROTOCOL_TYPE",self.__protocol_type.get_key(), self.__protocol_type.get_key_format(), None) 
        source_key_length = ResolvedParameter("SOURCE_KEY_LENGTH",self.__target_key_length,ParameterFormat("UINT8"), None) 
        target_key_length = ResolvedParameter("TARGET_KEY_LENGTH",self.__target_key_length,ParameterFormat("UINT8"), None)         
        
        WriteableParameter(id_set, "KEY= " + str(self.__type_key) + " ID= " +str(self.__id)).write(my_writer)
        
        WriteableParameterSet([ number_of_mappers,protocol_type, source_key_length, target_key_length]).write(my_writer)
         
        # write the mapping rules for all mapping types (Simple, Fixed, Variable) 
        [mapping_type.write(my_writer)  for mapping_type in self.__mapping_type_list]      
    
        #my_writer.close_section()
        my_writer.close_length_encoded_section(ParameterFormat("UINT16"))

       
class WriteableMappingType(Writeable):
    def __init__(self, my_mapping_type):
        self.__mapping_type = my_mapping_type
        self.__rules = []
    
    def insert_rule(self,my_rule):
        my_rule.set_mapping_type(self.__mapping_type)
        self.__rules.append(my_rule)
            
    def write(self,my_writer):      
        my_writer.open_length_encoded_section("CONTENT FOR MAPPING_TYPE = " + str(self.__mapping_type) + " OF TYPE " + str(self.__mapping_type.get_key()))

        WriteableParameterSet([ResolvedParameter("MAPPING_TYPE",self.__mapping_type.get_key(), self.__mapping_type.get_key_format(), None)]).write(my_writer)        
        [ rule.write(my_writer) for rule in self.__rules ]            
        WriteableParameterSet([ResolvedParameter("END_CLOSURE",0, ParameterFormat("UINT16"), None)]).write(my_writer)        
        my_writer.close_length_encoded_section("UINT16")
        
    
class WriteableRule(Writeable):
    def __init__(self, my_source_event, my_target_events):
        self.__source_event = my_source_event
        self.__target_events = my_target_events
        self.__mapping_type = None
    
    def set_mapping_type(self,my_mapping_type):
        self.__mapping_type = my_mapping_type
    
    def write(self,my_writer):
        my_writer.open_section("RULE_START:")
        
        # start with length information for this rule:
        my_writer.open_length_encoded_section("LENGTH_OF_RULE") 
     
        # start with from event:        
        my_writer.open_section("FROM_EVENT:")
        WriteableEvent(self.__source_event,self.__mapping_type).write(my_writer)
             
        my_writer.close_section()
        # collect target events:
        target_events = []
        for target_event in self.__target_events:
            target_events.append(WriteableEvent(target_event,self.__mapping_type))
                                    
        my_writer.open_section("TO EVENT(S):")                       
        # state number of target events: 
        WriteableParameterSet([ResolvedParameter("NUMBER_OF_MAPPINGS",len(target_events), ParameterFormat("UINT8"), None)]).write(my_writer)                    
        # write all target events:        
        [target_event.write(my_writer) for target_event in target_events]                                        
          
        my_writer.close_section()
        my_writer.close_length_encoded_section(ParameterFormat("UINT16"))
        my_writer.close_section()


class WriteableEvent(Writeable):
    def __init__(self, my_event, my_mapping_type):
        self.__event = my_event
        self.__mapping_type = my_mapping_type

    def write(self,my_writer):
        (event_path_name, event_path_key)  = self.__event.get_description_list("EVENT_PATH")
        (event_id_name, event_id_key) = self.__event.get_description_list("EVENT_TYPE")
        event_path = ResolvedParameter("EVENT_PATH",event_path_key,ParameterFormat("UINT16"), None)
        event_id = ResolvedParameter("EVENT_ID",event_id_key,ParameterFormat("UINT8"), None)
        my_writer.write_comment(event_path_name + "::" + event_id_name)
        WriteableParameterSet([ event_path, event_id]).write(my_writer) 
        
        if str(self.__mapping_type) == "SIMPLE":
            return
        
        if str(self.__mapping_type) == "FIXED":
            parameters = self.__event.get_description_list("PARAMETER")
            my_writer.open_length_encoded_section("PARAMETER_SET")  
            my_writer.open_section("PARAMETER")
            WriteableParameterSet([ parameter for parameter in parameters]).write(my_writer)
            my_writer.close_section()    
            my_writer.close_length_encoded_section(ParameterFormat("UINT16"))  

        if str(self.__mapping_type) == "VARIABLE":
            parameters = self.__event.get_description_list("PARAMETER")
                                    
            my_writer.open_length_encoded_section("EXPRESSION")  
        
            if len(parameters) > 0:
                my_writer.open_section("EXPRESSION")
                for parameter in parameters:   
                        # target format:
                        target_format = parameter.get_format()
                        WriteableParameterSet([ResolvedParameter("TARGET_FORMAT",target_format.get_key(),target_format.get_key_format(),None )]).write(my_writer)
                        # expression:                  
                        [WriteableExpressionElement(element).write(my_writer)  for element in parameter.get_value_as_expression()]
                                
                my_writer.close_section()   
                 
            my_writer.close_length_encoded_section(ParameterFormat("UINT16"))  


class WriteableVariable(Writeable):
    def __init__(self, my_variable_instance):
        self.__variable = my_variable_instance

    def write(self, my_writer):
        # <ID> <Format><Type> [<Expr>]
        my_writer.open_section(self.__variable.get_name())        

        id_value       = ResolvedParameter("ID", self.__variable.get_id(),ParameterFormat("UINT16"),None)
        format_value   = ResolvedParameter("FORMAT", self.__variable.get_format().get_key(), self.__variable.get_format().get_key_format(),None)   

        # each variable entry shall cover 4 Bytes in the descriptive part to avoid compiler issues:
        is_expression_value =  0 if self.__variable.is_expression() is False else 1
        publish_value  =  1 if (len(self.__variable.get_reference_controller_names()) > 1 and is_expression_value == False) else 0
        attribute_value  = is_expression_value + (publish_value << 1)
        attribute      = ResolvedParameter("ATTRIBUTE", attribute_value, ParameterFormat("UINT8"),None)
        
        parameter_set = [id_value,format_value, attribute]
        #parameter_set = [id_value, var_type]        
        WriteableParameterSet(parameter_set).write(my_writer)
        
        if is_expression_value == 1:  
            my_writer.open_length_encoded_section("VARIABLE_EXPRESSION")            
            var_value    = self.__variable.get_value()
            for element in var_value:
                WriteableExpressionElement(element).write(my_writer)
            my_writer.close_length_encoded_section(ParameterFormat("UINT16")) 
        my_writer.close_section()
                      
class WriteableExpressionElement(Writeable):
    def __init__(self, my_element):
        self.__element = my_element
        
    def write(self,my_writer):
        
        parameter_set = []
        my_writer.open_section(self.__element.get_name())
        parameter_set.append(ResolvedParameter("ELEMENT_TYPE", self.__element.get_type_key(),self.__element.get_type_key_format() ,None))
        
        if self.__element.is_type("FUNCTION"):
            parameter_set.append(ResolvedParameter("OPERATOR_KEY", self.__element.get_operator_key(),self.__element.get_operator_key_format() ,None))
            
        elif self.__element.is_type("CONSTANT_FLOAT"):
            parameter_format = self.__element.get_value_format()
            parameter_set.append(ResolvedParameter("FORMAT", parameter_format.get_key(), parameter_format.get_key_format(),None))

        elif self.__element.is_type("EVENT_PARAMETER"):
            parameter_format = self.__element.get_event_parameter_format()
            parameter_set.append(ResolvedParameter("FORMAT", parameter_format.get_key(), parameter_format.get_key_format(),None))

        elif self.__element.is_type("VARIABLE"):
            pass
        else:
            self.__element.is_type("CONSTANT_FLOAT")
            raise ValueError

        parameter_set.append(ResolvedParameter("VALUE", self.__element.get_value(),self.__element.get_value_format() ,None))
        WriteableParameterSet(parameter_set).write(my_writer)
        my_writer.close_section()