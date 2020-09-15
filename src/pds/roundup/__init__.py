# encoding: utf-8

'''🤠 PDS Roundup: Continuous Integration and Development'''

from .context import Context
from .step import Step
import pkg_resources


def contextFactories():
    # ☑️ TODO: Think about a priority list instead of a dictionary.
    #
    # For example, we could have a PythonBuildoutContext which has setup.cfg, setup.py, but also
    # buildout.cfg and bootstrap.py; if we detect those, we can do a builout-based context instead
    # of a plain Python context.
    from ._python import PythonContext
    from ._maven import MavenContext
    return {
        'setup.cfg':   PythonContext,
        'setup.py':    PythonContext,
        'pom.xml':     MavenContext,
        'project.xml': MavenContext
    }


def _read_version():
    '''In Python 3.8, we should use ``importlib.metadata`` instead. But until then,
    we keep version information in a separate ``VERSION.txt`` file. Note that this file
    cannot contain any extra comments and we assume it's text witn bytes encoded in
    utf-8.
    '''
    return pkg_resources.resource_string(__name__, 'VERSION.txt').decode('utf-8').strip()


__version__ = VERSION = _read_version()


__all__ = (
    __version__,
    VERSION,
    Context,
    Step,
)
