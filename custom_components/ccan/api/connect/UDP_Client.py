import socket
import time
import logging

from threading import Thread
from threading import Event
from .SocketConnect import SocketConnect
from api.base.PlatformDefaults import PlatformDefaults
from api.base.PlatformConfiguration import PlatformConfiguration
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

_LOGGER = logging.getLogger(__name__)


class UDP_Client:
    CLIENT_TIMED_OUT = 40
    SAFETY_BELT = 3

    def __init__(self, my_server_address):
        self.__management_socket = SocketConnect("PC", 0)
        self.__message_socket = SocketConnect("PC", 0)
        self.__server_address = my_server_address
        self.__message_address = None
        self.__ccan_address = PlatformDefaults.INVALID_CCAN_ADDRESS
        self.__is_connected = False

        self.__alive_thread = None
        self.__exit_event = Event()
        self.__timeout = 0.1

        self.__platform_configuration = PlatformConfiguration().get()
        self.__alive_thread: Thread = None

    def set_client_ccan_address(self, my_ccan_address):
        self.__ccan_address = my_ccan_address

    def connect(self, attempts=5):
        # start thread:
        while attempts > 0:
            self.__is_connected = self.__connect()
            if self.__is_connected:
                return True
            attempts -= 1

        raise CCAN_Error(CCAN_ErrorCode.SERVER_NOT_REACHABLE, "Could not connect.")

    def stay_connected(self):
        # start thread if connection has been established:
        if self.is_connected() and self.__alive_thread is None:
            self.__alive_thread = Thread(target=self.__connect_and_keep_alive_thread)
            self.__alive_thread.daemon = True
            self.__alive_thread.start()

    def receive(self, my_timeout):
        return self.__message_socket.receive(my_timeout)

    def send(self, my_message):
        self.__message_socket.send(my_message, self.__message_address)

    def get_ccan_address(self):
        return self.__ccan_address

    def is_connected(self):
        return self.__is_connected

    def who_is_connected(self):
        if not self.is_connected():
            return None
        request = self.__management_socket.create_command("WHO_IS_CONNECTED")
        self.__management_socket.send(request, self.__server_address)

        # wait for answer:
        answer_list = []
        while True:
            try:
                (message, address) = self.__management_socket.receive(self.__timeout)
                result = self.__management_socket.get_command(message)
                if result[0] == SocketConnect.LIST_OF_CONNECTIONS:
                    answer_list.append(result[1])
                elif result[0] == SocketConnect.LIST_OF_CONNECTIONS_END:
                    return answer_list
                else:
                    raise ValueError

            except TimeoutError:
                self.__is_connected = False
                return None

    def mask_client(self, my_client):
        if not self.is_connected():
            return []
        request = self.__management_socket.create_command("MASK_CLIENT", my_client)
        self.__management_socket.send(request, self.__server_address)
        return []

    def unmask_client(self, my_client):
        if not self.is_connected():
            return []
        request = self.__management_socket.create_command("UNMASK_CLIENT", my_client)
        self.__management_socket.send(request, self.__server_address)
        return []

    def disconnect(self):
        if self.__is_connected is True:
            self.__goodbye()
            self.__exit_event.set()  # terminate stay_connected Thread!
            time.sleep(self.__timeout + 0.1)

    def __connect_and_keep_alive_thread(self):
        while True:
            success = self.__connect()
            # _LOGGER.info("Reconnecting success:  %d", success)
            time.sleep(UDP_Client.CLIENT_TIMED_OUT - UDP_Client.SAFETY_BELT)
            if self.__exit_event.is_set() is True:
                "Alive Thread terminated on signal.."
                break

    def __connect(self):
        request = self.__management_socket.create_command(
            "AVAILABLE", ["PC", self.__message_socket.get_port(), self.__ccan_address]
        )

        address, port = self.__server_address
        if port == PlatformDefaults.INVALID_SERVER_PORT:
            result = self.__scan(self.__server_address)
            if result is None:
                self.__is_connected = False
                return False

        else:
            self.__management_socket.send(request, self.__server_address)

            # wait for answer:
            try:
                message, address = self.__management_socket.receive(self.__timeout)
                result = self.__management_socket.get_command(message)
            except TimeoutError:
                self.__is_connected = False
                return False

        if result[0] == SocketConnect.SERVER_ADDRESS_OFFER:
            self.__message_address = (self.__server_address[0], result[2])

        if self.__ccan_address == PlatformDefaults.INVALID_CCAN_ADDRESS:
            self.__ccan_address = result[1]

        if self.__ccan_address != PlatformDefaults.INVALID_CCAN_ADDRESS:
            self.__is_connected = True

        return True

    def __goodbye(self):
        request = self.__management_socket.create_command("GOODBYE")
        self.__management_socket.send(request, self.__server_address)

    def __scan(self, my_server_address):
        # scan range:
        request = self.__management_socket.create_command(
            "AVAILABLE", ["PC", self.__message_socket.get_port(), self.__ccan_address]
        )
        server_port_range = range(
            self.__platform_configuration["UDP_SERVER"]["MIN_PORT"],
            self.__platform_configuration["UDP_SERVER"]["MAX_PORT"] + 1,
        )

        for port in server_port_range:
            server_address = (my_server_address[0], port)
            self.__management_socket.send(request, server_address)

        try:
            (message, address) = self.__management_socket.receive(self.__timeout)
            self.__server_address = address
            return self.__management_socket.get_command(message)

        except TimeoutError:
            self.__is_connected = False
            return None

    def get_server_address(self):
        return self.__server_address
