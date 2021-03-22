from django.core.exceptions import ValidationError

from shuup.utils.django_compat import force_text

# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class Problem(Exception):
    """ User-visible exception. """

    message = property(lambda self: self.args[0] if self.args else None)

    def __init__(self, message, title=None):
        super(Problem, self).__init__(message)
        self.title = title
        self.links = []

    def with_link(self, url, title):
        """
        Append a link to this Problem and return itself.

        This API is designed after `Exception.with_traceback()`,
        so you can fluently chain this in a `raise` statement::

            raise Problem("Oops").with_link("...", "...")

        :param url: URL string.
        :type url: str
        :param title: Title text.
        :type title: str
        :return: This same Problem.
        :rtype: shuup.utils.excs.Problem
        """
        self.links.append({"url": url, "title": title})
        return self


class ExceptionalResponse(Exception):
    def __init__(self, response):
        self.response = response
        super(ExceptionalResponse, self).__init__(force_text(response))


def extract_messages(obj_list):
    """
    Extract "messages" from a list of exceptions or other objects.

    For ValidationErrors, `messages` are flattened into the output.
    For Exceptions, `args[0]` is added into the output.
    For other objects, `force_text` is called.

    :param obj_list: List of exceptions etc.
    :type obj_list: Iterable[object]
    :rtype: Iterable[str]
    """
    for obj in obj_list:
        if isinstance(obj, ValidationError):
            for msg in obj.messages:
                yield force_text(msg)
            continue
        if isinstance(obj, Exception):
            if len(obj.args):
                yield force_text(obj.args[0])
                continue
        yield force_text(obj)
