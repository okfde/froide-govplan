from django import forms
from django.contrib import admin, auth
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tinymce.widgets import TinyMCE

from froide.helper.widgets import TagAutocompleteWidget

from .models import Government, GovernmentPlan, GovernmentPlanUpdate

User = auth.get_user_model()


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
        widgets = {"content": TinyMCE(attrs={"cols": 80, "rows": 30})}


class GovernmentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "public", "start_date", "end_date")
    list_filter = ("public",)


def has_limited_access(user):
    return not user.has_perm("froide_gov.change_governmentplanupdate")


def get_allowed_plans(request):
    if not has_limited_access(request.user):
        return GovernmentPlan.objects.all()
    groups = request.user.groups.all()
    return GovernmentPlan.objects.filter(group__in=groups).distinct()


class GovernmentPlanAdmin(admin.ModelAdmin):
    form = GovernmentPlanAdminForm

    save_on_top = True
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)
    raw_id_fields = ("responsible_publicbody",)
    list_display = (
        "title",
        "public",
        "status",
        "rating",
        "organization",
        "get_categories",
    )
    list_filter = (
        "status",
        "rating",
        "public",
        "government",
        "categories",
    )

    actions = ["make_public"]

    def get_queryset(self, request):
        qs = get_allowed_plans(request)
        qs = qs.prefetch_related(
            "categories",
            "organization",
        )
        return qs

    def get_fields(self, request, obj=None):
        if has_limited_access(request.user):
            return (
                "title",
                "description",
                "quote",
                "public",
                "due_date",
                "measure",
                "status",
                "rating",
                "reference",
            )
        return super().get_fields(request, obj=obj)

    def get_categories(self, obj):
        """
        Return the categories linked in HTML.
        """
        categories = [category.name for category in obj.categories.all()]
        return ", ".join(categories)

    get_categories.short_description = _("category(s)")

    def make_public(self, request, queryset):
        queryset.update(public=True)

    make_public.short_description = _("Make public")


class GovernmentPlanUpdateAdmin(admin.ModelAdmin):
    form = GovernmentPlanUpdateAdminForm
    save_on_top = True
    raw_id_fields = ("user", "foirequest")
    date_hierarchy = "timestamp"
    search_fields = ("title", "content")
    list_display = (
        "title",
        "timestamp",
        "plan",
        "user",
        "status",
        "rating",
        "public",
    )
    list_filter = (
        "status",
        "public",
        "organization",
    )
    search_fields = (
        "title",
        "plan__title",
    )
    date_hierarchy = "timestamp"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related(
            "plan",
            "user",
        )
        if has_limited_access(request.user):
            qs = qs.filter(plan__in=get_allowed_plans(request))
        return qs

    def save_model(self, request, obj, form, change):
        limited = has_limited_access(request.user)
        if not change and limited:
            # When added by a limited user,
            # autofill user and organization
            obj.user = request.user
            if obj.plan.organization:
                user_has_org = request.user.organization_set.all().filter(pk=1).exists()
                if user_has_org:
                    obj.organization = obj.plan.organization

        res = super().save_model(request, obj, form, change)

        obj.plan.update_from_updates()

        return res

    def get_fields(self, request, obj=None):
        if has_limited_access(request.user):
            return (
                "plan",
                "title",
                "timestamp",
                "content",
                "url",
                "status",
                "rating",
                "public",
            )
        return super().get_fields(request, obj=obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "plan":
            if has_limited_access(request.user):
                kwargs["queryset"] = get_allowed_plans(request)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def user_in_obj_group(self, request, obj):
        if not obj.plan.group_id:
            return False
        user = request.user
        return User.objects.filter(pk=user.pk, groups=obj.plan.group_id).exists()

    def has_view_permission(self, request, obj=None):
        if obj and self.user_in_obj_group(request, obj):
            return True
        return super().has_view_permission(request, obj=obj)

    def has_add_permission(self, request):
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if obj and self.user_in_obj_group(request, obj):
            return True
        return super().has_change_permission(request, obj=obj)


admin.site.register(Government, GovernmentAdmin)
admin.site.register(GovernmentPlan, GovernmentPlanAdmin)
admin.site.register(GovernmentPlanUpdate, GovernmentPlanUpdateAdmin)
