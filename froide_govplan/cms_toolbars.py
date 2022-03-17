from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool


class GovPlanToolbar(CMSToolbar):
    def populate(self):
        if (
            self.request.current_page
            and self.request.current_page.application_namespace != "govplan"
        ):
            return
        menu = self.toolbar.get_or_create_menu("govplan-menu", "Koalitionstracker")

        url = reverse(
            "admin:app_list",
            kwargs={"app_label": "froide_govplan"},
            current_app="govplanadmin",
        )
        menu.add_modal_item(_("Edit plans and updates"), url=url)

        if hasattr(self.request, "govplan"):
            govplan = self.request.govplan
            url = reverse(
                "admin:froide_govplan_governmentplan_change",
                args=(govplan.pk,),
                current_app="govplanadmin",
            )
            menu.add_modal_item(_("Edit government plan"), url=url)
            url = reverse(
                "admin:froide_govplan_governmentplanupdate_add",
                current_app="govplanadmin",
            )
            url = "{}?plan={}".format(url, govplan.id)
            menu.add_modal_item(_("Add update"), url=url)


toolbar_pool.register(GovPlanToolbar)
