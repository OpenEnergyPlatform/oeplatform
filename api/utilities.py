from api import actions

def transform_results(cursor, triggers, trigger_args):
    row = cursor.fetchone() if not cursor.closed else None
    while row is not None:
        yield list(map(actions._translate_fetched_cell, row))
        row = cursor.fetchone()
    for t, targs in zip(triggers, trigger_args):
        t(*targs)
