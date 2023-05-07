from django.db.models.deletion import ProtectedError
from django.utils.cache import patch_cache_control
from eremaea import models, serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response

class RetentionPolicyViewSet(viewsets.ModelViewSet):
	queryset = models.RetentionPolicy.objects.all()
	serializer_class = serializers.RetentionPolicySerializer
	lookup_field = 'name'

	def destroy(self, request, name):
		try:
			return super(RetentionPolicyViewSet, self).destroy(request, name)
		except ProtectedError as e:
			return Response(status=status.HTTP_400_BAD_REQUEST)
	@action(methods=['post'], detail=True)
	def purge(self, request, name):
		retention_policy = models.RetentionPolicy.objects.get(name = name)
		retention_policy.purge()
		return Response(status=status.HTTP_201_CREATED)

class CollectionViewSet(viewsets.ModelViewSet):
	queryset = models.Collection.objects.select_related("default_retention_policy")
	serializer_class = serializers.CollectionSerializer
	lookup_field = 'name'

	def retrieve(self, request, name=None):
		response = super(CollectionViewSet, self).retrieve(request, name)
		link = []
		if 'begin' in response.data:
			link.append("{0}; rel=begin".format(response.data['begin']))
		if 'end' in response.data:
			link.append("{0}; rel=end".format(response.data['end']))
		if link:
			response['Link'] = ", ".join(link)
		patch_cache_control(response, max_age=0, must_revalidate=True)
		return response

class SnapshotViewSet(viewsets.ModelViewSet):
	queryset = models.Snapshot.objects.select_related("collection", "retention_policy")
	serializer_class = serializers.SnapshotSerializer
	parser_classes = (FileUploadParser,)

	def create(self, request):
		if 'collection' not in request.query_params:
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail':'collection is not specified'})
		if 'file' not in request.data:
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail':'file is not supplied'})
		kwargs = {}
		kwargs['file'] = request.data['file']
		kwargs['collection'] = models.Collection.objects.get(name = request.query_params['collection'])
		if 'retention_policy' in request.query_params:
			kwargs['retention_policy'] = models.RetentionPolicy.objects.get(name = request.query_params['retention_policy'])
		models.Snapshot.objects.create(**kwargs)
		return Response(status=status.HTTP_201_CREATED)
	def retrieve(self, request, pk=None):
		response = super(SnapshotViewSet, self).retrieve(request, pk)
		link = []
		if response.data['next'] is not None:
			link.append("{0}; rel=next".format(response.data['next']))
		if response.data['prev'] is not None:
			link.append("{0}; rel=prev".format(response.data['prev']))
		link.append("{0}; rel=alternate".format(response.data['file']))
		if link:
			response['Link'] = ", ".join(link)
		return response
