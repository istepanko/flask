from flask import Flask, render_template, Response
from flask_restful import Resource, Api
import json
from sqlalchemy import create_engine
import queries
import constants


application = Flask(__name__)
api = Api(application)
application.debug = True


DB_STRING = 'mysql+pymysql://%s:%s@%s:%s/%s' % ('user', 'password', 'projectdb.cv6b9gyk6jxg.us-west-1.rds.amazonaws.com', 3306, 'db1')
engine = create_engine(DB_STRING, pool_recycle=3600)


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
            return {'errorMessage': 'User not found.'}, 404

    def delete(self, uuid):
        conn = engine.connect()
        q = conn.execute(queries.QUERY_SELECT_USER_BY_UUID.format(uuid))
        r = q.cursor.fetchall()
        if not r:
            json_body = json.dumps({'errorMessage': 'User not found.'})
            response = Response(response=json_body, status=404)
            return response
        else:
            #conn.execute(queries.QUERY_DELETE_USER_BY_UUID.format(uuid))
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
