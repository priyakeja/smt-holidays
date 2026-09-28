import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import FAQ, GalleryImage, Package, Testimonial
from core.seeding import seed_content

# Every source image lives in the project's `images/` folder. `seed` copies
# them into MEDIA_ROOT under the file names the models expect.
SRC_DIR = Path(settings.BASE_DIR) / "images"
MEDIA_DIR = Path(settings.MEDIA_ROOT)

PKGS = [
    {
        "title": "Ooty Tour Package", "duration": "3D/2N", "price": 6999, "category": "Ooty",
        "short": "Tea gardens, Doddabetta peak, boat ride at Ooty Lake.",
        "src": "ooty img.jpg", "image": "ooty.jpg",
        "highlights": ["Ooty Lake boating", "Doddabetta peak view", "Botanical Gardens", "Tea estate visit"],
        "inclusions": ["AC vehicle", "Hotel stay (2 nights)", "Daily breakfast", "Sightseeing"],
    },
    {
        "title": "Kodaikanal Tour Package", "duration": "3D/2N", "price": 6499, "category": "Kodaikanal",
        "short": "Princess of hill stations — lakes, viewpoints and pine forests.",
        "src": "kodaikanal img.jpg", "image": "kodaikanal.jpg",
        "highlights": ["Kodai Lake", "Coaker's Walk", "Pillar Rocks", "Bryant Park"],
        "inclusions": ["AC vehicle", "Hotel stay (2 nights)", "Daily breakfast", "Sightseeing"],
    },
    {
        "title": "Kerala Tour Package", "duration": "5D/4N", "price": 14999, "category": "Kerala",
        "short": "Munnar hills, Alleppey houseboat and Kochi heritage.",
        "src": "kerala img.jpg", "image": "kerala.jpg",
        "highlights": ["Munnar tea valleys", "Alleppey houseboat", "Kochi Fort", "Spice plantations"],
        "inclusions": ["AC vehicle", "Houseboat stay", "Resort stay", "Breakfast & dinner"],
    },
    {
        "title": "Kanyakumari Tour Package", "duration": "2D/1N", "price": 4999, "category": "Kanyakumari",
        "short": "Sunrise at land's end with Vivekananda Rock and Thiruvalluvar statue.",
        "src": "kanyakumari img.jpg", "image": "kanyakumari.jpg",
        "highlights": ["Sunrise point", "Vivekananda Rock", "Thiruvalluvar statue", "Padmanabhapuram Palace"],
        "inclusions": ["AC vehicle", "Hotel stay", "Daily breakfast", "Sightseeing"],
    },
    {
        "title": "Tirupati Temple Tour", "duration": "2D/1N", "price": 5499, "category": "Tirupati",
        "short": "Darshan at Sri Venkateswara Temple with comfortable transport.",
        "src": "tirupathi img.jpg", "image": "tirupati.jpg",
        "highlights": ["Tirumala darshan", "Padmavathi temple", "Pilgrim assistance", "Local meals"],
        "inclusions": ["AC vehicle", "Hotel stay", "Darshan assistance", "Daily breakfast"],
    },
    {
        "title": "South India Temple Tour", "duration": "6D/5N", "price": 17999, "category": "Temple Circuit",
        "short": "Madurai, Rameswaram, Kanyakumari, Trivandrum temple circuit.",
        "src": "south india temple img.jpg", "image": "south-india-temple.jpg",
        "highlights": ["Meenakshi temple", "Rameswaram Jyotirlinga", "Kanyakumari", "Padmanabhaswamy"],
        "inclusions": ["AC vehicle", "Hotel stays", "All breakfasts", "Pilgrim guide"],
    },
]

GALLERY = [
    ("travel img1.jpg", "travel-1.jpg", "Family tour group", "Group Tours"),
    ("travel img 2.jpg", "travel-2.jpg", "Hill station morning", "Hill Stations"),
    ("travel img 3.jpg", "travel-3.jpg", "Backwater cruise", "Kerala"),
    ("travel img 4.jpg", "travel-4.jpg", "Beach sunset memories", "Kanyakumari"),
    ("travel img 5.jpg", "travel-5.jpg", "Ooty tea gardens", "Ooty"),
    ("travel img 6.jpg", "travel-6.jpg", "Alleppey houseboat", "Kerala"),
    ("travel img 7.jpg", "travel-7.jpg", "Sunrise at land's end", "Kanyakumari"),
    ("travel img 8.jpg", "travel-8.jpg", "Temple gopuram", "Temple Tours"),
]

