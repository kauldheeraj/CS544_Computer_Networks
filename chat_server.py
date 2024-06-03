import asyncio
from typing import Coroutine,Dict
import json
from chat_quic import ChatQuicConnection, QuicStreamEvent
import pdu
from dataclasses import dataclass
from typing import List

#Class to maintain live client connections
@dataclass
class Client_Connection :
        connection: ChatQuicConnection
        user : str
        stream_id : int
        original_usr : str


#Server Protocol 
async def chat_server_proto(scope:Dict, conn:ChatQuicConnection, client_conn_list:List[Client_Connection]) -> List[Client_Connection]:
      local_client_conn_list = client_conn_list
      try:
            # print(len(client_conn_list))
            class ServerError(Exception):
                  pass

            @dataclass
            class User_Id_Passkey_DB :
                  user_id: str
                  pass_key : str

            #List of users hardcoded
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
            
            async def raise_custom_error(err_str:str, dgram_in, stream_id):
                  e = ServerError(err_str) 
                  err_msg = pdu.ErrorMsg(error_message=str(e))
                  dgram_out = pdu.Datagram(pdu.ContentType.CONTENT_ERROR_MSG, dgram_in.sender, pdu.Content(err_msg=err_msg),"")    
                  msg_send_rsp_msg = dgram_out.to_bytes()
                  msg_send_rsp_evnt = QuicStreamEvent(stream_id, msg_send_rsp_msg, False)
                  await conn.send(msg_send_rsp_evnt)
                  
            ack_str = ""
            message:QuicStreamEvent = await conn.receive()
            
            dgram_in = pdu.Datagram.from_bytes(message.data)
            print("[svr] received message from: ", dgram_in.sender)
            
            if (dgram_in.content_type == pdu.ContentType.CONTENT_LOGIN):
                  try :
                        await authenticate_user(dgram_in.content.user_id_passkey, user_id_pass_key)
                        dgram_out = dgram_in         
                  except ServerError as e:
                        err_msg = pdu.ErrorMsg(error_message=str(e))
                        dgram_out = pdu.Datagram(pdu.ContentType.CONTENT_ERROR_MSG, dgram_in.sender, pdu.Content(err_msg=err_msg),"")
            #Logging off
            elif (dgram_in.content_type == pdu.ContentType.CONTENT_LOGOFF):
                  dgram_out = dgram_in
                  del_client_conn_list = client_conn_list
                  try:
                        for i in range(len(client_conn_list)):
                              if dgram_in.sender == del_client_conn_list[i].user :
                                    is_present = 1
                                    del client_conn_list[i]
                        ack_str = ack_str + "Logged off User : "
                  except:
                        await raise_custom_error("Error in logoff.", dgram_in=dgram_in, stream_id=stream_id)
                        return del_client_conn_list
            else:
                  dgram_out = dgram_in

            target_conn = None
            target_stream_id = None
            stream_id = message.stream_id
            sender = str(dgram_out.sender)
            dgram_out.ack = "SVR-ACK: " + ack_str + str(dgram_out.sender)
            rsp_msg = dgram_out.to_bytes()
            rsp_evnt = QuicStreamEvent(stream_id, rsp_msg, False)
            local_client_conn_list = client_conn_list
            # print (f"Source Connection =  {id(conn)}")
            if (dgram_in.content_type != pdu.ContentType.CONTENT_CONNECTION_SET_UP):
                  # Logic to store connection
                  is_present = 0
                  for conns in client_conn_list:
                        print(f"User: {conns.user}, Stream ID: {conns.stream_id}, Connection: {id(conns.connection)}")
                  
                  # To update the latest stream id from the user in the list
                  iter_client_conn_list = client_conn_list
                  
                  for i in range(len(client_conn_list)):
                        if sender == iter_client_conn_list[i].user :
                              is_present = 1
                              client_conn_list[i].stream_id = stream_id
                              client_conn_list[i].connection = conn
                              
                  for conns in client_conn_list:
                        print(f"User: {conns.user}, Stream ID: {conns.stream_id}, Connection: {id(conns.connection)}")

                  if is_present == 0 :
                        curr_conn = Client_Connection(conn,sender,stream_id, sender)
                        local_client_conn_list.append(curr_conn)
                        
                  # Logic to store connection

            # await conn.send(rsp_evnt)
            
            target_is_present = 0
            if (dgram_in.content_type == pdu.ContentType.CONTENT_MESSAGE):
                  target_user_id = dgram_in.content.message.target_user_id
                  for conns in client_conn_list:
                        if target_user_id == conns.user:
                              target_is_present = 1
                              target_conn = conns.connection
                              target_stream_id = conns.stream_id
                              print (f"Data being sent to {conns.user} over connection id {id(conns.connection)} : {dgram_in.content.message.message_text}")    
                  # new_stream_id = target_conn.new_stream()
                  try:
                        if target_is_present:
                              target_qs = QuicStreamEvent(target_stream_id, message.data, False)
                              await target_conn.send(target_qs)   
                        else:
                              await raise_custom_error("User to whom the message was intended not found online.", dgram_in=dgram_in, stream_id=stream_id)
                  except:
                        print (f"Error sending data to the target user. {target_user_id}")
            else:
                  await conn.send(rsp_evnt)
      except:
            print("Error in chat_server.")
      
      return local_client_conn_list