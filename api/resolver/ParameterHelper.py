import ipaddress
from enum import Enum
from api.resolver.ResolverElements import ParameterFormat

class ConstraintType(Enum):
    MIN_MAX = 0
    LIST    = 1

class ParameterHelperFactory:

    Helpers = {}  
    Helpers["BOOL"] = ParameterHelper_Bool()

    Helpers["UINT8"] = ParameterHelper_Uint8()
    Helpers["UINT16"] = ParameterHelper_Uint16()
    Helpers["UINT32"] = ParameterHelper_Uint32()
    Helpers["UINT64"] = ParameterHelper_Uint64()

    Helpers["INT8"] = ParameterHelper_Int8()
    Helpers["INT16"] = ParameterHelper_Int16()
    Helpers["INT32"] = ParameterHelper_Int32()
    Helpers["INT64"] = ParameterHelper_Int64()

    Helpers["FLOAT"] = ParameterHelper_Float()

    Helpers["IPV4_ADDRESS"] = ParameterHelper_IP4V_Address()    
    Helpers["CCAN_ADDRESS"] = ParameterHelper_CCAN_Address()
    Helpers["NAME"] = ParameterHelper_Name()
    Helpers["STRING"] = ParameterHelper_String()
    Helpers["DEVICE"] = ParameterHelper_Device()

    def makeParameterHelper(requested_format, location_info):    
        try:
                helper = Helpers(requested_format)                
            except KeyError: 
                raise ResolverError(location_info,"Parameter format <" + requested_format + "> is not supported.")
         return helper 
         
         
class ParameterHelperBase():  
    def __init__(my_constraint_type: ConstraintType, my_constraints:list):
        self.__constraint_type = my_constraint_type
        self.__constraints     = my_constraints

    def set_constraints(my_type: ConstraintType, my_constraints:list)
        self.__constraint_type = my_constraint_type
        self.__constraints     = [ self.__make_comparable(value) for value in my_constraints]
     
    def check_value(my_value):
        self.__internal_type_check(my_value)
        comparable_value = self.__make_comparable(my_value)
        
        if self._constraint_type == ConstraintType.MIN_MAX:
            if self.__internal_compare(my_value, self.__constraints[0]) == -1:
                raise ResolverError(location_info,f"Parameter value {my_value} is smaller than allowed (min value: {self.__constraints[0]}).")
            if self.__internal_compare(my_value, self.__constraints[1]) ==  1:
                raise ResolverError(location_info,f"Parameter value {my_value} is smaller than allowed (min value: {self.__constraints[1]}).")
                
        elif self._constraint_type == ConstraintType.LIST:
            if comparable value not in self.__constraints:
                 raise ResolverError(location_info,f"Parameter value {my_value} is not allowed).")

        else:
            raise ResolverError(location_info,f"Internal Error: Not supported parameter constraint checking type {self.__constraint_type}".")
 
    def __internal_compare(self, my_value, constraint):     
        if value  < constraint:
            return -1
        if value == constraint:
            return 0        
        return 1
        
    
class ParameterHelper_Number(ParameterHelperBase):
    def __init__(my_constraints):
        super.__init__(ConstraintType.MIN_MAX,my_constraints)
                    
    def __internal_type_check(self,my_value):
        if not isinstance(my_value,Number):
            raise ResolverError(location_info,f"Parameter value {my_value} is not a number.")
   
    def self.__make_comparable(my_value):
        return my_value
                
           
   
class ParameterHelper_Uint8(ParameterHelperNumber):
    def __init__():
        super.__init__([0,2**8-1])

class ParameterHelper_Uint16(ParameterHelperNumber):
    def __init__():
        super.__init__([0,2**16-1])    
    
class ParameterHelper_Uint32(ParameterHelperNumber):
    def __init__():
        super.__init__([0,2**32-1])     
    
class ParameterHelper_Uint64(ParameterHelperNumber):
    def __init__():
        super.__init__([0,2**64-1])      
    
class ParameterHelper_Uint8(ParameterHelperNumber):
    def __init__():
        super.__init__([-2**7,2**7-1])

class ParameterHelper_Int16(ParameterHelperNumber):
    def __init__():
        super.__init__([-2**15,2**15-1])    
    
class ParameterHelper_Int32(ParameterHelperNumber):
    def __init__():
        super.__init__([2**31,2**31-1])     
    
class ParameterHelper_Int64(ParameterHelperNumber):
    def __init__():
        super.__init__([-2**63,2**63-1])    
    
class ParameterHelper_CCAN_Address(ParameteHelper_Uint16):

class ParameterHelper_IPV4_Address(ParameteHelperBase):
    def __init__():       
        super.__init__(ConstraintType.MIN_MAX,["0.0.0.1","255.255.255.254")
        
    def __internal_type_check(self,my_value):
        try:
            value = ipaddress.ip_address(my_value)
        except ValueError:       
            raise ResolverError(location_info,f"Parameter value {my_value} is not a valid ip address")
   
    def __make_comparable(my_value):
        return ipaddress.ip_address(my_value))
        
    


class ParameterHelper_Name():

class ParameterHelper_String():

class ParameterHelper_Device():
    @static_method:
    def set_instance_dictionary(my_instance_dictionary):
        ParameterHelper_Device.__instance_dictionary = my_instance_dictionary
        
    
    def __init___