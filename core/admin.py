"""Django admin registrations.

The custom dashboard at ``/dashboard/`` is the main editing interface. These
registrations are kept so that ``/admin/`` remains a complete, working fallback
(useful for bulk edits, permission management and user accounts).
"""

import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import (
    ContactMethod,
    DownloadableFile,
    FAQ,
    GalleryImage,
    HeroBadge,
    HeroSlide,
    Inquiry,
    MenuItem,
    Package,
    PackageImage,
    Point,
    Service,
    SiteImage,
    SiteSettings,
    SiteText,
    Stat,
    Step,
    Testimonial,
    TrustBadge,
)


def _image(obj, field, height=100):
    """<img> tag for an ImageField, or None when there is nothing to show."""
    if obj is None or not getattr(obj, "pk", None):
        return None
    img = getattr(obj, field, None)
    if not img:
        return None
    try:
        return format_html(
            '<img src="{}" style="height:{}px;border-radius:8px;object-fit:cover">',
            img.url, height)
    except ValueError:
        return None


def thumb(obj, field="main_image"):
    return _image(obj, field, 44) or "-"


class OrderedAdmin(admin.ModelAdmin):
    """Admin base for the simple ordered content lists.

    Subclasses declare ``list_display`` ending with ``is_active`` and ``order``
    so both can be edited straight from the changelist.
    """

    save_on_top = True
    list_editable = ("is_active", "order")


class PreviewMixin:
    """Adds an image thumbnail column and an inline preview of the file."""

    image_field = "image"

    @admin.display(description="Image")
    def preview(self, obj):
        return thumb(obj, self.image_field)

    @admin.display(description="Current image")
    def image_preview(self, obj):
        return _image(obj, self.image_field, 160) or "No image uploaded yet."


class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    inlines = (PackageImageInline,)
    list_display = ("preview", "title", "duration", "starting_price", "category",
                    "is_popular", "is_active", "order")
    list_display_links = ("preview", "title")
    list_editable = ("starting_price", "is_popular", "is_active", "order")
    list_filter = ("is_active", "is_popular", "category")
    search_fields = ("title", "category", "short_description", "overview")
    prepopulated_fields = {"slug": ("title",)}
    save_on_top = True
    readonly_fields = ("image_preview",)
    fieldsets = (
        ("Package details", {"fields": ("title", "slug", "category", "duration",
                                        "badge", "short_description")}),
        ("Description", {"fields": ("overview",)}),
        ("Pricing", {"fields": ("starting_price",)}),
        ("Images & files", {"fields": ("main_image", "image_preview", "brochure")}),
        ("Highlights & inclusions", {"fields": ("highlights", "inclusions", "exclusions")}),
        ("Search engines", {"fields": ("seo_title", "seo_description")}),
        ("Visibility", {"fields": ("is_popular", "is_active", "order")}),
    )

    @admin.display(description="Image")
    def preview(self, obj):
        return thumb(obj)

    @admin.display(description="Current image")
    def image_preview(self, obj):
        return _image(obj, "main_image", 140) or "No image uploaded yet."


@admin.register(PackageImage)
class PackageImageAdmin(admin.ModelAdmin):
    list_display = ("preview", "package", "caption", "order")
    list_editable = ("caption", "order")
    list_filter = ("package",)
    search_fields = ("caption",)

    @admin.display(description="Photo")
    def preview(self, obj):
        return thumb(obj, "image")


@admin.register(FAQ)
class FAQAdmin(OrderedAdmin):
    list_display = ("question", "answer_excerpt", "is_active", "order")
    search_fields = ("question", "answer")

    @admin.display(description="Answer")
    def answer_excerpt(self, obj):
        return (obj.answer[:80] + "…") if len(obj.answer) > 80 else obj.answer


@admin.register(Testimonial)
class TestimonialAdmin(PreviewMixin, admin.ModelAdmin):
    image_field = "customer_image"
    list_display = ("avatar", "customer_name", "location", "rating",
                    "is_featured", "is_active", "order")
    list_display_links = ("avatar", "customer_name")
    list_editable = ("rating", "is_featured", "is_active", "order")
    list_filter = ("is_active", "is_featured", "rating")
    search_fields = ("customer_name", "location", "review_text")
    readonly_fields = ("photo_preview",)
    fields = ("customer_name", "location", "rating", "review_text",
              "customer_image", "photo_preview", "is_featured", "is_active", "order")

    @admin.display(description="")
    def avatar(self, obj):
        return _image(obj, "customer_image", 44) or "-"

    @admin.display(description="Current photo")
    def photo_preview(self, obj):
        return _image(obj, "customer_image", 120) or "No photo uploaded."


