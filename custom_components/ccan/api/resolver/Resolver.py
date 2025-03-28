import pickle
from numbers import Number
import hashlib


# Parser Definitions:
from .Definitions import (
    ParsedDeviceInstance,
    ParsedHADeviceInstance,    
    ParsedAppInstance,
    ParsedControllerInstance,
    ParsedEvent,
    ParsedMappingList,
)
from .Definitions import (
    ParsedAliasDefinition,
    ParsedDeviceDescription,
)  # , ParsedControllerDescription
from .Definitions import (
    ParsedGeneralAppDescription,
    ParsedAutomation,
    ParsedVariableName,
    ParsedSensorDriverDescriptionList,
    ParsedTransportAdapterDescriptionList,
)
from .Definitions import (
    SensorDriverTypeKeys,
    CommunicationDriverTypeKeys,
    ParsedCommunicationDriverDescriptionList,
)  # SupportedVariableTypes,
from .Definitions import (
    DriverDescription,
    DeviceDescription,
    TemplateDescription,
    BoardDescription,
)
from .Definitions import (
    BoardInstance,
    DeviceInstance,
    OfferedConnection,
    ConnectionSet,
    UsedConnection,
)
from .Definitions import (
    MappingDescription,
    MappingDescriptionSet,
    ParameterSet,
)  # DriverListEntry, VariableParameterSet
from .Definitions import ParsedProtocolAdapterDescriptionList
from .Definitions import (
    ParsedParameterDescriptionList,
    HCAN_Message,
    HCAN_ProtocolEntry,
)
from .Definitions import (
    ExternalMappingDescription,
    MixedMappingDescriptionSet,
    ParsedProtocol,
    ParsedVariableInExpression,
    Operator,
    ParsedSymbol,
)
from .Definitions import ParsedExportList
from .Definitions import (
    ParsedVariableInstance,
    ParsedTemplateVariableInstance,
)  # FunctionExpression, ElementTypeKey, OperatorTypeKey, Operator,ExpressionElement,
from .Definitions import ParamListInfo  # VariableTypeKey, Variable, DeviceVariable,


from .ResolverElements import (
    DeviceAttribute,
    ResolvedSensorDriverDescriptionDictionary,
    ResolvedCommunicationDriverDescriptionDictionary,
)
from .ResolverElements import (
    ResolvedTransportAdapterDescriptionDictionary,
    ResolvedAdditionalProtocolDescriptionDictionary,
)

from .ResolverElements import (
    ResolvedConnection,
    ResolvedParameter,
    ResolvedVariable,
    ResolvedAppInstance,
)  # , ResolvedVariableReference
from .ResolverElements import (
    ResolvedFunctionElement,
    ResolvedVariableElement,
    ResolvedConstantElement,
    ResolvedEventParameterElement,
    ResolvedEventDescription
    #ResolvedEventEquivalent,
    #ResolvedStateVariableEquivalent
)
from .ResolverElements import MappingType, ProtocolType, ResolvedMapping
from .ResolverElements import ResolvedDescription, ResolvedDeviceInstance, ResolvedHomeAssistantDeviceInstance
from .ResolverElements import ResolvedMap, ResolvedCheckedMap
from .ResolverElements import ResolvedAppDescription
from .ResolverElements import ResolvedDeviceDescription
from .ResolverElements import ResolvedParameterDescriptionMap
from .ResolverElements import ResolvedAdditionalProtocolsDictionary
from .ResolverElements import ResolvedProtocolInstance
from .ResolverElements import ResolvedAppDescriptionDictionary
from .ResolverElements import ResolvedInstanceDictionaryBase
from .ResolverElements import ResolvedDeviceDescriptionDictionary
from .ResolverElements import ResolvedUsedDriverInstance
from .ResolverElements import ResolvedVariableReference
from .ResolverElements import ResolvedEventParameterElement
from .ResolverElements import ResolvedEventInstance
from .ResolverElements import ResolvedEventDescription
from .ResolverElements import SerializedFunctionExpression
from .ResolverElements import AliasEventPair
from .ResolverElements import get_automatic_parameter_variable_prefix

from .ResolverElements import DriverClassType
from .ParameterStore import ParameterStore
from .ResolverError import ResolverError
from api.PyCCAN_Warnings import CCAN_Warnings

from .ResolverStore import ResolverStore

from .ResolverElements import ParameterFormat

from .ResolverElements import FunctionExpression



from .EventCollector import EventCollectorFactory, EventCollector


