from flask import Flask, render_template, Response
from flask_restful import Resource, Api
import json
from sqlalchemy import create_engine


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
        query = 'SELECT * FROM users'
        conn = engine.connect()
        r = conn.execute(query).cursor.fetchall()
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
        query = 'SELECT * FROM users WHERE uuid = %s' % uuid
        conn = engine.connect()
        r = conn.execute(query).cursor.fetchall()
        if r:
            user = dict()
            user['uuid'] = r[0][0]
            user['email'] = r[0][1]
            user['firstname'] = r[0][2]
            user['lastname'] = r[0][3]
            return user, 200
        else:
            return {'errorMessage': 'User not found.'}, 404

api.add_resource(Users, '/api/v1/users')
api.add_resource(User, '/api/v1/users/<uuid>')

if __name__ == '__main__':
    application.run(host='0.0.0.0')
