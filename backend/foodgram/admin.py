from django.contrib import admin
from foodgram.models import (
    Ingredient,
    Recipe,
    Tag,
    RecipeTag,
    RecipeIngredient,
    IngredientAmount,
    FavoriteRecipe)


class TagsInline(admin.StackedInline):
    model = RecipeTag
    extra = 0


class IngredientsAmountAdmin(admin.ModelAdmin):

    list_display = ("ingredient", "amount",)


class RecipeIngredientsInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 0


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit",)
    search_fields = ("name",)
    empty_value_display = "-пусто-"


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', )
    readonly_fields = ['favorited_count']
    fieldsets = (
        (None, {
            'fields': [(
                'name',
                'image',
                'text',
                'cooking_time',),
                'favorited_count'],
                }),
                )
    search_fields = ('name', 'author__first_name',)
    list_filter = ('tags', )
    inlines = [TagsInline, RecipeIngredientsInline, ]
    empty_value_display = "-пусто-"

    @admin.display(description='Общее число добавлений в избранное')
    def favorited_count(self, obj):
        return FavoriteRecipe.objects.filter(recipe=obj.id).count()


class TagsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug",)
    empty_value_display = "-пусто-"


admin.site.register(Ingredient, IngredientsAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagsAdmin)
admin.site.register(IngredientAmount, IngredientsAmountAdmin)
