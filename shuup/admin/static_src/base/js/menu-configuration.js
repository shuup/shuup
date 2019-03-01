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
        itemSerializer: function(serializedItem) {
            var childrenList = Array.from($(serializedItem.node).find(".card"));
            var childrenNames = childrenList.map(function(child) {
                return child.dataset.name;
            });
            var node = $(serializedItem.node);
            var icon = $(node).find(".category-icon").attr("class");
            if (icon) {
                icon = icon.split(" ").slice(0, 2).join(" ");
            }
            return {
                name: node.data("name"),
                visibleInMenu: node.data("visible-in-menu"),
                position: serializedItem.index,
                children: childrenNames,
                icon: icon,
            }
        }
    });
    $("#menu-configuration-save").on("click", function() {
        var serialized = html5sortable(".sortable", "serialize");
        
        var subMenus = Array.from(serialized.slice(1, serialized.length));
        var structuredSubMenus = {};
        subMenus.forEach(function(subMenu) {
            Array.from(subMenu.items).forEach(function(menuItem) {
                structuredSubMenus[menuItem.name] = {
                    identifier: menuItem.name,
                    title: "_('" + menuItem.name + "')",
                    visible: menuItem.visibleInMenu,
                    position: menuItem.position, 
                };
            });
        });

        var categories = serialized[0].items;
        var structuredMenu = [];

        categories.forEach(function(category) {
            var name = category.name.split("-")[0];
            var entry = {
                identifier: name.toUpperCase() + "_MENU_CATEGORY",
                title: "_('" + name + "')",
                icon: category.icon,
                visible: category.visibleInMenu,
                position: category.position,
                children: category.children.map(function(child) {
                    return structuredSubMenus[child];
                }),
            }
            structuredMenu.push(entry);
        });
        console.log(structuredMenu);
    });
});

// MAIN_MENU = [
//     {
//         "identifier": ORDERS_MENU_CATEGORY,
//         "title": _("Orders"),
//         "icon": "fa fa-inbox",
//         "children": [
//             {
//                 "identifier": "orders",
//                 "title": _("Orders")
//             },
//         ]
//     },
//     {
//         "identifier": PRODUCTS_MENU_CATEGORY,
//         "title": _("Products"),
//         "icon": "fa fa-cube",
//         "children": [
//             {
//                 "identifier": "products",
//                 "title": _("Products")
//             },
//         ]
//     },
// ]




// configured_menu = [
//     {
//         "container": None,
//         "items": [
//             {
//                 "children": ["orders", "carts"],
//                 "name": "orders-category",
//                 "postion": 0,
//                 "visible-in-menu": True,
//             },
//             {
//                 "children": ["products", "categories"],
//                 "name": "products-category",
//                 "postion": 1,
//                 "visible-in-menu": True,
//             }
//         ]
//     },
//     {
//         "container": None,
//         "items": [
//             {
//                 "children": [],
//                 "name": "orders",
//                 "postion": 0,
//                 "visible-in-menu": True,
//             },
//             {
//                 "children": [],
//                 "name": "carts",
//                 "postion": 1,
//                 "visible-in-menu": True,
//             }
//         ]
//     },
//     {
//         "container": None,
//         "items": [
//             {
//                 "children": [],
//                 "name": "products",
//                 "postion": 0,
//                 "visible-in-menu": True,
//             },
//             {
//                 "children": [],
//                 "name": "categories",
//                 "postion": 1,
//                 "visible-in-menu": True,
//             }
//         ]
//     }
// ]
