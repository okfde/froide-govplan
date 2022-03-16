from django import forms
from django.utils.safestring import mark_safe

import bleach
from bleach.linkifier import Linker
from tinymce.widgets import TinyMCE

from .models import GovernmentPlan, GovernmentPlanUpdate

BLEACH_OPTIONS = {
    "tags": [
        "a",
        "strong",
        "b",
        "i",
        "em",
        "ul",
        "ol",
        "li",
        "p",
        "h3",
        "h4",
        "h5",
        "blockquote",
    ]
}


def set_link_attrs(attrs, new=False):
    attrs[(None, "rel")] = "noopener"
    return attrs


class BleachField(forms.CharField):
    """Bleach form field"""

    def to_python(self, value):
        """
        Strips any dodgy HTML tags from the input.
        Mark the return value as template safe.
        """
        if value in self.empty_values:
            return self.empty_value
        cleaned = bleach.clean(value, **BLEACH_OPTIONS)
        linker = Linker(callbacks=[set_link_attrs])
        return mark_safe(linker.linkify(cleaned))


class GovernmentPlanForm(forms.ModelForm):
    description = BleachField(required=False, widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = GovernmentPlan
        fields = "__all__"


class GovernmentPlanUpdateForm(forms.ModelForm):
    content = BleachField(required=False, widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = GovernmentPlanUpdate
        fields = "__all__"
