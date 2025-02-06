from collections import namedtuple

class CompilerValues():

    def __init__(self):
                
        GeneratorItem = namedtuple("GeneratorItem","table encoding")
            
        EncodingKey = {} 
        EncodingKey["BOOL"]   = 1
        EncodingKey["UINT8"]  = 1
        EncodingKey["UINT16"] = 2
        EncodingKey["UINT32"] = 4
        EncodingKey["UINT64"] = 8
        EncodingKey["FLOAT"]  = 4    
        
        EncodingKey["CCAN_ADDRESS"]  = 2
        EncodingKey["IPV4_ADDRESS"]  = 4
        EncodingKey["CONNECTION"] = 4
        
        
        #################################################
        
        self.__generator_tables = {}
        
    def add_mapping_table(self,name, my_table, my_encoding):
        try:
            dummy = self.__generator_tables[my_table]
        except KeyError:         
            dummy = CompilerValues.EncodingKey[my_encoding]            
            self.__generator_tables[name] = CompilerValues.GeneratorItem(table = my_table, encoding = my_encoding)
    
        raise KeyError
        
    def get_table_iterator(self):
        raise NotImplementedError
                    
    def get_encoding_for_table(self, my_table):
        return [ self.__generator_tables[my_table].encoding,  CompilerValues.EncodingKey[self.__generator_tables[my_table].encoding]]
        
    def map_string_to_value(self,item,entry):
        return self.__config_sections
        