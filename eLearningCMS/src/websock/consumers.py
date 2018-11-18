from channels.generic.websocket import WebsocketConsumer
import json
from . import api
import cdn

class ClientConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        message = json.loads(text_data)
        if "result" in message.keys():
            result = message["result"]
        if "upload" in message.keys():
            videokey = message["videokey"]
            chapterid = message["chapterid"]
            self.send(cdn.views.saveSession())
        if "geturl" in message.keys():
            urldict = {}
            urldict["url"] = cdn.views.createVideoUploadURL()
            self.send(json.dumps(urldict))

