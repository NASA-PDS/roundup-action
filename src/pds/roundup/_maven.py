# encoding: utf-8


from . import Context
from .step import Step, StepName
from .util import NullStep, 
import logging

_logger = logging.getLogger(__name__)


class MavenContext(Context):
    '''A Maven context supports Maven (Java) software proejcts'''
    def __init__(self, name, cwd, environ):
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
        super(MavenContext, self).__init__(name, cwd, environ)


class _UnitTestStep(Step):
    def execute(self):
        _logger.debug('Maven unit test step')


class _IntegrationTestStep(Step):
    def execute(self):
        _logger.debug('Maven integration test step; TBD')


class _ChangeLogStep(Step):
    def execute(self):
        _logger.debug('Maven changelog step; TBD')


class _RequirementsStep(Step):
    def execute(self):
        _logger.debug('Maven requierments step; TBD')


class _DocsStep(Step):
    def execute(self):
        _logger.debug('Maven docs step; TBD')


class _BuildStep(Step):
    def execute(self):
        _logger.debug('Maven build step; TBD')


class _GitHubReleaseStep(Step):
    def execute(self):
        _logger.debug('Maven GitHub release step; TBD')


class _ArtifactPublicationStep(Step):
    def execute(self):
        _logger.debug('Maven artifact publication step; TBD')


class _DocPublicationStep(Step):
    def execute(self):
        _logger.debug('Maven doc publication step; TBD')
