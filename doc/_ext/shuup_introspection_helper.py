"""
Monkey patches for enabling better introspection of Shuup code.

Call the `enable_patches` function to do the monkey patching.  Currently
it will patch a few property descriptors to allow calling ``__get__``
without an instance.

This fixes some warnings that Sphinx will yield when it tries to parse
Shuup's models.
"""
import django_countries.fields
import jsonfield.subclassing

PATCHES = []


class PatchFor(object):
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        self.original = getattr(obj, name)
        PATCHES.append(self)

    def __call__(self, func):
        self.patcher = func
        return func

    def enable(self):
        setattr(self.obj, self.name, self.replacer)

    def disable(self):
        setattr(self.obj, self.name, self.original)

    def replacer(self, *args, **kwargs):
        return self.patcher(self.original, *args, **kwargs)


@PatchFor(django_countries.fields.CountryDescriptor, "__get__")
def country_descriptor_get(original, self, instance=None, owner=None):
    if instance is None:
        return self
    return original(self, instance, owner)


@PatchFor(jsonfield.subclassing.Creator, "__get__")
def jsonfield_creator_get(original, self, obj, type=None):
    if obj is None:
        return self
    return original(self, obj, type)


def enable_patches(patches=PATCHES):
    for patch in patches:
        patch.enable()
