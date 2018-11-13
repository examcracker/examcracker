import os
import sys
import http
import service

clientObj = None

def main():
    clientObj = service.ClientService("websock_client.exe")
    clientObj.run()


if __name__ == '__main__':
    main()