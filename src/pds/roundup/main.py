# encoding: utf-8


'''🤠 PDS Roundup: Main entrypoint'''


from .context import Context
from .errors import InvokedProcessError
from .util import populateEnvVars, invoke
from .assembly import (
    StablePDSAssembly, UnstablePDSAssembly, IntegrativePDSAssembly, NoOpAssembly, EnvironmentalAssembly
)
import os, logging, argparse, sys

_logger = logging.getLogger(__name__)

_assemblies = {
    'env':         EnvironmentalAssembly,
    'integration': IntegrativePDSAssembly,
    'noop':        NoOpAssembly,
    'stable':      StablePDSAssembly,
    'unstable':    UnstablePDSAssembly,
}
_defaultAssembly = 'unstable'


def _parseArgs():
    '''Parse the command line arguments and return a namespace'''
    parser = argparse.ArgumentParser(
        description='🤠 PDS Roundup helps corral software for the Planetary Data System',
    )

    parser.add_argument(
        '-c', '--context', default=os.environ.get('GITHUB_WORKSPACE', os.getcwd()),
        help='🗺 Context directory where the roundup should happen, default %(default)s'
    )
    parser.add_argument(
        '-a', '--assembly', default=_defaultAssembly, choices=_assemblies.keys(),
        help=f'🤪 Mode of assembly; default %(default)s'
    )
    parser.add_argument(
        '-p', '--packages',
        help='📦 Additional pacakges (separated with a comma) to install prior to assembly'
    )

    parser.add_argument(
        '-D', '--documentation-dir',
        help='📄 Directory where the online documentation is generated; '
             'default values are docs/build for Python and target/staging for Maven'
    )

    # Maven 😩
    group = parser.add_argument_group('Maven phases (or goals), comma-separated')
    group.add_argument('--maven-test-phases', help='🩺 Test (%(default)s)', default='test')
    group.add_argument('--maven-doc-phases', help='📚 Documentation (%(default)s)', default='clean,site,site:stage')
    group.add_argument('--maven-build-phases', help='👷‍ Build (%(default)s)', default='install')
    group.add_argument(
        '--maven-stable-artifact-phases',
        help='😌 Stable artifacts (%(default)s)', default='clean,site,site:stage,deploy'
    )
    group.add_argument(
        '--maven-unstable-artifact-phases',
        help='🤪 Unstable artifacts (%(default)s)',
        default='clean,site,deploy'
    )

    # Handle logging
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO,
        help='🔊 Log debugging messages; handy for developers'
    )
    group.add_argument(
        '-q', '--quiet', action='store_const', dest='loglevel', const=logging.WARNING,
        help="🤫 Don't log info messages; just warnings and critical notes"
    )
    return parser.parse_args()


def main():
    '''Main entrypoint'''
    args = _parseArgs()
    logging.basicConfig(level=args.loglevel)
    cwd = os.getcwd()
    context = Context.create(cwd, populateEnvVars(os.environ), args)
    if context is None:
        contents = ', '.join(os.listdir(cwd))
        _logger.critical("💥 No usable context in «%s»; note I can only handle Python and Maven projects so far", cwd)
        if not contents:
            _logger.critical('🤷‍♀️ The directory is empty; that might have something to do with it 😝')
        else:
            _logger.critical("🔎 Here's what's in that directory: %s", contents)
        sys.exit(1)

    # Bonus package time
    if args.packages:
        invoke(['apk', 'update'])
        for package in args.packages.split(','):
            try:
                _logger.debug('🎁 Adding package %s', package)
                invoke(['apk', 'add', '--no-progress', package])
            except InvokedProcessError:
                _logger.critical('💥 Cannot add package %s, aborting', package)
                sys.exit(1)

    # This belongs somewhere else; essentially the ``Context`` already captures the
    # environment, but we made invoking programs a utility function devoid of context.
    # Instead, ``invoke`` should be a method of ``Context``. But since it's close to
    # quitting time and I'm trying to solve a specific issue (#14), I'm doing this
    # ugly setting here:
    os.environ['JAVA_HOME'] = os.environ.get('JAVA_HOME', '/usr/lib/jvm/default-jvm')

    # Sanity check in GitHub Acions logs: show the version of ``pds-github-util`` by calling
    # ``--version`` on any one of its programs.
    version = invoke(['pds-issues', '--version']).strip()
    _logger.info('🗺 The version of ``lasso-issues`` I shall be using: %s', version)

    # Here we go daddy
    _assemblies[args.assembly](context).roundup()
    sys.exit(0)


if __name__ == '__main__':
    main()
