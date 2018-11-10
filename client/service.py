import thread

class serviceObject(thread.CallBackObject):
    def execute(self):
        return

    def terminate(self):
        return self.stop

    def stop(self):
        self.stop = True

    stop = False

class clientService:
    recur = True
    timeout = 60
    threadObj = None
    callbackObj = serviceObject()

    def __init__(self):
        self.threadObj = thread.AppThread(self.callbackObj, self.recur, self.timeout)
        self.threadObj.start()

    def stop(self):
        self.callbackObj.stop()

