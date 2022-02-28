import datetime
import re

from django.template.defaultfilters import slugify

from froide.publicbody.models import PublicBody

from .models import GovernmentPlan


class PlanImporter(object):
    def __init__(self, government, col_mapping=None):
        if col_mapping is None:
            col_mapping = {}
        self.col_mapping = col_mapping
        self.government = government
        self.post_save_list = []

    def import_rows(self, reader):
        for row in reader:
            self.import_row(row)

    def import_row(self, row):
        print("importing", row)
        title = row[self.col_mapping["title"]]
        if not title:
            return
        plan = GovernmentPlan.objects.filter(
            government=self.government, title=title
        ).first()
        if plan:
            return

        plan = GovernmentPlan(government=self.government)
        for col, row_col in self.col_mapping.items():
            method_name = "handle_{}".format(col)
            if hasattr(self, method_name):
                getattr(self, method_name)(plan, row[row_col])
            else:
                setattr(plan, col, row[row_col])
        plan.save()
        for func in self.post_save_list:
            func(plan)

    def handle_title(self, plan, title):
        plan.title = title
        plan.slug = slugify(title)

    def handle_categories(self, plan, categories):
        categories = [
            x.strip() for x in re.split(r" & | und ", categories) if x.strip()
        ]
        if categories:
            self.post_save_list.append(lambda p: p.categories.add(*categories))

    def handle_reference(self, plan, reference):
        plan.reference = ", ".join(re.split(r"\s*[,/]\s*", reference))

    def handle_responsible_publicbody(self, plan, pb):
        if not pb.strip():
            return
        pb = PublicBody.objects.get(
            jurisdiction=self.government.jurisdiction,
            other_names__iregex=r"(\W|^){}(\W|$)".format(pb),
        )
        plan.responsible_publicbody = pb

    def handle_due_date(self, plan, date_descr):
        if not date_descr.strip():
            return

        def parse_date(date_descr):
            match = re.search(r"(\d{4})", date_descr)
            if not match:
                return
            year = int(match.group(1))
            if "Mitte" in date_descr:
                return datetime.date(year, 7, 1)
            if "Ende" in date_descr:
                return datetime.date(year, 12, 1)
            if "Anfang" in date_descr:
                return datetime.date(year, 3, 1)
            if "Innerhalb" in date_descr:
                return datetime.date(year, 12, 31)
            return datetime.date(year, 1, 1)

        plan.due_date = parse_date(date_descr)

    def handle_status(self, plan, status):
        if not status.strip() or status == "noch nicht umgesetzt":
            status = "not_started"
        plan.status = status
