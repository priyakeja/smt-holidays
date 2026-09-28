# SMT Holidays — dynamic Django travel website

Every piece of front-end content — headings, paragraphs, button labels, contact
details, menus, hero images, banners, packages, gallery photos, reviews, FAQs,
downloads — is stored in the database and edited from a secured dashboard at
`/dashboard/`. Nothing on the public site requires a code change or a redeploy.

## Run locally

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate          # creates tables and seeds the default content
python manage.py seed             # optional: 6 demo packages, gallery, reviews, FAQs
python manage.py createsuperuser  # the same account signs into /dashboard/
python manage.py runserver
```

Site: <http://127.0.0.1:8000/> · Dashboard: <http://127.0.0.1:8000/dashboard/>

## The dashboard

`/dashboard/` is staff-only. Anonymous visitors are redirected to the login page;
signed-in accounts without `is_staff` get a 403. Every create/edit/delete/reorder
action is a CSRF-protected POST. The Django admin at `/admin/` is still available
as a fallback.

| Area | What you can edit |
| --- | --- |
| **Enquiries** | View, filter, search, update status, keep internal notes, export CSV |
| **Packages** | Full CRUD, publish/hide, feature on the home page, extra photos, brochures |
| **Home page** | Hero slides, hero badges, trust badges, services, steps, statistics, bullet points |
| **Media & reviews** | Gallery photos (with home-page featuring), testimonials, FAQs, downloads |
| **Navigation** | Header / footer / top-bar links, nesting, ordering, show/hide |
| **Appearance** | All text & copy, section images, site settings |
| **Media library** | Every stored file, who uses it, one-click cleanup of unused files |

### WYSIWYG editing

Long-form prose (about text, the enquiry blurb, the SEO paragraph, package
overviews, reviews, FAQ answers, service and step descriptions) opens in a
TinyMCE rich-text editor, so you can add bold text, lists and links. Values are
output as HTML on the public site.

Short values — headings, button labels, page titles — stay as plain inputs, so
they can never pick up stray markup. The `{{ value|rich }}` filter escapes any
field that was typed as plain text but preserves its line breaks.

### Live previews

Uploading an image shows an immediate preview of the file you selected before you
save, next to the file currently on the server. The dashboard's setup checklist
also flags which section images are still missing.

### Automatic file cleanup

Replacing or deleting a package image, gallery photo, testimonial portrait, hero
slide, brochure or download removes the old file from `media/` automatically, so
storage never fills with orphaned uploads. A file shared by more than one record
is kept until the last reference is gone. `/dashboard/media/` lists files nothing
points at and clears them on request.

## How the content model works

Two complementary layers:

1. **Structured models** — `Package`, `PackageImage`, `GalleryImage`,
   `Testimonial`, `FAQ`, `Service`, `Step`, `Stat`, `Point`, `HeroSlide`,
   `HeroBadge`, `TrustBadge`, `MenuItem`, `ContactMethod`, `DownloadableFile`,
   `Inquiry` and the `SiteSettings` singleton.
2. **A copy registry** — `core/content.py` declares every one-off string and
   section image with a label, a group and a **default**. Values are stored in
   `SiteText` / `SiteImage`.

The registry is what makes the site self-healing: a text block with no stored row
falls back to its built-in default, and empty lists render a sensible empty state.
Add a new editable line by declaring it in `core/content.py` and using
`{{ TEXT.my_key }}` in a template — it appears in the dashboard automatically.

Adding a brand-new content type means one model, one entry in
`core/dashboard/registry.py`, and one form in `core/dashboard/forms.py`; the
generic CRUD views, list page, filters, reordering and delete confirmation are
generated from that registry.

## Pages

`/` · `/packages/` · `/packages/<slug>/` · `/gallery/` · `/about/` · `/faq/` ·
`/contact/` — each fully responsive and driven by the dashboard.

Menu links point at a *page key* (`home`, `packages`, …) rather than a raw URL, so
changing a route never leaves dead links behind. A custom URL can be used instead
for external links or anchors.

## JSON endpoints

* `GET /api/packages/<slug>/` — package details for the quick-view popup.
* `POST /api/inquiry/` — enquiry and contact form submissions.

Validation runs on both sides: `RULES` in `static/js/main.js` mirrors `clean_lead()`
in `core/views.py`. Keep the two in sync when changing the rules.

## Tests

```bash
python manage.py test core
```

58 tests cover page rendering, the empty-database fallback, menu resolution,
enquiry validation, dashboard access control, CRUD, reordering, CSV export,
rich-text handling and the automatic media cleanup.

## Production

```bash
export DEBUG=0
export SECRET_KEY=...
export ALLOWED_HOSTS=yourdomain.com
export CSRF_TRUSTED_ORIGINS=https://yourdomain.com
export DATABASE_URL=postgres://user:pass@host:5432/db
# Optional: SMTP plus a lead-notification address
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=... EMAIL_HOST_USER=... EMAIL_HOST_PASSWORD=...
export LEAD_NOTIFY_EMAIL=sales@yourdomain.com

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi
```

Business identity, phone, email, address and social links are edited in
**Dashboard → Site Settings** (not in `settings.py`). When `LEAD_NOTIFY_EMAIL` is
unset, new enquiries are emailed to the address in Site Settings.

Uploaded media needs persistent storage (or S3) in production.
