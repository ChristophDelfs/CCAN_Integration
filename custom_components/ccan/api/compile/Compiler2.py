import os
from lark import exceptions

from api.ConfigurationValidator import ConfigurationValidator

from api.compile.Parser import TransformingParser
from api.resolver.ParameterStore import ParameterStore
from api.resolver.ResolverError import ResolverError   
from api.resolver.Resolver import Resolver
from api.resolver.Definitions import BinaryConfig
from api.resolver.Definitions import LocationInfo

from api.base.PlatformConfiguration import PlatformConfiguration

from   api.compile.ControllerStore import ControllerStore
import api.compile.CompilerHelper as CompilerHelper

from api.base.CCAN_Defaults import CCAN_Defaults
from api.PyCCAN_Warnings import CCAN_Warnings

class Compiler:
#    _store = Store()
    
    def __init__(self):

        self.__text = None
        self.__config_file =""
        self.__compiled = False
        self.__basename = None
        self.__resolver  = Resolver()

    def save(self,output_path):
        self.__resolver.resolver_store.save(output_path+"/" + self.__basename)

      
        pf = PlatformConfiguration()
        pf.load()
        self._platform_configuration = pf.get()

    def get_resolver(self):
        return self.__resolver

    def write_controller_stores(self,my_writer):
        return_list = []
        self.__load_defaults() 
        exit(0)

        controller_map = ControllerStore.get_controller_map()
        for controller_name in controller_map:
            # Engine Config
            controller_store = controller_map[controller_name]
            
            # identify controller:
            controller_type  = controller_store.get_controller_type()
            try:
                print(controller_type)
                crc = self.__ccan_defaults.get_default_attribute("CONTROLLER_CRC_LIST",controller_type+"_CONFIGURATION")
            except KeyError:
                print("Internal Error: CRC key for configuration not found..")
                exit(0)

            # write engine config:
            print("Controller : " + controller_name)
            controller_store.write_config(my_writer, crc)
            engine_config = BinaryConfig(controller_name = controller_name, type="ENGINE_CONFIG", binary_config =my_writer.get_result(), controller_crc = crc)
            return_list.append(engine_config)           
        return return_list


    def create_header_file(self,binary_sequence, my_var_name = "default_configuration"):
        text_output = "/** GENERATED  - do not modify **/\n"
        text_output += "const uint32_t " + my_var_name + "_len = " + str(len(binary_sequence)) + ";\n"
        text_output += "static constexpr char " + my_var_name + "[]   = { "
        i = 0
        j = 0
        for element in binary_sequence:
            text_output += hex(element)
            i += 1
            j += 1
            if i < len(binary_sequence):
                text_output += ", "
            if j == 16:
                text_output +="\n"
                j = 0

        text_output +=" };"
        return text_output


    def create_bootloader_header_file(self,segments, sequence, my_var_name):
        text_output = "/** GENERATED  - do not modify **/\n"
        text_output = "namespace updater {\n"
        text_output += "static constexpr uint8_t number_of_segments = " + str(len(segments)) + ";\n"

        text_segment_start = "static constexpr uint32_t segment_start[] = { " 
        text_segment_end   = "static constexpr uint32_t segment_stop[]   = { "
        for segment in segments:
            if segment == segments[-1]:
                adder = "}; \n"
            else:
                adder = ", "
            text_segment_start += str(segment[0]) + adder
            text_segment_end   += str(segment[1]) + adder
        text_output += text_segment_start + text_segment_end

        text_output += "static constexpr char " + my_var_name + "[]   = { \n"        
        i = j = 0

        padding =  4
   
        for element in sequence:                                  
            text_output += f"{element:#0{padding}x}" #hex(element)          
            i += 1
            j += 1            
            if i < len(sequence):
                text_output += ", "
            if j == 16:
                text_output +="\n"
                j = 0                      
        text_output +=" };\n" 
        text_output +="}; // end namespace"
        return text_output

    def do(self,filename,extra_include_path):
         # strip the ending if supplied:
        if filename.endswith(".ccan"):           
            filename = filename[:-5]

        self.__compiled = False
            
        self.__basename = str(os.path.basename(filename))
        parser = TransformingParser()

        include_path_list = CompilerHelper.include_path_defaults()

        include_path_list.extend(extra_include_path)
        include_path_list.extend([str(os.path.dirname(filename))])
       
        try:
            result = parser.parse(filename,include_path_list)
        except exceptions.UnexpectedCharacters as e: 
            location = LocationInfo(filename+".ccan",e.line, e.column)              
            #print(filename + ": " +str(e.line)+":" +str(e.column) + " Syntax error")
            raise ResolverError(location,"Syntax error detected. Found unexpected character: '" + e.char + "'.")       
     
        except Exception as e:   
            pass                  
            raise e.orig_exc
        

        if result is None:
            return

        prefix = ''
        parameter_store = ParameterStore()
        self.__resolver.do(result,prefix,parameter_store,include_path_list)
        print("resolving completed")      

        self.__compiled = True
        
        try:
            ConfigurationValidator.do(self.__resolver)
        except ResolverError as e:
            location = e.get_location()
            print(self.__get_file_context(location.file,location.line))
            print(location.file + ":" +str(location.line)+":" +str(location.column) + " >> " + e.get_error_text())
            return False

        CCAN_Warnings.show_all()
        
        # version check, currently disabled:
        # ConfigurationManager(self.__resolver.resolver_store.get_description_dictionary())

        return True
        # separate into ControllerStores:
        ControllerStore.create_controller_stores(self.__resolver)
        
        return True
    


    # load config file
    def load_file(self,config_file):
        self.__config_file = config_file
    #config_file = "../config/config.txt"
        text_file = open(config_file+".txt", "r")
        self.__text = text_file.read()
        self.__compiled = False


    def __load_defaults(self):
        filename = os.path.join(os.environ["CCAN"],"gen","ccan_generated_definitions")
        self.__ccan_defaults = CCAN_Defaults()
        self.__ccan_defaults.init_from_pkl(filename)        

