import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from PIL import Image
from io import BytesIO

MAX_IMAGE_SIZE = 3 * 1024 * 1024

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1].lower()

                if ext == 'jpeg':
                    ext = 'jpg'

                file_data = base64.b64decode(imgstr)
            except (ValueError, TypeError, base64.binascii.Error):
                raise serializers.ValidationError('Неверный формат base64 изображения.')

            if len(file_data) > MAX_IMAGE_SIZE:
                raise serializers.ValidationError('Размер изображения превышает 5MB.')

            try:
                image = Image.open(BytesIO(file_data))
                image.verify()
            except Exception:
                raise serializers.ValidationError('Загруженный файл не является изображением.')

            file_name = f'{uuid.uuid4()}.{ext}'
            return ContentFile(file_data, name=file_name)

        return super().to_internal_value(data)

