import csv
import json

from django.core.management.base import BaseCommand

from ...models import Government
from ...utils import PlanImporter


class Command(BaseCommand):
    help = "Loads public bodies"

    def add_arguments(self, parser):
        parser.add_argument("government", type=str)
        parser.add_argument("json_mapping", type=str)
        parser.add_argument("filename", type=str)

    def handle(self, *args, **options):
        government = Government.objects.get(slug=options["government"])

        with open(options["json_mapping"]) as f:
            col_mapping = json.load(f)

        importer = PlanImporter(government, col_mapping=col_mapping)

        filename = options["filename"]
        with open(filename) as csv_file:
            reader = csv.DictReader(csv_file)
            importer.import_rows(reader)

        self.stdout.write("Import done.\n")
