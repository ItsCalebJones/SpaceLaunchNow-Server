import django_tables2 as tables
from api.models import Launch
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_tables2 import A

from web.templatetags.sln_utils import launch_time_context


class LaunchTable(tables.Table):
    name = tables.LinkColumn("launch_by_slug", args=[A("slug")])
    rocket = tables.Column(empty_values=(), verbose_name="Rocket", accessor="rocket.configuration.name")
    net = tables.Column(verbose_name="NET")

    def render_net(self, value, record):
        """Render NET through the shared launch-time markup, so table rows carry
        the same labeled UTC fallback and client-side localisation as the cards."""
        context = launch_time_context(value, getattr(record, "net_precision", None))
        return mark_safe(render_to_string("web/includes/launch_time.html", context))

    class Meta:
        model = Launch
        fields = (
            "name",
            "status",
            "launch_service_provider",
            "rocket",
            "mission",
            "net",
            "pad",
        )
        template_name = "django_tables2/bootstrap4.html"
