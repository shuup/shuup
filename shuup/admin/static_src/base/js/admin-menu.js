/*
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */

// eslint-disable-next-line no-unused-vars
window.saveMenus = () => {
  const target = $("input[name=menus]");
  target.val(serializeAdminMenus());
};

const serializeAdminMenus = () => {
  const elementData = (entry) => {
    const id = $(entry).data("id");
    const data = {
      "id": id,
      "name": $(entry).find(".name").text().trim(),
      "is_hidden": !$(entry).find(".is-visible-control").is(":checked"),
    };
    const children = $(entry).find("+.menu-entries > .list-group-item > .menu-entry").map(function (index, childEntry) {
      return elementData(childEntry);
    });
    if (children.length) {
      data.entries = children.get();
    }
    return data;
  };

  const menuEntries = $(".admin-menus > .menu-entries > .list-group-item > .menu-entry");
  const data = menuEntries.map(function (index, entry) {
    return elementData(entry);
  }).get();
  return JSON.stringify(data);
};

const sortStart = (e) => {
  const menuEntry = $(e.detail.item);
  // mark if element has children
  const hasChildren = menuEntry.find(".menu-entry").length > 1;
  menuEntry.parent().toggleClass("has-children", hasChildren);
};

const sortUpdate = (e) => {
  const menuEntry = $(e.detail.item);
  // update parent and menu-entries sorter
  connectSortable(menuEntry.parent());
  connectSortable(menuEntry.find("> .menu-entries"));
};

const connectSortable = (menuEntries) => {
  let menuSubEntries;
  let sortable;
  const id = menuEntries.attr("id");
  const parentsLength = menuEntries.parents(".menu-entries").length;

  let acceptFrom = ".menu-entries";
  if (parentsLength === 0) {
    menuSubEntries = menuEntries.find("> .list-group-item > .menu-entries");
    menuSubEntries.removeClass("disabled");
  } else {
    // above the first level do not accept drop elements with children
    acceptFrom += ":not(.has-children)";
    menuSubEntries = menuEntries.find("> .list-group-item > .menu-entries");
    menuSubEntries.addClass("disabled");
  }

  // use id instead of class to avoid bug with nested elements
  sortable = window.html5sortable("#" + id + ":not(.disabled)", {
    forcePlaceholderSize: true,
    handle: ".sortable-handler",
    acceptFrom: acceptFrom,
  })[0];

  if (sortable) {
    sortable.addEventListener("sortstart", sortStart);
    sortable.addEventListener("sortupdate", sortUpdate);
  }
};

const menuEntries = $(".menu-entries");
menuEntries.each(function (index, element) {
  element = $(element);
  connectSortable(element);
});

export default saveMenus;
