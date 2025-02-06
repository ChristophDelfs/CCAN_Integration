from pydoc import doc
import socket
import select
from ..PyCCAN_ConvertBinary import SequenceExtractor, SequenceCreator


class SocketConnect:
    __BUFFER_SIZE = 1200

    CONNECT_COMMAND = 99

    CLIENT_AVAILABLE = 0
    CLIENT_ALIVE = 1
    CLIENT_GOODBYE = 2
    SERVER_ADDRESS_OFFER = 3
    WHO_IS_CONNECTED = 4
    LIST_OF_CONNECTIONS = 5
    LIST_OF_CONNECTIONS_END = 6
    MASK_CLIENT = 7
    UNMASK_CLIENT = 8

    CLIENT_TYPE = {}
    CLIENT_TYPE["PC"] = 0
    CLIENT_TYPE["EMBEDDED"] = 1

    def create_command(self, my_request, my_param=None):
        seq = SequenceCreator()
        seq.convert8(SocketConnect.CONNECT_COMMAND)
        if my_request == "AVAILABLE":
            seq.convert8(SocketConnect.CLIENT_AVAILABLE)
            seq.convert8(SocketConnect.CLIENT_TYPE[my_param[0]])
            seq.convert16(my_param[1])
            seq.convert16(my_param[2])
        elif my_request == "ALIVE":
            seq.convert8(SocketConnect.CLIENT_ALIVE)
        elif my_request == "GOODBYE":
            seq.convert8(SocketConnect.CLIENT_GOODBYE)
        elif my_request == "SERVER_ADDRESS_OFFER":
            seq.convert8(SocketConnect.SERVER_ADDRESS_OFFER)
            for value in my_param:
                seq.convert16(int(value))
        elif my_request == "WHO_IS_CONNECTED":
            seq.convert8(SocketConnect.WHO_IS_CONNECTED)
        elif my_request == "LIST_OF_CONNECTIONS":
            seq.convert8(SocketConnect.LIST_OF_CONNECTIONS)
            for value in my_param:
                seq.convert16(int(value))
        elif my_request == "LIST_OF_CONNECTIONS_END":
            seq.convert8(SocketConnect.LIST_OF_CONNECTIONS)
        elif my_request == "MASK_CLIENT":
            seq.convert8(SocketConnect.MASK_CLIENT)
            seq.convert_string(my_param)

        elif my_request == "UNMASK_CLIENT":
            seq.convert8(SocketConnect.UNMASK_CLIENT)
            seq.convert_string(my_param)

        else:
            raise ValueError
        return bytes(list(seq.get_sequence()))

    def __init__(self, my_type, port=0):
        self.__socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        self.__type = SocketConnect.CLIENT_TYPE[my_type]

        try:
            self.__socket.bind(("0.0.0.0", port))
            self.__port = self.__socket.getsockname()[1]
        except Exception:
            print("Another instance is running.. bailing out")
            raise ValueError
        self.__socket.setblocking(True)

    def __del__(self):
        # free port:
        del self.__socket

    def get_port(self):
        return self.__port

    def receive(self, my_timeout):
        if my_timeout is not None:
            self.__socket.settimeout(my_timeout)
            (message, address) = self.__socket.recvfrom(SocketConnect.__BUFFER_SIZE)
            return (message, address)
            # self.__socket.setblocking(False)
            # ready = select.select([self.__socket], [], [], my_timeout)
            # if ready[0]:
            #    (message, address) = self.__socket.recvfrom(SocketConnect.__BUFFER_SIZE)
            #    return (message, address)
            # raise TimeoutError

        self.__socket.setblocking(True)
        (message, address) = self.__socket.recvfrom(SocketConnect.__BUFFER_SIZE)
        return (message, address)

    def send(self, my_message, my_address):
        self.__socket.setblocking(True)
        self.__socket.sendto(my_message, my_address)

    def get_command(self, message):
        seq = SequenceExtractor(list(message))
        addressing = seq.convertback8()
        if addressing != SocketConnect.CONNECT_COMMAND:
            return False

        command = seq.convertback8()

        if command == SocketConnect.SERVER_ADDRESS_OFFER:
            offered_address = seq.convertback16()
            message_port = seq.convertback16()
            return [command, offered_address, message_port]

        if command == SocketConnect.CLIENT_AVAILABLE:
            client_type = seq.convertback8()
            message_port = seq.convertback16()
            address_available = seq.convertback16()
            return [command, client_type, message_port, address_available]

        if command == SocketConnect.CLIENT_GOODBYE:
            return [command]

        if command == SocketConnect.WHO_IS_CONNECTED:
            return [command]

        if command == SocketConnect.LIST_OF_CONNECTIONS:
            list_of_connections = []
            while not seq.is_empty():
                list_of_connections.append(seq.convertback16())
            return [command, list_of_connections]

        if (
            command == SocketConnect.MASK_CLIENT
            or command == SocketConnect.UNMASK_CLIENT
        ):
            client = seq.convertback_string()
            return [command, client]

        raise ValueError
