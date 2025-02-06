from ..resolver.ParameterStore import ParameterStore# ,OperandTypeKey,ElementTypeKey
from api.resolver.ResolverElements import ProtocolType, MappingType, ResolvedParameter, ParameterFormat, MapperType

from ..PyCCAN_Writables import WriteableDevice, WriteableVariable, WriteableMapperDevice,WriteableMappingType, WriteableRule, WriteableConfig
from api.resolver.ResolverElements import ResolvedEventInstance


class ControllerMappingStore():
    def __init__(self):
        self._mappings = {}
        self._mappings_order = {}        
        for mapper_type in ["INTERNAL","INBOUND","OUTBOUND"]:
            self._mappings[mapper_type] = {}          
            self._mappings_order[mapper_type] = {}  
            for protocol_type in ProtocolType().get_list_of_types():
                self._mappings[mapper_type][protocol_type] = {}               
                self._mappings_order[mapper_type][protocol_type] = {}  
                for mapping_type in MappingType().get_list_of_types():
                    self._mappings[mapper_type][protocol_type][mapping_type] = {}
                    self._mappings_order[mapper_type][protocol_type][mapping_type] = {}
                    
                    self._mappings_order[mapper_type][protocol_type][mapping_type]["CURRENT_INDEX"] = 0


    def add_mapping(self,mapper_type, protocol_type, mapping_type, source_event,target_event):

        try:
            mappings = self._mappings[mapper_type][protocol_type][mapping_type][source_event]                  
            # check for existing mappings:        
            if target_event is None:
                if len(mappings) > 0:
                    raise KeyError # Error     
                else:
                    return                                         
            mappings.append(target_event)
            #self._mappings[mapper_type][protocol_type][mapping_type][source_event] = mappings
        except KeyError:
            current_index =  self._mappings_order[mapper_type][protocol_type][mapping_type]["CURRENT_INDEX"]
            
            if target_event is not None:
                self._mappings[mapper_type][protocol_type][mapping_type][source_event] = [target_event]
            else:
                 self._mappings[mapper_type][protocol_type][mapping_type][source_event] = []

            self._mappings_order[mapper_type][protocol_type][mapping_type][source_event] = current_index
 
            self._mappings_order[mapper_type][protocol_type][mapping_type]["CURRENT_INDEX"] = current_index + 1


    def get_list_of_mapper_directions(self):
        return list(self._mappings.keys())
        
    def is_mapper_device_needed(self,mapper_type,protocol_type):    
        
        if mapper_type == "OUTBOUND":
            return True
        
        for mapping_types in self._mappings_order[mapper_type][protocol_type]:
            selected_mappings = self._mappings_order[mapper_type][protocol_type][mapping_types]
            if len(selected_mappings.keys()) > 1: # ignore "CURRENT_INDEX" element
                return True
        return False  
    
    def get_source_mapping_list(self,mapper_type,protocol_type,mapping_type):
        list_of_source_events = list(self._mappings[mapper_type][protocol_type][mapping_type].keys())        
        list_of_indices = list(map(lambda x: self._mappings_order[mapper_type][protocol_type][mapping_type][x], list_of_source_events))        
        #sorted_source_events = list(map(lambda x: list_of_source_events[x],list_of_indices))
        return list_of_source_events
    
    #def get_sorted_mappings_as_list(self,mapping_direction,protocol_type):
    #    return self._mappings

    def get_target_mappings(self, mapper_type,protocol_type,mapping_type,source_event):
        list_of_target_events = self._mappings[mapper_type][protocol_type][mapping_type][source_event]
        return list_of_target_events

