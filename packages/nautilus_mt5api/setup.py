#from distutils.core import setup
from setuptools import setup
from mt5api import get_version_string
import sys

if sys.version_info < (3,1):
    sys.exit("Only Python 3.1 and greater is supported") 

setup(
    name='mt5api',
    version=get_version_string(),
    packages=['mt5api'],
    url='https://www.mql5.com/en/docs/python_metatrader5',
    license='MT5 API Non-Commercial License or the MT5 API Commercial License',
    author='Fortesense Labs',
    author_email='fortesenselabs@gmail.com',
    description='Python MT5 API'
)