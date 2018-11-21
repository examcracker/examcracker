from __future__ import print_function
from Crypto.Cipher import AES
import captureFeed
import uploadVideo
import configparser
import os
import websocket
import time
import api
import base64
import json
import signal

try:
    import thread
except ImportError:
    import _thread as thread

aes_key = base64.b64decode("iUmAAGnhWZZ75Nq38hG76w==")
aes_iv = base64.b64decode("rgMzT3a413fIAvESuQjt1Q==")
clientid = None

def on_message(ws, message):
    print(message)
    responseDict = {}
    messageDict = json.loads(message)

    if "command" in messageDict.keys():
        command = messageDict["command"]
        if command == api.command_start:
            if ws.obj.capturing:
                responseDict["result"] = api.status_capture_started
            else:
                chapterid = messageDict["chapterid"]
                responseDict["result"] = api.status_start_success
                ws.obj.chapterid = chapterid
                ws.obj.startCapture()
        elif command == api.command_stop:
            if not ws.obj.capturing:
                responseDict["result"] = api.status_no_capture_started
            else:
                ws.obj.stopCapture()
                responseDict["result"] = api.status_stop_success
                responseDict["chapterid"] = ws.obj.chapterid
                responseDict["videokey"] = ws.obj.videokey

        ws.send(json.dumps(responseDict))
    elif "id" in messageDict.keys():
        global clientid
        print("Synced with id " + str(clientid))
        pass
    else:
        print ("Unhandled command: ", messageDict.keys())


def on_error(ws, error):
    print(error)

def on_close(ws):
    pass

def on_open(ws):
    iddict = {}
    iddict["id"] = int(clientid)
    ws.send(json.dumps(iddict))

class ClientService(object):

    wsclient = None
    capturing = False
    chapterid = None
    videokey = None
    wsclient = None

    def __init__(self):
        websocket.enableTrace(True)

        dir_path = os.path.dirname(os.path.realpath(__file__))
        config = configparser.ConfigParser()
        config.readfp(open(os.path.join(dir_path, "arguments.cfg")))

        global clientid
        b64clientid = base64.b64decode(config.get("config", "clientId"))
        decipher = AES.new(aes_key, AES.MODE_CFB, aes_iv)
        clientid = decipher.decrypt(b64clientid).decode()

        self.capture = captureFeed.captureFeed(clientid)
        self.upload = uploadVideo.uploadVideo(clientid)

    def close(self):
        self.wsclient.close()

    def startCapture(self):
        if self.capturing:
            print ("Already capturing")
            return

        self.capturing = True
        self.capture.startCapturing()

    def stopCapture(self):
        if not self.capturing:
            print ("No active capturing")
            return

        self.capturing = False
        self.capture.stopCapturing()
        print ("Uploading file to jw: ", self.capture.outputFileName)
        uploadResponse = self.upload.uploadVideoJW(self.capture.outputFileName)
        print ("Uploading done: ", uploadResponse)

    def run(self):
        self.wsclient = websocket.WebSocketApp("ws://127.0.0.1:8000/ws/gyaan/", on_message = on_message, on_close = on_close, on_error = on_error)
        self.wsclient.on_open = on_open
        self.wsclient.obj = self
        self.wsclient.run_forever()

def main():
    service = ClientService()
    service.run()

if __name__ == "__main__":
    main()

