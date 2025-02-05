from src.cli.interactions.controller.SimpleInteraction import SimpleInteraction
from src.cli.interactions.controller.Reset import Reset
import time

class EraseConfiguration(SimpleInteraction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries, request="CONFIG_SERVICE::ERASE_CONFIG()",
                                                   answer= "CONFIG_SERVICE::ERASE_CONFIG_ACK()",
                                                   success_message="Configuration has been erased. Default configuration is active now.\n" )     
        self._retries = my_retries  
        self._connector = my_connector  
  
    def do(self):    
        Reset(self._connector,self._retries, my_wait_for_startup = True).do()    
        # wait for an unconfigured client to get an address:
        time.sleep(2)
        return super().do()
