'''
    Various utilities for vectorl, including model factories.

    @author: vsam@softnet.tuc.gr
'''

from vectorl.model import ModelFactory
import os.path

class FileModelFactory(ModelFactory):
    def __init__(self):
        super().__init__()
        self.__path = ['.']

    @property
    def path(self):
        '''
        Return the path as a list of strings
        '''
        return self.__path

    def add(self, dir, pos=None):
        '''
        Add the directory to the specified position. If the path is already in the
        list, nothing is done.
        '''
        if dir not in self.path:
            self.path.insert(pos if pos is not None else len(self.path), dir)

    def remove(self, dir):
        '''
        Remove a directory from the list. It is not an error if it is missing.
        '''
        try:
            self.path.remove(dir)
        except ValueError:
            pass # ignore

    def get_model_source(self, name, ext=['.vl']):
        '''
        Look up for model in a series of directories in the path. A list of 
        file extensions can be provided. The default list only contains .vl
        '''

        for d in self.__path:
            for e in ext:
                fpath = os.path.join(d, name+e)
                try:
                    with open(fpath, 'r') as f:
                        return f.read()
                except FileNotFoundError:
                    pass

        raise ValueError("Model source for %s cannot be located" % name)



