from .ResolvedBase import ResolvedBase
from .InstanceDescriptionType import InstanceDescriptionType

class ResolvedDescriptionBase(ResolvedBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)
        # self.__parameter_name_list = None
        # self.__parameter_format_list = []
        self.__description_list = {}

    #    def set_parameter_definition(self,my_param_name_list, my_param_format_list):
    #        self.__parameter_name_list = my_param_name_list
    #
    #        for format in my_param_format_list:
    #            try:
    #                self.__parameter_format_list.append(ParameterFormat(format))
    #            except KeyError:
    #                raise ResolverError(self.__location_info,"Parameter format <" + format + "> is not supported.")

    #    def get_parameter_definition(self):
    #        return (self.__parameter_name_list,  self.__parameter_format_list)

    def insert_description_list(self, my_description_type, my_list):
        # should never lead to a KeyError (would be an internal Compiler error)
        test = InstanceDescriptionType(my_description_type)
        self.__description_list[my_description_type] = my_list

    def insert_checked_description_list(
        self, my_description_type, my_list, checking_function
    ):
        checking_function(my_list, super().get_location())
        self.insert_description_list(my_description_type, my_list)

    def get_description_list(self, my_description_type):
        return self.__description_list[my_description_type]