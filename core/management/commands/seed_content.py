from django.core.management.base import BaseCommand

from core.seeding import seed_content


class Command(BaseCommand):
    help = ("Load the default site content (settings, menus, hero badges, services, "
            "steps, statistics, bullet points and contact cards). Safe to re-run.")

    def handle(self, *args, **options):
        counts = seed_content(verbose=True)

        summary = ", ".join(f"{value} {name}" for name, value in counts.items())
        self.stdout.write(self.style.SUCCESS(f"Seeded {summary}."))
        self.stdout.write(
            "Headings and paragraphs live in core/content.py and already have built-in "
            "defaults, so the site renders fully even before you edit them."
        )
