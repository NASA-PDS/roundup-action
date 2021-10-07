# encoding: utf-8

'''🤠 PDS Roundup: Maven context'''

from .context import Context
from .errors import InvokedProcessError, MissingEnvVarError, RoundupError
from .step import Step, StepName, NullStep, ChangeLogStep, DocPublicationStep, RequirementsStep
from .util import invoke, invokeGIT, BRANCH_RE, commit
from lxml import etree
import logging, os, base64, subprocess, re

_logger = logging.getLogger(__name__)

_mavenNamespace = 'http://maven.apache.org/POM/4.0.0'
_mavenSettingsNamespace = 'http://maven.apache.org/SETTINGS/1.0.0'
_xsiNamespace = 'http://www.w3.org/2001/XMLSchema-instance'
_mavenXSDLocation = 'https://maven.apache.org/xsd/settings-1.0.0.xsd'
_homeDir = '/root' if os.getenv('GITHUB_ACTIONS', 'true') == 'true' else os.getenv('HOME')


class MavenContext(Context):
    '''A Maven context supports Maven (Java) software proejcts'''
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
        }
        super(MavenContext, self).__init__(cwd, environ, args)


class _MavenStep(Step):
    '''☕️ Maven steps provide common conveniences for Maven and the Java environment'''
    def getVersionFromPOM(self):
        '''Get the version string from a ``pom.xml`` file'''
        cwd = self.assembly.context.cwd
        pomFile = os.path.join(cwd, 'pom.xml')
        if not os.path.isfile(pomFile):
            _logger.info('☡ No ``pom.xml`` found in %s; cannot determine version', cwd)
            return None
        pom = etree.parse(pomFile)
        versions = pom.xpath('/ns:project/ns:version', namespaces={'ns': _mavenNamespace})
        if len(versions) == 0:
            _logger.info('☡ No ``<version>`` found in %s; cannot determine version', pomFile)
            return None
        elif len(versions) > 1:
            _logger.info(
                '☡ More than one ``<version>`` found in %s; using the first one, but your POM is bad',
                pomFile
            )

        return versions[0].text.strip()
    def invokeMaven(self, args):
        '''Invoke Maven with the given ``args``.'''
        argv = ['mvn', '--quiet'] + args
        return invoke(argv)


class _PreparationStep(Step):
    '''Step that prepares for future steps by setting up Maven and code signing.'''
    def _createSettingsXML(self):
        '''Create a Maven-compatible ``settings.xml`` file for future use by
        ``Step``s created by this context.
        '''
        container = os.path.join(_homeDir, '.m2')
        os.makedirs(container, exist_ok=True)
        settings = os.path.join(container, 'settings.xml')
        if os.path.isfile(settings): return

        _logger.info('✍️ Writing Maven settings to %s', settings)

        env, creds = self.assembly.context.environ, {}
        for var in ('username', 'password'):
            varName = 'ossrh_' + var
            value = env.get(varName)
            if not value: raise MissingEnvVarError(varName)
            creds[var] = value

        nsmap = {
            None: _mavenSettingsNamespace,
            'xsi': _xsiNamespace
        }
        prefix = f'{{{_mavenSettingsNamespace}}}'
        root = etree.Element(
            prefix + 'settings',
            attrib={f'{{{_xsiNamespace}}}schemaLocation': f'{_mavenSettingsNamespace} {_mavenXSDLocation}'},
            nsmap=nsmap
        )
        servers = etree.Element(prefix + 'servers')
        root.append(servers)
        server = etree.Element(prefix + 'server')
        servers.append(server)
        etree.SubElement(server, prefix + 'id').text = 'ossrh'
        etree.SubElement(server, prefix + 'username').text = creds['username']
        etree.SubElement(server, prefix + 'password').text = creds['password']
        profiles = etree.Element(prefix + 'profiles')
        root.append(profiles)
        profile = etree.Element(prefix + 'profile')
        profiles.append(profile)
        etree.SubElement(profile, prefix + 'id').text = 'release'  # The PDS Maven Parent POM calls it ``release``
        activation = etree.Element(prefix + 'activation')
        profile.append(activation)
        etree.SubElement(activation, prefix + 'activeByDefault').text = 'true'
        properties = etree.Element(prefix + 'properties')
        profile.append(properties)
        etree.SubElement(properties, prefix + 'gpg.executable').text = '/usr/bin/gpg'
        etree.SubElement(properties, prefix + 'gpg.useagent').text = 'false'

        tree = etree.ElementTree(root)
        with open(settings, 'wb') as out:
            tree.write(out, encoding='utf-8', xml_declaration=True, pretty_print=True)

    def _createKeyring(self):
        '''Make a GPG keyring we can later use for signing artifacts'''
        container, keyVarName = os.path.join(_homeDir, '.gnupg'), 'CODE_SIGNING_KEY'

        # Assumption: the .gnupg directory's existence means we've already imported the code signing key
        if os.path.isdir(container): return

        key = self.assembly.context.environ.get(keyVarName)
        if not key: raise MissingEnvVarError(keyVarName)
        subprocess.run(['gpg', '--batch', '--yes', '--import'], input=base64.b64decode(key), check=True)

    def execute(self):
        _logger.debug('Maven preparation step')
        self._createSettingsXML()
        self._createKeyring()


class _UnitTestStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven unit test step')
        self.invokeMaven(self.assembly.context.args.maven_test_phases.split(','))


class _IntegrationTestStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven integration test step; TBD')


class _DocsStep(_MavenStep):
    '''Docs generation.

    To generate maven docs, usually you can just do `mvn site`
    However, in order to support repos with sub-modules, you have 
    to package the software in case there are sub-module dependencies,
    build the site as normal, and aggregate the docs (site:stage)
    '''
    def execute(self):
        _logger.debug('Maven docs step')
        self.invokeMaven(self.assembly.context.args.maven_doc_phases.split(','))


