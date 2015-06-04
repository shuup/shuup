from django.utils.encoding import force_text
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.


class Problem(Exception):
    """ User-visible exception """

    message = property(lambda self: self.args[0] if self.args else None)


class ExceptionalResponse(Exception):
    def __init__(self, response):
        self.response = response
        super(ExceptionalResponse, self).__init__(force_text(response))
