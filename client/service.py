from __future__ import print_function
from Crypto.Cipher import AES
import captureFeed
import uploadVideo
import configparser
import os
import sys
import websocket
import pysher
import pusher
import time
import api
import base64
import json
import signal
import httpReq
import platform
try:
    import thread
except ImportError:
    import _thread as thread

aes_key = base64.b64decode("iUmAAGnhWZZ75Nq38hG76w==")
aes_iv = base64.b64decode("rgMzT3a413fIAvESuQjt1Q==")

serviceObj = None
systemname = platform.node()

def on_message(message):
    print(message)

    responseDict = {}
    messageDict = json.loads(message)
    global serviceObj

    if "command" in messageDict.keys():
        command = messageDict["command"]
        if command == api.command_start:
            if serviceObj.capturing:
                responseDict["result"] = api.status_capture_started
            else:
                responseDict["result"] = api.status_start_success
                serviceObj.chapterid = messageDict["chapterid"]
                serviceObj.publish = messageDict["publish"]
                serviceObj.startCapture()
        elif command == api.command_stop:
            if not serviceObj.capturing:
                responseDict["result"] = api.status_no_capture_started
            else:
                res = serviceObj.stopCapture()
                responseDict["result"] = api.status_stop_success
                responseDict["chapterid"] = serviceObj.chapterid
                responseDict["videokey"] = res["videoKey"]
                responseDict["publish"] = serviceObj.publish

        global pusherServer
        responseDict["id"] = serviceObj.clientid
        print("Sending " + str(responseDict))
        if command == api.command_stop:
            httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))

        #ws.send(json.dumps(responseDict))
    elif "id" in messageDict.keys():
        print("Synced with id " + str(serviceObj.clientid))
        pass
    else:
        print ("Unhandled command: ", messageDict.keys())

'''
def on_error(ws, error):
    print(error)

def on_close(ws):
    pass

def on_open(ws):
    iddict = {}
    iddict["id"] = int(clientid)
    ws.send(json.dumps(iddict))
'''

def connect_handler(data):
    print(data)
    global serviceObj
    channel = serviceObj.pusherobj.subscribe(str(serviceObj.clientid))
    channel.bind(str(serviceObj.clientid), on_message)

class ClientService(object):

    wsclient = None
    capturing = False
    chapterid = None
    #wsclient = None
    publish = False
    debug = False
    encryptedid = None
    clientid = None
    pusherobj = None
    url = None

    def __init__(self):
        websocket.enableTrace(True)

        dir_path = os.path.dirname(os.path.realpath(__file__))
        if getattr(sys, 'frozen', False):
            dir_path = os.path.dirname(sys.executable)

        config = configparser.ConfigParser()
        configPath = os.path.join(dir_path, "arguments.cfg")
        config.readfp(open(configPath))

        self.encryptedid = config.get("config", "clientId")
        decipher = AES.new(aes_key, AES.MODE_CFB, aes_iv)
        self.clientid = decipher.decrypt(base64.b64decode(self.encryptedid)).decode()

        self.capture = captureFeed.captureFeed(self.clientid, configPath, os.path.join(dir_path, "ffmpeg.exe"))
        self.upload = uploadVideo.uploadVideo(self.clientid)

        try:
            self.debug = bool(int(config.get("config", "debug")))
        except:
            pass

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
            return {"videoKey": None}

        self.capturing = False
        self.capture.stopCapturing()
        time.sleep(5)
        print ("Uploading file to jw: ", self.capture.outputFileName)
        uploadResponse = self.upload.uploadVideoJW(self.capture.outputFileName)
        print ("Uploading done: ", uploadResponse)
        return uploadResponse

    def run(self):
        self.url = "https://www.gyaanhive.com"
        if self.debug:
            self.url = "http://127.0.0.1:8000"
        print(self.url)

        #self.wsclient = websocket.WebSocketApp(url, on_message = on_message, on_close = on_close, on_error = on_error)
        #self.wsclient.on_open = on_open
        #self.wsclient.obj = self
        #self.wsclient.run_forever()

        self.pusherobj = pysher.Pusher("3ff394e3371be28d8abd", "ap2")
        self.pusherobj.connection.bind('pusher:connection_established', connect_handler)
        self.pusherobj.connect()

        global systemname
        initDict = {}
        initDict["id"] = self.encryptedid
        initDict["system"] = systemname
        httpReq.send(self.url, "/schedule/systemName", json.dumps(initDict))

        while True:
            time.sleep(1)

def main():
    global serviceObj
    serviceObj = ClientService()
    serviceObj.run()

if __name__ == "__main__":
    main()

