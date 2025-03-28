# encoding: utf-8
#
# Refactored from lasso.requirements to reduce coupling and dependency traffic jams

import os.path, logging

_logger = logging.getLogger(__name__)


class VersionDetective(object):
    '''🕵️‍♀️ Abstract detective for a version of a Python package given its source code.'''

    def __init__(self, workspace: str):
        self.workspace = workspace

    def findfile(self, fn: str):
        '''Utility method: Find the file named ``fn`` in the workspace and return its path.

        Return None if it's not found. Handy for subclasses.
        '''
        path = os.path.join(self.workspace, fn)
        return path if os.path.isfile(path) else None

    def detect(self):
        '''Detect the version of the Python package in the source code ``workspace`` and return it.

        Return None if we can't figure it out.
        '''
        raise NotImplementedError("Subclasses must implement ``VersionDetective.detect``")


class TextFileDetective(VersionDetective):
    '''Detective that looks for a ``version.txt`` file of some kind for a version indication.'''

    @classmethod
    def locate_file(cls, root_dir):
        src_dir = os.path.join(root_dir, "src")
        if not os.path.isdir(src_dir):
            raise ValueError("Unable to locate ./src directory in workspace.")

        version_file = None
        for dirpath, _dirnames, filenames in os.walk(src_dir):
            for fn in filenames:
                if fn.lower() == "version.txt":
                    version_file = os.path.join(dirpath, fn)
                    _logger.debug("🪄 Found a version.txt in %s", version_file)
                    break

        return version_file

    def detect(self):
        version_file = self.locate_file(self.workspace)
        if version_file is not None:
            with open(version_file, "r") as inp:
                return inp.read().strip()
        else:
            return None
