import os
import ftplib
import socket
import logging
from pathlib import Path

from api.base.CCAN_Error import CCAN_Error
from api.base.CCAN_Error import CCAN_ErrorCode
# https://www.digitalocean.com/community/tutorials/how-to-set-up-vsftpd-for-a-user-s-directory-on-ubuntu-16-04

_LOGGER = logging.getLogger(__name__)

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
            self._automation_filename = self._production_settings["FTP_SERVER"][
                "TEMPORARY_AUTOMATION_FILE"
            ]
        except KeyError:
            raise CCAN_Error(
                CCAN_ErrorCode.CONFIGURATION_ERROR,
                "FTP Settings are incomplete. Please provide 'IP_ADDRESS', 'LOGIN','PASSWORD' and 'TEMPORARY_AUTOMATION_FILENAME'.",
            )

        if self._automation_filename[0] != os.sep:
            self._automation_filename = (
                Path(os.environ["CCAN"]) / self._automation_filename
            )

        if not Path.is_dir(self._automation_filename.parent):
            raise CCAN_Error(
                CCAN_ErrorCode.CONFIGURATION_ERROR,
                f"Check configuration for TEMPORARY_AUTOMATION_FILE. The resulting path {self._automation_filename.parent} is not valid",
            )
        self._automation_filename = str(self._automation_filename)

        # check connection:
        try:
            session = ftplib.FTP(self._ip_address)
        except socket.gaierror:
            raise CCAN_Error(
                CCAN_ErrorCode.CONFIGURATION_ERROR,
                f"FTP server address '{self._ip_address}' is not valid",
            )

        try:
            session.login(self._login, self._password)
        except ftplib.error_perm:
            raise CCAN_Error(
                CCAN_ErrorCode.CONFIGURATION_ERROR,
                f"FTP server credentials login '{self._login}' or password '{self._password}' are not correct.",
            )
        session.quit()
        self.valid = True

    def push_to_ftp_server(self, my_pkl_file_name: str):
        if not self.valid:
            return

        with open(my_pkl_file_name, mode='rb') as file: # b is important -> binary
            pkl_content = file.read()

        my_ftp_pkl_file_name = os.path.basename(my_pkl_file_name)
       
        session = ftplib.FTP(self._ip_address)
        session.login(self._login, self._password)
        session.cwd("files")
        session.storbinary("STOR " + my_ftp_pkl_file_name + ".pkl", pkl_content)
        session.quit()


    def pull_from_ftp_server(self, my_pkl_file_name):
        _LOGGER.warning("FTP: pull from server", self.valid)
        if not self.valid:
            return
        session = ftplib.FTP(self._ip_address)
        session.login(self._login, self._password)
        session.cwd("files")
        self._temp_file = open(self._automation_filename, "wb")
        try:
            session.retrbinary(f"RETR {my_pkl_file_name}.pkl", self.__callback)
        except ftplib.error_perm:
            _LOGGER.error("FTP file %spkl not found",my_pkl_file_name)
            raise FileNotFoundError
        session.quit()
        self._temp_file.close()
        return self._automation_filename

    def __callback(self, my_data):
        self._temp_file.write(my_data)
