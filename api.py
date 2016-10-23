from uuid import uuid4

import flask
from flask_restful import Resource, Api

from rStream.libs import reddit


app = flask.Flask(__name__)
api = Api(app)
content_store = dict()


def take_n(iterable, number):
    results = []
    for __ in range(number):
        try:
            item = next(iterable)
            results.append(item)
        except StopIteration:
            break

    return results


class DummyResource(Resource):
    def get(self):
        return {}


class ViewSubs(Resource):
    def get(self, subs):
        selected = subs.split('+')
        stream = reddit.SubredditsStream(selected,
                                         key=lambda x: x.score,
                                         func='get_hot')

        ident = flask.session['id'] = str(uuid4())
        app.logger.debug('New UUID: {}'.format(ident))
        content_store[ident] = reddit.submission_filter(stream)

        return {
            'SubsSelected': selected
        }


class IterSubs(Resource):
    def get(self, count):
        ident = flask.session['id']
        filtered_stream = content_store[ident]
        app.logger.debug('Retrieved UUID: {}'.format(ident))
        return flask.jsonify(take_n(filtered_stream, count))


api.add_resource(DummyResource, '/')
api.add_resource(ViewSubs, '/<string:subs>')
api.add_resource(IterSubs, '/next/<int:count>')

app.secret_key = 'test'

if __name__ == '__main__':
    app.run(debug=True)
    flask.g.content_streams = dict()