REVIEWS = [
    ("Senthil Kumar", "Tirunelveli", "senthil img.jpg", "senthil.jpg",
     "Booked the Kerala family package with SMT Holidays — comfortable vehicle, great driver and a perfectly planned houseboat stay. Highly recommended!"),
    ("Priya Lakshmi", "Sankarankovil", "priya img.jpg", "priya.jpg",
     "Our Ooty trip was wonderful. Affordable price, neat hotel and the team was responsive even at midnight. Will book again."),
    ("Murugan R.", "Tenkasi", "murugan img.jpg", "murugan.jpg",
     "Did the South India temple tour with my parents. Smooth darshan assistance and very respectful staff. Truly stress-free pilgrimage."),
]

FAQS = [
    ("Which destinations do you cover?", "We cover Ooty, Kodaikanal, Kerala, Kanyakumari, Tirupati, Rameswaram, Madurai and other Tamil Nadu & Kerala destinations, plus custom routes."),
    ("Do you provide customized packages?", "Yes. Every package is customizable — tell us your dates, group size and budget and we will prepare a tailored itinerary."),
    ("Do you arrange hotel bookings?", "Yes. Hotels, resorts and houseboat stays are included in our packages, matched to your budget and comfort level."),
    ("Do you provide transportation?", "All packages include clean, well-maintained AC vehicles with experienced local drivers, starting from Sankarankovil."),
    ("How can I get a quotation?", "Fill in the free consultation form or message us on WhatsApp. You will receive a transparent quote usually within an hour."),
]


class Command(BaseCommand):
    help = "Copy images from images/ into media/ and load SMT Holidays sample content"

    def _place(self, src_name, sub, dest_name):
        """Copy images/<src_name> to media/<sub>/<dest_name>. Returns the media-relative path."""
        src = SRC_DIR / src_name
        dest_dir = MEDIA_DIR / sub
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / dest_name
        rel = f"{sub}/{dest_name}"
        if not src.exists():
            self.stderr.write(self.style.WARNING(f"  ! missing source image: images/{src_name}"))
            return rel
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(src, dest)
            self.stdout.write(f"  + {rel}  <-  images/{src_name}")
        return rel

    def handle(self, *a, **kw):
        for i, p in enumerate(PKGS):
            image = self._place(p["src"], "packages", p["image"])
            Package.objects.update_or_create(title=p["title"], defaults=dict(
                duration=p["duration"], starting_price=p["price"], category=p["category"],
                short_description=p["short"], order=i, main_image=image,
                overview=(f"<p>{p['short']}</p>"
                          "<p>This itinerary is fully customizable \u2014 tell us your dates, "
                          "group size and budget and we will tailor it for you. All packages "
                          "start from Sankarankovil with an experienced local driver.</p>"),
                highlights="\n".join(p["highlights"]), inclusions="\n".join(p["inclusions"]),
                is_popular=True, is_active=True))

        gallery_paths = []
        for i, (src_name, dest_name, caption, category) in enumerate(GALLERY):
            image = self._place(src_name, "gallery", dest_name)
            gallery_paths.append(image)
            GalleryImage.objects.update_or_create(image=image, defaults=dict(
                caption=caption, category=category, order=i))
        # Drop gallery rows left over from earlier seeds so the grid stays deterministic.
        GalleryImage.objects.exclude(image__in=gallery_paths).delete()

        for name, location, src_name, dest_name, review in REVIEWS:
            image = self._place(src_name, "testimonials", dest_name)
            Testimonial.objects.update_or_create(customer_name=name, defaults=dict(
                location=location, review_text=review, rating=5, customer_image=image, is_active=True))

        for i, (question, answer) in enumerate(FAQS):
            FAQ.objects.update_or_create(question=question, defaults=dict(answer=answer, order=i))

        # Menus, hero badges, services, steps, statistics and contact cards.
        seed_content(verbose=True)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Package.objects.count()} packages, {GalleryImage.objects.count()} gallery images, "
            f"{Testimonial.objects.count()} testimonials, {FAQ.objects.count()} FAQs, "
            f"{GalleryImage.objects.count()} gallery photos."))
