from __future__ import print_function
import configparser
import os
import sys
import subprocess
import signal
import time
import logger

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

        self.ffmpegProcLive = None
    
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
            rtmpUrl = 'rtmp://'+self.mediaServer+'/'+self.mediaServerApp+'/'+self.liveStreamName
            self.LOG.debug(rtmpUrl)
            self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, '-threads', '2', '-c:v', 'libx264', '-c:a', 'aac', '-f', 'tee', '-flags', '+global_header', '-map', '0:v', '-map', '0:a', r'[select=v \'a:0\':f=flv]{}|{}'.format(rtmpUrl, self.outputFileName), '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            self.LOG.info("Start streaming")
        else:
            self.LOG.info("Live streaming flag is false")
            if self.videoFramerate:
                self.LOG.info("Start capturing")
                self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow','-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    def stopCapturing(self):
    	try:
            if self.ffmpegProcLive:
                os.kill(self.ffmpegProcLive.pid, signal.CTRL_BREAK_EVENT)
            os.kill(self.ffmpegProc.pid, signal.CTRL_BREAK_EVENT)
    	except Exception as ex:
            self.LOG.error("Exception in killing ffmpeg process: ", str(ex))
			
	
	
def main():
    capture = captureFeed("testId")
    print ("Start capturing video")
    capture.startCapturing()
    time.sleep(capture.timeout)
    print ("Stop capturing video")
    capture.stopCapturing()
    print ("Done")

if __name__ == "__main__":
    main()
