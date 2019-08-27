import json


def load_content(response):
    if response.streaming:
        return b"".join(response.streaming_content)
    else:
        return response.content


def content2json(content):
    if isinstance(content, bytes):
        content = content.decode("utf-8")
        print(content)
    return json.loads(content)


def load_content_as_json(response):
    return content2json(load_content(response))
