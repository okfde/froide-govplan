from django.urls import path
from django.utils.translation import pgettext_lazy

from .views import (
    GovPlanDetailView,
    GovPlanProposeUpdateView,
    GovPlanSectionDetailView,
    search,
)

app_name = "govplan"

urlpatterns = [
    path("search/", search, name="search"),
    path(
        pgettext_lazy("url part", "<slug:gov>/plan/<slug:plan>/"),
        GovPlanDetailView.as_view(),
        name="plan",
    ),
    path(
        pgettext_lazy("url part", "<slug:gov>/plan/<slug:plan>/propose-update/"),
        GovPlanProposeUpdateView.as_view(),
        name="propose_planupdate",
    ),
    path(
        pgettext_lazy("url part", "<slug:gov>/<slug:section>/"),
        GovPlanSectionDetailView.as_view(),
        name="section",
    ),
]
