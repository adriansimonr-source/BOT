from core.system.system_info import SystemInfo



class CaptureSelector:


    def __init__(self):

        self.system = SystemInfo()





    def get_capture_method(self):


        if self.system.is_windows():

            return "wgc"



        if self.system.is_linux():

            return "x11"



        return None