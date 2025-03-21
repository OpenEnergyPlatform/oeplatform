class MetadataError(Exception):
    """Raised if metadata is invalid"""


class DeployError(Exception):
    """Raised if deploy fails"""


class MossError(Exception):
    """Raised if submitting metadata to MOSS fails"""
