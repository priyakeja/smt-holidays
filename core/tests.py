"""Tests for the dynamic website and the admin dashboard."""

import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import content, defaults
from .models import (
    ContactMethod,
    FAQ,
    GalleryImage,
    HeroSlide,
    Inquiry,
    MenuItem,
    Package,
    SiteImage,
    SiteSettings,
    SiteText,
    Testimonial,
)
from .site import resolve_link, text_map

User = get_user_model()

# A minimal valid 1x1 GIF, so ImageField validation passes without Pillow work.
GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
       b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


def gif(name="test.gif"):
    return SimpleUploadedFile(name, GIF, content_type="image/gif")


class MediaRootMixin:
    """Give each test an isolated MEDIA_ROOT so file cleanup is observable."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="smt-test-media-")
        cls._override = override_settings(MEDIA_ROOT=cls._media)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)


class PageContentMixin:
    """Publish one of each section so the public pages render fully."""

    def publish_content(self):
        package = Package.objects.create(
            title="Ooty Tour Package", duration="3D/2N", starting_price=6999,
            category="Ooty", short_description="Tea gardens and boat rides.",
            main_image=gif(), highlights="Lake\nPeak", inclusions="Car\nHotel",
            is_popular=True, is_active=True,
        )
        GalleryImage.objects.create(image=gif(), caption="Happy group",
                                    category="Group Tours", is_featured=True)
        Testimonial.objects.create(customer_name="Priya", location="Tenkasi",
                                   rating=5, review_text="Wonderful trip.",
                                   is_featured=True)
        FAQ.objects.create(question="Do you customise?", answer="Yes, always.")
        HeroSlide.objects.create(image=gif(), title="Explore South India",
                                 is_active=True)
        return package


# --------------------------------------------------------------------------- #
# Public site                                                                  #
# --------------------------------------------------------------------------- #

class PublicPagesTests(PageContentMixin, MediaRootMixin, TestCase):

    def setUp(self):
        self.package = self.publish_content()

    def test_every_public_page_renders(self):
        urls = [reverse("home"), reverse("packages"), reverse("gallery"),
                reverse("about"), reverse("faq"), reverse("contact"),
                self.package.get_absolute_url()]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_pages_render_with_no_content_at_all(self):
        """The site must not break on a completely empty database."""
        Package.objects.all().delete()
        GalleryImage.objects.all().delete()
        Testimonial.objects.all().delete()
        FAQ.objects.all().delete()
        HeroSlide.objects.all().delete()
        MenuItem.objects.all().delete()

        for url in [reverse("home"), reverse("packages"), reverse("gallery"),
                    reverse("about"), reverse("faq"), reverse("contact")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                # Built-in copy from content.py is used when nothing is stored.
                self.assertContains(response, "SMT Holidays")

    def test_home_uses_builtin_text_defaults(self):
        """With nothing stored, the copy from content.py is what renders."""
        response = self.client.get(reverse("home"))
        self.assertContains(response, content.TEXT_BY_KEY["packages_title"].default)

    def test_hero_falls_back_to_the_default_heading_without_slides(self):
        HeroSlide.objects.all().delete()
        response = self.client.get(reverse("home"))
        # Django escapes the ampersand in "Best Tour & Travels in".
        self.assertContains(response, "Best Tour &amp; Travels in")

    def test_a_slide_heading_replaces_the_default(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Explore South India")
        self.assertNotContains(response, "Best Tour &amp; Travels in")

    def test_saved_text_block_overrides_the_default(self):
        SiteText.objects.create(key="packages_title", value="Adventures start here")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Adventures start here")
        self.assertNotContains(response, content.TEXT_BY_KEY["packages_title"].default)

    def test_blank_field_override_removes_the_text(self):
        """Clearing a field in the dashboard must clear it on the site too."""
        SiteText.objects.create(key="packages_title", value="")
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, content.TEXT_BY_KEY["packages_title"].default)

    def test_package_detail_page_shows_the_package(self):
        response = self.client.get(self.package.get_absolute_url())
        self.assertContains(response, "Ooty Tour Package")
        self.assertContains(response, "Tea gardens and boat rides.")

    def test_unpublished_package_is_hidden(self):
        self.package.is_active = False
        self.package.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(self.package.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(f"/api/packages/{self.package.slug}/").status_code, 404)

    def test_gallery_category_filter(self):
        GalleryImage.objects.create(image=gif(), caption="Temple photo", category="Temple Tours")
        response = self.client.get(reverse("gallery"), {"category": "Temple Tours"})
        self.assertContains(response, "Temple photo")
        self.assertNotContains(response, "Happy group")

    def test_menu_items_render_in_the_header(self):
        MenuItem.objects.create(menu=MenuItem.HEADER, label="Special Offers",
                                page="packages", order=1)
        self.assertContains(self.client.get(reverse("home")), "Special Offers")

    def test_hidden_menu_item_is_not_rendered(self):
        MenuItem.objects.create(menu=MenuItem.HEADER, label="Secret Page",
                                page="packages", is_active=False)
        self.assertNotContains(self.client.get(reverse("home")), "Secret Page")

    def test_meta_description_comes_from_settings(self):
        settings_obj = SiteSettings.load()
        settings_obj.meta_description = "Award winning travel agency."
        settings_obj.save()
        self.assertContains(self.client.get(reverse("home")), "Award winning travel agency.")


class LinkResolutionTests(TestCase):

    def test_page_keys_resolve_to_urls(self):
        self.assertEqual(resolve_link("contact"), reverse("contact"))
        self.assertEqual(resolve_link("home"), reverse("home"))

    def test_external_and_anchor_links_pass_through(self):
        for raw in ["https://wa.me/91", "tel:+919000000000", "#enquiry", "/custom/"]:
            self.assertEqual(resolve_link(raw), raw)

    def test_menu_item_url_uses_the_page_choice(self):
        item = MenuItem.objects.create(label="Contact", page="contact", url="/ignored/")
        self.assertEqual(item.get_url(), reverse("contact"))

    def test_menu_item_falls_back_to_the_custom_url(self):
        item = MenuItem.objects.create(label="Blog", url="https://example.com/blog")
        self.assertEqual(item.get_url(), "https://example.com/blog")
        self.assertTrue(item.is_external)

    def test_contact_card_maps_placeholder_uses_the_site_maps_url(self):
        site = SiteSettings.load()
        site.maps_url = "https://maps.google.com/?q=Ooty"
        site.save()
        card = ContactMethod.objects.create(
            title="Visit us", value="Ooty, Tamil Nadu", link="{maps}")
        self.assertEqual(card.get_link(), site.maps_url)

    def test_seeded_visit_card_links_to_the_map(self):
        """The 'Visit us' card must be a link, not plain text."""
        from .seeding import seed_content

        seed_content()
        card = ContactMethod.objects.get(title="Visit us")
        self.assertTrue(card.get_link().startswith("http"))


# --------------------------------------------------------------------------- #
# Enquiries                                                                    #
# --------------------------------------------------------------------------- #

class EnquiryApiTests(TestCase):

    def payload(self, **overrides):
        data = {
            "full_name": "Senthil Kumar",
            "email": "senthil@example.com",
            "phone": "9000000000",
            "destination": "Ooty",
            "travelers": 4,
            "travel_date": (timezone.localdate() + timedelta(days=20)).isoformat(),
            "source": "consultation form",
        }
        data.update(overrides)
        return data

    def test_valid_enquiry_is_stored(self):
        response = self.client.post("/api/inquiry/", self.payload(),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(Inquiry.objects.count(), 1)
        self.assertEqual(Inquiry.objects.first().status, Inquiry.NEW)

    def test_phone_number_is_normalised(self):
        self.client.post("/api/inquiry/", self.payload(phone="+91 90000 00000"),
                         content_type="application/json")
        self.assertEqual(Inquiry.objects.first().phone, "9000000000")

    def test_invalid_enquiry_returns_field_errors(self):
        response = self.client.post(
            "/api/inquiry/",
            self.payload(email="nope", phone="123"),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("email", body["errors"])
        self.assertIn("phone", body["errors"])
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_past_travel_date_is_rejected(self):
        response = self.client.post(
            "/api/inquiry/",
            self.payload(travel_date=(timezone.localdate() - timedelta(days=1)).isoformat()),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("travel_date", response.json()["errors"])

    def test_contact_form_does_not_require_trip_details(self):
        response = self.client.post("/api/inquiry/", {
            "full_name": "Priya Lakshmi",
            "email": "priya@example.com",
            "phone": "9123456789",
            "message": "Please call me about a honeymoon package.",
            "source": "contact form",
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.message, "Please call me about a honeymoon package.")
        self.assertIsNone(inquiry.travel_date)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get("/api/inquiry/").status_code, 405)


# --------------------------------------------------------------------------- #
# Dashboard access                                                             #
# --------------------------------------------------------------------------- #

class DashboardAccessTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user("editor", password="pw", is_staff=True)
        self.member = User.objects.create_user("visitor", password="pw")

    def test_anonymous_users_are_sent_to_the_login_page(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("dashboard:login"), response["Location"])

    def test_non_staff_users_are_refused(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboard:settings")).status_code, 403)

    def test_staff_users_get_in(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)

    def test_non_staff_cannot_log_in_through_the_dashboard_form(self):
        response = self.client.post(reverse("dashboard:login"),
                                    {"username": "visitor", "password": "pw"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have dashboard access")

    def test_sign_out_ends_the_session(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse("dashboard:logout")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class DashboardRouteTests(TestCase):
    """Every resource in the registry must render its list and add form."""

    def setUp(self):
        self.staff = User.objects.create_user("editor", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_all_registered_resources_render(self):
        from .dashboard.registry import RESOURCES

        for resource in RESOURCES:
            for name in ("resource_list", "resource_create"):
                url = reverse(f"dashboard:{name}", args=[resource.slug])
                with self.subTest(resource=resource.slug, view=name):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_fixed_pages_render(self):
        for name in ("index", "text_blocks", "images", "settings", "media"):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(f"dashboard:{name}")).status_code, 200)

    def test_unknown_resource_is_a_404(self):
        self.assertEqual(self.client.get("/dashboard/not-a-thing/").status_code, 404)

    def test_editor_page_is_not_indexable(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertContains(response, "noindex")


# --------------------------------------------------------------------------- #
# Dashboard CRUD                                                               #
# --------------------------------------------------------------------------- #

class DashboardCrudTests(MediaRootMixin, TestCase):

    def setUp(self):
        self.staff = User.objects.create_user("editor", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_create_a_package(self):
        response = self.client.post(reverse("dashboard:resource_create", args=["packages"]), {
            "title": "Kodaikanal Weekend",
            "slug": "",
            "category": "Kodaikanal",
            "duration": "3D/2N",
            "badge": "",
            "short_description": "Lakes, viewpoints and pine forests.",
            "overview": "<p>Lovely hills.</p>",
            "starting_price": "7499",
            "main_image": gif(),
            "highlights": "Kodai Lake",
            "inclusions": "AC vehicle",
            "exclusions": "",
            "seo_title": "",
            "seo_description": "",
            "is_popular": "on",
            "is_active": "on",
            "order": "0",
        })
        self.assertEqual(response.status_code, 302)
        package = Package.objects.get()
        self.assertEqual(package.slug, "kodaikanal-weekend")
        self.assertTrue(package.is_active)

    def test_edit_updates_existing_content(self):
        package = Package.objects.create(
            title="Ooty", duration="2D/1N", starting_price=5000,
            short_description="Short", main_image=gif(),
            highlights="A", inclusions="B")

        self.client.post(reverse("dashboard:resource_update", args=["packages", package.pk]), {
            "title": "Ooty Deluxe",
            "slug": package.slug,
            "category": "Ooty",
            "duration": "3D/2N",
            "badge": "",
            "short_description": "Longer stay",
            "overview": "",
            "starting_price": "5500",
            "highlights": "A\nB",
            "inclusions": "B",
            "exclusions": "",
            "seo_title": "",
            "seo_description": "",
            "is_active": "on",
            "order": "0",
        })

        package.refresh_from_db()
        self.assertEqual(package.title, "Ooty Deluxe")
        self.assertEqual(package.starting_price, 5500)

    def test_invalid_submission_shows_errors(self):
        response = self.client.post(reverse("dashboard:resource_create", args=["packages"]),
                                    {"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Package.objects.count(), 0)

    def test_visibility_toggle(self):
        package = Package.objects.create(
            title="Ooty", duration="2D/1N", starting_price=5000,
            short_description="Short", main_image=gif(),
            highlights="A", inclusions="B", is_active=True)

        self.client.post(reverse("dashboard:resource_toggle", args=["packages", package.pk]))
        package.refresh_from_db()
        self.assertFalse(package.is_active)

    def test_reordering_swaps_positions(self):
        first = FAQ.objects.create(question="First", answer="a", order=0)
        second = FAQ.objects.create(question="Second", answer="b", order=1)

        self.client.post(reverse("dashboard:resource_move", args=["faqs", second.pk]),
                         {"direction": "up"})

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(second.order, 0)
        self.assertEqual(first.order, 1)

    def test_delete_removes_the_record(self):
        faq = FAQ.objects.create(question="Temp", answer="a")
        response = self.client.post(
            reverse("dashboard:resource_delete", args=["faqs", faq.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FAQ.objects.exists())

    def test_delete_page_warns_before_deleting(self):
        faq = FAQ.objects.create(question="Temp", answer="a")
        response = self.client.get(reverse("dashboard:resource_delete", args=["faqs", faq.pk]))
        self.assertContains(response, "cannot be undone")

    def test_enquiry_csv_export(self):
        Inquiry.objects.create(full_name="Senthil", email="s@example.com",
                               phone="9000000000", destination="Ooty")
        response = self.client.get(reverse("dashboard:resource_export", args=["inquiries"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Senthil", response.content.decode())

    def test_enquiry_detail_marks_it_as_read(self):
        inquiry = Inquiry.objects.create(full_name="Senthil", email="s@example.com",
                                         phone="9000000000")
        self.client.get(reverse("dashboard:inquiry_detail", args=[inquiry.pk]))
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, Inquiry.READ)


class DashboardEditorTests(MediaRootMixin, TestCase):

    def setUp(self):
        self.staff = User.objects.create_user("editor", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_saving_copy_persists_every_block(self):
        payload = {block.key: f"Custom {block.key}" for block in content.TEXT_BLOCKS}
        response = self.client.post(reverse("dashboard:text_blocks"), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SiteText.objects.count(), len(content.TEXT_BLOCKS))
        self.assertEqual(SiteText.objects.get(key="hero_title").value, "Custom hero_title")

    def test_uploading_a_section_image(self):
        self.client.post(reverse("dashboard:images"), {
            "image_hero_bg": gif(),
            "alt_hero_bg": "Sunrise over the hills",
        })
        row = SiteImage.objects.get(key="hero_bg")
        self.assertTrue(row.image.name)
        self.assertEqual(row.alt_text, "Sunrise over the hills")

    def test_clearing_a_section_image_removes_the_file(self):
        import os

        self.client.post(reverse("dashboard:images"), {"image_hero_bg": gif()})
        path = SiteImage.objects.get(key="hero_bg").image.path
        self.assertTrue(os.path.exists(path))

        self.client.post(reverse("dashboard:images"), {"clear_hero_bg": "on"})
        self.assertFalse(os.path.exists(path))
        self.assertFalse(SiteImage.objects.get(key="hero_bg").image)

    def test_site_settings_round_trip(self):
        response = self.client.post(reverse("dashboard:settings"), {
            "site_name": "SMT Holidays",
            "brand_mark": "S",
            "tagline": "South India specialists",
            "phone_display": "+91 91234 56789",
            "phone_raw": "919123456789",
            "email": "new@smtholidays.in",
            "address": "Sankarankovil",
            "instagram_url": "",
            "facebook_url": "",
            "youtube_url": "",
            "maps_url": "",
            "meta_title": "Best travel agency",
            "meta_description": "Family tours across India.",
        })
        self.assertEqual(response.status_code, 302)

        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.phone_raw, "919123456789")
        self.assertEqual(settings_obj.whatsapp_url, "https://wa.me/919123456789")
        self.assertContains(self.client.get(reverse("home")), "919123456789")


# --------------------------------------------------------------------------- #
# Automatic media cleanup                                                      #
# --------------------------------------------------------------------------- #

class MediaCleanupTests(MediaRootMixin, TestCase):

    def setUp(self):
        self.staff = User.objects.create_user("editor", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_deleting_a_record_removes_its_file(self):
        import os

        package = Package.objects.create(
            title="Ooty", duration="2D/1N", starting_price=100,
            short_description="s", main_image=gif(), highlights="a", inclusions="b")
        path = package.main_image.path
        self.assertTrue(os.path.exists(path))

        self.client.post(reverse("dashboard:resource_delete", args=["packages", package.pk]))
        self.assertFalse(os.path.exists(path))

    def test_replacing_a_file_deletes_the_previous_one(self):
        import os

        package = Package.objects.create(
            title="Ooty", duration="2D/1N", starting_price=100,
            short_description="s", main_image=gif("old.gif"), highlights="a", inclusions="b")
        old_path = package.main_image.path

        self.client.post(reverse("dashboard:resource_update", args=["packages", package.pk]), {
            "title": "Ooty",
            "slug": package.slug,
            "category": "",
            "duration": "2D/1N",
            "badge": "",
            "short_description": "s",
            "overview": "",
            "starting_price": "100",
            "main_image": gif("new.gif"),
            "highlights": "a",
            "inclusions": "b",
            "exclusions": "",
            "seo_title": "",
            "seo_description": "",
            "is_active": "on",
            "order": "0",
        })

        package.refresh_from_db()
        self.assertTrue(package.main_image.name.endswith("new.gif"))
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(package.main_image.path))

    def test_shared_files_are_kept_while_another_record_uses_them(self):
        """Seeded demo images share a path; deleting one row must not break the other."""
        import os

        first = GalleryImage.objects.create(image="gallery/shared.jpg", caption="One")
        second = GalleryImage.objects.create(image="gallery/shared.jpg", caption="Two")

        first.delete()

        self.assertTrue(GalleryImage.objects.filter(pk=second.pk).exists())
        # The second row still points at the path, so nothing should have been removed.
        self.assertEqual(second.image.name, "gallery/shared.jpg")

    def test_media_library_flags_unused_files(self):
        import os

        media_root = SiteImage._meta.get_field("image").storage.location
        gallery_dir = os.path.join(media_root, "gallery")
        os.makedirs(gallery_dir, exist_ok=True)
        with open(os.path.join(gallery_dir, "orphan.jpg"), "wb") as handle:
            handle.write(GIF)

        response = self.client.get(reverse("dashboard:media"))
        self.assertContains(response, "orphan.jpg")
        self.assertContains(response, "Unused")

    def test_purging_unused_files_leaves_used_ones_alone(self):
        import os

        row = SiteImage.objects.create(key="hero_bg", image=gif("used.gif"))
        used_path = row.image.path

        media_root = SiteImage._meta.get_field("image").storage.location
        orphan = os.path.join(media_root, "site", "orphan.gif")
        with open(orphan, "wb") as handle:
            handle.write(GIF)

        self.client.post(reverse("dashboard:media"), {"action": "purge"})

        self.assertFalse(os.path.exists(orphan))
        self.assertTrue(os.path.exists(used_path))


# --------------------------------------------------------------------------- #
# Defaults and seeding                                                         #
# --------------------------------------------------------------------------- #

class DefaultContentTests(TestCase):

    def test_registry_defaults_are_all_populated(self):
        """No heading should render blank out of the box."""
        for block in content.TEXT_BLOCKS:
            if block.optional:
                continue
            with self.subTest(key=block.key):
                self.assertNotEqual(block.default, "",
                                    f"{block.key} has no default content")

    def test_groups_cover_every_block(self):
        grouped = {block.key for blocks in content.TEXT_GROUPS.values() for block in blocks}
        self.assertEqual(grouped, {block.key for block in content.TEXT_BLOCKS})

    def test_seeding_creates_menus_and_is_idempotent(self):
        from .seeding import seed_content

        seed_content()
        first = MenuItem.objects.count()
        seed_content()
        self.assertEqual(MenuItem.objects.count(), first)
        self.assertGreaterEqual(first, len(defaults.MENU_ITEMS["header"]))

    def test_expected_header_links_exist(self):
        from .seeding import seed_content

        seed_content()
        labels = set(MenuItem.objects.filter(menu=MenuItem.HEADER)
                     .values_list("label", flat=True))
        for label, _page, _url, _icon, _order in defaults.MENU_ITEMS["header"]:
            self.assertIn(label, labels)


# --------------------------------------------------------------------------- #
# Rich text                                                                    #
# --------------------------------------------------------------------------- #

class RichTextTests(TestCase):

    def test_html_from_the_editor_is_rendered(self):
        FAQ.objects.create(question="Q", answer="<p>Bold <strong>answer</strong></p>")
        response = self.client.get(reverse("faq"))
        self.assertContains(response, "<strong>answer</strong>")

    def test_plain_text_keeps_its_line_breaks_but_is_escaped(self):
        from .templatetags.site_extras import rich

        rendered = str(rich("Line one\nLine two & five"))
        self.assertIn("Line one<br>", rendered)
        self.assertIn("&amp;", rendered)

    def test_empty_rich_value_renders_nothing(self):
        from .templatetags.site_extras import rich

        self.assertEqual(str(rich("")), "")
        self.assertEqual(str(rich(None)), "")

    def test_plain_filter_strips_tags_for_meta_description(self):
        from .templatetags.site_extras import plain

        self.assertEqual(plain("<p>Hello <b>there</b></p>"), "Hello there")
