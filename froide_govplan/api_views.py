from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets

from .models import Government, GovernmentPlan, GovernmentPlanUpdate


class GovernmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Government
        fields = ("id", "name", "slug", "start_date", "end_date", "planning_document")


class GovernmentPlanSerializer(serializers.ModelSerializer):
    site_url = serializers.CharField(source="get_absolute_domain_url")
    updates = serializers.SerializerMethodField()

    class Meta:
        model = GovernmentPlan
        fields = (
            "id",
            "site_url",
            "government",
            "title",
            "slug",
            "description",
            "quote",
            "due_date",
            "measure",
            "status",
            "rating",
            "properties",
            "updates",
        )

    def get_updates(self, obj):
        return GovernmentPlanUpdateSerializer(
            obj.updates.all(), read_only=True, many=True, context=self.context
        ).data


class GovernmentPlanUpdateSerializer(serializers.ModelSerializer):
    site_url = serializers.CharField(source="get_absolute_domain_url")

    class Meta:
        model = GovernmentPlanUpdate
        fields = (
            "timestamp",
            "title",
            "content",
            "site_url",
            "url",
            "status",
            "rating",
        )


class GovernmentPlanFilter(filters.FilterSet):
    government = filters.ModelChoiceFilter(
        queryset=Government.objects.filter(public=True)
    )
    properties = filters.CharFilter(method="properties_filter")

    class Meta:
        model = GovernmentPlan
        fields = (
            "government",
            "status",
            "rating",
            "properties",
        )

    def properties_filter(self, queryset, name, value):
        try:
            key, value = value.split(":", 1)
        except ValueError:
            return queryset.filter(properties__has_key=value)

        return queryset.filter(**{"properties__%s__contains" % key: value})


class GovernmentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GovernmentPlanSerializer
    filterset_class = GovernmentPlanFilter

    def get_queryset(self):
        return (
            GovernmentPlan.objects.filter(public=True)
            .select_related("government")
            .prefetch_related("updates")
        )
