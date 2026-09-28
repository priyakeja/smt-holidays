"""Idempotent seeding of the default site content.

Running this twice never duplicates anything: every row is matched on a natural
key and updated in place. Used by ``manage.py seed_content``.
"""

from . import defaults
from .models import (
    ContactMethod,
    HeroBadge,
    MenuItem,
    Point,
    Service,
    SiteSettings,
    Stat,
    Step,
    TrustBadge,
)


def _sync(model, rows, key_fields, defaults_for):
    """update_or_create each row, matching on ``key_fields``."""
    created = updated = 0
    for row in rows:
        lookup = {field: row[field] for field in key_fields}
        _, was_created = model.objects.update_or_create(
            **lookup, defaults=defaults_for(row))
        created += was_created
        updated += not was_created
    return created, updated


def seed_content(verbose=False):
    """Populate settings, menus and the home-page sections. Returns counts."""
    log = print if verbose else (lambda *a, **k: None)
    counts = {}

    # Site settings singleton (model defaults are already sensible).
    settings_obj = SiteSettings.load()
    counts["site settings"] = 1
    log("  = site settings ready")

    # Menus
    total = 0
    for menu, entries in defaults.MENU_ITEMS.items():
        for order, (label, page, url, icon, position) in enumerate(entries):
            MenuItem.objects.update_or_create(
                menu=menu, label=label, parent=None,
                defaults={"page": page, "url": url, "icon": icon,
                          "order": position, "is_active": True},
            )
            total += 1
    counts["menu items"] = total
    log(f"  = {total} menu items")

    # Hero badges
    created, _ = _sync(
        HeroBadge,
        [{"icon": icon, "text": text} for icon, text in defaults.HERO_BADGES],
        ["text"],
        lambda row: {"icon": row["icon"], "is_active": True,
                     "order": defaults.HERO_BADGES.index((row["icon"], row["text"]))},
    )
    counts["hero badges"] = created

    # Trust badges
    created, _ = _sync(
        TrustBadge,
        [{"icon": icon, "text": text} for icon, text in defaults.TRUST_BADGES],
        ["text"],
        lambda row: {"icon": row["icon"], "is_active": True,
                     "order": defaults.TRUST_BADGES.index((row["icon"], row["text"]))},
    )
    counts["trust badges"] = created

    # Services
    _sync(Service,
          [{"icon": i, "title": t, "description": d} for i, t, d in defaults.SERVICES],
          ["title"],
          lambda row: {"icon": row["icon"], "description": row["description"],
                       "is_active": True,
                       "order": [t for _, t, _ in defaults.SERVICES].index(row["title"])})
    counts["services"] = len(defaults.SERVICES)

    # Steps
    _sync(Step,
          [{"icon": i, "title": t, "description": d} for i, t, d in defaults.STEPS],
          ["title"],
          lambda row: {"icon": row["icon"], "description": row["description"],
                       "is_active": True,
                       "order": [t for _, t, _ in defaults.STEPS].index(row["title"])})
    counts["steps"] = len(defaults.STEPS)

    # Statistics
    for order, (number, suffix, value, label) in enumerate(defaults.STATS):
        Stat.objects.update_or_create(
            label=label,
            defaults={"number": number, "suffix": suffix, "value": value,
                      "order": order, "is_active": True})
    counts["statistics"] = len(defaults.STATS)

    # Bullet points
    for order, (group, icon, text) in enumerate(defaults.POINTS):
        Point.objects.update_or_create(
            group=group, text=text,
            defaults={"icon": icon, "order": order, "is_active": True})
    counts["bullet points"] = len(defaults.POINTS)

    # Contact cards
    for order, (icon, title, value, link) in enumerate(defaults.CONTACT_METHODS):
        ContactMethod.objects.update_or_create(
            title=title,
            defaults={"icon": icon, "value": value, "link": link,
                      "order": order, "is_active": True})
    counts["contact cards"] = len(defaults.CONTACT_METHODS)

    return counts
