from django.contrib import admin, auth
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from adminsortable2.admin import SortableAdminMixin

from froide.api import api_router
from froide.follow.admin import FollowerAdmin
from froide.helper.admin_utils import make_choose_object_action, make_emptyfilter
from froide.helper.widgets import TagAutocompleteWidget
from froide.organization.models import Organization

from .api_views import GovernmentPlanViewSet
from .auth import get_allowed_plans, has_limited_access
from .forms import (
    GovernmentPlanForm,
    GovernmentPlanUpdateAcceptProposalForm,
    GovernmentPlanUpdateForm,
)
from .models import (
    Government,
    GovernmentPlan,
    GovernmentPlanFollower,
    GovernmentPlanSection,
    GovernmentPlanUpdate,
)

User = auth.get_user_model()

api_router.register(r"governmentplan", GovernmentPlanViewSet, basename="governmentplan")


class GovPlanAdminSite(admin.AdminSite):
    site_header = "Regierungsvorhaben"
    site_url = "/koalitionstracker/"


class GovernmentPlanAdminForm(GovernmentPlanForm):
    class Meta:
        model = GovernmentPlan
        fields = "__all__"
        widgets = {
            "categories": TagAutocompleteWidget(
                autocomplete_url=reverse_lazy("api:category-autocomplete")
            ),
        }


class GovernmentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "public", "start_date", "end_date")
    list_filter = ("public",)


def execute_assign_organization(admin, request, queryset, action_obj):
    queryset.update(organization=action_obj)


def execute_assign_group(admin, request, queryset, action_obj):
    queryset.update(group=action_obj)


PLAN_ACTIONS = {
    "assign_organization": make_choose_object_action(
        Organization, execute_assign_organization, _("Assign organization...")
    ),
    "assign_group": make_choose_object_action(
        Group, execute_assign_group, _("Assign permission group...")
    ),
}


class GovernmentPlanAdmin(admin.ModelAdmin):
    form = GovernmentPlanForm

    save_on_top = True
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)
    raw_id_fields = ("responsible_publicbody",)

    actions = ["make_public"]

    def get_queryset(self, request):
        qs = get_allowed_plans(request)
        qs = qs.prefetch_related(
            "categories",
            "organization",
            "group",
        )
        return qs

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not has_limited_access(request.user):
            admin_actions = {
                action: (
                    func,
                    action,
                    func.short_description,
                )
                for action, func in PLAN_ACTIONS.items()
            }
            actions.update(admin_actions)
        return actions

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:pk>/accept-proposal/",
                self.admin_site.admin_view(self.accept_proposal),
                name="froide_govplan-plan_accept_proposal",
            ),
        ]
        return my_urls + urls

    def get_list_display(self, request):
        list_display = [
            "title",
            "public",
            "status",
            "rating",
            "organization",
            "get_categories",
        ]
        if not has_limited_access(request.user):
            list_display.append("group")
        return list_display

    def get_list_filter(self, request):
        list_filter = [
            "status",
            "rating",
            "public",
        ]
        if not has_limited_access(request.user):
            list_filter.extend(
                [
                    make_emptyfilter(
                        "proposals", _("Has change proposals"), empty_value=None
                    ),
                    "organization",
                    "group",
                    "government",
                    "categories",
                ]
            )
        return list_filter

    def get_fields(self, request, obj=None):
        if has_limited_access(request.user):
            return (
                "title",
                "slug",
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

    def accept_proposal(self, request, pk):
        obj = get_object_or_404(self.get_queryset(request), pk=pk)
        plan_url = reverse(
            "admin:froide_govplan_governmentplan_change",
            args=(obj.pk,),
            current_app=self.admin_site.name,
        )
        if not obj.proposals:
            return redirect(plan_url)
        if request.method == "POST":
            proposals = obj.proposals or {}
            proposal_id = request.POST.get("proposal_id")
            delete_proposals = request.POST.getlist("proposal_delete")
            update = None
            if proposal_id:
                data = proposals[proposal_id]["data"]
                form = GovernmentPlanUpdateAcceptProposalForm(data=data, plan=obj)
                if form.is_valid():
                    update = form.save(
                        proposal_id=proposal_id,
                        delete_proposals=delete_proposals,
                    )
            else:
                form = GovernmentPlanUpdateAcceptProposalForm(data={}, plan=obj)
                form.delete_proposals(delete_proposals)

            if update is None:
                self.message_user(request, _("The proposal has been deleted."))

                return redirect(plan_url)

            self.message_user(
                request,
                _("An unpublished update has been created."),
            )
            update_url = reverse(
                "admin:froide_govplan_governmentplanupdate_change",
                args=(update.pk,),
                current_app=self.admin_site.name,
            )
            return redirect(update_url)
        else:
            form = GovernmentPlanUpdateAcceptProposalForm(plan=obj)

        opts = self.model._meta
        context = {
            "form": form,
            "proposals": form.get_proposals(),
            "object": obj,
            "app_label": opts.app_label,
            "opts": opts,
        }
        return render(
            request,
            "froide_govplan/admin/accept_proposal.html",
            context,
        )


class GovernmentPlanUpdateAdmin(admin.ModelAdmin):
    form = GovernmentPlanUpdateForm
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


class GovernmentPlanSectionAdmin(SortableAdminMixin, admin.ModelAdmin):
    save_on_top = True
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)
    raw_id_fields = ("categories",)
    list_display = (
        "title",
        "featured",
    )
    list_filter = (
        "featured",
        "categories",
        "government",
    )


admin.site.register(Government, GovernmentAdmin)
admin.site.register(GovernmentPlan, GovernmentPlanAdmin)
admin.site.register(GovernmentPlanUpdate, GovernmentPlanUpdateAdmin)
admin.site.register(GovernmentPlanSection, GovernmentPlanSectionAdmin)
admin.site.register(GovernmentPlanFollower, FollowerAdmin)

govplan_admin_site = GovPlanAdminSite(name="govplanadmin")
govplan_admin_site.register(GovernmentPlan, GovernmentPlanAdmin)
govplan_admin_site.register(GovernmentPlanUpdate, GovernmentPlanUpdateAdmin)
