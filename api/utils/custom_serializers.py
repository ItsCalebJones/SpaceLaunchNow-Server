import time
from rest_framework import serializers


class TimeStampField(serializers.Field):
    def to_internal_value(self, data):
        pass

    def to_representation(self, value):
        try:
            return int(time.mktime(value.timetuple()))
        except OverflowError:
            return 0
