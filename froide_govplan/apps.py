from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FroideGovPlanConfig(AppConfig):
    name = "froide_govplan"
    verbose_name = _("GovPlan App")

    def ready(self):
        from froide.api import api_router
        from froide.follow.configuration import follow_registry

        from .api_views import GovernmentPlanViewSet
        from .configuration import GovernmentPlanFollowConfiguration

        follow_registry.register(GovernmentPlanFollowConfiguration())

        api_router.register(
            r"governmentplan", GovernmentPlanViewSet, basename="governmentplan"
        )
