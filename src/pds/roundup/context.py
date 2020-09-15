# encoding: utf-8

'''🤠 PDS Roundup: Context tells the shape of the local software surroundings'''

import os


class Context(object):
    '''A context captures the landscape of the software environment, namely the
    directory in which any roundips will occur, plus (literal) environment variables.
    '''
    def __init__(self, cwd, environ):
        '''Don't call this directly; instead use the ``create`` method'''
        self.cwd, self.environ = cwd, environ

    def __repr__(self):
        return f'<{self.__class__.__name__}(cwd={self.cwd},environ=({len(self.environ)} items))>'

    def createStep(self, name, assembly):
        '''Create a step fitted to the local context named ``name`` using the given
        ``assembly``. Or return None if no such step is appropriate in the context.
        '''
        stepFactory = self.steps.get(name)
        return stepFactory(assembly) if stepFactory else None

    @staticmethod
    def create(cwd, environ):
        '''Create a new context for given current working directory, ``cwd``, and the given
        ``environ``ment variables.
        '''
        from . import contextFactories
        factories, factory = contextFactories(), None
        for entry in os.listdir(cwd):
            factory = factories.get(entry)
            if factory: break
        return factory(cwd, environ) if factory else None
