from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'
    MODER = 'moderator'
    USER_ROLES = [
        (USER, 'user'),
        (MODER, 'moderator'),
        (ADMIN, 'admin'),
    ]
    email = models.EmailField(
        db_index=True,
        unique=True
    )
    first_name = models.CharField(
        max_length=255,
        blank=True
    )
    last_name = models.CharField(
        max_length=255,
        blank=True
    )
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=20,
        choices=USER_ROLES,
        default=USER
    )

    objects = UserManager()

    @property
    def is_moderator(self):
        return self.role == self.MODER

    @property
    def is_admin(self):
        terms = (self.role == self.ADMIN, self.is_staff, self.is_superuser)
        return any(terms)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def create_auth_token(sender, instance=None, created=False, **kwargs):
        if created:
            Token.objects.create(user=instance)


class Tag(models.Model):
    """Тэги."""
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text="Введите тег",
        unique=True,
    )
    color = ColorField(
        verbose_name="Цвет",
        help_text="Выберите цветовой HEX-код (пример: #49B64E)",
        default="#888888",
        max_length=200,
        validators=[
            RegexValidator(regex=r"#[0-9a-fA-F]{6}",
                           message="Цвет должен быть задан в "
                                   "формате hex-кода")],
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Ссылка',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str___(self):
        return self.name


class Ingredient(models.Model):
    """Ингридиенты."""
    name = models.CharField(
        verbose_name="Название",
        help_text="Введите название ингридиента",
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        help_text="Введите единицу измерения ингредиента",
        max_length=200,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """Рецепты."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        null=True,
        verbose_name='Изображение',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Введите описание рецепта',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингридиенты",
        help_text="Выберите ингридиенты",
        related_name='recipes',
        through="IngredientsAmount",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        help_text="Выберите теги",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления в минутах.",
        help_text="Введите время приготовления в минутах.",
        validators=[MinValueValidator(
            limit_value=1,
            message="Время приготовления должно быть не менее 1.")
        ]
    )
    who_likes_it = models.ManyToManyField(
        User,
        related_name='favourite_recipes',
        verbose_name='Кому понравилось',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:15]


class IngredientsAmount(models.Model):
    """Количество каждого ингридиента в рецепте."""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
        related_name="ingredient_amount"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="Ингредиент",
        help_text="Выберите ингредиент",
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        verbose_name="Количество",
        help_text="Введите количество",
        validators=[MinValueValidator(
            limit_value=1,
            message="Количество должно быть не менее 1.")
        ],
    )

    class Meta:
        verbose_name = "Ингридиент рецепта"
        verbose_name_plural = "Ингридиенты рецепта"
        constraints = [models.UniqueConstraint(
            fields=['ingredient', 'recipe'],
            name='unique_ingredient_in_recipe'
        ), ]

    def __str__(self):
        return f"{self.recipe} - {self.ingredient}"


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        help_text='Автор',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Подписчик',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'user'],
                name='unique_following')
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f"{self.author} - {self.user}"


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="favourites",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="favourites",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite')
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class Cart(models.Model):
    """список покупок """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="to_cart",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
        related_name="to_cart",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart')
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class Comment(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запись',
        help_text='Запись',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
        help_text='Автор',
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Введите текст комментария',
    )
    pub_date = models.DateTimeField(
        'Дата комментария',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return (f'Комментарий {self.text[:15]} от '
                f'{self.author} к {self.recipe}')
