/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function adjustStock(event, button) {
    event.preventDefault();
    var stockAdjustDiv = button.parent("div.form");
    var url = stockAdjustDiv.data("url");
    var data = stockAdjustDiv.find(":input").serialize();
    $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function(msg) {
            $(msg.stockInformationDiv).html(msg.updatedStockInformation);
            window.Messages.enqueue({tags: "info", text: msg.message});
        },
        error: function(response) {
            window.Messages.enqueue({tags: "error", text: response.responseJSON.message});
        }
    });
}
