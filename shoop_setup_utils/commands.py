# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import distutils.command.build
import distutils.core
import distutils.errors

from . import resource_building


class BuildCommand(distutils.command.build.build):
    command_name = 'build'

    def get_sub_commands(self):
        super_cmds = distutils.command.build.build.get_sub_commands(self)
        my_cmds = [
            BuildProductionResourcesCommand.command_name,
        ]
        return super_cmds + my_cmds


class BuildResourcesCommand(distutils.core.Command):
    command_name = 'build_resources'
    description = "build Javascript and CSS resources"
    mode = 'development'
    clean = False
    force = False
    directory = '.'
    user_options = [
        ('mode=', 'm', "build mode: 'development' (default) or 'production'"),
        ('clean', 'c', "clean intermediate files before building"),
        ('force', 'f', "force rebuild even if cached result exists"),
        ('directory=', 'd', "directory to build in, or '.' for all (default)"),
    ]
    boolean_options = ['clean', 'force']

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
        resource_building.build_resources(opts)


class BuildProductionResourcesCommand(BuildResourcesCommand):
    command_name = 'build_production_resources'
    description = "build Javascript and CSS resources for production"
    mode = 'production'
    clean = True


COMMANDS = dict((x.command_name, x) for x in [
    BuildCommand,
    BuildResourcesCommand,
    BuildProductionResourcesCommand,
])
