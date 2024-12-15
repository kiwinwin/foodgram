from .base_import import BaseImport

MESSAGE = "Данные тегов загружены."
COMMAND = "INSERT INTO foodgram_tag (name, slug) VALUES (%s, %s)"
FILE = "tags.json"


class Command(BaseImport):
    """For importing tags data into database."""

    def __init__(self, message=MESSAGE,
                 command=COMMAND,
                 json_f=FILE, *args, **kwargs):
        super().__init__(self, message, command, json_f)
        self.message = message
        self.command = command
        self.json_f = json_f
