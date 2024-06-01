
from typing import Dict
import json
from chat_quic import ChatQuicConnection, QuicStreamEvent
import pdu
import code
import argparse
import asyncio
import subprocess
import chat_client
#New changes to test
class CustomInteractiveConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", custom_prompt=">>>"):
        super().__init__(locals)
        self.custom_prompt = custom_prompt

    def raw_input(self, prompt=None):
        if prompt is None:
            prompt = self.custom_prompt
        prompt += " "
        return input(prompt)

    async def push(self, command, conn:ChatQuicConnection):
        first_cmd_option = command.split()[0].strip()
        
        if first_cmd_option == 'login':
            # asyncio.run(start_client())  # Custom command to start the client
            print ('Logging in......')
            await chat_client.chat_client_login(conn, command)
        elif first_cmd_option == 'bye' or first_cmd_option == 'logoff' or first_cmd_option == 'exit':
            print ("Signing off......")
            raise SystemExit
        elif first_cmd_option == 'help' or first_cmd_option == "?":
            print ("[Usage] : login , help, ? , send, bye, logoff, exit")
            raise SystemExit
        else:
            print ("Invalid chat command")
            # try:
            #     result = subprocess.run(line, shell=True, check=True, capture_output=True, text=True)
            #     print(result.stdout, end="")
            # except subprocess.CalledProcessError as e:
            #     print(e.stderr, end="")
            # except FileNotFoundError:
            #     return super().push(line)
            
# def chat_client_interactive(conn:ChatQuicConnection):

async def interactive_shell(conn:ChatQuicConnection):
    variables = globals().copy()
    variables.update(locals())
    custom_prompt="CS544_Chat>>>"
    shell = CustomInteractiveConsole(variables, custom_prompt=custom_prompt)
    while True:
        try:
            line = shell.raw_input()
            await shell.push(line, conn)
        except EOFError:
            # Exit on Ctrl+D or EOF
            break        
    # shell.interact() 
    # interactive_shell()