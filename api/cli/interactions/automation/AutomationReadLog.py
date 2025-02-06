from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.events.RawEvent import RawEvent
import os

from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)


class AutomationReadLog(AutomationInteraction): 
    def __init__(self,  my_connector, my_waiting_time, my_retries,  my_file, my_automation_file):                             
        self._file = my_file
        self._connector = my_connector     
        super().__init__(my_connector,  my_waiting_time, my_retries, my_automation_file)      

               
    def do(self):

        # open log file:
        if self._file == False:
            log_filename = os.path.basename(self._connector.get_automation_filename())
        else:
            log_filename = self._file

        log_path = self._platform_configuration["LOG_FILES"]["PATH"]
        full_path = os.sep.join([os.environ["CCAN"],log_path, log_filename+".log"]) 


        # open log file:
        self._log_file = open(full_path, 'rb')           
        self._connector._read(self._log_file)
        counter = 0

        while True:
            raw_event = RawEvent.restore_state_from_file(self._log_file)
            if raw_event == False:
                break           
          
            resolved_event = self._connector.resolve_raw_event(raw_event)    
            resolved_event.print_with_colors(True)    
            counter +=1
            Report.print(ReportLevel.VERBOSE,'#{:<8}:  '.format(counter) + str(resolved_event)+"\n")
           
     

