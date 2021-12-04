import djoser.serializers
import requests.exceptions
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from djoser.conf import settings
from rest_framework.generics import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField)
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.views import exceptions

from .models import (Cart, Comment, Favourite, Follow, Ingredient,
                     IngredientsAmount, Recipe, Tag, User)


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    id = serializers.IntegerField(required=False)
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'bio',
            'email',
            'role',
            'is_subscribed',
            'password'
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        try:
            author = self.context.get("request").user
            if not author or author.is_anonymous:
                return False
            return Follow.objects.filter(author=author, user=obj).exists()
        except requests.exceptions.RequestException as exception:
            return exception.response

    def get_recipes(self, obj):
        try:
            recipes = Recipe.objects.filter(author=obj).order_by("-pub_date")
            params = self.context.get("request").query_params
            recipes_limit = params.get("recipes_limit")
            if not params:
                return False
            elif recipes_limit is not None:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
        except requests.exceptions.RequestException as exception:
            return exception.response

        serializer = RecipeReadShortSerializer(
            recipes,
            many=True,
            context={"request": self.context.get("request")}
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        try:
            user = self.context["request"].user or self.user
            assert user is not None

            try:
                validate_password(attrs["new_password"], user)
            except django_exceptions.ValidationError as e:
                raise serializers.ValidationError(
                    {"new_password": list(e.messages)})
            return super().validate(attrs)
        except requests.exceptions.RequestException as exception:
            return exception.response


class PasswordRetypeSerializer(PasswordSerializer):
    re_new_password = serializers.CharField(style={"input_type": "password"})

    default_error_messages = {
        "password_mismatch":
            settings.CONSTANTS.messages.PASSWORD_MISMATCH_ERROR
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["new_password"] == attrs["re_new_password"]:
            return attrs
        else:
            self.fail("password_mismatch")


class CurrentPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(style={"input_type": "password"})

    default_error_messages = {
        "invalid_password": settings.CONSTANTS.messages.INVALID_PASSWORD_ERROR
    }

    def validate_current_password(self, value):
        try:
            is_password_valid = self.context[
                "request"].user.check_password(value)
            if is_password_valid:
                return value
            else:
                self.fail("invalid_password")
        except requests.exceptions.RequestException as exception:
            return exception.response


class SetPasswordSerializer(PasswordSerializer, CurrentPasswordSerializer):
    pass


class SetPasswordRetypeSerializer(PasswordRetypeSerializer,
                                  CurrentPasswordSerializer):
    pass


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "color",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "measurement_unit",
        )

    def to_internal_value(self, data):
        try:
            ingredient = Ingredient.objects.get(id=data)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError({f"Ингредиента с id={data}"
                                               f" не существует."})
        return ingredient


class IngredientsRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = IngredientsAmount
        fields = ["id", "name", "amount", "measurement_unit"]

    def get_ingredients(self, obj):
        qs = IngredientsAmount.objects.filter(recipe=obj)
        return IngredientsRecipeReadSerializer(qs, many=True).data


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    image = serializers.SerializerMethodField('get_image')
    ingredients = serializers.SerializerMethodField('get_ingredients')
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "author", "name", "text", "ingredients", "tags",
                  "image", "cooking_time", "is_favorited",
                  "is_in_shopping_cart")

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Favourite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Cart.objects.filter(user=user, recipe=obj).exists()

    def get_ingredients(self, obj):
        ingredients = IngredientsAmount.objects.filter(recipe=obj)
        return IngredientsRecipeReadSerializer(ingredients, many=True).data

    def get_image(self, obj):
        request = self.context.get('request')
        photo_url = obj.image.url
        return request.build_absolute_uri(photo_url)


