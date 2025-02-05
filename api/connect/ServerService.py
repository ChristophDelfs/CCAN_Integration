from src.events.EventResolver import EventResolver
from src.events.ApplicationEvent import ApplicationEvent
from binascii import crc32
from src.base.PlatformDefaults import PlatformDefaults


class ServerService:
    def __init__(self, my_ccan_address, my_address_server):
        self.__event_resolver = EventResolver()
        self.__address_server = my_address_server

        self.__event_resolver.set_own_address(my_ccan_address)
        self.__event_resolver.set_destination_address(0)

        self.__connected_boards = {}

    def handle_message(self, my_message):
        result = self.__event_resolver.resolve_binary_event(my_message)

        if isinstance(result, ApplicationEvent) is False:
            return None

        if result.get_service() == "CONFIG_SERVICE":
            if result.get_event_name() == "REQUEST_ADDRESS":
                uuid = result.get_parameter_values()[0]

                try:
                    crc_uuid = crc32(bytes(uuid))
                    address = self.__connected_boards[crc_uuid]

                except KeyError:
                    try:
                        address = self.__address_server.allocate()
                        self.__connected_boards[crc_uuid] = address
                    except IndexError:
                        address = PlatformDefaults.INVALID_CCAN_ADDRESS

                answer = (
                    "CONFIG_SERVICE::REQUEST_ADDRESS_REPLY("
                    + str(uuid)
                    + ", "
                    + str(address)
                    + " )"
                )
                self.__event_resolver.set_destination_address(
                    result.get_sender_address()
                )
                resolved_answer = self.__event_resolver.resolve_event(answer)
                binary_sequence = bytes(resolved_answer.get_sequence())
                return binary_sequence
        return None
