import json
import uuid
from utils import Utils as Ut
from flask_restful import Resource, Api, reqparse
from sqlalchemy import create_engine
import queries
from flask import Flask, render_template, Response
from validate_email import validate_email

application = Flask(__name__)
api = Api(application)
application.debug = True


DB_STRING = 'mysql+pymysql://%s:%s@%s:%s/%s' % ('user', 'password', 'projectdb.cv6b9gyk6jxg.us-west-1.rds.amazonaws.com', 3306, 'db1')
engine = create_engine(DB_STRING, pool_recycle=3600)
utils = Ut()    # what's that?


@application.route('/', methods=['GET'])
def index():
    return render_template('index.html')


class Users(Resource):
    def get(self):
        conn = engine.connect()
        r = conn.execute(queries.QUERY_SELECT_ALL_USERS).cursor.fetchall()
        users = dict()
        users['users'] = list()

        for row in r:
            user = dict()
            user['uuid'] = row[0]
            user['email'] = row[1]
            user['firstname'] = row[2]
            user['lastname'] = row[3]
            user['password'] = row[4]
            user['token'] = row[5]
            users['users'].append(user)
        return users, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, location='json')
        parser.add_argument('firstname', type=str, location='json')
        parser.add_argument('lastname', type=str, location='json')
        parser.add_argument('password', type=str, location='json')
        args = parser.parse_args(strict=True)
        for key in args:
            if args[key] is None:
                json_body = json.dumps({'errorMessage': '{0} is required.'.format(key)})
                response = Response(response=json_body, status=400)
                return response

        email = args['email']
        if not validate_email(email):
            json_body = json.dumps({'errorMessage': 'Email is not valid.'})
            response = Response(response=json_body, status=400)
            return response

        firstname = args['firstname']
        lastname = args['lastname']
        password = args['password']

        conn = engine.connect()
        r = conn.execute(queries.QUERY_SELECT_USER_BY_EMAIL.format(email)).cursor.fetchall()
        if r:
            json_body = json.dumps({'errorMessage': 'Email already exists.'})
            response = Response(response=json_body, status=409)
            return response

        new_uuid = uuid.uuid1()
        token = utils.generate_token()
        conn.execute(queries.QUERY_INSERT_USER.format(new_uuid, email, firstname, lastname, password, token))
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
        args = parser.parse_args(strict=True)

        conn = engine.connect()
        q = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid)).cursor.fetchall()
        if not q:
            json_body = json.dumps({'errorMessage': 'User not found.'})
            response = Response(response=json_body, status=404)
            return response
        token = q[0][5]
        if args['email']:
            r = conn.execute(queries.QUERY_SELECT_USER_BY_EMAIL.format(args['email'])).cursor.fetchall()
            email = args['email']
            if r and r[0][0] != uuid:
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
            res = utils.pass_check(password)
            if res:
                json_body = json.dumps({'errorMessage': res})
                response = Response(response=json_body, status=400)
                return response
            if password != q[0][4]:
                token = utils.generate_token()
        else:
            password = q[0][4]

        conn.execute(queries.QUERY_UPDATE_USER.format(email, firstname, lastname, password, token, uuid))

        q = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid)).cursor.fetchall()
        user = dict()
        user['email'] = q[0][1]
        user['firstname'] = q[0][2]
        user['lastname'] = q[0][3]
        json_body = json.dumps(user)
        response = Response(response=json_body, status=200)
        return response


api.add_resource(Users, '/api/v1/users')
api.add_resource(User, '/api/v1/users/<uuid>')


if __name__ == '__main__':
    application.run(host='0.0.0.0')

#PUT         # curl 'http://0.0.0.0:5000/api/v1/users/180e3768-e430-11e5-bb28-acbc32cf3ae5' -d '{"email": "ilya2.email@icloud.com"}' -H 'Content-Type: application/json' -XPUT -v
#POST        # curl 'http://0.0.0.0:5000/api/v1/users' -d '{"email": "ilya.email@icloud.com", "firstname": "Ilya", "lastname": "Stepanko", "password": "testpass"}' -H 'Content-Type: application/json' -XPOST -v
#GET ALL     # curl 'http://0.0.0.0:5000/api/v1/users' -v
#GET BY UUID # curl 'http://0.0.0.0:5000/api/v1/users/180e3768-e430-11e5-bb28-acbc32cf3ae5' -v
#DELETE      # curl 'http://0.0.0.0:5000/api/v1/users/7c2660e6-d9f0-11e5-86ea-a45e60d95013' -XDELETE -v

