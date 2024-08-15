# from .metatrader5 import *

""" Package implementing the Python API for the MT5 Terminal """

VERSION = {
    'major': 0,
    'minor': 1,
    'micro': 0}


def get_version_string():
    version = '{major}.{minor}.{micro}'.format(**VERSION)
    return version

__version__ = get_version_string()



# Behave like the https://github.com/nautechsystems/nautilus_ibapi/blob/main/pyproject.toml
 
