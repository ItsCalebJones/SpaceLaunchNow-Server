from django.test import TestCase

from bot.utils.version import read_package_name_from_pyproject, read_version_from_pyproject


class TestSLN(TestCase):
    def test_get_version(self):
        assert read_version_from_pyproject()

    def test_get_package_name(self):
        assert read_package_name_from_pyproject()
