
from typing import Dict
import json
from echo_quic import EchoQuicConnection, QuicStreamEvent
import pdu
import chat_interactive

async def echo_client_proto(scope:Dict, conn:EchoQuicConnection):
    #START CLIENT HERE
    print('[cli] starting client')
    # datagram = pdu.Datagram(pdu.MSG_TYPE_DATA, "This is a NOT test message")
    content_type = 1 # pdu.ContentType.CONTENT_MESSAGE
    sender = "default_sender"
    content = "First Message for Connection" #pdu.Message
    # content.message_text = "First Message for Connection"
    datagram = pdu.Datagram(content_type, sender, content,0)
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
    await conn.send(qs)
    message:QuicStreamEvent = await conn.receive()
    dgram_resp = pdu.Datagram.from_bytes(message.data)
    # print('[cli] got message: ', dgram_resp.msg)
    print('[cli] got message from sender: ', dgram_resp.sender)
    print('[cli] msg as json: ', dgram_resp.to_json())
    await chat_interactive.interactive_shell(conn)
    # chat_interactive.chat_client_interactive()
    #END CLIENT HERE

async def echo_client_login(conn:EchoQuicConnection):
    #START Logging
    print('[cli] Logging in')
    datagram = pdu.Datagram(pdu.MSG_TYPE_DATA, "This is a NOT test message")
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
    await conn.send(qs)
    message:QuicStreamEvent = await conn.receive()
    dgram_resp = pdu.Datagram.from_bytes(message.data)
    print('[cli] got message: ', dgram_resp.msg)
    print('[cli] msg as json: ', dgram_resp.to_json())
    #END LOGGING IN  
        