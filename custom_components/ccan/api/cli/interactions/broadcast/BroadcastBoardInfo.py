from api.cli.interactions.broadcast.BroadcastInteraction import (
    BroadcastInteraction,
)
from api.base.Report import Report, ReportLevel
from api.base.PlatformServices import PlatformServices

# from .....api.base.CCAN_Defaults import CCAN_Defaults
import time


class BroadcastBoardInfo(BroadcastInteraction):
    def __init__(self, my_connector, my_waiting_time, my_retries):
        super().__init__(my_connector, my_waiting_time, my_retries)
        self.__connector = my_connector
        self.__received_info = {}

    def do(self):
        self.set_request("CONFIG_SERVICE::SHORT_INFO_REQUEST()")
        self.set_expected_answers(["CONFIG_SERVICE::SHORT_INFO_REQUEST_REPLY()"])
        return super().do()

    def before_send(self):
        pass

    def on_receive(self, my_received_event, my_index):
        return False

    def on_iteration_end(self):
        pass

    def on_loop_end(self):
        collected_parameters = self.get_collected_values()
        receivers = list(collected_parameters)
        receivers.sort()
        if len(list(receivers)) > 0:
            Report.print(
                ReportLevel.VERBOSE,
                f"{'Controller Board':25}" + f"{'Address':10}" + "UUID" + "\n",
            )
            for receiver in sorted(list(receivers)):
                uuid, controller_crc = collected_parameters[receiver]
                controller_type = self.get_defaults().get_controller_from_crc(
                    controller_crc
                )
                uuid_string = PlatformServices.uuid_to_string(uuid)
                Report.print(
                    ReportLevel.VERBOSE,
                    f"{controller_type:25}"
                    + "{:<10}".format(receiver)
                    + uuid_string
                    + "\n",
                )
        else:
            Report.print(
                ReportLevel.VERBOSE,
                "CCAN Network is down or no controllers are available.\n",
            )
        return collected_parameters
