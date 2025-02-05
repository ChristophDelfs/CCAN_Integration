from src.resolver.ResolverError import ResolverError
#from lark import Lark, InlineTransformer
from lark import Lark, Visitor
from src.resolver.Definitions import CompilerMode,ParameterSet, LocationInfo

from src.resolver.Definitions import OperatorTypeKey,Operator, ParsedVariableInExpression, ElementTypeKey, OperandTypeKey, ParsedSymbol
from numbers import Number

from src.resolver.ResolverError import ResolverError

from src.resolver.ResolverElements import ResolvedParameter, ParameterFormat
from src.resolver.ResolverElements import EventVariable, SerializedFunctionExpression, Function, FunctionExpression
from src.resolver.ResolverElements import ResolvedFunctionElement, ResolvedConstantElement, ResolvedVariableElement, ResolvedEventParameterElement, ResolvedSymbol

       
class ParameterStore(Visitor): #InlineTransformer):
    from operator import add, sub, mul, truediv as div, neg
    
    #from operator import methodcaller as event_name
    #from operator import methodcaller as instance_name
    #from operator import methodcaller as alias
    
    from operator import methodcaller as get_string
    from operator import methodcaller as add_string
    number= float
    #string = str
    
    #__mode_binary = "binary"
    #__mode_binary_config = "binary_config"
    #__mode_text  = "text"
    #__mode_xml    = "xml"
    __engine_magic_cookie = 0xE138 
    
    #https://github.com/lark-parser/lark/blob/master/examples/calc.py
    
    __expression_parser = Lark('''
    ?start: arg  
    

    arg:     sum           -> argument
           | sum_str       -> string_argument
  
    ?sum: product 
        | sum "+" product   -> add_func
        | sum "-" product   -> sub_func
      
    ?product: atom
        | product "*" atom  -> mul_func
        | product "/" atom  -> div_func
        | "(" sum ")"

    ?atom: NUMBER               -> number
         | hex                  -> hex_number
         | "-" atom             -> neg_func
         | ALIAS                -> alias       
         | "(" sum ")"
         | function_expression 
         | function
         
    ?function_expression:  event_variable
                         | instance_variable       

    ?sum_str: atom_string 
        | sum_str "+" atom_string  -> add
    ?atom_string: QUOTED_STRING    -> get_string
        | ALIAS_STRING             -> alias
                                  
    event_variable:             ("EVENT" "::" PARAM_NAME)         -> event_name 
    instance_variable:          ( (CNAME "::" CNAME))   
    function:                   (CNAME "(" arg_list  ")")
    arg_list:                   [arg ("," arg)*]

    hex.2 : HEXNUMBER
    OPERATOR:                    ("*"|"+"|"-"|"/")

    
    UCASE_CNAME:                 (UCASE) ("_"|UCASE|DIGIT)*
    LCASE_CNAME:                 (LCASE) ("_"|LCASE|DIGIT)*
    
    PARAM_NAME:                  DNAME  
    NAME:                        CNAME

    VALUE:                       (UNBRACKETED_VALUE|BRACKETED_VALUE)
    BRACKETED_VALUE:             "(" UNBRACKETED_VALUE ")"
    UNBRACKETED_VALUE:           (HEXNUMBER|NUMBER|QUOTED_STRING|SYMBOL)
    SYMBOL:                      (NAME ("::" NAME)*)     
    DNAME:                       ((LETTER) ("_"|LETTER)* [NUMBER*])   
    QUOTED_STRING:               /"[^"]*"/
    HEXNUMBER :                  (("0x"|"0X") ("0".."9" | "A".."F" | "a".."f")+)  
        
    ALIAS: (CNAME)
    ALIAS_STRING: (CNAME)
    
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

        ''', parser = "earley")
    
    def __init__(self):
    
        self.__alias_list = {}
        #__dev_current_key          = 100

        #self.load_device_table("dummy_file")
        pass

    def argument(self,matches):
        result = self.simplify(matches)
        return result

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
      
      
    def resolve_alias(self,alias): 

        if isinstance(alias, ParsedVariableInExpression):
            name = alias.name                
        elif isinstance(alias,str) is True:
            name = alias
        else:          
            return alias

        if name.upper() == "TRUE":
            return 1
        if name.upper() == "FALSE":
            return 0        
   
        try:            
            return self.__alias_list[name]    
        except KeyError:
            return alias 




    def add_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '+')
        return result
    
    def sub_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '-')
        return result        

    def mul_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '*')
        return result  
    
    def div_func(self,arg1,arg2):
        result = FunctionExpression(operand1= arg1,operand2 = arg2, operator = '/')
        return result  

    def neg_func(self,arg):
        result = FunctionExpression(operand1= 0,operand2 = arg, operator = '-')
        return result

    def event_name(self,name):        
        event = ParsedVariableInExpression(name = name, type = "EVENT_PARAMETER")
        return event
 
   
    def instance_variable(self,device,variable):
        # instance can be_
        #   a) TEMPLATE alias
        test_item = device+"::"+variable
        alias = self.resolve_alias(test_item)
        if alias != test_item:
           return alias
        
        name = str(device)+"::"+str(variable)
        var = ParsedVariableInExpression(name = name,type = "VARIABLE")        

        return var

    def function(self,name,argument_list):
        function = Function(name,argument_list)
        result = ParsedVariableInExpression(value= function,type = "FUNCTION")
        return result
         
    def arg_list(self,*matches):
        args = []
        for i in range(len(matches)):
            args.append(matches[i])
        
        return args
            
    def insert_alias(self,param,value):
        # Check whether element already has been defined:
        try:
            test = self.__alias_list[param] 
        except KeyError:
            # convert value:
            try:
                numeric_value = float(value)
                self.__alias_list[param] = numeric_value
            except (ValueError,TypeError):
                if isinstance(value,str):
                    self.__alias_list[param] = self.get_string(value)                                    
                else:
                    self.__alias_list[param] = value
            return

        raise ResolverError(None,"Symbol <" + param + "> has been defined already.")
        return

    def resolve(self,expression, parameter_type, parameter_event_reference_allowed= True):
        resolved_parameter = self.simplify(expression, parameter_type, parameter_event_reference_allowed)
        #resolved_parameter = self.transform(self.__expression_parser.parse(expression_text))
        return resolved_parameter 

        
    def simplify(self,expression, parameter_type, parameter_event_reference_allowed = True):
        """ simplifies the given expression as far as possible
            The given expression is simplified with the following goals:
            
            1)  return a single value
            2)  return a function expression with first operand being a number
            3)  return a function expression with both operands being not a number
        """                             
        if isinstance(expression, FunctionExpression) is False:
           
            alias = self.resolve_alias(expression)
            # and parameter_event_reference_allowed == False:
            #    raise AttributeError

            if isinstance(alias,ParsedVariableInExpression) is True:               
                return FunctionExpression(alias,None,None)
            elif isinstance(alias, ResolvedConstantElement) is True:
                return alias.get_value()
            else:
                return alias

        op1 = expression.operand1()
        op2 = expression.operand2()



        # auskommentiert, weil Template-Parameter wie ein Event-Parameter erscheinen!        
        #if (isinstance(op1, ParsedVariableInExpression) or isinstance(op2, ParsedVariableInExpression)) and parameter_event_reference_allowed == False:
        #    raise AttributeError

        # expression is a function expression:
        #if isinstance(op1,FunctionExpression):
        op1 = self.simplify(op1, parameter_type) 
        #if isinstance(op2,FunctionExpression):
        op2 = self.simplify(op2, parameter_type)        

        if isinstance(op1,ResolvedConstantElement):
            op1 = op1.get_value()
        if isinstance(op2,ResolvedConstantElement):
            op2 = op2.get_value()
                        


        # Goal 1 is reached!
        if isinstance(op1,Number) and isinstance(op2,Number):
            return self.__calculate(op1,op2,expression.operator())

        # default result:
        result = FunctionExpression(op1,op2,expression.operator())

        # check whether at least 1 operator is a function expression
        # only in this case it makes sense to continue and check for merges / rearrangement:
        if isinstance(op1,FunctionExpression) == False and isinstance(op2,FunctionExpression) == False:
            return result

        # second check: do the embracing operation allows a merge of the embedded operators:
        if  isinstance(op1,FunctionExpression):
            if self.__is_similar(op1.operator(),expression.operator()) == False:
                return result
        if  isinstance(op2,FunctionExpression):
            if self.__is_similar(op2.operator(),expression.operator()) == False:
                return result            

        #
        # Now we are ready to analyze to merge and rearrange (goal 2)
        #
                
        op_list = []
        operator_list = []
        # if at least one number is part of the result, let us check whether we can / need to rearrange
        if isinstance(result.operand1(),FunctionExpression):
            op_list.append(result.operand1().operand1())
            op_list.append(result.operand1().operand2())
            operator_list.append(result.operand1().operator())
        else:
            op_list.append(result.operand1())

        operator_list.append(result.operator())

        if isinstance(result.operand2(),FunctionExpression):
            op_list.append(result.operand2().operand1())
            op_list.append(result.operand2().operand2())
            operator_list.append(self.__combine_operators(result.operator(), result.operand2().operator()))
        else:
            op_list.append(result.operand2())

        if len(op_list) < 3:
            # this cannot be done shorter:
            return result

        # rearrange the list of operand and operators so that numbers come first: 
        new_op_list = []
        new_operator_list = []
        for (i,op) in zip (range(len(op_list)),op_list):
            if isinstance(op,Number):
                new_op_list.insert(0,op)
                new_operator_list.insert(0,self.__access_operator_list(operator_list,i-1))
            else:
                new_op_list.append(op)
                new_operator_list.append(self.__access_operator_list(operator_list,i-1))
            
            
        # check outcome:
        if isinstance(new_op_list[0],Number) == False:
            # no numbers in the result expression -> give up
            return result
        elif isinstance(new_op_list[1],Number) == True:
            # the first two are numbers -> merge them!
            (first_op, ignored_operator) = self.__reverse_operation(new_op_list[0],new_operator_list[0],None)
            new_op_list[0] = self.__calculate(first_op,new_op_list[1], new_operator_list[1])
            # and remove the merged item:
            del new_op_list[1]
            del new_operator_list[0]
            
        # assemble new operand and operators:
        # special handling for division:
        if new_operator_list[0] == '/':
            op2 = new_op_list[0]
                                 
            if len(new_op_list) == 3:
                new_operator = self.__combine_operators(new_operator_list[1],new_operator_list[2])
                op1    = FunctionExpression(new_op_list[1],new_op_list[2],new_operator)
                result = FunctionExpression(op1, op2, new_operator_list[0])
            else:
                op1 = new_op_list[1]
                result = FunctionExpression(op1, op2, new_operator_list[0])
            
        else:
            (op1, ignored_operand) = self.__reverse_operation(new_op_list[0], new_operator_list[0],None)
        
            if len(new_op_list) == 3:
                new_operator = self.__combine_operators(new_operator_list[1],new_operator_list[2])
                op2    = FunctionExpression(new_op_list[1],new_op_list[2],new_operator)
                result = FunctionExpression(op1, op2, new_operator_list[1])
            else:
                op2 = new_op_list[1]
                result = FunctionExpression(op1, op2, new_operator_list[1])
            
        return result

    def __access_operator_list(self,liste,index):
        if index < 0:
            if liste[0] == '*' or liste[0] == '/':
                return '*'
            if liste[0] == '-' or liste[0] == '+':
                return '+'
        return liste[index]

    def __combine_operators(self,op1,op2):
        if op1 == op2:
            if op1 == '/':
                return '*'
            if op1 == '-':
                return '+'
            return op1
        if op1 != op2:
            if op1 in  ['/','*']:
                return '/'
            else:
                return '-'
      
    def __reverse_operation(self,operand,operator,offered_operator):
        if operator =='*' and offered_operator == None:
            return (operand,operator)
        if operator =='/' and offered_operator == None:
            return (1/operand,'*')
        if operator =='+' and offered_operator == None:
            return (operand,operator)
        if operator =='-' and offered_operator == None:
            return (-operand,'+')

        if operator =='*' and offered_operator =='/':
            return (1/operand,'/')
        else:
            return (operand,'*')
        
    def __is_similar(self,operator1,operator2):
        l1 = [ '*','/']
        l2 = ['+','-']
        if operator1 in l1 and operator2 in l1:
            return True
        if operator1 in l2 and operator2 in l2:
            return True
        return False
    
    def __calculate(self,operand1,operand2,my_operator):
        if isinstance(my_operator,ResolvedFunctionElement) is True:
            operator = str(my_operator.get_operator())
        else:
            operator = my_operator

        result = None
        if operator == "*":
            result = operand1 * operand2
        elif operator == "/":
            result = operand1 / operand2            
        elif operator == "+":
            result = operand1 + operand2
        elif operator == "-":
            result = operand1 - operand2
        else:
            raise AttributeError

        return result
    

    def get_parameter_value(self, my_parameter):
        result = my_parameter.get_value()
        if isinstance(result,SerializedFunctionExpression):
            return result.get_value()
        
        return result

    def find_and_replace_in_function_expression(self,my_function_expression, my_replace_variables):
          
        changed_flag = False    
        new_expression_list = []  

        if isinstance(my_function_expression,list) is False:
            return (False,my_function_expression)

        try:
            for var_element,i in zip(my_function_expression,range(0,len(my_function_expression))):                       
                    if isinstance(var_element, ResolvedEventParameterElement):
                        if var_element.get_name() in list(my_replace_variables.keys()):
                            replacement_list = my_replace_variables[var_element.get_name()]

                            if isinstance(replacement_list,list) is False:
                                replacement_list = [replacement_list]

                            new_expression_list += replacement_list
                            changed_flag = True 
                        else:
                            # referenced variable name is not part of the list
                            error_string = "Reference to variable EVENT::"+var_element.get_name()+ " cannot be used here. Allowed references are "
                            for i, var_name in zip(range(len(list(my_replace_variables.keys()))),list(my_replace_variables.keys())):
                                error_string += "EVENT::"+var_name
                                if i < len(list(my_replace_variables.keys()))-1:
                                    error_string += ", "
                                else:
                                    error_string +="."
                                
                            raise ResolverError(None,error_string)
                    else:
                        new_expression_list.append(var_element)
        except TypeError:
            pass
        except AttributeError:
            pass

        return (changed_flag, new_expression_list)


    def serialize_operations(self, expression):   
        """ provides a flat list of operators and operands in UPN sequence from the expression.           
        """    
        result_list = []
        if isinstance(expression, (Number, ParsedVariableInExpression, ResolvedVariableElement, ResolvedEventParameterElement)):
            result_list.append(expression)
            return result_list

        if isinstance(expression,ResolvedConstantElement):
            result_list.append(expression.get_value())
            return result_list

        if isinstance(expression,SerializedFunctionExpression):
            result_list.extend(expression.get_value())

        if isinstance(expression,FunctionExpression):
            if expression.operator() == None:
                result_list.extend(self.serialize_operations(expression.operand1()))    
            else:
                resolved_operator = ParameterStore.__resolve_operator(expression.operator())
                result_list.append(resolved_operator)
                result_list.extend(self.serialize_operations(expression.operand1()))
                result_list.extend(self.serialize_operations(expression.operand2()))
        
        return result_list


    def deserialize(self,remaining_list):
        return  self.deserialize_operations(remaining_list)
      
    
    def deserialize_operations(self,remaining_list):
        
        first_element = remaining_list[0]
        remaining_list = remaining_list[1:]        

        is_operator, operator = ParameterStore.__identify_operator(first_element)

        # first element is an operator:
        if is_operator == True:
        
            operand1 = remaining_list[0]

            is_operator, value = ParameterStore.__identify_operator(operand1)
            if is_operator == True:
                (remaining_list, operand1) = self.deserialize_operations(remaining_list)
            else:
                remaining_list = remaining_list[1:]                             
                if isinstance(operand1 , ResolvedConstantElement):
                    # either this is a constant value:
                    operand1 = operand1.get_value()
                    
            operand2 = remaining_list[0]
            is_operator, value = ParameterStore.__identify_operator(operand2)
            if is_operator == True:
                (remaining_list, operand2) = self.deserialize_operations(remaining_list)
            else:
                remaining_list = remaining_list[1:]                 
                if isinstance(operand2 , ResolvedConstantElement):
                    # either this is a constant value:
                    operand2 = operand2.get_value()
           

            resolved_operator = ParameterStore.__resolve_operator(operator)
                #resolved_operator.set_number_of_arguments(2)
            return  (remaining_list,FunctionExpression(operand1,operand2,resolved_operator))
        
            # if both operand1 now turn out to be constant numbers, we can simplify the expression by providing the result:
            #if isinstance(operand1, Number) and isinstance(operand2, Number):               
            #    # calculate:
            #    if isinstance(Operator,str):
            #        operator = str(operator.get_operator())
            #    result = self.__calculate(operand1,operand2,operator)

            #else:
            #    # otherwise we put it all into a function expression:
              
        
        else:
            # first element must be a constant:
            result = first_element         
            # check whether the result is a constant:
            if isinstance(result, ResolvedConstantElement):                
                # if yes, rather return the value than the container:
                result = result.get_value()

        return (remaining_list, result)

    
    @staticmethod
    def __identify_operator(my_operator):
        result = False     
        operator = my_operator
        if isinstance(my_operator,ResolvedFunctionElement):
            result = True
            operator = str(my_operator)
        elif isinstance(my_operator,Operator):
            operator = my_operator.value
            result = True

        return result, operator


    @staticmethod
    def __resolve_operator(operator):
        if isinstance(operator,str):
            resolved_element = ResolvedFunctionElement(operator)
            resolved_element.set_number_of_arguments(2)
        elif isinstance(operator,Operator):
            resolved_element = ResolvedFunctionElement(operator.name)
            resolved_element.set_number_of_arguments(operator.number_of_arguments)
            operator_id = OperatorTypeKey[operator]
        elif isinstance(operator,ResolvedFunctionElement):
            resolved_element = operator
        else:
            raise TypeError

        return resolved_element
        #return Operator(value = operator, id = operator_id, number_of_arguments = 2)


    @staticmethod
    def convert_param_to_string(param_list,param_type_list):
        seq = ParameterStore.convert_param_list_to_byte_array(param_list,param_type_list)
        converted = ""               
        for i in range(len(seq)):
            converted  +=  "{:02x}".format(seq[i])
        return converted
    
    @staticmethod
    def convert_param_list_to_byte_array(resolved_parameter):
        seq = []
        
        value_list = map( lambda ResolvedParameter: ResolvedParameter.get_value(), resolved_parameter)
        format_list  = map( lambda ResolvedParameter: ResolvedParameter.get_format(), resolved_parameter)
        
        for value,my_format in zip(value_list,format_list):           
            target_format = str(my_format)
            try:
                value = int(value)
            except TypeError:
                pass
            if target_format == "UINT64" or target_format == "INT64":
                div_steps = 8
            if  target_format == "UINT32" or target_format == "IPV4_ADDRESS" or target_format == "INT32":       
                div_steps = 4
            elif target_format == "UINT16" or target_format == "INT16":
                div_steps = 2
            elif target_format == "UINT8" or target_format == "INT8":
                div_steps = 1
            else:
                raise ResolverError(None,"Internal Error in convert_param_list_to_byte_array - unsupported type:" + str(target_format))
            
            for j in range(div_steps):
                seq.extend([value & 255])
                value >>= 8            
        return seq
         
    def resolve_optional_parameter_list(self,param_list, parameter_name_list,parameter_type_list, parameter_event_reference_allowed,location_info):
        if param_list is None:
            return  []
        if len(param_list) == 0:
            return []
        return self.resolve_parameter_list(param_list, parameter_name_list,parameter_type_list, parameter_event_reference_allowed, location_info)
        
        
    def resolve_parameter_list(self,param_list, parameter_name_list,parameter_type_list, parameter_event_reference_allowed, location_info):
        """ Resolves arguments, i.e. replaces symbolic information, resolves symbolic arguments, calculates the final value of an argument
        Input:
            parameter list (user input to resolve)
            parameter description list (type and name information)
            
         Returns:
             resolved parameters""" 
        
        if (parameter_name_list == None) or (len(parameter_name_list) == 0):
            return []
                
        resolved_params = [None]* len(parameter_name_list)

        if len(param_list) != len(parameter_name_list):
            raise ResolverError(location_info,"Number of arguments " + str(len(param_list)) + " does not match expected number which is " + str(len(parameter_name_list))+".")

        
        param_names_given = False
        param_value_set = [False]* len(param_list)
        
        for param,i in zip(param_list,range(len(param_list))):
            
            try:
                resolved_parameter_type = ParameterFormat(parameter_type_list[i])
            except:
                raise ResolverError(location_info,"Parameter type" + parameter_type_list[i] + " is not supported. Available parameter types are " + str(ParameterFormat.get_list_of_types()) + ".")
               
            
            param_value = param[1]
            if param[0] is not None:
                param_names_given  = True
            elif param_names_given is True:
                raise ResolverError(location_info,"All arguments need to be given either with a name or with the value only. A mix is not allowed.")

            if param_names_given is True:
                index = -1
                for param_name , j in zip(parameter_name_list,range(len(parameter_name_list))):
                    if param_name == param[0]:
                        index = j    
                        break
                if index == -1:
                    raise ResolverError(location_info,"The parameter <" + param[0] + "> is not known in this context. Did you want to use <" + parameter_name_list[i] + "> instead?")

            else:
                index = i
            
            if param_value_set[index] is True:
                raise ResolverError(location_info,"The parameter <" + param[0] + "> has been stated more than once.")
            else:
                param_value_set[index] = True
            
           

            try:
                expression = self.resolve(param_value,  resolved_parameter_type , parameter_event_reference_allowed)       
            except AttributeError:
                raise ResolverError(location_info,"Unknown value reference detected in parameter " + parameter_name_list[index] +".")
            if isinstance(expression,FunctionExpression):              
                resolved_expression = self.serialize_operations(expression) 
            else:
                try:
                    resolved_expression = self.__validate_parameter_type(expression, parameter_type_list[index])  
                except:
                    raise ResolverError(location_info,"Expression <" + str(param_value) + "> does not look like a valid expression of type " + parameter_type_list[index] +".")

            resolved_parameter = ResolvedParameter(parameter_name_list[index], resolved_expression, resolved_parameter_type, location_info)

            resolved_params[index] = resolved_parameter

 
        return resolved_params                                                                    

    def resolve_functional_expression(self,param_value): 
        resolved_expression = self.resolve(param_value, ParameterFormat("FLOAT"))
                          
        if isinstance(resolved_expression,FunctionExpression) or isinstance(resolved_expression,ParsedVariableInExpression):
            return SerializedFunctionExpression(self.serialize_operations(resolved_expression))
        
        resolved_expression = self.resolve(param_value,ParameterFormat("FLOAT"))
        
        return resolved_expression
     
    # ToDo:     
    def resolve_connection_list(self,connection_values,location_info):
        """ Resolves arguments, i.e. replaces symbolic information, resolves symbolic arguments for pinnings
        Input:
            pinning arguments
            
         Returns:
             resolved pinning information """ 
        if (connection_values == None):
            return None


        resolved_connections = []

        # calculate the values:        
        for param in connection_values:

            if isinstance(param[1], ParsedVariableInExpression):
                value = self.resolve_alias(param[1].name)
            else:
                value = self.resolve_alias(param[1]) # Workaround            
            
            resolved_connections.append(value)            

        return resolved_connections
  
    def __validate_parameter_type(self,value,requested_type):
        
        
        parameter_key = ParameterFormat(requested_type).get_key()
        
        if (parameter_key == ParameterFormat("IPV4_ADDRESS").get_key()):
            # additional check needed
            return value       
        elif (parameter_key == ParameterFormat("FLOAT").get_key()):
            return value
        elif (parameter_key == ParameterFormat("BOOL").get_key()):
            if value != 0 and value != 1:               
                raise ResolverError(None,"Unknown parameter value for type BOOL. Please choose either 'true' or 'false', but not:"  + value + ".")        
            return value
        elif (parameter_key == ParameterFormat("UINT64").get_key()):
            boundary_value = 2**64
        elif (parameter_key == ParameterFormat("UINT32").get_key()):
            boundary_value = 2**32
        elif (parameter_key == ParameterFormat("UINT16").get_key()):
            boundary_value = 2**16
        elif (parameter_key == ParameterFormat("UINT8").get_key()):
            boundary_value =  2**8
        elif (parameter_key == ParameterFormat("INT64").get_key()):
            boundary_value = 2**63-1
        elif (parameter_key == ParameterFormat("INT32").get_key()):
            boundary_value = 2**31-1
        elif (parameter_key == ParameterFormat("INT16").get_key()):
            boundary_value = 2**15-1
        elif (parameter_key == ParameterFormat("INT8").get_key()):
            boundary_value =  2**7-1

        elif (parameter_key == ParameterFormat("CCAN_ADDRESS").get_key()):
            boundary_value = 2**16
        elif parameter_key == ParameterFormat("CONNECTION").get_key():
            return value
        elif (parameter_key == ParameterFormat("NAME").get_key()):
            return value
        elif (parameter_key == ParameterFormat("STRING").get_key()):
            return value             
        elif (parameter_key == ParameterFormat("DEVICE").get_key()):
            return value              
        else:
            # should not be reached:
            raise ResolverError(None,"Unknown parameter type <" + requested_type + ">  .. refused to check.")      

        if (int(value) >=  boundary_value):
            raise ResolverError(None,"Value " + value + " is to high. Allowed is " + str( 2**32-1)+".")
        else:
            validated_value = int(value)
        
        return validated_value
        

    @staticmethod
    def validate_parameter_types(lists,location_info):
        list_of_parameter_names = lists[0]
        list_of_requested_types = lists[1]
        
        for format in list_of_requested_types:
            try:
                test = ParameterFormat(format)                
            except KeyError: 
                raise ResolverError(location_info,"Parameter format <" + format + "> is not supported.")
        
