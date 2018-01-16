from eremaea import models
from rest_framework import serializers

class RetentionPolicySerializer(serializers.HyperlinkedModelSerializer):
	url = serializers.HyperlinkedIdentityField(lookup_field='name', view_name='retention_policy-detail')

	class Meta:
		model = models.RetentionPolicy
		fields = ('url', 'name', 'duration')

class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
	collection = serializers.HyperlinkedRelatedField(view_name='collection-detail', read_only=True, lookup_field='name')
	retention_policy = serializers.HyperlinkedRelatedField(view_name='retention_policy-detail', queryset=models.RetentionPolicy.objects.all(), lookup_field='name')
	next = serializers.HyperlinkedRelatedField(view_name='snapshot-detail', read_only=True, source="get_next")
	prev = serializers.HyperlinkedRelatedField(view_name='snapshot-detail', read_only=True, source="get_previous")

	class Meta:
		model = models.Snapshot
		fields = ('url', 'collection', 'file', 'date', 'retention_policy', 'next', 'prev')

class CollectionSerializer(serializers.HyperlinkedModelSerializer):
	url = serializers.HyperlinkedIdentityField(lookup_field='name', view_name='collection-detail')
	default_retention_policy = serializers.HyperlinkedRelatedField(view_name='retention_policy-detail', queryset=models.RetentionPolicy.objects.all(), lookup_field='name')
	begin = serializers.HyperlinkedRelatedField(view_name='snapshot-detail', read_only=True, source="get_earliest")
	end = serializers.HyperlinkedRelatedField(view_name='snapshot-detail', read_only=True, source="get_latest")

	class Meta:
		model = models.Collection
		fields = ('url', 'name', 'default_retention_policy', 'begin', 'end')
