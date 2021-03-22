# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import subprocess


def get_version(version, root, version_file):
    """
    Get version from given version or from git or from version_file.

    If version does not contain string 'dev', it is used as is.
    Otherwise if we're inside a Git checkout, we'll try to get version
    with "git describe" and if we're not in a git checkout (e.g. we're
    in sdist package), then we'll return version from the version_file,
    which should have been written there when the package was created.
    """
    if "dev" not in version:
        return version

    git_repo_path = os.path.join(root, ".git")

    if os.path.exists(git_repo_path) and not os.path.isdir(git_repo_path):
        _remove_git_file_if_invalid(git_repo_path)

    if os.path.exists(git_repo_path):
        return _get_version_from_git(version, root) or version
    else:
        return _get_version_from_file(version_file, version) or version


def _remove_git_file_if_invalid(git_file_path):
    """
    Remove invalid .git file.

    This is needed, because .git file that points to non-existing
    directory will cause problems with build_resources, since some git
    commands are executed there and invalid .git file will cause them to
    fail with error like

      fatal: Not a git repository: ../.git/modules/shuup

    Invalid .git files are created when "pip install" copies shuup from
    a Git submodule to temporary build directory, for example.
    """
    with open(git_file_path, "rb") as fp:
        contents = fp.read(10000).decode("utf-8")
    if contents.startswith("gitdir: "):
        gitdir = contents.split(" ", 1)[1].rstrip()
        if not os.path.isabs(gitdir):
            gitdir = os.path.join(os.path.dirname(git_file_path), gitdir)
        if not os.path.exists(gitdir):
            os.remove(git_file_path)


def _get_version_from_git(version, root):
    tag_name = "v" + version.split(".post")[0].split(".dev")[0]
    describe_cmd = ["git", "describe", "--dirty", "--match", tag_name]
    try:
        described = subprocess.check_output(describe_cmd, cwd=root)
    except Exception:
        return None
    suffix = described.decode("utf-8")[len(tag_name) :].strip()
    cleaned_suffix = suffix[1:].replace("-g", "+g").replace("-dirty", ".dirty")
    return version + cleaned_suffix


def _get_version_from_file(version_file, version_prefix=""):
    verstr = ""
    if os.path.exists(version_file):
        with open(version_file, "rt") as fp:
            verstr = fp.read(100).strip()
    if verstr.startswith('__version__ = "' + version_prefix):
        return verstr.split('"', 2)[1]
    return None


def write_version_to_file(version, version_file):
    with open(version_file, "wt") as fp:
        fp.write('__version__ = "{version}"\n'.format(version=str(version)))
