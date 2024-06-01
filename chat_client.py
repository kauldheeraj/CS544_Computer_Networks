
from typing import Dict
import asyncio
import json
from chat_quic import ChatQuicConnection, QuicStreamEvent
import pdu
import chat_interactive

async def wait_for_message(stop_event: asyncio.Event):
    while not stop_event.is_set():
        # print("[svr] Server main loop running")
        # Add your server-side logic here
        await asyncio.sleep(5)  # Sleep for 5 seconds

async def handle_user_input(conn: ChatQuicConnection, stop_event: asyncio.Event):
   while not stop_event.is_set():
        # Display the prompt and read input from the user
        # user_input = input("Chat544>>")
        user_input = await asyncio.to_thread(input, "Chat544>>")
        # Process the input
        if user_input.lower() == 'exit':
            print("Exiting...")
            stop_event.set()
            break
        elif user_input.lower().split()[0].strip() == 'help':
            print("Available commands: exit, help, login")
        elif user_input.lower().split()[0].strip() == 'login':
            await chat_client_login(conn, user_input.lower())
        else:
            print(f"Received command: {user_input}")

async def chat_client_proto(scope:Dict, conn:ChatQuicConnection):
    #START CLIENT HERE
    print('[cli] starting client')
    content_type = pdu.ContentType.CONTENT_CONNECTION_SET_UP # pdu.ContentType.CONTENT_MESSAGE
    sender = "New Client"
    message = pdu.Message (message_text = "REQUESTING CONNECTION")
    content = pdu.Content(message=message)
    datagram = pdu.Datagram(content_type, sender, content,0)
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
    
    await conn.send(qs)
    message:QuicStreamEvent = await conn.receive()
    dgram_resp = pdu.Datagram.from_bytes(message.data)
    print('[cli] got message from sender: ', dgram_resp.sender)
    stop_event = asyncio.Event()
    main_loop_task = asyncio.ensure_future(wait_for_message(stop_event))
    user_input_task = asyncio.ensure_future(handle_user_input(conn,stop_event))    
    await asyncio.gather(main_loop_task, user_input_task)

    # await chat_interactive.interactive_shell(conn)


async def chat_client_login(conn:ChatQuicConnection, command:str):
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

        if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
            print('[cli] Login Successful for : ', dgram_resp.sender)
            return 0
        else:
            print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
            return 1
        # await chat_interactive.interactive_shell(conn)

    else:
        print("Invalid command")
    # $$$$$$$$$$$$$$$$$$$$ CHANGE THE USER PROMPT BY USING THE ASYNC CALLS IN THE ABOVE FUNCTION
    #END LOGGING IN