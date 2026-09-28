"""Point the seeded "Visit us" contact card at the Maps URL.

The card was seeded without a link, so it rendered as plain text. ``{maps}`` is
resolved by ``ContactMethod._substitute`` from the Maps URL in Site Settings.
Only cards with a blank link are touched, so an admin's own link is kept.
"""

from django.db import migrations

BLANK_LINK_CARDS = ["Visit us"]


def link_visit_card(apps, schema_editor):
    ContactMethod = apps.get_model("core", "ContactMethod")
    ContactMethod.objects.filter(
        title__in=BLANK_LINK_CARDS, link="").update(link="{maps}")


def unlink_visit_card(apps, schema_editor):
    ContactMethod = apps.get_model("core", "ContactMethod")
    ContactMethod.objects.filter(
        title__in=BLANK_LINK_CARDS, link="{maps}").update(link="")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_seed_defaults"),
    ]

    operations = [
        migrations.RunPython(link_visit_card, unlink_visit_card),
    ]
