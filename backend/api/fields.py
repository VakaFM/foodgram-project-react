import base64
import imghdr
import uuid
import tempfile

from rest_framework.serializers import ImageField
from django.core.files.uploadedfile import SimpleUploadedFile


class Base64ImageField(ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post
    data.
    It uses base64 for encoding and decoding the contents of the file.
    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268
    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        data = data.strip('data:image/')
        index = data.find(';')
        content_type = data[:index]
        data = data[index + 8:]
        image_data = base64.b64decode(data)
        filename = uuid.uuid4().hex
        with tempfile.TemporaryFile() as image:
            image.write(image_data)
            image.seek(0)
            file = SimpleUploadedFile(
                name=f'{filename}.{content_type}',
                content=image.read(),
                content_type=f'image/{content_type}'
            )
        return super().to_internal_value(file)

    def get_file_extension(self, file_name, decoded_file):

        extension = imghdr.what(file_name, decoded_file)

        return "jpg" if extension == "jpeg" else extension
