"""
This module has tools for implementing the rpyc messaging.
"""

import struct
import logging
import sys

from mt5api.common import UNSET_INTEGER, UNSET_DOUBLE, DOUBLE_INFINITY, INFINITY_STR
from mt5api.utils import ClientException
from mt5api.utils import isAsciiPrintable
from mt5api.errors import INVALID_SYMBOL

logger = logging.getLogger(__name__)


def make_msg(method: str, *args, **kwargs) -> str:
    """Compose message with optional args and kwargs."""
    
    # Convert args to a string if there are any
    args_str = ', '.join(repr(arg) for arg in args)
    
    # Convert kwargs to a string if there are any
    kwargs_str = ', '.join(f'{key}={repr(value)}' for key, value in kwargs.items())
    
    # Combine args_str and kwargs_str
    if args_str and kwargs_str:
        combined_str = f'{args_str}, {kwargs_str}'
    else:
        combined_str = args_str or kwargs_str
    
    # Format the final message
    if combined_str:
        msg = f'mt5.{method}({combined_str})'
    else:
        msg = f'mt5.{method}()'
    
    return msg


def make_field(val) -> str:
    """ adds the NULL string terminator """
    if val is None:
        raise ValueError("Cannot send None to TWS")

    # if string is not empty and contains invalid symbols
    if val is not None and type(val) == str and val and not isAsciiPrintable(val):
        raise ClientException(INVALID_SYMBOL.code(), INVALID_SYMBOL.msg(), val.encode(sys.stdout.encoding, errors='ignore').decode(sys.stdout.encoding))

    # bool type is encoded as int
    if type(val) is bool:
        val = int(val)

    field = str(val) + '\0'
    return field


def make_field_handle_empty(val) -> str:
    if val is None:
        raise ValueError("Cannot send None to TWS")

    if UNSET_INTEGER == val or UNSET_DOUBLE == val:
        val = ""
        
    if DOUBLE_INFINITY == val:
        val = INFINITY_STR

    return make_field(val)


def read_msg(buf: bytes) -> tuple:
    """ first the size prefix and then the corresponding msg payload """

    if len(buf) < 4:
        return (0, "", buf)
    size = struct.unpack("!I", buf[0:4])[0]
    logger.debug("read_msg: size: %d", size)
    if len(buf) - 4 >= size:
        text = struct.unpack("!%ds" % size, buf[4:4+size])[0]
        return (size, text, buf[4+size:])
    else:
        return (size, "", buf)


def read_fields(buf:bytes) -> tuple:
    if isinstance(buf, str):
        buf = buf.encode()

    """ msg payload is made of fields terminated/separated by NULL chars """
    fields = buf.split(b"\0")

    return tuple(fields[0:-1])   #last one is empty; this may slow dow things though, TODO


