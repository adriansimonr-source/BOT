import ctypes
from ctypes import wintypes

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400


class MemoryReader:

    def __init__(self):
        self.handle = None

    def open_process(self, pid: int) -> bool:

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self.handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
            False,
            pid
        )

        return self.handle != 0

    def close(self):

        if self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None

    def is_connected(self):

        return self.handle is not None