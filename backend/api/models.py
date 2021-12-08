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
    def create_auth_token(self, sender, instance=None, created=False,
                          **kwargs):
        if created:
            Token.objects.create(user=instance)


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text="Enter tag name",
        unique=True,
    )
    color = ColorField(
        verbose_name="Color",
        help_text="Select the HEX color code (example: #49B64E)",
        default="#888888",
        max_length=200,
        validators=[
            RegexValidator(regex=r"#[0-9a-fA-F]{6}",
                           message="The color must be specified "
                                   "in HEX-code format")],
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Link',
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str___(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name="Name",
        help_text="Enter ingredient name",
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name="Measurement unit",
        help_text="Enter the measurement unit of the ingredient",
        max_length=200,
    )

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        null=True,
        verbose_name='Image',
    )
    text = models.TextField(
        verbose_name='Description',
        help_text='Enter recipe description',
    )
    pub_date = models.DateTimeField(
        'Publication date',
        auto_now_add=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ingredients",
        help_text="Select ingredients",
        related_name='recipes',
        through="IngredientsAmount",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Tags",
        help_text="Select tags",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Cooking time in minutes.",
        help_text="Enter cooking time in minutes.",
        validators=[MinValueValidator(
            limit_value=1,
            message="Cooking time should be at least 1.")
        ]
    )
    who_likes_it = models.ManyToManyField(
        User,
        related_name='favourite_recipes',
        verbose_name='Who liked it',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.name[:15]


class IngredientsAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Recipe",
        help_text="Select recipe",
        on_delete=models.CASCADE,
        related_name="ingredient_amount"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="Ingredient",
        help_text="Select ingredients",
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        verbose_name="Amount",
        help_text="Enter the amount",
        validators=[MinValueValidator(
            limit_value=1,
            message="Quantity must be at least 1.")
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
        verbose_name='Author',
        help_text='Author',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Follower',
        help_text='Follower',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'user'],
                name='unique_following')
        ]
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.author} - {self.user}"


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="User",
        related_name="favourites",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Recipe",
        related_name="favourites",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite')
        ]
        verbose_name = "Favourite"
        verbose_name_plural = "Favourites"

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="User",
        related_name="to_cart",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Recipe",
        help_text="Select a recipe",
        on_delete=models.CASCADE,
        related_name="to_cart",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart')
        ]
        verbose_name = "Shopping cart"
        verbose_name_plural = "Shopping carts"

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class Comment(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Recipe',
        help_text='Select a recipe',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Author',
        help_text='Select an author',
    )
    text = models.TextField(
        verbose_name='Comment',
        help_text='Enter your comment',
    )
    pub_date = models.DateTimeField(
        'Comment date',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return (f'Комментарий {self.text[:15]} от '
                f'{self.author} к {self.recipe}')
