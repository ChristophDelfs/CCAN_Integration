class ResolverError(BaseException): 
    __level = { "ERROR","WARNING"}
    
    def __init__(self,location,text,my_level="ERROR"):
        self.__text = text
        self.__location = location
        if my_level in ResolverError.__level:
            self.__level = my_level
        else:
            raise ValueError    
    
    def get_error_text(self):
        return self.__text
    
    def get_location(self):
        return self.__location
    
    def get_line(self):
        return self.__location.line
    
    def get_column(self):
        return self.__location.column    

    def is_warning(self):
        return (self.__level == "WARNING")
    
    def __str__(self):
        if self.__location  != None:
            line = self.__get_file_context(self.__location.file,self.__location.line)     

            marker_line = line[0:self.__location.column-1]
            marker = ''
            for char in marker_line:
                marker += char if char.isspace() else " "
            marker += "^"
            result = self.__location.file + ":" +str(self.__location.line)+":" +str(self.__location.column) + "\n" + line + marker + "\n" + ">> " + self.__text
        else:
            result = "Unknown location : " + self.__text
        return result

    def __get_file_context(self,file,line_no):
        with open(file) as file:
            #Iterate through lines
            for i, line in enumerate(file):
                if i== line_no-1:
                    return line 
        return "<no text available (?)"


