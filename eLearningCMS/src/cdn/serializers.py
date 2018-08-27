from rest_framework import serializers
from .models import CdnSession

"""Data serializer for uploading urls"""
class uploadURLSerializer(serializers.Serializer):
   url = serializers.URLField()

class CdnSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CdnSession
        fields = '__all__'