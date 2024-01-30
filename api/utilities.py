from api import actions
from api.encode import GeneratorJSONEncoder
from rest_framework import status
from django.http import StreamingHttpResponse


def transform_results(cursor, triggers, trigger_args):
    row = cursor.fetchone() if not cursor.closed else None
    while row is not None:
        yield list(map(actions._translate_fetched_cell, row))
        row = cursor.fetchone()
    for t, targs in zip(triggers, trigger_args):
        t(*targs)


def conjunction(clauses):
    return {"type": "operator", "operator": "AND", "operands": clauses}


class OEPStream(StreamingHttpResponse):
    def __init__(self, *args, session=None, **kwargs):
        self.session = session
        super(OEPStream, self).__init__(*args, **kwargs)

    def __del__(self):
        if self.session:
            self.session.close()


def stream(data, allow_cors=False, status_code=status.HTTP_200_OK, session=None):
    encoder = GeneratorJSONEncoder()
    response = OEPStream(
        encoder.iterencode(data),
        content_type="application/json",
        status=status_code,
        session=session,
    )
    if allow_cors:
        response["Access-Control-Allow-Origin"] = "*"
    return response
