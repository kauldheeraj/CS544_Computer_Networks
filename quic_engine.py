import asyncio
from aioquic.asyncio import connect, serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from typing import Optional, Dict, Callable, Coroutine, Deque, List, Tuple
from aioquic.tls import SessionTicket
from collections import deque
import json
from chat_quic import ChatQuicConnection, QuicStreamEvent
import chat_server, chat_client
from dataclasses import dataclass

ALPN_PROTOCOL = "chat-protocol"

def build_server_quic_config(cert_file, key_file) -> QuicConfiguration:
    configuration = QuicConfiguration(
        alpn_protocols=[ALPN_PROTOCOL], 
        is_client=False
    )
    configuration.load_cert_chain(cert_file, key_file)
  
    return configuration

def build_client_quic_config(cert_file = None):
    configuration = QuicConfiguration(alpn_protocols=[ALPN_PROTOCOL], 
                                      is_client=True)
    if cert_file:
        configuration.load_verify_locations(cert_file)
  
    return configuration

def create_msg_payload(msg):
    return json.dumps(msg).encode('utf-8')

SERVER_MODE = 0
CLIENT_MODE = 1



class AsyncQuicServer(QuicConnectionProtocol):
    def __init__(self, *args, conn_list=None,  **kwargs):
        # print("____AsyncQuicServer_Init___")
        super().__init__(*args, **kwargs)
        self._handlers: Dict[int, ChatServerRequestHandler] = {}
        self._client_handler: Optional[ChatClientRequestHandler] = None
        self._is_client: bool = self._quic.configuration.is_client
        self._mode: int = SERVER_MODE if not self._is_client else CLIENT_MODE
        self.conn_list: List[chat_server.Client_Connection] = conn_list
        if self._mode == CLIENT_MODE:
            self._attach_client_handler()
        # try:
        #     print(self.track_int)
        #     self.track_int=1
        #     print("Able to track in AsyncQuicServer")
        # except:
        #     print("Not able to track in AsyncQuicServer")

    def _attach_client_handler(self): 
        # print("____attach_client_handler___")
        if self._mode == CLIENT_MODE:
            self._client_handler = ChatClientRequestHandler(
                       authority=self._quic.configuration.server_name,
                        connection=self._quic,
                        protocol=self,
                        scope={},
                        stream_ended=False,
                        stream_id=None,
                        transmit=self.transmit,
                        conn_list=[]
                 )
        
    def remove_handler(self, stream_id):
        self._handlers.pop(stream_id)
        
    def _quic_client_event_dispatch(self, event):
        # print("____quic_client_event_dispatch___")
        if isinstance(event, StreamDataReceived):
            self._client_handler.quic_event_received(event)
        
    def _quic_server_event_dispatch(self, event):
        # print("___quic_server_event_dispatch___")
        handler = None
        if isinstance(event, StreamDataReceived):
            if event.stream_id not in self._handlers:
                 handler = ChatServerRequestHandler(
                        authority=self._quic.configuration.server_name,
                        connection=self._quic,
                        protocol=self,
                        scope={},
                        stream_ended=False,
                        stream_id=event.stream_id,
                        transmit=self.transmit,
                        conn_list=self.conn_list
                 )
                 self._handlers[event.stream_id] = handler
                 handler.quic_event_received(event)
                 asyncio.ensure_future(handler.launch_chat())
            else:
                handler = self._handlers[event.stream_id]
                handler.quic_event_received(event)

    def quic_event_received(self, event):
        # print("__quic_event_received___")
        if self._mode == SERVER_MODE:
            self._quic_server_event_dispatch(event)
            # print ("Quic server event received")
        else:
            self._quic_client_event_dispatch(event)
            # print ("Quic client event received")

    def is_client(self) -> bool:
        return self._quic.configuration.is_client

class SessionTicketStore:
    """
    Simple in-memory store for session tickets.
    """

    def __init__(self) -> None:
        self.tickets: Dict[bytes, SessionTicket] = {}

    def add(self, ticket: SessionTicket) -> None:
        self.tickets[ticket.ticket] = ticket

    def pop(self, label: bytes) -> Optional[SessionTicket]:
        return self.tickets.pop(label, None)

