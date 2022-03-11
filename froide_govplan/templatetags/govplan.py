from django import template

from froide_govplan.models import STATUS_CSS, PlanStatus

register = template.Library()


@register.simple_tag
def get_plan_progress(object_list):
    sections = []
    for value, label in PlanStatus.choices:
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
