"""Secured admin dashboard.

Every view here requires an authenticated **staff** account; anonymous users
are bounced to the dashboard login and signed-in non-staff users get a 403.
All mutating views are POST-only and CSRF protected (Django's default).
"""

import csv
import os
from functools import wraps
from pathlib import Path

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models as db
from django.db.models import Max, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from .. import content
from ..models import (
    FAQ,
    GalleryImage,
    HeroSlide,
    Inquiry,
    MenuItem,
    Package,
    SiteImage,
    SiteSettings,
    SiteText,
    Testimonial,
)
from ..site import image_map, site_settings
from . import forms as dash_forms
from .registry import RESOURCE_MAP, nav_sections

PAGE_SIZE = 25


# --------------------------------------------------------------------------- #
# Access control                                                               #
# --------------------------------------------------------------------------- #

def staff_required(view):
    """Allow only active staff accounts through to a dashboard view."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            login = reverse("dashboard:login")
            return redirect(f"{login}?next={request.get_full_path()}")
        if not user.is_staff:
            raise PermissionDenied("You do not have access to the dashboard.")
        return view(request, *args, **kwargs)

    return wrapper


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not form.get_user().is_staff:
            form.add_error(None, "This account does not have dashboard access.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_redirect_url() or reverse("dashboard:index")


class DashboardLogoutView(LogoutView):
    next_page = reverse_lazy("dashboard:login")


# --------------------------------------------------------------------------- #
# Shared helpers                                                               #
# --------------------------------------------------------------------------- #

def dash_context(request, **extra):
    context = {
        "nav": nav_sections(),
        "active": "",
        "new_enquiries": Inquiry.objects.filter(status=Inquiry.NEW).count(),
        "site": site_settings(),
    }
    context.update(extra)
    return context


def get_resource(slug):
    resource = RESOURCE_MAP.get(slug)
    if not resource:
        raise Http404("Unknown dashboard section")
    return resource


def human_size(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return ""


def build_cell(obj, column):
    """Turn one model attribute into something the list template can render."""
    value = getattr(obj, column.name, None)

    if column.kind == "image":
        url = ""
        if value and getattr(value, "name", ""):
            try:
                url = value.url
            except ValueError:
                url = ""
        return {"image": url, "text": ""}

    if column.kind == "bool":
        return {"bool": bool(value), "text": "Yes" if value else "No",
                "field": column.name, "obj": obj}

    if column.kind == "date":
        if not value:
            return {"text": "—"}
        if hasattr(value, "strftime"):
            fmt = "%d %b %Y, %H:%M" if getattr(value, "hour", None) is not None else "%d %b %Y"
            return {"text": value.strftime(fmt)}
        return {"text": str(value)}

    if column.kind == "price":
        return {"text": f"\u20b9{value:,}"} if value is not None else {"text": "—"}

    if column.kind == "stars":
        return {"stars": range(1, 6), "rating": value or 0}

    if column.kind == "choice":
        getter = getattr(obj, f"get_{column.name}_display", None)
        return {"text": getter() if getter else (value or "—"),
                "tone": getattr(obj, f"{column.name}_tone", None)}

    if column.kind == "file":
        if not value or not getattr(value, "name", ""):
            return {"text": "—"}
        try:
            return {"text": os.path.basename(value.name), "url": value.url}
        except ValueError:
            return {"text": "—"}

    text = str(value)
    bound = getattr(obj, f"get_{column.name}_display", None)
    if callable(bound):
        text = bound()
    return {"text": text if text else "—"}


def build_rows(objects, columns):
    rows = []
    for obj in objects:
        cells = []
        for column in columns:
            cell = build_cell(obj, column)
            cell["kind"] = column.kind
            cell["name"] = column.name
            cell["primary"] = column.primary
            cells.append(cell)
        rows.append({"obj": obj, "cells": cells})
    return rows


def build_filters(resource, request):
    """Choice lists for the list-page filter bar, plus the applied values."""
    filters = []
    for name in resource.filter_fields:
        try:
            field = resource.model._meta.get_field(name)
        except db.FieldDoesNotExist:
            continue

        current = request.GET.get(name, "")

        if isinstance(field, db.BooleanField):
            options = [{"value": "", "label": "All"},
                       {"value": "1", "label": "Yes"},
                       {"value": "0", "label": "No"}]
        elif field.choices:
            options = [{"value": "", "label": "All"}] + [
                {"value": str(v), "label": str(l)} for v, l in field.choices]
        elif field.is_relation:
            options = [{"value": "", "label": "All"}] + [
                {"value": str(o.pk), "label": str(o)}
                for o in field.related_model.objects.all()[:200]]
        else:
            values = (resource.model.objects.exclude(**{name: ""})
                      .values_list(name, flat=True).distinct()[:50])
            options = [{"value": "", "label": "All"}] + [
                {"value": str(v), "label": str(v)} for v in values]

        filters.append({"name": name, "label": field.verbose_name.title(),
                        "options": options, "current": str(current)})
    return filters


def apply_filters(resource, queryset, request):
    for name in resource.filter_fields:
        raw = request.GET.get(name, "")
        if raw == "":
            continue
        try:
            field = resource.model._meta.get_field(name)
        except db.FieldDoesNotExist:
            continue
        if isinstance(field, db.BooleanField):
            queryset = queryset.filter(**{name: raw == "1"})
        else:
            queryset = queryset.filter(**{name: raw})
    return queryset


def queryset_for(resource, request):
    queryset = resource.model.objects.all()

    if resource.orderable:
        queryset = queryset.order_by("order", "id")

    query = (request.GET.get("q") or "").strip()
    if query and resource.search_fields:
        condition = Q()
        for name in resource.search_fields:
            condition |= Q(**{f"{name}__icontains": query})
        queryset = queryset.filter(condition)

    return apply_filters(resource, queryset, request)


# --------------------------------------------------------------------------- #
# Overview                                                                     #
# --------------------------------------------------------------------------- #

@staff_required
def index(request):
    stats = {
        "packages": Package.objects.count(),
        "published": Package.objects.filter(is_active=True).count(),
        "gallery": GalleryImage.objects.count(),
        "reviews": Testimonial.objects.count(),
        "faqs": FAQ.objects.count(),
        "hero_slides": HeroSlide.objects.filter(is_active=True).count(),
    }

    checklist = [
        ("Hero slides added", stats["hero_slides"] > 0,
         reverse("dashboard:resource_list", args=["hero-slides"])),
        ("At least one package published", stats["published"] > 0,
         reverse("dashboard:resource_list", args=["packages"])),
        ("Gallery has photos", stats["gallery"] > 0,
         reverse("dashboard:resource_list", args=["gallery"])),
        ("Reviews published", stats["reviews"] > 0,
         reverse("dashboard:resource_list", args=["testimonials"])),
        ("Contact details filled in", bool(site_settings().phone_raw),
         reverse("dashboard:settings")),
        ("Header menu has links",
         MenuItem.objects.filter(is_active=True, parent__isnull=True,
                                 menu=MenuItem.HEADER).exists(),
         reverse("dashboard:resource_list", args=["menu-items"])),
    ]

    resolved_images = image_map()

    return render(request, "dashboard/index.html", dash_context(
        request,
        active="index",
        stats=stats,
        checklist=checklist,
        recent=Inquiry.objects.all()[:6],
        missing_images=[b.label for k, b in content.IMAGE_BY_KEY.items()
                        if not resolved_images[k]],
    ))


# --------------------------------------------------------------------------- #
# Generic CRUD                                                                 #
# --------------------------------------------------------------------------- #

@staff_required
def resource_list(request, slug):
    resource = get_resource(slug)
    queryset = queryset_for(resource, request)

    paginator = Paginator(queryset, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "dashboard/resource_list.html", dash_context(
        request,
        resource=resource,
        active=resource.slug,
        rows=build_rows(page.object_list, resource.columns),
        page=page,
        filters=build_filters(resource, request),
        query=request.GET.get("q", ""),
        total=queryset.count(),
        has_filters=bool(resource.filter_fields or resource.search_fields),
    ))


@staff_required
def resource_form(request, slug, pk=None):
    resource = get_resource(slug)
    instance = get_object_or_404(resource.model, pk=pk) if pk else None
    form = resource.form(request.POST or None, request.FILES or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        obj = form.save()
        verb = "updated" if pk else "created"
        messages.success(request, f"{resource.label} “{obj}” {verb}.")
        return redirect("dashboard:resource_list", slug=resource.slug)

    if request.method == "POST":
        messages.error(request, "Please fix the highlighted fields below.")

    return render(request, "dashboard/form.html", dash_context(
        request,
        resource=resource,
        active=resource.slug,
        form=form,
        instance=instance,
        previews=form.file_previews(),
        title=f"Edit {resource.label.lower()}" if instance
              else f"New {resource.label.lower()}",
    ))


@staff_required
def resource_delete(request, slug, pk):
    resource = get_resource(slug)
    instance = get_object_or_404(resource.model, pk=pk)

    if request.method == "POST":
        label = str(instance)
        instance.delete()  # signals clean up any attached files
        messages.success(request, f"{resource.label} “{label}” deleted.")
        return redirect("dashboard:resource_list", slug=resource.slug)

    return render(request, "dashboard/confirm_delete.html", dash_context(
        request, resource=resource, active=resource.slug, instance=instance,
    ))


@require_POST
@staff_required
def resource_toggle(request, slug, pk):
    resource = get_resource(slug)
    if not resource.toggle_field:
        raise Http404("This section cannot be toggled")

    instance = get_object_or_404(resource.model, pk=pk)
    value = not getattr(instance, resource.toggle_field)
    setattr(instance, resource.toggle_field, value)
    instance.save(update_fields=[resource.toggle_field])

    messages.success(request, f"“{instance}” {'shown' if value else 'hidden'}.")
    return redirect(request.META.get("HTTP_REFERER")
                    or reverse("dashboard:resource_list", args=[slug]))


@require_POST
@staff_required
def resource_move(request, slug, pk):
    resource = get_resource(slug)
    if not resource.orderable:
        raise Http404("This section is not ordered")

    direction = request.POST.get("direction")
    items = list(resource.model.objects.order_by("order", "id"))
    index = next((i for i, obj in enumerate(items) if obj.pk == int(pk)), None)

    if index is None:
        raise Http404("Item not found")

    target = index - 1 if direction == "up" else index + 1

    if 0 <= target < len(items):
        items[index], items[target] = items[target], items[index]
        for position, obj in enumerate(items):
            if obj.order != position:
                obj.order = position
                obj.save(update_fields=["order"])
        messages.success(request, "Order updated.")
    else:
        messages.info(request, "Already at the edge of the list.")

    return redirect(request.META.get("HTTP_REFERER")
                    or reverse("dashboard:resource_list", args=[slug]))


@staff_required
def resource_export(request, slug):
    """CSV export of the current (filtered) enquiry list."""
    resource = get_resource(slug)
    if resource.slug != "inquiries":
        raise Http404

    rows = queryset_for(resource, request)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="enquiries.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Phone", "Destination", "Travelers",
                     "Travel date", "Message", "Source", "Status", "Received"])
    for inq in rows:
        writer.writerow([inq.full_name, inq.email, inq.phone, inq.destination,
                         inq.travelers, inq.travel_date or "", inq.message,
                         inq.source, inq.get_status_display(),
                         inq.created_at.strftime("%Y-%m-%d %H:%M")])
    return response


# --------------------------------------------------------------------------- #
# Enquiry detail                                                               #
# --------------------------------------------------------------------------- #

@staff_required
def inquiry_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)

    if request.method == "POST":
        form = dash_forms.InquiryForm(request.POST, instance=inquiry)
        if form.is_valid():
            form.save()
            messages.success(request, "Enquiry updated.")
            return redirect("dashboard:inquiry_detail", pk=inquiry.pk)
        messages.error(request, "Please fix the highlighted fields below.")
    else:
        form = dash_forms.InquiryForm(instance=inquiry)
        if inquiry.status == Inquiry.NEW:
            inquiry.status = Inquiry.READ
            inquiry.save(update_fields=["status"])

    return render(request, "dashboard/inquiry_detail.html", dash_context(
        request, active="inquiries", inquiry=inquiry, form=form,
        title=f"Enquiry #{inquiry.pk}",
    ))


# --------------------------------------------------------------------------- #
# Appearance editors                                                           #
# --------------------------------------------------------------------------- #

@staff_required
def text_blocks(request):
    current = dict(SiteText.objects.values_list("key", "value"))
    initial = {b.key: current.get(b.key, b.default) for b in content.TEXT_BLOCKS}
    form = dash_forms.TextBlocksForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        for block in content.TEXT_BLOCKS:
            SiteText.objects.update_or_create(
                key=block.key,
                defaults={"value": form.cleaned_data[block.key]},
            )
        messages.success(request, "Website copy updated.")
        return redirect("dashboard:text_blocks")

    groups = [{"title": title, "entries": [
        {"block": block, "field": form[block.key]} for block in blocks]}
        for title, blocks in content.TEXT_GROUPS.items()]

    return render(request, "dashboard/text_blocks.html", dash_context(
        request, active="text_blocks", form=form, groups=groups,
    ))


@staff_required
def images(request):
    form = dash_forms.ImageBlocksForm(request.POST or None, request.FILES or None)
    stored = {row.key: row for row in SiteImage.objects.all()}

    if request.method == "POST" and form.is_valid():
        for block in content.IMAGE_BLOCKS:
            row, _ = SiteImage.objects.get_or_create(key=block.key)

            if form.cleaned_data[f"clear_{block.key}"]:
                row.image = None          # pre_save signal removes the file
            upload = form.cleaned_data[f"image_{block.key}"]
            if upload:
                row.image = upload
            row.alt_text = form.cleaned_data[f"alt_{block.key}"]
            row.save()

        messages.success(request, "Section images updated.")
        return redirect("dashboard:images")

    groups = []
    for title, blocks in content.IMAGE_GROUPS.items():
        entries = []
        for block in blocks:
            row = stored.get(block.key)
            entries.append({
                "block": block,
                "image": form[f"image_{block.key}"],
                "alt": form[f"alt_{block.key}"],
                "clear": form[f"clear_{block.key}"],
                "current": row.image.url if row and row.image else "",
            })
        groups.append({"title": title, "entries": entries})

    return render(request, "dashboard/images.html", dash_context(
        request, active="images", form=form, groups=groups,
    ))


@staff_required
def settings_view(request):
    instance = SiteSettings.load()
    form = dash_forms.SiteSettingsForm(request.POST or None, request.FILES or None,
                                       instance=instance)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Site settings saved.")
        return redirect("dashboard:settings")

    if request.method == "POST":
        messages.error(request, "Please fix the highlighted fields below.")

    return render(request, "dashboard/settings.html", dash_context(
        request, active="settings", form=form, previews=form.file_previews(),
    ))


# --------------------------------------------------------------------------- #
# Media library                                                                #
# --------------------------------------------------------------------------- #

# Imported lazily to avoid a circular import at module load time.
def _file_fields():
    from ..signals import FILE_FIELDS

    return FILE_FIELDS


def _usage_index():
    """Map stored file name -> list of human labels that reference it."""
    index = {}
    for model, fields in _file_fields().items():
        label = model._meta.verbose_name
        for field_name in fields:
            values = (model.objects.exclude(**{f"{field_name}": ""})
                      .values_list(field_name, flat=True))
            for name in values:
                if name:
                    index.setdefault(str(name), []).append(label)
    return index


@staff_required
def media_library(request):
    root = Path(django_settings.MEDIA_ROOT)
    usage = _usage_index()

    entries = []
    if root.exists():
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            stat = path.stat()
            entries.append({
                "rel": rel,
                "url": django_settings.MEDIA_URL + rel,
                "size": human_size(stat.st_size),
                "bytes": stat.st_size,
                "used_by": sorted(set(usage.get(rel, []))),
            })

    orphans = [e for e in entries if not e["used_by"]]

    if request.method == "POST" and request.POST.get("action") == "purge":
        removed = 0
        for entry in orphans:
            try:
                (root / entry["rel"]).unlink()
                removed += 1
            except OSError:
                continue
        messages.success(request, f"Removed {removed} unused file(s).")
        return redirect("dashboard:media")

    total = sum(e["bytes"] for e in entries)

    return render(request, "dashboard/media.html", dash_context(
        request, active="media", entries=entries, orphans=orphans,
        total=human_size(total), total_count=len(entries),
    ))
