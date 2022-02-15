from django.urls import path
from django.utils.translation import pgettext_lazy

from .views import GovPlanDetailView

app_name = "govplan"

urlpatterns = [
    path(
        pgettext_lazy("url part", "<slug:gov>/plan/<slug:plan>/"),
        GovPlanDetailView.as_view(),
        name="plan",
    ),
]
