from api.v331.common.serializers import *


class EventsSerializer(serializers.HyperlinkedModelSerializer):
    type = EventTypeSerializer(many=False, read_only=True)
    launches = LaunchListSerializer(many=True, source='launch')
    expeditions = ExpeditionSerializer(many=True, source='expedition')
    spacestations = SpaceStationSerializerForCommon(many=True, source='spacestation')

    class Meta:
        model = Events
        fields = ('id', 'url', 'name', 'type', 'description', 'location', 'news_url', 'video_url', 'feature_image',
                  'date', 'launches', 'expeditions', 'spacestations')
