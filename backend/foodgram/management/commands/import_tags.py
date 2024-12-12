from foodgram_project.base_import import BaseImport


class Command(BaseImport):
    """For importing tags data into database."""

    message = "Данные тегов загружены."
    command = "INSERT INTO foodgram_tag (name, slug) VALUES (%s, %s)"
    json_f = "tags.json"
