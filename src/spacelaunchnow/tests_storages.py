"""Guards for the STORAGES configuration.

Django 5.1 removed DEFAULT_FILE_STORAGE and STATICFILES_STORAGE. Setting them is
silently ignored, so a misconfiguration here does not raise -- it just quietly
falls back to local filesystem storage while STATIC_URL still points at Spaces.
That combination let collectstatic "succeed" without ever uploading, and new
static files 404'd in production.

These tests assert the *resolved* backend rather than the setting string, so the
same class of silent breakage cannot come back.
"""

from django.conf import settings
from django.test import SimpleTestCase


class StoragesConfigTests(SimpleTestCase):
    def test_storages_setting_is_defined(self):
        """Without STORAGES, Django silently uses local filesystem defaults."""
        self.assertTrue(hasattr(settings, "STORAGES"))
        self.assertIn("default", settings.STORAGES)
        self.assertIn("staticfiles", settings.STORAGES)

    def test_removed_django_5_settings_are_not_used(self):
        """These names are inert on Django >= 5.1; defining them invites confusion."""
        for removed in ("DEFAULT_FILE_STORAGE", "STATICFILES_STORAGE"):
            with self.subTest(setting=removed):
                self.assertFalse(
                    hasattr(settings, removed),
                    f"{removed} was removed in Django 5.1 and is silently ignored; configure STORAGES instead.",
                )

    def test_remote_storage_backends_resolve_to_s3(self):
        """The real regression: staticfiles must resolve to the S3 backend, not
        Django's local default, whenever remote storage is in use."""
        if getattr(settings, "USE_LOCAL_STORAGE", False):
            self.skipTest("local storage configured")

        from django.contrib.staticfiles.storage import staticfiles_storage
        from storages.backends.s3boto3 import S3Boto3Storage

        self.assertIsInstance(
            staticfiles_storage,
            S3Boto3Storage,
            "staticfiles resolved to a non-S3 backend; collectstatic would write "
            "to local disk while STATIC_URL points at Spaces.",
        )

    def test_static_url_and_backend_agree(self):
        """STATIC_URL pointing at Spaces while the backend is local is the exact
        half-configured state that caused the outage."""
        if getattr(settings, "USE_LOCAL_STORAGE", False):
            self.skipTest("local storage configured")

        self.assertIn("digitaloceanspaces.com", settings.STATIC_URL)
        self.assertEqual(
            settings.STORAGES["staticfiles"]["BACKEND"],
            "api.custom_storages.StaticStorage",
        )
