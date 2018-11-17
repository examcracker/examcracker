import websocket
import time
import api
import json
import capture

def on_message(ws, message):
    responseDict = {}
    messageDict = json.loads(message)

    command = messageDict["command"]
    if command == api.command_start:
        if ws.obj.capturing:
            responseDict["result"] = api.status_capture_started
        else:
            chapterid = messageDict["chapterid"]
            responseDict["result"] = api.status_success
            ws.obj.capturing = True
            capture.startCapturing(chapterid)
    elif command == api.command_stop:
        if not ws.obj.capturing:
            responseDict["result"] = api.status_no_capture_started
            responseDict["result"] = api.status_success
        else:
            cature.stopCapturing()
            ws.obj.capturing = False

    ws.send(json.dumps(responseDict))

def on_error(ws, error):
    print(error)

def on_close(ws):
    pass

class ClientService(object):
    wsclient = None
    capturing = False

    def __init__(self):
        self.wsclient = None
        websocket.enableTrace(True)

    def close(self):
        self.wsclient.close()

    def run(self):
        self.wsclient = websocket.WebSocketApp("ws://127.0.0.1:8000/ws/gyaan/", on_message = on_message, on_close = on_close,
                                          on_error = on_error)
        self.wsclient.obj = self
        self.wsclient.run_forever()

