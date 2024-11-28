from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    follows = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='follows',
        null=True, blank=True,)

    class Meta:

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


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
        return self.slug


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
        return f'{self.name} {self.measurement_unit}'


class IngredientsAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Название ингредиента',)
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1),],)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    
    def __str__(self):
        return f'{self.ingredient.name} {self.amount}'

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
        through='RecipeTags',
        verbose_name='Теги')
    ingredients = models.ManyToManyField(
        IngredientsAmount,
        through='RecipeIngredients',
        verbose_name='Ингредиенты')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", )
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeTags(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        verbose_name='Тег')
    
    class Meta:
        ordering = ('id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
    
    def __str__(self):
        return self.tag.slug


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        IngredientsAmount,
        on_delete=models.CASCADE)
    
    class Meta:
        ordering = ('id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
    
    def __str__(self):
        return self.ingredient.ingredient.name
        

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