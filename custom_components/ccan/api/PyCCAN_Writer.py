# Interface for PyCCAN Writer: 
class Writer:
    
    app_cookie    = 0x5E95
    engine_cookie = 0xE138 
    
    def __init__(self):
        raise NotImplementedError

    def open(self):
        raise NotImplementedError
    
    def close(self):
        raise NotImplementedError

    def write_comment(self, my_comment):
        raise NotImplementedError
     
    def get_result(self):
        raise NotImplementedError
    
    ########### new API:
    
    def open_config_section(self, config_section_path):
        raise NotImplementedError    
    
    def close_config_section(self):
        raise NotImplementedError  
 
    def open_section(self,section_title):  
        raise NotImplementedError  
    
    def close_section(self):
        raise NotImplementedError        
    
    def open_length_encoded_section(self, section_name, encoding_type):
        raise NotImplementedError        
        
    def close_length_encoded_section(self, my_length_format):
        raise NotImplementedError      
    
    def write_item(self, item_name, item_value, item_format, my_comment):
        raise NotImplementedError          
    
   