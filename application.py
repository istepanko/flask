from flask import Flask, render_template, Response
from flask_restful import Resource, Api
import json
from sqlalchemy import create_engine


application = Flask(__name__)
api = Api(application)
application.debug = True


DB_STRING = 'mysql+pymysql://%s:%s@%s:%s/%s' % ('user', 'password', 'projectdb.ckapg67klplg.us-west-1.rds.amazonaws.com', 3306, 'db1')
engine = create_engine(DB_STRING, pool_recycle=3600)
query = 'SELECT * FROM users'
conn = engine.connect()
r = conn.execute(query).cursor.fetchall()


@application.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@application.route('/api', methods=['GET'])
def index1():
    return render_template('index1.html')


class User(Resource):
    def get(self):
        return {'test':'test'}, 200

api.add_resource(User, '/api/v1/users')

if __name__ == '__main__':
    application.run(host='0.0.0.0')
