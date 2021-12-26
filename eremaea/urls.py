import django
from eremaea import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'collections', views.CollectionViewSet)
router.register(r'snapshots', views.SnapshotViewSet)
router.register(r'retention_policies', views.RetentionPolicyViewSet, basename='retention_policy')

if django.VERSION[0] > 1:
	from django.urls import include, re_path
else:
	from django.conf.urls import include, url as re_path

urlpatterns = [
	re_path(r'^', include(router.urls)),
]
