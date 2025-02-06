import json
import jsonschema
from pathlib import Path
import os


class PlatformConfiguration:
    def __init__(self):
        self.__ccan_json_instance_file = (
            Path(PlatformConfiguration.CCAN_PATH()) / "production" / "CCAN.json"
        )
        self.__ccan_json_schema_file = (
            Path(PlatformConfiguration.CCAN_PATH()) / "production" / "CCAN_schema.json"
        )
        self.load()
      

    @staticmethod
    def CCAN_PATH() -> str:
        try:
            ccan_path = os.environ["CCAN"]
        except KeyError:
            current_path = str(Path(__file__).parent)
            index = current_path.find("CCAN")
            ccan_path = str(Path(current_path[:index]) / "CCAN")
            os.environ["CCAN"] = ccan_path
        return ccan_path

    @staticmethod
    def DEFAULT_DEFINITIONS_FILENAME():
        return str(
            Path(PlatformConfiguration.CCAN_PATH())
            / "gen"
            / "ccan_generated_definitions"
        )

    def load(self):
        schema = {                                                                                                                                                                        
             "$schema": "http://json-schema.org/draft-04/schema",                                                                                                                         
             "type": "integer",                                                                                                                                                            
        }                                                                                                                                                                                 
        jsonschema.validators.validator_for(schema)  


        json_instance = json.loads(
            self.__ccan_json_instance_file.read_text(encoding="UTF-8")
        )
        json_schema = json.loads(
            self.__ccan_json_schema_file.read_text(encoding="UTF-8")
        )
        jsonschema.validate(instance=json_instance, schema=json_schema)

        # erweitern: dict_1.update(dict_2)
        # https://favtutor.com/blogs/merge-dictionaries-python

        self.__defaults = json_instance
        # add file:
        self.__defaults["PlatformConfigurationFile"] = self.__ccan_json_instance_file

    def get(self):
        return self.__defaults
