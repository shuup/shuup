# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import re
import sys
from babel.messages.pofile import read_po
from rope.base.codeanalyze import ChangeCollector
from rope.base.project import Project
from rope.refactor.restructure import Restructure
from rope.refactor.similarfinder import CodeTemplate
from six import print_

safe_double_quote_re = re.compile(r"^[\w ]+$", re.UNICODE)


class LanguageTwist(CodeTemplate):
    def __init__(self, po_file):
        with open(po_file, "rb") as in_f:
            self.catalog = read_po(in_f)
        self.not_in_catalog = set()
        super(LanguageTwist, self).__init__(template="_(${str})")

    def get_names(self):
        return ["str"]

    def substitute(self, mapping):
        collector = ChangeCollector(self.template)
        for name, occurrences in self.names.items():
            for region in occurrences:
                original = mapping[name]
                result = self.twist(eval(original))
                collector.add_change(region[0], region[1], result)
        result = collector.get_changed()
        if result is None:
            return self.template
        return result

    def twist(self, string):
        if string in self.catalog:
            string = self.catalog[string].string
        else:
            if string not in self.not_in_catalog:
                self.not_in_catalog.add(string)
                print_("Not in catalog: %r" % string, file=sys.stderr)

        return repr(string)


def main():
    prj = Project(os.path.realpath("../shuup/core/models"))
    rst = Restructure(prj, "_(${str})", "")
    rst.template = LanguageTwist("./shuup_fi_to_en.po")

    twist_set = rst.get_changes()

    for chg in twist_set.changes:
        print(chg.get_description())  # noqa

    prj.do(twist_set)


if __name__ == "__main__":
    main()
