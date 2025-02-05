import os
import ftplib
import socket

from src.base.CCAN_Error import CCAN_Error
from src.base.CCAN_Error import CCAN_ErrorCode
#https://www.digitalocean.com/community/tutorials/how-to-set-up-vsftpd-for-a-user-s-directory-on-ubuntu-16-04


class FTPFileServices:
    def __init__(self, my_platform_configuration_settings):    
        self._production_settings = my_platform_configuration_settings

        self.valid = False        
        try:
            self._production_settings["FTP_SERVER"]
        except KeyError:
            return
        
        try:
            self._ip_address = self._production_settings["FTP_SERVER"]["IP_ADDRESS"]
            self._login = self._production_settings["FTP_SERVER"]["LOGIN"]
            self._password = self._production_settings["FTP_SERVER"]["PASSWORD"]
            self._automation_filename = self._production_settings["FTP_SERVER"]["TEMPORARY_AUTOMATION_FILE"]
        except KeyError:
            raise CCAN_Error(CCAN_ErrorCode.CONFIGURATION_ERROR,"FTP Settings are incomplete. Please provide 'IP_ADDRESS', 'LOGIN','PASSWORD' and 'TEMPORARY_AUTOMATION_FILENAME'.")
    
        # check connection:
        try:
            session = ftplib.FTP(self._ip_address)
        except socket.gaierror:
            raise CCAN_Error(CCAN_ErrorCode.CONFIGURATION_ERROR,f"FTP server address '{self._ip_address}' is not valid")

        try:
            session.login(self._login,self._password)
        except ftplib.error_perm:
            raise CCAN_Error(CCAN_ErrorCode.CONFIGURATION_ERROR,f"FTP server credentials login '{self._login}' or password '{self._password}' are not correct.")
        session.quit()
        self.valid = True


    def push_to_ftp_server(self, my_pkl_file_name: str, my_pkl_file):      
        if not self.valid:
            return
        fp = open(my_pkl_file + ".pkl", 'rb')

        session = ftplib.FTP(self._ip_address)
        session.login(self._login, self._password)
        session.cwd("files")
        session.storbinary("STOR " + my_pkl_file_name + ".pkl", fp)
        session.quit()

        
    def pull_from_ftp_server(self, my_pkl_file_name):      
        if not self.valid:
            return      
        session = ftplib.FTP(self._ip_address)
        session.login(self._login, self._password)
        session.cwd("files")       
        self._temp_file = open(self._automation_filename,"wb")
        try:
            session.retrbinary(f"RETR {my_pkl_file_name}.pkl", self.__callback)
        except ftplib.error_perm:
            raise FileNotFoundError
        session.quit()
        self._temp_file.close()       
        return self._automation_filename

    def __callback(self, my_data):
        self._temp_file.write(my_data)


