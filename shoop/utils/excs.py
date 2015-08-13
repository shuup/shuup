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

    def __init__(self, message, title=None):
        super(Problem, self).__init__(message)
        self.title = title
        self.links = []

    def with_link(self, url, title):
        """
        Append a link to this Problem and return itself.

        This API is designed after `Exception.with_traceback()`,
        so you can fluently chain this in a `raise` statement:

        >>> raise Problem("Oops").with_link("...", "...")

        :param url: URL string
        :type url: str
        :param title: Title text
        :type title: str
        :return: This same Problem
        :rtype: shoop.utils.excs.Problem
        """
        self.links.append({"url": url, "title": title})
        return self


class ExceptionalResponse(Exception):
    def __init__(self, response):
        self.response = response
        super(ExceptionalResponse, self).__init__(force_text(response))
