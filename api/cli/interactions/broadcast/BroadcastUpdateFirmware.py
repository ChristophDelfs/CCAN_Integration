from src.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from src.base.Report import Report, ReportLevel
from src.base.PlatformServices import PlatformServices
from src.base.CCAN_Defaults import CCAN_Defaults
from src.cli.interactions.broadcast.BroadcastPing import BroadcastPing
from src.cli.interactions.controller.UpdateFirmware import UpdateFirmware
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
import time

class BroadcastUpdateFirmware(BroadcastInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries): 
        
        super().__init__(my_connector, my_waiting_time, my_retries)        
        self._connector = my_connector
        self._waiting_time = my_waiting_time
        self._retries = my_retries
    

    def do(self):     
        Report.push_level(ReportLevel.WARN)
        pings, losses, average_times = BroadcastPing(self._connector, self._waiting_time, 1, 0.5).do()
        Report.pop_level()
        Report.print(ReportLevel.VERBOSE,"Updating firmware for controllers " + str(list(pings.keys())) + "\n")
        for address in pings:
            Report.print(ReportLevel.VERBOSE,"Updating controller with address " + str(address) + "..\n")
            self._connector.set_destination_address(address)
            try:
                UpdateFirmware(self._connector, self._retries).do()
            except CCAN_Error as ccan_error:
                if ccan_error.get_code() != CCAN_ErrorCode.TARGET_UP_TO_DATE:
                    raise ccan_error
                else:
                    print(ccan_error)
                    time.sleep(25)
            
        