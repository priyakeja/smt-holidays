"""Assembles every editable piece of site chrome for templates.

``site_context()`` is wired into ``TEMPLATES`` via ``core.context_processors``,
so every template gets:

``SITE``          the :class:`~core.models.SiteSettings` singleton
``TEXT``          ``{key: value}`` for every text block in ``content.py``
``IMG``           ``{key: ImageValue}`` for every section image
``HEADER_MENU``   active top-level header links (with ``.active_children``)
``FOOTER_MENU``   active footer links
``TOPBAR_MENU``   active top-bar links
"""

from django.conf import settings as django_settings
from django.db.models import Prefetch
from django.urls import NoReverseMatch, reverse

from . import content
from .models import MenuItem, SiteImage, SiteSettings, SiteText


class ImageValue:
    """A resolved section image: ``.url`` may be empty, ``.alt`` never is."""

    __slots__ = ("url", "alt")

    def __init__(self, url="", alt=""):
        self.url = url
        self.alt = alt

    def __bool__(self):
        return bool(self.url)

    def __str__(self):
        return self.url


def site_settings():
    return SiteSettings.load()


def text_map():
    overrides = dict(SiteText.objects.values_list("key", "value"))
    return {block.key: overrides.get(block.key, block.default)
            for block in content.TEXT_BLOCKS}


def image_map():
    stored = {row.key: row for row in SiteImage.objects.all()}
    resolved = {}
    for block in content.IMAGE_BLOCKS:
        row = stored.get(block.key)
        if row and row.image:
            resolved[block.key] = ImageValue(row.image.url, row.alt_text or block.label)
        elif block.default:
            resolved[block.key] = ImageValue(django_settings.MEDIA_URL + block.default,
                                             block.label)
        else:
            resolved[block.key] = ImageValue("", block.label)
    return resolved


def menu(menu_name):
    """Top-level items for a menu, each with an ``active_children`` list."""
    active = MenuItem.objects.filter(is_active=True).order_by("order", "id")
    return list(
        MenuItem.objects
        .filter(menu=menu_name, is_active=True, parent__isnull=True)
        .order_by("order", "id")
        .prefetch_related(Prefetch("children", queryset=active, to_attr="active_children"))
    )


def resolve_link(value):
    """Turn a page key (``contact``) into a URL, or pass a raw link through."""
    value = (value or "").strip()
    if not value:
        return "#"
    if value.startswith(("http://", "https://", "tel:", "mailto:", "/", "#")):
        return value
    try:
        return reverse(value)
    except NoReverseMatch:
        return value


def site_context():
    texts = text_map()
    return {
        "SITE": site_settings(),
        "TEXT": texts,
        "IMG": image_map(),
        "HEADER_MENU": menu(MenuItem.HEADER),
        "FOOTER_MENU": menu(MenuItem.FOOTER),
        "TOPBAR_MENU": menu(MenuItem.TOPBAR),
        "NAV_CTA": {"label": texts["nav_cta_label"],
                    "url": resolve_link(texts["nav_cta_url"])},
        "HERO_CTA": resolve_link(texts["hero_cta_url"]),
        "HERO_SECONDARY": resolve_link(texts["hero_secondary_url"]),
        "HOW_CTA": resolve_link(texts["how_cta_url"]),
        "CONSULT_ANCHOR": resolve_link("contact") + "#enquiry",
    }
