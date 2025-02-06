from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class DetectExpander(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)
      
    def do(self):        
        self.set_request("EXPANDER_SERVICE::SEARCH()")
        self.set_expected_answers( ["EXPANDER_SERVICE::SEARCH_RESULT()"])
        return super().do()
    
    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          

        answer_values =  my_received_event.get_parameter_values()

        bank_detection_flags    = answer_values[0]
        detectected_types_flags = answer_values[1]
        names                   = answer_values[2]   

        expander = []          
        expander.append(bank_detection_flags[0:2])
        expander.append(bank_detection_flags[2:4])
        expander.append(bank_detection_flags[4:6])
        expander.append(bank_detection_flags[6:])

        self._result = []            
        address = 0
        for element,detected_type,name in zip(expander, detectected_types_flags,names):              
            if (detected_type == 0xffff):
                detected_type_string = "Not accessible"
            elif detected_type == 0xfffe:
                detected_type_string = "Not formatted"
            elif detected_type == 1:               
                detected_type_string = "Input"
            elif detected_type == 2:
                detected_type_string = "Output"
            else:
                raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_EXPANDER_TYPE,"Read type " + str(detected_type)+".")

            self._result.append((address,element,detected_type_string,name))
            address +=1   

        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):           
        
        Report.print(ReportLevel.VERBOSE, f"{'Address':8}" + f"{'Selectors':15}" +   f"{'MCP23017 Devices':20}" +  f"{'Typ':18}" + f"{'Name':40}\n")
        
        for entry in self._result:

                address = entry[0]
                element = entry[1]
                detected_type_string = entry[2]
                name = entry[3]              
             
                if address == 0:
                    selector_string = "[On , On]"
                if address == 2:
                    selector_string = "[On ,Off]"
                if address == 1:
                   selector_string =  "[Off, On]"
                if address == 3:
                    selector_string = "[Off,Off]"
                                        
                # reverse order of chips: left chip has higher address (A2 is Vcc)
                if element[1] == 0:
                    element_string = "[Ok    , "
                else:
                    element_string = "[Not Ok, "

                if element[0] == 0:
                    element_string2 = "Ok    ]"
                else:
                    element_string2 = "Not Ok]"
                element_string = ''.join([element_string, element_string2])

                Report.print(ReportLevel.VERBOSE, '{:<8}'.format(address) + f"{selector_string:15}" +   f"{element_string:20}" +  f"{detected_type_string:18}" + f"{name:40}\n")


        return self._result