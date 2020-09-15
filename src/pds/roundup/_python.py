# encoding: utf-8

'''PDS Roundup: Python context'''

from . import Context
from .step import Step, StepName
from .util import exec, NullStep, ChangeLogStep, RequirementsStep
import logging

_logger = logging.getLogger(__name__)


class PythonContext(Context):
    '''A Python context supports Python software proejcts'''
    def __init__(self, cwd, environ):
        self.steps = {
            StepName.null:                NullStep,
            StepName.unitTest:            _UnitTestStep,
            StepName.integrationTest:     _IntegrationTestStep,
            StepName.changeLog:           ChangeLogStep,
            StepName.requirements:        RequirementsStep,
            StepName.docs:                _DocsStep,
            StepName.build:               _BuildStep,
            StepName.githubRelease:       _GitHubReleaseStep,
            StepName.artifactPublication: _ArtifactPublicationStep,
            StepName.docPublication:      _DocPublicationStep,
        }
        super(PythonContext, self).__init__(cwd, environ)


class _UnitTestStep(Step):
    '''A step to take with Python unit'''
    def execute(self):
        _logger.debug('Python unit test step')
        # Since we're already in Python we could test directly, but the execution environment might
        # have set up a special ``python`` executable that has extra features needed for testing.
        exec(['python', 'setup.py', 'test'])


class _IntegrationTestStep(Step):
    '''A step to take for integration tests with Python; what actually happens here is yet
    to be determined.
    '''
    def execute(self):
        _logger.debug('Python integration test step; TBD')


class _DocsStep(Step):
    '''A step that uses Sphinx to generate documentation'''
    def execute(self):
        exec(['sphinx-build', '-a', '-b', 'html', 'docs/source', 'docs/build'])


class _BuildStep(Step):
    '''A step that makes a Python wheel (of cheese)'''
    def execute(self):
        exec(['python', 'setup.py' 'bdist_wheel'])


class _GitHubReleaseStep(Step):
    '''A step that releases software to GitHub
    🤔 TODO: Isn't this generic between kinds of contexts?
    '''
    def execute(self):
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return

        # 😮 TODO: Use Python GitHub API
        # But I'm in a rush:
        exec(['git', 'fetch', '--prune', '--unshallow', '--tags'])
        tags = exec(['git', 'tag', '--list', '*dev*'])
        for tag in tags:
            exec(['git', 'tag', '--delete', tag])
            exec(['git', 'push', '--delete', 'origin', tag])
        exec(['python-snapshot-release', '--token', token])


class _ArtifactPublicationStep(Step):
    '''A step that publishes artifacts to the Cheeseshop'''
    def execute(self):
        _logger.debug('Python artifact publication step; TBD')


class _DocPublicationStep(Step):
    '''A step that publishes documentation to a website'''
    def execute(self):
        _logger.debug('Python doc publication step; TBD')
