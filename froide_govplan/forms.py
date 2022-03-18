from django import forms
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import bleach
from bleach.linkifier import Linker
from tinymce.widgets import TinyMCE

from .models import GovernmentPlan, GovernmentPlanUpdate, PlanRating, PlanStatus

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
    description = BleachField(
        required=False, widget=TinyMCE(attrs={"cols": 80, "rows": 30})
    )

    class Meta:
        model = GovernmentPlan
        fields = "__all__"


class GovernmentPlanUpdateForm(forms.ModelForm):
    content = BleachField(
        required=False, widget=TinyMCE(attrs={"cols": 80, "rows": 30})
    )

    class Meta:
        model = GovernmentPlanUpdate
        fields = "__all__"


class GovernmentPlanUpdateProposalForm(forms.ModelForm):
    title = forms.CharField(
        label=_("title"),
        help_text=_("Summarize the update in a title."),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            }
        ),
    )
    content = forms.CharField(
        required=False,
        label=_("details"),
        help_text=_("Optionally give more details."),
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "3"}),
    )
    url = forms.URLField(
        label=_("source URL"),
        help_text=_("Please give provide a link."),
        widget=forms.URLInput(
            attrs={"class": "form-control", "placeholder": "https://"}
        ),
    )
    status = forms.ChoiceField(
        label=_("status"),
        help_text=_("Has the status of the plan changed?"),
        choices=[("", "---")] + PlanStatus.choices,
        required=False,
    )
    rating = forms.TypedChoiceField(
        label=_("rating"),
        help_text=_("What's your rating of the current implementation?"),
        choices=[("", "---")] + PlanRating.choices,
        coerce=int,
        empty_value="",
        required=False,
    )

    class Meta:
        model = GovernmentPlanUpdate
        fields = (
            "title",
            "content",
            "url",
            "status",
            "rating",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, plan, user):
        """
        This doesn't save instance, but saves
        the change proposal.
        """
        data = self.cleaned_data
        plan.proposals = plan.proposals or {}
        plan.proposals[user.id] = {
            "data": data,
            "timestamp": timezone.now().isoformat(),
        }
        plan.save(update_fields=["proposals"])
        return plan
