# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
#: Require email-based activation for users?
#:
#: Configures the content subtype of the emails sent by Auth app
#: Set `html` if your template is HTML-based
#:
SHUUP_AUTH_EMAIL_CONTENT_SUBTYPE = 'plain'


#: Specify the authentication form to be used in login views
#:
SHUUP_AUTH_LOGIN_FORM_SPEC = 'shuup.front.apps.auth.forms.EmailAuthenticationForm'
