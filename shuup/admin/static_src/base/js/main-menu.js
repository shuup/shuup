// /**
//  * This file is part of Shuup.
//  *
//  * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
//  *
//  * This source code is licensed under the OSL-3.0 license found in the
//  * LICENSE file in the root directory of this source tree.
//  */

const handleMainMenu = () => {
  const categoryLink = document.getElementsByClassName('item-category');

  const closeMenu = () => {
    Array.from(categoryLink).forEach((item) => {
      const categoryArrow = item.querySelector('.item-arrow');
      const submenu = item.nextElementSibling;

      if (item.classList.contains('item-active')) {
        item.classList.remove('item-active');
        submenu.classList.remove('active');
        categoryArrow.classList.remove('rotate');
      }
    });
  }

  const openMenu = (element) => {
    const categoryArrow = element.querySelector('.item-arrow');
    const submenu = element.nextElementSibling;

    element.classList.add('item-active');
    submenu.classList.add('active');
    categoryArrow.classList.add('rotate');
  }

  Array.from(categoryLink).forEach((item) => {
    item.addEventListener('click', (event) => {
      event.preventDefault();

      const currentItem = event.currentTarget;
      const isActive = currentItem.classList.contains('item-active');

      closeMenu();
      openMenu(item);

      if (isActive) {
        closeMenu();
      }
    });
  });

  const toggleBtn = document.getElementById('menu-button');
  const mainMenu = document.getElementById('js-main-menu');

  function hideMainMenu() {
    document.addEventListener('click', event => {
      if (!mainMenu.contains(event.target) && !toggleBtn.contains(event.target)) {
        mainMenu.classList.remove('open');
        document.removeEventListener('click', hideMainMenu);
      }
    });
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', (event) => {
      if (mainMenu.classList.contains('open')) {
        mainMenu.classList.remove('open');
      } else {
        mainMenu.classList.add('open');
        hideMainMenu();
      }
    });
  }
}

export default handleMainMenu;
