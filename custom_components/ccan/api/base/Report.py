from enum import Enum

class ReportLevel(Enum):
    NONE    = 0
    ERROR   = 1
    WARN    = 2
    VERBOSE = 3   
    DEBUG   = 4

    def __le__(self,other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        raise NotImplementedError
    
    def __lt__(self,other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        raise NotImplementedError
    
    def __eq__(self,other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        raise NotImplementedError
    
    def __gt__(self,other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        raise NotImplementedError
    
    def __ge__(self,other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        raise NotImplementedError
    
    
    
class Report:        
    __Level = [ReportLevel.DEBUG]  # by default, everything gets reported

    def push_level(my_new_level):
        if my_new_level <= Report.__Level[-1]:
            Report.__Level.append(my_new_level)
        else:
            Report.__Level.append(Report.__Level[-1])     
        return
        
    
    def pop_level():
        Report.__Level.pop(-1)


    def print(my_level,my_string, my_rewind_flag = False):
        if my_level <= Report.__Level[-1]:
            if my_rewind_flag == False: 
                print(my_string,end='', flush=True)
            else:
                print(my_string+"\r",end='',flush=True)
