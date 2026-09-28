import json
import re
from datetime import date
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    ContactMethod,
    DownloadableFile,
    FAQ,
    GalleryImage,
    HeroBadge,
    HeroSlide,
    Inquiry,
    Package,
    Point,
    Service,
    Stat,
    Step,
    Testimonial,
    TrustBadge,
)
from .site import site_settings


# Lead form rules — keep in sync with RULES in static/js/main.js
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{2,}$")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")

EMAIL_FAIL = "Sorry, we could not send the enquiry email. Please try WhatsApp."


def active(model):
    """QuerySet of published rows, in admin-defined order."""
    qs = model.objects.all()
    if hasattr(model, "is_active"):
        qs = qs.filter(is_active=True)
    return qs


def clean_phone(raw):
    """'+91 90000 00000' / '919000000000' / '9000000000' -> '9000000000'."""
    digits = re.sub(r"\D", "", str(raw or ""))

    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[2:]

    return digits


def clean_lead(data, today=None, require_trip=True):
    """Return (cleaned_fields, errors) for a lead payload.

    ``require_trip`` mirrors RULES in static/js/main.js: the consultation form
    always asks for trip details, the short contact form does not.
    """

    today = today or timezone.localdate()

    name = " ".join(str(data.get("full_name") or "").split())
    email = str(data.get("email") or "").strip().lower()
    phone = clean_phone(data.get("phone"))
    destination = " ".join(str(data.get("destination") or "").split())[:100]
    message = str(data.get("message") or "").strip()[:2000]

    raw_date = str(data.get("travel_date") or "").strip()
    raw_travelers = str(data.get("travelers") or "").strip()

    errors = {}

    if not email:
        errors["email"] = "Please enter your email address."
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = "Please enter a valid email address."

    if len(name) < 3:
        errors["full_name"] = "Full name must be at least 3 letters."
    elif not NAME_RE.match(name):
        errors["full_name"] = "Only letters, spaces and . ' - are allowed."

    if not phone:
        errors["phone"] = "Please enter your mobile number."
    elif len(phone) != 10:
        errors["phone"] = "Phone number must be exactly 10 digits (excluding +91)."
    elif not PHONE_RE.match(phone):
        errors["phone"] = "Enter a valid mobile number starting with 6, 7, 8 or 9."

    travel_date = None
    travelers = None

    if require_trip:
        if not destination:
            errors["destination"] = "Please select a destination."

        if not raw_date:
            errors["travel_date"] = "Please choose your travel date."
        else:
            try:
                travel_date = date.fromisoformat(raw_date)
            except ValueError:
                errors["travel_date"] = "Please choose a valid travel date."
            else:
                if travel_date < today:
                    errors["travel_date"] = "Travel date must be today or a future date."

        if not raw_travelers:
            errors["travelers"] = "Please enter the number of travelers."
        else:
            try:
                travelers = int(raw_travelers)
            except ValueError:
                travelers = None

            if travelers is None or travelers < 1:
                errors["travelers"] = "Please enter at least 1 traveler."
            elif travelers > 50:
                errors["travelers"] = "For more than 50 travelers, please contact us directly."
    else:
        travel_date = _safe_date(raw_date)
        travelers = _safe_int(raw_travelers)

    return {
        "full_name": name,
        "email": email,
        "phone": phone,
        "destination": destination,
        "travel_date": travel_date,
        "travelers": travelers,
        "message": message,
    }, errors


def _safe_date(raw):
    try:
        return date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def _safe_int(raw):
    try:
        return max(1, min(50, int(raw)))
    except (TypeError, ValueError):
        return 2


def base_context(extra=None):
    """Content shared by the home page and the standalone section pages."""
    packages = active(Package)
    context = {
        "destinations": list(
            packages.exclude(category="").values_list("category", flat=True).distinct()
        ),
        "today": timezone.localdate().isoformat(),
        "services": active(Service),
        "steps": active(Step),
        "stats": active(Stat),
        "hero_badges": active(HeroBadge),
        "trust_badges": active(TrustBadge),
        "about_points": active(Point).filter(group=Point.ABOUT),
        "consult_points": active(Point).filter(group=Point.CONSULT),
        "faqs": active(FAQ),
        "downloads": active(DownloadableFile),
        "contact_methods": active(ContactMethod),
    }
    context.update(extra or {})
    return context


