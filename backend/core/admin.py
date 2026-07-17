from django.contrib import admin
from .models import Camera, ModelMeta, ModelAssignment, Detection, KpiRollup
from .models import AuditLog

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'owner', 'last_frame_at', 'created_at']
    list_filter = ['status', 'owner']
    search_fields = ['name', 'rtsp_url']


admin.site.register(ModelMeta)
admin.site.register(ModelAssignment)
admin.site.register(Detection)
admin.site.register(KpiRollup)
admin.site.register(AuditLog)