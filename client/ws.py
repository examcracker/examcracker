import websocket
import time
import json
import api

def on_message(ws, message):
    message_dict = json.dumps(message)
    command = message_dict['command']
    

def on_error(ws, error):
    print(error)

def on_close(ws):
    pass

def on_open(ws):
    while True:
        time.sleep(1000)


