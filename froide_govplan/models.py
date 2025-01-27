import functools
import re
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from filer.fields.image import FilerImageField
from froide.follow.models import Follower
from froide.georegion.models import GeoRegion
from froide.organization.models import Organization
from froide.publicbody.models import Category, Jurisdiction, PublicBody
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from . import conf
from .utils import make_request_url

try:
    from cms.models.fields import PlaceholderField
    from cms.models.pluginmodel import CMSPlugin
except ImportError:
    CMSPlugin = None
    PlaceholderField = None


if conf.GOVPLAN_ENABLE_FOIREQUEST:
    from froide.foirequest.models import FoiRequest
else:
    FoiRequest = None


class PlanStatus(models.TextChoices):
    NOT_STARTED = ("not_started", _("not started"))
    STARTED = ("started", _("started"))
    PARTIALLY_IMPLEMENTED = ("partially_implemented", _("partially implemented"))
    IMPLEMENTED = ("implemented", _("implemented"))
    DEFERRED = ("deferred", _("deferred"))


STATUS_CSS = {
    PlanStatus.NOT_STARTED: "light",
    PlanStatus.STARTED: "primary",
    PlanStatus.PARTIALLY_IMPLEMENTED: "warning",
    PlanStatus.IMPLEMENTED: "success",
    PlanStatus.DEFERRED: "danger",
}


class PlanRating(models.IntegerChoices):
    TERRIBLE = 1, _("terrible")
    BAD = 2, _("bad")
    OK = 3, _("OK")
    GOOD = 4, _("good")
    EXCELLENT = 5, _("excellent")


class Government(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("name"))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_("slug"))

    public = models.BooleanField(default=False, verbose_name=_("is public?"))
    jurisdiction = models.ForeignKey(
        Jurisdiction,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("jurisdiction"),
    )
    georegion = models.ForeignKey(
        GeoRegion,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("georegion"),
    )
    description = models.TextField(blank=True, verbose_name=_("description"))

    start_date = models.DateField(null=True, blank=True, verbose_name=_("start date"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("end date"))
    active = models.BooleanField(default=True, verbose_name=_("active"))

    planning_document = models.URLField(blank=True, verbose_name=_("planning document"))

    class Meta:
        verbose_name = _("Government")
        verbose_name_plural = _("Governments")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.planning_document:
            return self.planning_document
        # No planning document? Just return the base URL
        url = reverse("govplan:search")
        return url.rsplit("/", 2)[0]

    @property
    def days_available(self):
        if self.start_date is None:
            return 0
        if self.end_date is None:
            return 0
        return (self.end_date - self.start_date).days

    @property
    def days_left(self):
        if not self.end_date:
            return 0
        now = timezone.now().date()
        if now > self.end_date:
            return 0
        return (self.end_date - now).days

    def days_used_percentage(self) -> int:
        total_days = self.days_available
        if not total_days:
            return 0
        now = timezone.now().date()
        days_used = (now - self.start_date).days
        return int(days_used / total_days * 100)


class CategorizedGovernmentPlan(TaggedItemBase):
    tag = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="categorized_governmentplan"
    )
    content_object = models.ForeignKey("GovernmentPlan", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Categorized Government Plan")
        verbose_name_plural = _("Categorized Government Plans")


WORD_RE = re.compile(r"^\w+$", re.IGNORECASE)


class GovernmentPlanManager(models.Manager):
    SEARCH_LANG = "german"

    def get_search_vector(self):
        fields = [
            ("title", "A"),
            ("description", "B"),
            ("quote", "B"),
        ]
        return functools.reduce(
            lambda a, b: a + b,
            [SearchVector(f, weight=w, config=self.SEARCH_LANG) for f, w in fields],
        )

    def search(self, query, qs=None):
        if not qs:
            qs = self.get_queryset()
        query = query.strip()
        if not query:
            return qs
        search_queries = []
        for q in query.split():
            q = q.strip()
            if not q:
                continue
            if WORD_RE.match(q):
                sq = SearchQuery(
                    "{}:*".format(q), search_type="raw", config=self.SEARCH_LANG
                )
            else:
                sq = SearchQuery(q, search_type="plain", config=self.SEARCH_LANG)
            search_queries.append(sq)

        if not search_queries:
            return qs
        search_query = functools.reduce(lambda a, b: a & b, search_queries)

        search_vector = self.get_search_vector()
        qs = (
            qs.annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=0.1)
            .order_by("-rank")
        )
        return qs


