from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from . import conf


class GovPlanToolbar(CMSToolbar):
    def populate(self):
        if not self.is_current_app:
            return
        menu = self.toolbar.get_or_create_menu("govplan-menu", conf.GOVPLAN_NAME)

        url = reverse(
            "admin:app_list",
            kwargs={"app_label": "froide_govplan"},
            current_app="govplanadmin",
        )
        menu.add_link_item(_("Edit plans and updates"), url=url)

        if hasattr(self.request, "govplan"):
            govplan = self.request.govplan
            url = reverse(
                "admin:froide_govplan_governmentplan_change",
                args=(govplan.pk,),
                current_app="govplanadmin",
            )
            menu.add_link_item(_("Edit government plan"), url=url)
            url = reverse(
                "admin:froide_govplan_governmentplanupdate_add",
                current_app="govplanadmin",
            )
            url = "{}?plan={}".format(url, govplan.id)
            menu.add_link_item(_("Add update"), url=url)


toolbar_pool.register(GovPlanToolbar)
