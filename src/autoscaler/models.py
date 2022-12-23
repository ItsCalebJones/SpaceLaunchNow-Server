from django.db import models

from spacelaunchnow.base_models import SingletonModel


class AutoscalerSettings(SingletonModel):
    enabled = models.BooleanField(default=False)
    custom_worker_count = models.IntegerField(null=True, blank=True, default=None)
    current_workers = models.IntegerField(null=True, blank=True, default=None)
    max_workers = models.IntegerField(null=False, blank=False, default=10)

    spacex_weight = models.IntegerField(null=False, blank=False, default=5)
    ula_weight = models.IntegerField(null=False, blank=False, default=3)
    rocket_lab_weight = models.IntegerField(null=False, blank=False, default=3)

    starship_event_weight = models.IntegerField(null=False, blank=False, default=5)
    starship_launch_weight = models.IntegerField(null=False, blank=False, default=3)

    other_weight = models.IntegerField(null=False, blank=False, default=1)

    def __str__(self):
        return "Autoscaler Settings"
