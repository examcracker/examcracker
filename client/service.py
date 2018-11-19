from __future__ import print_function
import captureFeed
import uploadVideo
import configparser
import os
import websocket
import time
import api
import json

def on_message(ws, message):
	responseDict = {}
	messageDict = json.loads(message)

	if "command" in messageDict.keys():
		command = messageDict["command"]
		if command == api.command_start:
			if ws.obj.capturing:
				responseDict["result"] = api.status_capture_started
			else:
				chapterid = messageDict["chapterid"]
				responseDict["result"] = api.status_success
				ws.obj.chapterid = chapterid
				ws.obj.startCapture()
				
		elif command == api.command_stop:
			if not ws.obj.capturing:
				responseDict["result"] = api.status_no_capture_started
			else:
				ws.obj.stopCapture()
				responseDict["result"] = api.status_success

		ws.send(json.dumps(responseDict))
	else:
		print ("Unhandled command: ", messageDict.keys())


def on_error(ws, error):
    print(error)

def on_close(ws):
    pass

class ClientService(object):
	def __init__(self):
		wsclient = None
		capturing = False
		chapterid = None
		videokey = None
		self.wsclient = None
		websocket.enableTrace(True)

		dir_path = os.path.dirname(os.path.realpath(__file__))
		config = configparser.ConfigParser()
		config.readfp(open(os.path.join(dir_path, 'arguments.cfg')))

		self.clientId = config.get("config","clientId")

		self.capture = captureFeed.captureFeed(self.clientId)
		self.upload = uploadVideo.uploadVideo(self.clientId)
		self.wsClient = websocketClient.clientWebsocket(self.clientId)

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
		#uploadResponse = self.upload.uploadVideoJW(self.capture.outputFileName)


	def run(self):
		self.wsclient = websocket.WebSocketApp("ws://127.0.0.1:8000/ws/gyaan/", on_message = on_message, on_close = on_close, on_error = on_error)
		self.wsclient.obj = self
		self.wsclient.run_forever()
		
def main():
	service = ClientService()
	service.run()

if __name__ == "__main__":
	main()

