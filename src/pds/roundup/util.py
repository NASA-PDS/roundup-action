# encoding: utf-8

'''🤠 PDS Roundup — Utilities'''

from .step import Step
import subprocess, logging

_logger = logging.getLogger(__name__)


# Functions
# =========

def exec(argv):
    '''Execute a command within the operating system, returning its output. On any error,
    raise ane exception. The command is the first element of ``argv``, with remaining elements
    being arguments to the command.
    '''
    _logger.debug('🏃‍♀️ Running «%r»', argv)
    cp = subprocess.run(argv, stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
    _logger.debug('🏁 Run complete, rc=%d, output=%s', cp.returncode, cp.stdout)
    return cp.stdout


def populateEnvVars(env):
    '''Populate the environment variable mapping in ``env`` with our "standard" set of variables
    required by a roundup. Return a copy of this modified mapping. Note that we may also log
    some warning messages if certain expected variables are missing.
    '''
    copy = dict(env)
    pypi_username = copy.get('pypi_username', 'pypi')
    pypi_password = copy.get('pypi_password', 'secret')
    copy['pypi_username'] = pypi_username
    copy['pypi_password'] = pypi_password

    for var in ('GITHUB_TOKEN', 'GITHUB_REPOSITORY'):
        if var not in env:
            _logger.warn('⚠️ «%s» not found in environment; some steps may fail', var)

    return copy


def commit(filename, message):
    '''Commit the file named ``filename`` to the local Git repository with the given ``message``.
    '''
    # 😮 TODO: Use Python GitHub API
    # But I'm in a rush:
    exec(['git', 'config', '--local', 'user.email', 'pdsen-ci@github.com'])
    exec(['git', 'config', '--local', 'user.name', 'PDS dev admin'])
    exec(['git', 'pull', 'origin', 'master'])
    exec(['git', 'add', filename])
    exec(['git', 'commit', '--allow-empty', '--message', message])


# Classes
# =======

class NullStep(Step):
    '''This is a "null" or "no-op" step that does nothing.'''
    def execute(self):
        pass


class ChangeLogStep(Step):
    '''This step generates a PDS-style changelog'''
    _sections = '{"improvements":{"prefix":"**Improvements:**","labels":["Epic"]},"defects":{"prefix":"**Defects:**","labels":["bug"]},"deprecations":{"prefix":"**Deprecations:**","labels":["deprecation"]}}'

    def execute(self):
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot generate changelog')
            return
        exec([
            'github_changelog_generator',
            '--user',
            '--NASA-PDS',
            '--project',
            self.getRepository(),
            '--output',
            'CHANGELOG.md',
            '--token',
            token,
            '--configure-sections',
            self._sections,
            '--no-pull-requests',
            '--issues-label',
            '**Other closed issues:**',
            '--issue-line-labels',
            'high,low,medium'
        ])
        commit('CHANGELOG.md', 'Update changelog')


class RequirementsStep(Step):
    '''This step generates a PDS-style requirements file'''
    def execute(self):
        token = self.getToken()
        if not token:
            _logger.info('🤷‍♀️ No GitHub administrative token; cannot generate requirements')
            return
        argv = [
            'requirement-report',
            '--format',
            'md',
            '--organization',
            'NASA-PDS',
            '--repository',
            self.repository(),
            '--output',
            'docs/requirements/',
            '--token',
            token
        ]
        if not self.assembly.isStable():
            argv.append('--dev')
        generatedFile = exec(argv)
        commit(generatedFile, 'Update requirements')
