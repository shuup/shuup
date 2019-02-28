$(document).ready(function() {

    $("button").on("click", function() {
        console.log($(this).find(".fa-caret-down"));
    })

    html5sortable(".sortable", {
        placeholder: "<div class=\"card\"></div>",
        forcePlaceholderSize: true,
        handle: ".fa-reorder",
        containerSerializer: function() {
            return null;
        },
        itemSerializer: function(serializedItem, sortableContainer) {
            var childrenList = $(serializedItem.node).children(".card");
            var node = $(serializedItem.node);
            return {
                name: node.data("name"),
                visible_in_menu: node.data("visible-in-menu"),
                position: serializedItem.index,
                parent: serializedItem.parent.parentNode.parentNode.dataset.name,
            }
        }
    });
    $("#menu-configuration-save").on("click", function() {
        var serialized = html5sortable(".sortable", "serialize");
        // console.log(serialized);
        
    })
});