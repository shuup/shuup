# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import six
from django.middleware.csrf import get_token
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.forms import flatatt_filter
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.utils.str_utils import camelcase_to_snakecase
from shuup.admin.utils.urls import NoModelUrl, get_model_url
from shuup.apps.provides import get_provide_objects
from shuup.utils.django_compat import NoReverseMatch, Resolver404, force_text, resolve, reverse


class BaseToolbarButtonProvider(object):
    @classmethod
    def get_buttons_for_view(cls, view):
        """
        Implement this method to add custom buttons to a view's toolbar

        You can check the view attributes before returning buttons.
        In case you need to access the request, get it from the view: `view.request`.
        You can also access the view object when that is available:

        ```
        if getattr(view, "object", None):
            yield JavaScriptActionButton(onclick="window.doSomething()", text="Do Something")
        ```

        :param view django.views.View: the view object to add the toolbar.
        :rtype iterator|list
        """
        return []


class BaseActionButton(object):
    base_css_classes = ("btn", "")

    def __init__(
        self,
        text="",
        icon=None,
        disable_reason=None,
        tooltip=None,
        extra_css_class="",
        required_permissions=(),
        identifier=None,
    ):
        """
        :param text: The actual text for the button.
        :param icon: Icon CSS class string
        :param disable_reason: The reason for this button to be disabled.
                               It's considered good UX to have an user-visible reason for disabled
                               actions; thus the only way to disable an action is to set the reason.
                               See http://stackoverflow.com/a/372503/51685.
        :type disable_reason: str|None
        :param tooltip: Tooltip string, if any. May be replaced by the disable reason.
        :type tooltip: str|None
        :param extra_css_class: Extra CSS class(es)
        :type extra_css_class: str
        :param required_permissions: Optional iterable of permission strings
        :type required_permissions: Iterable[str]
        """
        self.text = text
        self.icon = icon
        self.disable_reason = disable_reason
        self.disabled = bool(self.disable_reason)
        self.tooltip = self.disable_reason or tooltip
        self.extra_css_class = extra_css_class
        self.required_permissions = required_permissions
        self.identifier = identifier

    def render(self, request):
        """
        Yield HTML bits for this object.
        :type request: HttpRequest
        :rtype: Iterable[str]
        """
        return ()

    def render_label(self):
        bits = []
        if self.icon:
            bits.append('<i class="%s"></i>&nbsp;' % self.icon)
        bits.append(conditional_escape(self.text))
        return "".join(force_text(bit) for bit in bits)

    def get_computed_class(self):
        return " ".join(
            filter(None, list(self.base_css_classes) + [self.extra_css_class, "disabled" if self.disabled else ""])
        )


class URLActionButton(BaseActionButton):
    """
    An action button that renders as a link leading to `url`.
    """

    def __init__(self, url, **kwargs):
        """
        :param url: The URL to navigate to. For convenience, if this contains no slashes,
                    `reverse` is automatically called on it.
        :type url: str
        """
        if "/" not in url:
            try:
                url = reverse(url)
            except NoReverseMatch:
                pass
        self.url = url

        if "required_permissions" not in kwargs:
            try:
                permission = resolve(six.moves.urllib.parse.urlparse(force_text(url)).path).url_name
                kwargs["required_permissions"] = (permission,)
            except Resolver404:
                pass

        super(URLActionButton, self).__init__(**kwargs)

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            yield "<a %s>" % flatatt_filter(
                {"href": self.url, "class": self.get_computed_class(), "title": self.tooltip}
            )
            yield self.render_label()
            yield "</a>"


class SettingsActionButton(URLActionButton):
    """
    A generic settings button meant to be used across many modules
    """

    def __init__(self, url, **kwargs):
        kwargs.setdefault("icon", "fa fa-cog")
        kwargs.setdefault("text", _("Settings"))
        kwargs.setdefault("extra_css_class", "btn-inverse")
        kwargs.pop("return_url")
        super(SettingsActionButton, self).__init__(url, **kwargs)

    @classmethod
    def for_model(cls, model, **kwargs):
        """
        Generate a SettingsActionButton for a model, auto-wiring the URL.

        :param model: Model class
        :rtype: shuup.admin.toolbar.SettingsActionButton|None
        """
        if "url" not in kwargs:
            try:
                url = get_model_url(model, kind="list_settings")
            except NoModelUrl:
                return None
            return_url = kwargs.get("return_url")
            if not return_url:
                return_url = camelcase_to_snakecase(model.__name__)
            kwargs["url"] = url + "?module=%s&model=%s&return_url=%s" % (model.__module__, model.__name__, return_url)

        return cls(**kwargs)


