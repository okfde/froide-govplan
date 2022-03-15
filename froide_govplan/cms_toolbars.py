from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool


class GovPlanToolbar(CMSToolbar):
    def populate(self):
        if not hasattr(self.request, "govplan"):
            return

        menu = self.toolbar.get_or_create_menu("govplan-menu", _("GovPlan"))
        govplan = self.request.govplan
        url = reverse(
            "govplan:admin:froide_govplan_governmentplan_change",
            args=(govplan.pk,),
            current_app="govplan",
        )
        menu.add_modal_item(_("Edit government plan"), url=url)
        url = reverse(
            "govplan:admin:froide_govplan_governmentplanupdate_add",
            current_app="govplan",
        )
        menu.add_modal_item(_("Add update"), url=url)


toolbar_pool.register(GovPlanToolbar)
