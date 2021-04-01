# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils.text import camel_case, flatten, identifierify, kebab_case, snake_case, space_case


def test_casers():
    text = u"What is Love? Baby Don't Hurt Me"
    assert snake_case(text) == "what_is_love?_baby_don't_hurt_me"
    assert kebab_case(text) == "what-is-love?-baby-don't-hurt-me"
    assert camel_case(text) == "WhatIsLove?BabyDon'THurtMe"
    assert identifierify(snake_case(text)) == "what_is_love_baby_dont_hurt_me"
    assert identifierify(kebab_case(text), "-") == "what-is-love-baby-dont-hurt-me"
    assert identifierify(camel_case(text)) == "WhatIsLoveBabyDonTHurtMe"
    assert space_case("some_identifier") == "some identifier"


def test_flatten():
    text = "Whät is Löve? Bäby Don't Hurt Me"
    assert flatten(text) == "what-is-love?-baby-don't-hurt-me"
    assert flatten(text, "/") == "what/is/love?/baby/don't/hurt/me"
