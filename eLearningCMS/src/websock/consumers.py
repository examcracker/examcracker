from channels.generic.websocket import WebsocketConsumer
import json
from . import api
import cdn

connectedConsumerClients = {}

class ClientConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        print(text_data)
        message_json = json.loads(text_data)

        if "message" in message_json.keys():
            message = message_json["message"]
            self.send(text_data=json.dumps({"message": message}))
        elif "id" in message_json.keys():
            self.send(text_data=json.dumps({"id": message_json["id"]}))
        elif "result" in message_json.keys():
            result = message_json["result"]
        elif "upload" in message.keys():
            videokey = message["videokey"]
            chapterid = message["chapterid"]
            self.send(cdn.views.saveSession(videokey, chapterid))

