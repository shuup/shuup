import os
from fnmatch import fnmatch

_EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.py[cod]",
    "node_modules",
    "bower_components",
    ".tox",
    ".cache",
    "venv*",
    ".git",
    ".gitignore",
]


def add_exclude_patters(excludes):
    global _EXCLUDE_PATTERNS
    for exclude in excludes:
        if exclude not in _EXCLUDE_PATTERNS:
            _EXCLUDE_PATTERNS.append(exclude)


def set_exclude_patters(excludes):
    global _EXCLUDE_PATTERNS
    _EXCLUDE_PATTERNS = excludes


def get_exclude_patterns():
    return _EXCLUDE_PATTERNS


def walk_excl(path, **kwargs):
    """
    Do os.walk dropping our excluded directories on the way.
    """
    for (dirpath, dirnames, filenames) in os.walk(path, **kwargs):
        dirnames[:] = [dn for dn in dirnames if not is_excluded_filename(dn)]
        yield (dirpath, dirnames, filenames)


def is_excluded_filename(filename):
    return any(fnmatch(filename, pat) for pat in _EXCLUDE_PATTERNS)
