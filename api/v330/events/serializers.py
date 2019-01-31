from api.v330.common.serializers import *


class EventsSerializer(serializers.HyperlinkedModelSerializer):
    type = EventTypeSerializer(many=False, read_only=True)

    class Meta:
        model = Events
        fields = ('id', 'url', 'name', 'type', 'description', 'location', 'news_url', 'feature_image', 'date')
