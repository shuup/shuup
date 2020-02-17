# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os
import subprocess
import sys


def get_pip_path():
    """
    Try to figure out an explicit path to the Pip executable script.

    :return: Pip path
    :rtype: str
    """
    try:
        from virtualenv import path_locations
        (home_dir, lib_dir, inc_dir, bin_dir) = path_locations(sys.prefix)
        return os.path.join(bin_dir, "pip")
    except ImportError:
        pass
    return "pip"


class PackageInstaller(object):
    def __init__(self):
        self._log_buffer = b""

    def install_package(self, package_path):
        cmd = [
            get_pip_path(),
            "install",
            "--upgrade",
            "--verbose",
            "--require-venv",
            "--no-cache-dir",
            package_path
        ]
        pipe = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=_is_shell_needed_for_subprocess_calls(),
        )
        stdout, _ = pipe.communicate()
        self._log_buffer += stdout
        if pipe.returncode != 0:
            raise subprocess.CalledProcessError(pipe.returncode, cmd)

    def get_log(self):
        return self._log_buffer.decode("utf-8", "replace")


def _is_shell_needed_for_subprocess_calls():
    """
    Check if current environment needs shell for running subprocess calls.

    Essentially return True for Windows and False otherwise.  See
    http://bugs.python.org/issue6689 for details.
    """
    return (os.name == 'nt')
