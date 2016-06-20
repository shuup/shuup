# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.campaigns.models.campaigns import CatalogCampaign

from ._base import BaseCampaignForm


class CatalogCampaignForm(BaseCampaignForm):
    class Meta(BaseCampaignForm.Meta):
        model = CatalogCampaign
        exclude = BaseCampaignForm.Meta.exclude + ["filters", "coupon"]
