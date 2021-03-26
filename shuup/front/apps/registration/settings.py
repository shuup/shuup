# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
#: Require email-based activation for users?
#:
#: This corresponds to using the `default` or `simple`
#: `django-registration` backends.
SHUUP_REGISTRATION_REQUIRES_ACTIVATION = True

#: The Shuup default registration form for person
#: This overrides the setting from `registration` lib
#: to allow custom logic like receiving the request from kwargs
REGISTRATION_FORM = "shuup.front.apps.registration.forms.PersonRegistrationForm"
