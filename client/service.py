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
import logger


try:
    import thread
except ImportError:
    import _thread as thread

aes_key = base64.b64decode("iUmAAGnhWZZ75Nq38hG76w==")
aes_iv = base64.b64decode("rgMzT3a413fIAvESuQjt1Q==")

serviceObj = None
systemname = platform.node()

# Log file
LOG = logger.getLogFile(__name__)

def sendCaptureResponse(state):
    global serviceObj
    data = {}
    data["state"] = state
    data["id"] = serviceObj.encryptedid
    httpReq.send(serviceObj.url, "/schedule/captureState/" + str(serviceObj.scheduleid), json.dumps(data))

def on_message(message):
    LOG.info(str(message))

    responseDict = {}
    messageDict = json.loads(message)
    global serviceObj

    if "command" in messageDict.keys():
        machine = messageDict["machine"]
        # check if this client is intended recipient
        if machine != systemname:
            LOG.error("Mismatch in the machine name, input name: " + str(machine) + " actual name is: " + str(systemname))
            return
        command = messageDict["command"]
        if command == api.command_start:
            if serviceObj.capturing:
                responseDict["result"] = api.status_capture_started
            else:
                responseDict["result"] = api.status_start_success
                serviceObj.scheduleid = messageDict["id"]
                serviceObj.chapterid = messageDict["chapterid"]
                serviceObj.publish = messageDict["publish"]
                serviceObj.timeout = int(messageDict["duration"])*60
                sendCaptureResponse(True)
                serviceObj.startCapture()
        elif command == api.command_stop:
            if not serviceObj.capturing:
                responseDict["result"] = api.status_no_capture_started
            else:
                sendCaptureResponse(False)
                res = serviceObj.stopCapture()
                responseDict["result"] = api.status_stop_success
                responseDict["chapterid"] = serviceObj.chapterid
                responseDict["videokey"] = res["videoKey"]
                responseDict["publish"] = serviceObj.publish

                global pusherServer
                responseDict["id"] = serviceObj.clientid
                httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))
    else:
        LOG.warn("Unhandled command: " + str(messageDict.keys())

def connect_handler(data):
    #print(data)
    global serviceObj
    channel = serviceObj.pusherobj.subscribe(str(serviceObj.clientid))
    channel.bind(str(serviceObj.clientid), on_message)

class ClientService(object):

    wsclient = None
    capturing = False
    chapterid = None
    publish = False
    debug = False
    encryptedid = None
    clientid = None
    pusherobj = None
    url = None
    scheduleid = None

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
        self.timeout = 0
        self.captureStartTime = -1

        try:
            self.debug = bool(int(config.get("config", "debug")))
        except:
            pass

    def close(self):
        self.wsclient.close()

    def startCapture(self):
        if self.capturing:
            LOG.warn ("Already capturing")
            return

        self.capturing = True
        self.captureStartTime = int(round(time.time()))
        self.capture.startCapturing()

    def stopCapture(self):
        if not self.capturing:
            LOG.warn ("No active capturing")
            return {"videoKey": None}

        self.capturing = False
        self.timeout = 0
        self.capture.stopCapturing()
        time.sleep(5)
        LOG.info ("Uploading file to server: " + str(self.capture.outputFileName))
        uploadResponse = self.upload.uploadVideoJW(self.capture.outputFileName)
        LOG.info ("Uploading done")
        LOG.debug("Video Server response: " + str(uploadResponse))
        return uploadResponse

    def run(self):
        self.url = "https://www.gyaanhive.com"
        if self.debug:
            self.url = "http://127.0.0.1:8000"
        LOG.info(self.url)

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
            if self.capturing and self.timeout > 0:
                timeDiff = int(round(time.time())) - self.captureStartTime
                if timeDiff >= self.timeout:
                    responseDict = {}
                    LOG.info ("Timeout stopping the capturing")
                    sendCaptureResponse(False)
                    res = self.stopCapture()
                    responseDict["result"] = api.status_stop_success
                    responseDict["chapterid"] = self.chapterid
                    responseDict["videokey"] = res["videoKey"]
                    responseDict["publish"] = self.publish

                    global pusherServer
                    responseDict["id"] = self.clientid
                    httpReq.send(self.url, "/cdn/saveClientSession/", json.dumps(responseDict))
				

def main():
    global serviceObj
    serviceObj = ClientService()
    serviceObj.run()

if __name__ == "__main__":
    main()

