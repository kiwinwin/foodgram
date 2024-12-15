from .base_import import BaseImport

MESSAGE = "Данные ингредиентов загружены."
COMMAND = "INSERT INTO foodgram_ingredients \
    (name, measurement_unit) VALUES (?, ?)"
FILE = "ingredients.json"


class Command(BaseImport):
    """For importing ingredients data into database."""

    def __init__(self, message=MESSAGE,
                 command=COMMAND,
                 json_f=FILE, *args, **kwargs):
        super().__init__(self, message, command, json_f)
        self.message = message
        self.command = command
        self.json_f = json_f