class NewActionButton(URLActionButton):
    """
    An URL button with sane "new" visual semantics
    """

    def __init__(self, url, **kwargs):
        kwargs.setdefault("icon", "fa fa-plus")
        kwargs.setdefault("text", _("Create new"))
        kwargs.setdefault("extra_css_class", "btn-primary")

        super(NewActionButton, self).__init__(url, **kwargs)

    @classmethod
    def for_model(cls, model, **kwargs):
        """
        Generate a NewActionButton for a model, auto-wiring the URL.

        :param model: Model class
        :rtype: shuup.admin.toolbar.NewActionButton|None
        """

        if "url" not in kwargs:
            try:
                url = get_model_url(model, kind="new")
            except NoModelUrl:
                return None
            kwargs["url"] = url

        kwargs.setdefault("text", _("New %(model)s") % {"model": model._meta.verbose_name})
        return cls(**kwargs)


class JavaScriptActionButton(BaseActionButton):
    """
    An action button that uses `onclick` for action dispatch.
    """

    base_css_classes = ("btn", "btn-default")

    def __init__(self, onclick, **kwargs):
        self.onclick = onclick
        super(JavaScriptActionButton, self).__init__(**kwargs)

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            yield "<a %s>" % flatatt_filter(
                {
                    "href": "#",
                    "class": self.get_computed_class(),
                    "title": self.tooltip,
                    "onclick": mark_safe(self.onclick) if self.onclick else None,
                }
            )
            yield self.render_label()
            yield "</a>"


class PostActionButton(BaseActionButton):
    """
    An action button that renders as a button POSTing a form
    containing `name`=`value` to `post_url`.
    """

    def __init__(self, post_url=None, name=None, value=None, form_id=None, confirm=None, **kwargs):
        self.post_url = post_url
        self.name = name
        self.value = value
        self.form_id = form_id
        self.confirm = confirm
        super(PostActionButton, self).__init__(**kwargs)

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            yield "<button %s>" % flatatt_filter(
                {
                    "form": self.form_id,  # This can be used to post another form
                    "formaction": self.post_url,
                    "name": self.name,
                    "value": self.value,
                    "type": "submit",
                    "title": self.tooltip,
                    "class": self.get_computed_class(),
                    "onclick": ("return confirm(%s)" % json.dumps(force_text(self.confirm)) if self.confirm else None),
                }
            )
            yield self.render_label()
            yield "</button>"


class DropdownActionButton(BaseActionButton):
    """
    An action button with a chevron button to open a dropdown
    menu.
    """

    base_css_classes = ("btn", "dropdown-toggle")

    def __init__(self, items, split_button=None, **kwargs):
        self.split_button = split_button
        self.items = list(items)
        super(DropdownActionButton, self).__init__(**kwargs)

    def render_dropdown(self, request):
        yield '<div class="dropdown-menu dropdown-menu-right">'
        for item in self.items:
            if not item:  # TODO: Revise!
                continue

            for bit in item.render(request):
                yield bit
        yield "</div>"

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            if not self.items:
                return
            yield '<div class="btn-group" role="group">'

            if self.split_button:
                for bit in self.split_button.render(request):
                    yield bit

            yield "<button %s>" % flatatt_filter(
                {"type": "button", "class": self.get_computed_class(), "data-toggle": "dropdown", "title": self.tooltip}
            )

            if not self.split_button:
                yield self.render_label()
                yield " "

            yield "</button>"
            for bit in self.render_dropdown(request):
                yield bit
            yield "</div>"


