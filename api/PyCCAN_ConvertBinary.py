import struct

class SequenceExtractor():
    def __init__(self, my_binary_sequence):
        self.__seq = my_binary_sequence

    def get_sequence(self):
        return self.__seq

    def __shorten_seq_by(self,num):
        self.__seq = self.__seq[num:]

    def convertback_char(self):
        return chr(self.convertback8())

    def convertback_string(self):      
        string = self.__seq[0: self.__seq.index(0)]       
        self.__shorten_seq_by(len(string)+1)
        return ''.join(chr(i) for i in string)      
    
    def convertback_float(self):
        result  = struct.unpack('f',bytes(self.__seq[0:4]))[0]
        self.__shorten_seq_by(4)
        return result
 
    def convertback64(self):        
        result_l32 = self.convertback32() 
        result_h32 = self.convertback32()  
        result  = result_h32*256*256*256*256 + result_l32 
        return result
   
    def convertback32(self):
        result_l16 = self.convertback16() 
        result_h16 = self.convertback16() 
        result = result_h16*256*256 + result_l16
        return result
    
    def convertback16(self):
        result_l8 = self.convertback8() 
        result_h8 = self.convertback8() 
        result = result_h8*256 + result_l8        
        return result

    def convertback8(self):
        try:
            result  = self.__seq[0]
        except IndexError:
            print("Internal error in event processing!")
            raise IndexError
        self.__shorten_seq_by(1)
        return result
    
    def is_empty(self):
        return len(self.__seq) == 0
    
    def convertback_bool(self):
        value = self.convertback8()
        result = False      
        if value > 0:
            result = True
        return result
    
    def __eq__(self,my_sequence):
        return set(self.__seq) == set(my_sequence.__seq)
    
class SequenceCreator():
    #def __init__(self):
    #    self.__seq = []

    def __init__(self, my_sequence = None):
        if my_sequence is None:
            self.__seq = []
        else:
            self.__seq = my_sequence


    def append(self,my_binary_sequence):
        self.__seq.extend(my_binary_sequence)

    def get_sequence(self):
        return self.__seq

    def convert_float(self,my_value):
        result = bytearray(struct.pack("f", float(my_value)))  
        self.__seq.extend(result)
        return result  

    def convert64(self,my_value):     
        value = int(my_value)
        result = [value & 255, (value >> 8) & 255, (value >> 16)&255, (value >> 24)&255, (value >> 32)&255, (value >> 40)&255, (value >> 48)&255, (value >> 56)&255  ] # little endian
        self.__seq.extend(result)
        return result

    def convert32(self,my_value):
        value = int(my_value)
        if value < 0:
            raise ValueError
        result = [value & 255, (value >> 8) & 255, (value >> 16)&255, value >> 24 ] # little endian
        self.__seq.extend(result)
        return result

    def convert16(self,my_value):                 
        value = int(my_value)
        if value < 0:
            raise ValueError
        result = [value & 255, value >> 8 ] # little endian
        self.__seq.extend(result)
        return result

    def convert8(self,my_value):
        value = int(my_value)
        if value < 0:
            raise ValueError        
        result = [value & 255] 
        self.__seq.extend(result)
        return result       
    
    def convert_char(self,value):
        self.__seq.extend(ord(value))
        return ord(value)
    
    def convert_string(self,value):
        result = [ord(c) for c in value]
        result.extend([0])
        self.__seq.extend(result)
        return result             
    
    def convert_bool(self,value):
        if isinstance(value,str):
            test_str = value.upper()
            if test_str == "FALSE":
                result =  [0]
            elif test_str == "TRUE":
                result =  [1]                
            else:
                raise AttributeError
        else:
            if value is True:
                result = [1]
            elif value is False:
                result = [0]
            else:
                raise AttributeError
        
        self.__seq.extend(result)
        return result 
        