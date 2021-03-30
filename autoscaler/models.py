from django.db import models


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class AutoscalerSettings(SingletonModel):
    enabled = models.BooleanField(default=False)
    custom_worker_count = models.IntegerField(null=True, blank=True, default=None)
    current_workers = models.IntegerField(null=True, blank=True, default=None)
    max_workers = models.IntegerField(null=False, blank=False, default=5)

    def __str__(self):
        return "Autoscaler Settings"
