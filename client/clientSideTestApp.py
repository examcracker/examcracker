from __future__ import print_function
import captureFeed
import uploadVideo
import websocketClient
import configparser
import os
import time

class clienApp:
	def __init__(self):
		dir_path = os.path.dirname(os.path.realpath(__file__))
		config = configparser.ConfigParser()
		config.readfp(open(os.path.join(dir_path, 'arguments.cfg')))
		
		self.clientId = config.get("config","clientId")
		
		self.capture = captureFeed.captureFeed(self.clientId)
		self.upload = uploadVideo.uploadVideo(self.clientId)
		self.wsClient = websocketClient.clientWebsocket(self.clientId)
		
	def run(self):
		flag = True
		self.capture.startCapturing()
		time.sleep(60)
		self.capture.stopCapturing()
		uploadResponse = self.upload.uploadVideoJW(self.capture.outputFileName)
		print ("uploadResponse: ", uploadResponse)
		#while flag:
			

def main():
	app = clienApp()
	app.run()

if __name__ == "__main__":
	main()