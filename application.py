import json
import uuid
from utils import Utils as Ut
from flask_restful import Resource, Api, reqparse
from sqlalchemy import create_engine
import queries
from flask import Flask, render_template, Response
from validate_email import validate_email


import chardet


application = Flask(__name__)
api = Api(application)
application.debug = True


DB_STRING = 'mysql+pymysql://%s:%s@%s:%s/%s' % ('user', 'password', 'projectdb.cv6b9gyk6jxg.us-west-1.rds.amazonaws.com', 3306, 'db1')
engine = create_engine(DB_STRING, pool_recycle=3600)
utils = Ut()


@application.route('/', methods=['GET'])
def index():
    return render_template('index.html')


class Users(Resource):    #What means Resource imported from flask_restful?
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('authorization', type=str, location='headers')
        args = parser.parse_args(strict=True)
        for key in args:
            if args[key] is None:
                json_body = json.dumps({'errorMessage': '{0} is required.'.format(key)})
                response = Response(response=json_body, status=400)
                return response

        conn = engine.connect()
        role = utils.authenticate(args['authorization'], conn)
        users = dict()
        users['users'] = list()
        if not role:
            json_body = json.dumps({'errorMessage': 'Invalid token.'})
            response = Response(response=json_body, status=401)
            return response
        elif role != 'admin':
            r = conn.execute(queries.QUERY_SELECT_USER_BY_TOKEN.format(args['authorization'])).cursor.fetchall()
        else:
            r = conn.execute(queries.QUERY_SELECT_ALL_USERS).cursor.fetchall()

        for row in r:
            user = dict()
            user['uuid'] = row[0]
            user['email'] = row[1]
            user['firstname'] = row[2]
            user['lastname'] = row[3]
            user['password'] = row[4]
            user['token'] = row[5]
            user['role'] = row[6]
            users['users'].append(user)
        return users, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, location='json')
        parser.add_argument('firstname', type=str, location='json')
        parser.add_argument('lastname', type=str, location='json')
        parser.add_argument('password', type=str, location='json')
        parser.add_argument('role', type=str, location='json')
        parser.add_argument('authorization', type=str, location='headers')
        args = parser.parse_args(strict=True)
        for key in args:
            if args[key] is None:
                json_body = json.dumps({'errorMessage': '{0} is required.'.format(key)})
                response = Response(response=json_body, status=400)
                return response
        conn = engine.connect()
        role = utils.authenticate(args['authorization'], conn)
        if not role:
            json_body = json.dumps({'errorMessage': 'Invalid token.'})
            response = Response(response=json_body, status=401)
            return response
        elif role != 'admin':
            json_body = json.dumps({'errorMessage': 'Not enough permissions.'})
            response = Response(response=json_body, status=403)
            return response
        email = args['email']
        if not validate_email(email):
            json_body = json.dumps({'errorMessage': 'Email is not valid.'})
            response = Response(response=json_body, status=400)
            return response

        firstname = args['firstname']
        lastname = args['lastname']
        password = args['password']
        role = args['role']
        if not Ut.validate_role(role):
            json_body = json.dumps({'errorMessage': 'Role can be Admin or Regular. Please provide correct role'})
            response = Response(response=json_body, status=403)
            return response

        r = conn.execute(queries.QUERY_SELECT_USER_BY_EMAIL.format(email)).cursor.fetchall()
        if r:
            json_body = json.dumps({'errorMessage': 'Email already exists.'})
            response = Response(response=json_body, status=409)
            return response

        new_uuid = uuid.uuid1()
        token = Ut.generate_token()
        conn.execute(queries.QUERY_INSERT_USER.format(new_uuid, email, firstname, lastname, password, token, role))
        r = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(new_uuid)).cursor.fetchall()
        if r:
            response = Response(status=201)
            return response
        else:
            json_body = json.dumps({'errorMessage': 'User not created, something went wrong.'})
            response = Response(response=json_body, status=500)
            return response


