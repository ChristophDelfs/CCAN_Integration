import time

from threading import Thread
from threading import Event
from threading import Lock

import logging
# from src.UDP_Client import UDP_Client

from .SocketConnect import SocketConnect
from .AddressManager import AddressManager

from .ServerService import ServerService
from src.base.PlatformDefaults import PlatformDefaults

from src.base.PlatformConfiguration import PlatformConfiguration


class UDP_Server:
    BUFFER_SIZE = 1200

    CLIENT_TIME_OUT = 70

    CLIENT_ADDRESS_BASE = 1024
    SERVER_CCAN_ADDRESS = 1023
    FREE_ADDRESSES = 256

    SOCKET_WAITING_TIME = 0.1

    def __init__(self, port=PlatformDefaults.INVALID_SERVER_PORT, client_time_out=None):
        self.__defaults = PlatformConfiguration().get()

        # ensures that these variables are initialized even if later an exception is thrown:
        if port is PlatformDefaults.INVALID_SERVER_PORT:
            port = self.__defaults["UDP_SERVER"]["DEFAULT_PORT"]

        self.__management_socket = None
        self.__message_socket = None

        # create sockets, might lead to an exception:
        try:
            self.__management_socket = SocketConnect("PC", port)
            self.__message_socket = SocketConnect("PC")
        except Exception:
            exit(0)

        self.__thread_count = 0

        self.__lock = Lock()

        self.__list_of_clients = []
        self.__list_of_message_clients = []
        self.__client_alive_counter = []
        self.__client_offered_address = []
        self.__client_types = []
        self.__list_of_masked_clients = []
        self.__address_manager = AddressManager(
            UDP_Server.CLIENT_ADDRESS_BASE,
            UDP_Server.CLIENT_ADDRESS_BASE + UDP_Server.FREE_ADDRESSES,
        )

        if client_time_out is None:
            self.__client_time_out = (
                UDP_Server.CLIENT_TIME_OUT / UDP_Server.SOCKET_WAITING_TIME
            )
        else:
            self.__client_time_out = client_time_out / UDP_Server.SOCKET_WAITING_TIME

        self.__server_service = ServerService(
            UDP_Server.SERVER_CCAN_ADDRESS, self.__address_manager
        )

        self.__exit_event = Event()

    def __del__(self):
        if self.__management_socket is not None:
            del self.__management_socket
        if self.__message_socket is not None:
            del self.__message_socket

    def get_number_of_free_client_slots(self):
        return UDP_Server.FREE_ADDRESSES - len(self.__list_of_clients)

    def run(self):
        # start threads:
        self.__message_thread = Thread(target=self.__propagate_messages_thread)
        self.__message_thread.daemon = True
        self.__message_thread.start()

        self.__handle_clients_thread = Thread(target=self.__handle_clients)
        self.__handle_clients_thread.daemon = True
        self.__handle_clients_thread.start()

        self.__handle_management_requests = Thread(
            target=self.__handle_management_requests
        )
        self.__handle_management_requests.daemon = True
        self.__handle_management_requests.start()

    def shutdown(self):
        self.__exit_event.set()

        while self.__thread_count > 0:
            time.sleep(UDP_Server.SOCKET_WAITING_TIME)

        del self.__message_thread
        del self.__handle_clients_thread
        del self.__handle_management_requests

    def __handle_management_requests(self):
        self.__thread_count += 1
        while True:
            try:
                if self.__exit_event.is_set() is True:
                    break
                (message, address) = self.__management_socket.receive(
                    UDP_Server.SOCKET_WAITING_TIME
                )
            except TimeoutError:
                continue

            result = self.__management_socket.get_command(message)
            if not result:
                continue

            command = result[0]
            if command == SocketConnect.CLIENT_AVAILABLE:
                client_type = result[1]
                client_message_port = result[2]
                ccan_address_available = result[3]
                logging.debug("Address available " + str(ccan_address_available))
                self.__add_or_update_client(
                    client_message_port, client_type, address, ccan_address_available
                )
            elif command == SocketConnect.CLIENT_GOODBYE:
                self.__remove_client(address)

            elif command == self.__management_socket.WHO_IS_CONNECTED:
                self.__who_is_connected(address)

            elif command == self.__management_socket.MASK_CLIENT:
                self.__mask_client(result[1])

            elif command == self.__management_socket.UNMASK_CLIENT:
                self.__unmask_client(result[1])

            else:
                # ignore "command"
                pass
        self.__thread_count -= 1

    def __add_or_update_client(
        self,
        my_client_message_port,
        my_client_type,
        my_address,
        my_ccan_address_available,
    ):
        self.__lock.acquire()
        try:
            client_index = self.__list_of_clients.index(my_address)
        except ValueError:
            client_index = -1

        if my_ccan_address_available == PlatformDefaults.INVALID_CCAN_ADDRESS:
            try:
                offered_address = self.__address_manager.allocate()
            except IndexError:
                logging.error("Could not allocate new address for unconfigured client.")
                offered_address = PlatformDefaults.INVALID_CCAN_ADDRESS
        else:
            offered_address = my_ccan_address_available

        # new client:
        if client_index == -1:
            # add management address
            self.__list_of_clients.append(my_address)
            # add message address:
            self.__list_of_message_clients.append(
                (my_address[0], my_client_message_port)
            )

            logging.warning(
                "ADDED : Client with management port: "
                + str(my_address[1])
                + ", message port "
                + str(my_client_message_port)
                + " and CCAN address "
                + str(offered_address)
                + " added."
            )

            # add alive counter:
            self.__client_alive_counter.append(0)
            # add atribute:
            self.__client_types.append(my_client_type)
            # and offered address:
            self.__client_offered_address.append(offered_address)

            # send to client:
            server_response = self.__management_socket.create_command(
                "SERVER_ADDRESS_OFFER",
                [offered_address, self.__message_socket.get_port()],
            )

        # known client:
        else:
            # reset alive counter:
            self.__client_alive_counter[client_index] = 0

            # respond anyway:
            offered_address = self.__client_offered_address[client_index]
            server_response = self.__management_socket.create_command(
                "SERVER_ADDRESS_OFFER",
                [offered_address, self.__message_socket.get_port()],
            )
            logging.info("Client " + str(my_address) + " still alive.")
            # print("Client with management port: " + str(my_address[1]) + " and message port " + str(my_client_message_port) + " confirmed.")

        self.__management_socket.send(server_response, my_address)
        self.__lock.release()

    def __who_is_connected(self, my_address):
        list_of_clients = self.__server_service.get_connected_boards()
        for client in list_of_clients:
            server_response = self.__management_socket.create_command(
                "LIST_OF_CONNECTIONS", client
            )
            self.__management_socket.send(server_response, my_address)
        server_response = self.__management_socket.create_command(
            "LIST_OF_CONNECTIONS_END"
        )
        self.__management_socket.send(server_response, my_address)

    def __remove_client(self, my_address):
        # find client:
        try:
            client_index = self.__list_of_clients.index(my_address)
        except ValueError:
            logging.warn("Client could not be removed - already done")
            return

        self.__remove_client_via_index(client_index)

    def __remove_client_via_index(self, my_index):
        self.__lock.acquire()
        # remove from lists:
        removed_client = self.__list_of_clients.pop(my_index)
        self.__list_of_message_clients.pop(my_index)
        self.__client_alive_counter.pop(my_index)
        self.__client_types.pop(my_index)

        offered_address = self.__client_offered_address[my_index]
        if (
            offered_address != PlatformDefaults.INVALID_CCAN_ADDRESS
            and self.__address_manager.is_allocated_address(offered_address)
        ):
            logging.info("Released address: " + str(offered_address))
            self.__address_manager.free(offered_address)
        self.__client_offered_address.pop(my_index)

        address = str(removed_client[0])
        port = str(removed_client[1])
        logging.warning(
            "REMOVED / GOODBYE : Client with IP address "
            + address
            + " and port "
            + port
            + " which used CCAN address "
            + str(offered_address)
            + " said goodbye - "
            + str(len(self.__list_of_message_clients))
            + " message clients still remain."
        )
        self.__lock.release()

    ## Threads:

    def __propagate_messages_thread(self):
        self.__thread_count += 1
        while True:
            try:
                if self.__exit_event.is_set() is True:
                    break
                (message, address) = self.__message_socket.receive(
                    UDP_Server.SOCKET_WAITING_TIME
                )
            except TimeoutError:
                continue

            logging.info("Message from " + str(address) + " received.")

            # skip over messages from masked clients:
            if address[0] in self.__list_of_masked_clients:
                logging.info(
                    "Message from client" + str(address[0]) + " ignored due to masking."
                )
                continue

            self.__lock.acquire()
            try:
                work_list = self.__list_of_message_clients.copy()
                work_list.remove(address)
            except ValueError:
                # client has been removed, e.g. timed out on the management port,
                # but still ships events on the message port
                # this is a bug in the client.
                logging.warning(
                    "SPOOKY: Client with message address "
                    + str(address)
                    + " timed out or sent goodbye, but still ships messages. Please check your client to reconnect properly."
                )
            self.__lock.release()

            if work_list != []:
                for receiver in work_list:
                    receiver_ip_address = receiver[0]
                    if receiver_ip_address not in self.__list_of_masked_clients:
                        self.__message_socket.send(message, receiver)
                        logging.debug("propagated to " + str(receiver))
                    # print("propagated to " +str(len(self.__list_of_clients)) + " clients")
            else:
                logging.debug("Message not propagated. No additional client available.")

            # handle SERVER_SERVICE message if needed:

            reply = self.__server_service.handle_message(message)

            if reply is not None and self.__list_of_message_clients != []:
                for receiver in self.__list_of_message_clients:
                    receiver_ip_address = receiver[0]
                    self.__message_socket.send(reply, receiver)
                    logging.debug("server service reply propagated to " + str(receiver))

        self.__thread_count -= 1

    def __handle_clients(self):
        self.__thread_count += 1
        while True:
            if len(self.__client_alive_counter) > 0:
                # increment age of all clients:
                self.__client_alive_counter = [
                    counter + 1 for counter in self.__client_alive_counter
                ]

                # get all clients which timed out:

                timed_out_clients = [
                    index
                    for index in range(len(self.__client_alive_counter))
                    if self.__client_alive_counter[index] >= self.__client_time_out
                ]
                if len(timed_out_clients) > 0:
                    timed_out_clients.sort(reverse=True)
                    for client_index in timed_out_clients:
                        # print("Entferne Element mit Index " + str(client_index))
                        address = str(self.__list_of_message_clients[client_index][0])
                        port = str(self.__list_of_message_clients[client_index][1])
                        logging.warn(
                            "REMOVED / TIMEOUT : Client with address "
                            + address
                            + " and port "
                            + port
                            + " - timed out."
                        )
                        self.__remove_client_via_index(client_index)

            time.sleep(UDP_Server.SOCKET_WAITING_TIME)
            if self.__exit_event.is_set() is True:
                break
        self.__thread_count -= 1

    def __mask_client(self, my_client):
        self.__list_of_masked_clients.append(my_client)
        logging.warning(
            "MASKED : Client "
            + my_client
            + " will not receive messages. Messages from this client will not be routed."
        )

    def __unmask_client(self, my_client):
        try:
            self.__list_of_masked_clients = list(
                filter((my_client).__ne__, self.__list_of_masked_clients)
            )
            logging.warning(
                "UNMASKED: Client "
                + str(my_client)
                + " has been unmasked. Messages will be accepted from & routed to this client."
            )
        except ValueError:
            logging.warning(
                "UNMASKED: Client "
                + str(my_client)
                + " has not been masked so far. Message handling remains unchanged."
            )
