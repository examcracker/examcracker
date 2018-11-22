from __future__ import print_function
import configparser
import os
import subprocess
import signal
import time

class captureFeed:
	def __init__(self, clientId):
		dir_path = os.path.dirname(os.path.realpath(__file__))
		config = configparser.ConfigParser()
		config.readfp(open(os.path.join(dir_path, 'arguments.cfg')))
		
		self.videoSource = config.get("source","video")
		self.audioSource = config.get("source","audio")
		self.dir_path = os.path.dirname(os.path.realpath(__file__))
		self.ffmpegPath = os.path.join(self.dir_path, 'ffmpeg.exe')
		
		self.videoResolution = config.get("config","videoResolution")
		self.videoFramerate = config.get("config","videoFramerate")
		
		self.outputFolder = config.get("config","outputFolder")
		
		self.loglevel = config.get("config","loglevel")
		
		# capturing timeout in seconds
		self.timeout = 30
		
		self.clientId = clientId
		
	def setCapturingTimeout(self, timeout):
		self.timeout = timeout
		
	def startCapturing(self):
		self.outputFileName = os.path.join(self.outputFolder, time.strftime("%c").replace(':', '_') + '.mp4')
		if self.videoFramerate:
			print ("Using frame rate and resolution information")
			self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow', '-video_size', self.videoResolution, '-framerate', self.videoFramerate,'-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, '-pix_fmt', 'yuv420p', self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
		else:
			self.ffmpegProc = subprocess.Popen([self.ffmpegPath, '-f', 'dshow','-i', 'video=' + self.videoSource + ':audio=' + self.audioSource, self.outputFileName, '-loglevel', self.loglevel], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

	def stopCapturing(self):
		os.kill(self.ffmpegProc.pid, signal.CTRL_BREAK_EVENT)
	
	
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