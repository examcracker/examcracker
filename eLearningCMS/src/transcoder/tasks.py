from django.conf import settings
import threading
import os
import ffmpy
import time
import subprocess
import multiprocessing
import sys
import signal

class mp4Converter():
    def __init__(self, sessionid, sessionpath):
        threading.Thread.__init__(self)
        self.sessionid = sessionid
        self.mediapath = os.path.join(settings.MEDIA_ROOT, sessionpath)
        self.videomp4 = os.path.join(os.path.dirname(self.mediapath), str(sessionid) + "_whole_v.mp4")
        self.audiomp4 = os.path.join(os.path.dirname(self.mediapath), str(sessionid) + "_whole_a.mp4")
        
    def run(self):
        response = ffmpy.FFmpeg(inputs={self.mediapath: None}, outputs={self.videomp4: ['-map', '0:0'], self.audiomp4: ['-map', '0:1']})
        response.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

class mp4Fragmenter():
    def __init__(self, converter):
        threading.Thread.__init__(self)
        self.converter = converter
        self.fragvideo = os.path.join(os.path.dirname(self.converter.videomp4), str(self.converter.sessionid) + "_v.mp4")
        self.fragaudio = os.path.join(os.path.dirname(self.converter.audiomp4), str(self.converter.sessionid) + "_a.mp4")

    def run(self):
        subprocess.call(['mp4fragment.exe', self.converter.videomp4, self.fragvideo])
        subprocess.call(['mp4fragment.exe', self.converter.audiomp4, self.fragaudio])

def run(sessionid, converter, fragmenter):
    converter.run()
    fragmenter.run()

def process():
    taskQueue.processTask()
    
class processQueue(threading.Thread):
    def __init__(self):
        # leave 2 cores free for webservice
        self.queuesize = multiprocessing.cpu_count() - 2
        self.taskdict = {}
        self.lock = threading.Lock()
        self.event = threading.Event()
        self.clearevent = threading.Event()
        self.runningtasks = 0
        self.running = True

    def signal(self, sessionid):
        self.lock.acquire()
        self.runningtasks = self.runningtasks - 1
        del(self.taskdict[sessionid])
        self.lock.release()
        self.event.set()

    def addTask(self, sessionid, sessionpath):
        converter = mp4Converter(sessionid, sessionpath)
        fragmenter = mp4Fragmenter(converter)
        self.lock.acquire()

        self.taskdict[sessionid] = {}
        self.taskdict[sessionid]['converter'] = converter
        self.taskdict[sessionid]['fragmenter'] = fragmenter

        self.lock.release()
        self.event.set()

    def execute(self, sessionid):
        runnintThread = threading.Thread(target=run, args=[sessionid, self.taskdict[sessionid]['converter'],
                                                        self.taskdict[sessionid]['fragmenter']])
        runnintThread.start()

    def processTask(self):
        while self.running:
            self.event.wait()
            if self.running == False:
                break

            self.lock.acquire()

            while self.runningtasks < self.queuesize:
                if len(list(self.taskdict.keys())) == 0:
                    break
                sessionid = list(self.taskdict.keys())[0]
                self.execute(sessionid)
                self.runningtasks = self.runningtasks + 1
                del(self.taskdict[sessionid])
                self.runningtasks = self.runningtasks - 1

            self.lock.release()
            self.event.clear()

taskQueue = processQueue()
processThread = threading.Thread(target=process)
processThread.start()

def signal_handler(signal, frame):
    taskQueue.running = False
    taskQueue.event.set()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def processSession(sessionid, sessionpath):
    taskQueue.addTask(sessionid, sessionpath)
