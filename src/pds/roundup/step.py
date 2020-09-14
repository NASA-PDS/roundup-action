# encoding: utf-8


'''A step takes you further towards a complete roundup'''

from enum import Enum


class Step(object):
    def __init__(self, assembly):
        self.assembly = assembly

    def __repr__(self):
        return f'<{self.__class__.__name__}()>'

    def execute(self):
        raise NotImplementedError('Subclasses must implement ``execute``')


class StepName(Enum):
    null                = 'null'
    unitTest            = 'unitTest'
    integrationTest     = 'integrationTest'
    changeLog           = 'changeLog'
    requirements        = 'requirements'
    docs                = 'docs'
    build               = 'build'
    githubRelease       = 'githubRelease'
    artifactPublication = 'artifactPublication'
    docPublication      = 'docPublication'