class DropdownItem(BaseActionButton):
    """
    An item to be shown in a `DropdownActionButton`.
    """

    base_css_classes = ()

    def __init__(self, url="#", onclick=None, **kwargs):
        self.url = url
        self.onclick = onclick
        super(DropdownItem, self).__init__(**kwargs)

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            attrs = {
                "class": "dropdown-item",
                "title": self.tooltip,
                "href": self.url,
                "onclick": (mark_safe(self.onclick) if self.onclick else None),
            }
            yield "<a %s>" % flatatt_filter(attrs)
            yield self.render_label()
            yield "</a>"

    @staticmethod
    def visible_for_object(object):
        """
        Used when dropdown item is added through provides

        :return whether this item must be shown
        :rtype: bool
        """
        return True


class PostActionDropdownItem(PostActionButton):
    """
    A POST action item to be shown in a `DropdownActionButton`.
    """

    base_css_classes = ("dropdown-item", "")

    def __init__(self, **kwargs):
        super(PostActionDropdownItem, self).__init__(**kwargs)

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            button = super(PostActionDropdownItem, self).render(request)
            for bit in button:
                yield bit

    @staticmethod
    def visible_for_object(object):
        """
        Used when dropdown item is added through provides

        :return whether this item must be shown
        :rtype: bool
        """
        return True


class DropdownDivider(BaseActionButton):
    """
    A Divider for DropdownActionButtons.
    """

    base_css_classes = ()

    def render(self, request):
        yield '<div class="dropdown-divider"></div>'


class DropdownHeader(BaseActionButton):
    """
    Header for DropdownActionButtons.
    """

    base_css_classes = ()

    def render(self, request):
        if not get_missing_permissions(request.user, self.required_permissions):
            yield '<h6 class="dropdown-header">%s</h6>' % self.text


# -----------


class ButtonGroup(list):
    def render(self, request):
        yield '<div class="btn-group" role="group">'
        for button in self:
            if button:
                if callable(button):  # Buttons may be functions/other callables too
                    yield button(request)
                else:
                    for bit in button.render(request):
                        yield bit
        yield "</div>"


class Toolbar(list):
    """
    Toolbar for admin views

    Add buttons (subclasses of BaseActionButton) to the toolbar through `toolbar.append(button)` method.

    A toolbar can be created for a given View using `Toolbar.for_view(view_instance)` class method.
    This method will create an empty toolbar and it will be populated using button providers
    that are loaded using provides.
    Views which have the `toolbar_buttons_provider_key` attribute indicate that buttons
    should be added to the toolbar using that provide key, e.g:

    in your `view.py`:
    ```
    class MyView(View):
        toolbar_buttons_provider_key = 'my_view_toolbar_provider_key'
    ```

    in your `apps.py`:
    ```
    class AppConfig(shuup.apps.AppConfig):
        provides = {
            "my_view_toolbar_provider_key": [
                "myapp.toolbar:MyViewToolbarButtonProvider"
            ]
        }
    ```

    in your `toolbar.py`:
    ```
    class MyViewToolbarButtonProvider(BaseToolbarButtonProvider):
        @classmethod
        def get_buttons_for_view(cls, view):
            if getattr(view, "object", None) and isinstance(view.object, Product):
                yield JavaScriptActionButton(onclick="window.doSomething()", text="Do Something")
    ```

    You can also provide buttons to the tollbar of any view using the `admin_toolbar_button_provider` provide key.
    """

    def __init__(self, *args, **kwargs):
        view = kwargs.pop("view", None)
        super(Toolbar, self).__init__(*args, **kwargs)
        if view:
            self.extend(Toolbar.for_view(view))

    def render(self, request):
        # The toolbar is wrapped in a form without an action,
        # but `PostActionButton`s use the HTML5 `formaction` attribute.
        yield '<div class="shuup-toolbar">'
        yield '<form method="POST">'
        yield format_html("<input type='hidden' name='csrfmiddlewaretoken' value='{0}'>", get_token(request))
        yield '<div class="btn-toolbar" role="toolbar">'

        for group in self:
            if group:
                for bit in group.render(request):
                    yield bit

        yield "</div></form></div>"

    def render_to_string(self, request):
        return "".join(force_text(bit) for bit in self.render(request))

    @classmethod
    def for_view(cls, view):
        toolbar = cls()

        # add buttons from the view toolbar button provider
        if getattr(view, "toolbar_buttons_provider_key", None):
            for toolbar_buttons_provider in get_provide_objects(view.toolbar_buttons_provider_key):
                toolbar.extend(list(toolbar_buttons_provider.get_buttons_for_view(view)))

        # add buttons from the global toolbar button provider
        for admin_toolbar_button_provider in get_provide_objects("admin_toolbar_button_provider"):
            toolbar.extend(list(admin_toolbar_button_provider.get_buttons_for_view(view)))

        return toolbar


