from __future__ import print_function
import configparser
import os
import sys
import subprocess
import signal
import time
import logger
import ctypes
import psutil

class captureFeed:
    def __init__(self, clientId, configPath, captureAppPath):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        # Log file
        self.LOG = logger.getLogFile(__name__)

        config = configparser.ConfigParser()
        config.readfp(open(configPath))

        self.configPath = configPath

        self.videoSource = config.get("source","video")
        self.audioSource = config.get("source","audio")
        self.captureAppPath = captureAppPath

        self.videoResolution = config.get("config","videoResolution")
        self.videoFramerate = config.get("config","videoFramerate")
        self.captureBitRate = config.get("config","captureBitRate")
        try:
            self.captureResolution = config.get("config","captureResolution")
        except:
            self.captureResolution = '1280*720'

        try:
            self.liveResolution = config.get("config","liveResolution")
        except:
            self.liveResolution = '720*406'

        self.outputFolder = config.get("config","outputFolder")
        self.loglevel = config.get("config","loglevel")

        self.outputFileName = ''

        self.captureAppLogPath = os.path.join(self.dir_path, "Capturing.log")
        self.captureAppLog = None
		
        # capturing timeout in seconds
        self.timeout = 30
        self.clientId = clientId
        self.mediaServer = None
        self.mediaServerApp = None
        self.liveStreamName = ''
        self.liveFlag = 'False'
        self.captureTmpFilePath = 'capture.tmp'

        #self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    
    def fillMediaServerSettings(self, mediaServer, mediaServerApp, liveFlag, liveStreamName):
        self.mediaServer = mediaServer
        self.mediaServerApp = mediaServerApp
        self.liveStreamName = liveStreamName
        if liveFlag == True:
            self.liveFlag = 'True'
        else:
            self.liveFlag = 'False'

    def setCapturingTimeout(self, timeout):
        self.timeout = timeout

    def checkCapturedFileExist(self):
        return os.path.exists(self.outputFileName)

    def startCapturing(self):
        self.outputFileName = os.path.join(self.outputFolder, time.strftime("%c").replace(':', '_').replace(' ','_') + '.mp4')
        self.captureTmpFile = open(self.captureTmpFilePath, 'w')
        self.captureTmpFile.close()

        CREATE_NO_WINDOW = 0x08000000
        self.captureAppProc = subprocess.Popen(['captureFeedApp.exe', self.configPath, self.captureAppPath, self.mediaServer, self.mediaServerApp, self.liveStreamName, self.liveFlag, str(self.timeout), self.captureTmpFilePath, self.clientId, self.outputFileName], creationflags=CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)

    def killProcessForcefully(self, pid):
        try:
            self.LOG.info("Killing captureApp process forcefully by psutil")
            captureAppHangProcess = psutil.Process(pid)
            captureAppHangProcess.terminate()

        except Exception as ex:
            self.LOG.error("Exception in killing captureApp process by psutil: "+ str(ex))

    def stopCapturing(self):
        try:
            os.remove(self.captureTmpFilePath)
            time.sleep(5)
            waitCount = 0
            retryCount = 0
            
            while self.captureAppProc.poll() is None:
                time.sleep(0.5)
                waitCount += 1
                if waitCount > 60:
                    if retryCount < 4:
                        self.LOG.info("Retring to kill the captureApp process")
                        os.kill(self.captureAppProc.pid, signal.CTRL_BREAK_EVENT)
                        time.sleep(3)
                        retryCount += 1
                    else:
                        self.LOG.error("Not able to kill captureApp process")
                        break
                    waitCount = 0

            if self.captureAppProc.poll() is None:
                self.killProcessForcefully(self.captureAppProc.pid)
            
        except Exception as ex:
            self.LOG.error("Exception in killing captureApp process: "+ str(ex))
            self.killProcessForcefully(self.captureAppProc.pid)
			
	
	
def main():
    capture = captureFeed("testId", r"C:\Hemant\Study\examcracker\examcracker\client\arguments.cfg", r"C:\Hemant\Study\examcracker\examcracker\client\captureApp.exe")
    print ("Start capturing video")
    capture.startCapturing()
    time.sleep(capture.timeout)
    print ("Stop capturing video")
    capture.stopCapturing()
    print ("Done")

if __name__ == "__main__":
    main()
