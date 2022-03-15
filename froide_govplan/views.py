from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView

from .models import Government, GovernmentPlan, GovernmentPlanSection


class GovernmentMixin:
    def get(self, *args, **kwargs):
        self.get_government()
        return super().get(*args, **kwargs)

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
        return GovernmentPlanSection.objects.filter(government=self.government)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = context["object"].get_plans()
        return context


class GovPlanDetailView(GovernmentMixin, DetailView):
    slug_url_kwarg = "plan"
    template_name = "froide_govplan/detail.html"

    def get_queryset(self):
        qs = GovernmentPlan.objects.filter(government=self.government)
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return qs
        return qs.filter(public=True)

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
        # For CMS toolbar
        self.request.govplan = self.object
        return context


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
