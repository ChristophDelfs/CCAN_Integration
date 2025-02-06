from api.cli.interactions.broadcast.SimpleBroadcastInteraction import SimpleBroadcastInteraction

class BroadcastEraseConfiguration(SimpleBroadcastInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries): 
        
        super().__init__(my_connector, my_retries, request="CONFIG_SERVICE::ERASE_CONFIG()",
                                                   answer= "CONFIG_SERVICE::ERASE_CONFIG_ACK()",
                                                   success_message="Configuration has been erased. Default configuration is active now." )  
   

    def do(self):        
       return super().do()