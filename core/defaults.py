"""Plain-data defaults used to seed a brand-new database.

Kept dependency-free (no Django imports) so it is safe to import from both the
``seed_content`` management command and the ``0004_seed_defaults`` data
migration. Every list here mirrors the original hand-written markup, so a fresh
install renders exactly like the original site until an admin changes it.
"""

# (label, page key, custom url, icon, order)
MENU_ITEMS = {
    "header": [
        ("Home", "home", "", "fa-solid fa-house", 0),
        ("Packages", "packages", "", "fa-solid fa-suitcase-rolling", 1),
        ("Gallery", "gallery", "", "fa-solid fa-images", 2),
        ("About", "about", "", "fa-solid fa-circle-info", 3),
        ("FAQ", "faq", "", "fa-solid fa-circle-question", 4),
        ("Contact", "contact", "", "fa-solid fa-envelope", 5),
    ],
    "footer": [
        ("About Us", "about", "", "", 0),
        ("Tour Packages", "packages", "", "", 1),
        ("Gallery", "gallery", "", "", 2),
        ("FAQ", "faq", "", "", 3),
    ],
    "topbar": [],
}

HERO_BADGES = [
    ("fa-solid fa-users", "1000+ Happy Travelers"),
    ("fa-solid fa-tags", "Affordable Packages"),
    ("fa-solid fa-shield-heart", "Safe & Comfortable"),
    ("fa-solid fa-headset", "24/7 Support"),
]

TRUST_BADGES = [
    ("fa-solid fa-circle-check", "Trusted Local Agency"),
    ("fa-solid fa-circle-check", "Govt Registered"),
    ("fa-solid fa-circle-check", "Since 2015"),
]

SERVICES = [
    ("fa-solid fa-van-shuttle", "Comfortable Vehicles",
     "Clean, well-maintained AC cars, tempo travellers and coaches for every group size."),
    ("fa-solid fa-user-tie", "Experienced Drivers",
     "Local drivers who know the routes, viewpoints and best places to stop."),
    ("fa-solid fa-wand-magic-sparkles", "Customized Itineraries",
     "Family-friendly, honeymoon or temple \u2014 built around your dates and budget."),
    ("fa-solid fa-headset", "24/7 Customer Support",
     "Real humans, real-time help \u2014 before, during and after your trip."),
]

STEPS = [
    ("fa-regular fa-clipboard", "Share Your Plan", "Tell us your destination, dates and travelers."),
    ("fa-solid fa-file-invoice", "Get Custom Quote", "Receive a tailored itinerary with transparent pricing."),
    ("fa-regular fa-calendar-check", "Confirm Booking", "Pay a small advance to lock your dates and hotels."),
    ("fa-solid fa-plane-departure", "Enjoy Your Trip", "Travel comfortably with 24/7 on-trip support."),
]

# (number, suffix, value, label)
STATS = [
    (1000, "+", "", "Happy Travelers"),
    (6, "+", "", "Destinations"),
    (None, "", "24/7", "Customer Support"),
    (10, "+", "", "Years of Trust"),
]

# (group, icon, text)
POINTS = [
    ("about", "fa-solid fa-heart", "Family-first travel planning with personal attention"),
    ("about", "fa-solid fa-map-location-dot", "Curated itineraries across Tamil Nadu & Kerala"),
    ("about", "fa-solid fa-headset", "Dedicated support before, during and after your trip"),
    ("consult", "fa-regular fa-circle-check", "No advance to get a quote"),
    ("consult", "fa-regular fa-circle-check", "Flexible dates & group sizes"),
    ("consult", "fa-regular fa-circle-check", "24/7 WhatsApp support"),
]

# (icon, title, value, link)
CONTACT_METHODS = [
    ("fa-solid fa-phone", "Call us", "{phone_display}", "tel:+{phone}"),
    ("fa-regular fa-envelope", "Email us", "{email}", "mailto:{email}"),
    ("fa-brands fa-whatsapp", "WhatsApp", "Chat with us instantly", "https://wa.me/{phone}"),
    ("fa-solid fa-location-dot", "Visit us", "Sankarankovil, Tamil Nadu", "{maps}"),
]
