$(document).ready(function() {
    html5sortable(".sortable", {
        placeholder: "<div class=\"card\"></div>",
        forcePlaceholderSize: true,
        handle: ".fa-reorder",
        containerSerializer: function() {
            return null;
        },
        itemSerializer: function(serializedItem, sortableContainer) {
            var childrenList = $(serializedItem.node).children(".card");
            // var serializedChildren = [];
            // for (var i = 0; i < childrenList.length; i += 1) {
            //     var serialized = html5sortable(childrenList[i], "serialize");
            //     if (serialized && serialized.length && serialized[0].items.length) {
            //         serializedChildren.push(serialized[0]);
            //     }
            // }
            var node = $(serializedItem.node);
            return {
                name: node.data("name"),
                visible_in_menu: node.data("visible-in-menu"),
                position: serializedItem.index,
                // children: serializedChildren,
                parent: serializedItem.parent.parentNode.parentNode.dataset.name,
            }
        }
    });
    $("#menu-configuration-save").on("click", function() {
        var serialized = html5sortable(".sortable", "serialize");
        console.log(serialized);
        
    })
});