class IngredientsAmountSerializer(serializers.ModelSerializer):
    id = IngredientSerializer()

    class Meta:
        model = IngredientsAmount
        fields = ["id", "amount"]


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAmountSerializer(many=True)
    image = Base64ImageField(max_length=300, use_url=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        exclude = ["pub_date"]
        validators = [
            UniqueTogetherValidator(queryset=Recipe.objects.all(),
                                    fields=['ingredients', 'tags',
                                            'cooking_time'])
        ]

    def validate(self, data):
        data = super().validate(data)
        ingredients = data["ingredients"]
        ingredients_ids = [ingredient["id"] for ingredient in ingredients]
        if len(ingredients) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                {"detail": "Нельзя добавлять одни и те же ингредиенты"
                           " несколько раз."})
        for item in ingredients:
            if int(item['amount']) < 0:
                raise serializers.ValidationError(
                    {"detail": "Убедитесь, что значение количества"
                     "ингредиента больше 0"})
        tags = data['tags']
        existing_tags = {}
        for tag in tags:
            if tag in existing_tags:
                raise serializers.ValidationError(
                    {"detail": "Нельзя добавлять одни и те же теги"
                               " несколько раз."})
            existing_tags['tag'] = True
        return data

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError(
                'Введите целое число больше 0 для времени готовки'
            )
        return data

    def recipe_ingredients(self, validated_data, ingredients):
        data = ingredients
        recipe_ingredients = []
        for ingredient in data:
            recipe_ingredients.append(IngredientsAmount(
                recipe=validated_data,
                ingredient=ingredient["id"],
                amount=ingredient["amount"],
            ))
        IngredientsAmount.objects.bulk_create(recipe_ingredients)
        return validated_data

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        recipe = Recipe.objects.create(**validated_data,
                                       author=self.context["request"].user)
        recipe.tags.set(tags)
        return self.recipe_ingredients(recipe, ingredients)

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        super().update(instance, validated_data)
        instance.save()
        IngredientsAmount.objects.filter(recipe=instance).delete()
        instance.tags.set(tags)
        return self.recipe_ingredients(instance, ingredients)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={"request": self.context.get("request")}
        ).data


class RecipeReadShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]
        read_only_fields = ['name', 'image', 'cooking_time']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("author", "user")

    def to_representation(self, instance):
        return UserSerializer(
            instance.user,
            context={"request": self.context.get("request")}
        ).data


class FavouriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Favourite
        fields = ("user", "recipe", )

    def validate(self, data):
        user = self.context.get('request').user
        recipe_id = data['recipe'].id
# worthless
        if (self.context.get('request').method == 'GET'
                and Favourite.objects.filter(user=user,
                                            recipe__id=recipe_id).exists()):
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное')

        recipe = get_object_or_404(Recipe, id=recipe_id)

        if (self.context.get('request').method == 'DELETE'
                and not Favourite.objects.filter(
                    user=user,
                    recipe=recipe).exists()):
            raise serializers.ValidationError()

        return data

    def to_representation(self, instance):
        return {
            "id": instance.recipe.id,
            "name": instance.recipe.name,
            "image": instance.recipe.image.url,
            "cooking_time": instance.recipe.cooking_time,
        }




class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ("user", "recipe", )

    def to_representation(self, instance):
        return {
            "id": instance.recipe.id,
            "name": instance.recipe.name,
            "image": instance.recipe.image.url,
            "cooking_time": instance.recipe.cooking_time,
        }


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date',)
        model = Comment
        read_only_fields = ('review',)


class CustomUserSerializer(djoser.serializers.UserSerializer):
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name",
                  "is_subscribed", "recipes", "recipes_count"]

    def get_is_subscribed(self, obj):
        try:
            user = self.context.get("request").user
            if not user or user.is_anonymous:
                return False
            return Follow.objects.filter(user=user, author=obj).exists()
        except requests.exceptions.RequestException as exception:
            return exception.response

    def get_recipes(self, obj):
        try:
            recipes = Recipe.objects.filter(author=obj).order_by("-pub_date")

            params = self.context.get("request").query_params
            recipes_limit = params.get("recipes_limit")
            if not params:
                return False
            if recipes_limit is not None:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]

            serializer = RecipeReadShortSerializer(
                recipes,
                many=True,
                context={"request": self.context.get("request")}
            )
            return serializer.data
        except requests.exceptions.RequestException as exception:
            return exception.response

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