class User(Resource):
    def get(self, uuid):
        conn = engine.connect()
        r = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid)).cursor.fetchall()
        if r:
            user = dict()
            user['uuid'] = r[0][0]
            user['email'] = r[0][1]
            user['firstname'] = r[0][2]
            user['lastname'] = r[0][3]
            return user, 200
        else:
            json_body = json.dumps({'errorMessage': 'User not found.'})
            response = Response(response=json_body, status=404)
            return response

    def delete(self, uuid):
        conn = engine.connect()
        q = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid))
        r = q.cursor.fetchall()
        if not r:
            json_body = json.dumps({'errorMessage': 'User not found.'})
            response = Response(response=json_body, status=404)
            return response
        else:
            conn.execute(queries.QUERY_DELETE_USER_BY_UUID.format(uuid))
            q = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid))
            r = q.cursor.fetchall()
            if not r:
                response = Response(status=200)
                return response
            else:
                json_body = json.dumps({'errorMessage': 'User not deleted, something went wrong.'})
                response = Response(response=json_body, status=500)
                return response

    def put(self, uuid):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, location='json')
        parser.add_argument('firstname', type=str, location='json')
        parser.add_argument('lastname', type=str, location='json')
        parser.add_argument('password', type=str, location='json')
        parser.add_argument('role', type=str, location='json')
        parser.add_argument('authorization', type=str, location='headers')
        args = parser.parse_args(strict=True)

        if args['authorization'] is None:
            json_body = json.dumps({'errorMessage': '{0} is required.'.format('authorization')})
            response = Response(response=json_body, status=400)
            return response

        if args['email']:
            if not validate_email(args['email']):
                json_body = json.dumps({'errorMessage': 'Email is not valid.'})
                response = Response(response=json_body, status=400)
                return response

        conn = engine.connect()
        r = utils.authenticate(args['authorization'], conn)
        if not r:
            json_body = json.dumps({'errorMessage': 'Invalid token.'})
            response = Response(response=json_body, status=401)
            return response

        q = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid)).cursor.fetchall()
        if not q:
            json_body = json.dumps({'errorMessage': 'User not found.'})
            response = Response(response=json_body, status=404)
            return response

        if r == 'admin' or args['authorization'] == q[0][5]:
            token = q[0][5]
            if args['email']:
                email = args['email']
                conn = engine.connect()
                b = conn.execute(queries.QUERY_SELECT_USER_BY_EMAIL.format(email)).cursor.fetchall()
                if b and b[0][0] != uuid:
                    json_body = json.dumps({'errorMessage': 'Email already exists.'})
                    response = Response(response=json_body, status=409)
                    return response
                if email != q[0][1]:
                    token = utils.generate_token()
            else:
                email = q[0][1]

            if args['firstname']:
                firstname = args['firstname']
            else:
                firstname = q[0][2]

            if args['lastname']:
                lastname = args['lastname']
            else:
                lastname = q[0][3]

            if args['password']:
                password = args['password']
                err = utils.pass_check(password)
                if err:
                    json_body = json.dumps({'errorMessage': err})
                    response = Response(response=json_body, status=400)
                    return response
                if password != q[0][4]:
                    token = utils.generate_token()
            else:
                password = q[0][4]

            if args['role']:
                if not Ut.validate_role(args['role']):
                    json_body = json.dumps({'errorMessage': 'Role can be Admin or Regular. Please provide correct role'})
                    response = Response(response=json_body, status=403)
                    return response
                else:
                    role = args['role']
            else:
                role = q[0][6]

            conn = engine.connect()
            conn.execute(queries.QUERY_UPDATE_USER.format(email, firstname, lastname, password, token, role, uuid))
            a = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid)).cursor.fetchall()
            if a:
                user = dict()
                user['email'] = a[0][1]
                user['firstname'] = a[0][2]
                user['lastname'] = a[0][3]
                user['password'] = a[0][4]
                user['authorization'] = a[0][5]
                user['role'] = a[0][6]
                return user, 200
            else:
                json_body = json.dumps({'errorMessage': 'User not updated.'})
                response = Response(response=json_body, status=404)
                return response

        else:
            json_body = json.dumps({'errorMessage': 'Not enough permissions.'})
            response = Response(response=json_body, status=403)
            return response



class Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, location='json')
        parser.add_argument('password', type=str, location='json')
        args = parser.parse_args(strict=True)
        for key in args:
            if args[key] is None:
                json_body = json.dumps({'errorMessage': '{0} is required.'.format(key)})
                response = Response(response=json_body, status=400)
                return response
        conn = engine.connect()
        q = conn.execute(queries.QUERY_SELECT_USER_BY_EMAIL.format(args['email'])).cursor.fetchall()
        if q:
            if q[0][4] == args['password']:
                token = utils.generate_token()
                conn.execute(queries.QUERY_UPDATE_TOKEN_BY_EMAIL.format(token, args['email']))
                json_body = json.dumps({'role': q[0][6], 'token': token})
                response = Response(response=json_body, status=200)
                return response
        json_body = json.dumps({'errorMessage': 'Invalid credentials.'})
        response = Response(response=json_body, status=401)
        return response


api.add_resource(Users, '/api/v1/users')
api.add_resource(User, '/api/v1/users/<uuid>')
api.add_resource(Login, '/api/v1/login')

if __name__ == '__main__':
    application.run(host='0.0.0.0')

#PUT          curl 'http://0.0.0.0:5000/api/v1/users/180e3768-e430-11e5-bb28-acbc32cf3ae5' -d '{"email": "ilya2.email@icloud.com"}' -H 'Content-Type: application/json' -XPUT -v
#POST         curl 'http://0.0.0.0:5000/api/v1/users' -d '{"email": "ilya.email12345@icloud.com", "firstname": "Ilya", "lastname": "Stepanko", "password": "tttestpass", "role": "regular"}' -H 'Content-Type: application/json' -H 'authorization: e0eb3604f0ec878c636d7fb282bda6676737ff11' -XPOST -v
#GET BY UUID  curl 'http://0.0.0.0:5000/api/v1/users/180e3768-e430-11e5-bb28-acbc32cf3ae5' -v
#DELETE       curl 'http://0.0.0.0:5000/api/v1/users/7c2660e6-d9f0-11e5-86ea-a45e60d95013' -XDELETE -v
#GET ALL      curl 'http://0.0.0.0:5000/api/v1/users' -v

#GET ALL      curl -H 'authorization: 4f659f9b7ec2072bd8166fb936d5aab6ecec92c1' 'http://0.0.0.0:5000/api/v1/users'