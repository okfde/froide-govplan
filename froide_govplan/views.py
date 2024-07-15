from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView

from froide.helper.breadcrumbs import BreadcrumbView

from .auth import get_visible_plans
from .forms import GovernmentPlanUpdateProposalForm
from .models import Government, GovernmentPlan, GovernmentPlanSection


class GovernmentMixin(BreadcrumbView):
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

    def get_breadcrumbs(self, context):
        if "request" in context:
            request = context["request"]

            title = request.current_page.get_title()
            url = request.current_page.get_absolute_url()
            return [(title, url)]

        return []


class GovPlanSectionDetailView(GovernmentMixin, DetailView):
    slug_url_kwarg = "section"
    template_name = "froide_govplan/section.html"

    def get_queryset(self):
        return GovernmentPlanSection.objects.filter(
            government=self.government
        ).select_related("government")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = get_visible_plans(self.request)
        context["plans"] = context["object"].get_plans(queryset=queryset)
        return context

    def get_breadcrumbs(self, context):
        return super().get_breadcrumbs(context) + [
            (self.object.title, self.object.get_absolute_url())
        ]


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["updates"] = self.object.updates.filter(public=True).order_by(
            "-timestamp"
        )
        context["section"] = self.object.get_section()
        if self.request.user.is_authenticated:
            context["update_proposal_form"] = GovernmentPlanUpdateProposalForm()
        # For CMS toolbar
        self.request.govplan = self.object
        return context

    def get_breadcrumbs(self, context):
        obj = context["object"]
        section = context["section"]

        breadcrumbs = super().get_breadcrumbs(context)

        if section:
            breadcrumbs.append((section.title, section.get_absolute_url()))

        return breadcrumbs + [
            (obj.title, obj.get_absolute_url()),
        ]


class GovPlanProposeUpdateView(GovernmentMixin, LoginRequiredMixin, UpdateView):
    slug_url_kwarg = "plan"
    form_class = GovernmentPlanUpdateProposalForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return redirect(self.object)

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

    def form_invalid(self, form):
        messages.add_message(
            self.request,
            messages.ERROR,
            _("There's been an error with your form submission."),
        )
        return redirect(self.object)


def search(request):
    q = request.GET.get("q", "")
    plans = GovernmentPlan.objects.filter(public=True)
    if q:
        plans = GovernmentPlan.objects.search(q, qs=plans)

    if request.GET.get("government"):
        try:
            gov_id = int(request.GET["government"])
            plans = plans.filter(government_id=gov_id)
        except ValueError:
            pass
    if request.GET.get("status"):
        try:
            status = request.GET["status"]
            plans = plans.filter(status=status)
        except ValueError:
            pass

    if q:
        # limit when there's a search
        plans = plans[:20]
    return render(
        request, "froide_govplan/plugins/card_cols.html", {"object_list": plans}
    )
