# encoding: utf-8

'''PDS Roundup: Python context'''

from . import Context
from .errors import MissingEnvVarError
from .step import Step, StepName, NullStep, ChangeLogStep, RequirementsStep, DocPublicationStep
from .util import invoke, invokeGIT, BRANCH_RE, VERSION_RE
from .errors import InvokedProcessError
import logging, os

_logger = logging.getLogger(__name__)


class PythonContext(Context):
    '''A Python context supports Python software proejcts'''
    def __init__(self, cwd, environ, args):
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
        super(PythonContext, self).__init__(cwd, environ, args)


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
    def _pruneDev(self):
        '''Get rid of any "dev" tags. Apparently we want to do this always; see
        https://github.com/NASA-PDS/roundup-action/issues/32#issuecomment-776309904
        '''
        _logger.debug('✂️ Pruning dev tags')

        # First do an "unshallow" fetch, with tags, and getting rid of obsolete detritus.
        # (Why they heck is it called "unshallow" when we have a perfectly good word for it in English: "deep"):
        try:
            invokeGIT(['fetch', '--prune', '--unshallow', '--tags'])
        except InvokedProcessError:
            # For a reason I can't fathom, the --unshallow (a/k/a "deep") fails, so let's just do it again
            # without that option:
            _logger.info('🤔 Unshallow prune fetch tags failed, so trying without unshallow')
            invokeGIT(['fetch', '--prune', '--tags'])

        # Next, find all the tags with "dev" in their name and delete them:
        tags = invokeGIT(['tag', '--list', '*dev*']).split('\n')
        for tag in tags:
            tag = tag.strip()
            if not tag: continue
            try:
                _logger.debug('␡ Attempting to delete tag %s', tag)
                invokeGIT(['tag', '--delete', tag])
                invokeGIT(['push', '--delete', 'origin', tag])
            except InvokedProcessError as ex:
                _logger.info(
                    '🧐 Cannot delete tag %s, stdout=«%s», stderr=«%s»; but pressing on',
                    tag, ex.error.stdout.decode('utf-8'), ex.error.stderr.decode('utf-8'),
                )

    def _findNextMicro(self):
        '''Find the next micro release number from the current repository'''
        _logger.debug('🔍 Finding next micro release')
        try:
            tag = invokeGIT(['describe', '--tags']).strip()
            match = VERSION_RE.match(tag)
            if not match or not match.group(3):
                _logger.debug('🚭 No match for «%s» as a version tag or missing micro version number; assume 0', tag)
                return 0
            _logger.debug('➕ Got micro version «%s» so upping by 1', match.group(3))
            return int(match.group(3)) + 1
        except InvokedProcessError as ex:
            _logger.info(
                '🧐 Error trying to get a git description, probably means there are no tags so using 0; stderr=«%s»',
                ex.error.stderr.decode('utf-8')
            )
            return 0

    def _tagRelease(self):
        '''Tag the current release using the branch name to signify the tag'''
        _logger.debug('🏷 Tagging the release')
        branch = invokeGIT(['branch', '--show-current']).strip()
        if not branch:
            _logger.debug('🕊 Cannot determine what branch we are on, so skipping tagging')
            return
        match = BRANCH_RE.match(branch)
        if not match:
            _logger.debug('🐎 Stable push to branch «%s» but not a ``release/`` branch, so skipping tagging', branch)
            return
        major, minor, micro = int(match.group(1)), int(match.group(2)), match.group(4)
        _logger.debug('🔖 So we got version %d.%d.%s', major, minor, micro)
        if micro is None:
            micro = self._findNextMicro()
        tag = f'v{major}.{minor}.{micro}'
        _logger.debug('🆕 New tag will be %s', tag)
        invokeGIT(['tag', '--annotate', '--force', '--message', f'Tag release {tag}', tag])
        invokeGIT(['push', '--tags'])

    def execute(self):
        '''Execute the Python GitHub release step'''
        _logger.debug('👣 Python GitHub release step')
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return
        self._pruneDev()
        if self.assembly.isStable():
            self._tagRelease()
        invoke(['python-snapshot-release', '--token', token])  # Equivalent to ``python-release``


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
