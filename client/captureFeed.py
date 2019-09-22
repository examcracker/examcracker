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
        self.liveFlag = False

        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    
    def fillMediaServerSettings(self, mediaServer, mediaServerApp, liveFlag, liveStreamName):
        self.mediaServer = mediaServer
        self.mediaServerApp = mediaServerApp
        self.liveStreamName = liveStreamName
        self.liveFlag = liveFlag

    def setCapturingTimeout(self, timeout):
        self.timeout = timeout

    def checkCapturedFileExist(self):
        return os.path.exists(self.outputFileName)

    def startCapturing(self):
        self.outputFileName = os.path.join(self.outputFolder, time.strftime("%c").replace(':', '_').replace(' ','_') + '.mp4')
		#os.path.join(self.outputFolder, time.strftime("%c").replace(':', '_').replace(' ','_') + '.mp4')
        if self.mediaServer != None and self.liveFlag == True:
            self.outputFileName = self.outputFileName.replace('\\','/')
            scheduleid = self.liveStreamName.split('__')[1]
            rtmpUrl = 'rtmp://'+self.mediaServer+'/'+self.mediaServerApp+'/'+self.liveStreamName+'?providerid='+self.clientId+'&scheduleid='+scheduleid
            self.LOG.info(rtmpUrl)
            self.captureAppLog = open(self.captureAppLogPath, 'w')
            #self.captureAppProc = subprocess.Popen([self.captureAppPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'scale=854x480,setsar=1,yadif', '-b', self.captureBitRate, '-threads', '2', '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p' ,'-f', 'tee', '-flags', '+global_header', '-map', '0:v', '-map', '0:a', r'[select=v,\'a:0\':f=flv]{}|{}'.format(rtmpUrl, self.outputFileName), '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            #self.captureAppProc = subprocess.Popen([self.captureAppPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-b', self.captureBitRate,'-vf', 'scale=720*406,setsar=1,yadif','-threads', '2', '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p' ,'-f', 'tee', '-flags', '+global_header', '-map', '0:v', '-map', '0:a', r'[onfail=ignore]{}|[select=v,\'a:0\':f=fifo:fifo_format=flv:drop_pkts_on_overflow=1:attempt_recovery=1:recovery_wait_time=1:onfail=ignore]{}'.format(self.outputFileName, rtmpUrl), '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            self.captureAppProc = subprocess.Popen([self.captureAppPath, '-f', 'dshow', '-video_size', self.videoResolution, '-rtbufsize','6082560','-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource,'-b:v', self.captureBitRate,'-filter_complex','[0:v]split=2[s0][s1];[s0]scale='+ self.captureResolution +',setsar=1,yadif[v0];[s1]scale='+ self.liveResolution +',setsar=1,yadif[v1]','-threads', '2', '-flags','+global_header','-map','[v0]','-map','[v1]','-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p' ,'-map', '0:a','-preset','fast','-f', 'tee', r'[select=\'v:0,a\']{}|[select=\'v:1,a\':f=fifo:fifo_format=flv:drop_pkts_on_overflow=1:attempt_recovery=1:recovery_wait_time=1:onfail=ignore:queue_size=180:format_opts=flvflags=no_duration_filesize]{}'.format(self.outputFileName, rtmpUrl), '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            self.LOG.info("Start streaming")
            time.sleep(2)
            result = self.kernel32.AttachConsole(self.captureAppProc.pid)
            #result = True
            if not result:
                err = ctypes.get_last_error()
                self.LOG.error("Could not allocate console. Error code:" + str(err))
        else:
            self.LOG.info("Live streaming flag is false")
            if self.videoFramerate:
                self.LOG.info("Start capturing")
                self.captureAppProc = subprocess.Popen([self.captureAppPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                time.sleep(2)
                result = self.kernel32.AttachConsole(self.captureAppProc.pid)
                if not result:
                    err = ctypes.get_last_error()
                    self.LOG.error("Could not allocate console. Error code:" + err)
            else:
                self.captureAppProc = subprocess.Popen([self.captureAppPath, '-f', 'dshow','-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-vf', 'yadif', '-b', self.captureBitRate, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    def killProcessForcefully(self, pid):
        try:
            self.LOG.info("Killing captureApp process forcefully by psutil")
            captureAppHangProcess = psutil.Process(pid)
            captureAppHangProcess.terminate()

        except Exception as ex:
            self.LOG.error("Exception in killing captureApp process by psutil: "+ str(ex))

    def stopCapturing(self):
        try:
            #self.kernel32.FreeConsole()
            os.kill(self.captureAppProc.pid, signal.CTRL_BREAK_EVENT)
            time.sleep(5)
            self.kernel32.FreeConsole()
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
                        self.LOG.info("Retring to free the console")
                        self.kernel32.FreeConsole()
                        retryCount += 1
                    else:
                        self.LOG.error("Not able to kill captureApp process")
                        break
                    waitCount = 0

            if self.captureAppProc.poll() is None:
                self.killProcessForcefully(self.captureAppProc.pid)
            
            self.captureAppLog.close()
        except Exception as ex:
            self.LOG.error("Exception in killing captureApp process: "+ str(ex))
            self.killProcessForcefully(self.captureAppProc.pid)
			
	
	
def main():
    capture = captureFeed("testId", r"C:\backup\examcracker\client\arguments.cfg", r"C:\backup\examcracker\client\captureApp.exe")
    print ("Start capturing video")
    capture.startCapturing()
    time.sleep(capture.timeout)
    print ("Stop capturing video")
    capture.stopCapturing()
    print ("Done")

if __name__ == "__main__":
    main()
