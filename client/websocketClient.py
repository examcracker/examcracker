from __future__ import print_function
import websocket
import threading
import json
from time import sleep

class clientWebsocket:
	def __init__(self, clientId):
		self.clientId = clientId
		