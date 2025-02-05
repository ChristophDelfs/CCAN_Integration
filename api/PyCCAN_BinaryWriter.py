
from src.PyCCAN_Writer import Writer
import typing
import binascii
import socket
import struct
from numbers import Number
 
class BinaryWriter (Writer):
    
    def __init__(self):
        self.__output = None
        
        self.__binary_sequences = None
        self.__current_sequence = None

    def open(self):
        self.__output = []       
        
        # clear result
        self.__binary_sequences = []      
        self.__current_sequence = []                  
        
    def close(self):
        pass
                                           
    def open_section(self,title):
        # section title is ignored in binary writer
        pass
    
    def close_section(self):
        pass
    
    def write_cookie(self):
        cookie = Writer.engine_cookie
        # create first bytes of level 0 sequence:
        self.__current_sequence.extend(self._convert16(cookie))           
    
    def open_configuration_section(self, my_configuration_section_path,dummy):
        self.__current_sequence.extend(self._convert8(dummy))   
        self.open_length_encoded_section(my_configuration_section_path)
        
    def close_configuration_section(self):
        self.close_length_encoded_section("UINT16")
            
    def open_length_encoded_section(self, section_name):
        # start a new sequence, add it to the sequence stack:
        self.__binary_sequences.append(self.__current_sequence)
        self.__current_sequence = []

    def close_length_encoded_section(self, my_length_format):       
        
        # determine and encode length information:
        length = len( self.__current_sequence)        
        length_format = str(my_length_format)
        trailer = self.__convert_parameter_to_seq(length,length_format)
        
        # get previous sequence and add length informaition plus current sequence
        parent_sequence = self.__binary_sequences.pop()
        parent_sequence.extend(trailer)
        parent_sequence.extend(self.__current_sequence)
        
        # continue with enlarged previous sequence:
        self.__current_sequence = parent_sequence
        
        # add child sequence to parent sequence with leading length information:
        #self.__binary_sequences.extend(parent_sequence)
        
    def write_comment(self, my_comment):
        pass
        
    def write_item(self, item_name, item_value, item_format, my_comment = None):      
  
        self.__current_sequence.extend(self.__convert_parameter_to_seq(item_value,str(item_format)))
    
    def close(self):
        if len(self.__binary_sequences) > 0:
            print("You have opened " + str(len(self.__binary_sequences)) + " more length coded sections than you have closed.")
            raise OverflowError
               
    def get_result(self):
        try:
            return bytes(self.__current_sequence) 
        except ValueError:
            pass
    
    #def print_result(self):
    #    for val,i in zip(self.__current_sequence,range(len(self.__current_sequence))):
    #        print(''.join('{:02x}'.format(val))+" ",end='')
    #        if (i+1) % 8 == 0:
    #            print("")
    #            
    #    print("\nNumber of Bytes: " + str(len(self.__current_sequence)))  
    
    ###################################################
    
    
    def _convert_string(self,value):
        result = bytes(value,'UTF-8')+bytes(1)
        return result
               
    def _convert64(self,value):
        lower32 = value   & (2**32-1)
        upper32 = value >> 32
        result = self._convert32(lower32) 
        upper_result = self._convert32(upper32)
        result.extend(upper_result)
        return result

    def _convert32(self,value):    
        if value == -1:
            value = 2**32-1            
        lower16 = value   & (2**16-1)
        upper16 = value >> 16
        result = self._convert16(lower16) 
        upper_result = self._convert16(upper16)
        result.extend(upper_result)
        return result

    def _convert16(self,value):
        if value == -1:
            value = 2**16-1
        if value > 65535 or value < 0:
            raise OverflowError
        result = [value & 255, value >> 8 ] # little endian
        return result

    def _convert_signed16(self,value):       
        if value > 32767 or value < -32768:
            raise OverflowError
        return self._convert16(value+32768)

    def _convert8(self,value):
        if value == -1:
            value = 2**8-1
        if value > 255 or value < 0:
            raise OverflowError
        result = [value & 255] # little endian
        return result 
              
    def _convert_signed8(self,value):   
        if value > 127 or value < -128:
            raise OverflowError
        
        return self._convert8(value+128)



    ##############################################################################   
    
    def __convert_parameter_to_seq(self,my_values, my_type):
        seq = []
        if not isinstance(my_values,typing.List):
            my_list = [ my_values ]
        else:
            my_list = my_values
            
        for value in my_list:            
            if my_type == "INT8": 
                try:
                    seq.extend(self._convert8(int(value)))
                except ValueError:
                    pass
            elif my_type == "INT16":
                seq.extend(self._convert16(int(value)))
            elif my_type == "INT32":
                seq.extend(self._convert32(int(value)))
            elif   my_type == "INT64": 
                seq.extend(self._convert32(int(value)))
            elif   my_type == "UINT8": 
                seq.extend(self._convert8(int(value)))
            elif my_type == "UINT16":
                seq.extend(self._convert16(int(value)))
            elif my_type == "UINT32":                
                seq.extend(self._convert32(int(value)))
            elif my_type == "UINT64":
                seq.extend(self._convert64(int(value)))                                 
            elif my_type == "FLOAT":  
                 binarized = struct.pack('>f',value)                   
                 seq.extend(self._convert32(struct.unpack('>L',binarized)[0]))

            elif my_type == "BOOL":
                seq.extend(self._convert8(int(value)))                 
            elif my_type == "CCAN_ADDRESS":
                seq.extend(self._convert16(int(value)))                            
            elif my_type == "NAME":
                seq.extend(self._convert_string(value))                            
            elif my_type == "STRING":
                seq.extend(self._convert_string(value))                            
            elif my_type == "IPV4_ADDRESS":
                seq.extend((self._convert_string(value)))
            else:
                print("Internal Error - not supported type: "  + my_type)
                raise TypeError
        return seq            
    
  