def try_reverse(viewname, **kwargs):
    try:
        return reverse(viewname, kwargs=kwargs)
    except NoReverseMatch:
        return viewname


def get_discard_button(discard_url):
    return URLActionButton(
        url=discard_url, text=_("Discard Changes"), icon="fa fa-undo", extra_css_class="btn btn-inverse"
    )


def get_save_as_copy_button(object, copy_url):
    if copy_url and object and object.pk:
        copy_url = try_reverse(copy_url, pk=object.pk)
        return DropdownItem(
            url=copy_url,
            text=_("Save as a copy"),
            icon="fa fa-clone",
        )
    elif object and object.pk:
        return DropdownItem(
            onclick="saveAsACopy()",
            text=_("Save as a copy"),
            icon="fa fa-clone",
        )


def get_default_edit_toolbar(
    view_object,
    save_form_id,
    discard_url=None,
    delete_url=None,
    copy_url=None,
    with_split_save=True,
    with_save_as_copy=False,
    toolbar=None,
    required_permissions=(),
):
    """
    Get a toolbar with buttons used for object editing.

    :param view_object: The class-based-view object requiring the toolbar
    :type view_object: django.views.generic.UpdateView
    :param save_form_id: The DOM ID to target for the save button
    :type save_form_id: str
    :param discard_url: The URL/route name for the Discard button. Falsy values default to the request URL.
    :type discard_url: str|None
    :param delete_url: The URL/route name for the Delete button. If this is not set, the delete button is not shown.
    :type delete_url: str|None
    :param with_split_save: Use split delete button with "Save and Exit" etc.?
    :type with_split_save: bool
    :param toolbar: The toolbar to augment. If None, a new one is created.
    :type toolbar: Toolbar
    :return: Toolbar
    :rtype: Toolbar
    """
    request = view_object.request
    object = getattr(view_object, "object", None)
    discard_url = discard_url or request.path
    existing_toolbar = toolbar is not None
    toolbar = toolbar if existing_toolbar else Toolbar.for_view(view_object)

    default_save_button = PostActionButton(
        icon="fa fa-check-circle",
        form_id=save_form_id,
        text=_("Save"),
        extra_css_class="btn-success btn-save",
        required_permissions=required_permissions,
    )

    if with_split_save:
        dropdown_options = [
            DropdownItem(
                onclick="setNextActionAndSubmit('%s', 'return')" % save_form_id,
                text=_("Save and Exit"),
                icon="fa fa-floppy-o",
            ),
            DropdownItem(
                onclick="setNextActionAndSubmit('%s', 'new')" % save_form_id,
                text=_("Save and Create New"),
                icon="fa fa-file-o",
            ),
        ]

        if with_save_as_copy:
            save_as_copy_button = get_save_as_copy_button(object, copy_url)
            if save_as_copy_button:
                dropdown_options.append(save_as_copy_button)

        if object and object.pk:
            if discard_url:
                dropdown_options.append(DropdownDivider())
                dropdown_options.append(get_discard_button(try_reverse(discard_url, pk=object.pk)))

        save_dropdown = DropdownActionButton(
            dropdown_options,
            split_button=default_save_button,
            extra_css_class="btn-success btn-dropdown-toggle",
            required_permissions=required_permissions,
        )
        toolbar.append(save_dropdown)
    else:
        toolbar.append(default_save_button)

    if with_save_as_copy and not with_split_save:
        toolbar.append(save_as_copy_button)

    if object and object.pk:
        if delete_url:
            delete_url = try_reverse(delete_url, pk=object.pk)
            toolbar.append(
                PostActionButton(
                    post_url=delete_url,
                    text=_("Delete"),
                    icon="fa fa-trash",
                    extra_css_class="btn-danger",
                    confirm=_("Are you sure you wish to delete %s?") % object,
                    required_permissions=required_permissions,
                )
            )

    if existing_toolbar:
        toolbar.extend(Toolbar.for_view(view_object))

    return toolbar
