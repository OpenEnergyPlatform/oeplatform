class MetadataException(Exception):
    def __init__(self, metadata, error):
        self.metadata = metadata
        self.error = error
