from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from .models import (Cart, Comment, Follow, Ingredient, IngredientsAmount,
                     Recipe, Tag, User, Favourite)


@register(User)
class UserAdmin(ModelAdmin):
    list_display = ('email', 'username', 'role')
    search_fields = ('username',)
    empty_value_display = '-пусто-'


@register(Tag)
class TagAdmin(ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "slug")


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_filter = ("name",)
    empty_value_display = "-пусто-"


class IngredientsAmountInline(admin.TabularInline):
    model = IngredientsAmount
    extra = 1


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    search_fields = ("name", "text")
    list_filter = ("author", "name", "tags")
    list_display = ("name", "author")
    inlines = [IngredientsAmountInline]


@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ("author", "user")
    search_fields = ("author",)
    empty_value_display = "-пусто-"


@register(Favourite)
class FavouriteAdmin(ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("recipe",)
    empty_value_display = "-пусто-"


@register(Cart)
class CartAdmin(ModelAdmin):
    search_fields = ("user",)
    list_display = ("user", "recipe")


@register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("recipe", "author", "text", "pub_date")
    search_fields = ("text",)
    empty_value_display = "-пусто-"
