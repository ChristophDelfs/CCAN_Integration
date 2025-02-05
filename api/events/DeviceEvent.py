import time

from src.events.RawEvent import RawEvent
from src.events.Parameters import Parameters
from src.PyCCAN_ConvertBinary import SequenceExtractor, SequenceCreator
from src.resolver.Definitions import Colors, NoColors


class DeviceEvent(RawEvent):
    def __init__(self, *my_input):
        if not isinstance(my_input[0], RawEvent):
            return self.__init__from_symbolic_expression(my_input)

        my_raw_event = my_input[0]
        my_instance_dict = my_input[1]
        my_description_dict = my_input[2]

        self._orig_seq = my_raw_event.get_sequence()
        self._time_stamp = my_raw_event.get_time_stamp()
        self._addressing_type = my_raw_event.get_addressing_type()
        self._payload = my_raw_event.get_payload()
        self._hex_mode = my_raw_event._hex_mode

        self._colors = my_raw_event._colors

        if not self._addressing_type.is_device_event():
            raise TypeError

        seq = SequenceExtractor(my_raw_event.get_payload())

        self.__device_id = seq.convertback16()
        self.__event_id = seq.convertback8()
        self.__parameter_seq = None

        device_instance = my_instance_dict.get_entry_by_id(self.__device_id)
        if device_instance is None:
            self.__device_name = "Unknown Device with ID " + str(self.__device_id)
            self.__controller_name = "Unknown Controller"
            self.__event_name = "Unknown Event with ID " + str(self.__event_id)
            self.__event_id_name = "Unknown Event with ID " + str(self.__event_id)
            self.__parameters = None
            self.__parameter_seq = []

        else:
            self.__device_name = device_instance.get_name()
            self.__controller_name = device_instance.get_description_list("CONNECTION")[
                0
            ].get_app_name()
            self.__device_type = device_instance.get_type()
            device_description = my_description_dict.get_entry_by_name(
                self.__device_type
            )
            device_event_list = device_description.get_description_list("EVENT")
            device_event = device_event_list.get_entry_by_id(self.__event_id)

            if device_event is None:
                # Error: automation file mismatch! Event cannot be resolved.
                self.__event_name = "Unknown Event with ID " + str(self.__event_id)
                self.__parameters = None
                self.__parameter_seq = []
                # raise ValueError
            else:
                self.__event_name = device_event.get_name()
                # self.__parameter_seq = seq.get_sequence()

                (parameter_set_names, parameter_set_formats) = (
                    device_event.get_description_list("PARAMETER")
                )

                self.__parameters = Parameters(
                    seq, parameter_set_names, parameter_set_formats
                )
                self.__parameter_seq = self.__parameters.get_sequence()

    def is_complete(self):
        return True

    def __init__from_symbolic_expression(self, my_input):
        self._time_stamp = time.time()
        self._addressing_type = my_input[0].get_addressing_type()
        self._seq = None

        my_event = my_input[0].get_event()
        my_parameters = my_input[0].get_parameters()
        my_instance_dict = my_input[1]
        my_description_dict = my_input[2]

        my_seq = SequenceCreator()
        my_seq.convert8(self._addressing_type.get_key())

        self.__device_name = my_event[0]
        self.__event_name = my_event[1]

        device_instance = my_instance_dict.get_entry_by_name(self.__device_name)
        if device_instance == None:
            raise TypeError

        self.__device_id = device_instance.get_id()
        my_seq.convert16(self.__device_id)
        self.__device_type = device_instance.get_type()
        device_description = my_description_dict.get_entry_by_name(self.__device_type)
        device_event_list = device_description.get_description_list("EVENT")
        device_event = device_event_list.get_by_name(self.__event_name)
        if device_event is None:
            raise TypeError

        self.__event_id = device_event_list.get_id_by_name(self.__event_name)
        my_seq.convert8(self.__event_id)

        if len(my_parameters) != 0:
            (parameter_set_names, parameter_set_formats) = (
                device_event.get_description_list("PARAMETER")
            )
            self.__parameters = Parameters(
                my_parameters, parameter_set_names, parameter_set_formats
            )
            self.__parameter_seq = self.__parameters.get_sequence()
            my_seq.append(self.__parameters.get_sequence())
        else:
            self.__parameters = Parameters()
            self.__parameter_seq = []

        self._seq = my_seq

    def get_parameters(self):
        return self.__parameters

    def get_parameter_values(self):
        if self.__parameters != None:
            return self.__parameters.get_values()
        return None

    def get_sequence(self):
        return self._seq.get_sequence()

    #######

    def __eq__(self, my_device_event):
        try:
            assert isinstance(my_device_event, DeviceEvent)
            assert self.__device_id == my_device_event.__device_id
            assert self.__event_id == my_device_event.__event_id
            assert self.__parameters == my_device_event.__parameters
        except AssertionError:
            return False
        return True

    def __str__(self):
        colors = self._get_colors()

        parameter_output = (
            str(self.__parameters.get_as_string(colors))
            if self.__parameters is not None
            else "()"
        )
        raw_output = super().__str__()

        if self._hex_mode:
            binary_output = (
                " [" + ", ".join(hex(n) for n in self._orig_seq.get_sequence()) + " ]"
            )
        else:
            binary_output = ""

        return (
            raw_output
            + " "
            + "("
            + self.__controller_name
            + ") "
            + colors.GREEN
            + self.__device_name
            + "::"
            + self.__event_name
            + colors.END
            + parameter_output
            + binary_output
        )
