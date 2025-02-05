from src.cli.interactions.Interaction import Interaction
from src.base.Report import Report, ReportLevel
from src.cli.interactions.controller.SwID import SwID
import time


class WaitForFirmware(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)       
        self._connector = my_connector
  
    def do(self):
        # wait for controller who may just start from reset
        time.sleep(1)

        # check current SW:
        try:
            result = SwID(self._connector, 1).do()
        except:
            time.sleep(1)
            result = SwID(self._connector, 1).do()
                   
        if result == 'FIRMWARE':
            return True # we are done
        else:
            # wait for Firmware startup:
            self._connector.wait_for_event(30,"LIFE_SERVICE::STARTUP_ENGINE()")
            return True


   