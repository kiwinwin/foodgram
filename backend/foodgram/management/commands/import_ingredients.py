from foodgram_project.base_import import BaseImport


class Command(BaseImport):
    """For importing ingredients data into database."""

    message = "Данные ингредиентов загружены."
    command = "INSERT INTO foodgram_ingredient \
        (name, measurement_unit) VALUES (%s, %s)"
    json_f = "ingredients.json"
