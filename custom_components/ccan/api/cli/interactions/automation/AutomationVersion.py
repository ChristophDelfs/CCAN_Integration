from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationVersion(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation_file):         
        super().__init__( my_connector, my_waiting_time, my_retries, my_automation_file)       
        self._sw_version = {}
        self._configuration_version = {}

        
    def do(self):     
        self.set_request("CONFIG_SERVICE::GET_VERSION()")
        self.set_expected_answers(["CONFIG_SERVICE::GET_VERSION_REPLY()"])
        super().do()

    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):   
        receiver = my_received_event.get_sender_address()                       
        version_data = my_received_event.get_parameters().get_values()

        self._sw_version[receiver] = version_data[0:3]
        self._configuration_version[receiver] = version_data[3:6]
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self):     
        if len(self._sw_version) == 0:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)
        
        controller_name_length = self._base.get_controller_name_max_length()

        Report.print(ReportLevel.VERBOSE, f"{'Controller name':{controller_name_length}}" + f"{'Address:':10}" + f"{'SW Version:':15}" + f"{'Configuration Version:':10}"" \n")         
        for address in self._sw_version:  
            controller_name = self._base.get_controller_name(address)     

            sw_version = self._sw_version[address]
            sw_configuration = self._configuration_version[address]

            sw_version_string = str(sw_version[0]) +"." + str(sw_version[1]) + "." + str(sw_version[2])
            configuration_version_string = str(sw_configuration[0]) +"." + str(sw_configuration[1]) + "." + str(sw_configuration[2])

            Report.print(ReportLevel.VERBOSE.VERBOSE, f"{controller_name:{controller_name_length}}" +'{:<10}'.format(address) +  f"{sw_version_string:15}" +  f"{configuration_version_string:10}""\n")                                    

        return [self._sw_version, self._configuration_version]    


