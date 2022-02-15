from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class GovPlanCMSApp(CMSApp):
    name = _("GovPlan CMS App")
    app_name = "govplan"

    def get_urls(self, page=None, language=None, **kwargs):
        return ["froide_govplan.urls"]
