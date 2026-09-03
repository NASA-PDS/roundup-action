# encoding: utf-8

'''🤠 PDS Roundup — Utilities'''

from .errors import InvokedProcessError, RoundupError
import subprocess, logging, re, os


_logger = logging.getLogger(__name__)


# Constants
# =========

TAG_RE = re.compile(r'^release/(\d+)\.(\d+)(\.(\d+))?')
RC_TAG_RE = re.compile(r'^release/(\d+)\.(\d+)\.(\d+)-rc\.(\d+)$')
VERSION_RE = re.compile(r'^v(\d+)\.(\d+)\.(\d+)')


# Functions
# =========

def populateEnvVars(env):
    '''Populate the environment variable mapping in ``env`` with our "standard" set of variables
    required by a roundup. Return a copy of this modified mapping. Note that we may also log
    some warning messages if certain expected variables are missing.
    '''
    copy                            = dict(env)
    pypi_username                   = copy.get('pypi_username', 'pypi')
    pypi_password                   = copy.get('pypi_password', 'secret')
    central_portal_username         = copy.get('central_portal_username', 'ossrh')
    central_portal_token            = copy.get('central_portal_token', 'secret')
    java_home                       = copy.get('JAVA_HOME', '/usr/lib/jvm/default-jvm')
    copy['pypi_username']           = pypi_username
    copy['pypi_password']           = pypi_password
    copy['central_portal_username'] = central_portal_username
    copy['central_portal_token']    = central_portal_token
    copy['JAVA_HOME']               = java_home

    for var in ('GITHUB_REPOSITORY',):  # List other important vars here
        if var not in env:
            _logger.warn('⚠️ «%s» not found in environment; some steps may fail', var)

    # NASA-PDS/roundup-action#160 — ensure the GITHUB_REF_NAME environment variable is set
    # and if missing, use the reasonable default of `main``. This is provided to all Steps
    # via the Context object.
    copy['GITHUB_REF_NAME'] = env.get('GITHUB_REF_NAME', 'main')

    return copy


def add_version_label_to_open_bugs(version):
    _logger.info('Per NASA-PDS/roundup-action#145 we are no longer adding a version label to open bugs')
    # The rest of this function is commented out for NASA-PDS/roundup-action#145; it remains
    # for posterity:
    #
    # _logger.debug('Adding version label to open bugs')
    # owner, repo = os.getenv('GITHUB_REPOSITORY').split('/')
    # invoke([
    #     'add-version-label-to-open-bugs', '--labelled-version', version,
    #     '--token', os.getenv('ADMIN_GITHUB_TOKEN'), '--github-org', owner, '--github-repo', repo,
    # ])


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


def get_rc_number(tag):
    '''Return the RC number from a tag like ``release/X.Y.Z-rc.N``, or ``None`` if not an RC tag.'''
    match = RC_TAG_RE.match(tag)
    return int(match.group(4)) if match else None


def get_branch_from_tag(tag_name):
    '''Return the single remote branch that contains the commit pointed to by ``tag_name``.
    Raises ``RoundupError`` if the commit is reachable from multiple branches, since roundup
    cannot determine which branch to target in that case.
    Falls back to ``get_default_branch()`` if no branch can be found.
    '''
    try:
        result = invokeGIT(['branch', '-r', '--contains', tag_name])
        branches = []
        for line in result.strip().split('\n'):
            line = line.strip()
            if not line or '->' in line:
                continue
            if line.startswith('origin/'):
                line = line[len('origin/'):]
            branches.append(line)

        if len(branches) == 1:
            _logger.debug('🌿 Tag "%s" is on branch: %s', tag_name, branches[0])
            return branches[0]

        if len(branches) > 1:
            raise RoundupError(
                f'The commit for tag "{tag_name}" was found on multiple branches: {branches}. '
                f'Roundup does not support this case. Please recreate the tag on a commit that '
                f'belongs to only one branch.'
            )

    except InvokedProcessError:
        _logger.debug('🔍 Could not determine branch for tag "%s" via git branch -r --contains', tag_name)

    _logger.debug('🌿 No branch found for tag "%s", falling back to default branch', tag_name)
    return get_default_branch()


def get_default_branch():
    '''Determine the default branch for the repository. Tries multiple methods:
    1. Check git ls-remote --symref for origin HEAD (most reliable)
    2. Try git symbolic-ref for origin/HEAD (if already fetched)
    3. Try "main" branch
    4. Try "develop" branch
    5. Fall back to "main"
    '''
    # First, try to get the default branch directly from the remote using ls-remote --symref
    try:
        result = invokeGIT(['ls-remote', '--symref', 'origin', 'HEAD'])
        # Result will be like "ref: refs/heads/main\t<commit-hash>" or "ref: refs/heads/develop\t<commit-hash>"
        for line in result.strip().split('\n'):
            if line.startswith('ref: refs/heads/'):
                branch = line.split('refs/heads/')[1].split('\t')[0]
                if branch:
                    _logger.debug('🌿 Found default branch via ls-remote --symref: %s', branch)
                    return branch
    except InvokedProcessError:
        _logger.debug('🔍 Could not determine default branch via ls-remote --symref, trying alternatives')

    # Try to get the default branch from local origin/HEAD (if already fetched)
    try:
        result = invokeGIT(['symbolic-ref', 'refs/remotes/origin/HEAD'])
        # Result will be like "refs/remotes/origin/main" or "refs/remotes/origin/develop"
        branch = result.strip().replace('refs/remotes/origin/', '')
        if branch:
            _logger.debug('🌿 Found default branch via symbolic-ref: %s', branch)
            return branch
    except InvokedProcessError:
        _logger.debug('🔍 Could not determine default branch via symbolic-ref, trying alternatives')

    # Try checking if "develop" exists as a remote branch
    try:
        result = invokeGIT(['ls-remote', '--heads', 'origin', 'develop'])
        if result.strip():
            _logger.debug('🌿 Found "develop" branch as default')
            return 'develop'
    except InvokedProcessError:
        pass

    # Try checking if "main" exists as a remote branch
    try:
        result = invokeGIT(['ls-remote', '--heads', 'origin', 'main'])
        if result.strip():
            _logger.debug('🌿 Found "main" branch as default')
            return 'main'
    except InvokedProcessError:
        pass

    # All else fails, let's just use `main`
    _logger.debug('🌿 Using "main" as default branch fallback')
    return 'main'


def git_pull(branch_ref_name='main'):
    # 😮 TODO: Use Python GitHub API
    # But I'm in a rush:
    git_config()
    # NASA-PDS/roundup-action#160 — pull from the named branch reference
    # --no-rebase required since git 2.27 which mandates explicit reconciliation strategy
    invokeGIT(['pull', '--no-rebase', 'origin', branch_ref_name])


def commit(filename, message, branch_ref_name='main'):
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
        invokeGIT(['pull', '--no-rebase', '--quiet', '--no-edit', '--no-stat', branch_ref_name])
    except InvokedProcessError:
        _logger.info('🔁 Pull before push to HEAD:%s failed but pressing on', branch_ref_name)
        pass
    invokeGIT(['push', 'origin',  f'HEAD:{branch_ref_name}', '--force'])


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
