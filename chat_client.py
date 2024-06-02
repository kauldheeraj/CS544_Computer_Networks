from typing import Dict
import asyncio
import json
from chat_quic import ChatQuicConnection, QuicStreamEvent
import pdu

async def wait_for_message(stop_event: asyncio.Event, conn:ChatQuicConnection):
    while not stop_event.is_set():
        # print("[svr] Server main loop running")
        # Add your server-side logic here
        await asyncio.sleep(30)  # Sleep for 5 seconds
        print("Refreshing......")

        message:QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)
        print('[cli] got message from sender: ', dgram_resp.content.message.message_text)
        # print("Some input\n")

async def handle_user_input(conn: ChatQuicConnection, stop_event: asyncio.Event):
   current_user_id_l = ""
   while not stop_event.is_set():
        print(f"User ID now = {current_user_id_l}")
        # Display the prompt and read input from the user
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "Chat_544 $$ " + current_user_id_l + ">>")
        # Process the input
        if user_input.lower().split()[0].strip() == 'send': 
           await chat_client_send(conn, user_input.lower(),current_user_id_l)

        elif user_input.lower().split()[0].strip() == 'login':
            print (f"Current connection in handle user input = {id(conn)}")
            current_user_id_l = await chat_client_login(conn, user_input.lower())
        
        elif user_input.lower() == 'exit' or user_input.lower() == 'logoff' or user_input.lower() == 'bye':
            print("Exiting...")
            stop_event.set()
            break
        
        elif user_input.lower().split()[0].strip() == 'help':
            print ("[Usage] : login user password")
            print ("[Usage] : send target_user_id \"text message\"")
            print ("[Usage] : bye/exit/logoff")

        else:
            print(f"Received command: {user_input}")

async def chat_client_proto(scope:Dict, conn:ChatQuicConnection):
    #START CLIENT HERE
    global user_id_global
    user_id_global=""
    print('[cli] starting client')
    content_type = pdu.ContentType.CONTENT_CONNECTION_SET_UP # pdu.ContentType.CONTENT_MESSAGE
    sender = "New Client"
    message = pdu.Message (target_user_id= "", message_text = "REQUESTING CONNECTION")
    content = pdu.Content(message=message)
    datagram = pdu.Datagram(content_type, sender, content,0,"")
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
    # print (f"Connection when establishing connection =  {id(conn)}")
    await conn.send(qs)
    message:QuicStreamEvent = await conn.receive()
    dgram_resp = pdu.Datagram.from_bytes(message.data)
    print('[cli] got message from sender: ', dgram_resp.sender)
    stop_event = asyncio.Event()
    main_loop_task = asyncio.ensure_future(wait_for_message(stop_event, conn))
    # print (f"Connection Before handing input = {id(conn)}")
    user_input_task = asyncio.ensure_future(handle_user_input(conn,stop_event))    
    await asyncio.gather(main_loop_task, user_input_task)

    # await chat_interactive.interactive_shell(conn)

async def chat_client_login(conn:ChatQuicConnection, command:str) -> 'str':
    #START Logging
    print('[cli] Logging in')
    cmd_arr = command.split()
    # print(f"Connection chat client login = {id(conn)}")
    content_type = pdu.ContentType.CONTENT_LOGIN
    if len(cmd_arr) > 2:
        user_id =  cmd_arr[1].strip()
        pass_key = cmd_arr[2].strip()        
        user_id_passkey = pdu.UserIdPasskey (user_id=user_id, pass_key=pass_key)
        content = pdu.Content(user_id_passkey=user_id_passkey)
        datagram = pdu.Datagram(content_type, user_id, content,0,"")
        new_stream_id = conn.new_stream()
        qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
        await conn.send(qs)
        message:QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)

        if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
            print('[cli] Login Successful for : ', dgram_resp.sender)
            return dgram_resp.sender
        else:
            print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
            return ""
        # await chat_interactive.interactive_shell(conn)

    else:
        print("Invalid command")
    # $$$$$$$$$$$$$$$$$$$$ CHANGE THE USER PROMPT BY USING THE ASYNC CALLS IN THE ABOVE FUNCTION
    #END LOGGING IN

async def chat_client_send(conn:ChatQuicConnection, command:str, user_id:str):
    #START sending message
    print('[cli] Sending Message')
    cmd_arr = command.split(maxsplit=2)
    content_type = pdu.ContentType.CONTENT_MESSAGE
    if len(cmd_arr) > 2:
        
        target_user_id =  cmd_arr[1].strip()
        message_text = cmd_arr[2].strip()     
        print (f"Message Type={message_text}")   
        message = pdu.Message (target_user_id=target_user_id, message_text=message_text)
        content = pdu.Content(message=message)
        
        datagram = pdu.Datagram(content_type, user_id, content,0,"")
        
        new_stream_id = conn.new_stream()
        qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
        await conn.send(qs)
        message:QuicStreamEvent = await conn.receive()
        dgram_resp = pdu.Datagram.from_bytes(message.data)

        if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
            print('[cli] Message successfully sent to : ', dgram_resp.content.message.target_user_id)
            return 0
        else:
            print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
            return 1
        # await chat_interactive.interactive_shell(conn)

    else:
        print("Invalid command")
    # $$$$$$$$$$$$$$$$$$$$ CHANGE THE USER PROMPT BY USING THE ASYNC CALLS IN THE ABOVE FUNCTION
    #END LOGGING IN    