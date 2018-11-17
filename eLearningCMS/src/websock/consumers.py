from channels.generic.websocket import WebsocketConsumer
import json
from . import api

class ClientConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        result = text_data_json["result"]

