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
  var desktop = false;
  function closeAdminMenu() {
    $('#top-header').css({ 'left' : '0px', 'width' : '100%'});
    $('.support-nav-wrap').css({ 'padding-left': '30px' });
    $('#main-content').css({ 'margin-left': '0px' });
  }
  function openAdminMenu() {
    $('#top-header').css({ left: '280px', width : 'calc(100% - 280px)' });
    $('.support-nav-wrap').css({ 'padding-left': '310px' });
    $('#main-content').css({ 'margin-left': '280px' });
  }
  // media query change
  function widthChange() {
    if(($(window).width() > 768) && (mainMenu.classList.contains('open'))) {
      openAdminMenu();
    } else {
      closeAdminMenu();
    }
  }

  window.addEventListener("resize", widthChange);
  if ($(window).width() >= 1024) {
    $('.main-menu').addClass('open');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (mainMenu.classList.contains('open')) {
        mainMenu.classList.remove('open');
          closeAdminMenu();
      } else {
        mainMenu.classList.add('open');
        if (!($(window).width() < 1024)) {
          openAdminMenu();
        }
       hideMainMenu();
      }
    });
  }
}

export default handleMainMenu;