class GovernmentPlan(models.Model):
    government = models.ForeignKey(
        Government, on_delete=models.CASCADE, verbose_name=_("government")
    )
    title = models.CharField(max_length=255, verbose_name=_("title"))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_("slug"))

    image = FilerImageField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("image"),
        on_delete=models.SET_NULL,
    )

    description = models.TextField(blank=True, verbose_name=_("description"))
    quote = models.TextField(blank=True, verbose_name=_("quote"))
    public = models.BooleanField(default=False, verbose_name=_("is public?"))
    due_date = models.DateField(null=True, blank=True, verbose_name=_("due date"))
    measure = models.CharField(max_length=255, blank=True, verbose_name=_("measure"))

    status = models.CharField(
        max_length=25,
        choices=PlanStatus.choices,
        default="not_started",
        verbose_name=_("status"),
    )
    rating = models.IntegerField(
        choices=PlanRating.choices, null=True, blank=True, verbose_name=_("rating")
    )

    reference = models.CharField(
        max_length=255, blank=True, verbose_name=_("reference")
    )

    categories = TaggableManager(
        through=CategorizedGovernmentPlan, verbose_name=_("categories"), blank=True
    )
    responsible_publicbody = models.ForeignKey(
        PublicBody,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("responsible public body"),
    )

    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("organization"),
    )

    group = models.ForeignKey(
        Group, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("group")
    )

    proposals = models.JSONField(blank=True, null=True)
    properties = models.JSONField(blank=True, default=dict)

    objects = GovernmentPlanManager()

    class Meta:
        ordering = ("reference", "title")
        verbose_name = _("Government plan")
        verbose_name_plural = _("Government plans")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "govplan:plan", kwargs={"gov": self.government.slug, "plan": self.slug}
        )

    def get_absolute_domain_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    def get_absolute_short_url(self):  # Return long url as short url for update emails
        return self.get_absolute_url()

    def get_absolute_domain_short_url(self):
        return settings.SITE_URL + self.get_absolute_short_url()

    def get_reference_links(self):
        if self.reference.startswith("https://"):
            return [self.reference]
        refs = [x.strip() for x in self.reference.split(",")]
        return [
            "{}#p-{}".format(self.government.planning_document, ref) for ref in refs
        ]

    def get_section(self):
        return GovernmentPlanSection.objects.filter(
            categories__in=self.categories.all()
        ).first()

    def update_from_updates(self):
        last_status_update = (
            self.updates.all().filter(public=True).exclude(status="").first()
        )
        if last_status_update:
            self.status = last_status_update.status
        last_rating_update = (
            self.updates.all().filter(public=True).exclude(rating=None).first()
        )
        if last_rating_update:
            self.rating = last_rating_update.rating
        if last_status_update or last_rating_update:
            self.save()

    def get_status_css(self):
        return STATUS_CSS.get(self.status, "")

    def make_request_url(self):
        if not self.responsible_publicbody:
            return []
        return make_request_url(self, self.responsible_publicbody)

    def has_recent_foirequest(self):
        frs = self.get_related_foirequests()
        ago = timezone.now() - timedelta(days=90)
        return any(fr.created_at > ago for fr in frs)

    def get_recent_foirequest(self):
        return self.get_related_foirequests()[0]

    def get_foirequest_reference(self):
        return "govplan:plan@{}".format(self.pk)

    def get_related_foirequests(self):
        if FoiRequest is None:
            return []
        if not self.responsible_publicbody:
            return []
        if hasattr(self, "_related_foirequests"):
            return self._related_foirequests

        self._related_foirequests = (
            FoiRequest.objects.filter(
                visibility=FoiRequest.VISIBILITY.VISIBLE_TO_PUBLIC,
                public_body=self.responsible_publicbody,
            )
            .filter(tags__name=conf.GOVPLAN_NAME)
            .filter(reference=self.get_foirequest_reference())
            .order_by("-created_at")
        )
        return self._related_foirequests


