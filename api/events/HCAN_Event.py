import time

from src.PyCCAN_ConvertBinary import SequenceExtractor
from src.PyCCAN_ConvertBinary import SequenceCreator
from src.events.RawEvent import RawEvent

from src.events.Parameters import Parameters
from src.base.CCAN_Error import CCAN_Error
from src.base.CCAN_Error import CCAN_ErrorCode


class HCAN_Event(RawEvent):
    HCAN_MULTICAST_INFO = 36
    PROTOCOL_ID = 1
    syslog_message_map = {}

    def set_dictionary(my_dict):
        raise NotImplementedError

    def is_complete(self):
        return self.__is_complete

    def __init__(
        self, *my_input
    ):  # my_raw_event, my_hcan_address, my_protocol_instance)
        if not isinstance(my_input[0], RawEvent):
            return self.__init_from_parsed_expression(
                my_input[0], my_input[1], my_input[2]
            )
        my_raw_event = my_input[0]
        my_protocol_instance = my_input[1]
        my_cli_reference = my_input[2]
        self._colors = my_raw_event._colors

        self._addressing_type = my_raw_event.get_addressing_type()
        self._payload = my_raw_event.get_payload()
        self._time_stamp = my_raw_event._time_stamp
        self._hex_mode = my_raw_event._hex_mode

        self.__seq = SequenceExtractor(self._payload)

        if not my_raw_event.get_addressing_type().is_external_protocol_event():
            raise CCAN_Error(
                CCAN_ErrorCode.PROTOCOL_EVENT_INVALID,
                " expected a HCAN event, but received data is "
                + str(self._payload)
                + ".",
            )

        self.__is_complete = False

        seq = self.__seq
        self.__external_protocol_id = seq.convertback8()
        if self.__external_protocol_id != 1:
            raise TypeError

        self._orig_seq = my_raw_event.get_sequence()

        # decompose HCAN IP frame:
        extended_id = seq.convertback32()
        self.__protocol_id = extended_id >> 20 & 0x07
        self.__destination_address = extended_id >> 10 & 0x3FF
        self.__sender_address = extended_id & 0x3FF
        self.__extended_id = extended_id

        # length will not be used
        seq.convertback32()  # length

        if self.__protocol_id == 3:
            return self.__init_from_syslog(seq, my_protocol_instance, my_cli_reference)

        self.__service_id = seq.convertback8()
        self.__message_id = seq.convertback8()

        self.__path_name = None
        for path in my_protocol_instance:
            path_entry = my_protocol_instance[path]
            if (
                path_entry.service_id == self.__service_id
                and path_entry.protocol_id == self.__protocol_id
            ):
                self.__protocol_name = path_entry.protocol_name
                self.__service_name = path_entry.service_name
                self.__path_name = (
                    path_entry.protocol_name + "/" + path_entry.service_name
                )
                break

        if self.__path_name == None:
            # message is likely to be a SYSLOG message with missing start:
            self.__path_name = "ServiceID=" + str(self.__service_id)
            self.__message_name = "MessageID=" + str(self.__message_id)
            self.__parameters = None
            self.__is_complete = True
            return

        self.__parameters = None
        for message in path_entry.message_map:
            message_entry = path_entry.message_map[message]
            if message_entry.id == self.__message_id:
                self.__message_name = message
                parameter_set_names = (
                    message_entry.parameter_description_list.parameter_name_list
                )
                parameter_set_formats = (
                    message_entry.parameter_description_list.parameter_type_list,
                )
                parameter_dimension_list = (
                    message_entry.parameter_description_list.dimension_list
                )
                self.__parameters = self.__parameters = Parameters(
                    seq,
                    parameter_set_names,
                    parameter_set_formats[0],
                    parameter_dimension_list,
                )
                break

        if self.__parameters == None:
            raise CCAN_Error(
                CCAN_ErrorCode.PROTOCOL_EVENT_INVALID,
                " HCAN event not known: \nservice: "
                + str(self.__service_id)
                + ", message id: "
                + str(self.__message_id)
                + "   - payload: "
                + str(seq.get_sequence()),
            )

        self.__is_complete = True

    ####
    #
    # see also libhcan++/transport_connection.cc
    # void transport_connection::syslog()
    #
    def __init_from_syslog(self, seq, my_protocol_instance, my_cli_reference):
        self.__protocol_name = "SYSLOG"
        self.__path_name = "SYSLOG"
        self.__parameters = None
        self.__service_name = "NO SERVICE"
        self.__event_name = "MESSAGE"

        continue_flag = False

        # check whether there is already a syslog message map:
        try:
            session_message_map = HCAN_Event.syslog_message_map[my_cli_reference]
        except KeyError:
            session_message_map = HCAN_Event.syslog_message_map[my_cli_reference] = {}

        # check whether the syslog message has been started and is continued with this event:
        try:
            (syslog_message_text, self.__priority) = session_message_map[
                self.__sender_address
            ]
            continue_flag = True
        except KeyError:
            syslog_message_text = ""
            self.__priority = seq.convertback8() & 0x111

        self.__message_name = ["", "CRITICAL", "ERROR", "Warning", "Info"][
            self.__priority
        ]

        data = seq.get_sequence()
        # print(data)
        end_detected = data[-1] == ord("\n")
        if end_detected is True:
            data.remove(ord("\n"))
        syslog_message_text += "".join([chr(letter) for letter in data])

        if end_detected:
            # finalize:
            self.__parameters = Parameters(
                [(None, syslog_message_text)], ["text"], ["STRING"]
            )
            if continue_flag is True:
                del session_message_map[self.__sender_address]
            self.__is_complete = True
        else:
            # store intermediate results:
            session_message_map[self.__sender_address] = (
                syslog_message_text,
                self.__priority,
            )
            self.__is_complete = False

    def __init_from_parsed_expression(
        self, my_raw_event, my_hcan_address, my_protocol_instance
    ):
        self._time_stamp = time.time()

        (self.__path_name, self.__message_name) = my_raw_event.get_event()
        path_entry = my_protocol_instance[self.__path_name]

        self._addressing_type = my_raw_event.get_addressing_type()
        self.__external_protocol_id = HCAN_Event.PROTOCOL_ID
        self.__protocol_id = path_entry.protocol_id
        self.__protocol_name = path_entry.protocol_name
        self.__service_id = path_entry.service_id
        message_entry = path_entry.message_map[self.__message_name]
        self.__message_id = message_entry.id

        self.__sender_address = my_hcan_address
        self.__destination_address = HCAN_Event.HCAN_MULTICAST_INFO

        my_seq = SequenceCreator()
        my_seq.convert8(self._addressing_type.get_key())
        my_seq.convert8(self.__external_protocol_id)

        # create HCAN IP Frame:

        # 1) extended id
        extended_id = (
            (self.__protocol_id << 20)
            + (self.__destination_address << 10)
            + self.__sender_address
        )
        my_seq.convert32(extended_id)

        # prepare parameters:
        parameter_set_names = (
            message_entry.parameter_description_list.parameter_name_list
        )
        parameter_set_formats = (
            message_entry.parameter_description_list.parameter_type_list,
        )
        parameter_dimension_list = (
            message_entry.parameter_description_list.dimension_list
        )
        self.__parameters = Parameters(
            my_raw_event.get_parameters(),
            parameter_set_names,
            parameter_set_formats[0],
            parameter_dimension_list,
        )

        # 2) length
        length = 2 + len(self.__parameters.get_sequence())
        my_seq.convert32(length)

        # 4) service and message id:
        my_seq.convert8(self.__service_id)
        my_seq.convert8(self.__message_id)

        # 5) parameters:
        my_seq.append(self.__parameters.get_sequence())

        self._seq = my_seq

    def get_sequence(self):
        return self._seq.get_sequence()

    def __eq__(self, my_hcan_event):
        if not isinstance(my_hcan_event, HCAN_Event):
            return False
        # equal sender & destination address remain unchecked
        try:
            assert self.__protocol_id == my_hcan_event.__protocol_id
            if self.__protocol_name == "SYSLOG":
                assert self.__parameter_list == my_hcan_event.__parameter_list
            else:
                assert self.__service_id == my_hcan_event.__service_id
                assert self.__message_id == my_hcan_event.__message_id
                assert self.__parameters == my_hcan_event.__parameters
                # if self.__parameters != None and my_hcan_event.__parameters != None:
                #    assert self.__parameters == my_hcan_event.__parameters
        except AssertionError:
            return False
        return True

    def get_sender_address(self):
        return None

    def get_parameters(self):
        return self.__parameters

    def get_parameter_values(self):
        if self.__parameters is not None:
            return self.__parameters.get_values()
        return None

    def __str__(self):
        if not self.__is_complete:
            return ""

        colors = self._get_colors()  # from raw event

        parameter_output = (
            self.__parameters.get_as_string(colors)
            if self.__parameters is not None
            else ""
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
            + colors.RED
            + "HCAN"
            + colors.END
            + " "
            +
            # if sender is 0, then this should not happen!
            (
                colors.MAGENTA
                + str(self.__sender_address)
                + " -> "
                + str(self.__destination_address)
                if self.__sender_address != 0
                else "[MAPPED]" + colors.END
            )
            + colors.END
            + " "
            + colors.GREEN
            + self.__path_name
            + "::"
            + self.__message_name
            + colors.END
            + parameter_output
            + binary_output
        )
