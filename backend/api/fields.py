import base64

from django.core.files.base import ContentFile
from rest_framework import serializers


class ImageField(serializers.Field):

    def to_representation(self, value):
        return value.url

    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name='temp.' + ext)