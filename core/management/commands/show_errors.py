from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Display recent entries from errors.log"

    def add_arguments(self, parser):
        parser.add_argument("-n", "--lines", type=int, default=50)

    def handle(self, *args, **options):
        log_path = Path(settings.BASE_DIR) / "errors.log"
        if not log_path.exists():
            self.stdout.write(f"No errors.log found at {log_path}.")
            return
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-options["lines"] :]:
            self.stdout.write(line)
