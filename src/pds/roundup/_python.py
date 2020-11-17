# encoding: utf-8

'''PDS Roundup: Python context'''

from . import Context
from .errors import MissingEnvVarError
from .step import Step, StepName, NullStep, ChangeLogStep, RequirementsStep, DocPublicationStep
from .util import invoke, invokeGIT
from .errors import InvokedProcessError
import logging, os

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


class _PythonStep(Step):
    '''🐍 Python steps provide some convenience functions to the Python environment'''
    def getCheeseshopURL(self):
        '''Get the URL to PyPI'''
        # 😮 TODO: This should import from twine.utils.DEFAULT_REPOSITORY and TEST_REPOSITORY
        # But if we do that we may as well use the Twine API in ``_ArtifactPublicationStep``'s
        # ``execute`` method instead of executing the ``twine`` command-line utility.
        return 'https://upload.pypi.org/legacy/' if self.assembly.isStable() else 'https://test.pypi.org/legacy/'

    def getCheeseshopCredentials(self):
        '''Get the username and password (as a tuple) to use to log into the PyPI'''
        env = self.assembly.context.environ
        username, password = env.get('pypi_username'), env.get('pypi_password')
        if not username: raise MissingEnvVarError('pypi_username')
        if not password: raise MissingEnvVarError('pypi_password')
        return username, password


class _UnitTestStep(_PythonStep):
    '''A step to take with Python unit'''
    def execute(self):
        _logger.debug('Python unit test step')
        # Since we're already in Python we could test directly, but the execution environment might
        # have set up a special ``python`` executable that has extra features needed for testing.
        invoke(['python', 'setup.py', 'test'])


class _IntegrationTestStep(_PythonStep):
    '''A step to take for integration tests with Python; what actually happens here is yet
    to be determined.
    '''
    def execute(self):
        _logger.debug('Python integration test step; TBD')


class _DocsStep(_PythonStep):
    '''A step that uses Sphinx to generate documentation'''
    def execute(self):
        invoke(['sphinx-build', '-a', '-b', 'html', 'docs/source', 'docs/build'])


class _BuildStep(_PythonStep):
    '''A step that makes a Python wheel (of cheese)'''
    def execute(self):
        invoke(['python', 'setup.py', 'bdist_wheel'])


class _GitHubReleaseStep(_PythonStep):
    '''A step that releases software to GitHub
    '''
    def execute(self):
        _logger.debug('Python GitHub release step')
        if self.assembly.isStable():
            _logger.debug("Stable releases don't automatically push a snapshot tag to GitHub")
            return

        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return

        # 😮 TODO: Use Python GitHub API

        try:
            invokeGIT(['fetch', '--prune', '--unshallow', '--tags'])
        except Exception:
            invokeGIT(['fetch', '--prune', '--tags'])
        tags = invokeGIT(['tag', '--list', '*dev*'])
        for tag in tags:
            tag = tag.strip()
            try:
                invokeGIT(['tag', '--delete', tag])
                invokeGIT(['push', '--delete', 'origin', tag])
            except InvokedProcessError:
                pass
        invoke(['python-snapshot-release', '--token', token])


class _ArtifactPublicationStep(_PythonStep):
    '''A step that publishes artifacts to the Cheeseshop'''
    def execute(self):
        # 😮 TODO: It'd be more secure to use PyPI access tokens instead of usernames and passwords!

        argv = [
            'twine',
            'upload',
            '--username',
            self.getCheeseshopCredentials()[0],
            '--password',
            self.getCheeseshopCredentials()[1],
            '--non-interactive',
            '--comment',
            "🤠 Yee-haw! This here ar-tee-fact got done uploaded by the Roundup!",
            '--skip-existing',
            '--disable-progress-bar',
            '--repository-url',
            self.getCheeseshopURL()
        ]
        dists = os.path.join(self.assembly.context.cwd, 'dist')
        argv.extend([os.path.join(dists, i) for i in os.listdir(dists) if os.path.isfile(os.path.join(dists, i))])
        # 😮 TODO: Use Twine API directly
        # But I'm in a rush:
        invoke(argv)


class _DocPublicationStep(DocPublicationStep):
    '''A step that publishes documentation, Python-style'''
    def getDocDir(self):
        return 'docs/build'
