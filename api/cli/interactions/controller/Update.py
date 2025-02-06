import os
import time
import math

from api.cli.interactions.Interaction import Interaction
from api.cli.download.DownloadRobot import DownloadRobot
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.base.Report import Report, ReportLevel
from api.cli.interactions.controller.Reset import Reset

class Update(Interaction): 
    def __init__(self, my_connector, my_retries, my_filename, my_enforce_flag):    
        super().__init__(my_connector, my_retries)       
        self._connector = my_connector  
        self._filename = my_filename
        self._enforce_flag = my_enforce_flag
  
    def do(self):
        
        download = DownloadRobot(self._connector, self._filename, enforce_flag = self._enforce_flag, lock_flag = False)
        download.do()

  
  


   