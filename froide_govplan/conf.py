from django.conf import settings

GOVPLAN_ENABLE_FOIREQUEST = getattr(settings, "GOVPLAN_ENABLE_FOIREQUEST", True)
GOVPLAN_NAME = getattr(settings, "GOVPLAN_NAME", "GovPlan")
