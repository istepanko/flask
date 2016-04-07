import hashlib
import os
import chardet
from functools import wraps
from flask import request, Response



class Utils:
    def __init__(self):
        pass

    @staticmethod
    def generate_token():
        access_token = hashlib.sha1(os.urandom(128)).hexdigest()
        return access_token

    @staticmethod
    def pass_check(password):
        password = str(password)
        encoding = chardet.detect(password)
        err = None
        if encoding['encoding'] != 'ascii':
            err = 'Your password contains non-ascii encoded characters.'
        else:
            if password.isalnum():
                valid = any(a.isalpha() for a in password) and any(b.isdigit() for b in password) and any(
                    c.islower() for c in password) and any(d.isupper() for d in password)
                if valid:
                    pass
                else:
                    err = 'Your password should contain at least one digit, one small letter and one capital letter.'
                if len(password) in range(8, 13):
                    pass
                else:
                    err = 'Your password should be from 8 to 12 characters.'
            else:
                err = 'Your password shouldn\'t contain special characters.'
        return err

    @staticmethod
    def check_auth(login, password):  #This function is called to check if a username / password combination is valid.
        return login == 'admin' and password == 'secret'

    @staticmethod
    def authenticate():   #Sends a 401 response that enables basic auth
        return Response("Could not verify your access level for that URL.\n You have to login with proper credentials", 401, {'WWW-Authenticate': 'Token realm="Authentication Required"'})

    @staticmethod
    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated