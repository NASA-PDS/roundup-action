# encoding: utf-8

'''Python context'''


from . import Context
from .step import Step, StepName
from .util import exec, NullStep, ChangeLogStep
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
            StepName.requirements:        _RequirementsStep,
            StepName.docs:                _DocsStep,
            StepName.build:               _BuildStep,
            StepName.githubRelease:       _GitHubReleaseStep,
            StepName.artifactPublication: _ArtifactPublicationStep,
            StepName.docPublication:      _DocPublicationStep,
        }
        super(PythonContext, self).__init__(cwd, environ)


class _UnitTestStep(Step):
    def execute(self):
        _logger.debug('Python unit test step')
        # Since we're already in Python we could test directly, but the execution environment might
        # have set up a special ``python`` executable that has extra features needed for testing.
        exec(['python', 'setup.py', 'test'])


class _IntegrationTestStep(Step):
    def execute(self):
        _logger.debug('Python integration test step; TBD')


class _RequirementsStep(Step):
    def execute(self):
        _logger.debug('Python requierments step; TBD')


class _DocsStep(Step):
    def execute(self):
        _logger.debug('Python docs step; TBD')


class _BuildStep(Step):
    def execute(self):
        _logger.debug('Python build step; TBD')


class _GitHubReleaseStep(Step):
    def execute(self):
        _logger.debug('Python GitHub release step; TBD')


class _ArtifactPublicationStep(Step):
    def execute(self):
        _logger.debug('Python artifact publication step; TBD')


class _DocPublicationStep(Step):
    def execute(self):
        _logger.debug('Python doc publication step; TBD')