def home(request):
    packages = active(Package).filter(is_popular=True)
    if not packages.exists():
        packages = active(Package)

    return render(request, "home.html", base_context({
        "packages": packages,
        "hero_slides": active(HeroSlide),
        "gallery": active(GalleryImage).filter(is_featured=True)[:8],
        "testimonials": active(Testimonial).filter(is_featured=True),
    }))


def packages(request):
    qs = active(Package)

    category = (request.GET.get("category") or "").strip()
    query = (request.GET.get("q") or "").strip()

    if category:
        qs = qs.filter(category=category)
    if query:
        qs = qs.filter(title__icontains=query) | qs.filter(short_description__icontains=query)

    return render(request, "packages.html", base_context({
        "packages": qs.distinct(),
        "categories": list(
            active(Package).exclude(category="")
            .values_list("category", flat=True).distinct()
        ),
        "selected_category": category,
        "query": query,
    }))


def package_detail(request, slug):
    package = get_object_or_404(active(Package), slug=slug)

    related = (active(Package)
               .filter(category=package.category, is_popular=True)
               .exclude(pk=package.pk)[:3])

    return render(request, "package_detail.html", base_context({
        "package": package,
        "related": related,
        "photos": package.images.all(),
    }))


def package_detail_json(request, slug):
    """JSON used by the home page's package popup."""
    return JsonResponse(get_object_or_404(active(Package), slug=slug).as_dict())


def gallery(request):
    images = active(GalleryImage)
    categories = list(images.exclude(category="")
                      .values_list("category", flat=True).distinct())

    selected = (request.GET.get("category") or "").strip()
    if selected and selected in categories:
        images = images.filter(category=selected)

    return render(request, "gallery.html", base_context({
        "gallery": images,
        "gallery_categories": categories,
        "selected_category": selected,
    }))


def about(request):
    return render(request, "about.html", base_context({
        "testimonials": active(Testimonial).filter(is_featured=True),
    }))


def faq(request):
    return render(request, "faq.html", base_context())


def contact(request):
    return render(request, "contact.html", base_context())


@require_POST
def inquiry_create(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        data = request.POST

    source = (data.get("source") or "website")[:40]
    require_trip = "contact" not in source.lower()

    cleaned, errors = clean_lead(data, require_trip=require_trip)

    if errors:
        return JsonResponse({
            "ok": False,
            "errors": errors,
            "error": " ".join(dict.fromkeys(errors.values())),
        }, status=400)

    inq = Inquiry(
        full_name=cleaned["full_name"],
        email=cleaned["email"],
        phone=cleaned["phone"],
        destination=cleaned["destination"],
        travelers=cleaned["travelers"] or 1,
        travel_date=cleaned["travel_date"],
        message=cleaned["message"],
        source=source,
    )
    inq.save()

    body = (
        f"New enquiry #{inq.pk}\n"
        f"Name: {inq.full_name}\n"
        f"Email: {inq.email}\n"
        f"Phone: +91 {inq.phone}\n"
        f"Destination: {inq.destination or '-'}\n"
        f"Travelers: {inq.travelers}\n"
        f"Date: {inq.travel_date or '-'}\n"
        f"Message: {inq.message or '-'}\n"
        f"Source: {inq.source}"
    )

    site = site_settings()
    notify_to = settings.LEAD_NOTIFY_EMAIL or site.email
    try:
        send_mail(
            f"New enquiry from {inq.full_name}",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [notify_to],
            fail_silently=True,
            reply_to=[inq.email],
        )
    except Exception:
        pass

    wa = f"https://wa.me/{site.phone_raw}?text={quote(body)}"

    return JsonResponse({
        "ok": True,
        "message": "Thank you! We'll contact you within an hour.",
        "whatsapp": wa,
    })
