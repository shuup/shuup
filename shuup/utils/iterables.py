# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


def first(iterable, default=None):
    """
    Get the first item from the iterable, if possible, or return `default`.

    The iterable is, naturally, iterated for one value.

    :param iterable: An iterable.
    :type iterable: Iterable
    :param default: Default value
    :type default: object
    :return: The first item from the iterable, or `default`
    :rtype: object
    """
    for x in iterable:
        return x
    return default


def batch(iterable, count):
    """
    Yield batches of `count` items from the given iterable.

    >>> tuple(x for x in batch([1, 2, 3, 4, 5, 6, 7], 3))
    ([1, 2, 3], [4, 5, 6], [7])

    :param iterable: An iterable
    :type iterable: Iterable
    :param count: Number of items per batch. If <= 0, nothing is yielded.
    :type count: int
    :return: Iterable of lists of items
    :rtype: Iterable[list[object]]
    """
    if count <= 0:
        return
    current_batch = []
    for item in iterable:
        if len(current_batch) == count:
            yield current_batch
            current_batch = []
        current_batch.append(item)
    if current_batch:
        yield current_batch
