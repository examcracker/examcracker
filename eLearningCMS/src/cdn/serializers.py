from rest_framework import serializers

"""Data serializer for uploading urls"""
class uploadURLSerializer(serializers.Serializer):
   url = serializers.URLField()
