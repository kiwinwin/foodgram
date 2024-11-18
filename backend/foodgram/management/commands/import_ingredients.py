import sqlite3
import json

from django.conf import settings

from django.core.management import BaseCommand

json_f = "ingredients.json"

#Ingredients.objects.all().delete()

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        conn = sqlite3.connect('db.sqlite3')
        with open(f"{settings.BASE_DIR}/data/{json_f}", 'r', encoding="utf-8") as json_file:
            data = json.load(json_file)
        self.import_generic(conn, data)
        
        self.stdout.write(self.style.SUCCESS(
            "Данные ингредиентов загружены."))

    def import_generic(self, conn, data):
        for item in data:
            conn.execute("INSERT INTO foodgram_ingredients (name, measurement_unit) VALUES (?, ?)", (item["name"], item["measurement_unit"]))
        conn.commit()
        conn.close()