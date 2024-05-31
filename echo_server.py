import asyncio
from typing import Coroutine,Dict
import json
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu
from dataclasses import dataclass
from typing import List


async def echo_server_proto(scope:Dict, conn:EchoQuicConnection):
        
        class ServerError(Exception):
              pass

        @dataclass
        class User_Id_Passkey_DB :
              user_id: str
              pass_key : str

        user_id_pass_key : List[User_Id_Passkey_DB] = [
              User_Id_Passkey_DB(user_id='deekay', pass_key='dheeraj'),
              User_Id_Passkey_DB(user_id='ryan', pass_key='reynods'),
              User_Id_Passkey_DB(user_id='jenny', pass_key='jennifer'),
              User_Id_Passkey_DB(user_id='matt', pass_key='mathew'),
        ]
        

        async def authenticate_user(user_id_pass_key:pdu.UserIdPasskey, user_list:List[User_Id_Passkey_DB]):
              input_user_id = user_id_pass_key.user_id
              input_pass_key = user_id_pass_key.pass_key
              for users in user_list:
                  if input_user_id == users.user_id and input_pass_key == users.pass_key :
                        return
              raise  ServerError("User not authenticate. Please try again.") 
        
        message:QuicStreamEvent = await conn.receive()
        
        dgram_in = pdu.Datagram.from_bytes(message.data)

        print("[svr] received message from: ", dgram_in.sender)
        
        if (dgram_in.content_type == pdu.ContentType.CONTENT_LOGIN):
                try :
                        await authenticate_user(dgram_in.content.user_id_passkey, user_id_pass_key)
                        dgram_out = dgram_in         
                except ServerError as e:
                        err_msg = pdu.ErrorMsg(error_message=str(e))
                        dgram_out = pdu.Datagram(pdu.ContentType.CONTENT_ERROR_MSG, dgram_in.sender, pdu.Content(err_msg=err_msg))
        else:
           dgram_out = dgram_in
        
        stream_id = message.stream_id
        
        # dgram_out.mtype |= pdu.MSG_TYPE_DATA_ACK
        # dgram_out.content_type.value |= pdu.MSG_TYPE_DATA_ACK
        # dgram_out.content_type = pdu.ContentType(dgram_out.content_type.value | pdu.MSG_TYPE_DATA_ACK)

        dgram_out.sender = "SVR-ACK: " + str(dgram_out.sender)
        
        # dgram_out.msg = "SVR-ACK: " + dgram_out.msg
        rsp_msg = dgram_out.to_bytes()
        rsp_evnt = QuicStreamEvent(stream_id, rsp_msg, False)
        await conn.send(rsp_evnt)