class ControllerStore ():
 
    __controller_map                 = {}
    __controller_map_helper          = {}

    MAPPER_DEVICE_KEY_OFFSET      = 10
 
    simple_mapper_key              = 1
    fixed_data_event_mapper_key    = 2
    variable_data_event_mapper_key = 3    
        
    variable_manager_device_id     = 10
 
    available_protocol_types    = None
 
    _param_values = None
    
    #__current_device_id = None
    __last_used_device_id    = None
    
    __app_config_key_map = {}
    
    __INVALID_DRIVER_KEY = 255

    def __init__(self,my_name):
        self.__name             = my_name
        self.__config           = WriteableConfig()
 
        self._communication_drivers  = []
        self._sensor_drivers         = []   
        self._transport_adapters     = []
        self._apps                   = []
        self._vartab                 =  []
        self._devices                = []
        
        ###############################
        
        #self.__board_pinning_list = []
        self._controller_name = None

        self._internal_mappings = {} 
        self._inbound_mappings  = {} 
        self._outbound_mappings = {} 
 
        self._inbound_protocol_mappings = {}
        self._outbound_protocol_mappings = {}
 
 
        self.__mapping_store = ControllerMappingStore()       

    @staticmethod
    def get_controller_map():
       return  ControllerStore.__controller_map


    def get_controller_type(self):
        return self.__controller_type

    def add_mapping(self,mapper_type, protocol_type, mapping_type, source_event,target_event):
        self.__mapping_store.add_mapping(mapper_type, protocol_type, mapping_type, source_event,target_event)
     
    def create_mapper_devices(self):
               
        for mapper_type in self.__mapping_store.get_list_of_mapper_directions():
            for protocol_type in ProtocolType().get_list_of_types():               
                # check whether there is at least one mapping for at least one mapping type
                # in that case create a mapping device
                if self.__mapping_store.is_mapper_device_needed(mapper_type,protocol_type):                                        
                    
                    # retrieve length of event id information:
                    if mapper_type == "INBOUND":
                        source_key_length = ProtocolType.get_key_length(protocol_type)
                        target_key_length = ProtocolType.get_key_length("CCAN")
                    elif mapper_type == "OUTBOUND":                    
                        source_key_length = ProtocolType.get_key_length("CCAN")
                        target_key_length = ProtocolType.get_key_length(protocol_type)
                    else: # INTERNAL
                        source_key_length = ProtocolType.get_key_length("CCAN")
                        target_key_length = ProtocolType.get_key_length("CCAN")                        
                                                     
                    mapping_device = WriteableMapperDevice(mapper_type,ProtocolType(protocol_type),source_key_length,target_key_length)       
                    mapping_device.set_name_id_and_type(mapper_type+"_MAPPER_" + protocol_type,ControllerStore.__get_new_unused_device_id(), ControllerStore.MAPPER_DEVICE_KEY_OFFSET+MapperType(mapper_type).get_key())
       
                    for mapping_type in MappingType().get_list_of_types():
                        mapping_type_set = WriteableMappingType(MappingType(mapping_type))
                        source_events = self.__mapping_store.get_source_mapping_list(mapper_type,protocol_type,mapping_type)
                        # add mapping type, iff there is at least one mapping:
                        if len(source_events) > 0:                                                     
                            for source_event in source_events:
                                target_events = self.__mapping_store.get_target_mappings(mapper_type,protocol_type,mapping_type,source_event)                                       
                                if target_events == [None]:
                                    target_events = None ##??
                                                                   
                                new_mapping_rule = WriteableRule(source_event,target_events)
                                mapping_type_set.insert_rule(new_mapping_rule)                            
                        
                            mapping_device.insert_mapping_type(mapping_type_set)
                    
                    self._devices.append(mapping_device)      
          
        
    def add_variable(self,variable_instance):
        self._vartab.append(WriteableVariable(variable_instance))
       
    def _sort_outbound_protocol_mapping_tables_TO_BE_REMREVBE(self,mappings): 
        keys = mappings.keys()
        sorted_keys = sorted(keys,key=lambda tup: (tup[0],tup[1], tup[2]))
        return sorted_keys
         
    def write_config(self,my_writer, my_controller_crc):

        crc = ResolvedParameter("CONTROLLER_CRC", my_controller_crc & 0xffffffff, ParameterFormat("UINT32"),None)

        major = ResolvedParameter("MAJOR", ControllerStore.__version[0], ParameterFormat("UINT16"),None)
        minor = ResolvedParameter("MINOR", ControllerStore.__version[1], ParameterFormat("UINT16"),None)  
        patch = ResolvedParameter("PATCH", ControllerStore.__version[2], ParameterFormat("UINT16"),None)                  
        version  = [major,minor,patch]
        
        self.__config.set_controller_crc(crc)                
        self.__config.set_version(version)
     
        self.__config.set_communication_drivers(self._communication_drivers)        
        self.__config.set_transport_adapters(self._transport_adapters)
        self.__config.set_sensor_drivers(self._sensor_drivers )
        self.__config.set_apps(self._apps)
        self.__config.set_variables(self._vartab )
        self.__config.set_devices(self._devices )
        
        self.__config.write(my_writer)
        
 
    def __insert_app(self, my_app_instance):
 
        # for controller CRC identification:
        if my_app_instance.get_controller_name() == my_app_instance.get_name():
            self.__controller_type = my_app_instance.get_type()

        for (driver_id, driver) in my_app_instance.get_description_list("SENSOR_DRIVER"):
             self._sensor_drivers.append(WriteableDevice(driver))  
 
        for (driver_id, driver) in my_app_instance.get_description_list("COMMUNICATION_DRIVER"):
             self._communication_drivers.append(WriteableDevice(driver))  
 
        for (driver_id, driver) in my_app_instance.get_description_list("TRANSPORT_ADAPTER"):
             self._transport_adapters.append(WriteableDevice(driver)) 
                     
        self._apps.append(WriteableDevice(my_app_instance))        


    def _write_outbound_mapper_device(self,my_writer,mappings_list,protocol_type):

        # sort mappings:
        keys_list = self. _sort_mapping_tables(mappings_list) 
  
        my_writer.open_mapping_set(self.available_protocol_types[protocol_type].id,3,3)
        
        mapper_types = [  self.simple_mapper_key,  self.fixed_data_event_mapper_key]
        length_flag_set = [ False, True]
        
        for mappings_key,keys,mapper_type, length_flag in zip (mappings_list,keys_list,mapper_types,length_flag_set):
            mappings = mappings_list[mappings_key]
            my_writer.open_mapping(mappings_key, mapper_type, length_flag)    
            for entry in keys:
                mapping_descriptor_set    = mappings[entry]
                
                self.__write_from_mapping_description_ccan(my_writer, mapping_descriptor_set.from_mapping_description,length_flag,len(mapping_descriptor_set.to_mapping_description_list))             
                for to_mapping_description in mapping_descriptor_set.to_mapping_description_list:
                    self.__write_to_mapping_description_ccan(my_writer, to_mapping_description,length_flag)  
                    my_writer.close_to_event()
                    
                my_writer.close_from_event()
            my_writer.close_mapping()
        my_writer.close_mapping_set()
 
    def _write_outbound_protocol_mapper_device(self,my_writer,mappings_list,protocol_type):

        # sort mappings:
        keys_list = self. _sort_mapping_tables(mappings_list) 
 
        my_writer.open_mapping_set(self.available_protocol_types[protocol_type].id,3,3)
        
        mapper_types = [  self.simple_mapper_key,  self.fixed_data_event_mapper_key]
        length_flag_set = [ False, True]
        
        for mappings_key,keys,mapper_type, length_flag in zip (mappings_list,keys_list,mapper_types,length_flag_set):
            mappings = mappings_list[mappings_key]
            my_writer.open_mapping(mappings_key, mapper_type, length_flag)    
            for entry in keys:
                mapping_descriptor_set    = mappings[entry]
                
                self.__write_from_mapping_description_ccan(my_writer, mapping_descriptor_set.from_mapping_description,length_flag,len(mapping_descriptor_set.to_mapping_description_list))             
                for to_mapping_description in mapping_descriptor_set.to_mapping_description_list[0]:
                    self.__write_to_protocol_mapping_description_ccan(my_writer, to_mapping_description,length_flag)  
                    my_writer.close_to_event()
                    
                my_writer.close_from_event()
            my_writer.close_mapping()
        my_writer.close_mapping_set()


    def _write_mapper_device(self,my_writer,mappings_list,protocol_type):

        # sort mappings:
        keys_list = self. _sort_mapping_tables(mappings_list) 
 
        #my_writer.open_mapping_set()

        my_writer.open_mapping_set(self.available_protocol_types[protocol_type].id,3,3)

        
        mapper_types = [  self.simple_mapper_key,  self.fixed_data_event_mapper_key, self.variable_data_event_mapper_key]
        length_flag_set = [ False, True,True]
        
        for mappings_key,keys,mapper_type, length_flag in zip (mappings_list,keys_list,mapper_types,length_flag_set):
            mappings = mappings_list[mappings_key]
            my_writer.open_mapping(mappings_key, mapper_type, length_flag)    
            for entry in keys:
                mapping_descriptor_set    = mappings[entry]

                self.__write_from_mapping_description_ccan(my_writer, mapping_descriptor_set.from_mapping_description,length_flag,len(mapping_descriptor_set.to_mapping_description_list))             
                for to_mapping_description in mapping_descriptor_set.to_mapping_description_list:
                    self.__write_to_mapping_description_ccan(my_writer, to_mapping_description,length_flag)  

                    my_writer.close_to_event()
                my_writer.close_from_event()
            my_writer.close_mapping()
        my_writer.close_mapping_set()

    def __write_from_mapping_description_ccan(self,my_writer,mapping_description,length_flag,length):
        if length_flag is True:                # prepare parameter:
            self.__write_parameter_set(my_writer,mapping_description) 
        my_writer.add_from_event(mapping_description.device_name,mapping_description.id,mapping_description.event_name,mapping_description.key,length)

        
    def __write_to_mapping_description_ccan(self,my_writer,mapping_description,length_flag):
        if length_flag is True:                # prepare parameter:
            self.__write_parameter_set(my_writer,mapping_description)
        my_writer.add_to_event(mapping_description.device_name,mapping_description.id,mapping_description.event_name,mapping_description.key)

    def __write_parameter_set(self,my_writer,mapping_description):
        my_writer.open_parameter_list()                                         
        for parameter in mapping_description.parameter_set:
            if isinstance(parameter.value,list):                                         
                self.__write_expression_parameter(my_writer,parameter)
            else:
                #if isinstance(parameter,VariableParameterSet) and parameter.variable_flag == 1:
                #    my_writer.write_parameter("VariableDataIndicator",1,"UINT8")   
                #    my_writer.write_parameter("VariableFormat",OperandTypeKey[parameter.type],"UINT8")   
                #    my_writer.write_parameter("VariableID",parameter.value,"UINT16")
                #    
                #elif isinstance(parameter,VariableParameterSet) and parameter.variable_flag == 0:
                #    my_writer.write_parameter("VariableDataIndicator",0,"UINT8")   
                 #   my_writer.write_parameter(parameter.name,parameter.value,parameter.type)
                #else:
                #    my_writer.write_parameter(parameter.name,parameter.value,parameter.type)
                pass
            
        my_writer.close_parameter_list()


    def __write_to_protocol_mapping_description_ccan(self,my_writer,mapping_description,length_flag):
        if length_flag is True:                # prepare parameter:
            my_writer.open_parameter_list()
                        #if to_mapping_description.param_list != None:                        
            for parameter in mapping_description.parameter_set:
                my_writer.write_parameter(parameter.name,parameter.value,parameter.type)
            my_writer.close_parameter_list()
        my_writer.add_to_event(mapping_description.path_set.name,mapping_description.path_set.value,mapping_description.event_set.name,mapping_description.event_set.value)

    @staticmethod
    def create_controller_stores(my_resolver):
                
        #Resolver.__resolver = my_resolver
        #description_dictionary = my_resolver.resolver_store.get_description_map() #get_description_dictionary()
        instance_dictionary    = my_resolver.resolver_store.get_instance_map() #get_instance_dictionary()

        # read version:        
        ControllerStore.__version = my_resolver.resolver_store.get_version()#get_instance_dictionary()["version"]

        # create empty controller stores:
        ControllerStore.__controller_map = {}
        for (id, app_instance) in instance_dictionary["APP"]:            
            if app_instance.is_app() is  False: 
                # Board is the Controller
                name = app_instance.get_name()
                controller_store = ControllerStore(name)                                              
                ControllerStore.__controller_map[name] = controller_store                                  
            else:
                # This board is an APP. Get the connected Controller:
                controller_store = ControllerStore.__controller_map[app_instance.get_controller_name()]
            
            ControllerStore.__controller_map_helper[app_instance.get_name()] = app_instance.get_controller_name()
            
            # add board/app to the selected controller store
            controller_store.__insert_app(app_instance)
                                    
        # 1) separate devices:
        my_list_of_devices = instance_dictionary["DEVICE"]
        ControllerStore.__last_used_device_id = 0
        for (id, stored_device) in  my_list_of_devices:
            
            # sort out template devices:
            if stored_device.is_template() is False:            
                # get first connection:
                connection = stored_device.get_description_list("CONNECTION")[0]
                app_instance = instance_dictionary["APP"].get_entry_by_name(connection.get_app_name())
                
                
                controller_name = app_instance.get_controller_name()
            
                controller_store = ControllerStore.__controller_map[controller_name]
                controller_store._devices.append(WriteableDevice(stored_device))

                if id >  ControllerStore.__last_used_device_id:
                    ControllerStore.__last_used_device_id = id
            
        # 2) separate mappings:
        master_list_of_maps = instance_dictionary["MAPPING"]
        for protocol_type in master_list_of_maps:
            for mapping_type in master_list_of_maps[protocol_type]:
                # sorting the sourde events first:
                source_events           = list(master_list_of_maps[protocol_type][mapping_type].keys())
                sorted_source_events    = ControllerStore.__sort_events(source_events,mapping_type)
                
                for sorted_source_event in sorted_source_events:                
                    target_events = master_list_of_maps[protocol_type][mapping_type][sorted_source_event]
                    for target_event in target_events:
                    
                        try:
                            source_controller = ControllerStore.__controller_map[ControllerStore.__controller_map_helper[sorted_source_event.get_controller_name()]]
                        except KeyError:
                            source_controller = None
                        try:
                             target_controller = ControllerStore.__controller_map[ControllerStore.__controller_map_helper[target_event.get_controller_name()]]
                        except KeyError:
                            target_controller = None
                        except AttributeError:
                            target_controller = None
                          
  
                       
                        # external protocol events 
                        if source_controller is None:
                            source_controller = target_controller
                        if target_controller is None:
                            target_controller = source_controller
                    
                        # this is for HA integration: target_event is None. These events shall be shipped anyway.    
                        if target_event is None and sorted_source_event.get_type() == "CCAN":
                            source_controller.add_mapping("OUTBOUND",protocol_type, mapping_type, sorted_source_event,None)  
                      
                        #if protocol_type == "CCAN":        
                        else:                                                  
                            if sorted_source_event.get_type() == "CCAN" and target_event.get_type() == "CCAN":
                                # CCAN -> CCAN mapping:
                                # Check for internal mapping vs inbound/outbound:
                                # pr(int(sorted_source_event.get_controller_name() + " <->" + target_event.get_controller_name())

                                if sorted_source_event.get_controller_name() == target_event.get_controller_name():
                                    if sorted_source_event.get_direction() == "IN":
                                        # "IN" -> "IN" = Inbound-Mapping
                                        target_controller.add_mapping("INBOUND",protocol_type, mapping_type, sorted_source_event,target_event)            
                                    elif target_event.get_direction() == "OUT":
                                        source_controller.add_mapping("OUTBOUND",protocol_type, mapping_type, sorted_source_event,target_event)    
                                    else:
                                        # "OUT" -> "IN"  = Internal Mapping
                                        source_controller.add_mapping("INTERNAL",protocol_type, mapping_type, sorted_source_event,target_event)                                                                                                                                                                                    
                                else:
                                    # Outbound to allow events to leave the controller (unmapped)
                                    source_controller.add_mapping("OUTBOUND",protocol_type, mapping_type, sorted_source_event,None)  
                                    # Inbound Mapping for actual mappings from source to target event:
                                    target_controller.add_mapping("INBOUND",protocol_type, mapping_type, sorted_source_event,target_event)                                   
                            else:                                                        
                                if sorted_source_event.get_type() == "CCAN":
                                    # source is CCAN, then destination is to be converted -> OUTBOUND-ProtocolMapper:
                                    source_controller.add_mapping("OUTBOUND",target_event.get_type(), mapping_type, sorted_source_event,target_event) 
                                else:
                                    # source is an incoming event -> INBOUND-ProtocolMapper:
                                    source_controller.add_mapping("INBOUND",sorted_source_event.get_type(), mapping_type, sorted_source_event,target_event) 
         
         
        # 4) create mapper devices from separated mappings:
        for (id,controller_store) in  ControllerStore.__controller_map.items():
            controller_store.create_mapper_devices()
            
          
        # 5) separate variables and add mirror variables where needed:                  
        master_list_of_variables =  instance_dictionary["VARIABLE"]    
        for (id,variable_instance) in master_list_of_variables:
            list_of_controller_names = variable_instance.get_reference_controller_names()
            for controller_name in list_of_controller_names:
                controller_store = ControllerStore.__controller_map[controller_name]
                controller_store.add_variable(variable_instance)            

############################

    @staticmethod
    def __get_new_unused_device_id():
        id = ControllerStore.__last_used_device_id
        ControllerStore.__last_used_device_id += 1
        return id

    #@staticmethod
    #def calculate_key(my_key):
    #    pass

    @staticmethod
    def __sort_events(list_of_source_events, mapping_type):
        if list_of_source_events == []:
            return list_of_source_events   
   
        # retrieve keys from event list:
        key_list = []   
        for event in list_of_source_events:
            param_key = ''
            if str(mapping_type) != "SIMPLE":
                resolved_parameters = event.get_description_list("PARAMETER")            
                param_key = ParameterStore.convert_param_list_to_byte_array(resolved_parameters)
                    
            key_list.append( (event.get_id_set().get_value() , param_key))
        
        sorted_key_list = sorted(key_list,key = lambda tup: (tup[0],tup[1]))
        sorted_source_events = [  list_of_source_events[index] for index in [key_list.index(key) for key in sorted_key_list]]                                
        return sorted_source_events       
