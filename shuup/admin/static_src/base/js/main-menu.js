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
  const closeBtn = document.getElementById('js-menu-close');

  const hideMainMenu = () => {
    closeBtn.addEventListener('click', event => {
      event.preventDefault();
      mainMenu.classList.remove('open');
    });
  }
  // media query change
  if ($(window).width() >= 1024) {
    $("body").toggleClass("menu-open");
    $('.main-menu').addClass('open');
  }
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      $("body").toggleClass("menu-open");
      $('.main-menu').toggleClass('open');

    });
  }
}

export default handleMainMenu;
