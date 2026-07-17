from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import AuditLog, Camera
from .serializers import CameraSerializer
from rest_framework.pagination import PageNumberPagination
import django_filters
from .models import Detection
from .serializers import DetectionSerializer
import base64
import time
import cv2
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ModelMeta, ModelAssignment
from .serializers import ModelMetaSerializer, ModelAssignmentSerializer
from .models import KpiRollup

from rest_framework.views import APIView
from django.utils.dateparse import parse_datetime

class DashboardView(APIView):
    def get(self, request):
        camera_id = request.query_params.get('camera')
        if not camera_id:
            return Response({'error': 'camera is required'}, status=400)

        camera = Camera.objects.filter(id=camera_id).first()   # TEMP: no owner check for testing
        if not camera:
            return Response({'error': 'Camera not found'}, status=404)

        models_csv = request.query_params.get('models')
        model_filter = models_csv.split(',') if models_csv else None

        # KPI tiles: latest 1h rollup per model
        rollups = KpiRollup.objects.filter(camera=camera, window='1h').select_related('model').order_by('model_id', '-window_start')
        seen = set()
        kpi_tiles = []
        for r in rollups:
            if r.model_id in seen:
                continue
            if model_filter and r.model.name not in model_filter:
                continue
            seen.add(r.model_id)
            kpi_tiles.append({'model': r.model.name, 'metrics': r.metrics, 'window_start': r.window_start})

        # Recent events: last 20 detections
        events_qs = Detection.objects.filter(camera=camera).select_related('model').order_by('-timestamp')
        if model_filter:
            events_qs = events_qs.filter(model__name__in=model_filter)
        recent_events = DetectionSerializer(events_qs[:20], many=True).data

        # Model status: enabled assignments + health
        assignments = ModelAssignment.objects.filter(camera=camera).select_related('model')
        model_status = [{'model': a.model.name, 'enabled': a.enabled} for a in assignments]

        return Response({
            'camera': CameraSerializer(camera).data,
            'kpi_tiles': kpi_tiles,
            'recent_events': recent_events,
            'model_status': model_status,
        })

@action(detail=True, methods=['patch'], url_path='models/(?P<model_name>[^/.]+)')
def toggle_model(self, request, pk=None, model_name=None):
    camera = self.get_object()
    try:
        model = ModelMeta.objects.get(name=model_name)
    except ModelMeta.DoesNotExist:
        return Response({'error': f'Unknown model: {model_name}'}, status=404)

    enabled = request.data.get('enabled')
    if enabled is None:
        return Response({'error': 'enabled is required'}, status=400)

    assignment, _ = ModelAssignment.objects.update_or_create(
        camera=camera, model=model, defaults={'enabled': enabled}
    )

    AuditLog.objects.create(
        user=request.user,
        action='model_toggle',
        target=f'camera={camera.id} model={model_name} enabled={enabled}',
    )

    return Response(ModelAssignmentSerializer(assignment).data)

class ModelMetaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModelMeta.objects.all()
    serializer_class = ModelMetaSerializer
    permission_classes = [permissions.IsAuthenticated]

class ModelAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = ModelAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ModelAssignment.objects.filter(camera__owner=self.request.user)

class CameraViewSet(viewsets.ModelViewSet):
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Camera.objects.filter(owner=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        camera = self.get_object()
        cap = cv2.VideoCapture(camera.rtsp_url)
        start = time.time()
        ret, frame = cap.read()
        cap.release()

        if not ret or time.time() - start > 5:
            return Response({'success': False, 'error': 'Could not connect to camera. Check the RTSP URL and network access.'}, status=400)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        return Response({'success': True, 'frame': f'data:image/jpeg;base64,{frame_b64}'})

class DetectionPagination(PageNumberPagination):
    page_size = 50


class DetectionFilter(django_filters.FilterSet):
    since = django_filters.IsoDateTimeFilter(field_name='timestamp', lookup_expr='gte')
    until = django_filters.IsoDateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = Detection
        fields = ['camera', 'model', 'since', 'until']


class DetectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DetectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DetectionPagination
    filterset_class = DetectionFilter

    def get_queryset(self):
        return Detection.objects.filter(camera__owner=self.request.user).order_by('-timestamp')


