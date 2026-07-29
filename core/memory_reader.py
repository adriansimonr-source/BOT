import ctypes

from core.winapi import (
    kernel32,
    PROCESS_VM_READ,
    PROCESS_QUERY_INFORMATION
)


class MemoryReader:

    def __init__(self):

        self.handle = None
        self.pid = None

    def connect(self, pid: int) -> bool:

        self.pid = pid

        self.handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
            False,
            pid
        )

        return self.handle != 0

    def disconnect(self):

        if self.handle:

            kernel32.CloseHandle(self.handle)

            self.handle = None
            self.pid = None

    @property
    def connected(self):

        return self.handle is not None

    def read_int(self, address: int):

        value = ctypes.c_int()

        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(value),
            ctypes.sizeof(value),
            ctypes.byref(bytes_read)
        )

        if not success:
            return None

        return value.value

    def read_float(self, address: int):

        value = ctypes.c_float()

        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(value),
            ctypes.sizeof(value),
            ctypes.byref(bytes_read)
        )

        if not success:
            return None

        return value.value