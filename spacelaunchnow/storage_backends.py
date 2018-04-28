from storages.backends.s3boto3 import S3Boto3Storage
from spacelaunchnow import settings


class LogoStorage(S3Boto3Storage):
    location = settings.LOGO_LOCATION
    file_overwrite = True