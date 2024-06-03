
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Union
import time

MSG_TYPE_DATA = 0x00
MSG_TYPE_ACK  = 0x01
MSG_TYPE_DATA_ACK = MSG_TYPE_DATA | MSG_TYPE_ACK

# Define ContentType enumeration
class ContentType(Enum):
    CONTENT_CONNECTION_SET_UP = 1
    CONTENT_LOGIN = 2
    CONTENT_MESSAGE = 3
    CONTENT_ERROR_MSG = 4
    CONTENT_LOGOFF = 5

# Define the UserIdPasskey class
@dataclass
class UserIdPasskey:
    user_id: str
    pass_key: str

    def to_bytes(self) -> bytes:
        user_id_bytes = self.user_id.encode('utf-8')[:32].ljust(32, b'\x01')
        pass_key_bytes = self.pass_key.encode('utf-8')[:32].ljust(32, b'\x01')
        return user_id_bytes + pass_key_bytes

    @staticmethod
    def from_bytes(data: bytes) -> 'UserIdPasskey':
        user_id = data[:32].rstrip(b'\x01').decode('utf-8')
        pass_key = data[32:].rstrip(b'\x01').decode('utf-8')
        return UserIdPasskey(user_id=user_id, pass_key=pass_key)
    

# Define the Message class
@dataclass
class Message:
    target_user_id : str
    message_text: str

    def to_bytes(self) -> bytes:
            total_bytes = self.target_user_id.encode('utf-8')[:32].ljust(32, b'\x01')
            total_bytes += self.message_text.encode('utf-8')[:150].ljust(150, b'\x01')
            return total_bytes

    @staticmethod
    def from_bytes(data: bytes) -> 'Message':
        target_user_id = data[:32].rstrip(b'\x01').decode('utf-8')
        message_text = data[32:].rstrip(b'\x01').decode('utf-8')
        return Message(target_user_id=target_user_id, message_text=message_text)

@dataclass
class Acknowledgement:
    ack_message : str

    def to_bytes(self) -> bytes:
        total_bytes = self.ack_message.encode('utf-8')
        return total_bytes

    @staticmethod
    def from_bytes(data: bytes) -> 'Acknowledgement':
        ack_message = data.decode('utf-8')
        return Acknowledgement(ack_message=ack_message)
    
# Define the ErrorMsg class
@dataclass
class ErrorMsg:

    error_message: str

    def to_bytes(self) -> bytes:
        error_message_bytes = self.error_message.encode('utf-8')
        return error_message_bytes
    
    @staticmethod
    def from_bytes(data: bytes) -> 'ErrorMsg':
        error_message = data.decode('utf-8')
        return ErrorMsg(error_message=error_message)
    
# Define the Content class with specific subclasses
@dataclass
class Content:
    user_id_passkey: UserIdPasskey = None
    message: Message = None
    err_msg: ErrorMsg = None

    def to_bytes(self, content_type: ContentType) -> bytes:
        if content_type == ContentType.CONTENT_LOGIN:
            return self.user_id_passkey.to_bytes()
        elif content_type == ContentType.CONTENT_MESSAGE or content_type == ContentType.CONTENT_CONNECTION_SET_UP or content_type == ContentType.CONTENT_LOGOFF:
            return self.message.to_bytes()
        elif content_type == ContentType.CONTENT_ERROR_MSG:
            return self.err_msg.to_bytes()
        else:
            raise ValueError('Unknown content type')

    @staticmethod
    def from_bytes(data: bytes, content_type: ContentType) -> 'Content':
        if content_type == ContentType.CONTENT_LOGIN:
            return Content(user_id_passkey=UserIdPasskey.from_bytes(data))
        elif content_type == ContentType.CONTENT_MESSAGE or content_type == ContentType.CONTENT_CONNECTION_SET_UP or content_type == ContentType.CONTENT_LOGOFF:
            return Content(message=Message.from_bytes(data))
        elif content_type == ContentType.CONTENT_ERROR_MSG:
            return Content(err_msg=ErrorMsg.from_bytes(data))
        else:
            raise ValueError('Unknown content type')


class Datagram:
    def __init__(self, content_type: ContentType,  sender: str, content: Content, sz:int = 0, sent_time:float = 99, ack:str=""):
        self.content_type = content_type
        self.sender = sender
        self.content = content
        self.sz = sz
        self.sent_time = time.time()
        self.ack = ack

    def to_json(self):
        
        return json.dumps(self.__dict__)    
    
    @staticmethod
    def from_json(json_str):
        return Datagram(**json.loads(json_str))
    
    def to_bytes(self):
        total_bytes = self.content_type.value.to_bytes(1, 'big')
        total_bytes =  b'\x00'.join([total_bytes, json.dumps(self.sender).encode('utf-8')])
        total_bytes = b'\x00'.join([total_bytes, self.content.to_bytes(self.content_type)])
        total_bytes = b'\x00'.join([total_bytes, json.dumps(self.sz).encode('utf-8')])
        total_bytes = b'\x00'.join([total_bytes, json.dumps(self.sent_time).encode('utf-8')])
        total_bytes = b'\x00'.join([total_bytes, json.dumps(self.ack).encode('utf-8')])
        return total_bytes
    
    @staticmethod
    def from_bytes(json_bytes):
     
      try :
      # Split the bytes object on the null byte delimiter
        parts = json_bytes.split(b'\x00')
        content_type = ContentType(int.from_bytes(parts[0], 'big'))
        sender = json.loads(parts[1].decode('utf-8'))
        content = Content.from_bytes(parts[2],content_type)
        sz = json.loads(parts[3].decode('utf-8'))
        sent_time = json.loads(parts[4].decode('utf-8'))
        ack = json.loads(parts[5].decode('utf-8'))
        return Datagram(content_type, sender, content, sz, sent_time, ack)
      except Exception :
        print("Exception encountered while converting from_bytes")