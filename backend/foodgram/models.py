from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    follows = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  related_name='follows',
                                  null=True, blank=True,)

    class Meta:

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
    
    def __str__(self):
        return {self.user}

class Tags(models.Model):
    name = models.CharField('Название тега',
                            max_length=32,
                            unique=True)
    slug = models.SlugField('Слаг тега',
                            max_length=32,
                            unique=True)
    
    class Meta:
        ordering = ('id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    
    name = models.CharField('Название ингредиента',
                            max_length=128)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=8)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name }{self.measurement_unit}'


class IngredientsAmount(models.Model):
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE,)
    amount = models.IntegerField(validators=[
        MinValueValidator(1)
    ])
    class Meta:
        ordering = ('id',)


class Recipe(models.Model):
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',)
    name = models.CharField('Название',
                            max_length=256)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',)
    tags = models.ManyToManyField(
        Tags,
        through='RecipeTags',)
    ingredients = models.ManyToManyField(
        IngredientsAmount,
        through='RecipeIngredients',
        )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',)
    
    #REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']
    
    class Meta:
        ordering = ["name"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeTags(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE)


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        IngredientsAmount,
        on_delete=models.CASCADE)


class FavoriteRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE)


class IncartRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE)