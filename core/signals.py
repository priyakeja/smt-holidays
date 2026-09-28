"""Automatic cleanup of media files.

Two guarantees, applied to every file/image field in the project:

1. **Replace** - uploading a new file for a field permanently removes the old
   one from storage instead of leaving orphaned files in ``media/``.
2. **Delete** - deleting a record deletes the files it owned.

A file is only removed when no other row still references the same stored
name, which keeps shared files (for example seeded demo photos) safe.
"""

from django.db.models.signals import post_delete, pre_save

from .models import (
    DownloadableFile,
    GalleryImage,
    HeroSlide,
    Package,
    PackageImage,
    SiteImage,
    SiteSettings,
    Testimonial,
)

# model -> file/image field names that should be cleaned up
FILE_FIELDS = {
    SiteSettings: ("logo", "favicon"),
    SiteImage: ("image",),
    HeroSlide: ("image",),
    Package: ("main_image", "brochure"),
    PackageImage: ("image",),
    GalleryImage: ("image",),
    Testimonial: ("customer_image",),
    DownloadableFile: ("file",),
}


def _remove(model, field_name, name, exclude_pk=None):
    """Delete a stored file unless a surviving row still points at it."""
    if not name:
        return
    others = model.objects.filter(**{field_name: name})
    if exclude_pk is not None:
        others = others.exclude(pk=exclude_pk)
    if others.exists():
        return
    try:
        model._meta.get_field(field_name).storage.delete(name)
    except Exception:  # storage hiccups must never break a save/delete
        pass


def _on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    for field_name in FILE_FIELDS[sender]:
        old_value = getattr(old, field_name, None)
        new_value = getattr(instance, field_name, None)
        if old_value and old_value.name != getattr(new_value, "name", None):
            _remove(sender, field_name, old_value.name, exclude_pk=instance.pk)


def _on_delete(sender, instance, **kwargs):
    for field_name in FILE_FIELDS[sender]:
        value = getattr(instance, field_name, None)
        if value and value.name:
            _remove(sender, field_name, value.name, exclude_pk=instance.pk)


def connect():
    """Wire the handlers. Called from ``CoreConfig.ready()``."""
    for model in FILE_FIELDS:
        uid = f"file_cleanup_{model.__name__.lower()}"
        pre_save.connect(_on_replace, sender=model, dispatch_uid=uid + "_replace")
        post_delete.connect(_on_delete, sender=model, dispatch_uid=uid + "_delete")
