# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import keyring
from django.conf import settings
from wheel import signatures
from wheel.install import WheelFile
from wheel.util import native


class WheelValidationFailed(Exception):
    pass


def verify_wheel(wheelfile):
    wf = WheelFile(wheelfile)
    sig_name = wf.distinfo_name + '/RECORD.jws'
    try:
        sig = json.loads(native(wf.zipfile.open(sig_name).read()))
    except KeyError:
        raise WheelValidationFailed("This wheel is not signed")
    verified = signatures.verify(sig)

    try:
        vk = verified[0][0]['jwk']['vk']
    except (KeyError, IndexError, ValueError):
        raise WheelValidationFailed("Invalid signature")

    if vk != settings.WHEEL_USER:
        raise WheelValidationFailed("Wheel validation failed")

    kr = keyring.get_keyring()
    password = kr.get_password("wheel", settings.WHEEL_USER)
    if password != settings.WHEEL_PASSWORD:
        raise WheelValidationFailed("Wheel validation failed")
