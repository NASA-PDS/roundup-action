# encoding: utf-8

'''🤠 PDS Roundup: Maven context'''

from . import Context
from .errors import InvokedProcessError, MissingEnvVarError
from .step import Step, StepName, NullStep, ChangeLogStep, DocPublicationStep, RequirementsStep
from .util import invoke, invokeGIT
from lxml import etree
import logging, os, base64, subprocess

_logger = logging.getLogger(__name__)

_mavenNamespace = 'http://maven.apache.org/POM/4.0.0'
_mavenSettingsNamespace = 'http://maven.apache.org/SETTINGS/1.0.0'
_xsiNamespace = 'http://www.w3.org/2001/XMLSchema-instance'
_mavenXSDLocation = 'https://maven.apache.org/xsd/settings-1.0.0.xsd'


class MavenContext(Context):
    '''A Maven context supports Maven (Java) software proejcts'''
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

    def _createSettingsXML(self):
        '''Create a Maven-compatible ``settings.xml`` file for future use by
        ``Step``s created by this context.
        '''
        container = '/root/.m2'
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
        etree.SubElement(profile, prefix + 'id').text = 'ossrh'
        activation = etree.Element(prefix + 'activation')
        etree.SubElement(activation, prefix + 'activeByDefault').text = 'true'
        properties = etree.Element(prefix + 'properties')
        etree.SubElement(properties, prefix + 'gpg.executable').text = '/usr/bin/gpg'
        etree.SubElement(properties, prefix + 'gpg.useagent').text = 'false'

        tree = etree.ElementTree(root)
        with open(settings, 'wb') as out:
            tree.write(out, encoding='utf-8', xml_declaration=True, pretty_print=True)

    def _createKeyring(self):
        '''Make a GPG keyring we can later use for signing artifacts'''
        container, keyVarName = '/root/.gnupg', 'CODE_SIGNING_KEY'

        # Assumption: the .gnupg directory's existence means we've already imported the code signing key
        if os.path.isdir(container): return

        key = self.assembly.context.environ.get(keyVarName)
        if not key: raise MissingEnvVarError(keyVarName)
        subprocess.run(['gpg', '--batch', '--yes', '--import'], input=base64.b64decode(key), check=True)

    def invokeMaven(self, args):
        '''Invoke Maven, creating a ``settings.xml`` file each time as necessary'''
        self._createSettingsXML()
        self._createKeyring()
        argv = ['mvn'] + args
        return invoke(argv)


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



    def execute(self):
        _logger.debug('Maven build step')
        self.invokeMaven(self.assembly.context.args.maven_build_phases.split(','))


class _GitHubReleaseStep(_MavenStep):

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
        if not self.assembly.isStable():
            self._create_dev_tag()
            # NASA-PDS/roundup-action#25; although ``maven-release`` and ``maven-snapshot-release`` are
            # the same script, they must examine argv[0] to change their behavior.
            invoke(['maven-release', '--token', token])
        else:
            invoke(['maven-snapshot-release', '--token', token])


class _ArtifactPublicationStep(_MavenStep):
    def execute(self):

        if self.assembly.isStable():
            try:
                args = ['--activate-profiles', 'release']
                args.extend(self.assembly.context.args.maven_stable_artifact_phases.split(','))
                self.invokeMaven(args)
            except InvokedProcessError as ipe:
                _logger.error("Error while releasing on the artifactory %s", ipe)
                _logger.info("let's assume it is because this version has already been released, and move on next step")
        else:
            self.invokeMaven(self.assembly.context.args.maven_unstable_artifact_phases.split(','))


class _DocPublicationStep(DocPublicationStep):

    default_documentation_dir = 'target/staging'
