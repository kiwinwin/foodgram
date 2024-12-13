import json
import os

import psycopg2
from django.conf import settings
from django.core.management import BaseCommand


class BaseImport(BaseCommand):

    def __init__(self, message, command, json_f, *args, **kwargs):
        super().__init__()
        self.message = message
        self.command = command
        self.json_f = json_f

    def handle(self, *args, **kwargs):

        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "django"),
            host=os.getenv("DB_HOST", ""),
            user=os.getenv("POSTGRES_USER", "django"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            port=os.getenv("DB_PORT", 5432))
        with open(f"{settings.BASE_DIR}/data/{self.json_f}", "r",
                  encoding="utf-8") as json_file:
            data = json.load(json_file)
        self.import_generic(conn, data)
        self.stdout.write(
            self.style.SUCCESS(self.message))

    def import_generic(self, conn, data):

        cursor = conn.cursor()
        for item in data:
            cursor.execute(self.command, tuple(item.values()))
        conn.commit()
        cursor.close()
        conn.close()
