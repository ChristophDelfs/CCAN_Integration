from src.PyCCAN_ConvertBinary import SequenceExtractor, SequenceCreator
from src.resolver.Definitions import Colors, NoColors
from src.resolver.ResolverElements import ParameterFormat


class ParameterIterator:    
        def __init__(self,dimensions,names, values, types):
            self.__dim = dimensions
            self.__values = values
            self.__names = names
            self.__types = types        
            self.__current = -1  
            
        def __next__(self):
            self.__current += 1
            if self.__current < len(self.__dim):
                return  self.__dim[self.__current], self.__names[self.__current], self.__values[self.__current], self.__types[self.__current]
            raise StopIteration


class Parameters:
    def __init__(self, *my_input):
        self.__values = []
        color = Colors
        self.__seq = SequenceCreator()

        if len(my_input) == 0:
            return

        my_values = my_input[0]
        my_parameter_name_list = my_input[1]
        my_parameter_type_list = my_input[2]
        my_parameter_dimension_list = None if len(my_input) < 4 else my_input[3]
        my_type_func_list = None if len(my_input) < 5 else my_input[4]

        if len(my_parameter_name_list) != len(my_parameter_type_list):
            raise TypeError

        self.__names = my_parameter_name_list
        self.__types = my_parameter_type_list
        self.__value_types = my_parameter_type_list
        self.__typed_func = (
            my_type_func_list
            if my_type_func_list is not None
            else [None] * len(self.__names)
        )
        self.__dim = (
            my_parameter_dimension_list
            if my_parameter_dimension_list is not None
            else ["Scalar"] * len(self.__names)
        )

        if not isinstance(my_values, SequenceExtractor):
            return self.__init_from_key_value_pairs(my_values, self.__dim)

        self.__seq = my_values

        last_value = None

        self.__value_types = []

        for param_type, param_typed_func, param_dim in zip(
            self.__types, self.__typed_func, self.__dim
        ):
            if not isinstance(param_type, str):
                function = param_type
                param_type = function(last_value)

            if param_type == "UINT64":
                func = my_values.convertback64
            elif param_type == "UINT32":
                func = my_values.convertback32
            elif param_type == "UINT16":
                func = my_values.convertback16
            elif param_type == "UINT8":
                func = my_values.convertback8
            elif param_type == "BOOL":
                func = my_values.convertback_bool
            elif param_type == "FLOAT":
                func = my_values.convertback_float
            elif param_type == "STRING":
                func = my_values.convertback_string
            else:
                print(
                    "Parameter type " + str(param_type) + " is not supported right now."
                )
                raise KeyError

            if param_dim == "Vector":
                num = my_values.convertback16()
                value = []
                # last_value = None
                for i in range(num):
                    # if param_type == 'TYPED_VALUE':
                    #    result = func(last_value)
                    # else:
                    result = func()
                    value.append(result)
                    last_value = None
            else:
                # if param_type == 'TYPED_VALUE':
                #    # derive param type from data:
                #    param_type = my_values.convertback8()
                #    if (param_type == 0)
                # alue = func(last_value)
                # else:
                value = func()
                last_value = value

            self.__values.append(value)
            self.__value_types.append(param_type)

   
    def get_values(self):
        return self.__values

    def __init_from_key_value_pairs(self, my_key_value_pairs, my_dimension_list):
        # names check:
        only_values = True
        for key_value_pair in my_key_value_pairs:
            if key_value_pair[0] is None and not only_values:
                raise ValueError
            if key_value_pair[0] is not None:
                only_values = False

        self.__seq = SequenceCreator()       
     

        if len(my_key_value_pairs) == 0:
            self.__values = []
            return

        reference_pairs = tuple(zip(*(self.__names, self.__types)))
        key_value_pairs = my_key_value_pairs

        if len(reference_pairs) != len(key_value_pairs):
            raise ValueError

        if not only_values and len(key_value_pairs) > 1:
            # reference_pairs = sorted( reference_pairs, key=lambda tup: tup[0])
            key_value_pairs = sorted(
                key_value_pairs, key=lambda tup: self.__names.index(tup[0])
            )

        # typed function?
        last_value = None
        self.__value_types = []
        for reference_pair, key_value_pair, param_dimension in zip(
            reference_pairs, key_value_pairs, my_dimension_list
        ):
            param_type = reference_pair[1]
            param_value = key_value_pair[1]



            if param_dimension == "Vector":
                self.__values.append(len(param_value))
                self.__seq.convert16(len(param_value))               
                for value in param_value:
                    value , value_type = self.__convert_from_value(param_type, value, last_value)
            else:              
                value, value_type = self.__convert_from_value(param_type, param_value, last_value)
                last_value = param_value

            self.__values.append(value)   
            self.__value_types.append(value_type)

    def __convert_from_value(self, my_param_type, my_param_value, my_last_value):
        if not isinstance(my_param_type, str):
            function = my_param_type
            my_param_type = function(my_last_value)
        
        if my_param_type == "BOOL":
            if my_param_value.lower() == "true":
                value = True
            elif my_param_value.lower() == "false":
                value = False
            else:
                raise ValueError
            self.__seq.convert_bool(my_param_value)

        elif my_param_type == "UINT8":
            value = int(my_param_value)
            self.__seq.convert8(my_param_value)
        elif my_param_type == "UINT16":
            value =int(my_param_value)
            self.__seq.convert16(my_param_value)
        elif my_param_type == "UINT32":
            value = int(my_param_value)
            self.__seq.convert32(my_param_value)
        elif my_param_type == "UINT64":
            value = int(my_param_value)
            self.__seq.convert64(my_param_value)
        elif my_param_type == "FLOAT":
            value = float(my_param_value)
            self.__seq.convert_float(my_param_value)
        elif my_param_type == "STRING":
            value = str(my_param_value)
            self.__seq.convert_string(my_param_value)
        else:
            raise TypeError      
        return value, my_param_type

    def get_sequence(self):
        return self.__seq.get_sequence()

    def __eq__(self, my_other):
        if my_other is None:
            if self.__values == []:
                return True
            else:
                return False

        if isinstance(my_other, Parameters):
            if self.__values != [] and my_other.__values != []:
                return self.__values == my_other.__values
        return True

    def get_as_string(self, colors):
        result = "("

        if len(self.__values) > 0:
            for param_value, param_name, param_dim in zip(
                self.__values, self.__names, self.__dim
            ):
                result += colors.BLUE + param_name + colors.END + "= "
                if isinstance(param_value, float):
                    result += "{:6.4f}".format(param_value)
                else:
                    result += str(param_value)
                result += ", "
            result = result[:- 2]
        result += ")"
        return result


    ## iterator stuff:

    def __iter__(self):
        return ParameterIterator(self.__dim,self.__names, self.__values, self.__value_types)
      

   