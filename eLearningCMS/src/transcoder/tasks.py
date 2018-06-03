from django.conf import settings
import threading
import os
import ffmpy
import time

class mp4Converter(threading.Thread):
    def __init__(self, sessionid, sessionpath):
        threading.Thread.__init__(self)
        self.sessionid = sessionid
        self.mediapath = os.path.join(settings.MEDIA_ROOT, sessionpath)
        self.outputmp4 = os.path.join(os.path.dirname(self.mediapath), str(sessionid) + ".mp4")

    def run(self):
        response = ffmpy.FFmpeg(inputs={self.mediapath: None}, outputs={self.outputmp4: None})
        response.run()
        
def convert_to_mp4(sessionid, sessionpath):
    converter = mp4Converter(sessionid, sessionpath)
    converter.start()
    
