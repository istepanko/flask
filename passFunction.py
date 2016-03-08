#!/usr/bin/python
# coding=utf-8

import chardet

def pass_check(password):
    password = str(password)
    encoding = chardet.detect(password)
    if encoding['encoding'] != 'ascii':
        valid = False
        print "Your password contains non ascii-encoded characters"
        return valid
    else:
        if password.isalnum():
            valid = any(a.isalpha() for a in password) and any(b.isdigit() for b in password) and any(
                c.islower() for c in password) and any(d.isupper() for d in password)
            if valid:
                pass
            else:
                print "Your password should contain at least one digit, one small letter and one capital letter"
                valid = False
            if len(password) in range(8, 13):
                pass
            else:
                valid = False
                print "Your password should be from 8 to 12 characters"
        else:
            print "Your password shouldn't contain special characters"
            valid = False
    return valid

print pass_check("hgGgg1ggg")