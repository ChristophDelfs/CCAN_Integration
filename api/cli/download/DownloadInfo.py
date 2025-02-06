from pathlib import Path
from api.cli.CliError import CliError, CliErrorCode
from api.cli.download.Downloads import DownloadImage, DownloadConfiguration

class DownloadInfo():
    def __init__(self):
        pass
       
    @classmethod
    def get_result(cls,my_filename):
                  
        result = DownloadImage(my_filename)
        if  result.is_valid() is True:
            return result
        
        result = DownloadConfiguration(my_filename)
        if  result.is_valid() is True:
            return result
     
        raise CliError(CliErrorCode.ILLEGAL_ARGUMENT,"File is no valid image or configuration file.")
            
