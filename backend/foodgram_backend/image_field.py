import base64
import imghdr
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

MAX_IMAGE_SIZE = 5 * 1024 * 1024


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file_data = base64.b64decode(imgstr)

            if len(file_data) > MAX_IMAGE_SIZE:
                raise serializers.ValidationError()

            file_name = f'{uuid.uuid4()}.{ext}'
            valid_image = imghdr.what(None, file_data)
            if not valid_image:
                raise serializers.ValidationError()

            return ContentFile(file_data, name=file_name)

        return super().to_internal_value(data)
