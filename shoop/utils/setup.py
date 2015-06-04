# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.


class Setup(object):

    def __init__(self, load_from=None):
        self.commit(load_from)

    def is_valid_key(self, key):
        return key == key.upper() and not key.startswith("_")

    def commit(self, source):
        if source:
            if not hasattr(source, "items"):  # pragma: no cover
                source = vars(source)
            for key, value in source.items():
                if self.is_valid_key(key):
                    setattr(self, key, value)

    def values(self):
        for key, value in self.__dict__.items():
            if self.is_valid_key(key):  # pragma: no branch
                yield (key, value)

    def get(self, key, default=None):  # pragma: no cover
        return getattr(self, key, default)

    def getlist(self, key, default=()):  # pragma: no cover
        val = getattr(self, key, default)
        return list(val)

    @classmethod
    def configure(cls, configure):
        setup = cls()
        try:
            configure(setup)
        except:  # pragma: no cover
            print("@" * 80)
            import traceback
            import sys
            traceback.print_exc()
            print("@" * 80)
            sys.exit(1)
        return setup.values()
