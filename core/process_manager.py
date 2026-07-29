import psutil


class ProcessManager:

    def __init__(self):
        self.process = None
        self.pid = None

    def find_process(self, process_name: str) -> bool:

        self.process = None
        self.pid = None

        for proc in psutil.process_iter(["pid", "name"]):

            try:
                if proc.info["name"].lower() == process_name.lower():

                    self.process = proc
                    self.pid = proc.info["pid"]
                    return True

            except (psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess):
                pass

        return False

    def is_connected(self):

        return self.process is not None

    def get_pid(self):

        return self.pid

    def get_process(self):

        return self.process