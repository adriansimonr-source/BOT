import psutil


class ProcessManager:

    def __init__(self):
        self.process = None
        self.pid = None

    def find_process(self, process_name: str) -> bool:
        """Busca un proceso por nombre."""

        self.process = None
        self.pid = None

        for proc in psutil.process_iter(["pid", "name"]):

            try:
                name = proc.info["name"]

                if name and name.lower() == process_name.lower():
                    self.process = proc
                    self.pid = proc.info["pid"]
                    return True

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        return False

    def is_connected(self) -> bool:
        return self.process is not None

    def get_pid(self):
        return self.pid

    def get_process(self):
        return self.process

    def get_name(self):
        if self.process is None:
            return ""

        return self.process.info["name"]