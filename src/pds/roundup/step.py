# encoding: utf-8

'''🤠 PDS Roundup: A step takes you further towards a complete roundup'''

from enum import Enum


class Step(object):
    '''An abstract step; executing steps comprises a roundup'''
    def __init__(self, assembly):
        '''Initialize a step with the given ``assembly``'''
        self.assembly = assembly

    def __repr__(self):
        return f'<{self.__class__.__name__}()>'

    def execute(self):
        raise NotImplementedError('Subclasses must implement ``execute``')

    def getRepository(self):
        '''Utility: get the name of the GitHub repository'''
        # 🤔 TODO: Maybe this should take into account the owner of a repo as well?
        return self.assembly.context.environ.get('GITHUB_REPOSITORY').split('/')[1]

    def getToken(self):
        '''Utility: get the administrative GitHub token'''
        return self.assembly.context.environ.get('ADMIN_GITHUB_TOKEN')


class StepName(Enum):
    '''Enumerated identifiers for each of the possible steps of a roundup'''
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
