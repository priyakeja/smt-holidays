"""Small template helpers shared by the public site and the dashboard."""

import os
import re

from django import template
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# Matches an opening/closing HTML tag written by the WYSIWYG editor.
TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


@register.filter
def rich(value):
    """Render a WYSIWYG field.

    Content authored in the dashboard editor is HTML and is emitted as-is
    (only staff can write it). Plain text written straight into the field is
    escaped and its line breaks preserved, so older or hand-typed content
    still renders sensibly.
    """
    text = str(value or "").strip()
    if not text:
        return ""
    if TAG_RE.search(text):
        return mark_safe(text)
    return mark_safe(escape(text).replace("\n", "<br>"))


@register.filter
def plain(value):
    """Strip tags for places that must stay text only (meta descriptions)."""
    return re.sub(r"<[^>]+>", "", str(value or "")).strip()


@register.filter
def get_item(mapping, key):
    """``{{ mydict|get_item:name }}`` - dictionary lookup by a variable key."""
    if not mapping:
        return None
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def fill_year(value):
    """Replace the ``{year}`` placeholder with the current year."""
    return str(value or "").replace("{year}", str(timezone.localdate().year))


@register.filter
def initials(value):
    parts = str(value or "?").split()
    return "".join(part[0] for part in parts[:2]).upper() or "?"


@register.filter
def is_external(value):
    return str(value).startswith(("http://", "https://"))


@register.simple_tag
def static_v(path):
    """``{% static_v 'js/main.js' %}`` - a static URL stamped with the file mtime.

    Static files carry no cache-busting hash in development, so a browser can
    keep serving a stale script after an edit. Appending the modification time
    forces a fresh copy whenever the file changes.
    """
    url = staticfiles_storage.url(path)
    try:
        located = finders.find(path) or staticfiles_storage.path(path)
        stamp = int(os.path.getmtime(located))
    except (OSError, ValueError, TypeError, NotImplementedError):
        return url
    return f"{url}?v={stamp}"


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Rebuild the current query string with the given keys replaced/removed."""
    request = context.get("request")
    params = request.GET.copy() if request else {}

    for key, value in kwargs.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value

    params.pop("page", None)
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""
