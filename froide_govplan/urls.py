from django.urls import path
from django.utils.translation import pgettext_lazy

from .views import (
    GovPlanDetailOGView,
    GovPlanDetailView,
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
        pgettext_lazy("url part", "<slug:gov>/plan/<slug:plan>/_og/"),
        GovPlanDetailOGView.as_view(),
        name="plan_og",
    ),
    path(
        pgettext_lazy("url part", "<slug:gov>/<slug:section>/"),
        GovPlanSectionDetailView.as_view(),
        name="section",
    ),
]
