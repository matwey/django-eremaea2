from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from os import path
from eremaea.conf import settings
import magic
import mimetypes

def guess_extension(instance, filename):
	content_type = getattr(instance.file.file, 'content_type', None)
	_, ext = path.splitext(filename)

	if content_type is not None:
		valid_exts = mimetypes.guess_all_extensions(content_type)
		if ext in valid_exts:
			return ext
		elif len(valid_exts):
			return valid_exts[0]

	if not ext:
		content_type = magic.from_buffer(next(instance.file.file.chunks()), mime=True)
		return mimetypes.guess_extension(content_type)

	return ext

def snapshot_upload_to(instance, filename):
	prefix = settings.PATH
	collection = instance.collection.name
	date = instance.date.strftime("%Y-%m-%d-%H-%M-%S")
	ext = guess_extension(instance, filename)
	newfilename = "{0}-{1}{2}".format(collection, date, ext)
	return path.join(prefix, collection, newfilename)

class SnapshotQuerySet(models.query.QuerySet):
	# Django storage API doesn't support transactions
	# We can't support bulk delete
	def delete(self):
		for x in self:
			x.delete()
	delete.queryset_only = False

class ExpiredSnapshotManager(models.Manager):
	def get_queryset(self):
		return super(ExpiredSnapshotManager, self).get_queryset(
			).annotate(
				expires=models.ExpressionWrapper(
					F('date') + F('retention_policy__duration'),
					output_field=models.DateTimeField())
			).filter(expires__lt = timezone.now())

class Snapshot(models.Model):
	collection = models.ForeignKey('Collection', on_delete=models.CASCADE, db_index=True)
	date = models.DateTimeField(db_index=True, default=timezone.now)
	file = models.FileField(max_length=256, upload_to=snapshot_upload_to)
	retention_policy = models.ForeignKey('RetentionPolicy', on_delete=models.PROTECT, db_index=True)

	objects = SnapshotQuerySet.as_manager()
	expired_objects = ExpiredSnapshotManager.from_queryset(SnapshotQuerySet)()

	def save(self, *args, **kwargs):
		if not self.retention_policy_id:
			self.retention_policy_id = self.collection.default_retention_policy_id
		return super(Snapshot, self).save(*args, **kwargs)

	@transaction.atomic
	def delete(self, *args, **kwargs):
		storage, path = self.file.storage, self.file.name
		super(Snapshot, self).delete(*args, **kwargs)
		if storage.exists(path):
			storage.delete(path)

	def get_next(self):
		try:
			return self.get_next_by_date(collection = self.collection)
		except Snapshot.DoesNotExist:
			pass
	def get_previous(self):
		try:
			return self.get_previous_by_date(collection = self.collection)
		except Snapshot.DoesNotExist:
			pass

	class Meta:
		ordering = ['-date']
		get_latest_by = 'date'

class Collection(models.Model):
	name = models.CharField(max_length=256, blank=False, unique=True, db_index=True)
	default_retention_policy = models.ForeignKey('RetentionPolicy', on_delete=models.PROTECT)

	def get_latest(self):
		try:
			return Snapshot.objects.filter(collection = self).latest()
		except Snapshot.DoesNotExist:
			pass
	def get_earliest(self):
		try:
			return Snapshot.objects.filter(collection = self).earliest()
		except Snapshot.DoesNotExist:
			pass

class RetentionPolicy(models.Model):
	name = models.CharField(max_length=256, blank=False, null=False, unique=True, db_index=True)
	duration = models.DurationField(blank=False, null=False)

	class Meta:
		db_table = 'retention_policy'

	def purge(self):
		return Snapshot.expired_objects.filter(retention_policy = self).delete()
