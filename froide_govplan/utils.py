from urllib.parse import quote, urlencode

from django.conf import settings
from django.urls import reverse

TAG_NAME = "Koalitionstracker"


def make_request_url(plan, publicbody):
    pb_slug = publicbody.slug
    url = reverse("foirequest-make_request", kwargs={"publicbody_slug": pb_slug})
    subject = "Stand des Regierungsvorhabens „{}“".format(plan.title)
    if len(subject) > 250:
        subject = subject[:250] + "..."
    body = "Dokumente, die den Stand des Regierungsvorhabens „{}“ (siehe Koalitionsvertrag), dokumentieren.".format(
        plan.title
    )
    query = {
        "subject": subject.encode("utf-8"),
        "body": body,
        "ref": plan.get_foirequest_reference(),
        "tags": TAG_NAME,
    }

    hide_features = ["hide_public", "hide_similar", "hide_draft"]

    query.update({f: b"1" for f in hide_features})
    query = urlencode(query, quote_via=quote)
    return "%s%s?%s" % (settings.SITE_URL, url, query)
