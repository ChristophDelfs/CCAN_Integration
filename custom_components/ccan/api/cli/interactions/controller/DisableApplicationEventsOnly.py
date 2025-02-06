from api.cli.interactions.controller.SimpleInteraction import SimpleInteraction

class DisableApplicationEventsOnly(SimpleInteraction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries, 
                            "ENGINE_SERVICE::DISABLE_APPLICATION_EVENTS_ONLY()", 
                            "ENGINE_SERVICE::DISABLE_APPLICATION_EVENTS_ONLY_ACK()",
                            "Mode 'Application events only' is no longer active. Controller reacts on all events again.\n")         
  
    def do(self):        
       return super().do()
