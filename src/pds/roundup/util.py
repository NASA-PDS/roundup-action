# encoding: utf-8

'''🤠 PDS Roundup — Utilities'''

from .errors import InvokedProcessError
import subprocess, logging, re, os


_logger = logging.getLogger(__name__)


# Constants
# =========

TAG_RE = re.compile(r'^release/(\d+)\.(\d+)(\.(\d+))?')
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

    for var in ('GITHUB_REPOSITORY',):  # List other important vars here
        if var not in env:
            _logger.warn('⚠️ «%s» not found in environment; some steps may fail', var)

    return copy


def add_version_label_to_open_bugs(version):
    _logger.debug('Adding version label to open bugs')
    owner, repo = os.getenv('GITHUB_REPOSITORY').split('/')
    invoke([
        'add-version-label-to-open-bugs', '--labelled-version', version,
        '--token', os.getenv('ADMIN_GITHUB_TOKEN'), '--github-org', owner, '--github-repo', repo,
    ])


def invoke(argv):
    '''Execute a command within the operating system, returning its output. On any error,
    raise ane exception. The command is the first element of ``argv``, with remaining elements
    being arguments to the command.
    '''
    _logger.debug('🏃‍♀️ Running «%r»', argv)
    try:
        cp = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, check=True)
        _logger.debug('🏁 Run complete, rc=%d', cp.returncode)
        _logger.debug('Stdout = «%s»', cp.stdout.decode('utf-8'))
        _logger.debug('Stderr = «%s»', cp.stderr.decode('utf-8'))
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


def git_config():
    '''Prepare necessary git configuration or else things might fail'''

    # Starting with git 2.36, we need to tell git our directory is safe to use
    invokeGIT(['config', '--global', '--add', 'safe.directory', '/github/workspace'])

    # And give the bot its credit
    invokeGIT(['config', '--local', 'user.email', 'pdsen-ci@jpl.nasa.gov'])
    invokeGIT(['config', '--local', 'user.name', 'PDSEN CI Bot'])


def git_pull():
    # 😮 TODO: Use Python GitHub API
    # But I'm in a rush:
    git_config()
    invokeGIT(['pull', 'origin', 'main'])


def commit(filename, message):
    '''Commit the file named ``filename`` to the local Git repository with the given ``message``.
    '''
    _logger.debug('🥼 Committing file %s with message «%s»', filename, message)
    git_config()
    invokeGIT(['add', filename])
    invokeGIT(['commit', '--allow-empty', '--message', message])
    # TODO: understand why a simple push does not work and make it work
    # see bug https://github.com/actions/checkout/issues/317
    #
    # NASA-PDS/roundup-action#98 … @jimmie suggests putting a `git pull` before the push.
    # @jordanpadams says that he did see an issue where a push occurred during a Roundup.
    # @nutjob4life maintains that a `git pull` at this point would result in `Already up
    # to date` but we all guess it wouldn't hurt.
    try:
        _logger.info('WTF')
        invokeGIT(['branch'])
        invokeGIT(['pull', '--quiet', '--no-edit', '--no-stat'])
    except InvokedProcessError:
        _logger.info('🔁 Pull before push to HEAD:main failed but pressing on')
        pass
    invokeGIT(['push', 'origin',  'HEAD:main', '--force'])


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


def contextFactories():
    # ☑️ TODO: Think about a priority list instead of a dictionary.
    #
    # For example, we could have a PythonBuildoutContext which has setup.cfg, setup.py, but also
    # buildout.cfg and bootstrap.py; if we detect those, we can do a builout-based context instead
    # of a plain Python context.
    from ._python import PythonContext
    from ._maven import MavenContext
    from ._nodejs import NodeJSContext
    return {
        'setup.cfg':         PythonContext,
        'setup.py':          PythonContext,
        'pom.xml':           MavenContext,
        'project.xml':       MavenContext,
        'package.json':      NodeJSContext,
        'package-lock.json': NodeJSContext
    }


def delete_tags(pattern):
    '''Delete tags matching ``pattern``.'''
    try:
        invokeGIT(['fetch', '--prune', '--unshallow', '--tags', '--prune-tags', '--force'])
    except InvokedProcessError:
        _logger.info('🤔 Unshallow prune fetch tags failed, so trying without unshallow')
        invokeGIT(['fetch', '--prune', '--tags', '--prune-tags', '--force'])
    tags = invokeGIT(['tag', '--list', pattern]).split('\n')
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
