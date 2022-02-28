from django import template

from froide_govplan.models import PlanStatus

register = template.Library()

STATUS_CSS = {
    PlanStatus.NOT_STARTED: "secondary",
    PlanStatus.STARTED: "primary",
    PlanStatus.PARTIALLY_IMPLEMENTED: "warning",
    PlanStatus.IMPLEMENTED: "success",
    PlanStatus.DEFERRED: "danger",
}


@register.simple_tag
def get_plan_progress(object_list):
    sections = []
    for value, label in PlanStatus.choices:
        status_count = len([x for x in object_list if x.status == value])
        percentage = status_count / len(object_list) * 100
        sections.append(
            {
                "count": status_count,
                "label": label,
                "css_class": STATUS_CSS[value],
                "percentage": round(percentage),
                "css_percentage": str(percentage),
            }
        )

    value, label
    return {"count": len(object_list), "sections": sections}
