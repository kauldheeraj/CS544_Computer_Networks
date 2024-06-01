import asyncio
from typing import Coroutine,Dict
import json
from chat_quic import ChatQuicConnection, QuicStreamEvent
import pdu
from dataclasses import dataclass
from typing import List

@dataclass
class Client_Connection :
        connection: ChatQuicConnection
        user : str
        stream_id : int

# all_conns : List[Client_Connection] = []

async def chat_server_proto(scope:Dict, conn:ChatQuicConnection, client_conn_list:List[Client_Connection]) -> List[Client_Connection]:

      # print(len(client_conn_list))
      class ServerError(Exception):
            pass

      @dataclass
      class User_Id_Passkey_DB :
            user_id: str
            pass_key : str

      user_id_pass_key : List[User_Id_Passkey_DB] = [
            User_Id_Passkey_DB(user_id='deekay', pass_key='dheeraj'),
            User_Id_Passkey_DB(user_id='ryan', pass_key='reynolds'),
            User_Id_Passkey_DB(user_id='jenny', pass_key='jennifer'),
            User_Id_Passkey_DB(user_id='matt', pass_key='mathew'),
      ]

      async def authenticate_user(user_id_pass_key:pdu.UserIdPasskey, user_list:List[User_Id_Passkey_DB]):
            input_user_id = user_id_pass_key.user_id
            input_pass_key = user_id_pass_key.pass_key
            for users in user_list:
                  if input_user_id == users.user_id and input_pass_key == users.pass_key :
                        return
            raise  ServerError("User not authenticated. Please try again.") 
      
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
      #   print(stream_id)
      #   print("stream id")
      sender = str(dgram_out.sender)
      dgram_out.sender = "SVR-ACK: " + str(dgram_out.sender)
      rsp_msg = dgram_out.to_bytes()
      rsp_evnt = QuicStreamEvent(stream_id, rsp_msg, False)

      # Logic to store connection
      # local_client_conn_list : List[Client_Connection] = []
      local_client_conn_list = client_conn_list
      is_present = 0
      print("Current number of connections = " + str(len(local_client_conn_list)))
      for conns in client_conn_list:
            if conns.connection.__eq__(conn):
                  print("Connection already found:" + sender + ":" + str(conns.stream_id))   
                  is_present = 1

      if is_present == 0 :
            curr_conn = Client_Connection(conn,sender,stream_id)
            local_client_conn_list.append(curr_conn)
               
      # Logic to store connection

      await conn.send(rsp_evnt)
      return local_client_conn_list