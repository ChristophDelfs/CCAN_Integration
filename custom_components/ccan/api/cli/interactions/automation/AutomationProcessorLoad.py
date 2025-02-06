from api.cli.interactions.automation.SimpleAutomationInteraction import SimpleAutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationProcessorLoad(SimpleAutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation):                     
        super().__init__(my_connector, my_waiting_time, my_retries,my_automation, "LIFE_SERVICE::PROCESSOR_LOAD_REQUEST()", "LIFE_SERVICE::PROCESSOR_LOAD_REPLY()", None, self._evaluate)            
        
    def _evaluate(self, load):
        return load

    def do(self):     
        Report.push_level(ReportLevel.WARN)
        results = super().do()[0]
        Report.pop_level()
     
        controller_name_length = self._base.get_controller_name_max_length()


        Report.print(ReportLevel.VERBOSE, f"{'Controller name':{controller_name_length}}"  + f"{'Address:':10}" + f"{'Average Load [%]':20}" + f"{'Maximum Load [%]':20}" + " \n")         
        for address in results:        
            controller_name = self._base.get_controller_name(address)      
            average_load, maximum_load = results[address]
            Report.print(ReportLevel.VERBOSE.VERBOSE, f"{controller_name:{controller_name_length}}" + '{:<10}'.format(address) +    f"{average_load:<20}"  +  f"{maximum_load:<20}"  + "\n")           

        return results
