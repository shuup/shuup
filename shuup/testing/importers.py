# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.core.models import Contact, PersonContact
from shuup.importer.importing import DataImporter, ImporterExampleFile


class DummyImporter(DataImporter):
    identifier = "dummy_importer"
    name = "Dummy Importer"
    model = Contact

    example_files = [
        ImporterExampleFile("sample_dummy_importer.csv", "text/csv", "shuup_testing/sample_dummy_importer.jinja")
    ]

    def get_related_models(self):
        return [Contact, PersonContact]

    def get_row_model(self, row):
        return PersonContact


class DummyFileImporter(DataImporter):
    identifier = "dummy_file_importer"
    name = "Dummy File Importer"
    model = Contact

    example_files = [
        ImporterExampleFile("doesn_exit.csv", "text/csv")
    ]

    def get_related_models(self):
        return [Contact, PersonContact]

    def get_row_model(self, row):
        return PersonContact

    @classmethod
    def get_example_file_content(cls, example_file, request):
        return None
