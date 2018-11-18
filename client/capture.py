import sys
import os
import ws
import json

def startCapturing(ws):
    urldict = {}
    urldict["geturl"] = True
    ws.send(json.dumps(urldict))
    pass

def stopCapturing(ws, videokey, chapterid):
    uploaddict = {}
    uploaddict["upload"] = True
    uploaddict["videokey"] = videokey
    uploaddict["chapterid"] = chapterid
    ws.send(json.dumps(uploaddict))
    pass
