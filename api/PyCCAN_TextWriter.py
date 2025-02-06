# Interface for PyCCAN Writer:
from api.PyCCAN_Writer import Writer
from api.resolver.Definitions import TextWriterOutput,TextWriterDevice, TextParameterSet,TextMappingDescriptor , TextEventDescriptor,TextMappingRuleDescriptor
from api.resolver.ResolverElements import ParameterFormat
import pprint
from io import StringIO
#from PyCCAN_Resolver import Resolved_Expression
 
class TextWriter (Writer):
    
    def __init__(self):
        self.__stacked_output = None
        self.__output = None
        self.__level  = None
        
     
    def __add_to_output(self, arg):
        tab = ''
        for i in range(self.__section_indent_counter):
            tab +='\t'
        self.__output = '\n'.join([self.__output, tab+arg])
       
     
    def open(self):
        self.__stacked_output = []
        self.__named_section  = []
        self.__output  = ''
        self.__section_indent_counter = 0
        
        self.__add_to_output ("-- CCAN TEXT Writer Output --")
        #r = 4

    def close(self):
        self.__add_to_output ("-- CCAN TEXT Writer Output END --")
     
    def write_cookie(self):
        cookie = Writer.engine_cookie
        # create first bytes of level 0 sequence:
        self.write_item("MAGIC COOKIE",cookie, ParameterFormat("UINT16"), None)
     
    def write_comment(self, my_comment):
        self.__add_to_output("# " + my_comment)
             
    def open_section(self,title):
        #self.__section_indent_counter += 1
        self.__add_to_output(title)   
        self.__section_indent_counter += 1
    
    def close_section(self):
         self.__section_indent_counter -= 1
         if self.__section_indent_counter < 0:
             print("You have closed " + str(-self.__section_indent_counter) + " more sections than you have opened")
             raise OverflowError
    
    def open_configuration_section(self, my_configuration_section_path, dummy):
        #self.print("START OF CONFIGURATION SECTION:")
        self.write_item("CONFIGURATION_SECTION: " + my_configuration_section_path, dummy, ParameterFormat("UINT8"), None)
        self.open_length_encoded_section(my_configuration_section_path)
    
    def close_configuration_section(self):
        self.close_length_encoded_section(ParameterFormat("UINT16"))
    
    def open_length_encoded_section(self, section_name):       
        self.__named_section.append(section_name)
        self.__stacked_output.append(self.__output)
        self.__output =''
        self.__section_indent_counter += 1          
        #self.__open_length_encoded_section()
        #self.__add_to_output("START_OF_LENGTH_ENCODED_SECTION:" + section_name)
       
    #def __open_length_encoded_section(self):
       
        
    def close_length_encoded_section(self, my_format):      
        section_name    = self.__named_section.pop()       
        previous_output = self.__stacked_output.pop()        
        tab = ''
        for i in range(self.__section_indent_counter):
            tab +='\t'
        
        self.__output = '\n'.join([previous_output, tab + "START_OF_LENGTH_ENCODED_SECTION: " + section_name + " [Format: " + str(my_format) + "]" +  self.__output])
        self.__add_to_output("END_OF_LENGTH_ENCODED_SECTION")
        
        self.__section_indent_counter -= 1
    
    def write_item(self, my_name, my_value, my_format, my_comment = None):
        printed_value = my_name + " = " + str(my_value) + "    [Format : " + str(my_format) + "]" 
        if my_comment is not None:
            printed_value +=  "  // "+ my_comment  
        self.__add_to_output(printed_value)

    
    def get_result(self):
        return self.__output
       
       
    def print(self,node,filename):
        with open(filename, 'wt') as output:
            output.writelines(node)# ('\n'.join(node))        
        
