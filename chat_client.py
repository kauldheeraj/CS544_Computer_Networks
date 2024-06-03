from typing import Dict
import asyncio
from chat_quic import ChatQuicConnection, QuicStreamEvent
import pdu, chat_states
import traceback

# Options for user to enter on the chat prompt
async def user_options_actions(user_input, conn, current_user_id_l, stop_event, current_client_state) -> 'str':
        
        main_cmd = user_input.lower().split()[0].strip()
        if main_cmd == 'help' or main_cmd == '?': 
            print ("[Usage] : login user password")
            print ("[Usage] : send target_user_id text-message  OR")
            print ("[Usage] : text target_user_id text-message")
            print ("[Usage] : bye/exit/logoff")
            return current_user_id_l
        elif current_user_id_l != "" or main_cmd == 'login':
            if main_cmd == 'send' or main_cmd == 'text': 
                next_state = chat_states.ClientStates.C_READY_TO_SEND_RECEIVE
                if chat_states.validate_client_state(current_client_state, next_state):
                    await chat_client_send(conn, user_input.lower(),current_user_id_l)
                else:
                    print ("Next DFA State not valid for the option chosen.")
                    next_state=current_client_state
                return current_user_id_l, next_state
            elif main_cmd == 'login':
                next_state = chat_states.ClientStates.C_WAITING_FOR_AUTHENTICATION
                if chat_states.validate_client_state(current_client_state, next_state):
                    current_user_id_l = await chat_client_login(conn, user_input.lower())
                else:
                    print ("Next DFA State not valid for the option chosen.")                
                    next_state=current_client_state
                return current_user_id_l, next_state
            elif user_input.lower() == 'exit' or user_input.lower() == 'logoff' or user_input.lower() == 'bye':
                next_state = chat_states.ClientStates.C_WAITING_TO_GET_LOGGED_OFF
                if chat_states.validate_client_state(current_client_state, next_state):
                    await chat_client_logoff(conn, current_user_id_l)
                else:
                    print ("Next DFA State not valid for the option chosen.")
                    next_state=current_client_state                                
                return None, next_state
        else:
            print(f"Received command: {user_input}")  
            invalidCommand()
            return current_user_id_l, current_client_state

#Wait for any message being sent from the server
async def wait_for_message(stop_event: asyncio.Event, conn:ChatQuicConnection):
    while not stop_event.is_set():
        try:
            await asyncio.sleep(10)  # Sleep for 5 seconds
            message: QuicStreamEvent = await asyncio.wait_for(conn.receive(), timeout=3)
            dgram_resp = pdu.Datagram.from_bytes(message.data)
            print(dgram_resp.sender , ' says :' , dgram_resp.content.message.message_text)
        except asyncio.TimeoutError:
            continue  # No message received, continue the loop
        except Exception as e:
            continue

#To handle user inputs on the chat prompt
async def handle_user_input(conn: ChatQuicConnection, stop_event: asyncio.Event, client_state_param):
   current_user_id_l = ""
   client_state=client_state_param
   while not stop_event.is_set():
        # Display the prompt and read input from the user
        
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(None, input, "Chat_544 $$ " + current_user_id_l + ">>")
            # user_input = await asyncio.to_thread(input, "Chat_544 $$ " + current_user_id_l + ">>")
            return_user_id, client_state = await user_options_actions(user_input, conn, current_user_id_l, stop_event, client_state)
            if  return_user_id is None:
                print("Exiting...")
                stop_event.set()
                break
            else:
                current_user_id_l = return_user_id
        except:
            print ("Exception in handle_user_input")
            continue

#To display invalid command message
def invalidCommand():
    print("Invalid command or arguments. Type 'help' or '?' for list of valid commands.")

#Initial client connectivity
async def chat_client_proto(scope:Dict, conn:ChatQuicConnection):
    #START CLIENT HERE
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
    print('[cli] Client request from : ', dgram_resp.sender)
        
    stop_event = asyncio.Event()
    main_loop_task = asyncio.ensure_future(wait_for_message(stop_event, conn))
    # print (f"Connection Before handing input = {id(conn)}")
    user_input_task = asyncio.ensure_future(handle_user_input(conn,stop_event, chat_states.ClientStates.C_CONNECTED))

    await asyncio.gather(main_loop_task, user_input_task)

# Client login using userid and password
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
    else:
        invalidCommand()
    #END LOGGING IN

#Sending messages to other users.
async def chat_client_send(conn:ChatQuicConnection, command:str, user_id:str):
    #START sending message
    print('[cli] Sending Message')
    cmd_arr = command.split(maxsplit=2)
    content_type = pdu.ContentType.CONTENT_MESSAGE
    try:
        if len(cmd_arr) > 2:
            
            target_user_id =  cmd_arr[1].strip()
            message_text = cmd_arr[2].strip()     
            message = pdu.Message (target_user_id=target_user_id, message_text=message_text)
            content = pdu.Content(message=message)
            
            datagram = pdu.Datagram(content_type, user_id, content,0,"")
            
            new_stream_id = conn.new_stream()
            qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
            await conn.send(qs)
            # message:QuicStreamEvent = await conn.receive()

            try:
                message:QuicStreamEvent = await asyncio.wait_for(conn.receive(), timeout=3) 
                dgram_resp = pdu.Datagram.from_bytes(message.data)
                if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
                    print('[cli] Message successfully sent to : ', dgram_resp.content.message.target_user_id)
                    return 0
                else:
                    print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
                    return 1
            except asyncio.TimeoutError as e:
                    print (e)
                    traceback.print_exception()
                    pass
            
            except Exception as e:
                    traceback.print_exception() 
            dgram_resp = pdu.Datagram.from_bytes(message.data)

            if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
                print('[cli] Message successfully sent to : ', dgram_resp.content.message.target_user_id)
                return 0
            else:
                print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
                return 1
        else:
            invalidCommand()
    except:
        print("Exception in chat_client_send")
    #END LOGGING IN    

#Logging off
async def chat_client_logoff(conn:ChatQuicConnection, current_user_id_l:str) -> 'str':
    #START Logging
    print('[cli] Logging off...')
    content_type = pdu.ContentType.CONTENT_LOGOFF

    try:
        user_id =  current_user_id_l
        message = pdu.Message (target_user_id=user_id, message_text=user_id)
        content = pdu.Content(message=message)
        datagram = pdu.Datagram(content_type, user_id, content,0,"")
        new_stream_id = conn.new_stream()
        qs = QuicStreamEvent(new_stream_id, datagram.to_bytes(), False)
        
        await conn.send(qs)
        message:QuicStreamEvent = await conn.receive()
        print ("Line 206")
        dgram_resp = pdu.Datagram.from_bytes(message.data)

        if dgram_resp.content_type != pdu.ContentType.CONTENT_ERROR_MSG:
            print('[cli] Logout Successful for : ', dgram_resp.sender)
            return dgram_resp.sender
        else:
            print('[cli] Error : ' , dgram_resp.content.err_msg.error_message)
            return ""
    except:
        print("Exception in client logoff.")
    #END LOGGING OFF