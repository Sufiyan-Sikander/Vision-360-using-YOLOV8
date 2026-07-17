from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CameraViewSet, DetectionViewSet, ModelMetaViewSet, ModelAssignmentViewSet, DashboardView

router = DefaultRouter()
router.register(r'cameras', CameraViewSet, basename='camera')
router.register(r'detections', DetectionViewSet, basename='detection')
router.register(r'models', ModelMetaViewSet, basename='model')
router.register(r'assignments', ModelAssignmentViewSet, basename='assignment')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]