class GovernmentPlanUpdate(models.Model):
    plan = models.ForeignKey(
        GovernmentPlan,
        on_delete=models.CASCADE,
        related_name="updates",
        verbose_name=_("plan"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("user"),
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("organization"),
    )
    timestamp = models.DateTimeField(default=timezone.now, verbose_name=_("timestamp"))
    title = models.CharField(max_length=1024, blank=True, verbose_name=_("title"))
    content = models.TextField(blank=True, verbose_name=_("content"))
    url = models.URLField(blank=True, max_length=1024, verbose_name=_("URL"))

    status = models.CharField(
        max_length=25,
        choices=PlanStatus.choices,
        default="",
        blank=True,
        verbose_name=_("status"),
    )
    rating = models.IntegerField(
        choices=PlanRating.choices, null=True, blank=True, verbose_name=_("rating")
    )
    public = models.BooleanField(default=False, verbose_name=_("is public?"))

    if FoiRequest:
        foirequest = models.ForeignKey(
            FoiRequest,
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            verbose_name=_("FOI request"),
        )

    class Meta:
        ordering = ("-timestamp",)
        get_latest_by = "timestamp"
        verbose_name = _("Plan update")
        verbose_name_plural = _("Plan updates")

    def __str__(self):
        return "{} - {} ({})".format(self.title, self.timestamp, self.plan)

    def get_absolute_url(self):
        return "{}#update-{}".format(
            reverse(
                "govplan:plan",
                kwargs={"gov": self.plan.government.slug, "plan": self.plan.slug},
            ),
            self.id,
        )

    def get_absolute_domain_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    def get_url_domain(self):
        return urlparse(self.url).netloc or None


class GovernmentPlanFollower(Follower):
    content_object = models.ForeignKey(
        GovernmentPlan,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name=_("Government plan"),
    )

    class Meta(Follower.Meta):
        verbose_name = _("Government plan follower")
        verbose_name_plural = _("Government plan followers")


class GovernmentPlanSection(models.Model):
    government = models.ForeignKey(
        Government, on_delete=models.CASCADE, verbose_name=_("government")
    )

    title = models.CharField(max_length=255, verbose_name=_("title"))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_("slug"))

    categories = models.ManyToManyField(Category, blank=True)

    description = models.TextField(blank=True, verbose_name=_("description"))
    image = FilerImageField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("image"),
        on_delete=models.SET_NULL,
    )

    icon = models.CharField(
        _("Icon"),
        max_length=50,
        blank=True,
        help_text=_(
            """Enter an icon name from the <a href="https://fontawesome.com/v4.7.0/icons/" target="_blank">FontAwesome 4 icon set</a>"""
        ),
    )
    order = models.PositiveIntegerField(default=0)
    featured = models.DateTimeField(null=True, blank=True)

    if PlaceholderField:
        content_placeholder = PlaceholderField("content")

    class Meta:
        verbose_name = _("Government plan section")
        verbose_name_plural = _("Government plan sections")
        ordering = (
            "order",
            "title",
        )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "govplan:section",
            kwargs={"gov": self.government.slug, "section": self.slug},
        )

    def get_absolute_domain_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    def get_plans(self, queryset=None):
        if queryset is None:
            queryset = GovernmentPlan.objects.filter(public=True)

        queryset = queryset.filter(
            categories__in=self.categories.all(), government_id=self.government_id
        )
        return queryset.distinct().order_by("title")


