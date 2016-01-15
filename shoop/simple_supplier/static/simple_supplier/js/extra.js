/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function adjustStock(button) {
    event.preventDefault();
    var stockAdjustDiv = button.parent("div.form");
    var url = stockAdjustDiv.data("url");
    var data = stockAdjustDiv.find(":input").serialize();
    $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function(msg) {
            $(msg.stockInformationDiv).replaceWith(msg.updatedStockInformation);
            window.Messages.enqueue({tags: "info", text: msg.message});
        },
        error: function(response) {
            window.Messages.enqueue({tags: "error", text: response.responseJSON.message});
        }
    });
}
