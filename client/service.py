import subprocess

class ClientService:
    executable = None

    def __init__(self, executable):
        self.executable = executable

    def run(self):
        subprocess.call(self.executable)
