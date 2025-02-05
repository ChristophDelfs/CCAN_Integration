from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class SetBoardLED(Interaction): 
    def __init__(self, my_connector,my_retries, my_led_name, my_new_status):            
        super().__init__(my_connector, my_retries)
        self.__led_name_input = my_led_name
        self.__new_status = my_new_status
       
    def do(self):        

        if self.__led_name_input == "ALARM":
            led_name = 0
        elif  self.__led_name_input == "WARN":
            led_name = 1
        else:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"Only 'ALARM' or 'WARN' are allowed board LED's") 

        if self.__new_status == "ON":
           status = 0
        elif self.__new_status == "FLASHING":
            status = 1
        elif self.__new_status == "OFF":
            status = 2      
        else:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"Only <ON> or <OFF> are allowed as LED state.")    

        self.set_request("LIFE_SERVICE::SET_BOARD_LED("+str(led_name) + "," + str(status) + ")")
        self.set_expected_answers(["LIFE_SERVICE::SET_BOARD_LED_ACK()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Board either does not provide LED's or the board cannot be reached.")    

    def on_iteration_end(self):
        return

    def on_loop_end(self):                                 
        return True

