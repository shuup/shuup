# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import os
import shutil
import subprocess

from . import excludes
from .nodejs_verify import verify_nodejs


class Options(object):
    """
    Options for resource building.

    :ivar directories: directories to build in, or all, if contains '.'
    :ivar production: build in production mode (default is development)
    :ivar clean: clean intermediate build files before building
    :ivar force: rebuild even if cached result exists
    :ivar no_install: do not install npm packages before building
    :ivar ci: whether the build is running inside a Continuous Integration environment
    """
    directories = '.'
    production = False
    clean = False
    force = False
    no_install = False
    ci = False


def build_resources(options):
    """
    Build resources.

    :type options: Options
    """
    verify_nodejs()
    builder = Builder('.', options)
    if '.' in options.directories:
        builder.build_all()
    else:
        builder.build_dirs(options.directories)


class Builder(object):
    def __init__(self, root_directory, options):
        self.root_directory = root_directory
        self.opts = options
        self.dirs_to_clean = ['node_modules', 'bower_components']
        self.install_command = ['npm', 'install']
        self.build_command = ['npm', 'run', 'build']
        self.env = os.environ.copy()
        self.env['NODE_ENV'] = 'production' if self.opts.production else ''
        self.env['CI'] = 'true'

        if self.opts.ci:
            self.install_command.append('--no-audit')

    def build_all(self):
        package_json_dirs = list(self._find_package_json_dirs())
        self.build_dirs(package_json_dirs)

    def _find_package_json_dirs(self):
        items = excludes.walk_excl(self.root_directory)
        for (dirpath, dirnames, filenames) in items:
            if 'package.json' in filenames:
                package = json.load(open(os.path.join(dirpath, "package.json")))
                if package.get("shuup", {}).get("static_build"):
                    yield dirpath

    def build_dirs(self, directories):
        for (i, dir) in enumerate(directories, 1):
            print("*** (%d/%d) Building: %s" % (i, len(directories), dir))  # noqa
            self.build(dir)

    def build(self, dir):
        if self.opts.clean:
            for dir_to_clean in self.dirs_to_clean:
                remove_all_subdirs(dir, dir_to_clean)

        shell = (os.name == 'nt')  # Windows needs shell, since npm is .cmd

        node_modules_exists = os.path.exists(os.path.join(dir, "node_modules"))
        if not self.opts.no_install or not node_modules_exists or self.opts.production:
            subprocess.check_call(self.install_command, cwd=dir, env=self.env, shell=shell)

        command = self.build_command
        if self.opts.force:
            command.append("--no-cache")

        subprocess.check_call(command, cwd=dir, env=self.env, shell=shell)


def remove_all_subdirs(root, subdir_name):
    for (dirpath, dirnames, filenames) in os.walk(root):
        if subdir_name in dirnames:
            dir_to_remove = os.path.join(dirpath, subdir_name)
            dirnames[:] = [dn for dn in dirnames if dn != subdir_name]
            print('Removing directory %s' % dir_to_remove)  # noqa
            shutil.rmtree(dir_to_remove)