async def run_server(server, server_port, configuration  , conn_list:List[chat_server.Client_Connection] ):  
    print("[svr] Server starting...")  
    
    # Custom protocol creation function
    def create_protocol(*args, **kwargs):
        return AsyncQuicServer(*args, conn_list=conn_list, **kwargs)
    
    await serve(server, server_port, configuration=configuration, 
            # create_protocol=AsyncQuicServer,
            create_protocol=create_protocol,
            session_ticket_fetcher=SessionTicketStore().pop,
            session_ticket_handler=SessionTicketStore().add)
    await asyncio.Future()
    
    
    # Wait for both tasks to complete (which they won't, in this case)
    # await asyncio.gather(server_task, main_loop_task)    
              
async def run_client(server, server_port, configuration):    
    # print("__run_client___")

    def create_protocol(*args, **kwargs):
        return AsyncQuicServer(*args, conn_list=List[chat_server.Client_Connection], **kwargs)
    
    async with connect(server, server_port, configuration=configuration, 
            create_protocol=create_protocol) as client:
        await asyncio.ensure_future(client._client_handler.launch_chat())

class ChatServerRequestHandler:
    
    def __init__(
        self,
        *,
        authority: bytes,
        connection: AsyncQuicServer,
        protocol: QuicConnectionProtocol,
        scope: Dict,
        stream_ended: bool,
        stream_id: int,
        transmit: Callable[[], None],
        conn_list: List[chat_server.Client_Connection]
    ) -> None:
        self.authority = authority
        self.connection = connection
        self.protocol = protocol
        self.queue: asyncio.Queue[QuicStreamEvent] = asyncio.Queue()
        self.scope = scope
        self.stream_id = stream_id
        self.transmit = transmit
        self.conn_list = conn_list
        if stream_ended:
            self.queue.put_nowait({"type": "quic.stream_end"})
        # print("__ChatServerRequestHandler_init___")
    
    def quic_event_received(self, event: StreamDataReceived) -> None:
        # print("__quic_event_received___")
         
        self.queue.put_nowait(
            QuicStreamEvent(event.stream_id, event.data, 
                            event.end_stream)
        )

    async def receive(self) -> QuicStreamEvent:
        queue_item = await self.queue.get()
        return queue_item
    
    async def send(self, message: QuicStreamEvent) -> None:
        self.connection.send_stream_data(
                stream_id=message.stream_id,
                data=message.data,
                end_stream=message.end_stream
        )
        
        self.transmit()
        
    def close(self) -> None:
        self.protocol.remove_handler(self.stream_id)
        self.connection.close()
        
    async def launch_chat(self):
        # print("__launch_chat___")
        qc = ChatQuicConnection(self.send, 
                self.receive, self.close, None)
        # try:
            # print("Total Connections =" + str(len(self.conn_list)))
            # print("Able to track in quic_event_received") 
        self.conn_list = await chat_server.chat_server_proto(self.scope, 
            qc, self.conn_list)               
        # except:
            # print("Not able to track in quic_event_received") 

        # try:
        #     print(len(self.conn_list))
        #     print("Able to track in quic_event_received after return") 
        # except:
        #     print("Not able to track in quic_event_received after return") 

        # print ("Launch Chat Start")  
        # print(f"client_conn_list is None: {self.client_conn_list is None}")
        # print(f"Type of client_conn_list: {type(self.client_conn_list)}")
        # try:
        #     print(f"Length of client_conn_list: {len(self.client_conn_list)}")
        # except TypeError as e:
        #     print(f"Error calculating length of client_conn_list: {e}")
        #     print(f"client_conn_list: {self.client_conn_list}")        
        # print ("Launch Chat Start")  
        print("___________________________________________________")      

class ChatClientRequestHandler(ChatServerRequestHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print("__ChatClientRequestHandler__ Init")

    def get_next_stream_id(self) -> int:
        return self.connection.get_next_available_stream_id()
    
    async def launch_chat(self):
        # print("launch_chat")
        qc = ChatQuicConnection(self.send, 
                self.receive, self.close, 
                self.get_next_stream_id)
        await chat_client.chat_client_proto(self.scope, 
            qc)