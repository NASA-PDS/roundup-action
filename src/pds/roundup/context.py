# encoding: utf-8

'''Context: how we define the local software surroundings'''

import os


class Context(object):
    def __init__(self, cwd, environ):
        self.cwd, self.environ = cwd, environ

    def __repr__(self):
        return f'<{self.__class__.__name__}(cwd={self.cwd},environ=({len(self.environ)} items))>'

    def createStep(self, name, assembly):
        stepFactory = self.steps.get(name)
        return stepFactory(assembly) if stepFactory else None

    @staticmethod
    def create(cwd, environ):
        from . import contextFactories
        factories, factory = contextFactories(), None
        for entry in os.listdir(cwd):
            factory = factories.get(entry)
            if factory: break
        if factory:
            context = factory(cwd, environ)
        return context
