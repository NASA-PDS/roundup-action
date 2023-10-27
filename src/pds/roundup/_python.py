# encoding: utf-8

'''PDS Roundup: Python context'''

from .context import Context
from .errors import InvokedProcessError, RoundupError
from .errors import MissingEnvVarError
from .step import ChangeLogStep as BaseChangeLogStep
from .step import Step, StepName, NullStep, RequirementsStep, DocPublicationStep
from .util import invoke, invokeGIT, TAG_RE, commit, delete_tags, git_config
from lasso.releasers._python_version import TextFileDetective
import logging, os, re, shutil

_logger = logging.getLogger(__name__)

# This should match what's in github-actions-base (goodness, this is complex!)
SPHINX_VERSION = '3.2.1'


class PythonContext(Context):
    '''A Python context supports Python software proejcts'''
    def __init__(self, cwd, environ, args):
        self.steps = {
            StepName.artifactPublication: _ArtifactPublicationStep,
            StepName.build:               _BuildStep,
            StepName.changeLog:           ChangeLogStep,
            StepName.cleanup:             _CleanupStep,
            StepName.docPublication:      _DocPublicationStep,
            StepName.docs:                _DocsStep,
            StepName.githubRelease:       _GitHubReleaseStep,
            StepName.integrationTest:     _IntegrationTestStep,
            StepName.null:                NullStep,
            StepName.preparation:         _PreparationStep,
            StepName.requirements:        RequirementsStep,
            StepName.unitTest:            _UnitTestStep,
            StepName.versionBump:         _VersionBumpingStep,
            StepName.versionCommit:       _VersionCommittingStep,
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
        '''Get the username and password (as a tuple) to use to log into the PyPI.

        ☑️ TODO: Use an API token instead of a username and password.
        '''
        env = self.assembly.context.environ
        username, password = env.get('pypi_username'), env.get('pypi_password')
        if not username: raise MissingEnvVarError('pypi_username')
        if not password: raise MissingEnvVarError('pypi_password')
        return username, password


class _PreparationStep(_PythonStep):
    '''Prepare the python repository for action.'''
    def execute(self):
        _logger.debug('Python preparation step')
        git_config()
        shutil.rmtree('venv', ignore_errors=True)
        # We add access to system site packages so that projects can save time if they need numpy, pandas, etc.
        invoke(['python', '-m', 'venv', '--system-site-packages', 'venv'])
        # Do the pseudo-equivalent of ``activate``:
        venvBin = os.path.abspath(os.path.join(self.assembly.context.cwd, 'venv', 'bin'))
        os.environ['PATH'] = f'{venvBin}:{os.environ["PATH"]}'
        # Make sure we have the latest of pip+setuptools+wheel
        invoke(['pip', 'install', '--quiet', '--upgrade', 'pip', 'setuptools', 'wheel'])
        # #79: ensure that the venv has its own ``sphinx-build``
        invoke(['pip', 'install', '--quiet', '--ignore-installed', f'sphinx=={SPHINX_VERSION}'])
        # Now install the package being rounded up
        invoke(['pip', 'install', '--editable', '.[dev]'])
        # ☑️ TODO: what other prep steps are there? What about VERSION.txt overwriting?


class _UnitTestStep(_PythonStep):
    '''Unit test step, duh.'''
    def execute(self):
        _logger.debug('Python unit test step')
        tox = os.path.abspath(os.path.join(self.assembly.context.cwd, 'venv', 'bin', 'tox'))
        if os.path.isfile(tox):
            _logger.debug('Trying the new way: ``tox``')
            invoke([tox, '-e', 'py39'])  # ``py39`` = unit tests
        else:
            _logger.debug('Trying the old way: ``setup.py test``')
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
        invoke(['/usr/local/bin/sphinx-build', '-a', '-b', 'html', 'docs/source', 'docs/build'])


class _VersionBumpingStep(_PythonStep):
    '''Bump the version but do not commit it (yet).'''
    def execute(self):
        if not self.assembly.isStable():
            _logger.debug('Skipping version bump for unstable build')
            return

        # Figure out the tag name; we use ``--tags`` to pick up all tags, not just the annotated
        # ones. This'll help reduce erros by users who forget to annotate (``-a`` or ``--annoate``)
        # their tags. The ``--abbrev 0`` truncates any post-tag commits
        tag = invokeGIT(['describe', '--tags', '--abbrev=0', '--match', 'release/*']).strip()

        if not tag:
            raise RoundupError('🕊 Cannot determine the release tag; version bump failed')

        match = TAG_RE.match(tag)
        if not match:
            raise RoundupError(f'🐎 Stable tag of «{tag}» but not a ``release/`` tag')

        major, minor, micro = int(match.group(1)), int(match.group(2)), match.group(4)
        _logger.debug('🔖 So we got version %d.%d.%s', major, minor, micro)
        if micro is None:
            raise RoundupError('Invalid release version supplied in tag name. You must supply Major.Minor.Micro')

        _logger.debug("Locating VERSION.txt to update with new release version.")
        try:
            version_file = TextFileDetective.locate_file(self.assembly.context.cwd)
        except ValueError:
            msg = 'Unable to locate ./src directory. Is your repository properly structured?'
            _logger.debug(msg)
            raise RoundupError(msg)

        if version_file is None:
            raise RoundupError('Unable to locate VERSION.txt in repo. Version bump failed.')
        else:
            with open(version_file, 'w') as inp:
                inp.write(f'{major}.{minor}.{micro}\n')


class _VersionCommittingStep(_PythonStep):
    '''Commit the bumped version.'''
    def execute(self):
        if not self.assembly.isStable():
            _logger.debug('Skipping version commit for unstable build')
            return

        _logger.debug("Locating VERSION.txt to commit")
        try:
            version_file = TextFileDetective.locate_file(self.assembly.context.cwd)
            if version_file is None:
                raise RoundupError('Unable to locate VERSION.txt in repo. Version commit failed.')
        except ValueError:
            msg = 'Unable to locate ./src directory. Is your repository properly structured?'
            _logger.debug(msg)
            raise RoundupError(msg)

        commit(version_file, f'Commiting {version_file} for stable release')


class _BuildStep(_PythonStep):
    '''A step that makes a Python wheel (of cheese)'''
    def execute(self):
        if self.assembly.isStable():
            invoke(['python', 'setup.py', 'bdist_wheel'])
        else:
            invoke(['python', 'setup.py', 'egg_info', '--tag-build', 'dev', 'bdist_wheel'])


class _GitHubReleaseStep(_PythonStep):
    '''A step that releases software to GitHub
    '''
    def _pruneDev(self):
        '''Get rid of any "dev" tags. Apparently we want to do this always; see
        https://github.com/NASA-PDS/roundup-action/issues/32#issuecomment-776309904
        '''
        delete_tags('*dev*')

    def _pruneReleaseTags(self):
        '''Get rid of ``release/*`` tags.'''
        delete_tags('release/*')

    def _tagRelease(self):
        '''Tag the current release using the v1.2.3-style tag based on the release/1.2.3-style tag.'''
        _logger.debug('🏷 Tagging the release')
        tag = invokeGIT(['describe', '--tags', '--abbrev=0', '--match', 'release/*']).strip()
        if not tag:
            _logger.debug('🕊 Cannot determine what tag we are currently on, so skipping re-tagging')
            return
        match = TAG_RE.match(tag)
        if not match:
            _logger.debug('🐎 Stable tag at «%s» but not a ``release/`` style tag, so skipping tagging', tag)
            return
        major, minor, micro = int(match.group(1)), int(match.group(2)), match.group(4)
        _logger.debug('🔖 So we got version %d.%d.%s', major, minor, micro)
        # roundup-action#90: we no longer bump the version number; just re-tag at the current HEAD
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
            invoke(['/usr/local/bin/python-release', '--debug', '--token', token])
        else:  # It's unstable release
            invoke(['/usr/local/bin/python-release', '--debug', '--snapshot', '--token', token])
            self._pruneReleaseTags()


class _ArtifactPublicationStep(_PythonStep):
    '''A step that publishes artifacts to the Cheeseshop'''
    def execute(self):
        # 😮 TODO: It'd be more secure to use PyPI access tokens instead of usernames and passwords!

        argv = [
            '/usr/local/bin/twine',
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
        try:
            invoke(argv)
        except InvokedProcessError:
            # Unstable releases, let it slide; this is test.pypi.org anyway, and we are abusing
            # it for snapshot releases, when it's probably just for testing release tools—which
            # in a way, is what this is.
            #
            # (We really ought to re-think (ab)using test.pypi.org in this way.)
            if self.assembly.isStable(): raise


class _DocPublicationStep(DocPublicationStep):

    default_documentation_dir = 'docs/build'


class _CleanupStep(_PythonStep):
    '''Step that tidies up.'

    At this point we're cleaing up so errors are not longer considered awful.
    '''
    def execute(self):
        _logger.debug('Python cleanup step')
        if not self.assembly.isStable():
            _logger.debug('Skipping cleanup for unstable build')
            return

        # NASA-PDS/roundup-action#99: delete the release/X.Y.Z tag
        tag = invokeGIT(['describe', '--tags', '--abbrev=0', '--match', 'release/*']).strip()
        if not tag:
            raise RoundupError('🏷 Cannot determine the release tag at cleanup step')
        invokeGIT(['push', 'origin', f':{tag}'])

        detective = TextFileDetective(self.assembly.context.cwd)
        version, version_file = detective.detect(), detective.locate_file(self.assembly.context.cwd)
        if not version:
            _logger.info('Could not figure out the version left in src/…/VERSION.txt, but we made it this far so punt')
            return
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        if not match:
            _logger.info(f'Expected Major.Minor.Micro version in src/…/VERSION.txt but got «{version}» but whatever')
            return
        # NASA-PDS/roundup-action#81: Jordan would prefer the ``minor`` version get bumped, not the ``micro`` version:
        major, minor, micro = int(match.group(1)), int(match.group(2)) + 1, int(match.group(3))
        new_version = f'{major}.{minor}.0'
        _logger.debug('🔖 Setting version %s in src/…/VERSION.txt', new_version)
        with open(version_file, 'w') as f:
            f.write(f'{new_version}\n')
        commit(version_file, f'Setting next dev version to {major}.{minor}.{micro}')


class ChangeLogStep(BaseChangeLogStep):
    def execute(self):
        _logger.debug('Python changelog step')
        delete_tags('*dev*')
        super().execute()
