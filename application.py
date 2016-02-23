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
utils = Ut()


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

api.add_resource(Users, '/api/v1/users')
api.add_resource(User, '/api/v1/users/<uuid>')


if __name__ == '__main__':
    application.run(host='0.0.0.0')
