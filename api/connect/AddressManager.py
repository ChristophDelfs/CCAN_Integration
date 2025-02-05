import logging

class AddressManager:
    """AddressManager handles a set of available CCAN addresses.
       User may allocate or free allocated addresses.
    """
    __START = 1024
    __END   = __START + 32
    
    def __init__(self,start= __START,end= __END):
        """ Constructor takes start and end address of address space which the AdressManager shall use.
            start : int
                start address of allowed address range
            end   : int
                end address of allowed address range
        """
        
        if end <= start:
            raise ValueError
        
        self.__used = [ False ]*(end-start)
        self.__start = start
        
    def allocate(self):
        """ allocate next available free address
            If no free address is available, an IndexError is raised.
        """  
        
        try:
            raw_address = self.__used.index(False)
        except ValueError:
            raise IndexError
        self.__used[raw_address] = True
        return self.__start + raw_address
    
    def is_allocated_address(self, my_address):
        return (my_address >= AddressManager.__START and my_address <= AddressManager.__END)
    
    def free(self, address):
        """ free address which has been allocated beforehand
            If an address is provided which has not been allocated beforehand, an IndexError is thrown."""
        if self.__used[address - self.__start] == False:
            ''' address has not been used'''
            logging.warn("Adress "  +str(address) + " has not been allocated and cannot be freed.")
                   
        self.__used[address - self.__start] = False
    
    