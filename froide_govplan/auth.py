from django.db.models import Q

from .models import GovernmentPlan


def has_limited_access(user):
    if not user.is_authenticated:
        return True
    return not user.has_perm("froide_govplan.add_governmentplan")


def get_allowed_plans(request):
    if not has_limited_access(request.user):
        return GovernmentPlan.objects.all()
    groups = request.user.groups.all()
    return GovernmentPlan.objects.filter(group__in=groups).distinct()


def get_visible_plans(request):
    if not has_limited_access(request.user):
        return GovernmentPlan.objects.all()
    if request.user.is_authenticated:
        groups = request.user.groups.all()
        return GovernmentPlan.objects.filter(
            Q(public=True) | Q(group__in=groups)
        ).distinct()
    return GovernmentPlan.objects.filter(public=True)
