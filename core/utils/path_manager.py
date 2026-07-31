import os
import sys


class PathManager:


    @staticmethod
    def root():

        if getattr(
            sys,
            "frozen",
            False
        ):

            return sys._MEIPASS


        return os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )



    @staticmethod
    def get(
        path
    ):

        return os.path.join(

            PathManager.root(),

            path

        )