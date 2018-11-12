from websocket_server import WebsocketServer

class ClientService:
    def __init__(self, port=8000):
        self.server = WebsocketServer(port)
        self.server.set_fn_client_left(self.clientConnected)
        self.server.set_fn_client_left(self.clientDisconnected)
        self.server.set_fn_message_received(self.messageReceived)

    def clientConnected(self):
        print("New client connected and was given id %d" % client['id'])

    def clientDisconnected(self, client, server):
        print("Client(%d) disconnected" % client['id'])

    def messageReceived(self,client, server, message):
        print("Client(%d) said: %s" % (client['id'], message))

    def run(self):
        self.server.run_forever()

