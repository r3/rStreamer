from flask import Flask
from flask_restful import Resource, Api


app = Flask(__name__)
api = Api(app)


class DummyResource(Resource):
    def get(self):
        return {}


api.add_resource(DummyResource, '/')

if __name__ == '__main__':
    app.run(debug=True)
