from flask import Flask, render_template, Response
from flask_restful import Resource, Api
import json


application = Flask(__name__)
api = Api(application)


@application.route('/', methods=['GET'])
def index():
    return render_template('index.html')


class User(Resource):
    def get(self):
        resp = Response(json.dumps({'test':'test'}))
        resp.status_code = 200
        return resp

api.add_resource(User, '/api/v1/users')

if __name__ == '__main__':
    application.run(host='0.0.0.0')
