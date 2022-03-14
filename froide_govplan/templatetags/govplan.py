from django import template

from froide_govplan.models import STATUS_CSS, PlanStatus

register = template.Library()


PROGRESS_ORDER = [
    PlanStatus.IMPLEMENTED,
    PlanStatus.PARTIALLY_IMPLEMENTED,
    PlanStatus.DEFERRED,
    PlanStatus.STARTED,
    PlanStatus.NOT_STARTED,
]


@register.simple_tag
def get_plan_progress(object_list):
    sections = []
    for value in PROGRESS_ORDER:
        label = value.label
        value = str(value)
        status_count = len([x for x in object_list if x.status == value])
        percentage = (
            0 if len(object_list) == 0 else status_count / len(object_list) * 100
        )
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


@register.inclusion_tag("froide_govplan/plugins/progress.html")
def get_section_progress(section):
    return {"object_list": section.get_plans()}
