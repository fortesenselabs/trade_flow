import json
import time
from metatrader import client
from metatrader.request import RequestBuilder


# Utility function
def current_timestamp():
    return int(time.time() * 1000)


# PingService
class PingService:
    def __init__(self, client: client.Client):
        self.client = client

    def do(self, opts=None):
        request = RequestBuilder("GET", "/api/ping")
        data = self.client.call_api(request, opts)
        return json.loads(data)


# ServerTimeService
class ServerTimeService:
    def __init__(self, client: client.Client):
        self.client = client

    def do(self, opts=None):
        request = RequestBuilder("GET", "/api/time")
        data = self.client.call_api(request, opts)
        return data["server_time"]


# SetServerTimeService
class SetServerTimeService:
    def __init__(self, client: client.Client):
        self.client = client

    def do(self, opts=None):
        server_time = self.client.new_server_time_service().do()
        time_offset = current_timestamp() - server_time
        self.client.time_offset = time_offset
        return time_offset


# ServerSystemStatusService
class ServerSystemStatusService:
    def __init__(self, client: client.Client):
        self.client = client

    def do(self, opts=None):
        request = RequestBuilder("GET", "/api/system/status")
        data = self.client.call_api(request, opts)
        return json.loads(data)
