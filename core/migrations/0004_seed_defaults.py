"""Seed the default content so a freshly migrated database is never empty.

Headings and paragraphs are not stored here: ``core/content.py`` already
supplies a built-in default for every one of them, so those render correctly
with no rows at all. This migration fills in the *lists* (menus, badges,
services, steps, statistics, bullets and contact cards) that would otherwise be
invisible until an admin created them.

The data itself lives in ``core/defaults.py``, a plain data module with no
model or Django imports, so importing it here stays safe.
"""

from django.db import migrations

from core import defaults


def create_defaults(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    MenuItem = apps.get_model("core", "MenuItem")
    HeroBadge = apps.get_model("core", "HeroBadge")
    TrustBadge = apps.get_model("core", "TrustBadge")
    Service = apps.get_model("core", "Service")
    Step = apps.get_model("core", "Step")
    Stat = apps.get_model("core", "Stat")
    Point = apps.get_model("core", "Point")
    ContactMethod = apps.get_model("core", "ContactMethod")

    SiteSettings.objects.get_or_create(pk=1)

    for menu, entries in defaults.MENU_ITEMS.items():
        for label, page, url, icon, position in entries:
            MenuItem.objects.get_or_create(
                menu=menu, label=label, parent=None,
                defaults={"page": page, "url": url, "icon": icon,
                          "order": position, "is_active": True},
            )

    for order, (icon, text) in enumerate(defaults.HERO_BADGES):
        HeroBadge.objects.get_or_create(
            text=text, defaults={"icon": icon, "order": order, "is_active": True})

    for order, (icon, text) in enumerate(defaults.TRUST_BADGES):
        TrustBadge.objects.get_or_create(
            text=text, defaults={"icon": icon, "order": order, "is_active": True})

    for order, (icon, title, description) in enumerate(defaults.SERVICES):
        Service.objects.get_or_create(
            title=title,
            defaults={"icon": icon, "description": description,
                      "order": order, "is_active": True})

    for order, (icon, title, description) in enumerate(defaults.STEPS):
        Step.objects.get_or_create(
            title=title,
            defaults={"icon": icon, "description": description,
                      "order": order, "is_active": True})

    for order, (number, suffix, value, label) in enumerate(defaults.STATS):
        Stat.objects.get_or_create(
            label=label,
            defaults={"number": number, "suffix": suffix, "value": value,
                      "order": order, "is_active": True})

    for order, (group, icon, text) in enumerate(defaults.POINTS):
        Point.objects.get_or_create(
            group=group, text=text,
            defaults={"icon": icon, "order": order, "is_active": True})

    for order, (icon, title, value, link) in enumerate(defaults.CONTACT_METHODS):
        ContactMethod.objects.get_or_create(
            title=title,
            defaults={"icon": icon, "value": value, "link": link,
                      "order": order, "is_active": True})


def remove_defaults(apps, schema_editor):
    """Reverse: drop the seeded chrome, leaving admin-created content alone."""
    MenuItem = apps.get_model("core", "MenuItem")
    HeroBadge = apps.get_model("core", "HeroBadge")
    TrustBadge = apps.get_model("core", "TrustBadge")
    Service = apps.get_model("core", "Service")
    Step = apps.get_model("core", "Step")
    Stat = apps.get_model("core", "Stat")
    Point = apps.get_model("core", "Point")
    ContactMethod = apps.get_model("core", "ContactMethod")

    MenuItem.objects.filter(
        label__in=[label for entries in defaults.MENU_ITEMS.values()
                   for label, *_ in entries]).delete()
    HeroBadge.objects.filter(text__in=[t for _, t in defaults.HERO_BADGES]).delete()
    TrustBadge.objects.filter(text__in=[t for _, t in defaults.TRUST_BADGES]).delete()
    Service.objects.filter(title__in=[t for _, t, _ in defaults.SERVICES]).delete()
    Step.objects.filter(title__in=[t for _, t, _ in defaults.STEPS]).delete()
    Stat.objects.filter(label__in=[s[3] for s in defaults.STATS]).delete()
    Point.objects.filter(text__in=[p[2] for p in defaults.POINTS]).delete()
    ContactMethod.objects.filter(title__in=[c[1] for c in defaults.CONTACT_METHODS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_contactmethod_downloadablefile_herobadge_heroslide_and_more"),
    ]

    operations = [
        migrations.RunPython(create_defaults, remove_defaults),
    ]
