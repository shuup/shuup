# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils.iterables import batch


def cache_translations(objects, languages=None, meta=None):
    """
    Cache translation objects in given languages to the objects in one fell swoop.
    This will iterate a queryset, if one is passed!

    :param objects: List or queryset of Translatable models
    :param languages: Iterable of languages to fetch. In addition, all "_current_language"s will be fetched
    :return: objects
    """
    if not objects:
        return objects
    languages = set(languages or ())
    if meta is None:
        meta = objects[0]._parler_meta.root  # work on base model by default
    xlate_model = meta.model

    object_map = dict((object.pk, object) for object in objects)
    languages.update(set(object._current_language for object in objects))
    master_ids = object_map.keys()

    # SQLite limits host variables to 999 (see http://www.sqlite.org/limits.html#max_variable_number),
    # so we're batching to a number around that, with enough leeway for other binds (`languages` in particular).
    for master_ids in batch(master_ids, 950):
        for translation in xlate_model.objects.filter(master_id__in=master_ids, language_code__in=languages):
            master = object_map[translation.master_id]
            master._translations_cache[xlate_model][translation.language_code] = translation
            # FIXME: setattr(translation, translation.__class__.master.cache_name, master)
    return objects


def cache_translations_for_tree(root_objects, languages=None):
    """
    Cache translation objects in given languages, iterating MPTT trees.

    :param root_objects: List of MPTT models
    :type root_objects: Iterable[model]
    :param languages: List of languages
    :type languages: Iterable[str]
    """
    all_objects = {}

    def walk(object_list):
        for object in object_list:
            all_objects[object.pk] = object
            walk(object.get_children())

    walk(root_objects)
    cache_translations(list(all_objects.values()), languages=languages)
