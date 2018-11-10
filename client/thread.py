from threading import Thread
import time

class CallBackObject:
    def execute(self):
        print("wrong area")
        return
    def terminate(self):
        print("wrong terminate")
        return True

class AppThread(Thread):
    def __init__(self, callback, recur=False, timeout=0):
        super().__init__()
        self.recur = recur
        self.timeout = timeout
        self.callback = callback

    def run(self):
        self.callback.execute()
        if not self.recur:
            return
        else:
            while not self.callback.terminate():
                time.sleep(self.timeout)
                self.callback.execute()
