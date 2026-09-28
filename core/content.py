"""Registry of every editable text and image block on the public site.

Anything that is *not* part of a structured model (packages, gallery,
testimonials, services, ...) is declared here as a key with a label, a group
and a sensible default. The dashboard renders these as friendly grouped forms
and stores overrides in ``core.models.SiteText`` / ``core.models.SiteImage``.

Adding a new editable line of copy is therefore a one-line change: declare it
here, reference ``{{ TEXT.my_key }}`` in a template, and it shows up in the
dashboard automatically.
"""

from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TextDef:
    """One editable piece of copy.

    ``multiline`` renders a plain textarea; ``rich`` renders the WYSIWYG
    editor and the value is output as HTML on the public site.
    """

    key: str
    label: str
    group: str
    default: str = ""
    multiline: bool = False
    rich: bool = False
    help_text: str = ""
    optional: bool = False  # empty by design, so an empty default is correct


@dataclass(frozen=True)
class ImageDef:
    key: str
    label: str
    group: str
    default: str = ""  # path relative to MEDIA_ROOT
    help_text: str = ""


# --------------------------------------------------------------------------- #
# Text blocks                                                                  #
# --------------------------------------------------------------------------- #

TEXT_BLOCKS = [
    # --- brand / chrome -----------------------------------------------------
    TextDef("brand_text", "Brand name", "Brand & top bar", "SMT Holidays"),
    TextDef("topbar_location", "Top bar location", "Brand & top bar",
            "Sankarankovil, Tamil Nadu, India"),
    TextDef("topbar_quote_label", "Top bar button", "Brand & top bar", "Get Quote"),
    TextDef("nav_cta_label", "Header button label", "Brand & top bar", "Get Free Quote"),
    TextDef("nav_cta_url", "Header button link", "Brand & top bar", "contact"),
    TextDef("no_results_text", "Message when a list is empty", "Brand & top bar",
            "Nothing to show here yet."),

    # --- hero ---------------------------------------------------------------
    TextDef("hero_pill", "Hero badge text", "Home · Hero",
            "Sankarankovil \u2022 Tamil Nadu, India"),
    TextDef("hero_title", "Hero heading", "Home · Hero", "Best Tour & Travels in"),
    TextDef("hero_accent", "Hero heading – highlighted word", "Home · Hero", "Sankarankovil"),
    TextDef("hero_subtitle", "Hero paragraph", "Home · Hero",
            "Explore Tamil Nadu, Kerala, Ooty, Kodaikanal, Kanyakumari and "
            "customized holiday packages with SMT Holidays.", multiline=True),
    TextDef("hero_cta_label", "Hero main button", "Home · Hero", "Get Free Quote"),
    TextDef("hero_cta_url", "Hero main button link", "Home · Hero", "contact"),
    TextDef("hero_whatsapp_label", "Hero WhatsApp button", "Home · Hero", "WhatsApp Now"),
    TextDef("hero_secondary_label", "Hero secondary link", "Home · Hero", "Explore packages"),
    TextDef("hero_secondary_url", "Hero secondary link target", "Home · Hero", "packages"),

    # --- search -------------------------------------------------------------
    TextDef("search_destination_label", "Destination label", "Home · Search bar", "Destination"),
    TextDef("search_destination_placeholder", "Destination placeholder", "Home · Search bar", "Where to?"),
    TextDef("search_date_label", "Date label", "Home · Search bar", "Travel date"),
    TextDef("search_travelers_label", "Travelers label", "Home · Search bar", "Travelers"),
    TextDef("search_travelers_placeholder", "Travelers placeholder", "Home · Search bar", "Select travelers"),
    TextDef("search_button_label", "Search button", "Home · Search bar", "Search"),

    # --- rating -------------------------------------------------------------
    TextDef("rating_score", "Score", "Home · Rating card", "4.9"),
    TextDef("rating_text", "Caption", "Home · Rating card", "Google rated by 500+ travelers"),

    # --- about --------------------------------------------------------------
    TextDef("about_eyebrow", "Eyebrow", "About section", "About SMT Holidays"),
    TextDef("about_title", "Heading", "About section", "Your Trusted Travel Partner in South India"),
    TextDef("about_paragraph", "Paragraph", "About section",
            "SMT Holidays provides family tour packages, temple tours, honeymoon "
            "packages, group tours, corporate tours and customized holiday "
            "experiences across South India. We focus on comfort, safety and "
            "memorable travel experiences \u2014 every journey planned with care "
            "from Sankarankovil.", multiline=True, rich=True),
    TextDef("about_image_caption", "Image caption", "About section", "",
            optional=True),

    # --- how it works -------------------------------------------------------
    TextDef("how_title", "Heading", "How it works", "Plan your trip in 4 simple steps"),
    TextDef("how_subtitle", "Sub-heading", "How it works",
            "From first call to final memory, we make every step smooth and stress-free."),
    TextDef("how_cta_label", "Button label", "How it works", "Start Planning My Trip"),
    TextDef("how_cta_url", "Button link", "How it works", "contact"),

    # --- packages -----------------------------------------------------------
    TextDef("packages_eyebrow", "Eyebrow", "Packages", "Popular Tour Packages"),
    TextDef("packages_title", "Heading", "Packages", "Handpicked holidays across South India"),
    TextDef("packages_subtitle", "Sub-heading", "Packages",
            "Customizable, affordable and built for comfortable family travel."),
    TextDef("packages_empty", "Empty-state message", "Packages",
            "Add packages from the dashboard."),
    TextDef("packages_view_label", "Card button label", "Packages", "View Details"),
    TextDef("packages_price_prefix", "Price prefix", "Packages", "From \u20b9"),
    TextDef("packages_per_person", "Price note", "Packages", "per person onwards"),

    # --- why us -------------------------------------------------------------
    TextDef("why_eyebrow", "Eyebrow", "Why choose us", "Why choose us"),
    TextDef("why_title", "Heading", "Why choose us", "Travel with people who care"),

    # --- gallery ------------------------------------------------------------
    TextDef("gallery_title", "Heading", "Gallery", "Moments from our travelers"),
    TextDef("gallery_subtitle", "Sub-heading", "Gallery",
            "Family tours, temple journeys, hill stations and happy faces."),

    # --- testimonials -------------------------------------------------------
    TextDef("testimonials_title", "Heading", "Testimonials",
            "Loved by travelers across Tamil Nadu"),

    # --- consultation -------------------------------------------------------
    TextDef("consult_eyebrow", "Eyebrow", "Enquiry form", "Free consultation"),
    TextDef("consult_title", "Heading", "Enquiry form", "Plan Your Dream Vacation"),
    TextDef("consult_paragraph", "Paragraph", "Enquiry form",
            "Tell us where you want to go. We'll send a custom itinerary with "
            "transparent pricing \u2014 usually within an hour.", multiline=True, rich=True),
    TextDef("consult_submit_label", "Submit button", "Enquiry form",
            "Get Free Travel Consultation"),
    TextDef("consult_whatsapp_label", "WhatsApp button", "Enquiry form", "Chat on WhatsApp"),

    # --- faq ----------------------------------------------------------------
    TextDef("faq_eyebrow", "Eyebrow", "FAQ", "FAQ"),
    TextDef("faq_title", "Heading", "FAQ", "Frequently asked questions"),

    # --- SEO strip ----------------------------------------------------------
    TextDef("seo_heading", "Heading", "SEO / footer strip",
            "Best Travel Agency in Sankarankovil"),
    TextDef("seo_paragraph", "Paragraph", "SEO / footer strip",
            "SMT Holidays offers affordable family tours, temple tour packages, "
            "honeymoon packages and customized holiday trips from Sankarankovil, "
            "Tirunelveli, Tenkasi and surrounding regions. From short weekend "
            "getaways to full-circuit South India temple tours, we make planning "
            "simple and travel memorable for every kind of traveler.",
            multiline=True, rich=True),

    # --- footer -------------------------------------------------------------
    TextDef("footer_about", "Footer paragraph", "Footer",
            "Your trusted travel partner in Sankarankovil for family tours, temple "
            "tours and customized South India holidays.", multiline=True, rich=True),
    TextDef("footer_links_title", "Links column title", "Footer", "Quick Links"),
    TextDef("footer_contact_title", "Contact column title", "Footer", "Contact"),
    TextDef("footer_follow_title", "Social column title", "Footer", "Follow Us"),
    TextDef("footer_credit", "Bottom-right credit", "Footer",
            "Made with \u2665 in Sankarankovil, Tamil Nadu"),
    TextDef("footer_copyright", "Bottom-left copyright", "Footer",
            "\u00a9 {year} SMT Holidays. All rights reserved."),

    # --- contact page -------------------------------------------------------
    TextDef("contact_title", "Heading", "Contact page", "Get in touch with us"),
    TextDef("contact_subtitle", "Sub-heading", "Contact page",
            "Call, WhatsApp or send the form below \u2014 we usually reply within an hour."),
    TextDef("contact_success", "Success message", "Contact page",
            "Thank you! We'll contact you within an hour."),
    TextDef("contact_map_query", "Google Maps search text", "Contact page", "Sankarankovil, Tamil Nadu"),
]

