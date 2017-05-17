from rest_framework import serializers


class LauncherDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    agency = serializers.CharField(max_length=50)
    imageURL = serializers.URLField(allow_blank=True)
    nationURL = serializers.URLField(allow_blank=True)

    def create(self, validated_data):
        """
        Create and return a new `Orbiter` instance, given the validated data.
        """
        return LauncherDetailSerializer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Orbiter` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.agency = validated_data.get('agency', instance.agency)
        instance.imageURL = validated_data.get('imageURL', instance.imageURL)
        instance.nationURL = validated_data.get('nationURL', instance.nationURL)
        instance.save()
        return instance


class LauncherSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    agency = serializers.CharField(max_length=50)
    imageURL = serializers.URLField(allow_blank=True)
    nationURL = serializers.URLField(allow_blank=True)

    def create(self, validated_data):
        """
        Create and return a new `Orbiter` instance, given the validated data.
        """
        return LauncherSerializer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Orbiter` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.agency = validated_data.get('agency', instance.agency)
        instance.imageURL = validated_data.get('imageURL', instance.imageURL)
        instance.nationURL = validated_data.get('nationURL', instance.nationURL)
        instance.save()
        return instance


class OrbiterSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    agency = serializers.CharField(max_length=50)
    history = serializers.CharField(max_length=500)
    details = serializers.CharField(max_length=500)
    imageURL = serializers.URLField(allow_blank=True)
    nationURL = serializers.URLField(allow_blank=True)
    wikiLink = serializers.URLField(allow_blank=True)

    def create(self, validated_data):
        """
        Create and return a new `Orbiter` instance, given the validated data.
        """
        return OrbiterSerializer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Orbiter` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.agency = validated_data.get('agency', instance.agency)
        instance.details = validated_data.get('details', instance.name)
        instance.history = validated_data.get('history', instance.agency)
        instance.imageURL = validated_data.get('imageURL', instance.imageURL)
        instance.nationURL = validated_data.get('nationURL', instance.nationURL)
        instance.wikiLink = validated_data.get('wikiLink', instance.nationURL)
        instance.save()
        return instance
