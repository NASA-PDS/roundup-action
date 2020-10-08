# encoding: utf-8

'''🤠 PDS Roundup: Maven context'''

from . import Context
from .errors import InvokedProcessError
from .step import Step, StepName, NullStep, ChangeLogStep, DocPublicationStep, RequirementsStep
from .util import invoke, invokeGIT
from lxml import etree
import logging, os

_logger = logging.getLogger(__name__)

_mavenNamespace = 'http://maven.apache.org/POM/4.0.0'


class MavenContext(Context):
    '''A Maven context supports Maven (Java) software proejcts'''
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
        super(MavenContext, self).__init__(cwd, environ)


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


class _UnitTestStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven unit test step')
        invoke(['mvn', 'test'])


class _IntegrationTestStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven integration test step; TBD')


class _DocsStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven docs step')
        invoke(['mvn', 'site'])


class _BuildStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven build step')
        invoke(['mvn', 'compile'])


class _GitHubReleaseStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven GitHub release step')

        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot release to GitHub')
            return

        # 😮 TODO: Use Python GitHub API!
        # 🤷‍♀️ Thomas uses ``--unshallow``, but when I try that I get an error.
        # So we skip it for now:
        invokeGIT(['fetch', '--prune', '--tags'])
        tags = invokeGIT(['tag', '--list', '*dev*'])
        for tag in tags:
            tag = tag.strip()
            try:
                invokeGIT(['tag', '--delete', tag])
                invokeGIT(['push', '--delete', 'origin', tag])
            except InvokedProcessError:
                pass
        invoke(['maven-snapshot-release', '--token', token])


class _ArtifactPublicationStep(_MavenStep):
    def execute(self):
        _logger.debug('Maven artifact publication step; TBD')
        if self.assembly.isStable():
            invoke(['mvn', '-DremoveSnapshot=true', 'versions:set'])
            invokeGIT(['add', 'pom.xml'])
            version = self.getVersionFromPOM()
            invoke(['mvn', '--activate-profiles', 'release', 'clean', 'site', 'deploy'])
            invokeGIT(['git', 'tag', 'v' + version])
            invokeGIT(['git', 'push', '--tags'])
        else:
            version = self.getVersionFromPOM()
            invoke(['mvn', 'clean', 'site', 'deploy'])


class _DocPublicationStep(DocPublicationStep):  # Could multiply inherit from _MavenStep too for semantics
    def getDocDir(self):
        return 'target/site'
