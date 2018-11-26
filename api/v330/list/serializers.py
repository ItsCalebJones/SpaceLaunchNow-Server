from api.models import *
from rest_framework import serializers

from api.v330.normal.serializers import LaunchStatusSerializer

CACHE_TIMEOUT_ONE_DAY = 24 * 60 * 60


class LaunchListSerializer(serializers.ModelSerializer):
    pad = serializers.StringRelatedField()
    location = serializers.StringRelatedField(source='pad.location')
    status = LaunchStatusSerializer(many=False, read_only=True)
    landing = serializers.SerializerMethodField()
    landing_success = serializers.SerializerMethodField()
    launcher = serializers.SerializerMethodField()
    orbit = serializers.SerializerMethodField()
    mission = serializers.StringRelatedField()
    mission_type = serializers.StringRelatedField(source='mission.mission_type.name')
    slug = serializers.SlugField(source='get_full_absolute_url')
    
    class Meta:
        model = Launch
        fields = ('id', 'url', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'mission', 'mission_type',
                  'pad', 'location', 'landing', 'landing_success', 'launcher', 'orbit')

    def get_landing(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-landing")
            landing = cache.get(cache_key)
            if landing is not None:
                return landing

            landings = []
            for stage in obj.rocket.firststage.all():
                if stage.landing is not None:
                    landings.append(stage.landing)

            if len(landings) == 0:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None
            elif len(landings) == 1:
                cache.set(cache_key, landings[0].landing_location.abbrev, CACHE_TIMEOUT_ONE_DAY)
                return landings[0].landing_location.abbrev
            elif len(landings) > 1:
                cache.set(cache_key, "MX Landing", CACHE_TIMEOUT_ONE_DAY)
                return "MX Landing"
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None

        except Exception as ex:
            return None

    def get_landing_success(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-landing-success")
            landing = cache.get(cache_key)
            if landing is not None:
                return landing

            landings = []
            for stage in obj.rocket.firststage.all():
                if stage.landing is not None:
                    landings.append(stage.landing)

            if len(landings) == 0:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None
            elif len(landings) == 1:
                landing_status = 0
                if landings[0].success is None:
                    landing_status = 0
                elif landings[0].success:
                    landing_status = 1
                elif not landings[0].success:
                    landing_status = 2
                cache.set(cache_key, landing_status, CACHE_TIMEOUT_ONE_DAY)
                return landing_status
            elif len(landings) > 1:
                landing_successes = 0
                landing_failures = 0
                landing_null = 0

                for landing in landings:
                    if landing.success is None:
                        landing_null += 1
                    elif landing.success:
                        landing_successes += 1
                    elif not landing.success:
                        landing_failures += 1

                landing_status = 0
                if (landing_failures > 0 or landing_null > 0) and landing_successes > 0:
                    landing_status = 3
                elif landing_failures > 0 and landing_successes == 0:
                    landing_status = 2
                elif landing_failures == 0 and landing_null == 0 and landing_successes > 0:
                    landing_status = 1
                cache.set(cache_key, landing_status, CACHE_TIMEOUT_ONE_DAY)
                return landing_status
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None

        except Exception as ex:
            return None

    def get_launcher(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-launcher")
            launcher = cache.get(cache_key)
            if launcher is not None:
                return launcher

            launchers = []
            for stage in obj.rocket.firststage.all():
                if stage.launcher is not None:
                    launchers.append(stage.launcher)

            if len(launchers) == 0:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None
            elif len(launchers) == 1:
                cache.set(cache_key, launchers[0].serial_number, CACHE_TIMEOUT_ONE_DAY)
                return launchers[0].serial_number
            elif len(launchers) > 1:
                cache.set(cache_key, "MX Launchers", CACHE_TIMEOUT_ONE_DAY)
                return "MX Launchers"
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None

        except Exception as ex:
            return None

    def get_orbit(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-orbit")
            orbit = cache.get(cache_key)
            if orbit is not None:
                return orbit

            if obj.mission.orbit is not None and obj.mission.orbit.abbrev is not None:
                cache.set(cache_key, obj.mission.orbit.abbrev, CACHE_TIMEOUT_ONE_DAY)
                return obj.mission.orbit.abbrev

        except Exception as ex:
            return None
