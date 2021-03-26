from __future__ import unicode_literals

import inspect
from django.apps import apps
from django.db import models
from django.utils.encoding import force_text
from django.utils.html import strip_tags
from parler.models import TranslatedFieldsModel


def setup(app):
    apps.get_models()  # Load models
    app.connect("autodoc-process-docstring", process_docstring)


def process_docstring(app, what, name, obj, options, lines):
    if inspect.isclass(obj) and issubclass(obj, models.Model):
        latelines = [""]
        _process_model(obj, lines, latelines)
        lines.extend(latelines)
    return lines


def _process_model(model, lines, latelines):
    for field in model._meta.get_fields():
        _process_model_field(field, lines, latelines)
    _process_model_translations(model, lines, latelines)


def _process_model_translations(model, lines, latelines):
    for trans_model in _get_translation_models(model):
        for field in trans_model._meta.get_fields():
            if field.name in ["id", "language_code", "master"]:
                continue
            _process_model_field(field, lines, latelines, is_translation=True)


def _get_translation_models(model):
    for field in model._meta.get_fields():
        if isinstance(field, models.ManyToOneRel):
            if issubclass(field.related_model, TranslatedFieldsModel):
                yield field.related_model


def _process_model_field(field, lines, latelines, is_translation=False):
    if not hasattr(field, "attname") or isinstance(field, models.ForeignKey):
        field.attname = field.name

    _process_field_help_text_and_verbose_name(field, lines, is_translation)
    _process_field_type(field, lines, latelines)


def _process_field_help_text_and_verbose_name(field, lines, is_translation=0):
    help_text = strip_tags(force_text(field.help_text)) if hasattr(field, "help_text") else None
    verbose_name = force_text(field.verbose_name).capitalize() if hasattr(field, "verbose_name") else None
    prefix = "(Translatable) " if is_translation else ""
    if help_text:
        lines.append(":param %s: %s" % (field.attname, prefix + help_text))
    elif verbose_name:
        lines.append(":param %s: %s" % (field.attname, prefix + verbose_name))


def _process_field_type(field, lines, latelines):
    if isinstance(field, models.ForeignKey):
        to = _resolve_field_destination(field, field.remote_field.model)

        lines.append(
            ":type %s: %s to :class:`%s.%s`" % (field.attname, type(field).__name__, to.__module__, to.__name__)
        )
    elif isinstance(field, models.ManyToManyField):
        to = _resolve_field_destination(field, field.remote_field.model)

        lines.append(
            ":type %s: %s to :class:`%s.%s`" % (field.attname, type(field).__name__, to.__module__, to.__name__)
        )
    elif isinstance(field, models.ManyToOneRel):
        to = _resolve_field_destination(field, field.related_model)
        latelines.append(".. attribute:: %s" % (field.related_name or field.name + "_set"))
        latelines.append("")
        latelines.append("   %s to :class:`%s.%s`" % (type(field).__name__, to.__module__, to.__name__))
        latelines.append("")
    else:
        lines.append(":type %s: %s" % (field.attname, type(field).__name__))


def _resolve_field_destination(field, to):
    if isinstance(to, type):  # Already a model class
        return to
    if to == "self":
        return field.model
    elif "." in to:
        return apps.get_model(to)
    return apps.get_model(field.model._meta.app_label, to)
