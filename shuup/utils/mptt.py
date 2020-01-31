# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals


def get_cached_trees(queryset):
    """
    Takes a list/queryset of model objects in MPTT left (depth-first) order and
    caches the children and parent on each node. This allows up and down
    traversal through the tree without the need for further queries. Use cases
    include using a recursively included template or arbitrarily traversing
    trees.

    NOTE: nodes _must_ be passed in the correct (depth-first) order. If they aren't,
    a ValueError will be raised.

    Returns a list of top-level nodes. If a single tree was provided in its
    entirety, the list will of course consist of just the tree's root node.

    For filtered querysets, if no ancestors for a node are included in the
    queryset, it will appear in the returned list as a top-level node.

    Aliases to this function are also available:

    ``mptt.templatetags.mptt_tag.cache_tree_children``
       Use for recursive rendering in templates.

    ``mptt.querysets.TreeQuerySet.get_cached_trees``
       Useful for chaining with queries; e.g.,
       `Node.objects.filter(**kwargs).get_cached_trees()`

    FIXME: This method fixed the original `mptt.utils.get_cached_trees` method
    as it doesn't consider filtered querysets that might not contain all tree nodes.

    """

    current_path = []
    top_nodes = []

    if queryset:
        # Get the model's parent-attribute name
        parent_attr = queryset[0]._mptt_meta.parent_attr
        root_level = None
        is_filtered = (hasattr(queryset, "query") and queryset.query.has_filters())
        for obj in queryset:
            # Get the current mptt node level
            node_level = obj.get_level()

            if root_level is None or (is_filtered and node_level < root_level):
                # First iteration, so set the root level to the top node level
                root_level = node_level

            elif node_level < root_level:
                # ``queryset`` was a list or other iterable (unable to order),
                # and was provided in an order other than depth-first
                raise ValueError(
                    'Error! Node %s not in depth-first order.' % (type(queryset),)
                )

            # Set up the attribute on the node that will store cached children,
            # which is used by ``MPTTModel.get_children``
            obj._cached_children = []

            # Remove nodes not in the current branch
            while len(current_path) > node_level - root_level:
                current_path.pop(-1)

            if node_level == root_level:
                # Add the root to the list of top nodes, which will be returned
                top_nodes.append(obj)
            else:
                # Cache the parent on the current node, and attach the current
                # node to the parent's list of children
                _parent = current_path[-1]
                setattr(obj, parent_attr, _parent)
                _parent._cached_children.append(obj)

                if root_level == 0:
                    # get_ancestors() can use .parent.parent.parent...
                    setattr(obj, '_mptt_use_cached_ancestors', True)

            # Add the current node to end of the current path - the last node
            # in the current path is the parent for the next iteration, unless
            # the next iteration is higher up the tree (a new branch), in which
            # case the paths below it (e.g., this one) will be removed from the
            # current path during the next iteration
            current_path.append(obj)

    return top_nodes
