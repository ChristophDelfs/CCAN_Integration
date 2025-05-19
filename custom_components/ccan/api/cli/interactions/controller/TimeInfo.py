from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class TimeInfo(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)
        self._average_load_during_list_minute = 0
        self._maximum_load_during_last_minute = 0
        self._connector = my_connector
  
    def do(self):
        
        self.set_request("LIFE_SERVICE::TIME_REQUEST()")
        self.set_expected_answers(["LIFE_SERVICE::TIME_REPLY()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        self.__time = my_received_event.get_parameters().get_values()[0]
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.SERVICE_NOT_SUPPORTED)
         

    def on_iteration_end(self):
        return

    def on_loop_end(self):        
        # controller time is (!) local time. to be interpreted as UTC, otherwise Python will "correct" it.
        date = datetime.fromtimestamp(self.__time, timezone.utc)
        Report.print(ReportLevel.VERBOSE,f"Controller time is {date} \n")

        return self.__time
    
   