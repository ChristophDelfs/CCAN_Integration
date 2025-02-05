from src.cli.interactions.broadcast.SimpleBroadcastInteraction import SimpleBroadcastInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class BroadcastProcessorLoad(SimpleBroadcastInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries): 
        
        super().__init__(my_connector, my_waiting_time, my_retries,"LIFE_SERVICE::PROCESSOR_LOAD_REQUEST()", "LIFE_SERVICE::PROCESSOR_LOAD_REPLY()", None, self._evaluate)            
        
    def _evaluate(self, load):
        return load

    def do(self):     
        Report.push_level(ReportLevel.WARN)
        results = super().do()
        Report.pop_level()
     
        Report.print(ReportLevel.VERBOSE, f"{'Address':10}" + f"{'Average Load [%]':20}" + f"{'Maximum Load [%]':20}" + " \n")         
        for address in sorted(list(results)):        
            average_load, maximum_load = results[address]
            Report.print(ReportLevel.VERBOSE.VERBOSE,'{:<10}'.format(address) +    f"{average_load:<20}"  +  f"{maximum_load:<20}"  + "\n")           

        return None

