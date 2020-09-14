# encoding: utf-8


from .step import Step
import subprocess, logging

_logger = logging.getLogger(__name__)


def exec(argv):
    _logger.debug('🏃‍♀️ Running «%r»', argv)
    cp = subprocess.run(argv, stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
    _logger.debug('🏁 Run complete, rc=%d, output=%s', cp.returncode, cp.stdout)


def populateEnvVars(env):
    copy = dict(env)
    pypi_username = copy.get('pypi_username', 'pypi')
    pypi_password = copy.get('pypi_password', 'secret')
    copy['pypi_username'] = pypi_username
    copy['pypi_password'] = pypi_password

    for var in ('GITHUB_TOKEN', 'GITHUB_REPOSITORY'):
        if var not in env:
            _logger.warn('⚠️ «%s» not found in environment; some steps may fail', var)

    return copy


class NullStep(Step):
    def execute(self):
        pass


class ChangeLogStep(Step):
    _sections = '{"improvements":{"prefix":"**Improvements:**","labels":["Epic"]},"defects":{"prefix":"**Defects:**","labels":["bug"]},"deprecations":{"prefix":"**Deprecations:**","labels":["deprecation"]}}'

    def execute(self):
        token = self.assembly.context.environ.get('ADMIN_GITHUB_TOKEN')
        if not token:
            _logger.info('🤷‍♀️ No ADMIN_GITHUB_TOKEN; cannot generate Changelog')
            return

        # 🤔 TODO: Maybe this should take into account the owner of a repo as well?
        repo = self.assembly.context.environ.get('GITHUB_REPOSITORY').split('/')[1]

        exec([
            'github_changelog_generator',
            '--user',
            '--NASA-PDS',
            '--project',
            repo,
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

