from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FroideGovPlanConfig(AppConfig):
    name = "froide_govplan"
    verbose_name = _("GovPlan App")

    def ready(self):
        from froide.follow.configuration import follow_registry

        from .configuration import GovernmentPlanFollowConfiguration

        follow_registry.register(GovernmentPlanFollowConfiguration())
