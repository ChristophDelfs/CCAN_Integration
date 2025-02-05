from src.cli.interactions.broadcast.SimpleBroadcastInteraction import SimpleBroadcastInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode


class BroadcastDisableApplicationEventsOnly(SimpleBroadcastInteraction):
    def __init__(self, my_connector, my_waiting_time, my_retries):
        super().__init__(
            my_connector,
            my_waiting_time,
            my_retries,
            "ENGINE_SERVICE::DISABLE_APPLICATION_EVENTS_ONLY()",
            "ENGINE_SERVICE::DISABLE_APPLICATION_EVENTS_ONLY_ACK()",
            "Controllers will react on all events again.'Application events only' mode is off.\n",
        )

    def do(self):
        return super().do()
