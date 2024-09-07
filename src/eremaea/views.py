import datetime
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from django.utils.cache import patch_cache_control
from django_filters import rest_framework as filters
from eremaea import models, serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action, parser_classes
from rest_framework.pagination import Cursor, CursorPagination, _positive_int
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.urls import replace_query_param


class CollectionFilter(filters.FilterSet):
	default_retention_policy = filters.ModelChoiceFilter(queryset=models.RetentionPolicy.objects.all(), to_field_name="name")

	class Meta:
		model = models.Collection
		fields = ['default_retention_policy']

class SnapshotPagination(CursorPagination):
	ordering = '-date'
	page_size_query_param = 'page_size'
	cursor_separator = '.'
	time_origin = datetime.datetime(1970, 1, 1)

	def decode_cursor(self, request):
		encoded = request.query_params.get(self.cursor_query_param)
		if encoded is None:
			return None

		try:
			position, offset, reverse = encoded.split(self.cursor_separator)

			if not position:
				position = None
			else:
				position = self.time_origin + datetime.datetime.resolution * _positive_int(position)
			offset   = _positive_int(offset, cutoff=self.offset_cutoff)
			reverse  = bool(int(reverse))
		except (TypeError, ValueError):
			raise NotFound(self.invalid_cursor_message)

		return Cursor(offset=offset, reverse=reverse, position=position)

	def encode_cursor(self, cursor):
		if cursor.position is not None:
			position = str(int((cursor.position - self.time_origin) / datetime.datetime.resolution))
		else:
			position = ''
		offset   = str(cursor.offset)
		reverse  = str(int(cursor.reverse))
		encoded  = self.cursor_separator.join([position, offset, reverse])

		return replace_query_param(self.base_url, self.cursor_query_param, encoded)

	def _get_position_from_instance(self, instance, ordering):
		field_name = ordering[0].lstrip('-')
		if isinstance(instance, dict):
			attr = instance[field_name]
		else:
			attr = getattr(instance, field_name)

		assert isinstance(attr, datetime.datetime), (
			'Invalid ordering value type. Expected datetime.datetime type, but got {type}'.format(type=type(attr).__name__)
		)

		return attr

class SnapshotContentNegotiation(api_settings.DEFAULT_CONTENT_NEGOTIATION_CLASS):
	def select_parser(self, request, parsers):
		viewset = request.parser_context['view']
		if viewset.action == 'create':
			return FileUploadParser()

		return super(SnapshotContentNegotiation, self).select_parser(request, parsers)

class SnapshotFilter(filters.FilterSet):
	retention_policy = filters.ModelChoiceFilter(queryset=models.RetentionPolicy.objects.all(), to_field_name="name")
	date = filters.IsoDateTimeFromToRangeFilter()

	class Meta:
		model = models.Snapshot
		fields = ['retention_policy', 'date']


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
	queryset = models.Collection.objects.select_related('default_retention_policy')
	serializer_class = serializers.CollectionSerializer
	lookup_field = 'name'
	filter_backends = [filters.DjangoFilterBackend]
	filterset_class = CollectionFilter

class SnapshotViewSet(viewsets.ModelViewSet):
	queryset = models.Snapshot.objects.select_related('collection', 'retention_policy')
	serializer_class = serializers.SnapshotSerializer
	create_serializer_class = serializers.CreateSnapshotSerializer
	list_serializer_class = serializers.ListSnapshotSerializer
	pagination_class = SnapshotPagination
	content_negotiation_class = SnapshotContentNegotiation
	filter_backends = [filters.DjangoFilterBackend]
	filterset_class = SnapshotFilter

	def get_queryset(self):
		collection_name = self.kwargs['collection']
		queryset = super(SnapshotViewSet, self).get_queryset()

		# For list action we need to distinguish
		# empty response from non-existing collection
		if self.action == 'list':
			collection = get_object_or_404(models.Collection, name = collection_name)
			return queryset.filter(collection = collection)

		return queryset.filter(collection__name = collection_name)

	def _get_create_serializer(self, request):
		file = getattr(request, 'data', {}).get('file')
		retention_policy = getattr(request, 'query_params', {}).get('retention_policy')

		data = {
			'file': file,
			'retention_policy': retention_policy,
		}

		return super(SnapshotViewSet, self).get_serializer(data = data)

	def get_serializer(self, *args, **kwargs):
		if self.action == 'create':
			return self._get_create_serializer(self.request)

		return super(SnapshotViewSet, self).get_serializer(*args, **kwargs)

	def get_serializer_class(self):
		if self.action == 'create':
			return self.create_serializer_class
		elif self.action == 'list':
			return self.list_serializer_class

		return super(SnapshotViewSet, self).get_serializer_class()

	def retrieve(self, request, pk=None, collection=None):
		response = super(SnapshotViewSet, self).retrieve(request, pk = pk, collection = collection)
		response['Link'] = '{0}; rel=alternate'.format(response.data['file'])
		return response
