import sys
from typing import Any

import requests
from jsonrpcclient.requests import request
from jsonrpcclient.responses import Error, Ok, parse
from trade_flow.commons import logging
from trade_flow.flow.server import TRADE_FLOW_SERVER_PORT

BASE_URL = "http://127.0.0.1"

class JSONRPCException(Exception):
    def __init__(self, code, message):
        try:
            errmsg = f"{code} {message}"
        except (KeyError, TypeError):
            errmsg = ""
        super().__init__(errmsg)


def rpc_call(rpc_method, params: dict[str, Any] | tuple[Any, ...] | None):
    payload = request(rpc_method, params)
    url = f"{BASE_URL}:{TRADE_FLOW_SERVER_PORT}/api"
    try:
        response = requests.post(url, json=payload)
    except ConnectionRefusedError as e:
        print(f"Error connecting to {url}. Is the server running and using matching API URL?")
        logging.debug(e)
        return
    match parse(response.json()):
        case Ok(result, _):
            return result
        case Error(code, message, _, _):
            print(f"{code}: {message}")
            sys.exit(1)
            # raise JSONRPCException(code, message)
