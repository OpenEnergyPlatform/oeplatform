from rdflib import RDF, Literal  # noqa

from oeo_ext.oekb import namespaces  # noqa
from oeo_ext.oekb.connection import oekb_oeo_ext


# Use this to implement filters that help you retrieve specific information
# from the new oeo ext oekg
class OekgQuery:
    def __init__(self):
        self.oekb = oekb_oeo_ext

    def implementMethods(self):
        raise NotImplementedError
