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
