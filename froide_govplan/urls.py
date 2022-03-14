from django.urls import path
from django.utils.translation import pgettext_lazy

from .admin import govplan_admin_site
from .views import GovPlanDetailView, GovPlanSectionDetailView, search

app_name = "govplan"

urlpatterns = [
    path("admin/", govplan_admin_site.urls),
    path("search/", search, name="search"),
    path(
        pgettext_lazy("url part", "<slug:gov>/plan/<slug:plan>/"),
        GovPlanDetailView.as_view(),
        name="plan",
    ),
    path(
        pgettext_lazy("url part", "<slug:gov>/<slug:section>/"),
        GovPlanSectionDetailView.as_view(),
        name="section",
    ),
]
