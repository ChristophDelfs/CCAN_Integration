from src.cli.interactions.controller.SimpleInteraction import SimpleInteraction

class EnableApplicationEventsOnly(SimpleInteraction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries, 
                            "ENGINE_SERVICE::ENABLE_APPLICATION_EVENTS_ONLY()", 
                            "ENGINE_SERVICE::ENABLE_APPLICATION_EVENTS_ONLY_ACK()",
                            "'Application events only' mode has been enabled. Controller now ignores every event which is not an application event.\n")         
  
    def do(self):        
       return super().do()
  
