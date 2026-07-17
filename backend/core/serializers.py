from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework import serializers as drf_serializers
from .models import Camera
from .models import Detection
from .models import ModelMeta, ModelAssignment

class ModelMetaSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = ModelMeta
        fields = ['id', 'name', 'version', 'description']

class ModelAssignmentSerializer(drf_serializers.ModelSerializer):
    model_name = drf_serializers.CharField(source='model.name', read_only=True)
    class Meta:
        model = ModelAssignment
        fields = ['id', 'camera', 'model', 'model_name', 'enabled']

class DetectionSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = ['id', 'camera', 'model', 'event_type', 'confidence', 'bbox', 'frame_reference', 'timestamp']

        
User = get_user_model()

class CameraSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'name', 'rtsp_url', 'status', 'owner', 'last_frame_at', 'created_at']
        read_only_fields = ['owner', 'status', 'last_frame_at', 'created_at']


class CustomRegisterSerializer(RegisterSerializer):
    username = None

    def get_cleaned_data(self):
        return {
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'email': self.validated_data.get('email', ''),
        }


class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Unable to log in with provided credentials.')
        user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials.')
        attrs['user'] = user
        return attrs