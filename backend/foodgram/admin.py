from django.contrib import admin

from foodgram.models import (Ingredients,
                             Tags,)


class TagsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug",)
    empty_value_display = "-пусто-"


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit",)
    search_fields = ("name",)
    empty_value_display = "-пусто-"


admin.site.register(Tags, TagsAdmin)
admin.site.register(Ingredients, IngredientsAdmin)