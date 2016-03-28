from django.db import models, transaction
from django.db.models import F,Q
from django.utils import timezone
from os import path
import mimetypes

class Snapshot(models.Model):
	def upload_to(instance, filename):
		(mimetype, encoding) = mimetypes.guess_type(filename)
		ext = mimetypes.guess_extension(mimetype)
		collection = instance.collection.name
		date = instance.date.strftime("%Y-%m-%d-%H-%M-%S")
		newfilename = "{0}-{1}{2}".format(collection, date, ext)
		return path.join(collection, newfilename)

	collection = models.ForeignKey('Collection', on_delete=models.CASCADE, db_index=True)
	date = models.DateTimeField(db_index=True, default=timezone.now)
	file = models.FileField(max_length=256, upload_to=upload_to)
	retention_policy = models.ForeignKey('RetentionPolicy', on_delete=models.PROTECT, db_index=True)

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
		index_together = ['collection', 'date', 'retention_policy']
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
		return Snapshot.objects.filter(retention_policy = self
			).annotate(
				expires=models.ExpressionWrapper(
					F('date') + F('retention_policy__duration'),
					output_field=models.DateTimeField()
				)
			).filter(expires__lt = timezone.now()).delete()
