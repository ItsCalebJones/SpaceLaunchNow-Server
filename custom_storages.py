from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):

    location = settings.STATICFILES_LOCATION


class LogoStorage(S3Boto3Storage):

    location = settings.LOGO_LOCATION
    file_overwrite = True
