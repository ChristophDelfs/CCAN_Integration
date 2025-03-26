import time
from api.base.PlatformDefaults import PlatformDefaults
from api.base.Report import ReportLevel, Report
from api.base.CCAN_Error import CCAN_Error
from api.cli.interactions.Interaction import Interaction


class BroadcastInteraction(Interaction):
    DEFAULT_BROADCAST_WAITING_TIME = 0.3

    def __init__(self, my_connect, my_waiting_time, my_retries):
        super().__init__(my_connect, my_retries)

        self._connect = my_connect
        self._waiting_time = my_waiting_time
        self._end_loop = False
        self._collected_answers = []
        self._collected_values = {}
        self._retries = my_retries
        my_connect.set_destination_address(PlatformDefaults.BROADCAST_CCAN_ADDRESS)   

    def get_collected_anwers(self):
        return self._collected_answers

    def get_collected_values(self):
        return self._collected_values

    def terminate_loop(self):
        self._end_loop = True

    def do(self):
        if not isinstance(self._expected_answers, list):
            raise ValueError  # only lists are allowed!

        self._end_loop = False

        while not self._end_loop and self._retries != 0:
            self.before_send()

            # send:
            if self._request is not None:
                self._connect.send_event(self._request)

            # receive:
            start_time = time.time()
            remaining_time = self._waiting_time
            while remaining_time > 0:
                try:
                   
                    received_event, index = self._connect.wait_for_event_list(
                        remaining_time, self._expected_answers
                    )

                    self._end_loop = (
                        self.on_receive(received_event, index) or self._end_loop
                    )
                    if self._end_loop:
                        break

                    self._collected_values[received_event.get_sender_address()] = (
                        received_event.get_parameters().get_values()
                    )
                    self._collected_answers.append((received_event, index))
                except CCAN_Error as ex:
                    pass

                remaining_time = start_time + self._waiting_time -time.time()
            self._retries -= 1

            # react in iteration end:
            self.on_iteration_end()

        # return final processing
        return self.on_loop_end()

    def on_iteration_end(self):
        raise NotImplementedError

    def before_send(self):
        raise NotImplementedError

    def on_receive(self, my_index, my_received_event):
        raise NotImplementedError

    def on_receive_failure(self, my_exception):
        raise NotImplementedError

    def on_loop_end(self):
        raise NotImplementedError


