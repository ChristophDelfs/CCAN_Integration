import time
from src.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

from src.cli.interactions.controller.Reset import Reset
from src.cli.interactions.controller.Lock import Lock
from src.cli.interactions.broadcast.BroadcastReset import BroadcastReset
from src.cli.interactions.broadcast.BroadcastLock import BroadcastLock
from src.cli.interactions.automation.AutomationWaitForBootloaderStart import AutomationWaitForBootloaderStart
from src.cli.interactions.controller.WaitForFirmware import WaitForFirmware
from src.cli.interactions.controller.WaitForBootloader import WaitForBootloader
from src.cli.download.DownloadRobot import DownloadRobot
from src.base.PlatformServices import PlatformServices
from src.PyCCAN_Warnings import CCAN_Warnings

class AutomationUpdate(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries,my_target_automation, my_enforce_flag, my_automation_file):         
        if my_target_automation == '':          
            self._filename = my_automation_file
        else:
            self._filename = my_target_automation            

        self._current_automation = my_automation_file

        Report.push_level(ReportLevel.WARN)      
        try: 
            super().__init__( my_connector, my_waiting_time, my_retries, self._filename, "MAX") 
        except CCAN_Error as ex:       
            raise ex
        except Exception:
            raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE,"Failure during initialization phase.")      

        if self._connector.is_automation_read_from_ftp_server:
            raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE,"Automation is only available on ftp Server. Update requires access to a local file.")      

        # here controllers are added if an erase of the configuration is required prior to the update
        self._erase_configuration = []
        
        Report.pop_level()       

        self._enforce_flag = my_enforce_flag
        #self._upgrade_flag = my_upgrade_flag
        self._m_real = False

        # unknown whether all controllers are "visible":
        self._all_controllers_visible  = None
        
    def do(self):     
        Report.print(ReportLevel.VERBOSE,"All controllers will be locked during update in bootloader mode.\n")
        
        Report.push_level(ReportLevel.ERROR)       

        # check whether compiled automation file is ok for an automatic update:
        self._check_automation_fitness()

        # check whether network fits to compiled automation file:
        self._check_network_fitness()

              
        # reset into bootloader:   
        try:                      
            answers = BroadcastReset(self._connector, self._base._platform_configuration["RESPONSE_WAITING_TIME"], 1).do()
        except:
            answers = []
        
        if answers is None or len(answers) != self._base.get_number_of_controllers_in_network():
            raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE," Only " + str(len(answers)) + " engines responded and entered bootloader (expected : " + str(self._base.get_number_of_controllers_in_network()) + ")")

        # disable automation for all other listeners:
        self._connector.mark_current_automation_as_invalid()

        # wait for first ethernet controller:
        self._connector.wait_for_event(10,"LIFE_SERVICE::CONTROLLER_RESET()")

        # and lock all controllers:
        try:                      
            answers = BroadcastLock(self._connector, self._base._platform_configuration["RESPONSE_WAITING_TIME"], 1).do()
        except:
            answers = []
        Report.pop_level()   

        # update controllers with Ethernet connection:

        Report.print(ReportLevel.VERBOSE,"..Updating controllers with Ethernet connection..\n")   
        self._do_update_loop(self._base.get_ethernet_controller(), False)

        # update network:
        Report.print(ReportLevel.VERBOSE,"..Updating network information..\n")   
        Report.push_level(ReportLevel.NONE)     
        try: 
            self._base.load_controller_data_from_network()
        except CCAN_Error as ex:
            Report.pop_level()   
            raise ex

        # lock all again:
        Report.pop_level()
        try:                                
            Report.print(ReportLevel.VERBOSE,"..Lock again all controllers with Ethernet connection..\n")   
            Report.push_level(ReportLevel.NONE)     
            answers = BroadcastLock(self._connector, self._base._platform_configuration["RESPONSE_WAITING_TIME"], 1).do()
        except:
            answers = []

        Report.pop_level()   
       
        # update controllers with CAN connection:
        Report.print(ReportLevel.VERBOSE,"..Updating controllers with CAN connection..\n")   
        self._do_update_loop(self._base.get_can_controller(),True)
       

        Report.print(ReportLevel.VERBOSE,"..Update completed, unlocking all controllers..\n")

        # ship info on new automation to all listeners_
        self._connector.announce_new_automation(self._base.get_automation_file())


        time.sleep(1)
        Report.push_level(ReportLevel.NONE)                             
        answers = BroadcastReset(self._connector, self._base._platform_configuration["RESPONSE_WAITING_TIME"], 1).do()
        if len(answers) != len(self._base.get_ccan_addresses_from_network()):
            Report.print(ReportLevel.VERBOSE,"Final reset was not successful. Likely, not all controllers are unlocked now.\n")
            return False
        return True


    def _do_update_loop(self,my_address_list, my_lock_flag):        
    
        uuid_map = self._base.get_uuid_map_from_automation()
      
        for address in my_address_list:
            # get uuid:
            uuid = uuid_map[address]

            current_address = self._base.get_current_address_via_uuid(uuid)
            if current_address is None:
                CCAN_Warnings.warn(None, "Controller with address " + str(address) + " is not available in network. Skipped.")
                continue
                

            attempts = 5

            while attempts > 0:             

                # create filename:
                configuration_filename = self._base.get_configuration_filename(address)
                controller_name        = self._base.get_controller_name(address)

                if self.perform_controller_update(current_address, controller_name, configuration_filename, my_lock_flag) is False:
                    attempts -=1 
                    # wait for failing update to be finished: "Engine Start"

                    # update address info

                else:
                    break
            if attempts == 0:
                CCAN_Warnings(" Controller " + controller_name + " with UUID " + uuid + " and current address in automation " + str(current_address) + " could not be updated. Skipping..")
             

        # end

    def perform_controller_update(self,current_address,my_controller_name, my_filename, my_lock_flag):
        Report.print(ReportLevel.VERBOSE,".. -> Update for controller " + my_controller_name + " with current address " + str(current_address) + "..")
        self._connector.set_destination_address(current_address)
        try:
            Report.push_level(ReportLevel.NONE)       
            download = DownloadRobot(my_connector=self._connector, my_filename= my_filename, enforce_flag= self._enforce_flag,lock_flag= my_lock_flag)
            download.do()                       
        except CCAN_Error as ex:
            Report.pop_level()
            if ex.get_code() == CCAN_ErrorCode.TARGET_UP_TO_DATE:               
                Report.print(ReportLevel.VERBOSE,"not needed.\n")              
                if not my_lock_flag:
                    Report.push_level(ReportLevel.NONE)                           
                    time.sleep(1)
                    try:
                        # releasing the lock and restarting bootloader:
                        Reset(self._connector,1, my_wait_for_startup = True).do()
                        # Lock again:
                        Lock(self._connector,1).do()
                    except CCAN_Error as ex:
                        Report.pop_level()
                        raise ex

                    Report.pop_level()
                return True
            else:                           
                raise ex
        
        Report.pop_level()
        Report.print(ReportLevel.VERBOSE, "completed\n")
     
        if my_lock_flag is False:
            self.wait_for_bootloader_start()
        
        return True


    def _check_automation_fitness(self):
        #
        # UUID:
        #
        #
        # have all controllers in the network an UUID?
        if len(self._base.get_uuid_map_from_automation().values())  != self._base.get_number_of_controllers_in_automation():
            raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE," not all controllers in the  automation file have an UUID. This case is not supported.")



    def _check_network_fitness(self):
        #
        # check whether UUID's from network fits to automation:
        uuids_from_automation =  list(self._base.get_uuid_map_from_automation().values())
        #uuids_from_network    = list(self._base.get_uuid_map_from_network().values())

        for controller_address in self._base.get_uuid_map_from_network():
            controller_uuid = self._base.get_uuid_map_from_network()[controller_address]
            if controller_uuid not in uuids_from_automation:
               
                try:
                    automation_uuid = self._base.get_uuid_map_from_automation()[controller_address]
                    automation_text = " The automation has defined " + automation_uuid + " for this controller."
                except:
                    automation_text = ''

                raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE," Controller with address " + str(controller_address) + " and UUID "  + controller_uuid+ " in CCAN network is not defined in automation." + automation_text)

        #
        # check version issues:
        #
        for controller_address in self._base.get_uuid_map_from_network():
            version = self._base.get_controller_version(controller_address)
            if not PlatformServices.are_versions_compatible(version, self._base.get_automation_version()):
                raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE," Bootloader SW for controller with address "+ str(controller_address) + " is incompatible with automation version. Perform a SW update first.")
                                                        
        #
        #
        # check whether there will be an address clash and whether all controllers are "visible"
        #
      
        self._all_controllers_visible = True

        for address in self._base.get_ccan_addresses_from_automation():
            # get uuid:
            uuid = self._base.get_uuid(address)

            # get the address of a controller with the same UUID in the network
            # current_address is None if the UUID is not available in the network
            current_address = self._base.get_current_address_via_uuid(uuid)

            # the controller is not visible? If yes -> skip further evaluation, but remember that not all controllers are visible:            
            if current_address is None:
                self._all_controllers_visible = False
                continue

            if current_address == address:
                continue

            # if not, check whether the new address is elsewhere in use -> if yes, the configuration of that controller needs to be erased 
            if current_address in self._base.get_ccan_addresses_from_network():
                self._erase_configuration.append(current_address)        



    def wait_for_bootloader_start(self):
        try:
            answers = self._connector.wait_for_event(10,"LIFE_SERVICE::CONTROLLER_RESET()")
        except CCAN_Error as ex:
            raise CCAN_Error(CCAN_ErrorCode.UPDATE_FAILURE," Failing to wait for bootloader startup")


