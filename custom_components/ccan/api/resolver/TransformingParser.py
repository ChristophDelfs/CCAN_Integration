import lark
import os
from lark.visitors import Transformer, v_args
import ast
from api.resolver.ResolverError import ResolverError
#import itertools

from api.resolver.Definitions import ParsedParameterDescriptionList
from api.resolver.Definitions import ParsedEventDescription,ParsedSensorDriverDescription,ParsedTransportAdapterDescriptionList
from api.resolver.Definitions import ParsedUsagePin,ParsedOfferedConnectionUsage,ParsedConnectedPin,ParsedUsagePinEntry
from api.resolver.Definitions import ParsedDeviceInstance,ParsedAppInstance, ParsedControllerInstance, ParsedGeneralAppDescription, ParsedMappingList
from api.resolver.Definitions import ParsedAliasDefinition,ParsedDeviceDescription
from api.resolver.Definitions import ParsedAutomation, ParsedSensorDriverDescriptionList,ParsedCommunicationDriverDescriptionList
from api.resolver.Definitions import ParsedPinList,ParsedAdapterList, ParsedCommunicationList, ParsedDegradationCode , ParsedProtocol, ParsedAdditionalProtocolType
from api.resolver.Definitions import ParsedProtocolAdapterDescriptionList, ParsedTransportAdapterDescription
from api.resolver.Definitions import ParsedEvent , ParsedTransportAdapterUsage, ParsedOfferedTransportAdapterUsage 
from api.resolver.Definitions import LocationInfo,ParsedOfferedTransportAdapterList, ParsedExportList
from api.resolver.Definitions import ParsedVariableInstance,ParsedTemplateVariableInstance, ParsedVariableInExpression
from api.resolver.Definitions import ParsedEquivalent, ParsedHADeviceInstance, ParsedVariableName, ParsedConstraints
                 


from api.resolver.ResolverElements import EventVariable, SerializedFunctionExpression, FunctionExpression, Function
from api.resolver.Definitions import OperatorTypeKey,Operator, ParsedSymbol, ElementTypeKey, OperandTypeKey

# https://lark-parser.readthedocs.io/en/latest/classes/
# https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark
# https://dexterritory.online/posts/parsing-context-free-grammars-using-lark 

