# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Optional


class ProductValidationIssue:
    """
    Class that represents an issue after a validation of a class AdminProductValidation is
    completed.
    """

    def __init__(self, message: str, issue_type: str, code: Optional[str] = None, is_html: bool = False):
        """
        :param code: The issue's error code.
        :type code: str
        :param message: The issue's alert message.
        :type message: str
        :param issue_type: The issue's type: can be `info`, `warning` or `error`.
        :type issue_type: str
        :param is_html: True if the message contains html code.
        :type is_html: bool
        """

        self.code = code
        self.message = message
        if issue_type not in ("error", "warning", "info"):
            raise ValueError("Error! Invalid value for issue_type.")
        self.issue_type = issue_type
        self.is_html = is_html

    def get_issue_type_priority(self):
        if self.issue_type == "info":
            return 3
        if self.issue_type == "warning":
            return 2
        return 1

    def get_alert_type(self):
        if self.issue_type == "error":
            return "danger"
        return self.issue_type

    def __str__(self):
        return self.message