if CMSPlugin:
    PLUGIN_TEMPLATES = [
        ("froide_govplan/plugins/default.html", _("Normal")),
        ("froide_govplan/plugins/progress.html", _("Progress")),
        ("froide_govplan/plugins/progress_row.html", _("Progress Row")),
        ("froide_govplan/plugins/time_used.html", _("Time used")),
        ("froide_govplan/plugins/card_cols.html", _("Card columns")),
        ("froide_govplan/plugins/search.html", _("Search")),
    ]

    class GovernmentPlansCMSPlugin(CMSPlugin):
        """
        CMS Plugin for displaying latest articles
        """

        government = models.ForeignKey(
            Government, null=True, blank=True, on_delete=models.SET_NULL
        )
        categories = models.ManyToManyField(
            Category, verbose_name=_("categories"), blank=True
        )

        count = models.PositiveIntegerField(
            _("number of plans"), default=1, help_text=_("0 means all the plans")
        )
        offset = models.PositiveIntegerField(
            _("offset"),
            default=0,
            help_text=_("number of plans to skip from top of list"),
        )
        template = models.CharField(
            _("template"),
            blank=True,
            max_length=250,
            choices=PLUGIN_TEMPLATES,
            help_text=_("template used to display the plugin"),
        )
        extra_classes = models.CharField(max_length=255, blank=True)

        @property
        def render_template(self):
            """
            Override render_template to use
            the template_to_render attribute
            """
            return self.template_to_render

        def copy_relations(self, old_instance):
            """
            Duplicate ManyToMany relations on plugin copy
            """
            self.categories.set(old_instance.categories.all())

        def __str__(self):
            if self.count == 0:
                return str(_("All matching plans"))
            return _("%s matching plans") % self.count

        def get_plans(self, request, published_only=True):
            if (
                published_only
                or not request
                or not getattr(request, "toolbar", False)
                or not request.toolbar.edit_mode_active
            ):
                plans = GovernmentPlan.objects.filter(public=True)
            else:
                plans = GovernmentPlan.objects.all()

            filters = {}
            if self.government_id:
                filters["government_id"] = self.government_id

            cat_list = self.categories.all().values_list("id", flat=True)
            if cat_list:
                filters["categories__in"] = cat_list

            plans = plans.filter(**filters).distinct()
            plans = plans.prefetch_related("categories", "government", "organization")
            if self.count == 0:
                return plans[self.offset :]
            return plans[self.offset : self.offset + self.count]

    class GovernmentPlanSectionsCMSPlugin(CMSPlugin):
        """
        CMS Plugin for displaying plan sections
        """

        government = models.ForeignKey(
            Government, null=True, blank=True, on_delete=models.SET_NULL
        )

    class GovernmentPlanUpdatesCMSPlugin(CMSPlugin):
        """
        CMS Plugin for displaying plan updates
        """

        government = models.ForeignKey(
            Government, null=True, blank=True, on_delete=models.SET_NULL
        )
        categories = models.ManyToManyField(
            Category, verbose_name=_("categories"), blank=True
        )

        count = models.PositiveIntegerField(
            _("number of updates"), default=1, help_text=_("0 means all the updates")
        )
        offset = models.PositiveIntegerField(
            _("offset"),
            default=0,
            help_text=_("number of updates to skip from top of list"),
        )

        def copy_relations(self, old_instance):
            """
            Duplicate ManyToMany relations on plugin copy
            """
            self.categories.set(old_instance.categories.all())

        def get_updates(self, request, published_only=True):
            # TODO: remove duplication with GovernmentPlansCMSPlugin.get_plans
            if (
                published_only
                or not request
                or not getattr(request, "toolbar", False)
                or not request.toolbar.edit_mode_active
            ):
                updates = GovernmentPlanUpdate.objects.filter(public=True)
            else:
                updates = GovernmentPlanUpdate.objects.all()

            updates = updates.order_by("-timestamp").prefetch_related(
                "plan", "plan__categories"
            )

            filters = {}
            if self.government_id:
                filters["plan__government_id"] = self.government_id

            cat_list = self.categories.all().values_list("id", flat=True)
            if cat_list:
                filters["plan__categories__in"] = cat_list

            updates = updates.filter(**filters).distinct()
            if self.count == 0:
                return updates[self.offset :]
            return updates[self.offset : self.offset + self.count]

        def __str__(self):
            if self.count == 0:
                return str(_("All matching updates"))
            return _("%s matching updates") % self.count
