import xml.etree.ElementTree as ElementTree
from collections import namedtuple
from PyCCAN_ParseError import ParseError 

class TemplateStore:


    def __init__(self):
        __template_table  = {}
        __available_template_types = {}
        __template_info     = namedtuple("TemplateInfo", "type_name type param_list text_tree")
        __template_list_info = namedtuple("param_list", "param_name_list param_type_list")
        #self.load_device_table("dummy_file")
        pass
    
    def check_parameter_type(self, input_type, requested_type, value):
        
        if (input_type == "NUMBER"):
            if (requested_type == "UINT32"):
                if (int(value) >= 2**32):
                    raise ParseError("Value " + value + " is to high. Allowed is " + str( 2**32-1)+".")
            if (requested_type == "UINT16"):
                if (int(value) >= 2**16):
                    raise ParseError("Value " + value + " is to high. Allowed is " +  str(2**16-1)+".") # return (False, 0)
            if (requested_type == "UINT8"):
                if (int(value) >=  2**8):
                    raise ParseError("Value " + value + " is to high. Allowed is " + str(2**8-1)+".") # return (False, 0)
            return value
        raise ParseError("Unknown parameter type <" + input_type + ">  .. refused to check.")
                          
    def add_device_description(self, device_name,param_list_names,param_list_types):

        new_dev_list = self.__param_list_info(param_list_names, param_list_types)        
        new_dev_info = self.__device_info(type_name=device_name, type= self.__user_device_id, param_list=new_dev_list)
        self.__available_device_types[device_name] = new_dev_info
        self.__user_device_id  += 1 
        pass
    
    def get_template_descriptions(self):
        if self.__available_device_types == {}:
            return None
        
        list_of_device_names       = []
        list_of_device_type_values = [] 

        list_of_device_names.append("NONE")
        list_of_device_type_values.append(0)

       # ToDo: double definition in PyCCAN_NEwCompiler:
        list_of_device_names.append("INTERNAL_MAPPER")
        list_of_device_type_values.append(5)
        
        for device_name in self.__available_device_types:
                device_descriptor = self.__available_device_types[device_name]
                list_of_device_names.append(device_name.upper())
                list_of_device_type_values.append(device_descriptor.type)

        return (list_of_device_names, list_of_device_type_values)

    def get_template_parameter_descriptions(self):
        
        if self.__available_device_types == {}:
            return None
         
        param_def_map   = {}
        
        for device_name in self.__available_device_types:
            device_descriptor = self.__available_device_types[device_name]
            param_def_map[device_name] = [device_descriptor.param_list.param_name_list, device_descriptor.param_list.param_type_list]
        
        return param_def_map         
     
    def load_device_table(self,filename):
        self.__device_table = {}
      
        counter_list = self.__param_list_info(param_name_list=["start","stop"], param_type_list= ["UINT32", "UINT32"])
        counter_device_info = self.__device_info(type_name="Counter", type=10, param_list=counter_list)
        self.__available_device_types["COUNTER"] = counter_device_info
        
        button_list = self.__param_list_info(param_name_list=["key_index"], param_type_list= ["UINT16"])
        button_device_info = self.__device_info(type_name="Button", type=11, param_list=button_list)
        self.__available_device_types["BUTTON"] =  button_device_info
        
        output_list = self.__param_list_info(param_name_list=["key_index"], param_type_list= ["UINT16"])
        output_device_info = self.__device_info(type_name="Output", type=12, param_list=output_list)
        self.__available_device_types["OUTPUT" ] =  output_device_info
    
        state_machine_list = self.__param_list_info(param_name_list=["number_of_states", "initial_state"], param_type_list= ["UINT8", "UINT8"])
        state_machine_device_info = self.__device_info(type_name="StateMachine", type=15, param_list=state_machine_list)
        self.__available_device_types["STATE_MACHINE" ] = state_machine_device_info    
    
        shutter_list = self.__param_list_info(param_name_list=["time_to_close" ,"time_to_open" ,"default_state"], param_type_list= ["UINT16" ,"UINT16" ,"UINT8"])
        shutter_device_info = self.__device_info(type_name="Shutter", type=30, param_list=shutter_list)
        self.__available_device_types["SHUTTER" ] = shutter_device_info    
    
        #print(self.__available_device_types)
        
    def get_xml_representation(self):
        device_xml_table =  ElementTree.Element("Devices")
        for entry in self.__device_table:
            descriptor = self.__device_table[entry]
            
            if self.__is_system_device(entry) is False:
                
                #element = ElementTree.Element(descriptor.type_name)
                child = ElementTree.SubElement(device_xml_table, descriptor.type_name)
             
                # setting the attributes:
                child.attrib["name"] = entry
                child.attrib["id"] = str(descriptor.id)            
             
                if (descriptor.param_list != None):
                    # setting the parameters:
                    parameter_child   = ElementTree.SubElement(child, "Parameter")
                    for j in range(len(descriptor.param_list[0])):
                        param_identifer = descriptor.param_list[0][j]
                        param_value     = descriptor.param_list[1][j]
                        parameter_child.attrib[param_identifer] = param_value 
            else:
                # SystemDevice
                descriptor.attrib["name"] = entry
                
                if entry == "INTERNALMAPPER":
                    descriptor.attrib["id"] = str(1)
                    
                device_xml_table.append(descriptor)
            #child = ElementTree.SubElement(device_xml_table, element.tag)
             
        #ElementTree.dump(device_xml_table)
        return device_xml_table
    
    def check_parameters(self, param_list, param_list_info):
        param_list_names =   []
        param_list_values =  []
        
        if (param_list == None) & (param_list_info == None):
            return None

        if (param_list == None) & (param_list_info != None):
            raise ParseError("No parameters have been provided - but " + str(len(param_list_info[0])) + " have been expected.")
        
        if (len(param_list) > 0) & (param_list_info == None):
            raise ParseError(str(len(param_list[0])) +"parameters have been provided, but none were expected")

        if (len(param_list[0]) != len(param_list_info[0])):
            raise ParseError("Parameter mismatch: " + str(len(param_list[0])) +" parameters have been provided, but "+str(len(param_list_info[0]))+ " were expected.")
       
        for i in range(len(param_list[0])):
            requested_param_type = param_list_info.param_type_list[i]
            name                 = param_list_info.param_name_list[i]
            value = self.check_parameter_type(param_list[1][i], requested_param_type,param_list[0][i])
            
            param_list_names.append(name)
            param_list_values.append(value)
        
        return [param_list_names, param_list_values]


    def get_device_info(self,device_name):
        
        if self.__is_system_device(device_name):
            return [None, None]
        
        try:
            entry = self.__device_table[device_name]
        except KeyError:
            raise ParseError("Device name " + device_name + " is unknown.")
                
        if entry is None:
            return [None, None]
        
        return (entry.type_name, entry.id)

    def get_number_of_devices(self):
        return len(self.__device_table)

    def get_device_table_entry(self,index):
        
        i = 0
        for elem in self.__device_table:

            if i == index:
                device_config = self.__device_table[elem]
                device_descriptor = self.__available_device_types[device_config.type_name]
                
                return (device_config.type, device_config.id, device_config.param_list[1],device_descriptor.param_list.param_type_list)
            i += 1
            
        raise ParseError("Internal error: Index " + str(index) + " is too big, maximum is " + str(len(self.__device_table)))

          
    def add_device(self,my_new_device_name, my_new_device_type,params):
        #device_descriptor = namedtuple("DeviceDescriptor", "type_name type id param_list")
        # Does this device type exist?
        if my_new_device_name in self.__device_table:
            #found: not so good
            raise ParseError("Device ", my_new_device_name, "already exists.")
        
        if (my_new_device_type in self.__available_device_types):
            new_type = self.__available_device_types[my_new_device_type]
            try:
                my_param_list = self.check_parameters(params,new_type.param_list)
            except ParseError as e:
                raise ParseError(e.get_error_text()+ " Wrong parameter set for " + my_new_device_name + ".")
                    
            self.__device_table[my_new_device_name] = self.__device_descriptor(type_name= my_new_device_type, type = new_type.type, id = self.__current_id, param_list= my_param_list)
            
            self.__current_id += 1            
            return True
        else:
            raise ParseError("Device type '" + my_new_device_type +"' is not known.")

    def add_system_device_in_xml_representation(self, system_device_xml_descriptor):
        
        if self.__is_system_device(system_device_xml_descriptor.tag) is True:
            self.__device_table[system_device_xml_descriptor.tag] =  system_device_xml_descriptor
            return True
        return False
        
    
    
    def print(self):
        print(self.__device_table)
