@lark.v_args(inline=True)
class TransformingParser(Transformer):

    def __init__(self):
        self.__transport_adapter_counter = 0
        
        
        self.__include_path = None
        
        self.__parse_tree = None
        self.__current_tree = None
        self.__current_file = None
        self.__parser = lark.Lark('''start:(sensor_drivers| communication_drivers | protocol_types | transport_adapter_types | ha_device_description | device_description| controller_description | app_description | template_description | automation | include)+

    include :                    ( ("INCLUDE"|"include") "{" PATHNAME "}") 

    sensor_drivers :             ("SENSOR_DRIVERS"   "{" driver_description_list "}")   
    communication_drivers:       ("COMMUNICATION_DRIVERS"  "{" driver_description_list "}")  
    transport_adapter_types :    ("TRANSPORT_ADAPTERS" "{" transport_adapter_description_list "}")    
 
    template_description:        ("TEMPLATE" TYPE_NAME "(" param_def_list ")" "->"  "(" connection_pin_list ")" "{" event_description status_variables_description automation  "}") 

    protocol_types:              ( "ADDITIONAL_PROTOCOLS"  protocol_type_list )
    enable_protocol.2:             ("ENABLE" PROTOCOL_NAME "(" param_list ")" )

    automation:                  ( "AUTOMATION"  "{" automation_rule_list "}" )
    automation_rule_list:        ( [automation_rule (automation_rule)*])
    automation_rule:             ( alias_definition | rule | export | controller_instance| app_instance| ha_device_instance | device_instance | template_variable_instance| variable_instance | enable_protocol)

    controller_description:      ("CONTROLLER_TYPE" TYPE_NAME "(" param_def_list ")"  "{" pin_list_description communication_driver_list transport_adapter_list degradation_codes_description"}")
    app_description :            ("APP"   TYPE_NAME "(" param_def_list ")" "->"  "(" connection_pin_list ")" "{" pin_list_description degradation_codes_description "}" )
    device_description:          ("DEVICE_TYPE"     TYPE_NAME "(" param_def_list ")" "->"  "(" connection_pin_list ")" "{" [attributes] event_description status_variables_description degradation_codes_description "}")  
    ha_device_description:       ("HOME_ASSISTANT_DEVICE_TYPE"   TYPE_NAME "(" param_def_list ")" "{"  event_description  status_variables_description "}" ) 

    alias_definition:            (PARAM_NAME  "=" arg) 
    rule:                         ( event ("triggers"|"TRIGGERS") event_list)
    export:                       ("EXPORT" event_list)
                                  
    controller_instance:         ("CONTROLLER" TYPE_NAME instance_with_param                           "{" [uuid_identifier] usage_pin_list communication_pin_list transport_adapter_instance_list "}" )
    app_instance:                ("APP"   TYPE_NAME instance_with_param  "->" "(" param_list  ")" "{" usage_pin_list "}")
    device_instance.1:           ( TYPE instance_with_param "->" "(" param_list  ")")
    ha_device_instance:           ( TYPE instance_with_param  equivalent_list )
  
    template_variable_instance.1:("VAR::" variable_name "=" arg ["->" "(" param_list  ")"])
    variable_instance.2:         ("VAR::" NAME          "=" arg ["->" "(" param_list  ")"])
  
    instance_with_param:         (NAME "(" param_list ")")
  
    uuid_identifier:           ("UUID" "="  QUOTED_STRING)                                    

    connection_pin_list :        ([connection_pin (connection_pin)*])
    connection_pin:              (PARAM_NAME "<" DRIVER_TYPE ">")

 
    transport_adapter_description_list: ([transport_adapter_description (transport_adapter_description)*])
    transport_adapter_description: (PROTOCOL_NAME DRIVER_NAME "(" param_def_list ")" degradation_codes_description  "->"  "(" connection_pin_list ")" ) 

    transport_adapter_list:      ( "TRANSPORT_ADAPTER" ":" "[" DRIVER_NAME ("," DRIVER_NAME)* "]")

    transport_adapter_instance_list:    ( "TRANSPORT_ADAPTER" "{" [ transport_adapter_instance ( transport_adapter_instance)*] "}" )
    transport_adapter_instance:  (instance_with_param "->" "(" [symbol]  ")")
     
    pin_list_description:         ( "SENSOR_PINS" "{" [pin_description (pin_description)*] "}") 
    pin_description:              (PIN_NAME ":" hw_driver_list)
    hw_driver_list:              ("[" [ DRIVER_NAME ("," DRIVER_NAME)*] "]")

    communication_driver_list:   ( "COMMUNICATION_PINS" "{" [pin_description (pin_description)*] "}")
    communication_pin_list:      ( "COMMUNICATION_PINS" "{" [usage_pin (usage_pin)*] "}")
    
    usage_pin_list:              ( "SENSOR_ACTOR_PINS" "{" [usage_pin (usage_pin)*] "}")
    usage_pin:                   ( PIN_NAME"::" (usage_pin_entry | usage_pin_entry_list))
    usage_pin_entry:             ( DRIVER_NAME "(" param_list ")" ["ALIAS" ALIAS_NAME])
    usage_pin_entry_list:        ("[" [usage_pin_entry ("," usage_pin_entry)*] "]")



    protocol_type_list:          (protocol_type ("," protocol_type)*)
    protocol_type:               (PROTOCOL_NAME "(" param_def_list ")")  


    driver_description_list:     ([driver_description (driver_description)*])
    driver_description:          (DRIVER_TYPE driver ("," driver )* )
    driver:                      (DRIVER_NAME "(" param_def_list ")" degradation_codes_description) 
    
    ha_event_description:        (input_events output_events get_state_events)  
    event_description:           (input_events output_events)    
    input_events:                ("INPUT_EVENTS"  "{" upper_case_param_list"}" )
    output_events:               ("OUTPUT_EVENTS" "{" upper_case_param_list"}" ) 
    get_state_events:            ("GET_STATE_EVENTS" "{" upper_case_param_list"}" ) 

    equivalent_list:             ( "{" equivalent+  "}")
    equivalent:                  ( NAME "=" equivalent_item)  
    equivalent_item:             (event| event_list |extended_variable_name)
                                  
    attributes :                  ("ATTRIBUTES" "{" attribute_list "}")
    attribute_list:              ([NAME ("," NAME)*])
  
                                  
    event_list:                  (event ("," event)*)
    event:                       (ccan_event|not_ccan_event)
    
    
    ccan_event:                  ((extended_name|template_symbol) "::" EVENT_NAME "(" param_list ")" )
    not_ccan_event:              ( PROTOCOL_NAME "(" var_expression ")" "::"  EVENT_NAME "(" param_list ")" )

    upper_case_param_list:       [upper_case_param ("," upper_case_param)*]  
    upper_case_param:            (UPPER_CASE_VARNAME "(" [param_def_list] ")" )
  
    extended_name:				  (DNAME ("." DNAME)*)  
 
    status_variables_description:  ("STATUS_VARIABLES" "{" param_def_list "}" )

    degradation_codes_description:("DEGRADATION_CODES" "{" degradation_code_list "}")
    degradation_code_list:       [degradation_code (degradation_code)*]
    degradation_code:            (NAME QUOTED_STRING)

    param_def_list:              ([param_def ("," param_def)*]) 
    param_def:                   ( PARAM_NAME "<" PARAM_TYPE ["::" "[" parameter_constraints "]" ] ["," "default" "=" arg]">")
 
    param_list:                  [ var_expression ("," var_expression)*] 
    var_expression:              ([PARAM_NAME "="] arg)
    parameter_constraints:        (enumeration_of_allowed_parameters|list_of_allowed_parameters)
    enumeration_of_allowed_parameters: (arg ".." arg)
    list_of_allowed_parameters:     (arg ["," arg]*) 

    variable_name:               (DNAME "::" DNAME)
    extended_variable_name:      ((extended_name|template_symbol) "::" DNAME)  

    symbol:  simple_symbol| template_symbol

    arg:     sum           -> argument
           | sum_str       -> string_argument
  
    ?sum: product 
        | sum "+" product   -> add_func
        | sum "-" product   -> sub_func
        | sum "&" product   -> and_func
        | sum "|" product   -> or_func
      
    ?product: atom
        | product "*" atom  -> mul_func    
        | product "/" atom  -> div_func
        | product "^" atom  -> pow_func
        | "(" sum ")"

    ?atom: NUMBER               -> number     
         | hex                  -> hex_number
         | "-" atom             -> neg_func      
         | "(" sum ")"
         | ALIAS                -> alias
         | event_parameter
         | variable             
         | symbol   
         | function
                   

    ?sum_str: atom_string 
        | sum_str "+" atom_string  -> add
    ?atom_string: QUOTED_STRING    -> get_string
        | ALIAS_STRING             -> alias
                                  
    
    event_parameter.2:          ("EVENT::" NAME)  
    variable.2:                 ("VAR::" NAME)              
    template_symbol:            ( "<" NAME "::" NAME ">")                                  
    simple_symbol:                     (NAME "::" NAME)   
    function:                   (CNAME "(" arg_list  ")")
    arg_list:                   [arg ("," arg)*]
 
    hex.2 : HEXNUMBER
    OPERATOR:                    ("*"|"+"|"-"|"/")

    
    UCASE_CNAME:                 (UCASE) ("_"|UCASE|DIGIT)*
    LCASE_CNAME:                 (LCASE) ("_"|LCASE|DIGIT)*
    
    PARAM_NAME:                  DNAME  
    NAME:                        CNAME   
    QUOTED_STRING:               /"[^"]*"/
    HEXNUMBER :                  (("0x"|"0X") ("0".."9" | "A".."F" | "a".."f")+)  

    ALIAS: (CNAME)
    ALIAS_STRING: (CNAME)

    EVENT_NAME: (LETTER|DIGIT) ("_"|LETTER|DIGIT)*
                                  
    PROTOCOL_NAME:               UCASE_CNAME
    DRIVER_TYPE:                 UCASE_CNAME
    DRIVER_NAME:                 UCASE_CNAME
    TYPE_NAME:                   UCASE_CNAME
    PIN_NAME:                    UCASE_CNAME
    ALIAS_NAME:                  CNAME
    TYPE:                        CNAME
    FROM_NAME:                   CNAME
    TO_NAME:                     CNAME
   
    

    DESCRIPTOR_NAME:             DNAME   

    PARAM_TYPE:                  (UCASE) ("_"|UCASE|DIGIT)*
    UPPER_CASE_VARNAME:          (UCASE) ("_"|UCASE|DIGIT)* 
    PATHNAME :                   (DNAME ["/" DNAME]*)
   
    DNAME:                       ((LETTER) ("_"|LETTER|NUMBER)*)   
        
    COMMENT:                     /#.*?\\n/
    %ignore COMMENT
 
    %import common.CNAME    -> CNAME
    %import common.WORD   -> WORD
    %import common.DIGIT   -> DIGIT
    %import common.LETTER   -> LETTER
    %import common.LCASE_LETTER   -> LCASE
    %import common.UCASE_LETTER   -> UCASE        
    %import common.ESCAPED_STRING   -> STRING
    %import common.SIGNED_NUMBER    -> NUMBER
    %import common.WS                -> WS
    %ignore WS
   
    ''', parser='earley', propagate_positions=True)


