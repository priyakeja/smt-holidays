"""Declarative registry that drives the whole dashboard.

Each :class:`Resource` bundles a model, its form, the columns shown in the list
and the sidebar group it belongs to. The generic CRUD views in ``views.py``
read this registry, so exposing a new model in the dashboard is one entry here
plus one login-free form in ``forms.py``.
"""

from dataclasses import dataclass, field

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
    Stat,
    Step,
    Testimonial,
    TrustBadge,
)
from . import forms


@dataclass
class Column:
    name: str
    label: str = ""
    kind: str = "text"     # text | image | bool | date | price | stars | choice | file
    primary: bool = False  # used as the link to the edit page


@dataclass
class Resource:
    slug: str
    model: type
    form: type
    label: str
    plural: str
    icon: str
    group: str
    columns: tuple = field(default_factory=tuple)
    search_fields: tuple = ()
    filter_fields: tuple = ()
    orderable: bool = False
    toggle_field: str = "is_active"
    detail: bool = False
    intro: str = ""

    @property
    def add_label(self):
        return f"Add {self.label.lower()}"


RESOURCES = [
    Resource(
        slug="inquiries", model=Inquiry, form=forms.InquiryForm,
        label="Enquiry", plural="Enquiries", icon="fa-inbox", group="Enquiries",
        columns=(Column("full_name", "Name", primary=True),
                 Column("phone", "Phone"),
                 Column("destination", "Destination"),
                 Column("travelers", "Pax"),
                 Column("travel_date", "Travel date", "date"),
                 Column("source", "Source"),
                 Column("status", "Status", "choice"),
                 Column("created_at", "Received", "date")),
        search_fields=("full_name", "email", "phone", "destination", "message"),
        filter_fields=("status", "is_contacted", "destination"),
        orderable=False, toggle_field="is_contacted", detail=True,
        intro="Every enquiry submitted through the website forms.",
    ),
    Resource(
        slug="packages", model=Package, form=forms.PackageForm,
        label="Package", plural="Tour Packages", icon="fa-suitcase-rolling",
        group="Packages",
        columns=(Column("main_image", "Image", "image"),
                 Column("title", "Title", primary=True),
                 Column("category", "Location"),
                 Column("duration", "Duration"),
                 Column("starting_price", "Price", "price"),
                 Column("is_popular", "Featured", "bool"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("title", "category", "short_description"),
        filter_fields=("is_active", "is_popular", "category"),
        orderable=True,
        intro="Everything about the holidays you sell, including the detail page.",
    ),
    Resource(
        slug="package-photos", model=PackageImage, form=forms.PackageImageForm,
        label="Package photo", plural="Package Photo Albums", icon="fa-camera-retro",
        group="Packages",
        columns=(Column("image", "Photo", "image"),
                 Column("package", "Package", primary=True),
                 Column("caption", "Caption"),
                 Column("order", "Pos")),
        search_fields=("caption",),
        filter_fields=("package",),
        orderable=False, toggle_field="",
        intro="Extra photos shown in the album on each package page.",
    ),
    Resource(
        slug="hero-slides", model=HeroSlide, form=forms.HeroSlideForm,
        label="Hero slide", plural="Hero Slides", icon="fa-images", group="Home page",
        columns=(Column("image", "Image", "image"),
                 Column("title", "Title", primary=True),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("title", "subtitle"),
        filter_fields=("is_active",),
        orderable=True,
        intro="Full-width banners that rotate behind the home page heading.",
    ),
    Resource(
        slug="hero-badges", model=HeroBadge, form=forms.HeroBadgeForm,
        label="Hero badge", plural="Hero Badges", icon="fa-certificate",
        group="Home page",
        columns=(Column("text", "Text", primary=True),
                 Column("icon", "Icon"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("text",),
        orderable=True,
        intro="The small glass chips under the hero buttons.",
    ),
    Resource(
        slug="trust-badges", model=TrustBadge, form=forms.TrustBadgeForm,
        label="Trust badge", plural="Trust Badges", icon="fa-shield-heart",
        group="Home page",
        columns=(Column("text", "Text", primary=True),
                 Column("icon", "Icon"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("text",),
        orderable=True,
        intro="Trust signals shown next to the Google rating card.",
    ),
    Resource(
        slug="services", model=Service, form=forms.ServiceForm,
        label="Service", plural="Services / Why Us", icon="fa-hand-holding-heart",
        group="Home page",
        columns=(Column("title", "Title", primary=True),
                 Column("icon", "Icon"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("title", "description"),
        orderable=True,
        intro="The 'Why choose us' cards.",
    ),
    Resource(
        slug="steps", model=Step, form=forms.StepForm,
        label="Step", plural="Process Steps", icon="fa-list-ol", group="Home page",
        columns=(Column("title", "Title", primary=True),
                 Column("icon", "Icon"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("title", "description"),
        orderable=True,
        intro="The numbered 'How it works' cards. Numbering follows the order.",
    ),
    Resource(
        slug="stats", model=Stat, form=forms.StatForm,
        label="Statistic", plural="Statistics", icon="fa-chart-simple", group="Home page",
        columns=(Column("label", "Label", primary=True),
                 Column("number", "Number"),
                 Column("suffix", "Suffix"),
                 Column("value", "Text value"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("label", "value"),
        orderable=True,
        intro="The animated counter tiles in the about section.",
    ),
    Resource(
        slug="points", model=Point, form=forms.PointForm,
        label="Bullet point", plural="Bullet Points", icon="fa-list-check",
        group="Home page",
        columns=(Column("text", "Text", primary=True),
                 Column("group", "Section", "choice"),
                 Column("icon", "Icon"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("text",),
        filter_fields=("group",),
        orderable=True,
        intro="Tick-list bullets used in the about and enquiry sections.",
    ),
    Resource(
        slug="gallery", model=GalleryImage, form=forms.GalleryForm,
        label="Gallery image", plural="Gallery", icon="fa-images", group="Media & reviews",
        columns=(Column("image", "Photo", "image"),
                 Column("caption", "Caption", primary=True),
                 Column("category", "Category"),
                 Column("is_featured", "Home", "bool"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("caption", "category"),
        filter_fields=("category", "is_active", "is_featured"),
        orderable=True,
        intro="Photos for the gallery page; featured ones also appear on the home page.",
    ),
    Resource(
        slug="testimonials", model=Testimonial, form=forms.TestimonialForm,
        label="Testimonial", plural="Testimonials", icon="fa-star",
        group="Media & reviews",
        columns=(Column("customer_image", "Photo", "image"),
                 Column("customer_name", "Customer", primary=True),
                 Column("location", "Location"),
                 Column("rating", "Rating", "stars"),
                 Column("is_featured", "Home", "bool"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("customer_name", "location", "review_text"),
        filter_fields=("is_active", "is_featured", "rating"),
        orderable=True,
        intro="Customer reviews and star ratings.",
    ),
    Resource(
        slug="faqs", model=FAQ, form=forms.FAQForm,
        label="FAQ", plural="FAQs", icon="fa-circle-question",
        group="Media & reviews",
        columns=(Column("question", "Question", primary=True),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("question", "answer"),
        orderable=True,
        intro="Questions shown in the FAQ accordion.",
    ),
    Resource(
        slug="downloads", model=DownloadableFile, form=forms.DownloadForm,
        label="Download", plural="Downloads", icon="fa-file-arrow-down",
        group="Media & reviews",
        columns=(Column("title", "Title", primary=True),
                 Column("file", "File", "file"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("title", "description"),
        orderable=True,
        intro="Brochures, itineraries and price lists visitors can download.",
    ),
    Resource(
        slug="menu-items", model=MenuItem, form=forms.MenuItemForm,
        label="Menu item", plural="Menus & Navigation", icon="fa-bars",
        group="Navigation & contact",
        columns=(Column("label", "Label", primary=True),
                 Column("menu", "Menu", "choice"),
                 Column("page", "Page"),
                 Column("parent", "Nested under"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("label", "url"),
        filter_fields=("menu", "is_active"),
        orderable=True,
        intro="Header, footer and top-bar links. Reorder them with the arrows.",
    ),
    Resource(
        slug="contact-methods", model=ContactMethod, form=forms.ContactMethodForm,
        label="Contact method", plural="Contact Cards", icon="fa-address-card",
        group="Navigation & contact",
        columns=(Column("title", "Title", primary=True),
                 Column("value", "Value"),
                 Column("icon", "Icon"),
                 Column("is_active", "Shown", "bool"),
                 Column("order", "Pos")),
        search_fields=("title", "value"),
        orderable=True,
        intro="The contact cards shown on the contact page.",
    ),
]

RESOURCE_MAP = {r.slug: r for r in RESOURCES}

# Fixed (non-model) dashboard pages, appended to the sidebar.
EXTRA_LINKS = [
    ("Appearance", "fa-palette", [
        ("dashboard:text_blocks", "Text & Copy", "fa-font"),
        ("dashboard:images", "Section Images", "fa-image"),
    ]),
    ("Configuration", "fa-gear", [
        ("dashboard:settings", "Site Settings", "fa-sliders"),
        ("dashboard:media", "Media Library", "fa-folder-open"),
    ]),
]


def nav_sections():
    """Ordered sidebar structure: registry groups followed by fixed pages."""
    sections = []
    for resource in RESOURCES:
        if not sections or sections[-1]["title"] != resource.group:
            sections.append({"title": resource.group, "icon": resource.icon, "items": []})
        sections[-1]["items"].append({
            "label": resource.plural, "icon": resource.icon,
            "url_name": "dashboard:resource_list", "slug": resource.slug,
            "key": resource.slug,
        })
    for title, icon, links in EXTRA_LINKS:
        sections.append({
            "title": title, "icon": icon,
            "items": [{"label": label, "icon": link_icon, "url_name": name,
                       "slug": "", "key": name.split(":")[-1]}
                      for name, label, link_icon in links],
        })
    return sections
