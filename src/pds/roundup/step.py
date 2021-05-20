# encoding: utf-8

'''🤠 PDS Roundup: A step takes you further towards a complete roundup'''

from enum import Enum
from .util import git_pull, commit, invoke
import logging, github3, tempfile, zipfile, os

_logger = logging.getLogger(__name__)


class Step(object):
    '''An abstract step; executing steps comprises a roundup'''
    def __init__(self, assembly):
        '''Initialize a step with the given ``assembly``'''
        self.assembly = assembly

    def __repr__(self):
        return f'<{self.__class__.__name__}()>'

    def execute(self):
        raise NotImplementedError('Subclasses must implement ``execute``')

    def getRepository(self):
        '''Utility: get the name of the GitHub repository'''
        return self.assembly.context.environ.get('GITHUB_REPOSITORY').split('/')[1]

    def getToken(self):
        '''Utility: get the administrative GitHub token'''
        return self.assembly.context.environ.get('ADMIN_GITHUB_TOKEN')

    def getOwner(self):
        '''Utility: return the owning user/organization of the repository in use'''
        return self.assembly.context.environ.get('GITHUB_REPOSITORY').split('/')[0]


class StepName(Enum):
    '''Enumerated identifiers for each of the possible steps of a roundup'''
    null                = 'null'
    unitTest            = 'unitTest'
    integrationTest     = 'integrationTest'
    changeLog           = 'changeLog'
    requirements        = 'requirements'
    docs                = 'docs'
    build               = 'build'
    githubRelease       = 'githubRelease'
    artifactPublication = 'artifactPublication'
    docPublication      = 'docPublication'


# Common Steps
# ============
#
# The folowing are concrete Step classes that are shared between contexts;
# i.e., they're independent of Python, Maven, etc.


class NullStep(Step):
    '''This is a "null" or "no-op" step that does nothing.'''
    def execute(self):
        pass
        # But for development, this sure is handy:
        # import pdb;pdb.set_trace()
        # import subprocess
        # subprocess.run('/bin/sh')


class ChangeLogStep(Step):
    '''This step generates a PDS-style changelog'''
    _sections = '{"requirements":{"prefix":"**Requirements:**","labels":["requirement"]},' \
                ' "improvements":{"prefix":"**Improvements:**","labels":["enhancement"]},' \
                ' "defects":{"prefix":"**Defects:**","labels":["bug"]}}'

    def execute(self):
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot generate changelog')
            return
        git_pull()
        invoke([
            'github_changelog_generator',
            '--user',
            self.getOwner(),
            '--project',
            self.getRepository(),
            '--output',
            'CHANGELOG.md',
            '--token',
            token,
            '--configure-sections',
            self._sections,
            '--no-pull-requests',
            '--exclude-labels',
            'wontfix,duplicate,invalid,theme',
            '--issues-label',
            '**Other closed issues:**',
            '--issue-line-labels',
            's.low,s.medium,s.high,s.critical'
        ])
        commit('CHANGELOG.md', 'Update changelog')


class RequirementsStep(Step):
    '''This step generates a PDS-style requirements file'''
    def execute(self):
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot generate requirements')
            return
        git_pull()
        argv = [
            'requirement-report',
            '--format',
            'md',
            '--organization',
            self.getOwner(),
            '--repository',
            self.getRepository(),
            '--output',
            'docs/requirements/',
            '--token',
            token
        ]
        if not self.assembly.isStable():
            argv.append('--dev')
        generatedFile = invoke(argv).strip()
        if not generatedFile:
            _logger.warn('🤨 Did not get a requirements file from the requirement-report; will skip it')
            return
        commit(generatedFile, 'Update requirements')


class DocPublicationStep(Step):
    def getDocDir(self):
        if self.assembly.context.args.documentation_dir:
            return self.assembly.context.args.documentation_dir
        else:
            return self.default_documentation_dir

    def execute(self):
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot send doc artifacts to GitHub')
            return
        github = github3.login(token=token)
        repo = github.repository(self.getOwner(), self.getRepository())

        # 😮 TODO: There's a race here. This code is looking for the *latest* release, which
        # we assume was made by the earlier ``StepName.githubRelease`` step. It's possible someone
        # could create another release in between these steps! It'd be better if we fetched the
        # release being worked on directly.
        tmpFileName = None
        try:
            release = repo.releases().next()  # ← here

            # Make a ZIP archive of the docs
            fd, tmpFileName = tempfile.mkstemp('.zip')
            with zipfile.ZipFile(os.fdopen(fd, 'wb'), 'w') as zf:
                for folder, subdirs, filenames in os.walk(self.getDocDir()):
                    for fn in filenames:
                        path = os.path.join(folder, fn)
                        # Avoid things like Unix-domain sockets if they just happen to appear:
                        if os.path.isfile(path):
                            zf.write(path, path[len(self.getDocDir()) + 1:])

            # Remove any existing ``documentation.zip``
            for asset in release.assets():
                if asset.name == 'documentation.zip':
                    asset.delete()
                    break

            # Add the new ZIP file as a downloadable asset
            with open(tmpFileName, 'rb') as tmpFile:
                release.upload_asset('application/zip', 'documentation.zip', tmpFile, 'Documentation (zip)')

        except StopIteration:
            _logger.info('🧐 No releases found at all, so I cannot publish documentation assets to them')
            return
        finally:
            if tmpFileName is not None: os.remove(tmpFileName)
