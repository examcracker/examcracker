import os
import sys
import http
import service

serviceObj = None
port = 8000

def main():
    serviceObj = service.ClientService(port)
    serviceObj.run()


if __name__ == '__main__':
    main()