@admin.register(GalleryImage)
class GalleryImageAdmin(PreviewMixin, admin.ModelAdmin):
    list_display = ("preview", "caption", "category", "is_featured", "is_active", "order")
    list_display_links = ("preview", "caption")
    list_editable = ("category", "is_featured", "is_active", "order")
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("caption", "category")
    readonly_fields = ("image_preview",)
    fields = ("image", "image_preview", "caption", "category",
              "is_featured", "is_active", "order")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "menu", "page", "parent", "is_active", "order")
    list_editable = ("menu", "page", "is_active", "order")
    list_filter = ("menu", "is_active")
    search_fields = ("label", "url")
    save_on_top = True


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    save_on_top = True
    fieldsets = (
        ("Identity", {"fields": ("site_name", "brand_mark", "tagline",
                                 "logo", "favicon")}),
        ("Contact details", {"fields": ("phone_display", "phone_raw", "email", "address")}),
        ("Social links", {"fields": ("instagram_url", "facebook_url",
                                     "youtube_url", "maps_url")}),
        ("Search engines", {"fields": ("meta_title", "meta_description")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteText)
class SiteTextAdmin(admin.ModelAdmin):
    list_display = ("key", "value_excerpt")
    search_fields = ("key", "value")

    @admin.display(description="Value")
    def value_excerpt(self, obj):
        return (obj.value[:100] + "…") if len(obj.value) > 100 else obj.value


@admin.register(SiteImage)
class SiteImageAdmin(PreviewMixin, admin.ModelAdmin):
    list_display = ("key", "preview", "alt_text")
    search_fields = ("key", "alt_text")
    readonly_fields = ("image_preview",)
    fields = ("key", "image", "image_preview", "alt_text")


@admin.register(HeroSlide)
class HeroSlideAdmin(PreviewMixin, admin.ModelAdmin):
    list_display = ("preview", "title", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("title", "subtitle")
    readonly_fields = ("image_preview",)
    fields = ("image", "image_preview", "title", "subtitle",
              "cta_label", "cta_url", "is_active", "order")


@admin.register(HeroBadge)
class HeroBadgeAdmin(OrderedAdmin):
    list_display = ("text", "icon", "is_active", "order")
    search_fields = ("text",)


@admin.register(TrustBadge)
class TrustBadgeAdmin(OrderedAdmin):
    list_display = ("text", "icon", "is_active", "order")
    search_fields = ("text",)


@admin.register(Service)
class ServiceAdmin(OrderedAdmin):
    list_display = ("title", "icon", "is_active", "order")
    search_fields = ("title", "description")


@admin.register(Step)
class StepAdmin(OrderedAdmin):
    list_display = ("title", "icon", "is_active", "order")
    search_fields = ("title", "description")


@admin.register(Stat)
class StatAdmin(OrderedAdmin):
    list_display = ("label", "number", "suffix", "value", "is_active", "order")
    search_fields = ("label", "value")


@admin.register(Point)
class PointAdmin(OrderedAdmin):
    list_display = ("text", "group", "icon", "is_active", "order")
    list_filter = ("group",)
    search_fields = ("text",)


@admin.register(ContactMethod)
class ContactMethodAdmin(OrderedAdmin):
    list_display = ("title", "value", "link", "icon", "is_active", "order")
    search_fields = ("title", "value")


@admin.register(DownloadableFile)
class DownloadableFileAdmin(OrderedAdmin):
    list_display = ("title", "file", "description", "is_active", "order")
    search_fields = ("title", "description")


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "destination", "travelers", "travel_date",
                    "source", "status", "is_contacted", "created_at")
    list_display_links = ("full_name",)
    list_editable = ("status", "is_contacted")
    list_filter = ("status", "is_contacted", "destination", "created_at")
    search_fields = ("full_name", "email", "phone", "destination", "message")
    date_hierarchy = "created_at"
    save_on_top = True
    readonly_fields = ("created_at",)
    actions = ("export_csv", "mark_contacted", "mark_not_contacted")

    @admin.action(description="Export selected enquiries to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="enquiries.csv"'
        writer = csv.writer(response)
        writer.writerow(["Name", "Email", "Phone", "Destination", "Travelers",
                         "Travel date", "Message", "Source", "Status", "Created"])
        for inquiry in queryset:
            writer.writerow([inquiry.full_name, inquiry.email, inquiry.phone,
                             inquiry.destination, inquiry.travelers,
                             inquiry.travel_date, inquiry.message, inquiry.source,
                             inquiry.get_status_display(),
                             inquiry.created_at.strftime("%Y-%m-%d %H:%M")])
        return response

    @admin.action(description="Mark as contacted")
    def mark_contacted(self, request, queryset):
        updated = queryset.update(is_contacted=True, status=Inquiry.REPLIED)
        self.message_user(request, f"{updated} enquiry(ies) marked as contacted.")

    @admin.action(description="Mark as not contacted")
    def mark_not_contacted(self, request, queryset):
        updated = queryset.update(is_contacted=False)
        self.message_user(request, f"{updated} enquiry(ies) marked as not contacted.")
