from typing import Optional
from pydantic import BaseModel 


class PingMessage(BaseModel):
    message: str


class ServerTimeResponse(BaseModel):
    timezone: str
    unix_timestamp: int
    server_time: Optional[int] = None