TEXT_BY_KEY = {b.key: b for b in TEXT_BLOCKS}

TEXT_GROUPS: "OrderedDict[str, list[TextDef]]" = OrderedDict()
for _block in TEXT_BLOCKS:
    TEXT_GROUPS.setdefault(_block.group, []).append(_block)


# --------------------------------------------------------------------------- #
# Image blocks                                                                 #
# --------------------------------------------------------------------------- #

IMAGE_BLOCKS = [
    ImageDef("hero_bg", "Home hero background", "Home", "packages/kanyakumari.jpg",
             "Shown behind the hero heading until you add hero slides."),
    ImageDef("about_image", "About section image", "Home", "",
             "Optional. Leave empty to hide the image column."),
    ImageDef("cta_bg", "Enquiry section background", "Home", "",
             "Optional background image behind the enquiry form panel."),
    ImageDef("packages_banner", "Packages page banner", "Page banners", "",
             "Optional banner behind the packages page heading."),
    ImageDef("gallery_banner", "Gallery page banner", "Page banners", ""),
    ImageDef("about_banner", "About page banner", "Page banners", ""),
    ImageDef("contact_banner", "Contact page banner", "Page banners", ""),
    ImageDef("faq_banner", "FAQ page banner", "Page banners", ""),
]

IMAGE_BY_KEY = {b.key: b for b in IMAGE_BLOCKS}

IMAGE_GROUPS: "OrderedDict[str, list[ImageDef]]" = OrderedDict()
for _block in IMAGE_BLOCKS:
    IMAGE_GROUPS.setdefault(_block.group, []).append(_block)

IMAGE_GROUP_CHOICES = [(g, g) for g in IMAGE_GROUPS]


def known_text_keys():
    return set(TEXT_BY_KEY)


def known_image_keys():
    return set(IMAGE_BY_KEY)
