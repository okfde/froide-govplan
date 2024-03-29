# Generated by Django 3.2.12 on 2022-03-17 14:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0022_auto_20180620_1551"),
        ("publicbody", "0039_publicbody_alternative_emails"),
        ("froide_govplan", "0008_governmentplan_proposals"),
    ]

    operations = [
        migrations.CreateModel(
            name="GovernmentPlanUpdatesCMSPlugin",
            fields=[
                (
                    "cmsplugin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="froide_govplan_governmentplanupdatescmsplugin",
                        serialize=False,
                        to="cms.cmsplugin",
                    ),
                ),
                (
                    "count",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="0 means all the updates",
                        verbose_name="number of updates",
                    ),
                ),
                (
                    "offset",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="number of updates to skip from top of list",
                        verbose_name="offset",
                    ),
                ),
                (
                    "categories",
                    models.ManyToManyField(
                        blank=True, to="publicbody.Category", verbose_name="categories"
                    ),
                ),
                (
                    "government",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="froide_govplan.government",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("cms.cmsplugin",),
        ),
    ]
