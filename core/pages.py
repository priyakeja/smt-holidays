"""Registry of the public pages of the site.

Menu items stored in the database point at a *page key* rather than a raw URL
wherever possible, so that changing a route never leaves dead links behind.
Add a page here (and a matching URL name in ``core/urls.py``) and it becomes
selectable in the dashboard menu editor automatically.
"""

# (url-name, label, description)
PAGES = [
    ("home", "Home", "Hero, search, packages, gallery and reviews"),
    ("packages", "Tour Packages", "Grid of all published packages"),
    ("gallery", "Gallery", "Photo gallery, grouped by category"),
    ("about", "About Us", "Company story, stats and why-us section"),
    ("faq", "FAQ", "Frequently asked questions"),
    ("contact", "Contact", "Enquiry form and contact details"),
]

PAGE_CHOICES = [(name, label) for name, label, _ in PAGES]

PAGE_HELP = (
    "Pick a page of this website, or leave blank and type a full link below "
    "(for example https://wa.me/919000000000 or #gallery)."
)
