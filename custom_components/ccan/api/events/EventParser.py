import os
import lark
from lark.visitors import Transformer
from api.resolver.ResolverError import ResolverError
from api.events.RawEvent import AddressingType


@lark.v_args(inline=True)
class CLI_EventParser(Transformer):
    def __init__(self, my_symbolic_event):
        self.__parameters = None
        self.__names = None
        try:
            result_tree = lark.Lark(
                self.__load_grammar(["EVENT", "PARAMETER"]), parser="earley"
            ).parse(my_symbolic_event)
        except lark.exceptions.UnexpectedEOF:
            raise ResolverError(
                None, "Syntax error in " + my_symbolic_event + " detected."
            )
        self.transform(result_tree)

    def get_event(self):
        return self.__names

    def get_parameters(self):
        return self.__parameters

    def is_device_event(self):
        return True if self.__event_type == "DEVICE" else False

    def is_application_event(self):
        return True if self.__event_type == "APPLICATION" else False

    def is_hcan_event(self):
        return True if self.__event_type == "HCAN" else False

    def get_addressing_type(self):
        if self.__addressing_type == "DEV":
            return AddressingType("DEVICE_EVENT_ADDRESSING")
        elif self.__addressing_type == "DIR":
            return AddressingType("DIRECT_EVENT_ADDRESSING")
        elif self.__addressing_type == "IND":
            return AddressingType("INDIRECT_EVENT_ADDRESSING")
        elif self.__addressing_type == "OUT":
            return AddressingType("OUTBOUND_EVENT_ADDRESSING")

        elif self.is_application_event():
            return AddressingType("APPLICATION_EVENT_ADDRESSING")
        elif self.is_hcan_event():
            return AddressingType("PROTOCOL_EVENT_ADDRESSING")
        raise TypeError

    def __load_grammar(self, my_file_marker_array):
        lines = []
        my_file_marker_array.append("CONSTANTS")
        path = os.path.dirname(os.path.realpath(__file__))
        for file_marker in my_file_marker_array:
            if file_marker == "EVENT":
                filename = "Event.lark"
            elif file_marker == "PARAMETER":
                filename = "ConstantParameterList.lark"
            elif file_marker == "CONSTANTS":
                filename = "StandardDefinitions.lark"

            with open(path + "/" + filename, "r") as file:
                lines.append(file.read())
        lines[0] = "start:" + lines[0]
        result = "\n".join(lines)
        return result

    def device_event(self, my_addressing_type, *device_event):
        self.__addressing_type = (
            str(my_addressing_type)
            if str(my_addressing_type) in ["DEV", "DIR", "IND", "OUT"]
            else None
        )
        if self.__addressing_type is None:
            raise TypeError

        # not used:
        parameters = device_event[-1]

        device_name = ""
        device_event = device_event[0:-1]
        # determine number of elements:
        for part, i in zip(device_event[0:-1], range(0, len(device_event))):
            device_name += str(part)
            if i < len(device_event) - 2:
                device_name += "."

        event_name = str(device_event[-1])

        self.__names = [str(device_name), str(event_name)]
        self.__event_type = "DEVICE"

    def application_event(self, my_device_name, my_event_name, my_parameters):
        self.__addressing_type = None
        self.__names = [str(my_device_name), str(my_event_name)]
        self.__event_type = "APPLICATION"

    def hcan_event(self, my_path_name, my_event_name, my_parameters):
        path_name = str(my_path_name)
        self.__names = [str(path_name[1 : len(path_name) - 1]), str(my_event_name)]
        self.__event_type = "HCAN"
        self.__addressing_type = None

    def parameter_list(self, *my_parameter):
        if my_parameter[0] == None:
            self.__parameters = []
        else:
            self.__parameters = my_parameter
        return None

    def parameter(self, *my_parameter):
        if my_parameter[0] == None:
            name = None
        else:
            name = str(my_parameter[0])

        value = my_parameter[1]

        return (name, value)

    def value_list(self, *my_param):
        values = []
        for param in my_param:
            values.append(str(param))
        return values
