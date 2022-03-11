from datetime import datetime
from typing import Iterator

from django.utils.translation import gettext_lazy as _

from froide.follow.configuration import FollowConfiguration
from froide.helper.notifications import Notification, TemplatedEvent

from .admin import get_allowed_plans
from .models import GovernmentPlanFollower, GovernmentPlanUpdate


class GovernmentPlanFollowConfiguration(FollowConfiguration):
    model = GovernmentPlanFollower
    title: str = _("Government plans")
    slug: str = "govplan"
    follow_message: str = _("You are now following this plan.")
    unfollow_message: str = _("You are not following this plan anymore.")
    confirm_email_message: str = _(
        "Check your emails and click the confirmation link in order to follow this government plan."
    )
    action_labels = {
        "follow": _("Follow plan"),
        "follow_q": _("Follow plan?"),
        "unfollow": _("Unfollow plan"),
        "following": _("Following plan"),
        "follow_description": _(
            "You will get notifications via email when something new happens with this plan. You can unsubscribe anytime."
        ),
    }

    def get_content_object_queryset(self, request):
        return get_allowed_plans(request)

    def can_follow(self, content_object, user, request=None):
        if request:
            get_allowed_plans(request)

        return super().can_follow(content_object, user)

    def get_batch_updates(
        self, start: datetime, end: datetime
    ) -> Iterator[Notification]:
        yield from get_plan_updates(start, end)

    def get_confirm_follow_message(self, content_object):
        return _(
            "please confirm that you want to follow the plan “{title}” by clicking this link:"
        ).format(title=content_object.title)

    def email_changed(self, user):
        # Move all confirmed email subscriptions of new email
        # to user except own requests
        self.model.objects.filter(email=user.email, confirmed=True).update(
            email="", user=user
        )


def get_plan_updates(start: datetime, end: datetime):
    plan_updates = GovernmentPlanUpdate.objects.filter(
        public=True, timestamp__gte=start, timestamp__lt=end
    ).select_related("plan")

    for plan_update in plan_updates:
        yield Notification(
            section=_("Government Plans"),
            event_type="planupdate",
            object=plan_update.plan,
            object_label=plan_update.plan.title,
            timestamp=plan_update.timestamp,
            event=make_plan_event(plan_update.plan),
            user_id=None,
        )


def make_plan_event(plan):
    return TemplatedEvent(
        _("An update was posted for the government plan “{title}”."),
        title=plan.title,
    )
