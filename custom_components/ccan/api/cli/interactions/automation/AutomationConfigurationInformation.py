from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.PlatformServices import PlatformServices
from api.base.PlatformDefaults import PlatformDefaults
import time

class AutomationConfigurationInformation(AutomationInteraction): 
    def __init__(self, my_cli, my_waiting_time, my_retries, my_automation_file):         
        super().__init__(my_cli, my_waiting_time, my_retries, my_automation_file)        

    
    def do(self):   
        self.set_request("CONFIG_SERVICE::INFO_REQUEST("+str(PlatformDefaults.UPDATE_SECTION_CONFIGURATION) + ")")
        self.set_expected_answers(["CONFIG_SERVICE::CONFIGURATION_INFO()"])
        return super().do()

    def on_iteration_end(self):
        return
  
    def before_send(self):
        return

    def on_receive(self,my_index, my_received_event):
        return False

    def on_loop_end(self):       
        receivers = list(self._collected_values)
        receivers.sort()
        result = {}

        controller_name_length = self._base.get_controller_name_max_length()

        if len(list(receivers)) > 0:
            Report.print(ReportLevel.VERBOSE,  f"{'Controller name':{controller_name_length}}" + f"{'Address':10}" + f"{'Version':10}" + f"{'Date':15}" f"{'Filename':60}" "\n")         
            for receiver in list(receivers):    
                version = [None]*3
                version[0],version[1], version[2], date, raw_filename = self._collected_values[receiver]

                version_string = str(version[0]) + "." + str(version[1]) + "." + str(version[2])
                config_date = time.localtime(date)
                config_date_string = str(config_date.tm_mday) + "." + str(config_date.tm_mon) + "." + str(config_date.tm_year)
                filename = raw_filename.replace('"','')
                controller_name = self._base.get_controller_name(receiver)
                if len(filename) != 0:
                    Report.print(ReportLevel.VERBOSE.VERBOSE, f"{controller_name:{controller_name_length}}" + '{:<10}'.format(receiver) +  f"{version_string:10}"  +  f"{config_date_string:15}"  + f"{filename:60}"+ "\n")              
                else:
                    Report.print(ReportLevel.VERBOSE,'{:<20}'.format('') +  '{:<10}'.format(receiver) +  f"{version_string:10}"  +  f"{'':15}"  + f"{'Default Configuration':60}"+ "\n")    
                
                result[receiver] = (version,config_date,filename)              
        else:
            Report.print(ReportLevel.VERBOSE,'CCAN Network is down or no controllers are available.\n')
            return None       
        return [result]

       

