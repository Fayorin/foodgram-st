import os
import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует данные из JSON файла в модель Ingredient'

    def handle(self, *args, **kwargs):
        data_folder = '/app/data'

        for filename in os.listdir(data_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(data_folder, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                    for item in data:
                        name = item['name']
                        measurement_unit = item['measurement_unit']

                        Ingredient.objects.create(
                            name=name,
                            measurement_unit=measurement_unit)

                self.stdout.write(self.style.SUCCESS(
                    f'Импорт данных из файла {filename} завершен'))
