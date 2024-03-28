# encoding: utf-8

'''PDS Roundup: Node.js context'''

from .context import Context
from .errors import RoundupError, InvokedProcessError
from .step import Step, StepName, NullStep, RequirementsStep, DocPublicationStep, ChangeLogStep as BaseChangeLogStep
from .util import git_config, invoke, invokeGIT, TAG_RE, add_version_label_to_open_bugs, commit, delete_tags
import shutil, logging, os, json, re

_logger = logging.getLogger(__name__)


class NodeJSContext(Context):
    '''A Node.js context supports Node.js software proejcts'''
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
        super().__init__(cwd, environ, args)


class _NodeJSStep(Step):
    '''A Node.js-specific step.'''

    # A version regular expression adhereing to npm's strict semver policy
    semver_re = re.compile(r'^(\d+)\.(\d+)\.(\d+)-unstable')

    def read_package_metadata(self):
        '''Read the package.json file and yield its contents as a dict.'''
        _logger.debug('Getting package metdadata from package.json')
        try:
            with open('package.json', 'r') as package_json_io:
                return json.load(package_json_io)
        except IOError as ex:
            _logger.exception('Failed to read package.json: %s', str(ex))
            raise RoundupError(ex)

    def write_version_number(self, version_number):
        '''Write the new ``version_number`` to the ``package.json`` file.'''
        _logger.debug('Finding version in package.json')
        try:
            metadata = self.read_package_metadata()
            metadata['version'] = version_number
            with open('package.json', 'w') as package_json_io:
                _logger.debug('Writing package.json with new version %s', version_number)
                json.dump(metadata, package_json_io, sort_keys=True, indent=4)
        except IOError as ex:
            _logger.exception('Failed to update package.json with new version %s: %s', version_number, str(ex))
            raise RoundupError(ex)


class _PreparationStep(_NodeJSStep):
    '''Prepare the python repository for action.'''
    def _make_npmrc(self):
        token = os.getenv('NPMJS_COM_TOKEN')
        if not token:
            raise RoundupError('💣 No NPMJS_COM_TOKEN in environment; cannot do anything; aborting')

        # home_dir = '/root' if os.getenv('GITHUB_ACTIONS', 'true') == 'true' else os.getenv('HOME')
        # with open(os.path.join(home_dir, '.npmrc'), 'w') as npmrc:
        with open('.npmrc', 'w') as npmrc:
            npmrc.write(f'''@nasapds:registry=https://registry.npmjs.org/
//registry.npmjs.org/:_authToken={token}
email=pdsen-ci@jpl.nasa.gov

npmScopes:
 nasapds:
   npmAlwaysAuth: true
   npmRegistryServer: "https://registry.npmjs.org/"
   npmAuthToken: {token}
//registry.npmjs.org/:_authToken={token}
            ''')

    def execute(self):
        _logger.debug('Node.js preparation step')
        git_config()
        self._make_npmrc()

        # In github-actions-base, Node.js executables get installed in ~root/node_modules/.bin,
        # so make sure that's on our PATH
        os.environ['PATH'] = f'/root/node_modules/.bin:{os.environ["PATH"]}'

        # Clean up any node_modules from earlier—if any
        shutil.rmtree('node_modules', ignore_errors=True)

        # Install our Node.js package
        invoke(['npm', 'install'])

        # ☑️ TODO: what other prep steps are there?


class _UnitTestStep(_NodeJSStep):
    '''Unit test step, bruh.'''
    def execute(self):
        _logger.debug('Node.js unit test step')
        invoke(['npm', 'test'])


class _IntegrationTestStep(_NodeJSStep):
    '''A step to take for integration tests with Node.js; what actually happens here is yet
    to be determined.
    '''
    def execute(self):
        _logger.debug('Node.js integration test step; TBD')


class _DocsStep(_NodeJSStep):
    '''A step that uses JSDoc (invoked by ``npm docs``) to generate documentation'''
    def execute(self):
        invoke(['npm', 'run', 'jsdoc'])


class _VersionBumpingStep(_NodeJSStep):
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
        full_version = f'{major}.{minor}.{micro}'
        _logger.debug('🔖 So we got version %s', full_version)

        if micro is None:
            raise RoundupError('Invalid release version supplied in tag name. You must supply Major.Minor.Micro')

        add_version_label_to_open_bugs(full_version)
        self.write_version_number(full_version)


