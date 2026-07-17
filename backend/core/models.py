from django.conf import settings
from django.db import models


class Camera(models.Model):
    STATUS_CHOICES = [
        ("online", "Online"),
        ("pending", "Pending"),
        ("offline", "Offline"),
    ]
    name = models.CharField(max_length=255)
    rtsp_url = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cameras")
    last_frame_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ModelMeta(models.Model):
    name = models.CharField(max_length=100, unique=True)   # e.g. "ppe", "theft"
    version = models.CharField(max_length=50, default="1.0")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} v{self.version}"
    

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)


class ModelAssignment(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="model_assignments")
    model = models.ForeignKey(ModelMeta, on_delete=models.CASCADE, related_name="assignments")
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ("camera", "model")


class Detection(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="detections")
    model = models.ForeignKey(ModelMeta, on_delete=models.CASCADE, related_name="detections")
    event_type = models.CharField(max_length=100)
    confidence = models.FloatField()
    bbox = models.JSONField()          # normalised [x, y, w, h]
    frame_reference = models.CharField(max_length=500, blank=True)  # path/URI to stored JPEG
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["camera", "timestamp"]),
            models.Index(fields=["camera", "model", "timestamp"]),
        ]


class KpiRollup(models.Model):
    WINDOW_CHOICES = [("1h", "1 Hour"), ("1d", "1 Day"), ("1w", "1 Week")]
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="kpi_rollups")
    model = models.ForeignKey(ModelMeta, on_delete=models.CASCADE, related_name="kpi_rollups")
    window = models.CharField(max_length=5, choices=WINDOW_CHOICES)
    window_start = models.DateTimeField()
    metrics = models.JSONField()   # e.g. {"compliance_pct": 92.3, "count": 14}

    class Meta:
        indexes = [models.Index(fields=["camera", "model", "window", "window_start"])]
        unique_together = ("camera", "model", "window", "window_start")