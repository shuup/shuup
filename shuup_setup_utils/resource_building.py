# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import hashlib
import os
import shutil
import subprocess
import tempfile

from . import excludes
from .nodejs_verify import verify_nodejs

CACHE_ROOT = (
    os.path.expanduser('~/.cache') if os.name == 'posix'
    else tempfile.gettempdir())


class Options(object):
    """
    Options for resource building.

    :ivar directories: directories to build in, or all, if contains '.'
    :ivar production: build in production mode (default is development)
    :ivar clean: clean intermediate build files before building
    :ivar force: rebuild even if cached result exists
    """
    directories = '.'
    production = False
    clean = False
    force = False


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
        self.command = 'npm run build'.split()
        self.env = os.environ.copy()
        self.env['NODE_ENV'] = 'production' if self.opts.production else ''
        self.env['CI'] = 'true'
        self.cache_base = os.path.join(CACHE_ROOT, 'shuup', 'build_resources')

        self._cachedirs = {}
        self._result_files = {}

    def build_all(self):
        package_json_dirs = list(self._find_package_json_dirs())
        self.build_dirs(package_json_dirs)

    def _find_package_json_dirs(self):
        items = excludes.walk_excl(self.root_directory)
        for (dirpath, dirnames, filenames) in items:
            if 'package.json' in filenames:
                if 'generated_resources.txt' in filenames:
                    yield dirpath
                else:
                    package = json.load(open(os.path.join(dirpath, "package.json")))
                    if package.get("shuup", {}).get("static_build"):
                        yield dirpath

    def build_dirs(self, directories):
        for (i, dir) in enumerate(directories, 1):
            print("*** (%d/%d) Building: %s" % (i, len(directories), dir))  # noqa
            self.build(dir)

    def build(self, dir):
        if not self.opts.force:
            cached_result = self._get_cached_build_result(dir)
            if cached_result:
                self._update_from_cached_result(dir, cached_result)
                return
        self._run_build(dir)
        self._save_to_cache(dir)

    def _run_build(self, dir):
        if self.opts.clean:
            for dir_to_clean in self.dirs_to_clean:
                remove_all_subdirs(dir, dir_to_clean)

        shell = (os.name == 'nt')  # Windows needs shell, since npm is .cmd
        subprocess.check_call(self.command, cwd=dir, env=self.env, shell=shell)

    def _save_to_cache(self, dir):
        cdir = self._get_cachedir_for(dir)
        print("Saving build result of %s" % dir)  # noqa
        files = self._get_result_files(dir)
        self._copy_files(files, src=dir, dest=cdir, message="Caching to")

    def _get_cached_build_result(self, dir):
        result = self._get_cachedir_for(dir)
        if os.path.isdir(result):
            return result
        return None

    def _update_from_cached_result(self, dir, cached_result):
        print("Using cached result from %s" % cached_result)  # noqa
        files = self._get_result_files(dir)
        self._copy_files(files, src=cached_result, dest=dir,
                         message="Updating from cache")

    def _copy_files(self, files, src, dest, message=''):
        for filepath in files:
            srcpath = os.path.join(src, filepath)
            destpath = os.path.join(dest, filepath)
            if message:
                print('{}: {}'.format(message, destpath))  # noqa
            if os.path.exists(srcpath):
                destdir = os.path.dirname(destpath)
                if not os.path.isdir(destdir):
                    os.makedirs(destdir)
                shutil.copy(srcpath, destpath)
            elif os.path.exists(destpath):
                os.remove(destpath)

    def _get_cachedir_for(self, dir):
        cachedir = self._cachedirs.get(dir)
        if not cachedir:
            tag = 'prod' if self.opts.production else 'dev'
            hash = self._get_dir_hash(dir)
            cachedir = os.path.join(self.cache_base, tag, hash[:2], hash[2:])
            self._cachedirs[dir] = cachedir
        return cachedir

    def _get_dir_hash(self, dir):
        ignores = set(
            os.path.join(dir, ignored_item)
            for ignored_item in self._get_result_files(dir))

        def ignorer(fullpath):
            basename = os.path.basename(fullpath)
            is_excluded_filename = excludes.is_excluded_filename
            return (is_excluded_filename(basename) or fullpath in ignores)

        return hash_path_recursively(dir, ignorer)['checksum'].hexdigest()

    def _get_result_files(self, dir):
        result_files = self._result_files.get(dir)
        if result_files is None:
            result_files = []
            list_file_path = os.path.join(dir, 'generated_resources.txt')
            if os.path.exists(list_file_path):
                with open(list_file_path, 'rt') as fp:
                    for line in fp:
                        stripped_line = line.strip()
                        if stripped_line and not stripped_line.startswith('#'):
                            file_path = stripped_line.replace('/', os.path.sep)
                            result_files.append(file_path)
            self._result_files[dir] = result_files
        return result_files


def hash_path_recursively(path, ignorer=None, hasher=hashlib.sha1):
    checksum = hasher()
    size = 0
    if os.path.isdir(path):
        tp = 'dir'
        checksum.update(b'DIR:\n')
        for item in sorted(os.listdir(path)):
            fullpath = os.path.join(path, item)
            if ignorer and ignorer(fullpath):
                continue
            item_res = hash_path_recursively(fullpath, ignorer, hasher)
            if item_res['type'] == 'dir' and item_res['size'] == 0:
                continue  # Ignore empty directories
            digest = item_res['checksum'].digest()
            line = digest + b' ' + item.encode('utf-8') + b'\n'
            checksum.update(line)
            size += 1
    else:
        tp = 'file'
        with open(path, 'rb') as fp:
            data = b'FILE:\n'
            while data:
                checksum.update(data)
                data = fp.read(65536)
                size += len(data)
    return {'checksum': checksum, 'size': size, 'type': tp}


def remove_all_subdirs(root, subdir_name):
    for (dirpath, dirnames, filenames) in os.walk(root):
        if subdir_name in dirnames:
            dir_to_remove = os.path.join(dirpath, subdir_name)
            dirnames[:] = [dn for dn in dirnames if dn != subdir_name]
            print('Removing directory %s' % dir_to_remove)  # noqa
            shutil.rmtree(dir_to_remove)
