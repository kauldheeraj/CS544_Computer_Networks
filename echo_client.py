
from typing import Dict
import json
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu
import chat_interactive

async def echo_client_proto(scope:Dict, conn:EchoQuicConnection):
    #START CLIENT HERE
    print('[cli] starting client')
    # datagram = pdu.Datagram(pdu.MSG_TYPE_DATA, "This is a NOT test message")
    content_type = pdu.ContentType.CONTENT_CONNECTION_SET_UP # pdu.ContentType.CONTENT_MESSAGE
    sender = "default_sender"
    # content = "First Message for Connection" #pdu.Message
    message = pdu.Message (message_text = "REQUESTING CONNECTION")
    content = pdu.Content(message=message)
    # content.message_text = "First Message for Connection"
    datagram = pdu.Datagram(content_type, sender, content,0)
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
    await conn.send(qs)
    message:QuicStreamEvent = await conn.receive()
    dgram_resp = pdu.Datagram.from_bytes(message.data)
    # print('[cli] got message: ', dgram_resp.msg)
    print('[cli] got message from sender: ', dgram_resp.sender)
    # print('[cli] msg as json: ', dgram_resp.to_json())
    await chat_interactive.interactive_shell(conn)
    # chat_interactive.chat_client_interactive()
    #END CLIENT HERE

async def echo_client_login(conn:EchoQuicConnection, command:str):
    #START Logging
    print('[cli] Logging in')
    cmd_arr = command.split()
    
    content_type = pdu.ContentType.CONTENT_LOGIN
    if len(cmd_arr) > 2:
        user_id =  cmd_arr[1].strip()
        pass_key = cmd_arr[2].strip()        
        user_id_passkey = pdu.UserIdPasskey (user_id=user_id, pass_key=pass_key)
        content = pdu.Content(user_id_passkey=user_id_passkey)
        datagram = pdu.Datagram(content_type, user_id, content,0)
        new_stream_id = conn.new_stream()
        qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
        await conn.send(qs)
        message:QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)
        # print('[cli] got message: ', dgram_resp.msg)
        if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
            print('[cli] got message from sender: ', dgram_resp.sender)
        else:
            print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
        # print('[cli] msg as json: ', dgram_resp.to_json())
        await chat_interactive.interactive_shell(conn)

    else:
        print("Invalid command")

    #END LOGGING IN