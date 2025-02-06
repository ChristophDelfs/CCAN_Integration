import time
import datetime
import struct
import copy

from api.PyCCAN_ConvertBinary import SequenceExtractor
from api.resolver.Definitions import Colors, NoColors


class AddressingType:
    Key = {}
    Key["DEVICE_EVENT_ADDRESSING"] = 0
    Key["DIRECT_EVENT_ADDRESSING"] = 1
    Key["INDIRECT_EVENT_ADDRESSING"] = 2
    Key["OUTBOUND_EVENT_ADDRESSING"] = 4
    Key["APPLICATION_EVENT_ADDRESSING"] = 10
    Key["PROTOCOL_EVENT_ADDRESSING"] = 20

    def __init__(self, my_value):
        if isinstance(my_value, str):
            self._key = AddressingType.Key[my_value]
            self._string = my_value
            return
        for key_string in AddressingType.Key:
            key = AddressingType.Key[key_string]
            if key == my_value:
                self._key = key
                self._string = key_string
                return
        print("Raw event with value" + str(my_value) + "could not be processed.")
        raise Exception

    def is_device_event(self):
        return self._key == AddressingType.Key["DEVICE_EVENT_ADDRESSING"]

    def is_application_event(self):
        return self._key == AddressingType.Key["APPLICATION_EVENT_ADDRESSING"]

    def is_external_protocol_event(self):
        return self._key == 20

    def get_key(self):
        return self._key

    def __str__(self):
        if self._string == "DEVICE_EVENT_ADDRESSING":
            return "DEVICE "
        if self._string == "DIRECT_EVENT_ADDRESSING":
            return "DIRECT "
        if self._string == "INDIRECT_EVENT_ADDRESSING":
            return "INDIRECT"
        if self._string == "APPLICATION_EVENT_ADDRESSING":
            return "APPLICATION"
        if self._string == "PROTOCOL_EVENT_ADDRESSING":
            return "PROTOCOL"
        raise TypeError


class RawEvent:
    def __init__(self, data=None):
        if data != None:
            seq = SequenceExtractor(data)
            self._orig_seq = copy.deepcopy(seq)

            self._time_stamp = time.time()
            self._addressing_type = AddressingType(seq.convertback8())
            self._payload = seq.get_sequence()
            self._hex_mode = False

        self._colors = Colors

    def get_time_stamp(self):
        return self._time_stamp

    def set_hex_mode(self):
        self._hex_mode = True

    def get_addressing_type(self):
        return self._addressing_type

    def get_payload(self):
        return self._payload

    def get_event_age(self):
        return time.time() - self._time_stamp

    def __str__(self):
        millis = round((self._time_stamp - int(self._time_stamp)) * 1000)
        result = (
            datetime.datetime.fromtimestamp(self._time_stamp).strftime(
                "%a, %d %b %Y %H:%M:%S"
            )
            + "."
            + str(millis).zfill(3)
            + " ["
            + str(self._addressing_type)
            + "]"
        )
        return result

    def print_with_colors(self, my_color_choice):
        if my_color_choice == True:
            self._colors = Colors
        else:
            self._colors = NoColors

    def get_sequence(self):
        return self._orig_seq

    def _get_colors(self):
        return self._colors

    def add_binary_state_to_file(self, my_file):
        time_stamp = struct.pack("=d", self._time_stamp)
        addressing_type = struct.pack("=B", self._addressing_type.get_key())

        payload = struct.pack("=%sB" % len(self._payload), *self._payload)
        length = struct.pack("=H", len(payload))

        my_file.write(time_stamp + addressing_type + length + payload)

    def restore_state_from_file(my_file):
        buffer = my_file.read(8)
        if len(buffer) == 0:
            return False

        time_stamp = struct.unpack("=d", buffer)[0]
        buffer = my_file.read(1)
        addressing_type = struct.unpack("=B", buffer)[0]

        buffer = my_file.read(2)
        length = struct.unpack("=H", buffer)[0]
        buffer = my_file.read(length)
        payload = list(struct.unpack("=%sB" % length, buffer))

        data = [addressing_type] + payload
        result = RawEvent(data)
        result.print_with_colors(True)

        result._time_stamp = time_stamp
        return result
