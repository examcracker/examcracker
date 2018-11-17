import os
import sys
import myhttp
import service

clientObj = None

def main():
    clientObj = service.ClientService()
    clientObj.run()


if __name__ == '__main__':
    main()
