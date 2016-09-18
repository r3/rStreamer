from flask import Flask
from flask_restful import Resource, Api


app = Flask(__name__)
api = Api(app)


class DummyResource(Resource):
    def get(self):
        return {}


class ViewSubs(Resource):
    def get(self, subs):
        selected = subs.split('+')
        return {
            'SubsSelected': selected
        }


api.add_resource(DummyResource, '/')
api.add_resource(ViewSubs, '/<string:subs>')

if __name__ == '__main__':
    app.run(debug=True)
