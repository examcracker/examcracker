from channels.generic.websocket import WebsocketConsumer
import json
from . import api
import cdn

# list of connected clients through web socket
connectedConsumerClients = {}

class ClientConsumer(WebsocketConsumer):
    id = None

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        global connectedConsumerClients
        connectedConsumerClients.pop(self.id, None)

    def receive(self, text_data):
        print(text_data)
        message_json = json.loads(text_data)

        if "message" in message_json.keys():
            message = message_json["message"]
            self.send(text_data=json.dumps({"message": message}))
        elif "id" in message_json.keys():
            global connectedConsumerClients
            self.id = message_json["id"]
            connectedConsumerClients[self.id] = self
            self.send(text_data=json.dumps({"id": self.id}))
        elif "result" in message_json.keys():
            result = message_json["result"]
        elif "upload" in message.keys():
            videokey = message["videokey"]
            chapterid = message["chapterid"]
            self.send(cdn.views.saveSession(videokey, chapterid))

    def startcourse(self, chapterid):
        msgDict = {}
        msgDict["command"] = api.command_start
        msgDict["chapterid"] = chapterid
        self.send(text_data=json.dumps(msgDict))

    def stopcourse(self, chapterid):
        msgDict = {}
        msgDict["command"] = api.command_stop
        msgDict["chapterid"] = chapterid
        self.send(text_data=json.dumps(msgDict))

