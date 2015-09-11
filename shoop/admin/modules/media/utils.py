# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _


def delete_folder(folder):
    """
    Delete a Filer folder and move files and subfolders up to the parent.

    :param folder: Folder
    :type folder: filer.models.Folder
    :return: Success message
    :rtype: str
    """
    parent_folder = (folder.parent if folder.parent_id else None)
    parent_name = (parent_folder.name if parent_folder else _("Root"))
    subfolders = list(folder.children.all())
    message_bits = []
    if subfolders:
        for subfolder in subfolders:
            subfolder.move_to(parent_folder, "last-child")
            subfolder.save()
        message_bits.append(_("%d subfolders moved to %s.") % (len(subfolders), parent_name))
    n_files = folder.files.count()
    if n_files:
        folder.files.update(folder=parent_folder)
        message_bits.append(_("%d files moved to %s.") % (n_files, parent_name))
    folder.delete()
    message_bits.insert(0, _("Folder %s deleted.") % folder.name)
    return "\n".join(message_bits)
