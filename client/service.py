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
import psutil
from collections import deque
import glob

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
    httpReq.send(serviceObj.url, "/schedule/captureState/" + str(serviceObj.scheduleid), json.dumps(data))

def on_message(message):
    LOG.info(str(message))

    responseDict = {}
    # always add encrypted provider id in response
    responseDict["id"] = serviceObj.encryptedid
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
                if 'videoKey' in res.keys():
                    responseDict["result"] = api.status_stop_success
                    responseDict["videokey"] = res["videoKey"]
                else:
                    responseDict["result"] = api.status_upload_fail
                    responseDict["fail_response"] = res
                    
                responseDict["chapterid"] = serviceObj.chapterid
                responseDict["publish"] = serviceObj.publish

                responseDict["id"] = serviceObj.clientid
                httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))
        elif command == api.command_upload_logs:
            lineCount = 50
            if 'lineCount' in messageDict.keys():
                lineCount = messageDict["lineCount"]
            logData = ""
            with open(logger.logFileName) as fin:
                logData = fin.readlines()[-lineCount:]
            responseDict["logs"] = logData
            print(json.dumps(responseDict))
            httpReq.send(serviceObj.url, "/cdn/logData/", json.dumps(responseDict))
        elif command == api.command_get_recent_capture_file_details:
            if serviceObj.capture.outputFileName != "":
                responseDict['filePath'] = str(serviceObj.capture.outputFileName)
            else:
                list_of_files = glob.glob( serviceObj.capture.outputFolder + r'\*.mp4')
                responseDict['filePath'] = max(list_of_files, key=os.path.getctime)

            responseDict["id"] = serviceObj.scheduleid
            responseDict["chapterid"] = serviceObj.chapterid
            responseDict["publish"] = serviceObj.publish
            httpReq.send(serviceObj.url, "/schedule/getFileDetails/" + str(serviceObj.scheduleid), json.dumps(responseDict))
        elif command == api.command_upload_file:
            filePath = messageDict["filePath"]
            
            res = serviceObj.uploadFileToCDN(filePath)
            if 'videoKey' in res.keys():
                responseDict["result"] = api.status_upload_sucess
                responseDict["videokey"] = res["videoKey"]
            else:
                responseDict["result"] = api.status_upload_fail
                responseDict["fail_response"] = res

            responseDict["chapterid"] = messageDict["chapterid"]
            responseDict["publish"] = messageDict["publish"]
            responseDict["id"] = messageDict["id"]
            httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))
            
        elif command == api.command_check_client_active:
            responseDict['result'] = api.status_client_active
            httpReq.send(serviceObj.url, "/cdn/clientState/", json.dumps(responseDict))
    else:
        LOG.warn("Unhandled command: " + str(messageDict.keys()))

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
        self.ffmpegProcName = "ffmpeg.exe"

        self.uploadRetryCount = 5
       
        self.checkFolderInterval = 60*60*1 # 1 hours

        try:
            self.deleteContent = config.getboolean("config", "deleteContent")
            self.waitBeforeDelete = int(config.get("config", "waitBeforeDelete"))
            self.outputFolder = config.get("config","outputFolder")

            self.debug = bool(int(config.get("config", "debug")))
        except:
            pass

    def close(self):
        self.wsclient.close()

    def checkAndCleanCapturedData(self):
        time_in_secs = time.time() - (self.waitBeforeDelete * 24 * 60 * 60)
        for root, dirs, files in os.walk(self.outputFolder):
            for file_ in files:
                try:
                    full_path = os.path.join(root, file_)
                    stat = os.stat(full_path)
                    if stat.st_mtime <= time_in_secs:
                        os.remove(full_path)
                except Exception as ex:
                    LOG.error("Exception in cleaning up the output folder: " + str(ex))
                    pass

    def checkAndKillProcess(self):
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() == self.ffmpegProcName:
                proc.kill()

    def startCapture(self):
        if self.capturing:
            LOG.warn ("Already capturing")
            return

        self.capturing = True
        self.captureStartTime = int(round(time.time()))
        self.capture.startCapturing()

    def uploadFileToCDN(self, filePath):
        LOG.info ("Uploading file to server: " + str(filePath))
        retryCount = 0
        uploadResponse = {}
        if not os.path.isfile(filePath):
            uploadResponse['fail_reason'] = "Invalid file path : " + str(filePath)
            return uploadResponse 

        if os.stat(filePath).st_size == 0:
            uploadResponse['fail_reason'] = "File size is 0 bytes: " + str(filePath)
            return uploadResponse

        while retryCount < self.uploadRetryCount:
            try:
                uploadResponse = self.upload.uploadVideoJW(filePath)
                LOG.info ("Uploading done")
                LOG.debug("Video Server response: " + str(uploadResponse))
                break
            except Exception as ex:
                LOG.error("Exception in uploading the file: " + str(ex))
                uploadResponse['fail_reason'] = str(ex)
                retryCount += 1
                continue
        return uploadResponse


    def stopCapture(self):
        if not self.capturing:
            self.checkAndKillProcess()
            LOG.warn ("No active capturing")
            return {"videoKey": None}

        self.capturing = False
        self.timeout = 0
        self.capture.stopCapturing()
        time.sleep(5)
        
        uploadResponse = self.uploadFileToCDN(self.capture.outputFileName)
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

        waitCounterForCleaningFiles = self.checkFolderInterval
        while True:
            time.sleep(1)
            if self.capturing and self.timeout > 0:
                timeDiff = int(round(time.time())) - self.captureStartTime
                if timeDiff >= self.timeout:
                    responseDict = {}
                    LOG.info ("Timeout stopping the capturing")
                    sendCaptureResponse(False)
                    res = self.stopCapture()
                    if 'videoKey' in res.keys():
                        responseDict["result"] = api.status_stop_success
                        responseDict["videokey"] = res["videoKey"]
                    else:
                        responseDict["result"] = api.status_upload_fail
                        responseDict["fail_response"] = res

                    responseDict["chapterid"] = self.chapterid
                    responseDict["publish"] = self.publish
                    httpReq.send(self.url, "/cdn/saveClientSession/", json.dumps(responseDict))
            
            waitCounterForCleaningFiles += 1
            if waitCounterForCleaningFiles > self.checkFolderInterval:
                waitCounterForCleaningFiles = 0
                if self.deleteContent:
                    self.checkAndCleanCapturedData()

				

def main():
    global serviceObj
    serviceObj = ClientService()
    serviceObj.run()

if __name__ == "__main__":
    main()

