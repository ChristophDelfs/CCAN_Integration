from api.cli.interactions.broadcast.SimpleBroadcastInteraction import SimpleBroadcastInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class BroadcastEnableApplicationEventsOnly(SimpleBroadcastInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries): 
        
        super().__init__(my_connector, my_waiting_time, my_retries,
                            "ENGINE_SERVICE::ENABLE_APPLICATION_EVENTS_ONLY()", 
                            "ENGINE_SERVICE::ENABLE_APPLICATION_EVENTS_ONLY_ACK()",
                            "'Application events only' mode has been enabled. The listed controllers now ignore every event which is not an application event:\n")                            
        
    def do(self):     
        return super().do()