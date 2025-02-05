import os
from src.cli.interactions.broadcast.BroadcastBoardInfo import BroadcastBoardInfo
from src.cli.interactions.broadcast.BroadcastVersion import BroadcastVersion
from src.cli.interactions.broadcast.BroadcastConfigurationInformation import (
    BroadcastConfigurationInformation,
)
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.CCAN_Defaults import CCAN_Defaults
from src.base.Report import Report, ReportLevel

from src.base.PlatformServices import PlatformServices


class AutomationBase:
    #
    # Reads automation data from available controllers and from configuration file
    # Configuration file is either provided or it is derived from the configuration found in the controllers.
    #
    #
    # Result are two controller maps.
    # Each map uses the address of the controller as key.
    # Entries are:
    #
    #    UUID
    #    Configuration File
    #    Configuration Version
    #    Bootloader Version
    #

    def __init__(self, my_connector, my_waiting_time, my_automation_file, my_mode):
        self._instance_dictionary = my_connector.get_instance_dictionary()

        self._waiting_time = my_waiting_time
        # self._ccan_defaults = CCAN_Defaults()
        # default_file =  os.path.join(os.environ["CCAN"],"gen","ccan_generated_definitions")
        # self._ccan_defaults.init_from_pkl(default_file)
        self._ccan_defaults = my_connector.get_ccan_defaults()
        self._platform_configuration = my_connector.get_platform_configuration()

        self._automation_file = my_automation_file
        self._mode = my_mode

        self._connector = my_connector

        self._controller_map = {}
        self._controller_map["file"] = {}

        self._controller_map["file"]["uuid"] = {}
        self._controller_map["file"]["configuration_version"] = {}
        self._controller_map["file"]["configuration_file"] = {}
        self._controller_map["file"]["name"] = {}
        self._controller_map["file"]["type"] = {}

        self._controller_map["network"] = {}
        self._controller_map["network"]["uuid"] = {}
        self._controller_map["network"]["configuration_version"] = {}
        self._controller_map["network"]["configuration_file"] = {}
        self._controller_map["network"]["software_version"] = {}

        self._ethernet_controller = []
        self._can_controller = []

        # evaluation result:
        self._answers_complete = False

        self.load()

    def load(self):
        # optimistic start:

        automation_available = True
        if self._mode == "MIN":
            if self._automation_file is not False:
                self.load_automation_data(self._automation_file)
                self.get_configuration_from_network()
            else:
                # self.get_configuration_from_network()
                #print("scan for automation..")
                automation_available = self.scan_for_automation()
                #try:
                #    print("Automation loaded " + self._automation_file)
                #except TypeError:
                #    print("Gotcha!")

        elif self._mode == "MAX":
            if self._automation_file is not False:
                self.load_automation_data(self._automation_file)
                self.load_controller_data_from_network()
            else:
                self.load_controller_data_from_network()
                automation_available = self.scan_for_automation()
        else:
            raise ValueError  # shall never happen

        if automation_available is False or self._instance_dictionary is None:
            return

        self._read_information_from_automation()

    def load_controller_data_from_network(self):
        self.get_uuid_from_network()
        self.get_configuration_from_network()
        self.get_bootloader_version_from_network()
        self.evaluate_network_answers()

    def get_uuid_from_network(self):
        result = BroadcastBoardInfo(self._connector, self._waiting_time, 1).do()
        for item in result:
            self._controller_map["network"]["uuid"][item] = (
                PlatformServices.uuid_to_string(result[item][0])
            )

    def get_configuration_from_network(self):
        result = BroadcastConfigurationInformation(
            self._connector, self._waiting_time, 1
        ).do()
        for item in result:
            self._controller_map["network"]["configuration_version"][item] = result[
                item
            ][0]
            self._controller_map["network"]["configuration_file"][item] = result[item][
                2
            ]

    def scan_for_automation(self):
        # if no automation has been provided, search for it:
        if self._instance_dictionary is None:
            try:
                result = BroadcastConfigurationInformation(
                    self._connector,
                    self._platform_configuration["RESPONSE_WAITING_TIME"],
                    1,
                ).do()
            except CCAN_Error as ex:
                Report.print(ReportLevel.WARN, str(ex))
                self._instance_dictionary = None
                return False

            filenames = []
            dates = []
            for ccan_address in result:
                version, date, filename = result[ccan_address]
                filenames.append(filename)
                dates.append(date)
            try:
                base_config_file = PlatformServices.determine_base_config_file_from_configuration_files(
                    filenames, self._platform_configuration["CONFIGURATION_PATH"]
                )

                self._connector.load_automation(base_config_file)
                self._automation_file = base_config_file
                self._instance_dictionary = self._connector.get_instance_dictionary()

            except CCAN_Error as ex:
                Report.print(ReportLevel.WARN, str(ex))
            except FileNotFoundError:
                self._instance_dictionary = None

            if self._instance_dictionary is None:
                return False
        return True

    # assumes that bootloader is already active:
    def get_bootloader_version_from_network(self):
        result = BroadcastVersion(self._connector, self._waiting_time, 1).do()
        for item in result[0]:
            self._controller_map["network"]["software_version"][item] = result[0][item]

    def evaluate_network_answers(self):
        # check equal number of answers:
        self._complete_answers = True
        number_of_answers = len(self._controller_map["network"]["uuid"])
        if (
            len(self._controller_map["network"]["configuration_version"])
            != number_of_answers
        ):
            self._complete_answers = False
        if (
            len(self._controller_map["network"]["configuration_file"])
            != number_of_answers
        ):
            self._complete_answers = False

    def _read_information_from_automation(self):
        if self._instance_dictionary is None:
            raise ValueError

        #print("Bin in _read_information_from_automation")

        for unused, controller in self._instance_dictionary["APP"]:
            if controller.is_app() is False:
                #
                # read uuid, controller name and address:
                #
                uuid = controller.get_description_list("UUID")
                parameters = controller.get_description_list("PARAMETER")
                for parameter in parameters:
                    if parameter.get_name() == "ccan_address":
                        ccan_address = parameter.get_value()
                        controller_name = controller.get_name()
                        break

                # check whether CCAN address has been used more than once:
                if ccan_address in self._can_controller:
                    raise CCAN_Error(
                        CCAN_ErrorCode.UPDATE_FAILURE,
                        "Controller with UUID "
                        + uuid
                        + " has been defined with CCAN address "
                        + str(ccan_address)
                        + " which is already in use by another controller.",
                    )

                self._controller_map["file"]["uuid"][ccan_address] = uuid
                self._controller_map["file"]["name"][ccan_address] = controller_name
                self._controller_map["file"]["type"][ccan_address] = (
                    controller.get_type()
                )

                #
                # detect communication drivers:
                #

                connection_type = None
                for unused, communication_driver in controller.get_description_list(
                    "COMMUNICATION_DRIVER"
                ):
                    if communication_driver.get_type() == "ETHERNET":
                        connection_type = "ETHERNET"
                    if (
                        communication_driver.get_type() == "CAN_DRIVER"
                        and connection_type == None
                    ):
                        connection_type = "CAN"
                if connection_type == "ETHERNET":
                    self._ethernet_controller.append(ccan_address)
                elif connection_type == "CAN":
                    self._can_controller.append(ccan_address)
                else:
                    print(
                        "Internal error: controller "
                        + controller.get_name()
                        + " has no communication driver..?"
                    )

                #
                # derive configuration file
                #

                self._controller_map["file"]["configuration_file"][ccan_address] = (
                    CCAN_Defaults.get_configuration_file_name(
                        self._automation_file, controller_name
                    )
                )

                #
                # get version information
                #
                #
                self._automation_version = self._instance_dictionary["version"]
                pass

    def load_automation_data(self, my_automation_file):
        if my_automation_file is False:
            try:
                result = BroadcastConfigurationInformation(
                    self._connector,
                    0.1,  # self._platform_configuration["RESPONSE_WAITING_TIME"],
                    1,
                ).do()
            except CCAN_Error as ex:
                self._number_of_expected_answers = 0
                Report.print(ReportLevel.WARN, str(ex))
                self._instance_dictionary = None
                return
            filenames = []
            dates = []
            for ccan_address in result:
                version, date, filename = result[ccan_address]
                filenames.append(filename)
                dates.append(date)

            my_automation_file = (
                PlatformServices.determine_base_config_file_from_configuration_files(
                    filenames, self._platform_configuration["CONFIGURATION_PATH"]
                )
            )
        try:
            self._connector.load_automation(my_automation_file)
            self._instance_dictionary = self._connector.get_instance_dictionary()
        except CCAN_Error as ex:
            Report.print(ReportLevel.ERROR, str(ex))
            self._instance_dictionary = None

    #
    #
    # Access functions:
    #
    #

    def get_automation_version(self):
        return self._automation_version

    def get_controller_version(self, my_address):
        return self._controller_map["network"]["software_version"][my_address]

    def get_number_of_controllers_in_network(self):
        return len(list(self._controller_map["network"]["uuid"].values()))

    def get_number_of_controllers_in_automation(self):
        return len(list(self._controller_map["file"]["name"].values()))

    # def get_controller_names(self):
    #    return list(self._controller_map["file"]["name"].values())

    def get_ccan_addresses_from_network(self):
        return list(self._controller_map["file"]["uuid"].keys())

    def get_ccan_addresses_from_automation(self):
        return list(self._controller_map["file"]["uuid"].keys())

    def get_controller_name(self, my_uuid):
        try:
            return self._controller_map["file"]["name"][my_uuid]
        except KeyError:
            return "Unknown Instance"

    def get_configuration_filename(self, my_ccan_address):
        return self._controller_map["file"]["configuration_file"][my_ccan_address]

    def get_uuid_map_from_automation(self):
        return self._controller_map["file"]["uuid"]

    def get_uuid_map_from_network(self):
        return self._controller_map["network"]["uuid"]

    def get_current_address_via_uuid(self, my_uuid):
        for address in self._controller_map["network"]["uuid"]:
            if self._controller_map["network"]["uuid"][address] == my_uuid:
                return address
        return None

    def get_uuid(self, my_address):
        return self._controller_map["file"]["uuid"][my_address]

    def get_controller_type(self, my_address):
        return self._controller_map["file"]["type"][my_address]

    def get_ethernet_controller(self):
        return self._ethernet_controller

    def get_can_controller(self):
        return self._can_controller

    ###############

    def get_automation_file(self):
        return self._automation_file

    def get_controller_name_max_length(self):
        return self._platform_configuration["TEXT_OUTPUT"]["CONTROLLER_NAME_MAX_LENGTH"]
