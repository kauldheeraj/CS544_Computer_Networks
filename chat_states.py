from enum import Enum

class ClientStates:
    C_CONNECTED = 0X00
    C_WAITING_FOR_AUTHENTICATION = 0X01
    C_READY_TO_SEND_RECEIVE = 0X02
    C_WAITING_FOR_ACK=0X03
    C_WAITING_TO_GET_LOGGED_OFF=0X04
    C_LOGGED_OFF=0X05

class ServerStates:
    S_CONNECTED = 0X00
    S_READY_TO_RECEIVE_SEND = 0X01
    S_MESSAGE_RECEIVED = 0X02
    S_WAITING_FOR_ACK = 0X03

def validate_client_state(current_state:ClientStates, proposed_state:ClientStates):
    next_possible_state = next_client_state(current_state)
    if (next_possible_state & proposed_state) != 0 :
        return True
    return False

def validate_server_state(current_state:ServerStates,proposed_state:ServerStates):
    next_possible_state = next_client_state(current_state)
    if (next_possible_state & proposed_state) != 0 :
        return True
    return False

def next_client_state(current_state:ClientStates) -> ClientStates:
    if current_state == ClientStates.C_CONNECTED:
        return ClientStates.C_WAITING_FOR_AUTHENTICATION
    elif current_state == ClientStates.C_WAITING_FOR_AUTHENTICATION :
        return ClientStates.C_READY_TO_SEND_RECEIVE  | ClientStates.C_WAITING_TO_GET_LOGGED_OFF
    elif current_state == ClientStates.C_READY_TO_SEND_RECEIVE :
        return ClientStates.C_WAITING_FOR_ACK | ClientStates.C_WAITING_TO_GET_LOGGED_OFF
    elif current_state == ClientStates.C_WAITING_FOR_ACK:
        return ClientStates.C_READY_TO_SEND_RECEIVE
    elif current_state == ClientStates.C_WAITING_TO_GET_LOGGED_OFF:
        return ClientStates.C_LOGGED_OFF | ClientStates.C_CONNECTED
    
def next_server_state(current_state:ServerStates) -> ServerStates:
    if current_state == ServerStates.S_CONNECTED :
        return ServerStates.S_READY_TO_RECEIVE_SEND
    elif current_state == ServerStates.S_READY_TO_RECEIVE_SEND :
        return ServerStates.S_MESSAGE_RECEIVED
    elif current_state == ServerStates.S_MESSAGE_RECEIVED :
        return ServerStates.S_READY_TO_RECEIVE_SEND | ServerStates.S_WAITING_FOR_ACK
    elif current_state == ServerStates.S_WAITING_FOR_ACK :
        return ServerStates.S_READY_TO_RECEIVE_SEND