from src.PyCCAN_ConvertBinary import SequenceExtractor, SequenceCreator
from src.events.RawEvent import RawEvent
from src.events.Parameters import Parameters
from src.base.PlatformDefaults import PlatformDefaults
from src.resolver.Definitions import Colors, NoColors

import time


class ApplicationEvent(RawEvent):
    AUTOMATION_INSTANCE_DICTIONARY = None
    APPLICATION_EVENT_DICTIONARY = None
    #BROADCAST_ADDRESS = 0xFFFF

    def __init__(self, *my_input):
        if not isinstance(my_input[0], RawEvent):
            return self.__init__from_parsed_expression(my_input)

        my_raw_event = my_input[0]
        my_instance_address = my_input[1]
        #my_app_instances = my_input[2]

        self._orig_seq = my_raw_event.get_sequence()
        self._time_stamp = my_raw_event.get_time_stamp()
        self._addressing_type = my_raw_event.get_addressing_type()
        self._payload = my_raw_event.get_payload()
        self._hex_mode = my_raw_event._hex_mode

        self._colors = my_raw_event._colors

        if not self._addressing_type.is_application_event():
            raise TypeError

        seq = SequenceExtractor(my_raw_event.get_payload())
        self.__sender_address = seq.convertback16()
        self.__service_id = seq.convertback8()
        self.__event_id = seq.convertback8()
        self.__destination_address = seq.convertback16()

        self.__service_name = "Unknown"
        self.__event_name = "Unknown"
        self.__parameters = None
        self.__parameter_seq = None

        for elem in ApplicationEvent.APPLICATION_EVENT_DICTIONARY:
            entry = ApplicationEvent.APPLICATION_EVENT_DICTIONARY[elem]
            if entry.service_id == self.__service_id:
                self.__service_name = elem
                for event in entry.event_list:
                    if event.id == self.__event_id:
                        self.__event_name = event.name

                        if event.parameters is not None:
                            self.__parameter_seq = seq.get_sequence()
                            try:
                                self.__parameters = Parameters(
                                    seq,
                                    event.parameters.parameter_name_list,
                                    event.parameters.parameter_type_list,
                                    event.parameters.dimension_list,
                                )
                            except ValueError:
                                self.__parameters = Parameters()
                        else:
                            self.__parameters = Parameters()
                            self.__parameter_seq = self.__parameters.get_sequence()

                        self.__sender_instance = (
                            self.__resolve_instance_by_ccan_address(
                                self.__sender_address,                            
                                my_instance_address,
                            )
                        )
                        self.__destination_instance = (
                            self.__resolve_instance_by_ccan_address(
                                self.__destination_address,
                                my_instance_address,
                            )
                        )
                        return

        print(
            "Internal Error: Unknown event service: <"
            + str(self.__service_id)
            + "> and event id <"
            + str(self.__event_id)
            + ">"
        )
        raise TypeError

    def __init__from_parsed_expression(self, my_input):
        super().__init__(None)
        self._addressing_type = my_input[
            0
        ].get_addressing_type()  # AddressingType("APPLICATION_EVENT_ADDRESSING")
        self._seq = None

        my_event = my_input[0].get_event()
        my_parameters = my_input[0].get_parameters()
        self.__sender_address = my_input[1]
        self.__destination_address = my_input[2]
        my_instance_address = my_input[3]
        #my_app_instances = my_input[4]      

        self.__service_name = my_event[0]
        self.__event_name = my_event[1]

        self.__parameters = None
        self.__parameter_seq = None

        service = ApplicationEvent.APPLICATION_EVENT_DICTIONARY[self.__service_name]
        self.__service_id = service.service_id
        for event in service.event_list:
            if event.name == self.__event_name:
                self.__event_id = event.id

                my_seq = SequenceCreator()
                my_seq.convert8(self._addressing_type.get_key())
                my_seq.convert16(self.__sender_address)
                my_seq.convert8(self.__service_id)
                my_seq.convert8(self.__event_id)
                my_seq.convert16(self.__destination_address)

                if event.parameters is not None:
                    self.__parameters = Parameters(
                        my_parameters,
                        event.parameters.parameter_name_list,
                        event.parameters.parameter_type_list,
                        event.parameters.dimension_list,
                    )
                    self.__parameter_seq = self.__parameters.get_sequence()
                    my_seq.append(self.__parameter_seq)
                else:
                    self.__parameters = Parameters()
                    self.__parameter_seq = self.__parameters.get_sequence()
                    if len(my_parameters) != 0:
                        raise TypeError

                if ApplicationEvent.AUTOMATION_INSTANCE_DICTIONARY is not None:
                    self.__sender_instance = (
                        self.__resolve_instance_by_ccan_address(
                            self.__sender_address, my_instance_address
                        ),
                    )
                    self.__destination_instance = (
                        self.__resolve_instance_by_ccan_address(
                            self.__destination_address,                            
                            my_instance_address,
                        )
                    )
                else:
                    self.__sender_instance = None
                    self.__destination_instance = None
                self._seq = my_seq
                self._time_stamp = time.time()
                return

        print("Could not identify event" + self.__event_name)
        raise TypeError

    def replace_simple_parameter(self, my_data):
        # isolate header:
        my_seq = self._seq.get_sequence()
        self._seq = SequenceCreator(my_seq[0:7])
        try:
            # add length:
            self._seq.convert16(len(my_data))
            self._seq.append(my_data)
        except Exception as ex:
            pass
        return self

    def get_service(self):
        return self.__service_name

    def get_event_name(self):
        return self.__event_name

    def get_parameters(self):
        return self.__parameters

    def get_sender_address(self):
        return self.__sender_address

    def get_sender_name(self):
        return self.__sender_instance

    def get_parameter_values(self):
        if self.__parameters != None:
            return self.__parameters.get_values()
        return None

    def get_sequence(self):
        return self._seq.get_sequence()

    def is_complete(self):
        return True

    def __resolve_instance_by_ccan_address(
        self, address, my_instance_address
    ):
        if address == PlatformDefaults.SERVER_CCAN_ADDRESS:
            return "CCAN Server"

        if address == PlatformDefaults.INVALID_CCAN_ADDRESS:
            return "UNCONFIGURED CLIENT"

        if address == PlatformDefaults.BROADCAST_CCAN_ADDRESS:
            return "BROADCAST"
             
        try:
            for id, app in ApplicationEvent.AUTOMATION_INSTANCE_DICTIONARY["APP"]:
                for parameter in app.get_description_list("PARAMETER"):
                    if str(parameter.get_format()) == "CCAN_ADDRESS":
                        if parameter.get_value() == address:
                            return app.get_name()
        except Exception:
            pass

        return "instance address " + str(address)

    #######

    def __eq__(self, my_event):
        try:
            assert isinstance(my_event, ApplicationEvent)
            assert self.__service_id == my_event.__service_id
            assert self.__event_id == my_event.__event_id
            # assert self.__sender_address == my__event.__destination_address
            # assert self.__destination_address ==  my__event.__sender_address
            if self.__parameter_seq != [] and my_event.__parameter_seq != []:
                assert self.__parameter_seq == my_event.__parameter_seq
        except AssertionError:
            return False
        return True

    def __str__(self):
        colors = self._get_colors()
     
        if self.__service_name == "VARIABLE_SERVICE" and ApplicationEvent.AUTOMATION_INSTANCE_DICTIONARY is not None:
            # retrieve variable name
            for dimension, name, value, value_type in self.__parameters:
                if dimension == 'Scalar' and name =="ID":
                    variable_entry= ApplicationEvent.AUTOMATION_INSTANCE_DICTIONARY["VARIABLE"].get_entry_by_id(value)
                    variable_name = variable_entry.get_name()
                    parameter_output = f"({variable_name} = "
                else:
                    if value_type == "FLOAT":
                        parameter_output+= f"{value:.4})"                 
                    else:
                        parameter_output+= f"{value})"
       
        else:
            parameter_output = (
            self.__parameters.get_as_string(colors) if self.__parameters is not None else ""
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
            + colors.MAGENTA
            + self.__sender_instance
            + " -> "
            + self.__destination_instance
            + colors.END
            + " "
            + colors.FAT_WHITE
            + self.__service_name
            + "::"
            + self.__event_name
            + colors.END
            + parameter_output
            + binary_output
        )
