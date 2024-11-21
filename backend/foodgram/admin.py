from django.contrib import admin
from foodgram.models import (Ingredients, Recipe, Tags, RecipeTags, RecipeIngredients)


'''class TagsInline(admin.TabularInline):
    model = RecipeTags
    extra = 1


class IngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1'''


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit",)
    search_fields = ("name",)
    empty_value_display = "-пусто-"


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    search_fields = ('name', 'author',)
    list_filter = ('tags', )
    #inlines = (TagsInline, IngredientsInline)
    empty_value_display = "-пусто-"


class TagsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug",)
    empty_value_display = "-пусто-"


admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tags, TagsAdmin)
