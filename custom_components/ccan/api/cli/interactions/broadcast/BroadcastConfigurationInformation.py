import time

from api.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction

# from .....api.base.PlatformServices import PlatformServices
from api.base.PlatformDefaults import PlatformDefaults
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode


class BroadcastConfigurationInformation(BroadcastInteraction):
    def __init__(self, my_connector, my_waiting_time, my_retries):
        super().__init__(my_connector, my_waiting_time, my_retries)

    def do(self):
        self.set_request(
            "CONFIG_SERVICE::INFO_REQUEST("
            + str(PlatformDefaults.UPDATE_SECTION_CONFIGURATION)
            + ")"
        )
        self.set_expected_answers(["CONFIG_SERVICE::CONFIGURATION_INFO()"])
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
        result = {}
        if len(list(receivers)) > 0:
            Report.print(
                ReportLevel.VERBOSE,
                f"{'Address':10}" + f"{'Version':10}" + f"{'Date':15}"
                f"{'Filename':60}"
                "\n",
            )
            for receiver in sorted(list(receivers)):
                version = [None] * 3
                version[0], version[1], version[2], date, raw_filename = (
                    collected_parameters[receiver]
                )

                version_string = (
                    str(version[0]) + "." + str(version[1]) + "." + str(version[2])
                )
                config_date = time.localtime(date)
                config_date_string = (
                    str(config_date.tm_mday)
                    + "."
                    + str(config_date.tm_mon)
                    + "."
                    + str(config_date.tm_year)
                )
                filename = raw_filename.replace('"', "")
                if len(filename) != 0:
                    Report.print(
                        ReportLevel.VERBOSE,
                        "{:<10}".format(receiver)
                        + f"{version_string:10}"
                        + f"{config_date_string:15}"
                        + f"{filename:60}"
                        + "\n",
                    )
                else:
                    Report.print(
                        ReportLevel.VERBOSE,
                        "{:<10}".format(receiver)
                        + f"{version_string:10}"
                        + f"{'':15}"
                        + f"{'Default Configuration':60}"
                        + "\n",
                    )
                result[receiver] = (version, config_date, filename)
        else:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)
            return None

        return result
