/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.onProductSubscriptionSelectionChange = function (element) {
  const optionsListGroup = $(element).closest('.product-purchase-options-list-group');

  // uncheck all
  optionsListGroup
    .find("input[name='purchase-option']")
    .prop("checked", null);

  // check subscription
  optionsListGroup
    .find("input[name='purchase-option'][value='subscription']")
    .prop("checked", "checked");
};

window.onProductPurchaseOptionChange = function (element) {
  $(element)
    .closest('.product-purchase-options-list-group')
    .find(".list-group-item")
    .removeClass("selected");

  $(element)
    .closest(".list-group-item")
    .addClass("selected");
};
