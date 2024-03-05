from . import *  # noqa

DEBUG = True
IN_TESTING = True
DISABLE_THROTTLE = True
THUMBNAIL_DUMMY = True
TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
TEST_OUTPUT_VERBOSE = True
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_DIR = "xmlrunner"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
