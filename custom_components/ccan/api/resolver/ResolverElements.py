import hashlib
import pickle
from .ResolverError import ResolverError


from .resolver_elements.ResolvedBase import ResolvedBase
from .resolver_elements.ResolvedDictionaryBase import ResolvedDictionaryBase
from .resolver_elements.KeyMapBase import KeyMapBase

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


class ResolvedOfferedConnectionBase(ResolvedBase):
    def __init__(self, my_name, my_connection_list, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__connection_list = my_connection_list


##########################################################################################


# class ResolvedGeneralDescriptionDictionary(ResolvedDictionaryBase):
#    def __init__(self):
#        super().__init__(DescriptionType.get_map())


class ResolvedSensorDriverDescriptionDictionary(ResolvedDictionaryBase):
    def __init__(self):
        self.__sensor_classes_map = {}
        self.__sensor_classes_map["BINARY_INPUT"] = 0
        self.__sensor_classes_map["MOTION"] = 1
        self.__sensor_classes_map["TEMPERATURE"] = 2
        self.__sensor_classes_map["BRIGHTNESS"] = 3
        self.__sensor_classes_map["WIND"] = 4
        self.__sensor_classes_map["TIME"] = 5
        self.__sensor_classes_map["BINARY_OUTPUT"] = 6
        self.__sensor_classes_map["BINARY_INPUT_OUTPUT"] = 7
        self.__sensor_classes_map["VOLTAGE"] = 8
        super().__init__(self.__sensor_classes_map)


class ResolvedCommunicationDriverDescriptionDictionary(ResolvedDictionaryBase):
    def __init__(self):
        self.__communication_classes_map = {}
        self.__communication_classes_map["CAN_DRIVER"] = 0
        self.__communication_classes_map["ETHERNET_DRIVER"] = 1
        self.__communication_classes_map["I2C_DRIVER"] = 2
        super().__init__(self.__communication_classes_map)


class ResolvedTransportAdapterDescriptionDictionary(ResolvedDictionaryBase):
    def __init__(self):
        super().__init__(ProtocolType().get_map())


class ResolvedAdditionalProtocolDescriptionDictionary(
    ResolvedTransportAdapterDescriptionDictionary
):
    pass


####################################################################
#
#
#
#  DescriptionSets
#
#
####################################################################


class ResolvedDescription(ResolvedDescriptionBase):
    def __init__(self, my_name, my_type, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__type = my_type

    def get_type(self):
        return self.__type

    def is_type(self, my_type):
        return my_type == self.__type


class ResolvedEventDescription(ResolvedDescriptionBase):
    def __init__(self, my_name, my_direction, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__direction = EventDirectionType(my_direction)

    def has_direction(self, my_direction):
        return self.__direction.get_key() == EventDirectionType(my_direction).get_key()


class ResolvedDeviceDescription(ResolvedDescription):
    pass


class ResolvedAppDescription(ResolvedDescription):
    pass


class ResolvedDeviceDescriptionDictionary(ResolvedDictionaryBase):
    def __init__(self):
        self.__device_classes_map = {}
        self.__device_classes_map["DEVICE"] = 1
        self.__device_classes_map["TEMPLATE"] = 2
        self.__device_classes_map["HOME_ASSISTANT_DEVICE"] = 3
        super().__init__(self.__device_classes_map, 20)

    def insert(self, my_new_entry, my_device_id=None):
        forbidden_names = ProtocolType().get_list_of_types()
        if my_new_entry.get_name() in forbidden_names:
            raise ResolverError(
                my_new_entry.get_location(),
                "The device type name "
                + my_new_entry.get_name()
                + " is reserved not allowed. Reserved names are "
                + str(forbidden_names)
                + ".",
            )
        return super().insert(my_new_entry, my_device_id)


class ResolvedAppDescriptionDictionary(ResolvedDictionaryBase):
    def __init__(self):
        self.__app_classes_map = {}
        self.__app_classes_map["CONTROLLER"] = 0
        self.__app_classes_map["APP"] = 1
        super().__init__(self.__app_classes_map)


class ResolvedAdditionalProtocolsDictionary(ResolvedDictionaryBase):
    def __init__(self, my_start_id=0):
        protocol_map = {}
        protocols = ProtocolType("CCAN").get_list_of_types()
        for protocol, i in zip(protocols, range(len(protocols))):
            protocol_map[protocol] = i
        super().__init__(protocol_map, my_start_id)


##################################################################
#
#
#  Instance Dictionaries
#
##################################################################


class ResolvedInstanceDictionaryBase(ResolvedDictionaryBase):
    def __init__(
        self,
        my_type_dictionary,
        my_start_id=0,
        my_global_id=True,
        my_get_local_id_method=None,
    ):
        if my_type_dictionary is not None:
            class_map = my_type_dictionary.get_type_map()
            super().__init__(class_map, my_start_id)
        else:
            super().__init__(None, my_start_id)

        self.__global_id = my_global_id
        self.__get_next_local_id_method = my_get_local_id_method

    def insert(self, my_new_instance, my_target_id=None):
        (name, id) = super().insert(my_new_instance, my_target_id)

        if self.__global_id == True:
            my_new_instance.set_id(id)
            return (name, id)

        # define local id
        local_id = self.__get_next_local_id_method(name)
        my_new_instance.set_id(local_id)

        return (name, local_id)

    def prepare_pickle(self):
        self.__get_next_local_id_method = None


##########################################
#
#
#
#
#
#
##########################################


class ResolvedMap:
    def __init__(self, my_type):
        self.__type = InstanceDescriptionType(my_type)
        self.__id = 0
        self.__map = {}
        self.__iter_count = 0

    def insert_and_replace(self, my_name, my_list, location_info):
        try:
            (id, old_list) = self.__map[my_name]
            self.__map[my_name] = (id, my_list)
        except KeyError:
            self.__map[my_name] = (self.__id, my_list)
            self.__id += 1

    def insert(self, my_name, my_list, location_info):
        try:
            test = self.__map[my_name]
            raise ResolverError(
                location_info, "Element " + my_name + " is already defined."
            )
        except KeyError:
            self.__map[my_name] = (self.__id, my_list)
            self.__id += 1

    def get_by_name(self, my_name):
        (my_id, my_list) = self.__map[my_name]
        return my_list
    

    def get_entry_by_id(self, my_id):
        for name in self.__map:
            (id, my_event) = self.__map[name]
            if id == my_id:
                return my_event
        return None

    def get_id_by_name(self, my_name):
        (id, my_list) = self.__map[my_name]
        return id

    def get_names_as_list(self):
        return list(self.__map.keys())

    def get_as_list(self):
        l = []
        for e in self.__map.keys():
            element = (self.__map[e][0], e, self.__map[e][1])
            l.append(element)
        return l

    # make it iterable:
    def __iter__(self):
        self.__iter_count = 0
        self.__iter_list = list(self.__map.keys())
        return self

    def __next__(self):
        if self.__iter_count < self.__id:
            result = self.__iter_list[self.__iter_count]
            self.__iter_count += 1
            return result

        else:
            raise StopIteration

    # only for debugging:
    def keys(self):
        return print(self.__map.keys())


class ResolvedParameterDescriptionMap(ResolvedMap):
    def __init__(self, my_type):
        super().__init__(my_type)

    def insert(self, my_name, my_format, location_info):
        try:
            format = ParameterFormat(my_format)
        except KeyError:
            raise ResolverError(
                location_info, "Parameter format " + my_format + " is not supported."
            )
        super().insert(my_name, my_format, location_info)


class ResolvedCheckedMap(ResolvedMap):
    def __init__(self, my_type, my_dictionary):
        super().__init__(my_type)
        self.__type = InstanceDescriptionType(my_type)
        self.__dictionary = my_dictionary

    def insert(self, my_name, my_list, location_info):
        # check whether the list contains allowed entries (entries must exist in dictionary)
        for element in my_list:
            try:
                test = self.__dictionary.get_by_name(element)
                if test is None:
                    raise ResolverError(
                        location_info,
                        element + " is not defined as " + str(self.__type),
                    )
            except KeyError:
                raise ResolverError(
                    location_info, element + " is unknown. Please check your typing."
                )
        super().insert(my_name, my_list, location_info)


####################################################################
#
#
#
#   Instances
#
#
#
####################################################################


class ResolvedInstanceBase(ResolvedBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__type = None
        self.__description_list = {}
        self.__type_key = None
        self.__id = None

    def set_type(self, my_type, my_type_key):
        self.__type_key = my_type_key
        self.__type = my_type

    def set_id(self, my_id):
        self.__id = my_id

    def get_type_key(self):
        return self.__type_key

    def get_type(self):
        return self.__type

    def get_id(self):
        return self.__id

    def get_id_set(self):
        id_parameter = ResolvedParameter(
            "ID_SET",
            (self.__type_key) + (self.__id << 16),
            ParameterFormat("UINT32"),
            super().get_location(),
        )
        return [id_parameter]

    def insert_description_list(self, my_description_type, my_list):
        self.__description_list[my_description_type] = my_list

    def get_description_list(self, my_description_type):
        if my_description_type == "ID":
            return self.get_id_set()

        try:
            result = self.__description_list[my_description_type]
        except KeyError:
            result = []
        return result


class ResolvedProtocolInstance(ResolvedInstanceBase):
    def set_protocol_map(self, my_map):
        self.__protocol_map = my_map

    def get_protocol_map(self):
        return self.__protocol_map


class ResolvedHomeAssistantDeviceInstance(ResolvedInstanceBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)

    def get_status_variable_ref_list(self):
        raise NotImplementedError
        
class ResolvedDeviceInstance(ResolvedInstanceBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__connection_list = None
        self.__is_template = False

    # def set_connection_list(self,my_connection_list):
    #    self.__connection_list = my_connection_list

    # def get_connection_list(self):
    #    return self.__connection_list
    def mark_as_template(self):
        self.__is_template = True

    def is_template(self):
        return self.__is_template

    def get_status_variable_ref_list(self):
        raise NotImplementedError


class ResolvedAppInstance(ResolvedInstanceBase):
    def __init__(self, my_name, my_location_info):
        self.__controller_name = my_name
        self.__next_free_local_id = 1
        super().__init__(my_name, my_location_info)

    def set_controller_name(self, my_controller_name):
        self.__controller_name = my_controller_name

    def is_app(self):
        return self.__controller_name != self.get_name()

    def is_controller(self):
        return self.__controller_name == self.get_name()

    def get_controller_name(self):
        return self.__controller_name

    def get_new_local_id(self):
        new_local_id = self.__next_free_local_id
        self.__next_free_local_id += 1
        return new_local_id

#
#
#
#


class ResolvedUsedDriverInstance(ResolvedInstanceBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__has_been_used = False

    def has_just_been_used(self):
        self.__has_been_used = True

    def is_not_used(self):
        return not self.__has_been_used


class ResolvedEventInstance(ResolvedInstanceBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__is_alias = False
        self.__is_template = False
        self.__controller_name = None

    def set_controller_name(self, my_controller_name):
        self.__controller_name = my_controller_name

    def get_controller_name(self):
        return self.__controller_name

    def set_alias_flag(self, my_alias_flag):
        self.__is_alias = my_alias_flag

    def is_alias(self):
        return self.__is_alias
    
    def set_template_flag(self, my_template_flag):
        self.__is_template = my_template_flag

    def is_template(self):
        return self.__is_template

    def set_direction(self, my_direction):
         self.__direction = EventDirectionType(my_direction)

    def get_direction(self):
        return str(self.__direction)

    #def __eq__(self, other, *attributes):
    #    if not isinstance(other, type(self)):
    #        return False
    #    
    #    if attributes:
    #        d = float('NaN')  # default that won't compare equal, even with itself
    #        return all(self.__dict__.get(a, d) == other.__dict__.get(a, d) for a in attributes)
    #    
    #    return self.__dict__ == other.__dict__

    ########################################################
    ### functions to define behaviour event hashing in maps:
    # see https://www.asmeurer.com/blog/posts/what-happens-when-you-mess-with-hashing-in-python/
    def __hash__(self):
        return ResolvedEventInstance.calculate_hash(self)

    @staticmethod
    def calculate_hash(my_object):    

       pseudo_object = [ my_object.get_full_name(), my_object.get_id(), my_object.get_description_list("PARAMETER")]

       return int(hashlib.sha256(pickle.dumps(pseudo_object,1)).hexdigest(),16) % (10 ** 64)       
    
    def __eq__(self, other):
        if not isinstance(other, ResolvedEventInstance):
            return False
        e1 =  ResolvedEventInstance.calculate_hash(self)
        e2 =  ResolvedEventInstance.calculate_hash(other)
        return e1 == e2

    #########################################################

    def get_full_name(self):
        path = self.get_description_list("EVENT_PATH")
        full_name = path[0] + "::" + self.get_name()
        return full_name

    def get_mapping_type(self):
        parameter_set = self.get_description_list("PARAMETER")

        if len(parameter_set) == 0:
            return MappingType("SIMPLE")

        for parameter in parameter_set:
            value = parameter.get_value()
            if isinstance(value, SerializedFunctionExpression):
                return MappingType("VARIABLE")

        return MappingType("FIXED")

    def __str__(self):
        result = self.get_full_name() + "("
        parameters = self.get_description_list("PARAMETER")
        if parameters is not None:
            for parameter in parameters:
                try:
                    result += str(parameter) +" ,"     
                except:
                    result += "expression ,"
                
            result = result[:-1]

        return result +")"
    

    def get_id_set(self):
        (event_path_name, event_path_id) = self.get_description_list("EVENT_PATH")
        (event_name, event_id) = self.get_description_list("EVENT_TYPE")

        # reshape event_path_id to fit little endian:
        reshaped_event_path_id = (event_path_id >> 8) + ((event_path_id & 0xFF) << 8)

        if event_path_id > 255:
            pass

        id_parameter = ResolvedParameter(
            "EVENT_ID_SET",
            (reshaped_event_path_id << 16) + event_id,
            ParameterFormat("UINT32"),
            super().get_location(),
        )
        return id_parameter


class ResolvedVariable(ResolvedInstanceBase):
    def __init__(self, my_name, var_format, var_expression, location_info):
        super().__init__(my_name, location_info)
        self.__expression = var_expression
        self.__format = var_format
        self.__reference_controller_names = set()

    def add_reference_controller_names(self, my_reference_controller_names):
        if my_reference_controller_names is None:
            return

        if not isinstance(my_reference_controller_names, list):
            my_reference_controller_names = [my_reference_controller_names]

        for controller_name in my_reference_controller_names:
            self.__reference_controller_names.add(controller_name)

    def get_value(self):
        return self.__expression.get_value()

    def get_format(self):
        return self.__format

    def get_reference_controller_names(self):
        return list(self.__reference_controller_names)

    def is_connected(self):
        return len(self.__reference_controller_names) != 0

    def is_expression(self):
        return isinstance(self.__expression, SerializedFunctionExpression)


#######################################


class EventVariable:
    def __init__(self, value):
        self.__name = value

    def __str__(self):
        return "EVENT::" + self.__name


class SerializedFunctionExpression:
    def __init__(self, my_serialized_expression):
        self.__expression = my_serialized_expression

    def get_value(self):
        return self.__expression

    def get_value_as_expression(self):
        return self.__expression

    def get_type(self):
        return "FUNCTION_EXPRESSION"

    def __str__(self):
        name = ""
        for element in self.__expression:
            name += str(element) + "_"
        return name[:-1]


class FunctionExpression:
    def __init__(self, operand1, operand2, operator):
        self.__operator = operator
        self.__operand1 = operand1
        self.__operand2 = operand2

    def operator(self):
        return self.__operator

    def operand1(self):
        return self.__operand1

    def operand2(self):
        return self.__operand2

    def __str__(self):
        if self.__operator is None:
            return str(self.__operand1)

        return str(self.__operand1) + str(self.__operator) + str(self.__operand2)


class Function:
    def __init__(self, name, argument_list):
        self.__name = name
        self.__argument_list = argument_list

    def name(self):
        return self.__operator

    def argument_list(self):
        return self.__argument_list

    def __str__(self):
        result = self.__name + "("
        for i in range(len(self.__argument_list)):
            result = result + str(self.__argument_list[i])
        result = result + ")"
        return result


######################################################################################
#
#
#  Parameter
#
#
#######################################################################################


class ResolvedParameterBase(ResolvedBase):
    def get_format(self):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


# class ResolvedReference(ResolvedParameterBase):
#    def __init__(self, my_name, my_map, my_location_info):
#        super().__init__(my_name, my_location_info)
#        self.__reference_map = my_map##

#    def get_value(self):
#        return self.__reference_map.get_entry_by_name(super().get_name()).get_value()

#    def get_format(self):
#        return self.__reference_map.get_entry_by_name(super().get_name()).get_format()

# def get_referenced_item(self):
#    return  self.__reference_map.get_item_by_name(super().get_name())


class ResolvedVariableReference(ResolvedParameterBase):
    def __init__(self, my_name, my_variable, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__reference = my_variable.get_id()

    def get_value(self):
        return self.__reference

    def get_format(self):
        return ParameterFormat("UINT16")

    def __str__(self):
        return super().get_name() + " (REF = " + str(self.__reference) + ")"


class ResolvedParameter(ResolvedParameterBase):
    def __init__(self, my_name, my_value, my_format, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__value = my_value
        self.__format = my_format

    def replace_value(self, my_new_value):
        self.__value = my_new_value

    def get_format(self):
        return self.__format

    def set_value(self, my_value):
        self.__value = my_value

    def __str__(self):
        if self.__value is None:
            result = ""
        elif isinstance(self.__value, list):
            result = str(self.__value)
        else:
            if str(self.__format) == "UINT8":
                div_steps = 1
            elif str(self.__format) == "UINT16":
                div_steps = 2
            elif str(self.__format) == "UINT32":
                div_steps = 4
            elif str(self.__format) == "UINT64":
                div_steps = 8
            else:
                raise ResolverError(
                    None,
                    "Internal Error in __str__  function. Unsupported type:"
                    + self.__format,
                )

            result = ""
            value = int(self.__value)
            for j in range(div_steps):
                item = value & 255
                value >>= 8
                result += "{:02x}".format(item)

        return result

    def get_value(self):
        return self.__value

    def get_value_as_expression(self):
        if isinstance(self.__value, SerializedFunctionExpression):
            return self.__value.get_value()

        new_value = ResolvedConstantElement(self.__value, self.__format)
        return SerializedFunctionExpression([new_value]).get_value()

    def is_expression(self):
        return isinstance(self.__value, list)

    def is_symbol(self):
        return isinstance(self.__value, ResolvedSymbol)


class ResolvedConnection(ResolvedParameterBase):
    def __init__(self, my_name, my_location_info):
        super().__init__(my_name, my_location_info)
        self.__app_name = None
        self.__driver_class_name = None
        self.__driver_name = None
        self.__pin_name = None

        self.__app_id = 0
        self.__driver_id = 0
        self.__driver_class_id = 0
        self.__pin_id = 0

    def get_app_name(self):
        return self.__app_name

    def get_name(self):
        return (
            self.__app_name
            + "[::"
            + self.__driver_class_name
            + "]::"
            + self.__driver_name
            + "::"
            + self.__pin_name
        )

    def get_pin_name(self):
        return self.__pin_name

    def __eq__(self,other):
        if not isinstance(other, ResolvedConnection):
            return TypeError
        if self.__app_id == other.__app_id and self.__pin_id == other.__pin_id and self.__driver_id == other.__driver_id:
             return True
        return False


    def get_pin_id(self):
        return self.__pin_id

    def set_app(self, my_app_name, my_app_id):
        self.__app_name = my_app_name
        self.__app_id = my_app_id

    def set_driver(self, my_driver_name, my_driver_id):
        self.__driver_name = my_driver_name
        self.__driver_id = my_driver_id

    def set_pin(self, my_pin_name, my_pin_id):
        self.__pin_name = my_pin_name
        self.__pin_id = my_pin_id

    def set_driver_class(self, my_driver_class_name, my_driver_class_id):
        self.__driver_class_name = my_driver_class_name
        self.__driver_class_id = my_driver_class_id

    def get_driver_name(self):
        return self.__driver_name

    def get_pin_name(self):
        return self.__pin_name

    def get_driver_class(self):
        return self.__driver_class_name

    def get_format(self):
        return ParameterFormat("UINT32")

    def get_value(self):
        full_id = (
            (self.__app_id << 0)
            + (self.__driver_class_id << 8)
            + (self.__driver_id << 16)
            + (self.__pin_id << 24)
        )
        return full_id

    def get_name(self):
        if self.__driver_name is not None:
            full_name = (
                self.__app_name + "." + self.__driver_name + "::" + self.__pin_name
            )
        else:
            full_name = self.__app_name
        return full_name

    def __str__(self):
        return self.__get_name()


#######################################################
#
#
#   Expression Elements:
#
#
#######################################################


class ResolvedElementBase:
    def __init__(self, my_type):
        self.__type = ExpressionElementType(my_type)

    def get_value_format(self):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError

    def get_type(self):
        return self.__type

    def get_type_key(self):
        return self.__type.get_key()

    def get_type_key_format(self):
        return self.__type.get_key_format()

    def get_name(self):
        raise NotImplementedError

    def __str__(self):
        return self.get_name()

    def is_type(self, my_type):
        return self.__type.get_key() == ExpressionElementType(my_type).get_key()


class ResolvedFunctionElement(ResolvedElementBase):
    def __init__(self, my_operator_string):
        self.__number_of_arguments = None
        super().__init__("FUNCTION")
        self.__operator_key = OperatorElementType(my_operator_string)
        self.__name = my_operator_string  # "FUNCTION::"+ my_operator_string

    def set_number_of_arguments(self, my_number_of_arguments):
        self.__number_of_arguments = my_number_of_arguments
        if my_number_of_arguments > 255:
            raise OverflowError

    def get_operator(self):
        return self.__operator_key

    def get_operator_key(self):
        return self.__operator_key.get_key()

    def get_operator_key_format(self):
        return ParameterFormat("UINT8")

    def get_value_format(self):
        return ParameterFormat("UINT8")

    def get_value(self):
        return self.__number_of_arguments

    def get_name(self):
        return self.__name

    # def __str__(self):
    #    return get_name()


class ResolvedVariableElement(ResolvedElementBase):
    def __init__(self, my_name, my_id):
        self.__reference_id = my_id
        self.__name = my_name
        super().__init__("VARIABLE")

    def get_value_format(self):
        return ParameterFormat("UINT16")

    def get_name(self):
        return self.__name

    def get_value(self):
        return self.__reference_id


class ResolvedSymbol(ResolvedElementBase):
    def __init__(self, my_value, my_format):
        self.__name = "SYMBOL::" + str(my_value)

        self.__value = my_value
        self.__value_format = my_format
        super().__init__("CONSTANT_STRING")

    def get_value_format(self):
        return self.__value_format

    def get_value(self):
        return self.__value

    def get_name(self):
        return self.__name


class ResolvedConstantElement(ResolvedElementBase):
    def __init__(self, my_value, my_format):
        self.__name = "CONSTANT::" + str(my_value)

        self.__value = my_value
        self.__value_format = my_format
        super().__init__("CONSTANT_FLOAT")

    def get_value_format(self):
        return self.__value_format

    def get_value(self):
        return self.__value

    def get_name(self):
        return self.__name

    # def __str__(self):
    #    return get_name()


class ResolvedEventParameterElement(ResolvedElementBase):
    def __init__(
        self,
        my_name,
        my_list_of_preceding_parameter_formats,
        my_format,
        my_reference_device_name,
    ):
        self.__name = "EVENT::" + my_name

        self.__value = 0
        for format_item in my_list_of_preceding_parameter_formats:
            self.__value += ParameterFormat(format_item).get_binary_format_length()

        self.__event_format = ParameterFormat(my_format)
        self.__reference_device_name = my_reference_device_name
        super().__init__("EVENT_PARAMETER")

    def get_value_format(self):
        return ParameterFormat("UINT16")

    def get_value(self):
        return self.__value

    def get_event_parameter_format(self):
        return self.__event_format

    def get_name(self):
        return self.__name

    def get_reference_device_name(self):
        return self.__reference_device_name

    # def __str__(self):
    #    return get_name()


##################################################################
#
#
#
#   Events, Mappings and MappingRules
#
#
##################################################################


class __ResolvedMappingEventBase:
    def __init__(self, my_protocol):
        # self.__key         = my_event_group << 8 | my_event_id
        self.__protocol = ProtocolType(my_protocol)
        self.__name = None
        self.__parameter = None
        self.__device_name = None
        self.__controller_name = None
        self.__event_group = None
        self.__event_id = None

    def set_controller_name(self, my_controller_name):
        self.__controller_name = my_controller_name

    def set_key(self, my_event_group, my_event_id):
        self.__event_group = my_event_group
        self.__event_id = my_event_id

    def set_device_path_name(self, my_name):
        self.__device_name = my_name

    def set_name(self, my_name):
        self.__name = my_name

    def set_parameter(self, my_parameter):
        self.__parameter = my_parameter

    def is_ccan_event(self):
        return self.__protocol.is_ccan()

    def get_key(self):
        return self.__event_group << 8 | self.__event_id

    @staticmethod
    def get_mapping_method_and_key(my_event1, my_event2):
        method1 = my_event1.__get_mapping_method()
        method2 = my_event2.__get_mapping_method()

        result_method = method1
        if method2 > method1:
            result_method = method2

        return (result_method, my_event1.__get_mapping_key(result_method))

    def __get_mapping_method(self):
        if self.__parameter is None:
            return MappingType("Simple")
        elif isinstance(self.__parameter, list):
            return MappingType("Variable")
        return MappingType("Fixed")

    def __get_mapping_key(self, my_mapping_type):
        if my_mapping_type == MappingType("Simple") or my_mapping_type == MappingType(
            "Variable"
        ):
            return self.__get_key()

        if self.__parameter is not None:
            return (self.get_key(), str(self.__parameter))
        else:
            return (self.get_key(), "")

    def get_parameter(self):
        return self.__parameter

    def get_device_path_name(self):
        return self.__device_name

    def get_name(self):
        return self.__name

    def get_protocol(self):
        return self.__protocol

    def get_controller_name(self):
        return self.__controller_name

    def is_alias_event(self):
        return self.__protocol.is_ccan() and self.__event_group is None


class __ResolvedMappingBase:
    def __init__(self, my_source_mapping):
        self.__source_mapping = my_source_mapping
        self.__target_mapping = []

    def add_target_mapping(self, my_target_mapping):
        self.__target_mapping.append(my_target_mapping)

    def get_source_mapping(self):
        return self.__source_mapping

    def get_target_mappings(self):
        return self.__target_mapping


class AliasEventPair:
    def __init__(self, my_target_event, my_alias_event, my_target_event_descriptor):
        self.__target_event = my_target_event
        self.__alias_event = my_alias_event
        self.__event_descriptor = my_target_event_descriptor

    def get_target_event(self):
        return self.__target_event

    def get_alias_event(self):
        return self.__alias_event

    def get_event_descriptor(self):
        return self.__event_descriptor
  
#####


class ResolvedMappingEvent(__ResolvedMappingEventBase):
    pass


class ResolvedMapping(__ResolvedMappingBase):
    pass


##################################################################
#
#
#   Formats, ExpressionTypes, OperatorTypes
#
#
##################################################################


def get_automatic_parameter_variable_prefix():
    return "VAR::AUTOMATIC_NAME_"


class InstanceDescriptionType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["DEVICE"] = 0
        Key["VARIABLE"] = 1
        Key["SENSOR_DRIVER"] = 2
        Key["COMMUNICATION_DRIVER"] = 3
        Key["TRANSPORT_ADAPTER"] = 4
        Key["EVENT"] = 5
        Key["MAPPING"] = 6
        Key["PARAMETER"] = 7
        Key["CONNECTION"] = 8
        Key["DEGRADATION"] = 9
        Key["ATTRIBUTES"] = 10

        Key["AUTOMATION"] = 11
        Key["ALIAS_EVENTS"] = 12
        Key["ALIAS_VARIABLES"] = 13
        super().__init__(Key, my_element)


class ParameterDescriptionType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["PARAMETER"] = 0
        Key["VARIABLE"] = 1
        Key["CONNECTION"] = 2
        Key["DEGRADATION"] = 3
        super().__init__(Key, my_element)


class ParameterFormat(KeyMapBase):
    def __init__(self, my_format):
        Key = {}
        Key["BOOL"] = 0
        Key["UINT8"] = 1
        Key["UINT16"] = 2
        Key["UINT32"] = 3
        Key["UINT64"] = 4
        Key["INT8"] = 5
        Key["INT16"] = 6
        Key["INT32"] = 7
        Key["INT64"] = 8
        Key["FLOAT"] = 9
        Key["STRING"] = 10
        Key["NAME"] = 11
        Key["CCAN_ADDRESS"] = 20
        Key["IPV4_ADDRESS"] = 21
        Key["CONNECTION"] = 40        
        Key["DEVICE"] = 80

        super().__init__(Key, my_format)

    def get_binary_format_length(self):
        Key = {}
        Key["BOOL"] = 1
        Key["UINT8"] = 1
        Key["UINT16"] = 2
        Key["UINT32"] = 4
        Key["UINT64"] = 8
        Key["INT8"] = 1
        Key["INT16"] = 2
        Key["INT32"] = 4
        Key["INT64"] = 8
        Key["FLOAT"] = 4
        Key["CCAN_ADDRESS"] = 2
        Key["IPV4_ADDRESS"] = 4
        Key["CONNECTION"] = 4

        length = Key[str(self)]

        return length

    def __ne__(self, other):
        return self.get_key() != other.get_key()
    
    def __eq__(self, other):
        return self.get_key() == other.get_key()

    def is_numerical(self):
        if self.get_key() < 6 or self.get_key() == 20 or self.get_key() == 40:
            return True
        return False


class ExpressionElementType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["CONSTANT_FLOAT"] = 0
        Key["CONSTANT_STRING"] = 1
        Key["VARIABLE"] = 2
        Key["EVENT_PARAMETER"] = 3
        Key["FUNCTION"] = 4
        Key["OPERATOR"] = 10
        super().__init__(Key, my_element)


class OperatorElementType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["+"] = 0
        Key["-"] = 1
        Key["*"] = 2
        Key["/"] = 3
        Key["BINARY"] = 10
        Key["AND"] = 20
        Key["OR"] = 21
        Key["NOT"] = 22
        Key["NAND"] = 23
        Key["NOR"] = 24
        super().__init__(Key, my_element)


class MapperType(KeyMapBase):
    def __init__(self, my_element="INTERNAL"):
        Key = {}
        Key["INTERNAL"] = 0
        Key["INBOUND"] = 1
        Key["OUTBOUND"] = 2
        super().__init__(Key, my_element)


class MappingType(KeyMapBase):
    def __init__(self, my_element="SIMPLE"):
        Key = {}
        Key["SIMPLE"] = 0
        Key["FIXED"] = 1
        Key["VARIABLE"] = 2
        super().__init__(Key, my_element)

    def maximum(self, mapping_type_list):
        result = MappingType("SIMPLE")
        for mapping_type in mapping_type_list:
            if mapping_type.get_key() > result.get_key():
                result = mapping_type

        return result

    def __gt__(self, my_mapping):
        return self.get_key() > my_mapping.get_key()

    def __lt__(self, my_mapping):
        return self.get_key() < my_mapping.get_key()


class EventDirectionType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["IN"] = 0
        Key["OUT"] = 1
        super().__init__(Key, my_element)


class DriverClassType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["SENSOR_DRIVER"] = 0
        Key["COMMUNICATION_DRIVER"] = 1
        Key["TRANSPORT_ADAPTER"] = 2
        super().__init__(Key, my_element)


class DeviceAttribute(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["CONTROLLER_SPECIFIC"] = 0
        # (..)
        super().__init__(Key, my_element)


class ProtocolType(KeyMapBase):
    Key = {}
    Key["CCAN"] = 0
    Key["HCAN"] = 1
    Key["HOME_ASSISTANT"] = 2

    def __init__(self, my_element="CCAN"):
        super().__init__(ProtocolType.Key, my_element)

    def get_key_length(self):
        return 3  # fixed Length for keys: 2 for ID, 1 for KEY

    def is_ccan(self):
        return self.get_key() == ProtocolType.Key["CCAN"]


#############################################################################
