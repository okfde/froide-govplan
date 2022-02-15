from django.views.generic import DetailView

from .models import GovernmentPlan


class GovPlanDetailView(DetailView):
    slug_url_kwarg = "plan"
    template_name = "froide_govplan/detail.html"

    def get_queryset(self):
        return GovernmentPlan.objects.filter(public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["updates"] = self.object.updates.filter(public=True).order_by(
            "-timestamp"
        )
        return context
