from storages.backends.s3boto3 import S3Boto3Storage

STATICFILES_LOCATION = "static/home"
MEDIA_LOCATION = "media"

APP_IMAGE_LOCATION = MEDIA_LOCATION + "/app_images"  # type: str
APP_IMAGE_STORAGE = "custom_storages.AppImageStorage"


class AppImageStorage(S3Boto3Storage):
    location = APP_IMAGE_LOCATION
    file_overwrite = True


class StaticStorage(S3Boto3Storage):
    location = STATICFILES_LOCATION
    file_overwrite = True
