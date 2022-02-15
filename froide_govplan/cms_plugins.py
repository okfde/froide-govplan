from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import PLUGIN_TEMPLATES, GovernmentPlansCMSPlugin


@plugin_pool.register_plugin
class GovernmentPlansPlugin(CMSPluginBase):
    name = _("Government plans")
    model = GovernmentPlansCMSPlugin
    filter_horizontal = ("categories",)
    cache = True

    def get_render_template(self, context, instance, placeholder):
        return instance.template or PLUGIN_TEMPLATES[0][0]

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        context["object_list"] = instance.get_plans(
            context["request"], published_only=False
        )
        return context
