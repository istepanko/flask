import hashlib
import os


class Utils:
    def __init__(self):
        pass

    @staticmethod
    def generate_token():
        access_token = hashlib.sha1(os.urandom(128)).hexdigest()
        return access_token
