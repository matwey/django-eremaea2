from eremaea import views
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework import routers

router = DefaultRouter()
router.register(r'collections', views.CollectionViewSet)
router.register(r'snapshots', views.SnapshotViewSet)
router.register(r'retention_policies', views.RetentionPolicyViewSet, base_name='retention_policy')

urlpatterns = [
	url(r'^', include(router.urls)),
]
