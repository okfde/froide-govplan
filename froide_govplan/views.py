from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView

from .forms import GovernmentPlanUpdateProposalForm
from .models import Government, GovernmentPlan, GovernmentPlanSection


class GovernmentMixin:
    def dispatch(self, *args, **kwargs):
        self.get_government()
        return super().dispatch(*args, **kwargs)

    def get_government(self):
        filter_kwarg = {}
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            filter_kwarg["public"] = True
        self.government = get_object_or_404(
            Government, slug=self.kwargs["gov"], **filter_kwarg
        )


class GovPlanSectionDetailView(GovernmentMixin, DetailView):
    slug_url_kwarg = "section"
    template_name = "froide_govplan/section.html"

    def get_queryset(self):
        return GovernmentPlanSection.objects.filter(
            government=self.government
        ).select_related("government")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = context["object"].get_plans()
        return context


class GovPlanSectionDetailOGView(GovPlanSectionDetailView):
    template_name = "froide_govplan/section_og.html"


class GovPlanDetailView(GovernmentMixin, DetailView):
    slug_url_kwarg = "plan"
    template_name = "froide_govplan/detail.html"

    def get_queryset(self):
        qs = GovernmentPlan.objects.filter(government=self.government)
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return qs
        return qs.filter(public=True).select_related(
            "responsible_publicbody", "organization"
        )

    def get_section(self):
        return GovernmentPlanSection.objects.filter(
            categories__in=self.object.categories.all()
        ).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["updates"] = self.object.updates.filter(public=True).order_by(
            "-timestamp"
        )
        context["section"] = self.get_section()
        if self.request.user.is_authenticated:
            context["update_proposal_form"] = GovernmentPlanUpdateProposalForm()
        # For CMS toolbar
        self.request.govplan = self.object
        return context


class GovPlanDetailOGView(GovPlanDetailView):
    template_name = "froide_govplan/plan_og.html"


class GovPlanProposeUpdateView(GovernmentMixin, LoginRequiredMixin, UpdateView):
    template_name = "publicbody/add_proposal.html"
    slug_url_kwarg = "plan"
    form_class = GovernmentPlanUpdateProposalForm

    def get_queryset(self):
        qs = GovernmentPlan.objects.filter(government=self.government)
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return qs
        return qs.filter(public=True)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        form.save(self.object, self.request.user)
        messages.add_message(
            self.request,
            messages.INFO,
            _(
                "Thank you for your proposal. We will send you an email when it has been approved."
            ),
        )
        return redirect(self.object)


def search(request):
    plans = GovernmentPlan.objects.search(request.GET.get("q", ""))

    if request.GET.get("government"):
        try:
            gov_id = int(request.GET["government"])
            plans = plans.filter(government_id=gov_id)
        except ValueError:
            pass

    plans = plans[:20]
    return render(
        request, "froide_govplan/plugins/card_cols.html", {"object_list": plans}
    )
