import django_filters
from django.contrib.auth import get_user_model
from .models import Recipe, Ingredient, User
from django_filters.rest_framework import filters

User = get_user_model()


class RecipeFilter(django_filters.FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = filters.BooleanFilter(method='cart_filter')
    is_favorited = filters.BooleanFilter(method='favorite_filter')

    def cart_filter(self, queryset, name, value):
        if value:
            return queryset.filter(to_cart__user=self.request.user)
        if not value:
            return queryset.all()

    def favorite_filter(self, queryset, name, value):
        if value:
            return queryset.filter(favourites__user=self.request.user)
        if not value:
            return queryset.all()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='startswith',
                                     )
    class Meta:
        model = Ingredient
        fields = ('name',)
