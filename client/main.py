import os
import sys
import http
import thread
import service
import signal

serviceObj = None

def sig_handler(signum, frame):
    serviceObj.stop()

signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT, sig_handler)

def main():
    try:
        serviceObj = service.clientService()
        serviceObj.threadObj.join()
    except KeyboardInterrupt:
        serviceObj.stop()


if __name__ == '__main__':
    main()