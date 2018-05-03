class APIError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status

class APIKeyError(APIError):
    def __init__(self, dictionary, key):
        self.message = "Key '%s' not found in %s"%(key,dictionary)
        self.status = 401
