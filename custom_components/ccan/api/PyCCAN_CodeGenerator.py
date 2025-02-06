from cogapp import cogapp as cog
import locale
import pickle
from collections import namedtuple
from pathlib import Path
from datetime import date
import os


class CodeGenerator():
    
    GENERATED_CODE_START = '\n/* start of generated code section - do not modify */\n'
    GENERATED_CODE_END   = '/* end of generated code section - do not modify */\n' 
   
    CCAN_BASE_PATH       = "not defined"
   
    @staticmethod
    def initialize(my_filename):
        CodeGenerator.__descriptors = {} 
        
        try:
            CodeGenerator.CCAN_BASE_PATH = os.environ["CCAN"]
        except KeyError:
            print("Environment variable CCAN is not defined. It is required as it defines the base path for many files!")
            exit(0)
             
        with open(my_filename + '.pkl', 'rb') as f:  
            __description_dictionary = pickle.load(f)

                      

        GenDevice    = namedtuple("GenDevice","name filename_base qualifier qualifier_id class_name factory_name factory_class_name parameter_names parameter_formats attributes variable_names variable_formats event_list pin_list")
        
        # create dataset from descriptors:
        for (qualifier_id,device_descriptor) in __description_dictionary["DEVICE"]:
            if qualifier_id > 0:       
                device_name = device_descriptor.get_name()
                device_qualifier = device_name + "_DEVICE"
                
                
                splitted = device_name.split("_")
                capitalized =''
                for element in splitted:
                    capitalized += element.capitalize()
                class_name = capitalized + "Device"
                
                filename_base =  class_name

                
                (parameter_names, parameter_formats) = device_descriptor.get_description_list("PARAMETER")
                attribute_list                       = device_descriptor.get_description_list("ATTRIBUTES")
                variables_as_list                    = device_descriptor.get_description_list("VARIABLE").get_as_list()
                events_as_list                       = device_descriptor.get_description_list("EVENT").get_as_list()
                pins_as_list                         = device_descriptor.get_description_list("CONNECTION").get_as_list() 
           
                variable_names   = [None]*len(variables_as_list)
                variable_formats = [None]*len(variables_as_list)
                for (var_id,var_name,var_format) in variables_as_list:                    
                    variable_names[var_id]   = var_name.lower()
                    variable_formats[var_id] = var_format


                if "CONTROLLER_SPECIFIC" in attribute_list:
                    suffix ="Base"
                else:
                    suffix =""
                
                #
                gen_device = GenDevice(name            = device_name + ('_' + suffix.upper() if  suffix != '' else ''), 
                                       factory_name    = device_name,
                                       filename_base   = filename_base + suffix,
                                       qualifier       = device_qualifier,
                                       qualifier_id    = qualifier_id,
                                       class_name      = class_name + suffix,
                                       factory_class_name = class_name,
                                       attributes      = attribute_list,
                                       parameter_names = parameter_names,
                                       parameter_formats = parameter_formats,
                                       variable_names  = variable_names,
                                       variable_formats = variable_formats,
                                       event_list       = events_as_list,
                                       pin_list         = pins_as_list
                                       )
                
                CodeGenerator.__descriptors[device_name] = gen_device
        
    # lib/CMakeLists.txt
    
    def __init__(self):
        pass

    @staticmethod
    def process():
        filename_list = []
        
        filename_list.append( CodeGenerator.CCAN_BASE_PATH +"/lib/src/manager/src/DeviceManager.cpp")
        filename_list.append( CodeGenerator.CCAN_BASE_PATH +"/lib/gen/ccan_definitions_gen.h")
        filename_list.append( CodeGenerator.CCAN_BASE_PATH +"/lib/src/devices/include/ccan_device_list.h")
        filename_list.append( CodeGenerator.CCAN_BASE_PATH +"/lib/CMakeLists.txt")
                
        for filename in filename_list:
            args = ['dummy']          
            args.append('-c')
            args.append('-r')
            #args.append('-o')
            #args.append(filename+'.gen')
            args.append(filename)

            # process file
            cog.Cog().main(args)
    
    
        include_template_file = CodeGenerator.CCAN_BASE_PATH +'/lib/src/devices/include/Device_template.h'
        cpp_template_file = CodeGenerator.CCAN_BASE_PATH +'/lib/src/devices/src/Device_template.cpp'
    
        for device_name in CodeGenerator.__descriptors:
            gen_device = CodeGenerator.__descriptors[device_name]
             
            path = CodeGenerator.CCAN_BASE_PATH +"/lib/src/devices/"

            include_file = Path(path +"include/"+gen_device.filename_base + ".h")
            cpp_file     = Path(path + "src/"+gen_device.filename_base + ".cpp")                  
            CodeGenerator.__current_device = gen_device
    
            if not include_file.is_file():                
                
                args = ['dummy']          
                args.append('-c')
                args.append('-d')            
                args.append('-o')
                args.append(str(include_file)) 
                args.append(include_template_file)                 
                
                # create file
                cog.Cog().main(args)
            
            args = ['dummy']          
            args.append('-c')
            args.append('-r')    
            args.append(str(include_file)) 
            cog.Cog().main(args)
            
            
            CodeGenerator.__current_source_filename = str(cpp_template_file)
            CodeGenerator.__current_target_filename = str(cpp_file)
            if not cpp_file.is_file():                    
                args = ['dummy']          
                args.append('-c')
                args.append('-d')            
                args.append('-o')
                args.append(str(cpp_file)) 
                args.append(cpp_template_file)     
                cog.Cog().main(args)
                            
            args = ['dummy']          
            args.append('-c')
            args.append('-r')    
            args.append(str(cpp_file)) 
            cog.Cog().main(args)
                
                
                #print("File " + str(cpp_file) + " does not exist.")
                
    
    # DeviceManager.cpp
    def make_new_device(self):
        output =  CodeGenerator.GENERATED_CODE_START
        for device_name in CodeGenerator.__descriptors:
            gen_device = CodeGenerator.__descriptors[device_name]

            if "CONTROLLER_SPECIFIC" not in gen_device.attributes:       
                output += "case " + str(gen_device.qualifier) + ":\n"
                output += "\tdevice_ptr = new "+ gen_device.factory_class_name +"();\n"
                output += "\tTRACE_PRINTF(\"Created " + str(gen_device.qualifier)  + "\\n\");\n"
                output += "\tbreak;\n\n"                         
        output += CodeGenerator.GENERATED_CODE_END               
        return output
 

    # ccan_definitions_gen.h
    def definitions_make_device_types(self):
        output = CodeGenerator.GENERATED_CODE_START
        for device_name in CodeGenerator.__descriptors:
            gen_device = CodeGenerator.__descriptors[device_name]
            output += gen_device.qualifier + " = " + str(gen_device.qualifier_id) + ",\n"
            
        output += CodeGenerator.GENERATED_CODE_END
        return output   

    # ccan_device_list.h
    def definitions_make_device_include_list(self):
        output = CodeGenerator.GENERATED_CODE_START
        for device_name in CodeGenerator.__descriptors:
            gen_device = CodeGenerator.__descriptors[device_name]
       
            if "CONTROLLER_SPECIFIC" not in gen_device.attributes:
                output += "#include <"  + gen_device.filename_base + ".h>\n"         
            
        output += CodeGenerator.GENERATED_CODE_END
        return output 

    # CMakeLists.txt
    def cmakelists_add_devices(self):       
        target_path = "src/devices/src/"
        
        output =''    
        for device_name in CodeGenerator.__descriptors:
            gen_device = CodeGenerator.__descriptors[device_name]            
            output += target_path + gen_device.filename_base +".cpp\n"
        
        return output     

    # header file
    def header_make_start1(self): 
        gen_device = CodeGenerator.__current_device
        output  = "*  " + gen_device.filename_base + ".h"
        return output
    
    def add_author_and_date(self):  
        locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
        today = date.today().strftime('%d.%m.%Y')

        gen_device = CodeGenerator.__current_device
        output  = " *  Created on " + today +"\n"
        output += " *  Author: Christoph Delfs\n */\n\n"  # getpass, https://stackoverflow.com/questions/842059/is-there-a-portable-way-to-get-the-current-username-in-python
        return output 
    
    def header_add_ifdef(self): 
        gen_device = CodeGenerator.__current_device
        output  = "#ifndef CCAN_LIB_INCLUDE_" + gen_device.name  + "_DEVICE_H_\n"
        output += "#define CCAN_LIB_INCLUDE_" + gen_device.name  + "_DEVICE_H_"
        return output 

    def header_make_class_declaration(self):  # class CounterDevice : public Device       
        gen_device = CodeGenerator.__current_device
        output  = "class " + gen_device.class_name  + " : public Device"     
        return output 
    
    
    def header_make_class_constructor_destructor(self):
        gen_device = CodeGenerator.__current_device
        output   = "\t" + gen_device.class_name+"();\n"   
        output  += "\tvirtual ~" + gen_device.class_name+"();"  
        return output
    
    def header_add_virtual_methods(self):
        output =''
        gen_device = CodeGenerator.__current_device
        if "CONTROLLER_SPECIFIC" in gen_device.attributes:
            output = "virtual void finalize_config(void) = 0;\n"
        return output

    def header_add_standard_methods(self):
        gen_device = CodeGenerator.__current_device
        if "CONTROLLER_SPECIFIC" in gen_device.attributes:
            output=  "\tvoid handle_event( ReadableLocalEvent& my_local_event, Engine& my_engine) = 0;\n"
            output+= "\tvoid handle_TimerMask(const TimerMask my_tick,Engine& my_engine) = 0;"
        else:
            output = "\tvoid handle_event( ReadableLocalEvent& my_local_event, Engine& my_engine);\n"
            output+= "\tvoid handle_TimerMask(const TimerMask my_tick,Engine& my_engine);" 
        return output
    
    def header_cog_make_device_parameters(self):
        
        output  = "/* [[[cog\n"  
        output += "from api.PyCCAN_CodeGenerator import CodeGenerator\n"
        output += "gen = CodeGenerator()\n"
        output += "output = gen.header_make_device_parameters()\n"
        output += "cog.outl(output)\n"
        output += "]]] */\n"
        output += "/* [[[end]]]  */"
        return output
    
    def header_make_device_parameters(self):        
        gen_device = CodeGenerator.__current_device
        output = CodeGenerator.GENERATED_CODE_START
        
        output += "// status parameter: \n"
        for variable_name, variable_format in zip(gen_device.variable_names, gen_device.variable_formats):
            output += self.create_var_declaration("variable_"+ variable_name, variable_format)   
            output += "uint16_t " + "m_variable_" + variable_name + "_id;\n"
                 
        output += "// device parameter:\n"
        for parameter_name, parameter_format in zip(gen_device.parameter_names, gen_device.parameter_formats):
            output += self.create_var_declaration(parameter_name, parameter_format)   
                 
        
        if len(gen_device.pin_list) > 0:
            output += "// driver access:\n"
            output += "Driver* m_driver; \n"
        
            
        output += CodeGenerator.GENERATED_CODE_END
        return output 
     
    def create_var_declaration(self,parameter_name, parameter_format):                               
            if parameter_format == "UINT32":
                decl_string = "uint32_t"
            elif parameter_format == "UINT16":
                decl_string = "uint16_t"
            elif parameter_format == "UINT8":
                decl_string = "uint8_t"                    
            elif parameter_format == "UINT64":
                decl_string = "uint64_t" 
            elif parameter_format == "INT16":
                decl_string = "int16_t"
            elif parameter_format == "INT32":
                decl_string = "int32_t"                
            elif parameter_format == "INT8":
                decl_string = "int8_t"                    
            elif parameter_format == "INT64":
                decl_string = "int64_t" 
            elif parameter_format == "BOOL":
                decl_string = "uint8_t"     # ensure that the size is always 1 Byte
            elif parameter_format == "FLOAT":
                decl_string = "float"   
            elif parameter_format == "STRING":
                decl_string = "char* "                
            elif parameter_format == "IPV4_ADDRESS":
                decl_string = "char* "
            else:
                print("\nError: Unsupported parameter type <" + parameter_format + ">\n.")
                raise ValueError
                
            output = decl_string + " m_" + parameter_name + ";\n"      
            return output
    
    #############################    
        
    def cpp_make_start(self):
        gen_device = CodeGenerator.__current_device
        output  = "*  " + gen_device.filename_base + ".cpp"
        return output        
        
        
    def add_include_header(self): 
        gen_device = CodeGenerator.__current_device
        output  = "\n\n"
        output += "#include <"  + gen_device.filename_base + ".h>\n"
        return output
        


    def cpp_cog_make_event_section(self):            
        output  = "/* [[[cog\n"  
        output += "from api.PyCCAN_CodeGenerator import CodeGenerator\n"
        output += "gen = CodeGenerator()\n"
        output += "output = gen.cpp_make_event_section()\n"
        output += "cog.outl(output)\n"
        output += "]]] */\n"
        output += "/* [[[end]]]  */\n"      
        return output         
        
                
    def cpp_make_event_section(self):           
        gen_device =  CodeGenerator.__current_device
        output = "// Event definitions: \n"
        for (id,name,dummy) in gen_device.event_list:
            output += "const event_id " + gen_device.name + "_" + name + " = " +  str(id) + ";\n"
        return output
        
    def cpp_cog_make_constructor(self):      
        gen_device = CodeGenerator.__current_device    
        output = gen_device.class_name + "::" + gen_device.class_name + "()\n"             
        output += "{\n\n"
        output += "/* [[[cog\n"  
        output += "from api.PyCCAN_CodeGenerator import CodeGenerator\n"
        output += "gen = CodeGenerator()\n"
        output += "output = gen.cpp_make_constructor_start()\n"
        output += "cog.outl(output)\n"
        output += "]]] */\n"
        output += "/* [[[end]]]  */\n"
        output += "}\n"
        return output      
    
    def cpp_make_constructor_start(self): 
        return ""
            
    def cpp_make_destructor(self):        
        gen_device = CodeGenerator.__current_device        
        output = gen_device.class_name + "::~" + gen_device.class_name + "()\n{\n}\n"    
        return output
    
    def cpp_cog_make_set_config(self):     
        gen_device = CodeGenerator.__current_device    
        output  = "void " + gen_device.class_name  + "::set_config(char* &config, Engine& my_engine)\n{\n"

        output += "    /* [[[cog\n"  
        output += "    from api.PyCCAN_CodeGenerator import CodeGenerator\n"
        output += "    gen = CodeGenerator()\n"
        output += "    output = gen.cpp_make_set_config()\n"
        output += "    cog.outl(output)\n "
        output += "    ]]] */\n "
        output += "    /* [[[end]]]  */\n"   
        output += "    return;\n"     
        output += "}"
        
        return output
    
    def cpp_make_set_config(self):
        gen_device = CodeGenerator.__current_device     
        output  = CodeGenerator.GENERATED_CODE_START 
        output += "ConfigurationManager* configuration_manager = my_engine.get_configuration_manager();\n\n"
        output += "// read connection:\n"
        
        
        if len(gen_device.pin_list) > 0:
            (id, pin_name, dummy) = gen_device.pin_list[0]                 
        else:
            output += "// connection information is irrelevant, skipping entry:\n"     
            pin_name = "dummy"            
            
        output += "driver_access " + pin_name + ";\n"     
        output += "configuration_manager->read_parameter((char*)&"+ pin_name + ", sizeof(" + pin_name + "));\n"
        if pin_name != "dummy":
            output += "// m_driver provides access to sensor data:\n"
            output += "m_driver = my_engine.get_driver_access(" + pin_name + ");\n\n"
        else: 
            output +"\n"
        
        
        output += "// read state variable id:\n"     
        for variable_name in gen_device.variable_names:
            variable_id_name = "m_variable_" + variable_name + "_id"
            output += "configuration_manager->read_parameter((char*) &" + variable_id_name+",sizeof("+ variable_id_name + "));\n"           
                 
        output += "\n// read device parameter:\n"
        for parameter_name, parameter_format in zip(gen_device.parameter_names, gen_device.parameter_formats):                 
            output += self.__create_read_parameter("m_" + parameter_name, parameter_format)
            
        if "CONTROLLER_SPECIFIC" in gen_device.attributes:
            output+= "finalize_config();\n"

        output += CodeGenerator.GENERATED_CODE_END
        return output
  
    def add_void_class_method(self,method_name):
        output=''
        gen_device = CodeGenerator.__current_device     
        if "CONTROLLER_SPECIFIC" not in gen_device.attributes:
            gen_device = CodeGenerator.__current_device
            output = "void " + gen_device.class_name + method_name 
            output+="\n{\n}\n"
        return output
    
    def __create_read_parameter(self,parameter_name,parameter_format):
        if parameter_format in ["STRING", "IPV4_ADDRESS"]:
                output = "configuration_manager->read_string_parameter(" + parameter_name + ");\n" 
                #output  = parameter_name + " = config;\n"
                #output += "while (config != 0) config++;\n"
        else:
                output = "configuration_manager->read_parameter((char*) &" + parameter_name+", sizeof("+ parameter_name + "));\n"
        return output
    
    