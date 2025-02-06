import os
from pathlib import Path

def include_path_defaults():
    basedir = os.getenv('CCAN')
    return [ os.path.join(basedir, "PyCCAN","defaults"),  
             os.path.join(os.getcwd(),basedir, "PyCCAN","defaults","templates"), 
             os.path.join(os.getcwd(),basedir, "PyCCAN","defaults","HA_Entities"),              
            os.path.join(os.getcwd(),basedir, "PyCCAN","defaults","HA_Devices"),   
             str(Path.cwd())]

def create_filename(basename, filename, file_content, file_type):      
    filename = basename + "_" + filename + "_" + file_content + "." + file_type
    return filename