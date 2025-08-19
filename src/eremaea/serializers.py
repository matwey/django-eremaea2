from eremaea import models
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.reverse import reverse


class SnapshotHyperlinkRelated(serializers.HyperlinkedRelatedField):
	view_name = 'snapshot-detail'

	def get_url(self, obj, view_name, request, format):
		url_kwargs = {
			'collection': obj.collection.name,
			'pk': obj.pk,
		}

		return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

	def get_object(self, view_name, view_args, view_kwargs):
		return self.get_queryset().get(collection__name = view_kwargs['collection'], pk = view_kwargs['pk'])

class SnapshotHyperlinkIdentity(SnapshotHyperlinkRelated):
	def __init__(self, **kwargs):
		kwargs['read_only'] = True
		kwargs['source'] = '*'
		super(SnapshotHyperlinkIdentity, self).__init__(**kwargs)

class CurrentCollectionDefault:
	requires_context = True

	def __call__(self, serializer_field):
		view = serializer_field.context['view']
		collection_name = view.kwargs['collection']
		collection = get_object_or_404(models.Collection, name = collection_name)
		return collection

class RetentionPolicySerializer(serializers.HyperlinkedModelSerializer):
	url = serializers.HyperlinkedIdentityField(lookup_field='name', view_name='retention_policy-detail')

	class Meta:
		model = models.RetentionPolicy
		fields = '__all__'

class CreateSnapshotSerializer(serializers.HyperlinkedModelSerializer):
	url = SnapshotHyperlinkIdentity()
	collection = serializers.SlugRelatedField(queryset=models.Collection.objects.all(), slug_field='name', allow_null=False, default=serializers.CreateOnlyDefault(CurrentCollectionDefault()))
	retention_policy = serializers.SlugRelatedField(queryset=models.RetentionPolicy.objects.all(), slug_field='name', allow_null=True)

	class Meta:
		model = models.Snapshot
		fields = '__all__'

class SnapshotSerializer(CreateSnapshotSerializer):
	class Meta(CreateSnapshotSerializer.Meta):
		read_only_fields = ['file']

class ListSnapshotSerializer(SnapshotSerializer):
	collection = None

	class Meta:
		model = models.Snapshot
		exclude = ['collection',]

class CollectionSerializer(serializers.HyperlinkedModelSerializer):
	url = serializers.HyperlinkedIdentityField(lookup_field='name', view_name='collection-detail')
	default_retention_policy = serializers.SlugRelatedField(queryset=models.RetentionPolicy.objects.all(), slug_field='name')

	class Meta:
		model = models.Collection
		fields = '__all__'
