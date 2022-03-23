import copy

from django import forms
from django.contrib.auth import get_user_model
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
        empty_value=None,
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


class GovernmentPlanUpdateAcceptProposalForm(GovernmentPlanUpdateProposalForm):
    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop("plan")
        super().__init__(*args, **kwargs)

    def get_proposals(self):
        data = copy.deepcopy(self.plan.proposals)
        user_ids = self.plan.proposals.keys()
        user_map = {
            str(u.id): u for u in get_user_model().objects.filter(id__in=user_ids)
        }
        status_dict = dict(PlanStatus.choices)
        rating_dict = dict(PlanRating.choices)
        for user_id, v in data.items():
            v["user"] = user_map[user_id]
            data[user_id]["data"]["rating_label"] = rating_dict.get(
                data[user_id]["data"]["rating"]
            )
            data[user_id]["data"]["status_label"] = status_dict.get(
                data[user_id]["data"]["status"]
            )
        return data

    def save(
        self,
        proposal_id=None,
        delete_proposals=None,
    ):
        update = super(forms.ModelForm, self).save(commit=False)
        update.plan = self.plan

        if delete_proposals is None:
            delete_proposals = []
        if proposal_id:
            proposals = self.get_proposals()
            proposal_user = proposals[proposal_id]["user"]
            user_org = proposal_user.organizations.all().first()
            if user_org:
                update.organization = user_org
            delete_proposals.append(proposal_id)

        self.delete_proposals(delete_proposals)
        update.save()
        return update

    def delete_proposals(self, delete_proposals):
        for pid in delete_proposals:
            if pid in self.plan.proposals:
                del self.plan.proposals[pid]
        if not self.plan.proposals:
            self.plan.proposals = None
        self.plan.save(update_fields=["proposals"])
