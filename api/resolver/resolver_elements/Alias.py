import os
from src.resolver.resolver_elements.ResolverElement import ResolverElement

from src.base.CCAN_Defaults import CCAN_Defaults
from src.base.PlatformConfiguration import PlatformConfiguration
from src.resolver.ResolverError import ResolverError



class AliasResolution(ResolverElement):
    def __init__(self, my_alias_resolution, my_location):                      
        self.__alias_resolution  = my_alias_resolution
        self.__location   = my_location

    def get_location(self):
        return self.__location
    
    def get_resolution(self):
        return self.__alias_resolution
    


class Alias(ResolverElement):
    def __init__(self):
        self.__alias = {}
        self.__add_builtins()
        self.__add_platform_configuration()

    def get_resolver_key(self):
        raise NotImplementedError

    def get_lark_description(self):
        return 'alias_platform_configuration: ("PLATFORM_CONFIGURATION" "[" NAME "]")'

    def get_transformer_method(self):
        return self.transform
        
    def get_resolver_method(self):
         return self.resolve

    def resolve(self,my_key,my_location):
        try:
            return self.__alias[my_key]
        except KeyError:
            raise ResolverError(my_location,"Key <" + my_key + " cannot be resolved.")     


    def add(self,my_key,my_resolution,my_location):
        try:
            self.__alias[my_key]
        except KeyError:             
            raise ResolverError(my_location,"Key <" + my_key + "> has been already defined.")    



    def __add_builtins(self):
        self.__alias["True"]  = AliasResolution(True,"builtin")
        self.__alias["False"] = AliasResolution(False,"builtin")

    def __add_platform_configuration(self):
        platform_configuration = PlatformConfiguration().get()        
        # process recursively:
        self.__add_set_recursively(platform_configuration,'')
        pass
        
    def __add_set_recursively(self,my_set, my_current_key):
        for key in list(my_set.keys()):
             # create "path":    
            full_entry = str(my_current_key) + str(key)

            try:               
                # can we go deeper?
                self.__add_set_recursively(my_set[key],full_entry + "/")
            except AttributeError: 
                # no, then we collect the result, unless it is a list:                        
                if not isinstance(my_set[key],list): 
                    self.__alias[full_entry] = my_set[key]
                