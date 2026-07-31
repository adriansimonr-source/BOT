import platform
import sys



class SystemInfo:


    def __init__(self):

        self.system = platform.system()

        self.release = platform.release()

        self.version = platform.version()

        self.machine = platform.machine()





    def is_windows(self):

        return self.system == "Windows"





    def is_linux(self):

        return self.system == "Linux"





    def is_windows_10(self):

        if not self.is_windows():

            return False


        return sys.getwindowsversion().build < 22000





    def is_windows_11(self):

        if not self.is_windows():

            return False


        return sys.getwindowsversion().build >= 22000





    def get_platform_name(self):


        if self.is_windows_11():

            return "Windows 11"


        if self.is_windows_10():

            return "Windows 10"


        if self.is_linux():

            return "Linux"


        return self.system





    def get_info(self):

        return {

            "system": self.system,

            "release": self.release,

            "version": self.version,

            "machine": self.machine,

            "platform": self.get_platform_name()

        }