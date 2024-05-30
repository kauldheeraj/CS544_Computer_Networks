
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Union
import time

MSG_TYPE_DATA = 0x00
MSG_TYPE_ACK  = 0x01
MSG_TYPE_DATA_ACK = MSG_TYPE_DATA | MSG_TYPE_ACK

# Define ContentType enumeration
class ContentType(Enum):
    CONTENT_USER_ID_PASSKEY = 1
    CONTENT_MESSAGE = 2
    CONTENT_ERROR_MSG = 3

# Define the UserIdPasskey class
@dataclass
class UserIdPasskey:
    user_id: str
    pass_key: str

# Define the Message class
@dataclass
class Message:
    message_text: str

# Define the ErrorMsg class
@dataclass
class ErrorMsg:
    error_code: int
    error_message: str


# Define the Content class with specific subclasses
@dataclass
class Content:
    user_id_passkey: UserIdPasskey = None
    message: Message = None
    err_msg: ErrorMsg = None

# Define the ChatMessage class
@dataclass
class ChatMessage:
    type: int
    sender: str
    content_message: Content
    content_type: ContentType
    sent_time: float = field(default_factory=time.time)

class Datagram:
    def __init__(self, content_type: int,  sender: str, content: str, sz:int = 0):
        self.content_type = content_type
        self.sender = sender
        self.content = content
        self.sz = sz
        # self.sz = len(self.msg)
        sent_time: float = field(default_factory=time.time)

    # def __init__(self, mtype: int, msg: str, sz:int = 0):
    #     self.mtype = mtype
    #     self.msg = msg
    #     self.sz = len(self.msg)

    def to_json(self):
        return json.dumps(self.__dict__)    
    
    @staticmethod
    def from_json(json_str):
        return Datagram(**json.loads(json_str))
    
    def to_bytes(self):
        return json.dumps(self.__dict__).encode('utf-8')
    
    @staticmethod
    def from_bytes(json_bytes):
        return Datagram(**json.loads(json_bytes.decode('utf-8')))    