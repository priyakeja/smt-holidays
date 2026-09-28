"""Database models for the fully dynamic SMT Holidays website.

Design notes
------------
* Structured content (packages, gallery, reviews, ...) gets a real model.
* One-off copy (headings, paragraphs, button labels) lives in
  :class:`SiteText` and is declared in ``core/content.py``.
* Section/hero images that are not attached to a record live in
  :class:`SiteImage`, declared in the same registry.
* Every model with an image or file gets automatic cleanup of replaced and
  deleted files (see ``core/signals.py``).
"""

import os

from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils.text import slugify

from .pages import PAGE_CHOICES, PAGE_HELP


def _lines(text):
    """Split a textarea value into a clean list of non-empty lines."""
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


class OrderedModel(models.Model):
    """Base for content lists that the admin can reorder and hide."""

    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_active = models.BooleanField("Show on website", default=True)

    class Meta:
        abstract = True
        ordering = ["order", "id"]


# --------------------------------------------------------------------------- #
# Global settings                                                              #
# --------------------------------------------------------------------------- #

class SiteSettings(models.Model):
    """Site-wide identity, contact details and social links (a singleton)."""

    site_name = models.CharField(max_length=80, default="SMT Holidays")
    brand_mark = models.CharField(
        max_length=3, default="S", help_text="Letter shown in the logo square.")
    tagline = models.CharField(max_length=160, blank=True)

    phone_display = models.CharField("Phone (as shown)", max_length=30,
                                     default="+91 90000 00000")
    phone_raw = models.CharField(
        "Phone (digits only)", max_length=20, default="919000000000",
        help_text="Used for call and WhatsApp links, e.g. 919000000000.")
    email = models.EmailField(default="hello@smtholidays.in")
    address = models.CharField(max_length=250,
                               default="Sankarankovil, Tirunelveli, Tamil Nadu 627756, India")

    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    maps_url = models.URLField(blank=True, default="https://maps.google.com/?q=Sankarankovil")

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    logo = models.ImageField(upload_to="brand/", blank=True, null=True)
    favicon = models.ImageField(upload_to="brand/", blank=True, null=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce a single row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_url(self):
        return f"https://wa.me/{self.phone_raw}"

    @property
    def call_url(self):
        return f"tel:+{self.phone_raw}"

    def social_links(self):
        """Only the networks that actually have a URL, ready for the footer."""
        links = [
            ("instagram", "Instagram", self.instagram_url),
            ("facebook", "Facebook", self.facebook_url),
            ("youtube", "YouTube", self.youtube_url),
            ("whatsapp", "WhatsApp", self.whatsapp_url),
        ]
        return [{"icon": i, "label": l, "url": u} for i, l, u in links if u]


class SiteText(models.Model):
    """A single editable piece of copy, keyed by an entry in ``content.py``."""

    key = models.SlugField(max_length=80, unique=True)
    value = models.TextField(blank=True)

    class Meta:
        verbose_name = "Text block"
        verbose_name_plural = "Text blocks"
        ordering = ["key"]

    def __str__(self):
        return self.key


class SiteImage(models.Model):
    """A single editable image, keyed by an entry in ``content.py``."""

    key = models.SlugField(max_length=80, unique=True)
    image = models.ImageField(upload_to="site/", blank=True, null=True)
    alt_text = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "Section image"
        verbose_name_plural = "Section images"
        ordering = ["key"]

    def __str__(self):
        return self.key


# --------------------------------------------------------------------------- #
# Navigation                                                                   #
# --------------------------------------------------------------------------- #

class MenuItem(OrderedModel):
    HEADER = "header"
    FOOTER = "footer"
    TOPBAR = "topbar"
    MENU_CHOICES = [(HEADER, "Header menu"), (FOOTER, "Footer menu"), (TOPBAR, "Top bar")]

    menu = models.CharField(max_length=20, choices=MENU_CHOICES, default=HEADER)
    label = models.CharField(max_length=60)
    page = models.CharField(
        "Page", max_length=40, blank=True, choices=PAGE_CHOICES, help_text=PAGE_HELP)
    url = models.CharField("Custom link", max_length=250, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE,
        related_name="children", help_text="Optional: nest this link under another one.")
    icon = models.CharField(
        max_length=60, blank=True, help_text="Optional Font Awesome class, e.g. fa-brands fa-whatsapp.")

    class Meta(OrderedModel.Meta):
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"

    def __str__(self):
        return f"{self.get_menu_display()}: {self.label}"

    def get_url(self):
        if self.page:
            try:
                return reverse(self.page)
            except NoReverseMatch:
                pass
        return self.url or "#"

    @property
    def is_external(self):
        return self.get_url().startswith("http")


# --------------------------------------------------------------------------- #
# Home page sections                                                           #
# --------------------------------------------------------------------------- #

class HeroSlide(OrderedModel):
    image = models.ImageField(upload_to="hero/")
    title = models.CharField(max_length=120, blank=True,
                             help_text="Optional heading shown over this slide.")
    subtitle = models.TextField(blank=True)
    cta_label = models.CharField(max_length=40, blank=True)
    cta_url = models.CharField(max_length=250, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Hero slide"
        verbose_name_plural = "Hero slides"

    def __str__(self):
        return self.title or f"Slide {self.pk}"


class HeroBadge(OrderedModel):
    icon = models.CharField(max_length=60, default="fa-solid fa-circle-check",
                            help_text="Font Awesome class.")
    text = models.CharField(max_length=80)

    class Meta(OrderedModel.Meta):
        verbose_name = "Hero badge"
        verbose_name_plural = "Hero badges"

    def __str__(self):
        return self.text


class TrustBadge(OrderedModel):
    icon = models.CharField(max_length=60, default="fa-solid fa-circle-check")
    text = models.CharField(max_length=80)

    class Meta(OrderedModel.Meta):
        verbose_name = "Trust badge"
        verbose_name_plural = "Trust badges"

    def __str__(self):
        return self.text


class Service(OrderedModel):
    """A card in the 'Why choose us' section."""

    icon = models.CharField(max_length=60, default="fa-solid fa-star")
    title = models.CharField(max_length=80)
    description = models.TextField()

    class Meta(OrderedModel.Meta):
        verbose_name = "Service / feature"
        verbose_name_plural = "Services / features"

    def __str__(self):
        return self.title


class Step(OrderedModel):
    """A card in the 'How it works' section."""

    icon = models.CharField(max_length=60, default="fa-regular fa-circle-check")
    title = models.CharField(max_length=80)
    description = models.TextField()

    class Meta(OrderedModel.Meta):
        verbose_name = "Process step"
        verbose_name_plural = "Process steps"

    def __str__(self):
        return self.title

    @property
    def number(self):
        return f"{self.order + 1:02d}"


class Stat(OrderedModel):
    """A counter tile in the about section.

    Set ``number`` for an animated counter, or leave it empty and fill ``value``
    with free text such as ``24/7``.
    """

    number = models.PositiveIntegerField(null=True, blank=True)
    suffix = models.CharField(max_length=8, blank=True, help_text="e.g. +")
    value = models.CharField(max_length=20, blank=True,
                             help_text="Used only when no number is given, e.g. 24/7.")
    label = models.CharField(max_length=60)

    class Meta(OrderedModel.Meta):
        verbose_name = "Statistic"
        verbose_name_plural = "Statistics"

    def __str__(self):
        return f"{self.display} {self.label}"

    @property
    def display(self):
        if self.number is None:
            return self.value
        return f"{self.number:,}{self.suffix}"


class Point(OrderedModel):
    """A tick-list bullet, used in the about and enquiry sections."""

    ABOUT = "about"
    CONSULT = "consult"
    GROUP_CHOICES = [(ABOUT, "About section"), (CONSULT, "Enquiry section")]

    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default=ABOUT)
    icon = models.CharField(max_length=60, blank=True)
    text = models.CharField(max_length=160)

    class Meta(OrderedModel.Meta):
        verbose_name = "Bullet point"
        verbose_name_plural = "Bullet points"

    def __str__(self):
        return self.text


# --------------------------------------------------------------------------- #
# Packages                                                                     #
# --------------------------------------------------------------------------- #

class Package(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    duration = models.CharField(max_length=20, help_text="e.g. 3D/2N")
    starting_price = models.PositiveIntegerField(help_text="Per person, in INR")
    category = models.CharField("Location / category", max_length=80, blank=True)
    badge = models.CharField(max_length=30, blank=True, help_text="Optional ribbon, e.g. Best seller.")

    short_description = models.CharField(max_length=200)
    overview = models.TextField(
        blank=True, help_text="Longer description shown on the package page.")
    main_image = models.ImageField(upload_to="packages/")

    highlights = models.TextField(help_text="One highlight per line")
    inclusions = models.TextField(help_text="One inclusion per line")
    exclusions = models.TextField(blank=True, help_text="One exclusion per line")

    brochure = models.FileField(
        upload_to="brochures/", blank=True, null=True,
        help_text="Optional PDF shown as a download on the package page.")

    is_popular = models.BooleanField("Featured on home page", default=True)
    is_active = models.BooleanField("Show on website", default=True)

    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("package_detail", args=[self.slug])

    @property
    def price_display(self):
        return f"{self.starting_price:,}"

    @property
    def highlight_list(self):
        return _lines(self.highlights)

    @property
    def inclusion_list(self):
        return _lines(self.inclusions)

    @property
    def exclusion_list(self):
        return _lines(self.exclusions)

    def as_dict(self):
        return {"title": self.title, "slug": self.slug, "duration": self.duration,
                "category": self.category, "price": self.price_display,
                "image": self.main_image.url,
                "highlights": self.highlight_list, "inclusions": self.inclusion_list}


class PackageImage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="packages/gallery/")
    caption = models.CharField(max_length=120, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Package photo"
        verbose_name_plural = "Package photos"

    def __str__(self):
        return self.caption or f"Photo {self.pk}"


class GalleryImage(OrderedModel):
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=60, blank=True)
    is_featured = models.BooleanField("Feature on home page", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Gallery image"
        verbose_name_plural = "Gallery images"

    def __str__(self):
        return self.caption or f"Image {self.pk}"


class Testimonial(OrderedModel):
    customer_name = models.CharField(max_length=80)
    location = models.CharField(max_length=80, blank=True)
    rating = models.PositiveSmallIntegerField(
        default=5, choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField()
    customer_image = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    is_featured = models.BooleanField("Feature on home page", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.customer_name} ({self.location})"

    @property
    def initial(self):
        return (self.customer_name or "?")[:1].upper()

    @property
    def stars(self):
        return range(1, 6)


class FAQ(OrderedModel):
    question = models.CharField(max_length=200)
    answer = models.TextField()

    class Meta(OrderedModel.Meta):
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class DownloadableFile(OrderedModel):
    """Brochures, itineraries, price lists - anything visitors can download."""

    title = models.CharField(max_length=120)
    file = models.FileField(upload_to="downloads/")
    description = models.CharField(max_length=200, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Downloadable file"
        verbose_name_plural = "Downloadable files"

    def __str__(self):
        return self.title

    @property
    def extension(self):
        return os.path.splitext(self.file.name)[1].lstrip(".").upper()

    @property
    def size_display(self):
        try:
            size = self.file.size
        except (OSError, ValueError):
            return ""
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return ""


# --------------------------------------------------------------------------- #
# Enquiries                                                                    #
# --------------------------------------------------------------------------- #

class Inquiry(models.Model):
    NEW = "new"
    READ = "read"
    REPLIED = "replied"
    CLOSED = "closed"
    STATUS_CHOICES = [(NEW, "New"), (READ, "Read"), (REPLIED, "Replied"), (CLOSED, "Closed")]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.CharField("Phone number", max_length=20)
    destination = models.CharField(max_length=100, blank=True)
    travelers = models.PositiveSmallIntegerField(default=2)
    travel_date = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True, help_text="Free-text message from the contact form.")
    source = models.CharField(max_length=40, blank=True,
                              help_text="Form / package that created the lead")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=NEW)
    admin_notes = models.TextField(blank=True, help_text="Internal notes (never shown publicly).")
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"

    def __str__(self):
        return f"{self.full_name} - {self.destination or 'General'}"

    @property
    def status_tone(self):
        return {"new": "info", "read": "muted", "replied": "success",
                "closed": "dark"}.get(self.status, "muted")


class ContactMethod(OrderedModel):
    """A contact card on the contact page (phone, email, address, ...)."""

    icon = models.CharField(max_length=60, default="fa-solid fa-phone")
    title = models.CharField(max_length=60)
    value = models.CharField(max_length=160)
    link = models.CharField(
        max_length=250, blank=True,
        help_text="Optional. Use 'tel:{phone}', 'mailto:{email}' or '{maps}' "
                  "placeholders (the last one becomes the Maps URL from Site Settings).")

    class Meta(OrderedModel.Meta):
        verbose_name = "Contact method"
        verbose_name_plural = "Contact methods"

    def __str__(self):
        return self.title

    @staticmethod
    def _substitute(text, site):
        """Replace {phone_display}/{phone}/{email}/{maps} from site settings.

        ``phone_display`` is replaced first because ``{phone}`` is a prefix of it.
        """
        return (text
                .replace("{phone_display}", site.phone_display)
                .replace("{phone}", site.phone_raw)
                .replace("{email}", site.email)
                .replace("{maps}", site.maps_url))

    def get_link(self):
        if not self.link:
            return ""
        return self._substitute(self.link, SiteSettings.load())

    @property
    def display_value(self):
        return self._substitute(self.value, SiteSettings.load())
