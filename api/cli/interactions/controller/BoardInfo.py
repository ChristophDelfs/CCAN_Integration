from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.base.PlatformServices import PlatformServices

class BoardInfo(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)
        self._average_load_during_list_minute = 0
        self._maximum_load_during_last_minute = 0
        self._connector = my_connector
  
    def do(self):
        
        self.set_request("CONFIG_SERVICE::SHORT_INFO_REQUEST()")
        self.set_expected_answers(["CONFIG_SERVICE::SHORT_INFO_REQUEST_REPLY()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        self._uuid, self._controller_crc = my_received_event.get_parameters().get_values()
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):        
        controller_uuid = PlatformServices.uuid_to_string(self._uuid)
        try:           
            controller_type_name = self.get_defaults().get_controller_from_crc(self._controller_crc)
        except ValueError:
            raise CCAN_Error(CCAN_ErrorCode.INTERNAL_ERROR)

        Report.print(ReportLevel.VERBOSE,"Controller Board " + controller_type_name + " with UUID " + controller_uuid + "\n")

        return controller_uuid, controller_type_name

    def uuid_to_string(my_uuid):
        result = ''
        length = len(my_uuid)
        result +=("0x")
        for element in my_uuid:
            result +=("{0:#0{1}x}".format(element,4)[2:4])
        return result   

    def on_interrupt(self,my_signal, frame):    
        return