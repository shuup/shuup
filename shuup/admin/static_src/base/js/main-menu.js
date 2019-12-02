// /**
//  * This file is part of Shuup.
//  *
//  * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
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
  };

  const openMenu = (element) => {
    const categoryArrow = element.querySelector('.item-arrow');
    const submenu = element.nextElementSibling;

    element.classList.add('item-active');
    submenu.classList.add('active');
    categoryArrow.classList.add('rotate');
  };
  const toggleBtn = document.getElementById('menu-button');
  const mainMenu = document.getElementById('js-main-menu');
  const closeBtn = document.getElementById('js-menu-close');
  const resizeBtn = document.getElementById('js-menu-resize');
  const header = document.getElementById('top-header');
  const content = document.getElementById('main-content');
  const supportNav = document.getElementsByClassName('support-nav-wrap')[0];
  const logoIcon = document.getElementById('logo-icon');
  [...categoryLink].forEach((item) => {
    item.addEventListener('click', (event) => {
      if (!(resizeBtn.classList.contains('active'))) {
        event.preventDefault();
      }
      const currentItem = event.currentTarget;
      const isActive = currentItem.classList.contains('item-active');

      closeMenu();
      openMenu(item);

      if (isActive) {
        closeMenu();
      }
    });
  });


  const hideMainMenu = () => {
    closeBtn.addEventListener('click', event => {
      event.preventDefault();
      mainMenu.classList.remove('open');
    });
  };
  const resizeMenu = () => {
    if(resizeBtn.classList.contains('active')) {
      mainMenu.classList.remove('resized');
      header.classList.remove('resized');
      content.classList.remove('resized');
      resizeBtn.classList.remove('active');
      supportNav.classList.remove('resized');
      mainMenu.classList.add('open');
      logoIcon.classList.add('hidden');
    } else {
      mainMenu.classList.remove('open');
      mainMenu.classList.add('resized');
      header.classList.add('resized');
      content.classList.add('resized');
      resizeBtn.classList.add('active');
      supportNav.classList.add('resized');
      logoIcon.classList.remove('hidden');
    }
  }

  const resizeMainMenu = () => {
    resizeBtn.addEventListener('click', event => {
      toggleMenu();
    });
  };
  resizeMainMenu();

  let menuOpen = ($("body").hasClass("desktop-menu-closed")) ? 0 : 1;
  if (!(menuOpen)) {
    resizeMenu();
  }

  function toggleMenu(){
    $("body").toggleClass("desktop-menu-closed");
    menuOpen = ($("body").hasClass("desktop-menu-closed")) ? 0 : 1;
    $.post(window.ShuupAdminConfig.browserUrls.menu_toggle, { "csrfmiddlewaretoken": window.ShuupAdminConfig.csrf, menuOpen });
    if (mainMenu.classList.contains('open')) {
      mainMenu.classList.remove('open');
    } else {
      mainMenu.classList.add('open');
      hideMainMenu();
    }
    resizeMenu();
  }
  toggleBtn.addEventListener('click', () => {
    toggleMenu();
  });
};

handleMainMenu();
export default handleMainMenu;
