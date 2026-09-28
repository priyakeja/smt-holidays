"""Forms used by the dashboard.

Everything is styled for Bootstrap and grouped into collapsible sections via a
declarative ``layout``. The same ``layout`` drives the form template, so adding
a field to a form is a one-line change here.
"""

from django import forms
from django.db import models

from .. import content
from ..models import (
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
    SiteSettings,
    Stat,
    Step,
    Testimonial,
    TrustBadge,
)


class RichTextWidget(forms.Textarea):
    """Textarea that the dashboard turns into a WYSIWYG editor.

    The editor itself is loaded from a CDN in ``dashboard/base.html`` and
    attached to every ``[data-richtext]`` textarea by ``dashboard.js``.
    """

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.setdefault("rows", 8)
        self.attrs.setdefault("class", "form-control richtext")
        self.attrs.setdefault("data-richtext", "true")


class SectionedFormMixin:
    """Adds Bootstrap widget classes and section grouping to any form."""

    layout = ()
    rich_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self._prepare()

    # -- styling ---------------------------------------------------------- #
    def _style(self):
        for name, field in self.fields.items():
            if name in self.rich_fields:
                field.widget = RichTextWidget()
                continue
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-control")
                widget.attrs.setdefault("rows", 4)
            elif isinstance(widget, (forms.ClearableFileInput, forms.FileInput)):
                widget.attrs.setdefault("class", "form-control")
            elif isinstance(widget, forms.DateInput):
                widget.attrs.setdefault("class", "form-control")
                widget.input_type = "date"
            else:
                widget.attrs.setdefault("class", "form-control")

    # -- hooks for subclasses --------------------------------------------- #
    def _prepare(self):
        """Override to tweak fields once they exist."""

    def _next_order(self):
        return (self._meta.model.objects.aggregate(models.Max("order"))["order__max"] or 0) + 1

    # -- template helpers -------------------------------------------------- #
    def grouped_fields(self):
        """``[{title, description, fields:[BoundField]}, ...]`` for the template."""
        used = set()
        groups = []
        for title, description, names in self.layout:
            fields = [self[n] for n in names if n in self.fields]
            used.update(n for n in names if n in self.fields)
            if fields:
                groups.append({"title": title, "description": description, "fields": fields})
        leftover = [self[name] for name in self.fields if name not in used]
        if leftover:
            groups.append({"title": "More options", "description": "", "fields": leftover})
        return groups

    @property
    def title_field(self):
        for name in ("title", "label", "question", "customer_name", "full_name", "text"):
            if name in self.fields:
                return self[name]
        return None

    def file_previews(self):
        """``{field_name: url}`` for file fields that already hold a value."""
        previews = {}
        instance = getattr(self, "instance", None)
        if not instance or not instance.pk:
            return previews
        for name in self.fields:
            value = getattr(instance, name, None)
            # Read ``.name`` first: ``.url`` raises ValueError when the field is
            # empty, and hasattr() only swallows AttributeError.
            if not getattr(value, "name", None):
                continue
            try:
                previews[name] = value.url
            except ValueError:
                continue
        return previews


class OrderMixin(SectionedFormMixin):
    """Prepares ordering, visibility and icon fields for content resources."""

    orderable = True
    visibility = True

    def _prepare(self):
        model = self._meta.model
        if self.orderable and "order" in self.fields and not self.instance.pk:
            self.fields["order"].initial = self._next_order()
        if self.orderable and "order" in self.fields:
            self.fields["order"].label = "Position"
            self.fields["order"].help_text = (
                "Lower numbers appear first. You can also use the arrows in the list."
            )
        if self.visibility and "is_active" in self.fields:
            self.fields["is_active"].label = "Show on website"


# Long-form copy that gets the WYSIWYG editor.
RICH_TEXT_HELP = "Use the toolbar to format text, add lists and insert links."


class CompactOrderMixin(OrderMixin):
    """Variation kept for symmetry; currently identical to :class:`OrderMixin`."""


# --------------------------------------------------------------------------- #
# Content resources                                                            #
# --------------------------------------------------------------------------- #

def _visibility_section(extra=()):
    return ("Visibility & order", "",
            (*extra, "is_active", "order"))


