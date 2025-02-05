import os
import pickle
import xml.etree.ElementTree as ET

from .Definitions import ParamListInfo 
from .Definitions import HCAN_Message
from .Definitions import HCAN_ProtocolEntry

from .ResolverElements import DeviceAttribute
from .ResolverElements import ResolvedSensorDriverDescriptionDictionary
from .ResolverElements import ResolvedCommunicationDriverDescriptionDictionary
from .ResolverElements import ResolvedAppDescriptionDictionary
from .ResolverElements import ResolvedTransportAdapterDescriptionDictionary
from .ResolverElements import ResolvedAdditionalProtocolDescriptionDictionary
from .ResolverElements import ResolvedInstanceDictionaryBase
from .ResolverElements import ResolvedDeviceDescriptionDictionary
from .ResolverElements import ResolvedAdditionalProtocolsDictionary
from .ResolverElements import MappingType
from .ResolverElements import ProtocolType
from .ResolverElements import ResolvedProtocolInstance
from .ResolverError import ResolverError
from src.base.PlatformDefaults import PlatformDefaults



class ResolverStore:    
    #ILLEGAL_DEVICE_ID = -1
    TEMPLATE_TYPE = -1
    ILLEGAL_DRIVER_ID = -1

    def __init__(self, filename = None):
        if filename is None:
            self.__description_dictionary = {}
            self.__description_dictionary["SENSOR_DRIVER"] = (
                ResolvedSensorDriverDescriptionDictionary()
            )
            self.__description_dictionary["COMMUNICATION_DRIVER"] = (
                ResolvedCommunicationDriverDescriptionDictionary()
            )
            self.__description_dictionary["TRANSPORT_ADAPTER"] = (
                ResolvedTransportAdapterDescriptionDictionary()
            )
            self.__description_dictionary["PROTOCOL"] = (
                ResolvedAdditionalProtocolDescriptionDictionary()
            )
            self.__description_dictionary["APP"] = ResolvedAppDescriptionDictionary()
            self.__description_dictionary["DEVICE"] = ResolvedDeviceDescriptionDictionary()
            self.__description_dictionary["HOME_ASSISTANT_DEVICE"] = ResolvedDeviceDescriptionDictionary()

            self.__instance_dictionary = {}
            self.__instance_dictionary["PROTOCOL"] = ResolvedAdditionalProtocolsDictionary()
            self.__instance_dictionary["APP"] = ResolvedInstanceDictionaryBase(
                self.__description_dictionary["APP"], 0, False, self.__get_local_app_id
            )
            self.__instance_dictionary["DEVICE"] = ResolvedInstanceDictionaryBase(
                self.__description_dictionary["DEVICE"], 100
            )
            self.__instance_dictionary["HOME_ASSISTANT_DEVICE"] = ResolvedInstanceDictionaryBase(
                self.__description_dictionary["HOME_ASSISTANT_DEVICE"]
            )
            self.__instance_dictionary["VARIABLE"] = ResolvedInstanceDictionaryBase(None)
            self.__instance_dictionary["MAPPING"] = {}

            self.__automatic_variable_count = 0

            for protocol in ProtocolType("CCAN").get_list_of_types():
                self.__instance_dictionary["MAPPING"][protocol] = {}
                for mapping_type in MappingType("SIMPLE").get_list_of_types():
                    self.__instance_dictionary["MAPPING"][protocol][
                        mapping_type
                    ] = {}  # ResolvedInstanceDictionaryBase(None)
        else:
        # Restore Resolver from instance and description dictionaries from file
            with open(filename + ".pkl", "rb") as f:
                    self.__description_dictionary = pickle.load(f)
                    self.__instance_dictionary = pickle.load(f)

        major = PlatformDefaults.CCAN_MAJOR_VERSION
        minor = PlatformDefaults.CCAN_MINOR_VERSION
        patch = PlatformDefaults.CCAN_PATCH_VERSION
        self.__instance_dictionary["version"] = (major, minor, patch)                    


    def get_version(self):
        return  self.__instance_dictionary["version"]

    def get_instance_map(self):
        return self.__instance_dictionary
    
    def description_map(self):
        return self.__description_dictionary
    


    ############
    def insert_instance(self, dictionary_key, element):
        return self.__instance_dictionary[dictionary_key].insert(element)

    def get_instance_by_name(self,dictionary_key, name):
        return self.__instance_dictionary[dictionary_key].get_entry_by_name(name)
    
    def get_id_and_instance_by_name(self,dictionary_key, name):
        return self.__instance_dictionary[dictionary_key].get_by_name(name)

    def get_instance_dictionary(self,dictionary_key):
        return self.__instance_dictionary[dictionary_key]

    def get_number_of_variable_entries(self) -> int:
        return self.__instance_dictionary["VARIABLE"].get_number_of_entries()

    def get_mapping_table(self, protocol: str, mapping_method: str):
        return self.__instance_dictionary["MAPPING"][str(protocol)][str(mapping_method)]

    def get_device_event_map(self, device_name):
        device_instance = self.get_instance_by_name("DEVICE",device_name)
        device_description = self.get_description_by_name("DEVICE", device_instance.get_type())
        return device_description.get_description_list("EVENT")

    ############

    def get_description_by_name(self,dictionary_key: str, name: str):
        return self.__description_dictionary[dictionary_key].get_entry_by_name(name)

    def get_type_and_description_by_name(self, dictionary_key: str,name: str):
        return self.__description_dictionary[dictionary_key].get_by_name(name)

    def get_type_id_by_name(self,dictionary_key: str, name: str):
        return self.__description_dictionary[dictionary_key].get_id_by_name(name)

    def is_class_supported(self, dictionary_key: str, element) -> bool:
        return self.__description_dictionary[dictionary_key].is_supported_class(element)
        
    def get_description_dictionary(self, dictionary_key: str):
        return self.__description_dictionary[dictionary_key]

    #############

    def add_to_dictionaries(self,dictionary_key, element, id=None):
        (name, id) = self.__description_dictionary[dictionary_key].insert(element,id)
        self.__instance_dictionary[dictionary_key].add_class_element(name, id)


    
    def get_local_app_id(self, my_app_name):
        app_instance = self.__instance_dictionary["APP"].get_entry_by_name(my_app_name)
        if not app_instance.is_app():
            return 0


    def __get_local_app_id(self, my_app_name):
        app_instance = self.get_instance_by_name("APP",my_app_name)

        if not app_instance.is_app():
            return 0

        controller_instance = self.get_instance_by_name("APP", app_instance.get_controller_name())
        new_local_id = controller_instance.get_new_local_id()
        return new_local_id

      
    def add_hcan_support_from_file(self, include_path, protocol_file, location_info):
        ''' Read a HCAN protocol file and add to protocol dictionary'''
        hcan_map = {}

        for path in include_path:
            found = True
            try:
                file_under_test = path + "/" + protocol_file.get_value()
                tree = ET.parse(file_under_test)
                protocols_root = tree.getroot()
                break
            except FileNotFoundError:
                found = False
                continue
        if found is False:
            raise ResolverError(
                location_info,
                "HCAN protocol file "
                + protocol_file.get_value()
                + " does not exist or contains errors.",
            )

        # assemble map from protocol file:
        for protocol in protocols_root:
            for service in protocol:
                message_map = {}
                for message in service:
                    parameter_name_list = []
                    parameter_type_list = []
                    dimension_list = []
                    pos = 0
                    for parameter in message:
                        if pos != int(parameter.attrib["pos"]):
                            raise ResolverError(
                                location_info,
                                "Position information for message "
                                + message.attrib["name"]
                                + " is not strictly increasing by 1. This cannot be handled.",
                            )
                        parameter_name_list.append(parameter.attrib["name"])
                        parameter_type_list.append("UINT8")
                        dimension_list.append("Scalar")
                        pos += 1

                    parameter_description_list = ParamListInfo(
                        parameter_name_list=parameter_name_list,
                        parameter_type_list=parameter_type_list,
                        dimension_list=dimension_list,
                    )
                    message_map[message.attrib["name"]] = HCAN_Message(
                        id=int(message.attrib["id"]),
                        name=message.attrib["name"],
                        parameter_description_list=parameter_description_list,
                    )

                path = protocol.attrib["name"] + "/" + service.attrib["name"]
                hcan_map[path] = HCAN_ProtocolEntry(
                    protocol_id=int(protocol.attrib["id"]),
                    protocol_name=protocol.attrib["name"],
                    service_id=int(service.attrib["id"]),
                    service_name=service.attrib["name"],
                    message_map=message_map,
                )

        new_protocol_instance = ResolvedProtocolInstance(
            "HCAN", location_info
        )
        # o = self.__description_dictionary["PROTOCOL"].get_type_map()
        new_protocol_instance.set_type(
            "HCAN",#descriptor.get_name(), 
            ProtocolType.Key["HCAN"]
        )
        #new_protocol_instance.insert_description_list("PARAMETER", parameter_set)
        new_protocol_instance.set_protocol_map(hcan_map)

        self.__instance_dictionary["PROTOCOL"].insert(
            new_protocol_instance, ProtocolType.Key["HCAN"]
        )



    def save(self, filename) -> None:
        ''' Save Resolver instance and description dictionary to file.'''
        # make pickling easier:
        self.__instance_dictionary["APP"].prepare_pickle()

        with open(filename + ".pkl", "wb") as f:
            pickle.dump(self.__description_dictionary, f, pickle.HIGHEST_PROTOCOL)
            pickle.dump(self.__instance_dictionary, f, pickle.HIGHEST_PROTOCOL)