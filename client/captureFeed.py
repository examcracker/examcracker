from __future__ import print_function
import configparser
import os
import sys
import subprocess
import signal
import time
import logger
import ctypes

class captureFeed:
    def __init__(self, clientId, configPath, ffmpegPath):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        # Log file
        self.LOG = logger.getLogFile(__name__)

        config = configparser.ConfigParser()
        config.readfp(open(configPath))

        self.videoSource = config.get("source","video")
        self.audioSource = config.get("source","audio")
        self.ffmpegPath = ffmpegPath

        self.videoResolution = config.get("config","videoResolution")
        self.videoFramerate = config.get("config","videoFramerate")
        self.captureBitRate = config.get("config","captureBitRate")

        self.outputFolder = config.get("config","outputFolder")
        self.loglevel = config.get("config","loglevel")

        self.outputFileName = ''
		
        # capturing timeout in seconds
        self.timeout = 30
        self.clientId = clientId
        self.mediaServer = None
        self.mediaServerApp = None
        self.liveStreamName = ''
        self.liveFlag = False

        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    
    def fillMediaServerSettings(self, mediaServer, mediaServerApp, liveFlag, liveStreamName):
        self.mediaServer = mediaServer
        self.mediaServerApp = mediaServerApp
        self.liveStreamName = liveStreamName
        self.liveFlag = liveFlag

    def setCapturingTimeout(self, timeout):
        self.timeout = timeout

    def startCapturing(self):

        self.outputFileName = os.path.join(self.outputFolder, time.strftime("%c").replace(':', '_').replace(' ','_') + '.mp4')
        if self.mediaServer != None and self.liveFlag == True:
            self.outputFileName = self.outputFileName.replace('\\','/')
            scheduleid = self.liveStreamName.split('__')[1]
            rtmpUrl = 'rtmp://'+self.mediaServer+'/'+self.mediaServerApp+'/'+self.liveStreamName+'?providerid='+self.clientId+'&scheduleid='+scheduleid
            self.LOG.debug(rtmpUrl)
            self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, '-threads', '2', '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p' ,'-f', 'tee', '-flags', '+global_header', '-map', '0:v', '-map', '0:a', r'[select=v,\'a:0\':f=flv]{}|{}'.format(rtmpUrl, self.outputFileName), '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            self.LOG.info("Start streaming")
            #time.sleep(2)
            #result = self.kernel32.AttachConsole(self.ffmpegProc.pid)
            #if not result:
            #    err = ctypes.get_last_error()
            #    self.LOG.error("Could not allocate console. Error code:" + err)
        else:
            self.LOG.info("Live streaming flag is false")
            if self.videoFramerate:
                self.LOG.info("Start capturing")
                self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, shell=True)
                time.sleep(2)
                result = self.kernel32.AttachConsole(self.ffmpegProc.pid)
                if not result:
                    err = ctypes.get_last_error()
                    self.LOG.error("Could not allocate console. Error code:" + err)
            else:
                self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow','-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    def stopCapturing(self):
    	try:
            os.kill(self.ffmpegProc.pid, signal.CTRL_BREAK_EVENT)
            waitCount = 0
            retryCount = 0
            while self.ffmpegProc.poll() is None:
                time.sleep(0.5)
                waitCount += 1
                if waitCount > 60:
                    if retryCount < 4:
                        os.kill(self.ffmpegProc.pid, signal.CTRL_BREAK_EVENT)
                        retryCount += 1
                    else:
                        self.LOG.error("Not able to kill ffmpeg process")
                        break
                    waitCount = 0
    	except Exception as ex:
            self.LOG.error("Exception in killing ffmpeg process: "+ str(ex))
			
	
	
def main():
    capture = captureFeed("testId", r"C:\backup\examcracker\client\arguments.cfg", r"C:\backup\examcracker\client\ffmpeg.exe")
    print ("Start capturing video")
    capture.startCapturing()
    time.sleep(capture.timeout)
    print ("Stop capturing video")
    capture.stopCapturing()
    print ("Done")

if __name__ == "__main__":
    main()
