from uuid import uuid4

import flask
from flask_restful import Resource, Api

from rStream.libs import reddit


app = flask.Flask(__name__)
api = Api(app)


def take_n(iterable, number):
    return [next(iterable) for __ in range(number)]


class DummyResource(Resource):
    def get(self):
        return {}


class ViewSubs(Resource):
    def get(self, subs):
        selected = subs.split('+')
        stream = reddit.SubredditsStream(selected,
                                         key=lambda x: x.score,
                                         func='get_hot')
        flask.session.id = uuid4()
        flask.g[flask.session.id] = reddit.submission_filter(stream)

        return {
            'SubsSelected': selected
        }


class IterSubs(Resource):
    def get(self, count):
        filtered_stream = flask.g[flask.session.id]
        return flask.jsonify(take_n(filtered_stream, count))


api.add_resource(DummyResource, '/')
api.add_resource(ViewSubs, '/<string:subs>')
api.add_resource(IterSubs, '/next/<int:count>')

if __name__ == '__main__':
    app.run(debug=True)
