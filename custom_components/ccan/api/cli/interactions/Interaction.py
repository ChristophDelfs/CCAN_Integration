import signal
import os
import time
from pathlib import Path

from api.base.CCAN_Error import CCAN_Error
from api.base.CCAN_Defaults import CCAN_Defaults
from api.base.PlatformConfiguration import PlatformConfiguration
from api.base.Report import Report, ReportLevel


class Interaction:
    timeout = 0.2
    ENDLESS_RETRIES = -1

    def __init__(self, my_connector, my_retries, my_waiting_time=0):
        self._connector = my_connector
        self._end_loop = False
        self._retries = my_retries
        self._waiting_time = (
            my_waiting_time if my_waiting_time != 0 else Interaction.timeout
        )

        self._ccan_defaults = CCAN_Defaults()
        default_file = PlatformConfiguration.DEFAULT_DEFINITIONS_FILENAME()
        self._ccan_defaults.init_from_pkl(default_file)

        self._platform_configuration = PlatformConfiguration().get()
        # signal.signal(signal.SIGINT, self.on_interrupt)

    def set_request(self, my_request):
        if my_request != None:
            self._request = self._connector.resolve_event(my_request)
        else:
            self._request = None

    def set_expected_answers(self, my_answers):
        if my_answers == None:
            self._expected_answers = None
            return

        if isinstance(my_answers, list) is False:
            my_answers = [my_answers]
        self._expected_answers = []
        for answer in my_answers:
            if answer != None:
                self._expected_answers.append(self._connector.resolve_event(answer))
            else:
                self._expected_answers.append(None)

    def terminate_loop(self):
        self._end_loop = True

    def get_defaults(self):
        return self._ccan_defaults

    def do(self):
        end_loop = False

        while (self._retries != 0) and self._end_loop == False:
            self.before_send()

            # send:
            if self._request != None:
                self._connector.send_event(self._request)

            # receive:
            try:
                if isinstance(self._expected_answers, list):
                    received_event, index = self._connector.wait_for_event_list(
                        self._waiting_time, self._expected_answers
                    )
                else:
                    received_event = self._connector.receive_event(self._waiting_time)
                    index = -1

                # react on success:
                self._end_loop = (
                    self.on_receive(received_event, index) or self._end_loop
                )

            except CCAN_Error as ex:
                # react on failure:
                self.on_receive_failure(ex)

            if self._retries > 0:
                self._retries -= 1

            if self._retries > 0:
                time.sleep(self._platform_configuration["RETRY_WAITING_TIME"])

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

    def on_interrupt(self, my_signal, frame):
        Report.print(ReportLevel.WARN, "\nInterrupted by user..\n")
        quit()
