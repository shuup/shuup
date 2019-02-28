$(document).ready(function() {

    // Button icons on Display Menu Children
    $("button.display-children").on("click", function() {
        var caretRight = $(this).find("i.fa");
        $(caretRight).toggleClass("fa-caret-right").toggleClass("fa-caret-down");
    });

    // Hide and make visible in menu
    $("label.menu-hidden").on("click", function() {
        var menuItem = $(this).parents(".card")[0];
        menuItem.dataset.visibleInMenu = false;
    });
    $("label.menu-visible").on("click", function() {
        var menuItem = $(this).parents(".card")[0];
        menuItem.dataset.visibleInMenu = true;
    });

    // Drag and Drop
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
        console.log(serialized);
        
    })
});