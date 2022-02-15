from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from filer.fields.image import FilerImageField
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from froide.foirequest.models import FoiRequest
from froide.organization.models import Organization
from froide.publicbody.models import Category, Jurisdiction, PublicBody

try:
    from cms.models.pluginmodel import CMSPlugin
except ImportError:
    CMSPlugin = None


class PlanStatus(models.TextChoices):
    NOT_STARTED = ("not_started", _("not started"))
    STARTED = ("started", _("started"))
    PARTIALLY_IMPLEMENTED = ("partially_implemented", _("partially implemented"))
    IMPLEMENTED = ("implemented", _("implemented"))
    DEFERRED = ("deferred", _("deferred"))


class PlanRating(models.IntegerChoices):
    TERRIBLE = 1, _("terrible")
    BAD = 2, _("bad")
    OK = 3, _("OK")
    GOOD = 4, _("good")
    EXCELLENT = 5, _("excellent")


class Government(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    public = models.BooleanField(default=False)
    jurisdiction = models.ForeignKey(Jurisdiction, null=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    planning_document = models.URLField(blank=True)

    class Meta:
        verbose_name = _("Government")
        verbose_name_plural = _("Governments")

    def __str__(self):
        return self.name


class CategorizedGovernmentPlan(TaggedItemBase):
    tag = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="categorized_governmentplan"
    )
    content_object = models.ForeignKey("GovernmentPlan", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Categorized Government Plan")
        verbose_name_plural = _("Categorized Government Plans")


class GovernmentPlan(models.Model):
    government = models.ForeignKey(Government, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    image = FilerImageField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("image"),
        on_delete=models.SET_NULL,
    )

    description = models.TextField(blank=True)
    public = models.BooleanField(default=False)

    status = models.CharField(
        max_length=25, choices=PlanStatus.choices, default="needs_approval"
    )
    rating = models.IntegerField(choices=PlanRating.choices, null=True, blank=True)

    reference = models.CharField(max_length=255, blank=True)

    categories = TaggableManager(
        through=CategorizedGovernmentPlan, verbose_name=_("categories"), blank=True
    )
    responsible_publicbody = models.ForeignKey(
        PublicBody, null=True, blank=True, on_delete=models.SET_NULL
    )

    organization = models.ForeignKey(
        Organization, null=True, blank=True, on_delete=models.SET_NULL
    )

    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ("reference", "title")
        verbose_name = _("Government plan")
        verbose_name_plural = _("Government plans")

    def __str__(self):
        return 'GovernmentPlan "%s" (#%s)' % (self.title, self.pk)

    def get_absolute_url(self):
        return reverse("govplan:plan", kwargs={
            "gov": self.government.slug,
            "plan": self.slug
        })

    def get_absolute_domain_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    def get_reference_link(self):
        if self.reference.startswith("https://"):
            return self.reference
        return "{}#{}".format(
            self.government.planning_document,
            self.reference
        )


class GovernmentPlanUpdate(models.Model):
    plan = models.ForeignKey(
        GovernmentPlan, on_delete=models.CASCADE, related_name="updates"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    organization = models.ForeignKey(
        Organization, null=True, blank=True, on_delete=models.SET_NULL
    )
    timestamp = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=1024, blank=True)
    content = models.TextField(blank=True)
    url = models.URLField(blank=True)

    status = models.CharField(
        max_length=25, choices=PlanStatus.choices, default="", blank=True
    )
    rating = models.IntegerField(choices=PlanRating.choices, null=True, blank=True)
    public = models.BooleanField(default=False)

    foirequest = models.ForeignKey(
        FoiRequest, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ("-timestamp",)
        get_latest_by = "timestamp"
        verbose_name = _("Plan update")
        verbose_name_plural = _("Plan updates")

    def __str__(self):
        return "Plan Update (%s)" % (self.pk,)


if CMSPlugin:

    PLUGIN_TEMPLATES = [
        ("froide_govplan/plugins/default.html", _("Normal")),
    ]

    class GovernmentPlansCMSPlugin(CMSPlugin):
        """
        CMS Plugin for displaying latest articles
        """

        government = models.ForeignKey(Government, null=True, blank=True, on_delete=models.SET_NULL)
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
            if self.government:
                filters["government"] = self.government

            cat_list = self.categories.all().values_list("id", flat=True)
            if cat_list:
                filters["categories__in"] = cat_list

            plans = plans.filter(**filters).distinct()
            plans = plans.prefetch_related(
                "categories", "government", "organization"
            )
            if self.count == 0:
                return plans[self.offset:]
            return plans[self.offset : self.offset + self.count]
