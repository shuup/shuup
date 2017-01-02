# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class CheckoutPhaseStorage(object):
    def __init__(self, request, phase_identifier):
        self.request = request
        self.phase_identifier = phase_identifier

    def reset(self):
        keys_to_pop = set()
        for key in self.request.session.keys():
            if key.startswith("checkout_%s:" % self.phase_identifier):
                keys_to_pop.add(key)
        for key in keys_to_pop:
            self.request.session.pop(key, None)

    def set(self, key, value):
        self.request.session["checkout_%s:%s" % (self.phase_identifier, key)] = value

    def get(self, key, default=None):
        return self.request.session.get("checkout_%s:%s" % (self.phase_identifier, key), default)

    def has_all(self, keys):
        return all(self.get(key) for key in keys)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        return self.get(key)
