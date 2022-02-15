from django import forms
from django.contrib import admin
from django.urls import reverse_lazy

from tinymce.widgets import TinyMCE

from froide.helper.widgets import TagAutocompleteWidget

from .models import Government, GovernmentPlan, GovernmentPlanUpdate


class GovernmentPlanAdminForm(forms.ModelForm):
    class Meta:
        model = GovernmentPlan
        fields = "__all__"
        widgets = {
            "categories": TagAutocompleteWidget(
                autocomplete_url=reverse_lazy("api:category-autocomplete")
            ),
        }


class GovernmentPlanUpdateAdminForm(forms.ModelForm):
    class Meta:
        model = GovernmentPlanUpdate
        fields = "__all__"
        widgets = {
            "content": TinyMCE(attrs={'cols': 80, 'rows': 30})
        }


class GovernmentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "public", "start_date", "end_date")
    list_filter = ("public",)


class GovernmentPlanAdmin(admin.ModelAdmin):
    form = GovernmentPlanAdminForm

    save_on_top = True
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("responsible_publicbody",)
    list_display = (
        "title",
        "public",
        "status",
        "rating",
    )
    list_filter = ("status", "rating", "public", "government")


class GovernmentPlanUpdateAdmin(admin.ModelAdmin):
    form = GovernmentPlanUpdateAdminForm
    raw_id_fields = ("user", "foirequest")
    list_display = (
        "plan",
        "user",
        "timestamp",
        "status",
        "rating",
        "public",
    )
    list_filter = (
        "status",
        "public",
    )
    search_fields = ("title", "plan__title",)
    date_hierarchy = "timestamp"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related(
            "plan",
            "user",
        )
        return qs


admin.site.register(Government, GovernmentAdmin)
admin.site.register(GovernmentPlan, GovernmentPlanAdmin)
admin.site.register(GovernmentPlanUpdate, GovernmentPlanUpdateAdmin)
