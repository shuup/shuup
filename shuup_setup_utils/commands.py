# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import distutils.core
import distutils.errors
import os
import subprocess
from distutils.command.build import build as du_build

from setuptools.command.build_py import build_py as st_build_py

from . import excludes, resource_building


class BuildCommand(du_build):
    command_name = 'build'

    def get_sub_commands(self):
        super_cmds = du_build.get_sub_commands(self)
        my_cmds = [
            BuildProductionResourcesCommand.command_name,
            BuildMessagesCommand.command_name,
        ]
        return my_cmds + super_cmds


class BuildPyCommand(st_build_py):
    command_name = 'build_py'

    def find_package_modules(self, package, package_dir):
        modules = st_build_py.find_package_modules(
            self, package, package_dir)
        return list(filter(_is_included_module, modules))


def _is_included_module(package_module_file):
    module = package_module_file[1]
    return not excludes.is_excluded_filename(module + '.py')


class BuildResourcesCommand(distutils.core.Command):
    command_name = 'build_resources'
    description = "build Javascript and CSS resources"
    mode = 'development'
    clean = False
    force = False
    no_install = False
    ci = False
    directory = '.'
    user_options = [
        ('mode=', 'm', "build mode: 'development' (default) or 'production'"),
        ('clean', 'c', "clean intermediate files before building"),
        ('force', 'f', "force rebuild even if cached result exists"),
        ('no-install', 'n', "do not install npm packages before building"),
        ('ci', 't', "indicates that this build is running inside a Continuous Integration environment"),
        ('directory=', 'd', "directory to build in, or '.' for all (default)"),
    ]
    boolean_options = ['clean', 'force', 'no-install']

    def initialize_options(self):
        pass

    def finalize_options(self):
        # Allow abbreviated mode, like d, dev, p, or prod
        for mode in ['development', 'production']:
            if self.mode and mode.startswith(self.mode):
                self.mode = mode
        if self.mode not in ['development', 'production']:
            raise distutils.errors.DistutilsArgError(
                "Mode must be 'development' or 'production'")

    def run(self):
        opts = resource_building.Options()
        opts.directories = [self.directory]
        opts.production = (self.mode == 'production')
        opts.clean = self.clean
        opts.force = self.force
        opts.no_install = self.no_install
        opts.ci = self.ci
        resource_building.build_resources(opts)


class BuildProductionResourcesCommand(BuildResourcesCommand):
    command_name = 'build_production_resources'
    description = "build Javascript and CSS resources for production"
    mode = 'production'
    clean = True


class BuildMessagesCommand(distutils.core.Command):
    command_name = 'build_messages'
    description = "compile message catalogs via Django compilemessages"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        appdirs = set()
        rootdir = os.getcwd()
        for (dirpath, dirnames, filenames) in os.walk(rootdir):
            # Filter out hidden directories (.git, .svn, .tox, etc.)
            for dirname in list(dirnames):
                if dirname.startswith('.'):
                    dirnames.remove(dirname)
            if 'LC_MESSAGES' in dirnames:
                parent_dir = os.path.dirname(dirpath)
                if os.path.basename(parent_dir) == 'locale':
                    appdirs.add(os.path.dirname(parent_dir))

        # Have to clear DJANGO_SETTINGS_MODULE to make sure it does not
        # get into way when compiling messages, since sometimes it might
        # be set to e.g. 'shuup_workbench.settings' but if we're in
        # middle of installing Shuup, then management commands will fail
        # because shuup_workbench is not yet installed.
        env = dict(os.environ, DJANGO_SETTINGS_MODULE='')
        command = ['django-admin', 'compilemessages']

        for appdir in sorted(appdirs):
            subprocess.check_call(command, env=env, cwd=appdir)


COMMANDS = dict((x.command_name, x) for x in [
    BuildCommand,
    BuildPyCommand,
    BuildResourcesCommand,
    BuildProductionResourcesCommand,
    BuildMessagesCommand,
])