class Resolver:
    #ILLEGAL_DEVICE_ID = -1
    TEMPLATE_TYPE = -1
    ILLEGAL_DRIVER_ID = -1

    def __init__(self):

        self.__include_path = None
        self.resolver_store = ResolverStore()
        self.__automatic_variable_count = 0    
        self.__home_assistant_enabled = False

    def OBSO__get_local_app_id(self, my_app_name):
        app_instance = self.resolver_store.get_instance_dictionary("APP").get_entry_by_name(my_app_name)

        if not app_instance.is_app():
            return 0

        controller_instance = self.resolver_store.get_instance_dictionary("APP").get_entry_by_name(
            app_instance.get_controller_name()
        )
        new_local_id = controller_instance.get_new_local_id()
        return new_local_id

    def do(self, parsed_list, prefix, parameter_store, include_path):
        self.__include_path = include_path

        if parsed_list is None:
            pass

        for item in parsed_list:
            if isinstance(item, ParsedSensorDriverDescriptionList):
                self.__insert_element_descriptions(
                    item, 
                   self.resolver_store.get_description_dictionary("SENSOR_DRIVER"),
                    parameter_store
                )

            elif isinstance(item, ParsedCommunicationDriverDescriptionList):
                self.__insert_element_descriptions(
                    item, 
                    self.resolver_store.get_description_dictionary("COMMUNICATION_DRIVER"),
                    parameter_store
                )

            elif isinstance(item, ParsedTransportAdapterDescriptionList):
                self.__insert_element_descriptions(
                    item, 
                    self.resolver_store.get_description_dictionary("TRANSPORT_ADAPTER"),
                    parameter_store
                )

            elif isinstance(item, ParsedProtocolAdapterDescriptionList):
                self.__insert_element_descriptions(
                    item, 
                    self.resolver_store.get_description_dictionary("PROTOCOL"),
                    parameter_store
                )

            elif isinstance(item, ParsedDeviceDescription):
                self.__insert_device_description(item)

            elif isinstance(item, ParsedGeneralAppDescription):
                self.__insert_general_app_description(item)

            elif isinstance(item, ParsedAutomation):
                self.__evaluate_automation(item, prefix, parameter_store)

            else:
                raise ResolverError(
                    None,
                    f"Internal Resolving Error - not supported item {item}")
        self.__assign_variables_to_controllers()

        return

    ##################################################   CONTROLLER_STORE PREPARATION ############################################

    def __assign_variables_to_controllers(self):
        connect_success_in_loop = True

        if self.resolver_store.get_number_of_variable_entries() == 0:
            return

        # ensure that all variables have a connection to a controller:
        while connect_success_in_loop:
            for id, varDev in  self.resolver_store.get_instance_dictionary("VARIABLE"):
                # varDev.get_name())
                connect_success_in_loop = False

                if varDev.get_name().startswith("VAR::AUTOMATIC_NAME_EVENT::"):
                    print(id, varDev.get_name())

                if varDev.is_connected() is False:
                    try:
                        var_expression = varDev.get_value()
                    except AttributeError:
                        pass
                    if isinstance(var_expression, list):
                        for elem in var_expression:
                            if isinstance(elem, ResolvedVariableElement):
                                pass
                            #    referenced_var = self.__instance_dictionary["VARIABLE"].get_entry_by_name(elem.get_name())
                            #    controller_names = referenced_var.get_reference_controller_names()
                            #    varDev.add_reference_controller_names(controller_names)

                            if isinstance(elem, ResolvedEventParameterElement):
                                referenced_device_name = (
                                    elem.get_reference_device_name()
                                )
                                controller_name = (
                                    self.resolve_controller_by_device_name(
                                        referenced_device_name
                                    )
                                )
                                varDev.add_reference_controller_names(controller_name)
                                connect_success_in_loop = True

        for id, var in  self.resolver_store.get_instance_dictionary("VARIABLE"):
            # is the variable an expression?
            try:
                var_expression = var.get_value()
                if isinstance(var_expression, list):
                    # this controller needs to be referenced by each variable in the expression:
                    var_controller = var.get_reference_controller_names()

                    # add the controller to all variables recursively:
                    if var_controller != []:
                        self.add_references_to_variables_in_expression(
                            var_expression, var_controller
                        )

            except AttributeError:
                pass  # no check for device variables

        for id, var in  self.resolver_store.get_instance_dictionary("VARIABLE"):
            # post check: is a reference controller defined?
            if var.is_connected() is False:
                CCAN_Warnings.warn(
                    var.get_location(), f"Variable {var.get_name()} is not connected to a controller. It will be omitted in the controller configurations.")

    def add_references_to_variables_in_expression(
        self, my_var_expression, my_var_controller
    ):
        #reference_controller = []

        for elem in my_var_expression:
            if isinstance(elem, ResolvedVariableElement):
                referenced_var =  self.resolver_store.get_instance_by_name("VARIABLE",elem.get_name()) 
                referenced_var.add_reference_controller_names(my_var_controller)

                try:
                    var_expression = referenced_var.get_value()
                    if isinstance(var_expression, list):
                        # this controller needs to be referenced by each variable in the expression:
                        var_controller = referenced_var.get_reference_controller_names()

                        # add the controller to all variables recursively:
                        self.add_references_to_variables_in_expression(
                            var_expression, var_controller
                        )
                except:
                    pass

    ##################################################          DESCRIPTIONS       ###############################################

    def __insert_element_descriptions(self, my_parsed_element_list, my_dictionary, my_parameter_store):
        for element in my_parsed_element_list.list:
            new_description = ResolvedDescription(
                element.name, element.type, element.location_info
            )

            inserted_list = (
                element.parameter_description_list.parameter_name_list,
                element.parameter_description_list.parameter_type_list,
                element.parameter_description_list.parameter_constraints_list,
                element.parameter_description_list.parameter_defaults_list
            )
         
            new_description.insert_checked_description_list(
                "PARAMETER", inserted_list, ParameterStore.validate_parameter_types
            )
       
            # prepare degradation list:
            if element.degradation_description_list is not None:
                map_type = "DEGRADATION"
                degradation_list = ResolvedMap(map_type)
                for element in element.degradation_description_list:
                    degradation_list.insert(
                    element.name, element.explanation, element.location_info
                )
                new_description.insert_description_list(map_type, degradation_list)

            my_dictionary.insert(new_description)

        return

    def __insert_general_app_description(self, item):
        new_app = ResolvedAppDescription(item.name, item.type, item.location_info)
        # new_app.set_parameter_definition(item.parameter_description_list.parameter_name_list, item.parameter_description_list.parameter_type_list)
           
        # check for reserved parameter "controller address" if this a HW controller.
        if item.type == "CONTROLLER":
            if "ccan_address" not in item.parameter_description_list.parameter_name_list:
                raise ResolverError(
                        item.location_info,
                        f"The controller type {item.name} requires a parameter 'ccan_address'.")
            else:
                index = item.parameter_description_list.parameter_name_list.index("ccan_address")
                if item.parameter_description_list.parameter_type_list[index] != "CCAN_ADDRESS":
                    raise ResolverError(
                        item.location_info,
                        f"The controller type {item.name} requires a parameter 'ccan_address' with type 'CCAN_ADDRESS'. The current definition uses type {item.parameter_description_list.parameter_type_list[index]}.")
        
        new_app.insert_checked_description_list(
            "PARAMETER",
            (
                item.parameter_description_list.parameter_name_list,
                item.parameter_description_list.parameter_type_list,
            ),
            ParameterStore.validate_parameter_types,
        )
           
        connection_map = ResolvedMap("CONNECTION")
        for element in item.connection_description_list:            
            if self.resolver_store.is_class_supported("COMMUNICATION_DRIVER", element.driver_type):
                # "SENSOR_DRIVER"?
                connection_map.insert(
                    element.name, element.driver_type, element.location_info
                )
        new_app.insert_description_list("CONNECTION", connection_map)

        # prepare sensor connection map:
        map_type = "SENSOR_DRIVER"
        sensor_map = ResolvedCheckedMap(
            map_type, self.resolver_store.get_description_dictionary(map_type)
        )
        for element in item.offered_connection_usage.list:
            sensor_map.insert(element.name, element.driver_list, element.location_info)
        new_app.insert_description_list(map_type, sensor_map)

        map_type = "COMMUNICATION_DRIVER"
        if item.offered_communication_usage is not None:
            # prepare communication_driver map:
            communication_map = ResolvedCheckedMap(
                map_type, self.resolver_store.get_description_dictionary(map_type)
            )
            for element in item.offered_communication_usage.list:
                communication_map.insert(
                    element.name, element.driver_list, element.location_info
                )
            new_app.insert_description_list(map_type, communication_map)

        # prepare transport adapter map:
        map_type = "TRANSPORT_ADAPTER"
        if item.offered_adapter_usage is not None:
            transport_adapter_map = ResolvedCheckedMap(
                map_type, self.resolver_store.get_description_dictionary(map_type)
            )
            transport_adapter_map.insert(
                map_type, item.offered_adapter_usage.list, element.location_info
            )
            new_app.insert_description_list(map_type, transport_adapter_map)

        # prepare degradation list:
        map_type = "DEGRADATION"
        degradation_list = ResolvedMap(map_type)
        for element in item.degradation_description_list:
            degradation_list.insert(
                element.name, element.explanation, element.location_info
            )
        new_app.insert_description_list(map_type, degradation_list)

        # insert in description and instance dictionary:
        self.resolver_store.add_to_dictionaries("APP",new_app)

    def __insert_device_description(self, item):
        new_device = ResolvedDeviceDescription(item.name, item.type, item.location_info)
        # new_device.set_parameter_definition(item.parameter_description_list.parameter_name_list, item.parameter_description_list.parameter_type_list)
        new_device.insert_checked_description_list(
            "PARAMETER",
            (
                item.parameter_description_list.parameter_name_list,
                item.parameter_description_list.parameter_type_list,
            ),
            ParameterStore.validate_parameter_types,
        )

        # check of device parameter types:
        # needed_parameter_types = item.parameter_description_list.parameter_type_list
        # self.__check_types(needed_parameter_types, SupportedVariableTypes, parsed_device_description.location_info)
        attribute_list = []
        for attribute in item.attribute_list:
            try:
                attribute_list.append(str(DeviceAttribute(attribute)))
            except:
                raise ResolverError(
                    item.location_info,f"The attribute '{attribute}' is not defined for a device description." )
        new_device.insert_description_list("ATTRIBUTES", attribute_list)

        var_map = ResolvedParameterDescriptionMap("VARIABLE")
        if item.status_variable_description_list is not None:
            for name, format in zip(
                item.status_variable_description_list.parameter_name_list,
                item.status_variable_description_list.parameter_type_list,
            ):
                var_map.insert(name, format, item.location_info)
        new_device.insert_description_list("VARIABLE", var_map)

        connection_map = ResolvedMap("CONNECTION")
        for element in item.connection_description_list:
            if self.resolver_store.is_class_supported("SENSOR_DRIVER",element.driver_type):
                connection_map.insert(
                    element.name, element.driver_type, element.location_info
                )
            elif self.resolver_store.is_class_supported("COMMUNICATION_DRIVER",element.driver_type):
                connection_map.insert(
                    element.name, element.driver_type, element.location_info
                )
            elif item.type == "TEMPLATE" and element.driver_type == "CONTROLLER":
                connection_map.insert(
                    element.name, element.driver_type, element.location_info
                )
            else:
                raise ResolverError(
                    element.location_info,#.location_info,
                    "The device/template has an invalid connection definition.",
                )

        if item.type == "TEMPLATE":
            new_device.insert_description_list("AUTOMATION", item.automation)

        new_device.insert_description_list("CONNECTION", connection_map)

        # status_parameter_types = item.status_variable_description_list.parameter_type_list

        # prepare in/out event map:
        event_map = ResolvedMap("EVENT")
        for element in item.event_description_list:
            new_event_description = ResolvedEventDescription(
                element.name, element.in_out_type, element.location_info
            )
            inserted_list = (
                element.parameter_description_list.parameter_name_list,
                element.parameter_description_list.parameter_type_list,
            )
            new_event_description.insert_checked_description_list(
                "PARAMETER", inserted_list, ParameterStore.validate_parameter_types
            )
            # new_event_description.set_parameter_definition(element.parameter_description_list.parameter_name_list, element.parameter_description_list.parameter_type_list)
            event_map.insert(element.name, new_event_description, element.location_info)
        new_device.insert_description_list("EVENT", event_map)

        # prepare degradation list:
        degradation_list = ResolvedMap("DEGRADATION")
        if item.type == "DEVICE":
            for element in item.degradation_description_list:
                degradation_list.insert(
                    element.name, element.explanation, element.location_info
                )
        new_device.insert_description_list("DEGRADATION", degradation_list)

        # insert in description dictionary:
        if item.type == "DEVICE":
            self.resolver_store.add_to_dictionaries("DEVICE",new_device)           
        elif item.type == "HOME_ASSISTANT_DEVICE":
            self.resolver_store.add_to_dictionaries("HOME_ASSISTANT_DEVICE",new_device)          
        else:
            self.resolver_store.add_to_dictionaries("DEVICE",new_device,Resolver.TEMPLATE_TYPE)            

    #######################################################    AUTOMATION      #############################################################

    def __evaluate_automation(self, parsed_statements, prefix, parameter_store):
        for statement in parsed_statements.list:
            if isinstance(statement, ParsedAliasDefinition):
                self.__insert_alias(statement, prefix, parameter_store)
            elif isinstance(statement, ParsedExportList):
                self.__insert_export_events(statement, prefix, parameter_store)  
            elif isinstance(statement, ParsedControllerInstance):
                self.__insert_app_instance(statement, parameter_store)
            elif isinstance(statement, ParsedDeviceInstance):
                self.__insert_device_instance(statement, prefix, parameter_store)
            elif isinstance(statement, ParsedHADeviceInstance):
                self.__insert_ha_device_instance(statement, prefix, parameter_store)
            elif isinstance(statement, ParsedAppInstance):
                self.__insert_app_instance(statement, parameter_store)
            elif isinstance(statement, ParsedMappingList):
                self.__insert_mapping_list(statement, prefix, parameter_store)
            elif isinstance(statement, ParsedProtocol):
                self.__insert_protocol(statement, parameter_store)
            elif isinstance(statement, ParsedVariableInstance):
                self.__insert_variable_instance(statement, prefix, parameter_store)
            elif isinstance(statement, ParsedTemplateVariableInstance):
                self.__insert_template_variable_instance(
                    statement, prefix, parameter_store
                )
            else:
                raise ResolverError(
                    None, "Internal Resolving Error - found not supported automation item '{statement}'.")       
        return

    def __insert_alias(self, parsed_alias_definition, prefix, parameter_store):
        new_alias = parsed_alias_definition.name
        value = parsed_alias_definition.expression

        if isinstance(value, FunctionExpression):
            value = parameter_store.simplify(value, ParameterFormat("FLOAT"))

        try:
            parameter_store.insert_alias(new_alias, value)
        except ResolverError as e:
            raise ResolverError(
                parsed_alias_definition.location_info, e.get_error_text()
            )
        return

    def __insert_protocol(self, protocol, parameter_store):
        # im dictionary nach Beschreibung suchen
        try:
            descriptor = self.resolver_store.get_description_by_name("PROTOCOL",protocol.name)          
        except KeyError:
            raise ResolverError(
                protocol.location_info,
                "The protocol type " + protocol.name + " is not defined.",
            )

        parameter_name_list, parameter_type_list, parameter_constraints_list, parameter_defaults_list = descriptor.get_description_list(
            "PARAMETER"
        )
        parameter_set = self.resolve_fixed_parameter_list(
            parameter_store,
            protocol.parameter_list,
            parameter_name_list,
            parameter_type_list,
            protocol.location_info,
        )

        if protocol.name == "HCAN":
            self.resolver_store.add_hcan_support_from_file(self.__include_path, parameter_set[0], protocol.location_info)         
        elif protocol.name == "HOME_ASSISTANT":
            self.__home_assistant_enabled = True

        return

    def __insert_app_instance(self, parsed_app_instance, parameter_store):
        # check type:
        descriptor = self.resolver_store.get_description_by_name("APP",parsed_app_instance.type)     
        if descriptor is None:
            raise ResolverError(
                parsed_app_instance.location_info,
                "Controller type <" + parsed_app_instance.type + "> is not defined.",
            )

        resolved_app = ResolvedAppInstance(
            parsed_app_instance.name, parsed_app_instance.location_info
        )
        resolved_app.set_type(
            parsed_app_instance.type,
            self.resolver_store.get_type_id_by_name("APP",parsed_app_instance.type)         
        )

        # read and check uuid string:

        if parsed_app_instance.uuid is None and descriptor.is_type("APP") is False:
            CCAN_Warnings.warn(
                parsed_app_instance.location_info,
                " No UUID is defined for controller. This does not allow an automated update later.",
            )

        if (
            parsed_app_instance.uuid is not None
            and not parsed_app_instance.uuid.startswith("0x")
        ):
            raise ResolverError(
                parsed_app_instance.location_info,
                "UUID "
                + parsed_app_instance.uuid
                + " is a hexadecimal value and needs to start with '0x'",
            )
        else:
            resolved_app.insert_description_list("UUID", parsed_app_instance.uuid)

        # checks missing: do the pins exist in the controller type? We assume: yes

        # resolve parameters:
        (parameter_name_list, parameter_type_list) = descriptor.get_description_list(
            "PARAMETER"
        )
        parameter_values = self.resolve_fixed_parameter_list(
            parameter_store,
            parsed_app_instance.parameter_list,
            parameter_name_list,
            parameter_type_list,
            parsed_app_instance.location_info,
        )

        resolved_app.insert_description_list("PARAMETER", parameter_values)

        if descriptor.is_type("APP") is True:
            connections = parameter_store.resolve_connection_list(
                parsed_app_instance.connected_to, parsed_app_instance.location_info
            )

            resolved_connection_set = self.__resolve_connection_parameter(
                descriptor,
                "CONNECTION",
                "COMMUNICATION_DRIVER",
                connections,
                parsed_app_instance.location_info,
            )

            resolved_app.insert_description_list("CONNECTION", resolved_connection_set)
            resolved_app.set_controller_name(resolved_connection_set[0].get_app_name())
   
        self.resolver_store.insert_instance("APP",resolved_app)

        used_sensor_drivers = self.__get_instance_list(
            resolved_app,
            "SENSOR_DRIVER",
            parsed_app_instance.sensor_usage_list,
            descriptor,
            None,
            parameter_store,
            True,
        )
        resolved_app.insert_description_list("SENSOR_DRIVER", used_sensor_drivers)

        if descriptor.is_type("APP") is False:
            used_communication_drivers = self.__get_instance_list(
                resolved_app,
                "COMMUNICATION_DRIVER",
                parsed_app_instance.communication_usage_list,
                descriptor,
                None,
                parameter_store,
            )
            resolved_app.insert_description_list(
                "COMMUNICATION_DRIVER", used_communication_drivers
            )

            used_transport_adapters = self.__get_instance_list(
                resolved_app,
                "TRANSPORT_ADAPTER",
                parsed_app_instance.adapter_usage_list,
                descriptor,
                used_communication_drivers,
                parameter_store,
            )
            resolved_app.insert_description_list(
                "TRANSPORT_ADAPTER", used_transport_adapters
            )

    def __insert_template_variable_instance(
        self, parsed_variable_instance, prefix, parameter_store
    ):
        resolved_expression = parameter_store.resolve_functional_expression(
            parsed_variable_instance.expression
        )
        var_name, alias_flag = self.__resolve_prefixed_name(
            prefix,
            parameter_store,
            parsed_variable_instance.name,
            parsed_variable_instance.location_info,
        )

        # vorläufig:
        template_name = prefix

        # get template instance as far as defined so far:
        preliminary_template_instance = self.resolver_store.get_instance_by_name("DEVICE", template_name)       
        template_qualifier = preliminary_template_instance.get_type()
        template_descriptor = self.resolver_store.get_description_by_name("DEVICE",template_qualifier)

        variable_map = template_descriptor.get_description_list("VARIABLE")

        # isolate state variable at the end:
        variable_name = var_name.split("::")[-1]
        try:
            format = variable_map.get_by_name(variable_name)
        except KeyError:
            raise ResolverError(
                parsed_variable_instance.location_info,
                "Template state variable " + variable_name + " is not defined.",
            )

        expression_format = ParameterFormat(format)
        self.__insert_variable(
            var_name,
            expression_format,
            resolved_expression,
            prefix,
            parameter_store,
            None,
            None,
            False,
            parsed_variable_instance.location_info,
        )

    def __insert_variable_instance(
        self, parsed_variable_instance, prefix, parameter_store
    ):
        # default format:
        default_expression_format = ParameterFormat("FLOAT")

        resolved_expression = parameter_store.resolve_functional_expression(
            parsed_variable_instance.expression
        )
        var_name, alias_flag = self.__resolve_prefixed_name(
            prefix,
            parameter_store,
            parsed_variable_instance.name,
            parsed_variable_instance.location_info,
        )

        if alias_flag:
            raise ResolverError(
                parsed_variable_instance.location_info,
                "Internal Error when resolving variables.",
            )

        full_var_name = "VAR::" + var_name
        self.__insert_variable(
            full_var_name,
            default_expression_format,
            resolved_expression,
            prefix,
            parameter_store,
            None,
            None,
            False,
            parsed_variable_instance.location_info,
        )

        # add connection if available:
        if parsed_variable_instance is None:
            connections = parameter_store.resolve_connection_list(
                parsed_variable_instance.connected_to,
                parsed_variable_instance.location_info,
            )
            var = self.resolver_store.get_instance_by_name("VARIABLE",full_var_name)
            var.add_reference_controller_names(connections)

        # except KeyError:
        #    raise ResolverError(parsed_variable_instance.location_info, "Expression <" + parsed_variable_instance.expression + "> cannot be fully resolved. Reference to an undefined status variable is provided.")

    def __insert_variable(
        self,
        my_name,
        my_format,
        my_expression,
        prefix,
        parameter_store,
        event_descriptor,
        reference_device_name,
        my_parameter_event_descriptor,
        my_location_info,
    ):
        serialized_expression = self.__resolve_variables_in_expression(
            my_expression,
            prefix,
            parameter_store,
            event_descriptor,
            reference_device_name,
            my_parameter_event_descriptor,
            my_location_info,
        )
        return self.__insert_resolved_variable(
            my_name, serialized_expression, my_format, my_location_info
        )

    def __insert_resolved_variable(
        self,
        my_name,
        my_serialized_expression,
        my_format,
        my_location_info,
        my_target_controller=None,
    ):
        serialized_expression = self.__rework_serialized_expression(
            my_serialized_expression
        )

        if my_name is None:
            # var_name = self.__resolve_prefixed_name(prefix, parameter_store,str(self.__instance_dictionary["VARIABLE"].get_number_of_entries()),my_location_info)[0]
            full_var_name = (
                get_automatic_parameter_variable_prefix()
                + str(serialized_expression)
                + "_"
                + str(self.__automatic_variable_count)
            )
            self.__automatic_variable_count += 1

        else:
            full_var_name = my_name

        try:
            (idx, value) = self.resolver_store.get_id_and_instance_by_name("VARIABLE",full_var_name)

        except KeyError:
            resolved_variable = ResolvedVariable(
                full_var_name, my_format, serialized_expression, my_location_info
            )
            if my_target_controller is not None:
                resolved_variable.add_reference_controller_names(my_target_controller)
            (name, idx) = self.resolver_store.insert_instance("VARIABLE",resolved_variable)
        
        # create reference:
        reference_expression = SerializedFunctionExpression(
            [ResolvedVariableElement(full_var_name, idx)]
        )
        return reference_expression

    def __rework_serialized_expression(self, my_expression):
        try:
            expression_list = my_expression.get_value()
        except AttributeError:
            pass
        result_list = []

        for element in expression_list:
            if isinstance(element, Number):
                result_list.append(
                    ResolvedConstantElement(element, ParameterFormat("FLOAT"))
                )
            else:
                result_list.append(element)
        return SerializedFunctionExpression(result_list)


    def __insert_export_events(self, statement, prefix, parameter_store):
        location_info = statement.location_info
        for event in statement.event_list:                
                resolved_event = self.__resolve_parsed_event(True, event, prefix, location_info, parameter_store, False, None)
                event_path = resolved_event.get_description_list("EVENT_PATH")[0]+"::" +resolved_event.get_name()
                # check event for characteristics:
                
                if resolved_event.get_type() != "CCAN":
                    raise ResolverError(location_info, f"Event {event_path} is not a CCAN event. This is not supported in EXPORT statements.") 
                if resolved_event.is_template():
                    raise ResolverError(location_info, f"Event {event_path} is a template event. This is not supported in EXPORT statements.")
                if resolved_event.is_alias():
                    raise ResolverError(location_info, f"Event {event_path} is an alias event. This is not supported in EXPORT statements.")
                if resolved_event.get_description_list("PARAMETER") != []: 
                    raise ResolverError(location_info, f"For event {event_path} parameters are provided here. This is not supported in EXPORT statements.")
                 

                self.__add_to_mapping_table(resolved_event, None)


               
    def __insert_ha_device_instance(self, parsed_instance, prefix, parameter_store):
   # check type:

        if not self.__home_assistant_enabled:
            raise ResolverError(
                parsed_instance.location_info,
                "Add 'ENABLE HOME_ASSISTANT()' in your automation to enable Home Assistant device support.")  

        try:
            descriptor = self.resolver_store.get_description_by_name("HOME_ASSISTANT_DEVICE", parsed_instance.type)
        except KeyError:
            raise ResolverError(
                parsed_instance.location_info,
                f"Device type '{parsed_instance.type}' is not defined.",
            )

        (instance_name, alias_flag) = self.__resolve_prefixed_name(
            prefix, parameter_store, parsed_instance.name, parsed_instance.location_info
        )

        # checks missing: do the pins exist in the controller type? We assume: yes

        # resolve parameters:
        (parameter_name_list, parameter_type_list) = descriptor.get_description_list(
            "PARAMETER"
        )
        parameter_values = self.resolve_fixed_parameter_list(
            parameter_store,
            parsed_instance.parameter_list,
            parameter_name_list,
            parameter_type_list,
            parsed_instance.location_info,
            descriptor.is_type("TEMPLATE"),            
        )


        resolved_instance = ResolvedHomeAssistantDeviceInstance(
            instance_name, parsed_instance.location_info
        )

        resolved_instance.set_type(
            parsed_instance.type,
            self.resolver_store.get_type_id_by_name("HOME_ASSISTANT_DEVICE", parsed_instance.type)         
        )

        resolved_instance.insert_description_list("PARAMETER", parameter_values)
      
        event_description_map = descriptor.get_description_list(
            "EVENT"
        )
        variable_description_map = descriptor.get_description_list(
            "VARIABLE"
        )                    
        equivalent_map, prefix_map, open_parameters = self.resolve_equivalent_list(parsed_instance.equivalent_list,event_description_map, variable_description_map, prefix, parameter_store)
        resolved_instance.insert_description_list("EQUIVALENT_MAP",equivalent_map)
        resolved_instance.insert_description_list("EVENT_PREFIX_MAP",prefix_map)
        resolved_instance.insert_description_list("OPEN_PARAMETERS_LIST",open_parameters)
                
        self.resolver_store.insert_instance("HOME_ASSISTANT_DEVICE",resolved_instance)

    def __insert_device_instance(self, parsed_instance, prefix, parameter_store):
        # check type:
        try:
            descriptor = self.resolver_store.get_description_by_name("DEVICE", parsed_instance.type)
        except KeyError:
            raise ResolverError(
                parsed_instance.location_info,
                "Device type '" + parsed_instance.type + "' is not defined.",
            )

        (instance_name, alias_flag) = self.__resolve_prefixed_name(
            prefix, parameter_store, parsed_instance.name, parsed_instance.location_info
        )

        # checks missing: do the pins exist in the controller type? We assume: yes

        # resolve parameters:
        (parameter_name_list, parameter_type_list) = descriptor.get_description_list(
            "PARAMETER"
        )
        parameter_values = self.resolve_fixed_parameter_list(
            parameter_store,
            parsed_instance.parameter_list,
            parameter_name_list,
            parameter_type_list,
            parsed_instance.location_info,
            descriptor.is_type("TEMPLATE"),
        )

        # resolve connection:
        connections = parameter_store.resolve_connection_list(
            parsed_instance.connected_to, parsed_instance.location_info
        )
        try:
            resolved_connection_set = self.__resolve_connection_parameter(
                descriptor,
                "SENSOR_DRIVER",
                "SENSOR_DRIVER",
                connections,
                parsed_instance.location_info,
            )
        except ResolverError:
            resolved_connection_set = self.__resolve_connection_parameter(
                descriptor,
                "COMMUNICATION_DRIVER",
                "COMMUNICATION_DRIVER",
                connections,
                parsed_instance.location_info,
            )

        resolved_instance = ResolvedDeviceInstance(
            instance_name, parsed_instance.location_info
        )
        resolved_instance.set_type(
            parsed_instance.type,
            self.resolver_store.get_type_id_by_name("DEVICE",parsed_instance.type
            )
        )
        resolved_instance.insert_description_list("PARAMETER", parameter_values)
        resolved_instance.insert_description_list("CONNECTION", resolved_connection_set)

        if descriptor.is_type("TEMPLATE"):
            self.resolver_store.insert_instance("DEVICE",resolved_instance) #, Resolver.ILLEGAL_DEVICE_ID

            resolved_instance.mark_as_template()
            alias_event_map = ResolvedMap("ALIAS_EVENTS")
            resolved_instance.insert_description_list("ALIAS_EVENTS", alias_event_map)

            alias_variable_map = ResolvedMap("ALIAS_VARIABLES")
            resolved_instance.insert_description_list(
                "ALIAS_VARIABLES", alias_variable_map
            )

            self.__resolve_template_instance(
                parsed_instance, descriptor, prefix, parameter_values, connections
            )
        else:
            # add device instance variables:
            vartab = descriptor.get_description_list("VARIABLE").get_as_list()
            resolved_references = []
            for id, name, var_format in vartab:
                var_name = instance_name + "::" + name
                resolved_variable = ResolvedVariable(
                    var_name,
                    ParameterFormat(var_format),
                    None,
                    parsed_instance.location_info,
                )
                app_name = resolved_connection_set[0].get_app_name()
                app_instance = self.resolver_store.get_instance_by_name("APP",app_name)
              
                controller_name = self.resolve_controller_by_app_name(
                    app_instance.get_name()
                )
                resolved_variable.add_reference_controller_names(controller_name)

                # insert variable instance in global var tab:
                self.resolver_store.insert_instance("VARIABLE",resolved_variable)

                # create local reference for this instance:
                resolved_variable_reference = ResolvedVariableReference(
                    var_name, resolved_variable, parsed_instance.location_info
                )
                resolved_references.append(resolved_variable_reference)

            # add references to device:
            resolved_instance.insert_description_list("VARIABLE", resolved_references)
            self.resolver_store.insert_instance("DEVICE",resolved_instance)
        return

    def __insert_mapping_list(self, parsed_mapping_list, prefix, parameter_store):
        from_event = parsed_mapping_list.from_event
        to_events = parsed_mapping_list.to_events
        location_info = parsed_mapping_list.location_info

        # investigate FROM mapping:
        resolved_from_event = self.__resolve_parsed_event(
            True, from_event, prefix, location_info, parameter_store, False, None
        )

        # If the from event is a template event, it shall not have any parameter conditions.
        if (
            resolved_from_event.is_alias() is True
            and str(resolved_from_event.get_mapping_type()) != "SIMPLE"
        ):
            raise ResolverError(
                location_info,
                "It is not allowed to have a triggering template with a parameter condition.",
            )

        # investigate TO mappings:     
        for to_event in to_events:
            # if to_event.protocol_name == "CCAN":
            resolved_to_event = self.__resolve_parsed_event(
                False,
                to_event,
                prefix,
                location_info,
                parameter_store,
                True,
                from_event,
            )

            # alias events get collected:
            if (
                resolved_from_event.is_alias() is True
                and resolved_to_event.is_alias() is False
            ):
                # print("ADD [ IN  ] ALIAS FOR " + resolved_from_event.get_name() + " AS " + resolved_to_event.get_name())
                self.__add_alias_event(
                    prefix, "IN", resolved_from_event, resolved_to_event
                )
            elif (
                resolved_from_event.is_alias() is False
                and resolved_to_event.is_alias() is True
            ):
                # print("ADD [ OUT ] ALIAS FOR " + resolved_to_event.get_name() + " AS " + resolved_from_event.get_name())
                self.__add_alias_event(
                    prefix, "OUT", resolved_to_event, resolved_from_event
                )

            elif (
                resolved_from_event.is_alias() is True
                and resolved_to_event.is_alias() is True
            ):
                raise ResolverError(
                    location_info,
                    "It is not allowed to map symbolic input mapping to symbolic output mapping.",
                )

            else:
                # self.__add_mapping(resolved_from_event, resolved_to_event, parameter_store)
                self.__add_resolved_mapping_pair(
                    resolved_from_event, resolved_to_event, prefix, parameter_store
                )

        return

    def __resolve_ccan_event(
        self,
        parameter_are_optional_flag,
        parsed_event,
        prefix,
        location_info,
        parameter_store,
    ):
        # check device:

        if isinstance(parsed_event.device_path_name,ParsedVariableInExpression):
            device_path_name = parsed_event.device_path_name.name
        else:
            device_path_name = parsed_event.device_path_name

        try:
            (device_name, alias_flag) = self.__resolve_prefixed_name(
                prefix, parameter_store, device_path_name, location_info
            )           
            device_id, device_instance = self.resolver_store.get_id_and_instance_by_name("DEVICE",device_name)                
                           
        except KeyError:
            raise ResolverError(
                location_info,
                "Device "
                + device_name
                + " does not exist. Mapping cannot be done.",
            )

        # check event:
        try:
            device_descriptor = self.resolver_store.get_description_by_name("DEVICE",device_instance.get_type())
            event_description_map = device_descriptor.get_description_list("EVENT")
            event_descriptor = event_description_map.get_by_name(
                parsed_event.event_name
            )
            event_id = event_description_map.get_id_by_name(parsed_event.event_name)

        except KeyError:
            raise ResolverError(
                location_info,
                f"Event {parsed_event.event_name} does not exist for the device type {device_instance.get_type()}. Mapping cannot be done.",
            )

        template_flag = device_instance.is_template()

        return device_name, device_id, event_id, event_descriptor, alias_flag, template_flag

    def __resolve_parsed_event(
        self,
        parameter_are_optional_flag,
        parsed_event,
        prefix,
        location_info,
        parameter_store,
        parameter_event_reference_allowed,
        my_from_event,
    ) -> ResolvedEventInstance:
        # test protocol type:
        try:
            protocol_type = ProtocolType(parsed_event.protocol_name)
        except KeyError:
            raise ResolverError(
                location_info,
                "Protocol mapping "
                + parsed_event.protocol_name
                + " is not supported for mappings.",
            )

        resolved_event = ResolvedEventInstance(parsed_event.event_name, location_info)
        resolved_event.set_type(str(protocol_type), protocol_type.get_key())

        if protocol_type.is_ccan():
            device_name, device_id, event_id, event_descriptor, alias_flag, template_flag = (
                self.__resolve_ccan_event(
                    parameter_are_optional_flag,
                    parsed_event,
                    prefix,
                    location_info,
                    parameter_store,
                )
            )

            if event_descriptor.has_direction("IN"):
                resolved_event.set_direction("IN")
            else:
                resolved_event.set_direction("OUT")  

            resolved_event.set_alias_flag(alias_flag)
            resolved_event.set_template_flag(template_flag)

            resolved_event.insert_description_list(
                "EVENT_PATH", [device_name, device_id]
            )
            resolved_event.insert_description_list(
                "EVENT_TYPE", [event_descriptor.get_name(), event_id]
            )

            # get controller_name:
            controller_name = self.resolve_controller_by_device_name(device_name)
            resolved_event.set_controller_name(controller_name)

            # get descriptor for the parameters:
            (parameter_name_list, parameter_type_list) = (
                event_descriptor.get_description_list("PARAMETER")
            )

        else:
            if str(protocol_type) != "HCAN":
                raise ResolverError(
                    location_info, "Protocol <" + protocol_type + "> is not supported."
                )

            (device_name, alias_flag) = self.__resolve_prefixed_name(
                prefix, parameter_store, parsed_event.device_path_name, location_info
            )

            protocol = self.resolver_store.get_instance_by_name("PROTOCOL",str(protocol_type))
            protocol_map = protocol.get_protocol_map()

            ##### check and insert path ######
            resolved_path = parameter_store.resolve_parameter_list(
                [parsed_event.device_path_name],
                ["path"],
                ["STRING"],
                parameter_event_reference_allowed,
                parsed_event.location_info,
            )

            try:
                protocol_entry = protocol_map[resolved_path[0].get_value()]
            except KeyError:
                raise ResolverError(
                    location_info,
                    "Mapping path <"
                    + resolved_path
                    + "> is not defined for protocol "
                    + protocol_type,
                )

            pseudo_device_name = (
                str(protocol_type) + '("' + resolved_path[0].get_value() + '")'
            )
            # ToDo: no path id, as this requires a strange multiplication to ensure the right order..:
            resolved_event.insert_description_list(
                "EVENT_PATH",
                [
                    pseudo_device_name,
                    (protocol_entry.protocol_id + protocol_entry.service_id * 256),
                ],
            )

            ##### check event #######

            try:
                message_description = protocol_entry.message_map[
                    resolved_event.get_name()
                ]
            except KeyError:
                raise ResolverError(location_info,
                    f"Event '{resolved_event.get_name()}'is not defined for protocol {str(protocol_type)} .")

            resolved_event.insert_description_list(
                "EVENT_TYPE", [message_description.name, message_description.id]
            )

            parameter_name_list = (
                message_description.parameter_description_list.parameter_name_list
            )
            parameter_type_list = (
                message_description.parameter_description_list.parameter_type_list
            )

            # controller name remains unset.

        # resolve parameters:
        if parameter_are_optional_flag is True:
            #
            partially_resolved_parameter_list = (
                parameter_store.resolve_optional_parameter_list(
                    parsed_event.parameter_list,
                    parameter_name_list,
                    parameter_type_list,
                    parameter_event_reference_allowed,
                    parsed_event.location_info,
                )
            )
        else:
            partially_resolved_parameter_list = parameter_store.resolve_parameter_list(
                parsed_event.parameter_list,
                parameter_name_list,
                parameter_type_list,
                parameter_event_reference_allowed,
                parsed_event.location_info,
            )

        # check whether parameter results contain expressions - in that case convert it to a variable and replace the expression by a reference to the variable:
        resolved_parameter_list = []
        #expression_detected = False
        for parameter, parameter_format in zip(
            partially_resolved_parameter_list, parameter_type_list
        ):
            if parameter.is_expression() is True:
                try:
                    if isinstance(my_from_event,ParsedEvent):
                        (
                            dummy1,
                            dummy2,
                            dummy3,
                            from_event_descriptor,
                            dummy4,
                            dummy5
                        ) = self.__resolve_ccan_event(
                            parameter_are_optional_flag,
                            my_from_event,
                            prefix,
                            location_info,
                            parameter_store,
                        )
                    elif isinstance(my_from_event,ResolvedEventDescription):
                        from_event_descriptor = my_from_event
                    else:
                        from_event_descriptor = None

                    # resolved_expression   = parameter_store.resolve_functional_expression(parameter.get_value())
                    result = self.__resolve_expression(
                        parameter.get_value(),
                        prefix,
                        parameter_store,
                        from_event_descriptor,
                        device_name,
                        event_descriptor,
                        parsed_event.location_info,
                    )
                    parameter.set_value(result)
                    parameter_result = parameter

                    # value_reference = self.__insert_variable(None,ParameterFormat(parameter_format),SerializedFunctionExpression(parameter.get_value()),prefix,parameter_store, event_descriptor, device_name,from_event_descriptor, parsed_event.location_info)
                    # parameter_result = ResolvedParameter(parameter.get_name(),resolved_expression, ParameterFormat(parameter_format), None)

                except KeyError:
                    raise ResolverError(
                        location_info,
                        "Expression <"
                        + parsed_event.parameter_list[0][1]
                        + "> cannot be fully resolved. Reference to an undefined status variable is provided.",
                    )
                #expression_detected = True
            else:
                parameter_result = parameter

            resolved_parameter_list.append(parameter_result)

        resolved_event.insert_description_list("PARAMETER", resolved_parameter_list)

        return resolved_event

    def __resolve_template_event(self,my_template_event,my_parameter_store):
        result = []

        template_event_collectors = (
            EventCollectorFactory.create_event_collectors_from_event(
                my_template_event, self.resolver_store.get_instance_dictionary("DEVICE") )
        )

        for event, parameter_collector in template_event_collectors:
            parameter_collector_copy = EventCollector.copy_queue(
                    parameter_collector
                )
            is_expression_flags_from_parameters, simplified_parameters = (
                self.__simplify_cascaded_event_parameters(
                        parameter_collector_copy, my_parameter_store
                    )
                )
            if event not in result:
                result.append(event)
            else:
                raise ResolverError(
                   my_template_event.get_location(),
                    "When resolving this template event, a target event has been identified twice. Please check!"
                )

        return result


    def __add_resolved_mapping_pair(
        self, my_from_event, my_to_event, my_prefix, my_parameter_store
    ):
        from_event_collectors = (
            EventCollectorFactory.create_event_collectors_from_event(
                my_from_event, self.resolver_store.get_instance_dictionary("DEVICE") )
        )
        to_event_collectors = EventCollectorFactory.create_event_collectors_from_event(
            my_to_event, self.resolver_store.get_instance_dictionary("DEVICE") )


        for from_event, from_parameter_collector in from_event_collectors:
            for to_event, to_parameter_collector in to_event_collectors:
                # simplify parameter chains:
                from_parameter_collector_copy = EventCollector.copy_queue(
                    from_parameter_collector
                )
                is_expression_flags_from_parameters, simplified_from_parameters = (
                    self.__simplify_cascaded_event_parameters(
                        from_parameter_collector_copy, my_parameter_store
                    )
                )
                is_expression_flags_to_parameters, simplified_to_parameters = (
                    self.__simplify_cascaded_event_parameters(
                        to_parameter_collector, my_parameter_store
                    )
                )

                # if to event parameter is expression AND from_event has fixed parameter, insert this parameter:
                event_collector = (
                    EventCollectorFactory.create_collector_from_event_and_parameters(
                        to_event, simplified_to_parameters, simplified_from_parameters
                    )
                )
                is_expression_flags_to_parameters, final_to_event_parameters = (
                    self.__simplify_cascaded_event_parameters(
                        event_collector, my_parameter_store
                    )
                )

                # if event parameters are expressions, move them to variables:
                target_controller = to_event.get_controller_name()
                self.__move_expressions_to_variables(
                    is_expression_flags_from_parameters,
                    target_controller,
                    from_event,
                    simplified_from_parameters,
                )
                self.__move_expressions_to_variables(
                    is_expression_flags_to_parameters,
                    target_controller,
                    to_event,
                    final_to_event_parameters,
                )

                to_event.insert_description_list("PARAMETER", final_to_event_parameters)

                self.__add_to_mapping_table(from_event, to_event)

    def __simplify_cascaded_event_parameters(
        self, my_parameter_collector, my_parameter_store
    ):
        if my_parameter_collector.qsize() == 0:
            pass

        if my_parameter_collector.qsize() == 1:
            return [False], my_parameter_collector.get()

        # if len(my_parameters) == 0:
        #    return False, my_parameters

        # just a set of flat parameters?
        # if len(my_parameters[:]) == 1:
        #    # then we are finished
        #    return [False], my_parameters

        # the first parameters in the list are the unmodified parameters of the target event:
        result_parameters = my_parameter_collector.get()

        # extract values / expressions:
        result_parameter_values = []
        for result_parameter in result_parameters:
            # event_parameter_value = self.__get_event_parameter_value(result_parameter)
            result_parameter_values.append(
                my_parameter_store.get_parameter_value(result_parameter)
            )

        MaxSkipCount = len(result_parameters)
        changed_flag = [False] * len(result_parameters)
        is_expression_flag = [False] * len(result_parameters)
        skip_count = 0

        # process following events in reverse order, from sink to source:
        for i in range(my_parameter_collector.qsize()):
            event_parameters = my_parameter_collector.get()
            replace_values_for_events = {}

            # each parameter entry:
            for event_parameter in event_parameters:
                event_parameter_name = event_parameter.get_name()
                event_parameter_value = (
                    event_parameter.get_value()
                )  # self.__get_event_parameter_value(event_parameter)
                if isinstance(event_parameter_value, SerializedFunctionExpression):
                    event_parameter_value = event_parameter_value.get_value()
                replace_values_for_events["EVENT::" + event_parameter_name] = (
                    event_parameter_value
                )

                skip_count = 0
                for result_parameter_value, i in zip(
                    result_parameter_values, range(0, len(result_parameter_values))
                ):
                    if isinstance(result_parameter_value, Number):
                        continue

                    # perform the replacement:
                    (changed_flag[i], result_serialized_expression) = (
                        my_parameter_store.find_and_replace_in_function_expression(
                            result_parameter_value, replace_values_for_events
                        )
                    )

                    if changed_flag[i]:
                        # optimize expression:

                        # make it ready for simplify:
                        (dummy, deserialized_expression) = (
                            my_parameter_store.deserialize(result_serialized_expression)
                        )
                        # simplify:
                        simplified_expression = my_parameter_store.simplify(
                            deserialized_expression, ParameterFormat("FLOAT")
                        )
                        # and serialize again:
                        serialized_result = my_parameter_store.serialize_operations(
                            simplified_expression
                        )
                        if len(serialized_result) == 1:
                            serialized_result = serialized_result[0]

                        result_parameter_values[i] = serialized_result
                    else:
                        skip_count += 1

                if skip_count == MaxSkipCount:
                    break
            if skip_count == MaxSkipCount:
                break

        for result_parameter_value, i in zip(
            result_parameter_values, range(0, len(result_parameter_values))
        ):
            if isinstance(result_parameter_value, Number):
                new_parameter_value = result_parameter_value

            elif isinstance(result_parameter_value, ResolvedConstantElement):
                new_parameter_value = result_parameter_value.get_value()

            elif isinstance(result_parameter_value, ResolvedEventParameterElement):
                new_parameter_value = SerializedFunctionExpression(
                    [result_parameter_value]
                )

            elif (
                isinstance(result_parameter_value, list)
                and len(result_parameter_value) == 0
            ):
                new_parameter_value = []

            elif (
                isinstance(result_parameter_value, list)
                and len(result_parameter_value) > 0
            ):
                is_expression_flag[i] = True
                new_parameter_value = SerializedFunctionExpression(
                    result_parameter_value
                )
            else:
                raise AttributeError

            result_parameters[i].set_value(new_parameter_value)

        return is_expression_flag, result_parameters

    def __move_expressions_to_variables(
        self, my_is_expression_flags, my_target_controller, my_event, my_parameters
    ):
        if my_parameters is not None and my_parameters != []:
            for is_expression_flag, parameter in zip(
                my_is_expression_flags, my_parameters
            ):
                if is_expression_flag:
                    parameter_format = parameter.get_format()
                    value_reference = self.__insert_resolved_variable(
                        None,
                        parameter.get_value(),
                        parameter_format,
                        my_event.get_location(),
                        my_target_controller,
                    )
                    parameter.set_value(value_reference)

            my_event.insert_description_list("PARAMETER", my_parameters)
        return

    def __add_to_mapping_table(self, from_event, to_event):

        if to_event is not None:
            # map to protocol related table:
            if str(from_event.get_type()) == "CCAN" or str(to_event.get_type()) == "CCAN":
                #from_protocol = from_event.get_type()
                to_protocol = to_event.get_type()

                # if from_protocol == "CCAN":
                #    target_protocol = from_protocol
                # else:
                target_protocol = to_protocol

            else:
                raise ResolverError(
                    from_event.get_location(),
                    "At least one CCAN event is needed in a mapping.\n",
                )

            # derive needed mapping method:
            mapping_method = MappingType().maximum(
                [from_event.get_mapping_type(), to_event.get_mapping_type()]
            )

        else:
            target_protocol = "CCAN"
            mapping_method = "SIMPLE"

        
        selected_mapping_table = self.resolver_store.get_mapping_table(target_protocol, mapping_method)
    
        try:
            existing_mapping_targets = selected_mapping_table[from_event]
         
            #print(f"From Event gibt es schon: {from_event}")

            #others = [ str(existing)+"," for existing in existing_mapping_targets]
 

            #print(f"     .... Vergleich von {to_event}  mit {others}")
            if to_event not in existing_mapping_targets:
            #    print(f"     .. mapping auf {to_event} ergänzt")
                existing_mapping_targets.append(to_event)
            else:
                matches = [ event for event in existing_mapping_targets if event == to_event]
                raise ResolverError(
                    to_event.get_location(),
                    f"This mapping has been defined twice. First occasion was in {matches[0].get_location()}.")
        except KeyError:
            if to_event is not None:
                #print (f"Neues From-Event: {from_event}")
                #if from_event.get_full_name() == "device_under_test.VoltageChecker::LOW":
                #    pass
            
                #print (f"   mapping auf {to_event}")
                selected_mapping_table[from_event] = [to_event]
            else:
                selected_mapping_table[from_event] = []
                #print (f"Neues From-Event: {from_event} mit leerem to_event!")
            
    #######################################


    def resolve_equivalent_list(self,
        my_equivalent_list: list,
        my_event_description_map: ResolvedMap, 
        my_variable_description_map: map,
        my_prefix: str,
        my_parameter_store
        ) -> tuple[map, map] :
      
        events_identified = 0
        variables_identified = 0

        prefix_map = {}
        equivalent_map = {}            
        for equivalent_entry in my_equivalent_list:           
            
            # check whether event name is already in the name:
            try:
                equivalent_map[equivalent_entry.name]
                raise ResolverError(equivalent_entry.location_info,f"For {equivalent_entry.name} an equivalence has already been defined.")
            except KeyError:
               pass

            # resolve equivalence name if possible:                             
            try:  
                # operation fails with  KeyError for state variables, see except handling:    
                entry = my_event_description_map.get_by_name(equivalent_entry.name)                                         

                parsed_event_list = equivalent_entry.equivalent
                if not isinstance(parsed_event_list,list):
                    parsed_event_list = [ parsed_event_list]
               
                equivalent_map[equivalent_entry.name] = []              
                prefix_map[equivalent_entry.name]     = []

                for parsed_event in parsed_event_list:

                    if isinstance(parsed_event,ParsedVariableName):                        
                        raise ResolverError(equivalent_entry.location_info,f"For the event equivalent {equivalent_entry.name} you have provided a variable.")      
                       


                    resolved_equivalent = self. __resolve_parsed_event(parameter_are_optional_flag=True,
                                                                    parsed_event= parsed_event,
                                                                    prefix= my_prefix,
                                                                    location_info=equivalent_entry.location_info,
                                                                    parameter_store= my_parameter_store,
                                                                    parameter_event_reference_allowed=True,
                                                                    my_from_event= entry)     


                    if resolved_equivalent.get_type() != "CCAN":
                        raise ResolverError(equivalent_entry.location_info,f"For {equivalent_entry.name} the defined equivalent mapping is of type '{resolved_equivalent.get_type()}', but only a  'CCAN' event are allowed.")      
    
                    # parameter check:
                    device_name, device_id = resolved_equivalent.get_description_list("EVENT_PATH")

                    available_parameters = resolved_equivalent.get_description_list("PARAMETER")
                    needed_parameters    = entry.get_description_list("PARAMETER")

                    open_parameters = []
                    for parameter,i in zip(available_parameters, range(len(available_parameters))):                      
                        parameter_value = my_parameter_store.get_parameter_value(parameter)
                        if not isinstance(parameter_value, Number) and not isinstance(parameter_value, str):
                            open_parameters.append(i)
                                          
                    event_map = self.resolver_store.get_device_event_map(device_name)         
                    equivalent_parameters = event_map.get_by_name(resolved_equivalent.get_name()).get_description_list("PARAMETER")
                  

 
                    if len(open_parameters)  != len(needed_parameters[0]):                     
                        raise ResolverError(equivalent_entry.location_info,f"For {equivalent_entry.name} the number of fixed and open parameters does not fit to the equivalent HA device event. {len(open_parameters)  + len(equivalent_parameters)} open parameters are provided, but {len(needed_parameters[0])} are needed.")

                    for open_parameter_index  in open_parameters:
                        available_parameter_format = str(available_parameters[open_parameter_index].get_format())
                        needed_parameter_format    = needed_parameters[1][open_parameter_index]
                        
                        if available_parameter_format != needed_parameter_format:
                             raise ResolverError(equivalent_entry.location_info,f"For {equivalent_entry.name} the parameter {open_parameter_index} must be of type {needed_parameter_format}, but is of type {available_parameter_format}.")   


                    # TBD: parameter check to be added
                    #if len(available_parameters) > 0:
                    #    for parameter_type_needed, parameter_type_available, index in zip(needed_parameters[1], available_parameters,range(len(available_parameters))):
                    #        if parameter_type_needed != parameter_type_available:
                    #            raise ResolverError(equivalent_entry.location_info,f"For {equivalent_entry.name} the parameter {index} must be of type {parameter_type_needed}, but is of type {parameter_type_available}.")                    

                    events_identified += 1
                        
                    # Remove open parameters in case of "IN" events. The symbolic value is not used and will be replaced when using it in the HA library:
                    if entry.has_direction("IN") and len(open_parameters) > 0:  
                        new_available_parameters = []
                        for parameter,i in zip(available_parameters,range(len(available_parameters))):
                            if i not in open_parameters:
                                new_available_parameters.append(parameter)
                        
                        resolved_equivalent.insert_description_list("PARAMETER",new_available_parameters)

                    prefix = "DEV"
                    # add mappings to simplify usage in case of a template 
                    if resolved_equivalent.is_template():
                        event_list = self.__resolve_template_event(resolved_equivalent,my_parameter_store)

                        if entry.has_direction("OUT"):                    
                            for event in event_list:                                                                                     
                                self.__add_to_mapping_table(event, resolved_equivalent)                      
                        else:
                            for event in event_list:    
                                self.__add_to_mapping_table(resolved_equivalent,event)   
                    else:
                        if entry.has_direction("OUT"):
                            self.__add_to_mapping_table(resolved_equivalent, None)   
                        else:                     
                            prefix = "DIR"
                                                                             
                    equivalent_map[equivalent_entry.name].append(resolved_equivalent)
                    prefix_map[equivalent_entry.name].append(prefix)

            except KeyError:
                # check for state variable:
                try:
                    entry =  my_variable_description_map.get_by_name(equivalent_entry.name)                       
                except KeyError:
                    raise ResolverError(equivalent_entry.location_info,f"For {equivalent_entry.name} no equivalence can ben defined. Please check the description of the Home Assistant device.")
                
                try:
                    resolved_equivalent = self.resolve_parsed_variable_reference(equivalent_entry.equivalent.name, my_parameter_store) 
                except KeyError:
                    raise ResolverError(equivalent_entry.location_info,f"The variable with name {equivalent_entry.equivalent.name} does not exist. Equivalence is invalid.")

                if resolved_equivalent.get_format() != ParameterFormat(entry):
                    raise ResolverError(equivalent_entry.location_info,f"The variable with name {equivalent_entry.equivalent.name} has format {str(resolved_equivalent.get_format())}, but but expected format is {entry}.")

                variables_identified +=1

                equivalent_map[equivalent_entry.name] = resolved_equivalent
                            
        
       

        if events_identified  < len(my_event_description_map.get_as_list()):            
            raise ResolverError(equivalent_entry.location_info,f"{len(my_event_description_map.get_as_list()) - events_identified} events are missing in the equivalence list for current HA device instance.")        
        
        if variables_identified  < len(my_variable_description_map.get_as_list()):
            raise ResolverError(equivalent_entry.location_info,f"{len(my_variable_description_map.get_as_list())- variables_identified} variables are missing in the equivalence list for current HA device instance.")        
        return equivalent_map, prefix_map,open_parameters


    def resolve_parsed_variable_reference(self, my_parsed_variable_name, my_parameter_store):
        # resolve name:    
        if isinstance(my_parsed_variable_name,tuple):   
           var_name = "::".join([my_parameter_store.resolve_alias(my_parsed_variable_name[0]),my_parsed_variable_name[1]])
        else:
            var_name = my_parameter_store.resolve_alias(my_parsed_variable_name)
        
        # resolve variable:
        resolved_variable_reference = self.resolver_store.get_instance_by_name("VARIABLE",self.__resolve_variable(var_name))

        #                  
        return resolved_variable_reference              
                    
    def __resolve_variable(self, my_name):
        ''' Resolve variable names and process template variables recursively until '''
        resolved_variable_reference = self.resolver_store.get_instance_by_name("VARIABLE",my_name)         
        (device_name, variable_name) = str(my_name).split("::")
        device_instance = self.resolver_store.get_instance_by_name("DEVICE",device_name)
        if device_instance.is_template():
            expression = resolved_variable_reference.get_value()
            if len(expression) == 1 and isinstance(expression[0],ResolvedVariableElement):                
                return self.__resolve_variable(expression[0].get_name())
            else:
                raise KeyError
        else:
            result = my_name
        return result

    def resolve_fixed_parameter_list(
        self,
        my_parameter_store,
        my_parameter_list,
        my_parameter_name_list,
        my_parameter_type_list,
        my_location_info,
        connections_allowed=False,
    ):
        result = my_parameter_store.resolve_parameter_list(
            my_parameter_list,
            my_parameter_name_list,
            my_parameter_type_list,
            False,
            my_location_info,
        )

        if result is None and len(my_parameter_name_list) == 0:
            return []

        if result is None and len(my_parameter_name_list) > 0:
            raise ResolverError(
                my_location_info,
                "No arguments have been specified,"
                + str(len(my_parameter_name_list))
                + " are required.",
            )

        if len(result) != len(my_parameter_name_list):
            raise ResolverError(
                my_location_info,
                "Number of arguments "
                + str(len(my_parameter_list))
                + " does not match expected number which is "
                + str(len(my_parameter_name_list))
                + ".",
            )

        # check for runtime parameters:
        for param, i, parameter_type in zip(
            result, range(len(result)), my_parameter_type_list
        ):
            if param.is_expression():
                param_list_length = len(param.get_value())
                if param_list_length == 1 and isinstance(
                    param.get_value()[0], ParsedVariableInExpression
                ):
                    if (
                        param.get_value()[0].type == "SYMBOL"
                        and parameter_type != "CONNECTION"
                    ):
                        raise ResolverError(
                            my_location_info,
                            "The symbol "
                            + param.get_value()[0].name
                            + " is not defined or cannot be used for a parameter of type "
                            + parameter_type,
                        )
                    result[i].set_value(param.get_value()[0].name)
                else:
                    raise ResolverError(
                        my_location_info,
                        "Compile-time constant expression is required here. Your expression is not valid or has operands which are available at runtime only.",
                    )

        return result

    #########################################################################################################################################

    @staticmethod
    def is_static_parameter_set(parameter_list):
        result = True
        for parameter in parameter_list:
            if not isinstance(parameter, Number) and not isinstance(parameter, str):
                result = False
        return result

    def __get_next_local_instance_id(self, controller_name, map_type):
        # get number of "map_type" instances which are already connected to this controller. This yields the next id:
        id = 0
        for unused, app in self.resolver_store.get_instance_dictionary("APP"):
            if app.get_controller_name() == controller_name:
                try:
                    id += app.get_description_list(map_type).get_number_of_entries()
                except AttributeError:
                    # this connected app has currently no description list like this, this zero entries
                    pass
        return id

    def __get_instance_list(
        self,
        my_app,
        map_type,
        parsed_used_list,
        descriptor,
        dependend_driver_dictionary,
        parameter_store,
        allow_multiple_connections_per_pin=False,
    ):
        """ """

        if my_app.get_controller_name() == my_app.get_name():
            # if this a controller, create a list from scratch:
            instance_list = ResolvedInstanceDictionaryBase(None, 0)
        else:
            # get number of instances of controller to avoid double id's:
            instance_list = ResolvedInstanceDictionaryBase(
                None,
                self.__get_next_local_instance_id(
                    my_app.get_controller_name(), map_type
                ),
            )

        my_map = descriptor.get_description_list(map_type)

        # list of all used pins:
        connection_list = []

        for pin in parsed_used_list:
            # check for pin name and related offered driver list:
            try:
                available_driver_list_for_pin = my_map.get_by_name(pin.name)
                pin_id = my_map.get_id_by_name(pin.name)
            except KeyError:
                raise ResolverError(
                    pin.location_info,
                    "Pin name " + pin.name + " is not available for this app.",
                )

            # resolve driver or drivers connected to this pin:

            pin_entry_list = pin.usage_pin_entry_list
            if not isinstance(pin_entry_list, list):
                pin_entry_list = [pin_entry_list]

            previous_driver_name = None
            for pin_entry in pin_entry_list:
                if pin_entry.driver_name not in available_driver_list_for_pin:
                    raise ResolverError(
                        pin.location_info,
                        "Driver "
                        + pin_entry.driver_name
                        + " needed for pin "
                        + pin.name
                        + " is not available for this app.",
                    )

                # get driver type:
                driver_type, driver_descriptor = self.resolver_store.get_type_and_description_by_name(map_type, pin_entry.driver_name)
                
                # has another driver of a different has been connected to this pin?
                if previous_driver_name is None:
                    previous_driver_name = pin_entry.driver_name
                elif (
                    previous_driver_name is not None
                    and previous_driver_name != pin_entry.driver_name
                ):
                    raise ResolverError(
                        pin_entry.location_info,
                        "Driver "
                        + pin_entry.driver_name
                        + " collides with parallel usage of different driver "
                        + previous_driver_name
                        + " at the same pin "
                        + pin.name
                        + ".",
                    )
                elif allow_multiple_connections_per_pin is False:
                    raise ResolverError(
                        pin_entry.location_info,
                        "It is not allowed to use parallel drivers at the same pin "
                        + pin.name
                        + ".",
                    )

                # is this element connected to something else:
                if pin_entry.connected_to is not None:
                    # identify element this element is connected to (this is valid for transport adapter)
                    (dummy, subdriver_name) = pin_entry.connected_to.split("::")
                    subdriver_id, subdriver = dependend_driver_dictionary.get_by_name(
                        subdriver_name
                    )
                    # reuse the app and pin information:

                    # subdriver_id = dependend_driver_dictionary.get_id_by_name(subdriver_name)
                    dependend_connection = subdriver.get_description_list("CONNECTION")
                    # read out pin information:
                    pin_id = dependend_connection[0].get_pin_id()
                    pin_name = dependend_connection[0].get_pin_name()
                    # app id remains

                else:
                    # this path is valid for sensor and communication drivers:
                    # here we have no dependent element, thus driver id is INVALID
                    subdriver_id = Resolver.ILLEGAL_DRIVER_ID
                    # pin_id remains
                    # app id remains
                    pin_name = pin_entry.alias_name

                resolved_used_pin = ResolvedUsedDriverInstance(
                    pin_entry.alias_name, pin_entry.location_info
                )
                resolved_used_pin.set_type(pin_entry.driver_name, driver_type)

                # resolve parameter:
                parameter_name_list, parameter_type_list, parameter_constraints_list, parameter_defaults_list = (
                    driver_descriptor.get_description_list("PARAMETER")
                )
                resolved_parameter_set = parameter_store.resolve_parameter_list(
                    pin_entry.parameter_list,
                    parameter_name_list,
                    parameter_type_list,
                    False,  # no EVENT parameter allowed
                    pin_entry.location_info,
                )

                resolved_used_pin.insert_description_list(
                    "PARAMETER", resolved_parameter_set
                )

                resolved_connection = ResolvedConnection(
                    pin_entry.alias_name, pin_entry.location_info
                )
                resolved_connection.set_app(my_app.get_name(), my_app.get_id())
                resolved_connection.set_driver_class(
                    map_type, DriverClassType(map_type).get_key()
                )
                resolved_connection.set_driver(pin_entry.driver_name, subdriver_id)
                resolved_connection.set_pin(pin_name, pin_id)

                resolved_used_pin.insert_description_list(
                    "CONNECTION", [resolved_connection]
                )

                if map_type == "SENSOR_DRIVER" or map_type == "COMMUNICATION_DRIVER":                
                    try: 
                        index = connection_list.index(resolved_connection)
                        raise ResolverError(resolved_connection.get_location(), f"Pin driver {resolved_connection.get_pin_name()} belonging to {resolved_connection.get_app_name()} uses the same pin as the previously defined alias {connection_list[index].get_pin_name()} ")             
                    except ValueError:
                        pass
                    
                connection_list.append(resolved_connection)                  
                instance_list.insert(resolved_used_pin)
                
        return instance_list

    def __add_alias_event(self, prefix, in_out_type, source_mapping, target_mapping):
        [template_name, template_id] = source_mapping.get_description_list("EVENT_PATH")
        template_instance = self.resolver_store.get_instance_by_name("DEVICE",template_name)
        source_event_map = self.resolver_store.get_device_event_map(template_name)
        from_event_descriptor = source_event_map.get_by_name(
            source_mapping.get_name()
        )

        if not from_event_descriptor.has_direction(in_out_type):
            raise ResolverError(
                source_mapping.get_location(), f"Event direction of event {source_mapping.get_name()}  does not fit to the expected direction {in_out_type} in the template definition."
            )

        [device_name, template_id] = target_mapping.get_description_list("EVENT_PATH")
        target_event_map = self.resolver_store.get_device_event_map(device_name)
        to_event_descriptor = target_event_map.get_by_name(

            target_mapping.get_name()
        )

        if not to_event_descriptor.has_direction(in_out_type):
            raise ResolverError(
                source_mapping.get_location(), f"Event direction of event {target_mapping.get_name()}  does not fit to the expected direction in the template definition."            
            )

        new_alias_event = AliasEventPair(
            target_mapping, source_mapping, from_event_descriptor
        )
        alias_event_map = template_instance.get_description_list("ALIAS_EVENTS")
        try:
            target_events = alias_event_map.get_by_name(source_mapping.get_name())
            # target_events.append(target_mapping)
            target_events.append(new_alias_event)
        except KeyError:
            # target_events = [ target_mapping]
            target_events = [new_alias_event]
            alias_event_map.insert_and_replace(
                source_mapping.get_name(), target_events, source_mapping.get_location()
            )
            template_instance.insert_description_list("ALIAS_EVENTS", alias_event_map)

    def __resolve_template_instance(
        self,
        parsed_template_instance,
        template_description,
        prefix,
        parameter_set,
        connection_values,
    ):
        local_parameter_store = ParameterStore()
        (local_prefix, alias_flag) = self.__resolve_prefixed_name(
            prefix,
            local_parameter_store,
            parsed_template_instance.name,
            parsed_template_instance.location_info,
        )

        for parameter in parameter_set:
            new_alias = template_description.get_name() + "::" + parameter.get_name()
            local_parameter_store.insert_alias(new_alias, parameter.get_value())

        # insert variables:
        variable_map = template_description.get_description_list("VARIABLE")
        for variable_name in variable_map:
            new_alias = template_description.get_name() + "::" + variable_name
            local_parameter_store.insert_alias(
                new_alias, local_prefix + "::" + variable_name
            )

        connection_names = template_description.get_description_list(
            "CONNECTION"
        ).get_names_as_list()
        for connection_name, connection_value in zip(
            connection_names, connection_values
        ):
            new_alias = template_description.get_name() + "::" + connection_name
            # connection_name = connection_value.board_name
            # if connection_value.pin_name is not None:
            #    connection_name +="::"+connection_value.pin_name
            local_parameter_store.insert_alias(new_alias, connection_value)

        local_parameter_store.insert_alias(
            template_description.get_name(), local_prefix
        )  # parsed_template_instance.name)
        self.__evaluate_automation(
            template_description.get_description_list("AUTOMATION"),
            local_prefix,
            local_parameter_store,
        )

    def __resolve_prefixed_name(self, prefix, parameter_store, name, location_info):
        test_name = parameter_store.resolve_alias(name)
        if test_name != name:
            # print("Mapped " + name + " to " + test_name + " -> ALIAS!")
            return (test_name, True)

        if prefix == "":
            prefixed_name = name
        else:
            prefixed_name = prefix + "." + name

        return (prefixed_name, False)

    def __resolve_variables_in_expression(
        self,
        my_expression,
        prefix,
        parameter_store,
        event_descriptor,
        reference_device_name,
        my_parameter_event_descriptor,
        location_info,
    ):
        if isinstance(my_expression, SerializedFunctionExpression) is False:
            return my_expression

        expression = my_expression.get_value()
        return self.__resolve_expression(
            expression,
            prefix,
            parameter_store,
            event_descriptor,
            reference_device_name,
            my_parameter_event_descriptor,
            location_info,
        )

    def __resolve_expression(
        self,
        my_expression,
        prefix,
        parameter_store,
        my_from_event_descriptor,
        reference_device_name,
        my_parameter_event_descriptor,
        location_info,
    ):
        resolved_list = []
        for element in my_expression:
            if isinstance(element, ParsedVariableInExpression):
                if element.type == "VARIABLE" or element.type == "SYMBOL":
                    var_name = self.__resolve_prefixed_name(
                        prefix, parameter_store, element.name, location_info
                    )[0]
                    if isinstance(var_name, Number):
                        resolved_element = ResolvedConstantElement(
                            var_name, ParameterFormat("FLOAT")
                        )
                    else:
                        try:
                            (operand_id, resolved_operand) = self.resolver_store.get_id_and_instance_by_name("VARIABLE",var_name)
                        except KeyError:
                            try:
                                (operand_id, resolved_operand) = self.resolver_store.get_id_and_instance_by_name("VARIABLE","VAR::" + var_name)                             
                            except KeyError:
                                raise ResolverError(
                                    location_info,
                                    "Variable " + element.name + " could not be found.",
                                )
                        resolved_element = ResolvedVariableElement(
                            resolved_operand.get_name(), operand_id
                        )
                elif element.type == "EVENT_PARAMETER":
                    if my_from_event_descriptor is None:
                        raise ResolverError(
                            location_info,
                            "Event parameter cannot be referred to in this context.",
                        )

                    (parameter_name_list, parameter_type_list) = (
                        my_from_event_descriptor.get_description_list("PARAMETER")
                    )
                    try:
                        position = parameter_name_list.index(element.name)
                        offset_list = parameter_type_list[0 : position - 1]

                        resolved_element = ResolvedEventParameterElement(
                            element.name,
                            offset_list,
                            parameter_type_list[position],
                            reference_device_name,
                        )
                    except ValueError:
                        error_string = (
                            "The event reference EVENT::"
                            + element.name
                            + " cannot be used. "
                        )
                        if len(parameter_name_list) == 0:
                            error_string("The triggering event has no parameters.")
                        elif len(parameter_name_list) == 1:
                            error_string += f"Single allowed value for the triggering event is EVENT::{parameter_name_list[0]}."
                          
                        else:
                            error_string += "Allowed values for the triggering event are :"                         
                            for i, var_name in zip(
                                range(len(parameter_name_list)), parameter_name_list
                            ):
                                error_string += "EVENT::" + var_name
                                if i < len(parameter_name_list) - 1:
                                    error_string += ", "
                                else:
                                    error_string += "."
                        raise ResolverError(location_info, error_string)

                else:
                    raise ResolverError(
                        location_info,
                        f"Internal Error: unsupported parsed variable type: {element.type}-"
                    )

            elif isinstance(element, Operator):
                resolved_element = ResolvedFunctionElement(element.value)
                resolved_element.set_number_of_arguments(element.number_of_arguments)

            # depending on controller the number might be saved as float or int:
            elif isinstance(element, Number):
                resolved_element = ResolvedConstantElement(
                    element, ParameterFormat("FLOAT")
                )

            elif isinstance(element, str):
                resolved_element = ResolvedConstantElement(
                    element, ParameterFormat("STRING")
                )

            else:
                resolved_element = element

            resolved_list.append(resolved_element)

        return SerializedFunctionExpression(resolved_list)

    def resolve_controller_by_device_name(self, device_name):
        device_instance = self.resolver_store.get_instance_by_name("DEVICE", device_name) 
        connection = device_instance.get_description_list("CONNECTION")
        app_name = connection[0].get_app_name()
        return self.resolve_controller_by_app_name(app_name)

    def resolve_controller_by_app_name(self, app_name):
        app_instance = self.resolver_store.get_instance_by_name("APP", app_name)
        controller_name = app_instance.get_controller_name()
        return controller_name

    def __resolve_connection_parameter(
        self,
        connected_item_type_descriptor,
        connection_type_item,
        offered_connection_type_for_item,
        connections,
        location_info,
    ):
        resolved_connection_set = []

        controller_name = None


        offered_connection_dictionary = self.resolver_store.get_description_dictionary(offered_connection_type_for_item)
     
        if len (connections) > 1:
            raise ResolverError(location_info,"Too many connections provided.")
        if len (connections) == 0:
            raise ResolverError(location_info,"Connection information is empty..?")

        # just check the first connection:
        if isinstance(connections[0], ParsedSymbol):
            connection = connections[0].name
        else:
            connection = connections[0]

        pin_id = None
        pin_flag = False

        # is connection valid:
        if "::" in connection:
            pin_flag = True
        connection_array = str(connection).split("::")
        if pin_flag is True and len(connection_array) == 1:
            raise ResolverError(
                location_info,
                "Illegal pin argument. Leading or trailing '::' is not allowed.",
            )
        elif pin_flag is True and len(connection_array) == 2:
            board_name = connection_array[0]
            pin_name = connection_array[1]
        else:
            board_name = connection_array[0]
            pin_name = None

        ################

        # find board:
        try:
            app_instance = self.resolver_store.get_instance_by_name("APP",board_name)           
        except KeyError:
            raise ResolverError(location_info, f"Invalid connection - board/app/alias {board_name} does not exist.")
        app_id = app_instance.get_id()
        # if app_instance is None:
        #    raise ResolverError(location_info, "Invalid connection - board " + board_name + " does not exist.")

        # prepare the resolved connection and set app_name and id:
        resolved_connection = ResolvedConnection(None, location_info)
        resolved_connection.set_app(board_name, app_id)

        # check whether this pin fits to what the item (device, app,..) needs:

        # what is needed from the item:
        needed_connection_type = connected_item_type_descriptor.get_description_list(
            "CONNECTION"
        )
        needed_connection_list = needed_connection_type.get_as_list()

        if pin_name is not None:
            try:
                (dummy_driver_id, dummy_name, needed_driver_type) = (
                    needed_connection_list[0]
                )  # we only have one connection right now..
            except IndexError:
                raise ResolverError(
                    location_info,
                    f"The device of type {connected_item_type_descriptor.get_name()} does not require pin information. The provided, resolved pin name is '{pin_name}' - did you mix up the connection type?")
         
            # what is available for this pin:
            board_descriptor_connection = app_instance.get_description_list(
                offered_connection_type_for_item
            )

            if board_descriptor_connection == []:
                raise ResolverError(
                    location_info,
                    f"Pin {pin_name} is not defined for board {board_name} .")

            # check wether pin exists (checks alias name)
            try:
                (local_driver_id, offered_connected_pin) = (
                    board_descriptor_connection.get_by_name(pin_name)
                )
            except KeyError:
                raise ResolverError(
                    location_info,
                    "Pin " + pin_name + " is not defined for board " + board_name + ".",
                )
            # and what kind of driver this pin offers:
            offered_connection = offered_connected_pin.get_description_list(
                "CONNECTION"
            )[0]
            offered_driver_name = offered_connection.get_driver_name()
            offered_driver_type, offered_driver_descriptor = (
                offered_connection_dictionary.get_by_name(offered_driver_name)
            )
            pin_id = offered_connection.get_pin_id()

            # do offer and need fit?
            if offered_driver_descriptor.get_type() != needed_driver_type:
                raise ResolverError(
                    location_info,
                    f"Offered driver {offered_driver_name} does not fit to element {connected_item_type_descriptor.get_name()} - a driver of type {needed_connection_list[0][2]} is required."
                    )             
            # insert resolved data_
            resolved_connection.set_driver(offered_driver_name, local_driver_id)
            resolved_connection.set_driver_class(
                offered_connection_type_for_item,
                DriverClassType(offered_connection_type_for_item).get_key(),
            )
            resolved_connection.set_pin(pin_name, pin_id)

            # preserve information that pin is in use:
            offered_connected_pin.has_just_been_used()

        else:
            if len(needed_connection_list) > 0:
                if needed_connection_list[0][2] != "CONTROLLER":
                    raise ResolverError(
                        location_info,
                        f"No pin name is given. But for the device type {connected_item_type_descriptor.get_name()} -  a driver of type {needed_connection_list[0][2]} is required."
                    )

        return [resolved_connection]
