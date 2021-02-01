# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six

from shuup.importer.utils import get_global_aliases


class ImportMetaBase(object):

    fk_matchers = {}
    global_aliases = {}

    """
    Aliases for keys usually used in the importing meta

    This is dictionary that contains list of values:
        {shuup_field: [expected_fields]}

    Example:
        aliases = {
            "name_ext": ["extension", "ext"]
        }
    """
    aliases = {}

    """
    Post save handlers

    You can directly assign post save handler for a field. Field
    That has post save handler assigned won't be available for mapping and
    won't cause it to appear in unmapped fields in importer.

    The handler is being triggered if any of the given values in trigger
    list is being encountered while iterating.

    This is a dictionary that contains list of values:
        {function_name: [list_of_triggers]}

    Example:
        post_save_handlers = {
            "handle_row_address": ['city', 'country', 'postal code', 'region code', 'street'],
        }

        In this example the `handle_row_address` is being called when
        any of the triggers is being encountered.
    """
    post_save_handlers = {}

    """
    Fields to skip

    It's sometimes necessary to skip fields in importer.

    For now we are using this to skip image fields in `ProductMetaBase`.
    """
    fields_to_skip = []

    def __init__(self, handler, model):
        self.handler = handler  # shuup.importer.importing.importing.DataImporter
        self.model = model
        self.global_aliases = get_global_aliases()

    def get_import_defaults(self):
        """
        Get default values for importing

        If a certain value is required in import but does not exist
        in the imported file this method completes said missing data.

        Example:
            return {
                "type_id": ProductType.objects.first().id,
                "tax_class_id": TaxClass.objects.first().id,
            }

        :return: Dict of field name -> default value.
        :rtype: dict[str, str]|dict
        """
        return {}

    def should_skip_row(self, row):
        """
        Allows you to skip a row from getting imported

        Used to set up a condition for a row to get imported

        :param row: Current row data
        :type row: dict

        :return: True if the row should get skipped, False otherwise
        :rtype: bool
        """
        return False

    def pre_process_row(self, row):
        """
        Do a pre-processing task on the given row and change the data in place.

        This method is called befor the row_session is created
        to allow to override values on the row or to create related objects.

        :param row: Current row data
        :type row: dict

        :return: the row modified, if needed
        :rtype: dict
        """
        return row

    def presave_hook(self, row_session):
        """
        Pre-save Hook

        This method is called before the row session is saved.
        This can be used to add data into `row_session.instance`

        :param row_session: Current row session
        :type row_session: shuup.importer.importing.session.DataImporterRowSession
        :return: None
        """
        pass

    def postsave_hook(self, row_session):
        """
        Post-save Hook

        This method is called after the row session is saved.
        This can be used to create related objects.

        :param row_session: Current row session
        :type row_session: shuup.importer.importing.session.DataImporterRowSession
        :return: None
        """
        pass

    def mutate_normal_field_set(self, row_session, field, value, original):
        return value

    def has_post_save_handler(self, field_name):
        """
        See if meta has Post-Save handler

        :param field_name: Name of the field to lookup
        :return: True or False if has post save handler
        :rtype: Boolean
        """
        for func, fields in six.iteritems(self.post_save_handlers):
            if field_name in fields:
                return True
            for field in fields:
                for alias_field in self.aliases.get(field, []):
                    if field_name == alias_field:
                        return True
        return False

    @property
    def field_aliases(self):
        """
        Get all field aliases

        If local aliases are being set, global aliases are extended.
        :return: Dict key => list of aliases
        :rtype: dict[str, list]|dict
        """
        if self.aliases:
            aliases = self.global_aliases.copy()
            aliases.update(self.aliases)
            return aliases
        return self.global_aliases
