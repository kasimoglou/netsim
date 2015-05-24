
#
# A model factory for tests
#

from vectorl.model import ModelFactory

class TestModelFactory(ModelFactory):
    '''
    A simple implementation of ModelFactory, for testing.
    '''
    def __init__(self, sources=[], fail_early=False):
        super().__init__()
        self.sources = dict()
        for name, src in sources:
            self.add_source(name, src)

    def add_source(self, name, src):
        self.sources[name]  = src

    def get_model_source(self, name):
        return self.sources[name]

