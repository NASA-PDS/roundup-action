# encoding: utf-8


from .context import Context
from .util import populateEnvVars
import os, logging, argparse, sys


def _parseArgs():
    parser = argparse.ArgumentParser(
        description='🤠 PDS Roundup helps corral software for the Planetary Data System',
    )

    parser.add_argument(
        '-c', '--context', default=os.environ.get('GITHUB_WORKSPACE', os.getcwd()),
        help='🗺 Context directory where the roundup should happen, default %(default)s'
    )
    parser.add_argument(
        '-m', '--mode', default='unstable',
        help='🤪 Unstable, stable, or other mode; default %(default)s'
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
    args = _parseArgs()
    logging.basicConfig(level=args.loglevel)
    context = Context.create(os.getcwd(), populateEnvVars(os.environ))
    if args.mode == 'stable':
        from .assembly import StablePDSAssembly
        assembly = StablePDSAssembly(context)
    else:
        from .assembly import UnstablePDSAssembly
        assembly = UnstablePDSAssembly(context)
    assembly.roundup()
    sys.exit(0)


if __name__ == '__main__':
    main()