class _BuildStep(_MavenStep):
    '''Maven build step.'''
    def execute(self):
        _logger.debug('Maven build step')
        self.invokeMaven(self.assembly.context.args.maven_build_phases.split(','))


class _GitHubReleaseStep(_MavenStep):
    '''Maven GitHub release step.'''
    def _create_dev_tag(self):
        try:
            invokeGIT(['fetch', '--prune', '--unshallow', '--tags'])
        except InvokedProcessError:
            _logger.info('🤔 Unshallow prune fetch tags failed, so trying without unshallow')
            invokeGIT(['fetch', '--prune', '--tags'])
        tags = invokeGIT(['tag', '--list', '*SNAPSHOT*']).split('\n')
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
                    tag,
                    ex.error.stdout.decode('utf-8'),
                    ex.error.stderr.decode('utf-8'),
                )

    def execute(self):
        _logger.debug('maven-release release step')

        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return

        # 😮 TODO: Use Python GitHub API!
        # create new dev tag if build is successful
        _logger.debug('❗️ Before I run maven-release, here is what the pom.xml looks like as far as <version>')
        with open('pom.xml', 'r') as f:
            for l in f:
                if 'version' in l: _logger.debug(f'“{l.strip()}”')

        if not self.assembly.isStable():
            self._create_dev_tag()
            invoke(['maven-release', '--snapshot', '--token', token])
        else:
            invoke(['maven-release', '--token', token])


class _ArtifactPublicationStep(_MavenStep):
    def execute(self):
        if self.assembly.isStable():
            try:
                _logger.debug('❗️ Before I run `mvn deploy`, here is what the pom.xml looks like as far as <version>')
                with open('pom.xml', 'r') as f:
                    for l in f:
                        if 'version' in l: _logger.debug(f'“{l.strip()}”')
                # The PDS Maven Parent POM calls it ``release``
                args = [
                    'mvn', '--errors', '--activate-profiles', 'release',
                    '-Dgpg.executable=/usr/bin/gpg', '-Dgpg.useagent=false'
                ]
                args.extend(self.assembly.context.args.maven_stable_artifact_phases.split(','))
                # self.invokeMaven(args)
                invoke(args)
            except InvokedProcessError as ipe:
                _logger.error("Error while releasing on the artifactory %s", ipe)
                _logger.info("let's assume it is because this version has already been released, and move on next step")
        else:
            self.invokeMaven(self.assembly.context.args.maven_unstable_artifact_phases.split(','))


class _DocPublicationStep(DocPublicationStep):

    default_documentation_dir = 'target/staging'

    def getDocDir(self):
        # Return the user's preference, if given
        userDocs = self.assembly.context.args.documentation_dir
        if userDocs:
            _logger.debug('🙋‍♀️ User has specified a doc dir of «%s», so using it', userDocs)
            return userDocs

        # Otherwise, use the staging directory if it exists, otherwise use the site directory
        if os.path.isdir('target/staging'):
            _logger.debug('🎭 The staging dir exists for docs, so using it')
            return 'target/staging'
        else:
            _logger.debug('🏗 Defaulting to site dir for docs')
            return 'target/site'


class _VersionBumpingStep(_MavenStep):
    '''Step that sets a version number as needed.'''
    def execute(self):
        '''Set the version number.'''
        if not self.assembly.isStable():
            _logger.debug('Skipping version bump for unstable build')
            return

        branch = invokeGIT(['branch', '--show-current']).strip()
        if not branch:
            raise RoundupError('🕊 Cannot determine what branch we are on so version bump fail')
        match = BRANCH_RE.match(branch)
        if not match:
            raise RoundupError(f'🐎 Stable workflow on «{branch}» but not a ``release/`` branch!')
        major, minor, micro = int(match.group(1)), int(match.group(2)), match.group(4)
        _logger.debug('🔖 So we got version %d.%d.%s', major, minor, micro)
        if micro is None:
            raise RoundupError('Invalid release version supplied in branch. You must supply Major.Minor.Micro')
        invoke([
            'mvn',
            '-DgenerateBackupPoms=false',
            '-DremoveSnapshot=true',
            f'-DnewVersion={major}.{minor}.{micro}',
            'versions:set'
        ])
        _logger.debug('❗️ After I ran `mvn versions:set`, here is what the pom.xml looks like as far as <version>')
        with open('pom.xml', 'r') as f:
            for l in f:
                if 'version' in l: _logger.debug(f'“{l.strip()}”')
        commit('pom.xml', f'Bumping version for {major}.{minor}.{micro} release')


class _CleanupStep(_MavenStep):
    '''Step that tidies up.'''
    def execute(self):
        _logger.debug('Maven cleanup step')
        if not self.assembly.isStable():
            _logger.debug('Skipping cleanup for unstable build')
            return
        pomVersion = self.getVersionFromPOM()
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', pomVersion)
        if not match:
            raise RoundupError(f'Expected Major.Minor.Micro version in pom but got «{pomVersion}»')
        major, minor, micro = int(match.group(1)), int(match.group(2)), int(match.group(3)) + 1
        _logger.debug('🔖 Setting version %d.%d.%d-SNAPSHOT in the pom', major, minor, micro)
        self.invokeMaven([
            '-DgenerateBackupPoms=false',
            '-DremoveSnapshot=false',
            f'-DnewVersion={major}.{minor}.{micro}-SNAPSHOT',
            'versions:set'
        ])
        commit('pom.xml', f'Setting snapshot version for {major}.{minor}.{micro}-SNAPSHOT')
