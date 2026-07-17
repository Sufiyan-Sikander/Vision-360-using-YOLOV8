import base64
import time
from datetime import datetime, timezone as dt_timezone

import cv2
from celery import shared_task

from .models import Camera, ModelAssignment, Detection
from .adapters import get_adapter

from django.utils import timezone
from django.db.models import Count, Avg, Q
from .models import KpiRollup

WINDOW_SECONDS = {"1h": 3600, "1d": 86400, "1w": 604800}

@shared_task
def rollup_kpis():
    now = timezone.now()
    for window, seconds in WINDOW_SECONDS.items():
        window_start = now - timezone.timedelta(seconds=seconds)
        pairs = ModelAssignment.objects.filter(enabled=True).values_list('camera_id', 'model_id').distinct()
        for camera_id, model_id in pairs:
            dets = Detection.objects.filter(
                camera_id=camera_id, model_id=model_id, timestamp__gte=window_start
            )
            total = dets.count()
            if total == 0:
                continue
            metrics = {"count": total}
            model_name = ModelMeta.objects.get(id=model_id).name
            if model_name == "ppe":
                compliant = dets.filter(event_type="compliant").count()
                metrics["compliance_pct"] = round(compliant / total * 100, 1)
            elif model_name == "attendance":
                metrics["attendance_count"] = total
            elif model_name in ("theft", "shoplifting"):
                metrics["incident_count"] = dets.exclude(event_type="suspicious_activity").count()

            KpiRollup.objects.update_or_create(
                camera_id=camera_id, model_id=model_id, window=window, window_start=window_start,
                defaults={"metrics": metrics},
            )
    return "KPI rollup complete"

_adapter_cache = {}

def _get_cached_adapter(model_name):
    if model_name not in _adapter_cache:
        adapter = get_adapter(model_name)
        adapter.load()
        _adapter_cache[model_name] = adapter
    return _adapter_cache[model_name]


@shared_task
def run_inference(camera_id):
    try:
        camera = Camera.objects.get(id=camera_id)
    except Camera.DoesNotExist:
        return f"Camera {camera_id} not found"

    cap = cv2.VideoCapture(camera.rtsp_url)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
    start = time.time()
    ret, frame = cap.read()
    cap.release()

    if not ret or time.time() - start > 5:
        camera.status = 'offline'
        camera.save(update_fields=['status'])
        return f"Camera {camera_id} failed to pull frame"

    camera.status = 'online'
    camera.last_frame_at = datetime.now(dt_timezone.utc)
    camera.save(update_fields=['status', 'last_frame_at'])

    assignments = ModelAssignment.objects.filter(camera=camera, enabled=True).select_related('model')
    saved = 0
    for assignment in assignments:
        try:
            adapter = _get_cached_adapter(assignment.model.name)
            detections = adapter.run(frame)
        except Exception as e:
            continue  # one bad model shouldn't block others

        for d in detections:
            Detection.objects.create(
                camera=camera,
                model=assignment.model,
                event_type=d['event_type'],
                confidence=d['confidence'],
                bbox=d['bbox'],
                timestamp=datetime.now(dt_timezone.utc),
            )
            saved += 1

    return f"Camera {camera_id}: {saved} detections saved"


@shared_task
def check_all_cameras():
    camera_ids = list(Camera.objects.values_list('id', flat=True))
    for cid in camera_ids:
        run_inference.delay(cid)
    return f"Queued {len(camera_ids)} cameras"