class PackageForm(OrderMixin, forms.ModelForm):
    rich_fields = ("overview",)
    layout = (
        ("Package details", "What customers see first.",
         ("title", "slug", "category", "duration", "badge", "short_description")),
        ("Description", "The longer story shown on the package page.",
         ("overview",)),
        ("Pricing", "Price per person in INR. The \u20b9 symbol is added automatically.",
         ("starting_price",)),
        ("Images & files", "", ("main_image", "brochure")),
        ("Highlights & inclusions", "One item per line.",
         ("highlights", "inclusions", "exclusions")),
        ("Search engine listing", "Optional. Leave blank to use the package title.",
         ("seo_title", "seo_description")),
        ("Visibility & order", "Only featured packages appear on the home page.",
         ("is_popular", "is_active", "order")),
    )

    class Meta:
        model = Package
        fields = "__all__"

    def _prepare(self):
        super()._prepare()
        self.fields["slug"].help_text = "Leave blank to generate it from the title."
        self.fields["overview"].help_text = RICH_TEXT_HELP
        self.fields["exclusions"].widget.attrs["rows"] = 4
        self.fields["highlights"].widget.attrs["rows"] = 5
        self.fields["inclusions"].widget.attrs["rows"] = 5
        self.fields["is_popular"].label = "Feature on home page"


class PackageImageForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Photo", "", ("package", "image")),
        ("Caption & order", "", ("caption", "order")),
    )

    class Meta:
        model = PackageImage
        fields = ["package", "image", "caption", "order"]

    def _prepare(self):
        super()._prepare()
        self.fields.pop("is_active", None)


class GalleryForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Photo", "", ("image", "caption", "category")),
        _visibility_section(("is_featured",)),
    )

    class Meta:
        model = GalleryImage
        fields = "__all__"

    def _prepare(self):
        super()._prepare()
        self.fields["is_featured"].label = "Feature on home page"


class TestimonialForm(CompactOrderMixin, forms.ModelForm):
    rich_fields = ("review_text",)
    layout = (
        ("Customer", "", ("customer_name", "location", "rating")),
        ("Review", "", ("review_text",)),
        ("Photo", "Optional. The customer's initial is shown when empty.",
         ("customer_image",)),
        _visibility_section(("is_featured",)),
    )

    class Meta:
        model = Testimonial
        fields = "__all__"

    def _prepare(self):
        super()._prepare()
        self.fields["review_text"].help_text = RICH_TEXT_HELP
        self.fields["is_featured"].label = "Feature on home page"


class FAQForm(CompactOrderMixin, forms.ModelForm):
    rich_fields = ("answer",)
    layout = (
        ("Question & answer", "", ("question", "answer")),
        _visibility_section(),
    )

    class Meta:
        model = FAQ
        fields = "__all__"


class ServiceForm(CompactOrderMixin, forms.ModelForm):
    rich_fields = ("description",)
    layout = (
        ("Card", "", ("icon", "title", "description")),
        _visibility_section(),
    )

    class Meta:
        model = Service
        fields = "__all__"

    def _prepare(self):
        super()._prepare()
        self.fields["icon"].help_text = "Font Awesome class, e.g. fa-solid fa-headset."


class StepForm(CompactOrderMixin, forms.ModelForm):
    rich_fields = ("description",)
    layout = (
        ("Step", "", ("icon", "title", "description")),
        _visibility_section(),
    )

    class Meta:
        model = Step
        fields = "__all__"


class StatForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Counter", "Fill in a number for an animated counter, or leave it empty "
                    "and use the text value (for example 24/7).",
         ("number", "suffix", "value")),
        ("Label", "", ("label",)),
        _visibility_section(),
    )

    class Meta:
        model = Stat
        fields = "__all__"


class PointForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Where it appears", "", ("group",)),
        ("Bullet", "", ("icon", "text")),
        _visibility_section(),
    )

    class Meta:
        model = Point
        fields = "__all__"


class HeroSlideForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Image", "Slides rotate automatically on the home page.",
         ("image", "title", "subtitle")),
        ("Call to action", "Optional button over the slide.",
         ("cta_label", "cta_url")),
        _visibility_section(),
    )

    class Meta:
        model = HeroSlide
        fields = "__all__"


class HeroBadgeForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Badge", "", ("icon", "text")),
        _visibility_section(),
    )

    class Meta:
        model = HeroBadge
        fields = "__all__"


class TrustBadgeForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Badge", "", ("icon", "text")),
        _visibility_section(),
    )

    class Meta:
        model = TrustBadge
        fields = "__all__"


class ContactMethodForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Card", "", ("icon", "title", "value")),
        ("Link", "Optional. Use {phone} or {email} to insert the value from "
                 "site settings.", ("link",)),
        _visibility_section(),
    )

    class Meta:
        model = ContactMethod
        fields = "__all__"


class DownloadForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("File", "", ("title", "file", "description")),
        _visibility_section(),
    )

    class Meta:
        model = DownloadableFile
        fields = "__all__"


class MenuItemForm(CompactOrderMixin, forms.ModelForm):
    layout = (
        ("Link", "", ("menu", "label")),
        ("Where it goes", "Choose one of your pages, or type a custom link.",
         ("page", "url")),
        ("Extras", "", ("parent", "icon")),
        _visibility_section(),
    )

    class Meta:
        model = MenuItem
        fields = "__all__"

    def _prepare(self):
        super()._prepare()
        query = MenuItem.objects.all()
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = query.order_by("menu", "order")
        self.fields["parent"].required = False

    def clean(self):
        cleaned = super().clean()
        parent = cleaned.get("parent")
        if not parent:
            return cleaned
        # Guard against a link being nested under one of its own descendants.
        seen = set()
        node = parent
        while node is not None and node.pk not in seen:
            if self.instance.pk and node.pk == self.instance.pk:
                raise forms.ValidationError("A menu item cannot be nested inside itself.")
            seen.add(node.pk)
            node = node.parent
        return cleaned


class InquiryForm(SectionedFormMixin, forms.ModelForm):
    layout = (
        ("Traveler", "", ("full_name", "email", "phone", "destination",
                          "travelers", "travel_date")),
        ("Message", "", ("message",)),
        ("Follow-up", "", ("status", "is_contacted", "source", "admin_notes")),
    )

    class Meta:
        model = Inquiry
        fields = ["full_name", "email", "phone", "destination", "travelers",
                  "travel_date", "message", "status", "is_contacted", "source",
                  "admin_notes"]

    def _prepare(self):
        self.fields["admin_notes"].widget.attrs["rows"] = 4
        self.fields["admin_notes"].help_text = "Internal only — never shown on the website."


class SiteSettingsForm(SectionedFormMixin, forms.ModelForm):
    layout = (
        ("Identity", "", ("site_name", "brand_mark", "tagline")),
        ("Contact details", "Used across the header, footer and contact page.",
         ("phone_display", "phone_raw", "email", "address")),
        ("Social links", "", ("instagram_url", "facebook_url", "youtube_url", "maps_url")),
        ("Search engines", "Shown in Google results for the home page.",
         ("meta_title", "meta_description")),
        ("Brand images", "", ("logo", "favicon")),
    )

    class Meta:
        model = SiteSettings
        fields = "__all__"


# --------------------------------------------------------------------------- #
# Registry-driven text and image editors                                       #
# --------------------------------------------------------------------------- #

def _build_text_form():
    fields = {}
    for block in content.TEXT_BLOCKS:
        if block.rich:
            widget = RichTextWidget()
        elif block.multiline:
            widget = forms.Textarea(attrs={"rows": 3})
        else:
            widget = forms.TextInput()
        fields[block.key] = forms.CharField(
            label=block.label, required=False, widget=widget,
            help_text=block.help_text or (RICH_TEXT_HELP if block.rich else ""))
    return type("TextBlocksForm", (SectionedFormMixin, forms.Form), fields)


def _build_image_form():
    fields = {}
    for block in content.IMAGE_BLOCKS:
        fields[f"image_{block.key}"] = forms.ImageField(
            label=block.label, required=False,
            help_text=block.help_text or "Recommended width 1600px or more.")
        fields[f"alt_{block.key}"] = forms.CharField(
            label="Alt text", required=False,
            help_text="Describes the image for screen readers and search engines.")
        fields[f"clear_{block.key}"] = forms.BooleanField(
            label="Remove current image", required=False)
    return type("ImageBlocksForm", (SectionedFormMixin, forms.Form), fields)


TextBlocksForm = _build_text_form()
ImageBlocksForm = _build_image_form()
