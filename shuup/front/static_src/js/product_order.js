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
