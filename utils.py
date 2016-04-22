import hashlib
import os
import chardet
import queries


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
        #encoding = chardet.detect(password)
        #err = None
        #if encoding['encoding'] != 'ascii':
        #    err = 'Your password contains non-ascii encoded characters.'
        err = None
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
            err = 'Your password should not contain special characters.'
        return err

    @staticmethod
    def authenticate(token, conn):
        q = conn.execute(queries.QUERY_SELECT_USER_BY_TOKEN.format(token)).cursor.fetchall()
        if q:
            return q[0][6]
        else:
            return False

    @staticmethod
    def validate_role(role):
        if role == "admin" or role == "regular":
            return True
        else:
            return False
