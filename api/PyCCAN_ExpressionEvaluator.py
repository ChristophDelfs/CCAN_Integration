from api.resolver.ResolverError import ResolverError
from lark import Lark, InlineTransformer
from api.resolver.Definitions import ParamListInfo, CompilerMode,ParameterSet

from api.resolver.ResolverError import ResolverError
from collections import namedtuple
from enum import Enum
from numbers import Number

import logging
#from lark import logger



Variable    = namedtuple("variable", "value source type")

class VARIABLE_SOURCE(Enum):
    CONSTANT = 0
    STATUS   = 1
    EVENT    = 2
    FUNCTION = 3

class EventVariable():
    def __init__(self,value):
        self.__name = value
        
    def __str__(self):
        return "EVENT::" + self.__name
        

class FunctionExpression():    
    def __init__(self,operand1,operand2,operator):
        self.__operator = operator
        self.__operand1 = operand1
        self.__operand2 = operand2

    def operator(self):
        return self.__operator
    def operand1(self):
        return self.__operand1
    def operand2(self):
        return self.__operand2
    
    def __str__(self):
        if self.__operator is None:
            return str(self.__operand1)
        
        return str(self.__operand1) + str(self.__operator) + str(self.__operand2)
        

class Function():
    def __init__(self,name,argument_list):
        self.__name = name
        self.__argument_list = argument_list
    def name(self):
        return self.__operator
    def argument_list(self):
        return self.__argument_list
 
    def __str__(self):
        result = self.__name + "("
        for i in range(len(self.__argument_list)):
            result = result + str(self.__argument_list[i])
        result = result + ")"        
        return result
    
class ExpressionEvaluator(InlineTransformer):
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
         
    ?function_expression: event_variable
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

        ''', parser = "earley", debug = False)
    
    def __init__(self):
    
        self.__alias_list = {}
        #__dev_current_key          = 100

        #self.load_device_table("dummy_file")
        pass

    def argument(self,matches):
        result = self.simplify(matches)
        return result

    def string_argument(self,matches):
        result = self.simplify(matches)
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
        try:
            value = self.__alias_list[alias]
        except KeyError:
            value = alias
            #for key in self.__alias_list:
            #    new_value = value.replace(key,str(self.__alias_list[key]))
            #    if new_value != value:
            #        value = new_value
            #        break
        #pass # raise ResolverError(None,"Symbol <" + alias + "> has not been defined (?)")       
        
        return value

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

    def event_name(self,value):
        event = Variable(value=str(value),source = VARIABLE_SOURCE.EVENT,type= None)
        return event
    
    def instance_variable(self,device,variable):
        # instance can be_
        #   a) device status variable
        #   b) TEMPLATE alias
        event = Variable(value=str(device)+"::"+str(variable),source = VARIABLE_SOURCE.STATUS,type= None)
        return event

    def function(self,name,argument_list):
        function = Function(name,argument_list)
        result = Variable(value= str(function),source = VARIABLE_SOURCE.FUNCTION,type= None)
        return result
    
    def __constant_to_variable(self,value):
        return Variable(value= value,source = VARIABLE_SOURCE.CONSTANT, type = type(value));     
        
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
            except ValueError:
                self.__alias_list[param] = self.get_string(value)
            
            
            
            return

        raise ResolverError(None,"Symbol <" + param + "> has been defined already.")
        return

    def resolve(self,expression_text):
        resolved_parameter = self.transform(self.__expression_parser.parse(expression_text))
        return resolved_parameter 

    def simplify(self,expression):
        """ simplifies the given expression as far as possible
            The given expression is simplified with the following goals:
            
            1)  return a single value
            2)  return a function expression with first operand being a number
            3)  return a function expression with both operands being not a number
        """
        if isinstance(expression,FunctionExpression) is False:
            return expression

        op1 = expression.operand1()
        op2 = expression.operand2()
                
        # expression is a function expression:
        if isinstance(op1,FunctionExpression):
            op1 = self.simplify(op1) 
        if isinstance(op2,FunctionExpression):
            op2 = self.simplify(op2)        


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
        
        if operator =='/' and offered_operator == '/':
            return (operand,'/')
        else:
            return (1/operand,'*')
        if operator =='+' and offered_operator == '-':
            return (-operand,'-')
        else:
            return (operand,operator)
        
        if operator =='-' and offered_operator == '-':
            return (operand,'-')
        else:
            return(-operand,'+')


 

    def __is_similar(self,operator1,operator2):
        l1 = [ '*','/']
        l2 = ['+','-']
        if operator1 in l1 and operator2 in l1:
            return True
        if operator1 in l2 and operator2 in l2:
            return True
        return False
    
    def __calculate(self,operand1,operand2,operator):
        result = None
        if operator == "*":
            result = operand1 * operand2
        if operator == "/":
            result = operand1 / operand2            
        if operator == "+":
            result = operand1 + operand2
        if operator == "-":
            result = operand1 - operand2
                                    
        return result
    
    
    def serialize(self, expression):
        result_list = []
        if isinstance(expression,Number) or isinstance(expression,Variable) or isinstance(expression,str):
            result_list.append(expression)
            return result_list
        
        if expression.operator() == None:
            result_list.extend(self.serialize(expression.operand1()))    
        else:
            result_list.extend(expression.operator())
            result_list.extend(self.serialize(expression.operand1()))
            result_list.extend(self.serialize(expression.operand2()))
        
        return result_list     
 
    def functional(self,*matches):
        if len(matches) == 1:
            return FunctionExpression(operator = None, operand1 = matches[0], operand2 = None)
        return FunctionExpression(operator = matches[1], operand1 = matches[0], operand2 = matches[2])
    


#logger.setLevel(logging.DEBUG)
        
text_list = []
text_list.append('"hcan-protocol"') 
text_list.append("sin(3+stop) - 20 + str(stop-2*stop-EVENT::blabla)") 
text_list.append("20*stop - EVENT::mein_name*start*stop*EVENT::blabla * stop - start") 
text_list.append("0x10 + 2*start -stop")
text_list.append("0x10 + 2*start -stop/(2*start+stop*stop)")
text_list.append("-EVENT::mein_name")
text_list.append("(0x10 + 2)*start -stop")
text_list.append("EVENT::mein_name - EVENT::neuer_name")
text_list.append("EVENT::mein_name * EVENT::neuer_name")
text_list.append("EVENT::super - EVENT::mein_name * EVENT::neuer_name")
text_list.append("EVENT::mein_name*20")
text_list.append("EVENT::mein_name* stop")
text_list.append("20 - EVENT::mein_name* stop")
text_list.append("20*stop - stop*EVENT::mein_name")

text_list.append("20*stop - EVENT::mein_name")
text_list.append("20*stop - EVENT::mein_name*start")
text_list.append("20*stop - EVENT::mein_name*start - stop*EVENT::blabla")
text_list.append("20*stop - EVENT::mein_name*start*stop*EVENT::blabla")        
text_list.append("20*stop - EVENT::mein_name*start*stop*EVENT::blabla * stop - start") 
text_list.append("Counter1::value") 
text_list.append("-Counter1::value")         
text_list.append("Counter1::value * (EVENT::mein_blabla / stop - 20) *Counter2::value2/ EVENT::param1") 



eval = ExpressionEvaluator()
eval.insert_alias("start",10)
eval.insert_alias("stop",20)

t = None
for i,text in zip(range(len(text_list)),text_list):
    t = eval.resolve(text)
    s = eval.serialize(t)

    print(str(i+1)+": "+  str(t))
    
#print(t)
