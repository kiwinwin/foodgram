import json
import os
import psycopg2
from django.conf import settings
from django.core.management import BaseCommand


json_f = "tags.json"


class Command(BaseCommand):
    """For importing tags data into database."""

    def handle(self, *args, **kwargs):
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'django'),
            host=os.getenv('DB_HOST', ''),
            user=os.getenv('POSTGRES_USER', 'django'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432)
            )
        with open(f"{settings.BASE_DIR}/data/{json_f}", 'r', encoding="utf-8") as json_file:
            data = json.load(json_file)
        self.import_generic(conn, data)
        self.stdout.write(self.style.SUCCESS("Данные тегов загружены."))

    def import_generic(self, conn, data):
        cursor = conn.cursor()
        for item in data:
            cursor.execute("INSERT INTO foodgram_tag (name, slug) VALUES (%s, %s)", (item["name"], item["slug"]))
        conn.commit()
        cursor.close()
        conn.close()