#     UNBRACKETED_VALUE:           (NUMBER|PARAM_VALUE|QUOTED_STRING)
#    PARAM_VALUE:                 (DNAME|HEXNUMBER|NUMBER|WORD|"::"|STRING)+


#    pseudo_pin:                   ( PIN_NAME"::" DRIVER_NAME "(" param_list ")" ["->"  "(" param_list ")"] ("transports"|"TRANSPORTS") PROTOCOL_NAME )  



    # https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark

    #def argument(self,matches):
    #    #result = self.simplify(matches)
    #    return matches

    def string_argument(self,result):
        #result = self.simplify(matches)
        return result
        
    def get_string(self,input_string):
        input_string = str(input_string)
        r =  input_string.replace("'",'')
        r =  r.replace('"','')
        return r

    def add_string(self,arg1,arg2):
        result = arg2
        return result

    def hex_number(self,value):
        return int(value.children[0],16)
            
    def alias(self,alias):   
        return str(alias)
        replaced = False
        #try:
        #        value = self.__alias_list[alias]
        # 
        #        except KeyError:
        #            value = alias      
        #            
        #        return value

    def number(self,value):
        return ast.literal_eval(value)

    def add_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '+')
        return result
    
    def sub_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '-')
        return result        

    def and_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '&')
        return result 

    def or_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '|')
        return result 

    def mul_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '*')
        return result  
    
    def div_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '/')
        return result  

    def pow_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '^')
        return result  

    def neg_func(self,arg):
        result = FunctionExpression(operand1= 0,operand2 = arg, operator = '-')
        return result

    def event_parameter(self,name):        
        event = ParsedVariableInExpression(name = str(name), type = "EVENT_PARAMETER")
        return event
 
    def variable(self,name):
        var = ParsedVariableInExpression(name = str(name), type = "VARIABLE")
        return var

    def symbol(self, symbol):
        return symbol

    def simple_symbol(self,*symbol_token):      
        text = str(symbol_token[0])
        parts = symbol_token[1:]
        for element in parts:
            text += ''.join("::"+str(element))
                             
        return ParsedVariableInExpression(name = text, type = "SYMBOL")

    def template_symbol(self,*symbol_token):      
        return self.simple_symbol(*symbol_token)

    def function(self,name,argument_list):
        function = Function(name,argument_list)
        result = ParsedVariableInExpression(value= str(function),type = "FUNCTION")
        return result
         
    def arg_list(self,*matches):
        args = []
        for i in range(len(matches)):
            args.append(matches[i])
        
        return args    





    # http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html
    def __flatten(self,l, ltypes=(list)):
        ltype = type(l)
        l = list(l)
        i = 0
        while i < len(l):
            while isinstance(l[i], ltypes):
                if not l[i]:
                    l.pop(i)
                    i -= 1
                    break
                else:
                    l[i:i + 1] = l[i]
            i += 1
        return ltype(l)


    def start(self,*statements):
        return self.__flatten(list(statements))
   
    @v_args(meta=True)
    def include(self,meta, matches):

        base_filename = str(matches[0])
        current_file = self.__current_file
        new_parser = TransformingParser()
        
        for path in self.__include_path:
            #print("Check for :"+path+"/"+base_filename+".ccan")
            if os.path.isfile(path+"/"+base_filename+".ccan"):  
             
                result_list =  new_parser.parse(path+"/"+base_filename,self.__include_path) 

                to_list = list(result_list)
                flattened_list = self.__flatten(to_list)
        
                self.__current_file = current_file
                return flattened_list                
            else:
                continue
       

        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        error_string = "File not found in the available include directories: " + base_filename + ".ccan. \n"
        error_string += "The following include directories have been checked:\n"
        for path in self.__include_path:
            error_string += path +"\n"
    
        raise ResolverError(location_info,error_string)
        
    
    def sensor_drivers(self,*driver_list):
        liste = driver_list[0]
        return ParsedSensorDriverDescriptionList(list=liste)

    def communication_drivers(self,*driver_list):
        liste = driver_list[0]
        return ParsedCommunicationDriverDescriptionList(list=liste)

    def transport_adapter_types(self,*driver_list):
        liste = list(driver_list[0])
        return ParsedTransportAdapterDescriptionList(list=liste)
        
    @v_args(meta=True)
    def template_description(self,meta, matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        template_type_name          = str(matches[0])
        parameter_def_list          = matches[1]
        connection_description_list = matches[2]
        event_description_list      = matches[3]
        status_variable_description_list = matches[4]
        automation                  = matches[5]
        return ParsedDeviceDescription(name                      = template_type_name,
                                       type                       = "TEMPLATE",                                  
                                      parameter_description_list  = parameter_def_list,
                                      connection_description_list = connection_description_list,
                                      attribute_list             = [],
                                      event_description_list      = event_description_list,
                                      status_variable_description_list  = status_variable_description_list,
                                      degradation_description_list = None,
                                      automation                  = automation,
                                      location_info               = location_info)
                    
    @v_args(meta=True)
    def controller_description(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        controller_type_name       = str(matches[0])
        parameter_description_list = matches[1]
        offered_connection_usage   = matches[2]
        offered_communication_usage = matches[3]
        offered_adapter_usage        = matches[4]   
        degradation_description_list = matches[5]     
        return ParsedGeneralAppDescription(type              = "CONTROLLER",                                        
                                      name                   = controller_type_name, 
                                      parameter_description_list  = parameter_description_list,
                                      connection_description_list = [],
                                      offered_connection_usage    = offered_connection_usage,
                                      offered_communication_usage = offered_communication_usage,
                                      offered_adapter_usage       = offered_adapter_usage, 
                                      degradation_description_list  = degradation_description_list,
                                      location_info               = location_info)

    @v_args(meta=True)
    def app_description(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        expander_type_name          = str(matches[0])
        parameter_description_list  = matches[1]
        connection_description_list = matches[2]
        offered_connection_usage    = matches[3]
        degradation_description_list  = matches[4]
        
        return ParsedGeneralAppDescription(type                = "APP",
                                      name                     = expander_type_name, 
                                      parameter_description_list  = parameter_description_list,
                                      connection_description_list = connection_description_list,
                                      offered_connection_usage    = offered_connection_usage,
                                      offered_communication_usage = None,
                                      offered_adapter_usage   = None,
                                      degradation_description_list  = degradation_description_list,
                                      location_info               = location_info)
        

        
        
    @v_args(meta=True)
    def device_description(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        device_type_name                 = str(matches[0])     
        parameter_def_list               = matches[1]
        connection_description_list      = matches[2]
        if (len(matches) > 6):
            offset = 1
            attribute_list              = matches[3]
        else:
            offset = 0
            attribute_list               = []

        if attribute_list == None:
            attribute_list = []

        event_description_list           = matches[3+offset]
        status_variable_description_list = matches[4+offset]
        degradation_description_list     = matches[5+offset]
        
        return ParsedDeviceDescription(name                       = device_type_name, 
                                       type                       = "DEVICE",                                     
                                      parameter_description_list  = parameter_def_list,
                                      connection_description_list = connection_description_list,
                                      attribute_list             = attribute_list,
                                      event_description_list      = event_description_list,
                                      status_variable_description_list = status_variable_description_list,
                                      degradation_description_list= degradation_description_list, 
                                      automation = None,
                                      location_info               = location_info)        

    
    @v_args(meta=True)
    def ha_device_description(self,meta,matches):
    #("PSEUDO_DEVICE" TYPE_NAME "(" param_def_list ")" "{"  ha_event_description   "}") 
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        device_type_name                 = str(matches[0])     
        parameter_def_list               = matches[1]              
        event_description_list           = matches[2]
        status_variable_description_list = matches[3]
      
       
        return ParsedDeviceDescription(name                       = device_type_name, 
                                       type                       = "HOME_ASSISTANT_DEVICE",                                     
                                      parameter_description_list  = parameter_def_list,
                                      connection_description_list = [],
                                      attribute_list             = [],
                                      event_description_list      = event_description_list,
                                      status_variable_description_list = status_variable_description_list,
                                      degradation_description_list= None,
                                      automation = None,
                                      location_info               = location_info)             
    
    
    @v_args(meta=True)
    def enable_protocol(self,meta,matches):
        name  = str(matches[0])
        parameter_list = matches[1]
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        protocol  = ParsedProtocol(name=name, parameter_list = parameter_list, location_info = location_info)
        return protocol  
 
    def protocol_types(self,*descriptions):
        return descriptions[0]
 
    def protocol_type_list(self, *descriptions):
        liste = ParsedProtocolAdapterDescriptionList(list = descriptions)
        return liste    
    
    @v_args(meta=True)
    def protocol_type(self,meta,matches):
        protocol_type_name  = str(matches[0])
        parameter_def_list          = matches[1]
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        additional_protocol_description = ParsedAdditionalProtocolType(type = protocol_type_name, name = protocol_type_name,  parameter_description_list = parameter_def_list, degradation_description_list = None, location_info = location_info)
    
        return additional_protocol_description
    
    @v_args(meta=True)
    def alias_definition(self,meta,matches): 
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        name = str(matches[0])
        if isinstance(matches[1],FunctionExpression):
            expression     = matches[1]
        else:
            expression = str(matches[1])
        return ParsedAliasDefinition(name=name, expression = expression, location_info = location_info)

    @v_args(meta=True)
    def rule(self,meta, unresolved_events):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        mapping_list = []
        from_event = unresolved_events[0]
        to_events  = unresolved_events[1]
        
        result = ParsedMappingList(from_event = from_event, to_events = to_events, location_info = location_info)
        return result
        
        #for to_event in to_events:
        #    mapping_list.extend(ParsedMapping(from_event = from_event, to_event = to_event, location_info = location_info))
        #return ParsedMappingList(list = mapping_list)


    @v_args(meta=True)
    def export(self, meta, matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        return ParsedExportList(event_list = matches[0],
                                location_info = location_info)


    def transport_adapter_description_list(self,*descriptions):
        #liste = [item for sublist in descriptions for item in sublist]
        return descriptions
    
    @v_args(meta=True)
    def transport_adapter_description(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        protocol_name = str(matches[0])
        adapter_name  = str(matches[1])
        param_def_list = matches[2]
      
        degradation_description_list = matches[3]
        connection_description_list  = matches[4]

        return ParsedTransportAdapterDescription(type   = protocol_name, 
                                                 name   = adapter_name,
                                                 parameter_description_list = param_def_list,                                                
                                                 connection_description_list = connection_description_list,
                                                 degradation_description_list = degradation_description_list,              
                                                 location_info = location_info)
 
    
    def driver_description_list(self, *descriptions):
        liste = [item for sublist in descriptions for item in sublist]
        return liste
    
    @v_args(meta=True)
    def controller_instance(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        expander_type = str(matches[0])
        instance_name = matches[1][0]
        parameter_list = matches[1][1]

        ## check for uuid:
        if len(matches) == 5:
            uuid = None
            count = 0 
        else:
            uuid = matches[2]
            count = 1

        sensor_usage_list     = matches[2+ count]
        communication_usage_list = matches[3+count]
        adapter_usage_list       = matches[4+count]

        #if sensor_usage_list[0] == None:
        #    sensor_usage_list = []      

        #if adapter_usage_list[0] == None:
        #    adapter_usage_list = []      

        #if communication_usage_list[0] == None:
        #    communication_usage_list = []


        return ParsedControllerInstance(type                   = expander_type, 
                                      name                     = instance_name, 
                                      uuid                     = uuid,
                                      parameter_list           = parameter_list,
                                      sensor_usage_list        = sensor_usage_list, 
                                      communication_usage_list = communication_usage_list,
                                      adapter_usage_list       = adapter_usage_list,
                                      location_info            = location_info)
     
    @v_args(meta=True)
    def app_instance(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        expander_type = str(matches[0])
        instance_name = matches[1][0]
        parameter_list = matches[1][1]
        connected_to   = matches[2]        
        sensor_usage_list = matches[3]
              
        return ParsedAppInstance(type           = expander_type, 

                                      name           = instance_name, 
                                      uuid           = None,   
                                      parameter_list = parameter_list,
                                      connected_to   = connected_to,
                                      sensor_usage_list = sensor_usage_list, 
                                      location_info  = location_info)
 
        
      
    @v_args(meta=True)
    def device_instance(self,meta,matches):  
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        device_type    = str(matches[0])
        device_name    = matches[1][0]
        parameter_list = matches[1][1]
        
        connected_to   = matches[2]
        
        return ParsedDeviceInstance(type           = device_type, 
                                    name           = device_name, 
                                    parameter_list = parameter_list, 
                                    connected_to   = connected_to, 
                                    location_info  = location_info)
 
    
    @v_args(meta=True)
    def ha_device_instance(self,meta,matches):  
      
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)    
       
        device_type    = str(matches[0])
        device_name    = matches[1][0]
        parameter_list = matches[1][1]
        equivalent_list = matches[2]       
        #state_event_equivalent_list = matches[3]
       
        return ParsedHADeviceInstance(type           = device_type, 
                                    name           = device_name, 
                                    parameter_list = parameter_list, 
                                    equivalent_list= equivalent_list,                                  
                                    location_info  = location_info)
    
    
    @v_args(meta=True)
    def variable_instance(self,meta,matches): 
        
        if len(matches) == 3:
            connected_to = matches[2]
        else:
            connected_to = None

        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)         
        return ParsedVariableInstance(name=str(matches[0]),
                                      expression = matches[1],
                                      connected_to = connected_to,
                                      location_info = location_info)

    @v_args(meta=True)
    def template_variable_instance(self,meta,matches): 
        
        if len(matches) == 3:
            connected_to = matches[2]
        else:
            connected_to = None

        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)         
        return ParsedTemplateVariableInstance(name=str(matches[0]),
                                      expression = matches[1],
                                      connected_to = connected_to,                                    
                                      location_info = location_info)
        
    def variable_name(self,arg1,arg2):
        return arg1+"::"+arg2

    
    @v_args(meta=True)
    def extended_variable_name(self, meta, matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)    
        if isinstance(matches[0], ParsedVariableInExpression):
            return ParsedVariableName(name = (matches[0],str(matches[1])),
                                  location_info= location_info) 
        else:
            return ParsedVariableName(name = self.variable_name(str(matches[0]),str(matches[1])),
                                  location_info= location_info)
        


    def uuid_identifier(self,match):
        return match.value.replace('"','')  
       
    def argument(self,match):
        return match
      
        #result = self.__flatten(matches)
        #return result
        #text = ''
     
        #for i in range(len(matches)):
        # #   try:
        #        text += ''.join(matches[i])
        #    except TypeError:
        #        print("asdfsd")
        #print(text)
        #return text
       
        
    ########################################

    def automation(self,rule_list):
        return ParsedAutomation(list=rule_list)

    def automation_rule_list(self,*rules):
        return rules

    def automation_rule(self,rule):
        return rule

    def instance_with_param(self,name,parameter_list):
        return(str(name),parameter_list)

    def communication_pin_list(self,*communication_pin_list):
        if communication_pin_list[0] is None:
            return []
        return communication_pin_list 
  
    def connection_pin_list(self,*connection_pin_list):
        if connection_pin_list[0] is None:
            return []
        return connection_pin_list 
 
    @v_args(meta=True)
    def connection_pin(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)       
        pin_parameter_name = str(matches[0])
        hw_driver_type = str(matches[1])
        return ParsedConnectedPin(name = pin_parameter_name,driver_type = hw_driver_type, location_info = location_info)

    def pin_list_description(self,*pin_description): 
        result = pin_description
        if pin_description[0] is None:
            result = []
            
        return ParsedPinList(list = result)

    def communication_driver_list(self,*pin_description):
        if pin_description[0] is None:
            pin_description = []
        return ParsedCommunicationList(list = pin_description)
        

    def adapter_list_description(self,*pin_description): 
        if pin_description[0] is None:
            pin_description = []
        return ParsedAdapterList(list = pin_description)

    @v_args(meta=True)
    def adapter_pin(self,meta,matches):
        pin_name = matches[0]
        driver_name = matches[1]
        parameter_list = matches[2]
        connected_to = matches[3]
        supported_protocol = str(matches[4])
        
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        return ParsedTransportAdapterUsage (name  = pin_name,     
                              alias_name          = None,                       
                              driver_name         = driver_name,
                              parameter_list      = parameter_list,
                              connected_to        = connected_to,
                              supported_protocol  = supported_protocol,
                              location_info       = location_info)



    def adapter_description(self,offered_pin_usage, supported_protocols):
        name          = offered_pin_usage.name
        driver_list   = offered_pin_usage.driver_list
        location_info = offered_pin_usage.location_info
          
        adapter_description = ParsedOfferedTransportAdapterUsage (name  = name,
                                                           driver_list = driver_list,
                                                           supported_protocols = supported_protocols,
                                                           location_info = location_info)
        return adapter_description

    @v_args(meta=True)
    def pin_description(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        
        pin_name = str(matches[0])
        
        driver_list = []
        for driver in matches[1]:
            driver_list.append(str(driver))
        
        return ParsedOfferedConnectionUsage(name = pin_name, driver_list = driver_list, location_info = location_info)

    def hw_driver_list(self,*hw_driver_list):
        driver_name_list= []
        for driver in hw_driver_list:
            driver_name_list.append(str(driver))
        return driver_name_list

    def adapter_list(self,*adapter_list):
        if adapter_list[0] is None:
            return []
        return adapter_list

    def usage_pin_list(self,*usage_pin_list):    
        if usage_pin_list[0] is None:  
            return []
        return usage_pin_list

    @v_args(meta=True)
    def usage_pin(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)     
        return ParsedUsagePin(name= str(matches[0]),
                    usage_pin_entry_list  = matches[1],
                    location_info  = location_info)

    @v_args(meta=True)
    def usage_pin_entry(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)    
       
        hw_driver_name      = str(matches[0])
        parameter_list      = matches[1]
        alias_name          = str(matches[2])
        
        pin_entry =  ParsedUsagePinEntry( driver_name = hw_driver_name,
                              alias_name = alias_name,                             
                              parameter_list = parameter_list,
                              connected_to  = None,
                              location_info = location_info)
        return pin_entry

    def usage_pin_entry_list(self,*entry_list):
        if entry_list[0] is None:
            return []
        return list(entry_list)

    @v_args(meta=True)
    def pseudo_pin(self,meta,matches):

        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        definition_pin_name = str(matches[0])
        hw_driver_name      = str(matches[1])
        parameter_list      = matches[2]
        connected_to          = matches[3]
        
        
        return ParsedUsagePin(name = definition_pin_name,
                              alias_name = None,
                              driver_name = hw_driver_name,
                              parameter_list = parameter_list,
                              connected_to = connected_to,
                              location_info = location_info)

    @v_args(meta=True)
    def transport_adapter_list(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        adapter_list = []
        for adapter in matches:
            adapter_list.append(str(adapter))
        return ParsedOfferedTransportAdapterList ( list = adapter_list,
                                                   location_info = location_info)
 
    
    #:      ( "TRANSPORT_ADAPTER" ":" "[" DRIVER_NAME ("," DRIVER_NAME)* "]")


    def transport_adapter_instance_list(self,*instances):
        if instances[0] is None:
            return []
        return instances
    #:    ( "TRANSPORT_ADAPTER" "{" [ transport_adapter_instance ("," transport_adapter_instance)*] "}" )
    
    
    @v_args(meta=True)
    def transport_adapter_instance(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
          
        instance_with_param = matches[0]
        if matches[1] is not None:
            connected_to_name  = matches[1].name
        else:
            connected_to_name = None

        parsed_used_pin_entry = ParsedUsagePinEntry(   driver_name = instance_with_param[0],
                              alias_name = "TRANSPORT_ADAPTER_" + str(self.__transport_adapter_counter),                           
                              parameter_list = instance_with_param[1],
                              connected_to  = connected_to_name,
                              location_info = location_info)


        parsed_usage_pin =  ParsedUsagePin(name = "TRANSPORT_ADAPTER",
                            usage_pin_entry_list = [ parsed_used_pin_entry],
                            location_info= location_info)

        self.__transport_adapter_counter += 1

        return parsed_usage_pin
        #return ParsedTransportAdapterInstance(name  = instance_with_param[0],
        #                                      parameter_list  = instance_with_param[1],
        #                                      connected_to = connected_to,
        #                                      location_info = location_info)
  

    @v_args(meta=True)
    def transport_adapter_description_OLD(self,meta,matches):
        adapter_descriptions = []
        adapter_type = str(matches[0])
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
 
        for i in range(len(matches)-1): 
            adapter_descriptions.append(ParsedTransportAdapterDescription(type= str(adapter_type), 
                                                                        name = matches[i+1].children[0], 
                                                                        parameter_description_list = matches[i+1].children[1],
                                                                        connection_description_list = matches[i+1].children[2],
                                                                        degradation_description_list  = matches[i+1].children[3],
                                                                        location_info = location_info))
        return adapter_descriptions
        
    @v_args(meta=True)
    def driver_description(self, meta,matches):
        driver_descriptions = []
     
        driver_type = str(matches[0])

        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        
        for i in range(len(matches)-1):
            driver_descriptions.append(ParsedSensorDriverDescription(type= str(driver_type), 
                                                                        name = matches[i+1][0], 
                                                                        parameter_description_list    = matches[i+1][1],
                                                                        degradation_description_list  = matches[i+1][2],
                                                                        location_info = location_info))
        return driver_descriptions  
    
    def driver(self,driver_name,param_def_list,degradation_code_description):   
        return([str(driver_name),param_def_list,degradation_code_description])

    def status_variables_description(self,status_variable_list):
        return status_variable_list

#    def status_variable_description_list(self,*status_variable_tuple):
#        status_variable_list = list(status_variable_tuple)
#        return status_variable_list 

#    @v_args(meta=True)
#    def status_variable_description(self,meta,matches):
#        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
#        result = ParsedStatusVariable( status_variable_name = str(matches[0]),
#                                       status_variable_type = str(matches[1]),
#                                       location_info = location_info)
#        return result

    def degradation_codes_description(self,code_list):
        return code_list

    def degradation_code_list(self,*code_list_tuple):
        if code_list_tuple[0] is None:
            return []
        code_list = list(code_list_tuple)
        return code_list

    @v_args(meta=True)            
    def degradation_code(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        code_name = matches[0]
        explanation_with_high_comma = str( matches[1])
        explanation_with_no_high_comma = explanation_with_high_comma.replace(chr(34),'')
        new_degradation_code = ParsedDegradationCode(name = str(code_name), explanation=  explanation_with_no_high_comma, location_info = location_info)  
        return new_degradation_code
 

    def function_expression(self,*matches):
        text = text = " ".join(matches)
        return text
    
    def operand(self, operand):
        return operand
        
    def function(self,name,*function_expressions):
        #location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        text = name + "("  + " ".join(function_expressions)  + ")"
        return text
    
    def equivalent_list(self, *equivalents):        
        equivalence_list = []
        for equivalent in equivalents:
             equivalence_list.append(equivalent)
        return equivalence_list  

    @v_args(meta=True)
    def equivalent(self, meta, matches):        
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)             
        name = str(matches[0])
        equivalent =  matches[1]
        
          
        return ParsedEquivalent(name = name,
                                equivalent  = equivalent,
                                location_info = location_info)

  
    def  equivalent_item(self,item):
        return item

    @v_args(meta=True)
    def event_description(self, meta, matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)                              
                          #input_event = None,output_events = None):
        input_events  = matches[0]
        output_events = matches[1]
        event_description_list = []
        if input_events != [None]:
            for event in input_events:
                event_description_list.append(ParsedEventDescription(in_out_type = "IN",name = event[0], parameter_description_list = event[1], location_info = location_info))
        if output_events != [None]:
            for event in output_events:
                event_description_list.append(ParsedEventDescription(in_out_type = "OUT", name = event[0], parameter_description_list = event[1], location_info = location_info))
        return event_description_list    
        
        #n_out_type name parameter_description_list location_info
      
    @v_args(meta=True)
    def ha_event_description(self, meta, matches):
        #(input_events output_events get_state_events)     
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)                              
                          #input_event = None,output_events = None):
        input_events  = matches[0]
        output_events = matches[1]
        get_state_events = matches[2]
        event_description_list = []
        if input_events != [None]:
            for event in input_events:
                event_description_list.append(ParsedEventDescription(in_out_type = "IN",name = event[0], parameter_description_list = event[1], location_info = location_info))
        if output_events != [None]:
            for event in output_events:
                event_description_list.append(ParsedEventDescription(in_out_type = "OUT", name = event[0], parameter_description_list = event[1], location_info = location_info))
        if get_state_events != [None]:
            for event in get_state_events:
                event_description_list.append(ParsedEventDescription(in_out_type = "GET_STATE", name = event[0], parameter_description_list = event[1], location_info = location_info))
                      
        return event_description_list    
                     
    def input_events(self, upper_case_param_list):
        return upper_case_param_list

    def output_events(self, upper_case_param_list):
        return upper_case_param_list
        
    def get_state_events(self, upper_case_param_list):
        return upper_case_param_list        

    @v_args(meta=True)
    def event_equivalent(self,meta,matches):      
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)    
        event_name  = str(matches[0])
        parameter_list = matches[1]
        equivalent_list   = matches[2]
        return ParsedEventEquivalent (event_name = event_name,
                                   parameter_list = parameter_list,
                                   equivalent_list = equivalent_list,
                                   location_info = location_info            
            ) 
            
    def simple_event_list(self, *events):
        event_list = []
        for event in events:
            event_list.append(event)
        return event_list    
                                   
                                   
    @v_args(meta=True)                                     
    def simple_event(self,meta,matches):  
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)    
        extended_name = matches[0]
        simple_parameter_list = matches[1]
        return ParsedSimpleEvent(extended_name = extended_name,
                                simple_parameter_list = simple_parameter_list,
                                location_info = location_info)
        
  
                                   
    def event_list(self,*events):
        event_list = []
        for event in events:
            event_list.append(event)
        return event_list    
        #return UnresolvedEvent(device_name = str(device_name), event_name = str(event_name), parameter_list = parameter_list)

    @v_args(meta=True)
    def event(self,meta,matches): 
        return matches[0]
        
    @v_args(meta=True)
    def not_ccan_event(self,meta,matches):
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)        
        protocol_name = str(matches[0])
        path  = matches[1]
        event_name = str(matches[2])
        parameter_list = matches[3]        

        return ParsedEvent(protocol_name = protocol_name, device_path_name = path, event_name = event_name,  parameter_list  = parameter_list,location_info = location_info)
    
    @v_args(meta=True)
    def ccan_event(self,meta,matches): #device_name,event_name,parameter_list):       
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)

        if isinstance(matches[0], ParsedVariableInExpression):
            device_name = matches[0]
        else:
            device_name = str(matches[0])
        event_name  = str(matches[1])
        parameter_list = matches[2]

        return ParsedEvent(protocol_name = "CCAN", device_path_name = device_name, event_name = str(event_name), parameter_list = parameter_list, location_info = location_info)


    def attribute_list(self,*names):
        return [str(*names)]

    def attributes(self,attribute_list):
        return attribute_list

    def simple_parameter_list(self,parameter_list):
        return parameter_list
    
    def upper_case_param_list(self, *upper_case_parameter_list):
        parameter_list= []
        for parameter in upper_case_parameter_list:
            parameter_list.append(parameter)
        return parameter_list
         

    def upper_case_param(self,name,param_def_list = None):
        return (str(name),param_def_list)

    def extended_name(self,*args):
        return ".".join(list(args))

    @v_args(meta=True)
    def param_def_list(self,meta, matches): 
        
        parameter_name_list = []
        parameter_type_list = []
        dimension_list      = []
        parameter_constraints_list    = []
        parameter_defaults_list= []
        location_info = None

    
        if len(matches) > 0 and matches[0] is not None:      
            
            location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)     
            for parameter in matches:  
                parameter_name_list.append(str(parameter[0]))
                parameter_type_list.append(str(parameter[1]))
                parameter_constraints_list.append(parameter[2])
                parameter_defaults_list.append(parameter[3])
                dimension_list.append("Scalar")

        
        return ParsedParameterDescriptionList( parameter_name_list = parameter_name_list, 
                                                parameter_type_list = parameter_type_list, 
                                                parameter_constraints_list = parameter_constraints_list,
                                                parameter_defaults_list= parameter_defaults_list,
                                                dimension_list = dimension_list,                                                  
                                                location_info = location_info)
  
    def param_def(self,param_name,param_type, param_constraints, default_value):                
        return [str(param_name),str(param_type), param_constraints, default_value]

    @v_args(meta=True)
    def param_list(self,meta, matches):
        try:
            parsed_parameter= []     
            if matches != [None]:
                for parameter in matches:  
                    parsed_parameter.append((parameter[0],parameter[1]))
            return parsed_parameter
        except Exception as e:
            pass

    @v_args(meta=True)
    def parameter_constraints(self,meta, matches):   
       
        location_info = LocationInfo(file = self.__current_file,line = meta.line, column = meta.column)
        constraint_type = matches[0]
        constraint_values = matches[1:]

        return ParsedConstraints(constraint_type = constraint_type,
                                 constraint_values = constraint_values,
                                 location_info = location_info)
        
    def enumeration_of_allowed_parameters(self,*args):
        
        constraint_type = "List"
        constraint_values = list(args)
        return (constraint_type, constraint_values)


 #(enumeration_of_allowed_parameters|list_of_allowed_parameters)


    def var_expression(self,*arg_list):   
        if (len(arg_list) == 1):
            pass        

        if arg_list[0] == None:
            return [None, arg_list[1]]
        else:         
            return [str(arg_list[0]),arg_list[1]]
      
    def expression(self,matches):
        text= str(matches)
        return text


    def parse(self,base_filename, include_path):
        self.__include_path = include_path
        
        if os.path.basename(base_filename) is not None:
            filename = base_filename + ".ccan"
            try:
                text_file = open(filename, "r")
                text = text_file.read()
                
            except FileNotFoundError:
                raise ResolverError(None,f"Could not find configuration file {filename}.")
                if  self.__current_file is None:
                    print("Could not find configuration file " + filename)
                else:
                    print("Could not find configuration file" + filename + ", included in " + self.__current_file)
                return None
        else:
            found = True
            for path in include_path:
                filename =  path + base_filename + ".ccan"
                found = True
                try:
                    text_file = open(filename, "r")
                    text = text_file.read()
                except FileNotFoundError:
                   found = False
                
                if found is True:
                   break
            
            if found is False:
                if  self.__current_file is None:
                    print("Could not find configuration file " + filename)
                else:
                    print("Could not find configuration file" + filename + ", included in " + self.__current_file)
                return None
        
        self.__current_file = filename    
        try:           
            tree = self.__parser.parse(text)
        except lark.exceptions.VisitError as e:
            location = LocationInfo(filename+".ccan",e.line, e.column)      
        except lark.exceptions.UnexpectedCharacters as e: 
            location = LocationInfo(filename,e.line, e.column)

            #print(filename + ": " +str(e.line)+":" +str(e.column) + " Syntax error")
            raise ResolverError(location,"Syntax error detected. Found unexpected character: '" + e.char + "'.")      

            #print(filename + ": " +str(e.line)+":" +str(e.column) + " Syntax error")
            raise ResolverError(location,"Syntax error detected. Found unexpected character: '" + e.char + "'.")  
        parsed_list = self.transform(tree)
        return parsed_list



 