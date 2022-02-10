from django.core.management import BaseCommand

from autoscaler.autoscaler import check_autoscaler


class Command(BaseCommand):
    help = "Run Auto Scaler"

    def handle(self, *args, **options):
        check_autoscaler()
