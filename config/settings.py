import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "jazzmin",  # must precede django.contrib.admin
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.site_info",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

# SQLite for development; set DATABASE_URL=postgres://user:pass@host/db for production
import dj_database_url
DATABASES = {"default": dj_database_url.config(
    default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600)}

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Business identity, contact details, logos, social links and SEO defaults are
# all managed in the dashboard (Dashboard -> Site Settings) and stored in the
# SiteSettings model. Only the outgoing mail configuration lives here.

# Lead notifications: console in dev; set SMTP env vars in production
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "hello@smtholidays.in")
# Optional override. When empty, new enquiries go to the address in Site Settings.
LEAD_NOTIFY_EMAIL = os.environ.get("LEAD_NOTIFY_EMAIL", "")

JAZZMIN_SETTINGS = {
    "site_title": "SMT Holidays Admin", "site_header": "SMT Holidays", "site_brand": "SMT Holidays",
    "welcome_sign": "Manage your travel website", "copyright": "SMT Holidays",
    "search_model": ["core.Package", "core.Inquiry"],
    "topmenu_links": [{"name": "View Website", "url": "/", "new_window": True}],
    "icons": {"core.Package": "fas fa-suitcase-rolling", "core.GalleryImage": "fas fa-images",
              "core.Testimonial": "fas fa-star", "core.Inquiry": "fas fa-inbox",
              "core.FAQ": "fas fa-question-circle", "core.MenuItem": "fas fa-bars",
              "core.HeroSlide": "fas fa-panorama", "core.Service": "fas fa-hand-holding-heart",
              "core.SiteSettings": "fas fa-sliders", "core.SiteText": "fas fa-font",
              "core.SiteImage": "fas fa-image", "core.DownloadableFile": "fas fa-file-arrow-down",
              "auth.User": "fas fa-user"},
    "order_with_respect_to": ["core.Inquiry", "core.Package", "core.GalleryImage",
                              "core.Testimonial", "core.FAQ", "core.MenuItem"],
}
JAZZMIN_UI_TWEAKS = {"navbar": "navbar-dark", "sidebar": "sidebar-dark-info", "brand_colour": "navbar-info",
                     "accent": "accent-warning", "theme": "flatly"}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