class _VersionCommittingStep(_NodeJSStep):
    '''Commit the bumped version.'''
    def execute(self):
        if not self.assembly.isStable():
            _logger.debug('Skipping version commit for unstable build')
            return
        commit('package.json', 'Commiting package.json for stable release')


class _BuildStep(_NodeJSStep):
    '''A step that makes an installable package.'''
    def execute(self):
        if self.assembly.isStable():
            # The package.json should already have the "stable" version number from the _VersionBumpingStep
            # so we can just invoke ``npm build``
            invoke(['npm', 'run', 'build'])
        else:
            # EA says we should rewrite the version number with ``-unstable`` in it
            metadata = self.read_package_metadata()
            unstable_version = metadata['version'] + '-unstable'
            self.write_version_number(unstable_version)
            invoke(['npm', 'run', 'build'])


class _GitHubReleaseStep(_NodeJSStep):
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
        '''Execute the Node.js GitHub release step'''
        _logger.debug('👣 Node.js GitHub release step')
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return
        self._pruneDev()
        if self.assembly.isStable():
            self._tagRelease()
            invoke(['/usr/local/bin/nodejs-release', '--debug', '--token', token])
        else:  # It's unstable release
            invoke(['/usr/local/bin/nodejs-release', '--debug', '--snapshot', '--token', token])
            self._pruneReleaseTags()


class _ArtifactPublicationStep(_NodeJSStep):
    '''A step that publishes artifacts to the npmjs.com'''
    def execute(self):
        try:
            if self.assembly.isStable():
                argv = ['npm', 'publish', '--verbose', '--access', 'public']
            else:
                # In NASA-PDS/devops#69 @jordanpadams pefers "beta" to "unstable". This was
                # corroborated in our stand up meeting on 2024-03-05.
                #
                # Also, apparently there's no way to re-release an unstable package to npm.
                # We have to bump the version number.

                metadata = self.read_package_metadata()
                match = self.semver_re.match(metadata['version'])
                if not match:
                    raise RoundupError(f'The version number {metadata["version"]} in package.json is malformed')
                major, minor, micro = int(match.group(1)), int(match.group(2)), int(match.group(3)) + 1
                self.write_version_number(f'{major}.{minor}.{micro}-unstable')
                argv = ['npm', 'publish', '--verbose', '--access', 'public']
                commit('package.json', f'Committing bumped version № {major}.{minor}.{micro} for unstable assembly')
            invoke(argv)
        except InvokedProcessError:
            # For unstalbe releases, we ignore this
            if self.assembly.isStable(): raise


class _DocPublicationStep(DocPublicationStep):

    default_documentation_dir = 'out'


class _CleanupStep(_NodeJSStep):
    '''Step that tidies up.'

    At this point we're cleaing up so errors are not longer considered awful.
    '''
    def execute(self):
        _logger.debug('Node.js cleanup step')
        if not self.assembly.isStable():
            _logger.debug('Skipping cleanup for unstable build')
            return

        # NASA-PDS/roundup-action#99: delete the release/X.Y.Z tag
        tag = invokeGIT(['describe', '--tags', '--abbrev=0', '--match', 'release/*']).strip()
        if not tag:
            raise RoundupError('🏷 Cannot determine the release tag at cleanup step')
        invokeGIT(['push', 'origin', f':{tag}'])

        version = self.read_package_metadata()['version']
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        if not match:
            _logger.info(f'Expected Major.Minor.Micro version in package.json but got «{version}» but whatever')
            return
        # NASA-PDS/roundup-action#81: Jordan would prefer the ``minor`` version get bumped, not the ``micro`` version:
        major, minor, micro = int(match.group(1)), int(match.group(2)) + 1, int(match.group(3))
        new_version = f'{major}.{minor}.0'
        _logger.debug('🔖 Setting version %s in package.json', new_version)
        self.write_version_number(new_version)
        commit('package.json', f'Setting next dev version to {major}.{minor}.{micro}')


class ChangeLogStep(BaseChangeLogStep):
    def execute(self):
        _logger.debug('Node.js changelog step')
        delete_tags('*dev*')
        super().execute()
