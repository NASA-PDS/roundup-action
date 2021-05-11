# encoding: utf-8

'''🤠 PDS Roundup — Utilities'''

from .errors import InvokedProcessError
import subprocess, logging, re

_logger = logging.getLogger(__name__)


# Constants
# =========

BRANCH_RE = re.compile(r'^release/(\d+)\.(\d+)(\.(\d+))?')
VERSION_RE = re.compile(r'^v(\d+)\.(\d+)\.(\d+)')


# Functions
# =========

def populateEnvVars(env):
    '''Populate the environment variable mapping in ``env`` with our "standard" set of variables
    required by a roundup. Return a copy of this modified mapping. Note that we may also log
    some warning messages if certain expected variables are missing.
    '''
    copy                   = dict(env)
    pypi_username          = copy.get('pypi_username', 'pypi')
    pypi_password          = copy.get('pypi_password', 'secret')
    ossrh_username         = copy.get('ossrh_username', 'ossrh')
    ossrh_password         = copy.get('ossrh_password', 'secret')
    java_home              = copy.get('JAVA_HOME', '/usr/lib/jvm/default-jvm')
    copy['pypi_username']  = pypi_username
    copy['pypi_password']  = pypi_password
    copy['ossrh_username'] = ossrh_username
    copy['ossrh_password'] = ossrh_password
    copy['JAVA_HOME']      = java_home

    for var in ('GITHUB_TOKEN', 'GITHUB_REPOSITORY'):  # 🤔 TODO: is GITHUB_TOKEN really used?
        if var not in env:
            _logger.warn('⚠️ «%s» not found in environment; some steps may fail', var)

    return copy


def invoke(argv):
    '''Execute a command within the operating system, returning its output. On any error,
    raise ane exception. The command is the first element of ``argv``, with remaining elements
    being arguments to the command.
    '''
    _logger.debug('🏃‍♀️ Running «%r»', argv)
    try:
        cp = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, check=True)
        _logger.debug('🏁 Run complete, rc=%d, output=«%s»', cp.returncode, cp.stdout.decode('utf-8'))
        return cp.stdout.decode('utf-8')
    except subprocess.CalledProcessError as ex:
        _logger.critical('💥 Process with command line %r failed with status %d', argv, ex.returncode)
        _logger.critical('🪵 Stdout = «%s»', ex.stdout.decode('utf-8'))
        _logger.critical('📚 Stderr = «%s»', ex.stderr.decode('utf-8'))
        raise InvokedProcessError(ex)


def invokeGIT(gitArgs):
    '''Execute the ``git`` command with the given ``gitArgs``.'''

    # 😬 The code below is to avoid making ``git`` ask ``ssh`` for a host key
    # verification. This should only happen with repositories that use ssh as
    # their remote protocol, which I hope doesn't happen in Github Actions.
    # In development, though, this could have the side-effect of altering
    # the user's ``~/.ssh/config`` which is probably a terrible idea, so
    # I'm disabling this code for now:
    #
    # ↓↓↓ Begin disabled code below these arrow ↓↓↓
    # sshDir = os.path.join(os.environ.get('HOME', '/github/home'), '.ssh')
    # if not os.path.isdir(sshDir):
    #     os.mkdir(sshDir)
    # sshConf = os.path.join(os.path.join(sshDir, 'config'))
    # hostKeyCheckingFound = False
    # with open(sshConf, 'r') as f:
    #     for line in f:
    #         if 'StrictHostKeyChecking no' in line:
    #             hostKeyCheckingFound = True
    #             break
    # if not hostKeyCheckingFound:
    #     with open(sshConf, 'a') as f:
    #         f.write('StrictHostKeyChecking no\n')
    # ↑↑↑ End disabled code above these arrows ↑↑↑

    argv = ['git'] + gitArgs
    return invoke(argv)


def git_pull():
    # 😮 TODO: Use Python GitHub API
    # But I'm in a rush:
    invokeGIT(['config', '--local', 'user.email', 'pdsen-ci@jpl.nasa.gov'])
    invokeGIT(['config', '--local', 'user.name', 'PDSEN CI Bot'])
    invokeGIT(['pull', 'origin', 'master'])


def commit(filename, message):
    '''Commit the file named ``filename`` to the local Git repository with the given ``message``.
    '''
    invokeGIT(['add', filename])
    invokeGIT(['commit', '--allow-empty', '--message', message])
    # TODO: understand why a simple push does not work and make it work
    # see bug https://github.com/actions/checkout/issues/317
    invokeGIT(['push', 'origin',  'HEAD:master', '--force'])


def findNextMicro():
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
