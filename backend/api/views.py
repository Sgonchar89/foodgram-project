import djoser
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import get_template
from django_filters.rest_framework import DjangoFilterBackend
from djoser import utils
from djoser.compat import get_user_email
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, RetrieveModelMixin)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wkhtmltopdf.views import PDFTemplateResponse

from .filters import IngredientFilter, RecipeFilter
from .models import (Cart, Favourite, Follow, Ingredient, IngredientsAmount,
                     Recipe, Tag, User)
from .permissions import IsAdministratorOrReadOnly, IsAuthorOrAdminOrModerator
from .serializers import (CartSerializer, CommentSerializer,
                          CustomUserSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, TagSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthorOrAdminOrModerator,
                          )
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    def get_serializer_class(self):
        if self.action == "set_password":
            if djoser.conf.settings.SET_PASSWORD_RETYPE:
                return djoser.conf.settings.SERIALIZERS.set_password_retype
            return djoser.conf.settings.SERIALIZERS.set_password
        return self.serializer_class

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(
            serializer.validated_data["new_password"])
        self.request.user.save()

        if djoser.conf.settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": self.request.user}
            to = [get_user_email(self.request.user)]
            (djoser.conf.settings.EMAIL.
             password_changed_confirmation(self.request, context).send(to))

        if djoser.conf.settings.LOGOUT_ON_PASSWORD_CHANGE:
            utils.logout_user(self.request)
        elif djoser.conf.settings.CREATE_SESSION_ON_LOGIN:
            update_session_auth_hash(self.request, self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdministratorOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (IsAuthorOrAdminOrModerator,
                          )
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'ingredients'
    ).all()
    pagination_class = PageNumberPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrAdminOrModerator,
                          )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['get', 'delete'],
        pagination_class=None,
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk,)
        like = recipe.favourites.filter(user=user)

        if request.method == 'GET' and not like:
            serializer = self.get_serializer(recipe)
            Favourite.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE' and like:
            serializer = self.get_serializer(recipe)
            Favourite.objects.get(user=user, recipe=recipe).delete()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Action already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserRecipeConnectViewSet(viewsets.GenericViewSet, CreateModelMixin,
                               RetrieveModelMixin,
                               DestroyModelMixin):
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        data["user"] = request.user.id
        data["recipe"] = kwargs.get("recipe_id")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(self.Meta.model,
                                     user=request.user.id,
                                     recipe=kwargs.get("recipe_id"))
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = Follow.objects.all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CustomUserSerializer
        return FollowSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(follower__author=user).order_by("id")

    def create(self, request, *args, **kwargs):
        data = request.data
        data["author"] = request.user.id
        data["user"] = kwargs.get("author_id")

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(Follow,
                                     author=request.user.id,
                                     user=kwargs.get("author_id"))
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartViewSet(UserRecipeConnectViewSet,
                  ListModelMixin):
    queryset = Cart.objects.order_by("-recipe__pub_date")
    serializer_class = CartSerializer

    class Meta:
        model = Cart

    def get_purchases(self, request):
        ingredients = IngredientsAmount.objects.filter(
            recipe__to_cart__user=request.user.id
        ).select_related('ingredient')
        purchases = ingredients.values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        return purchases

    def list(self, request, *args, **kwargs):
        template = get_template("shopping_cart.html")
        responce = PDFTemplateResponse(
            request=request,
            template=template,
            filename="shopping_cart.pdf",
            context={"purchases": self.get_purchases(request)},
            show_content_in_browser=False,
            cmd_options={'margin-top': 50, },
        )
        return responce


class DownloadShoppingCart(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ingredients = IngredientsAmount.objects.filter(
            recipe__to_cart__user=request.user.id
        ).select_related('ingredient')
        purchases = ingredients.values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        wishlist = []
        for item in purchases:
            wishlist.append(f'{item["ingredient__name"]} - {item["amount"]} '
                            f'{item["ingredient__measurement_unit"]} \n')

        response = HttpResponse(wishlist, 'Content-Type: text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="wishlist.txt"')
        return response


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrAdminOrModerator,
                          )
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return get_object_or_404(
            Recipe.objects.filter(title_id=self.kwargs.get('title_id')),
            pk=self.kwargs.get('review_id')
        ).comments.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=get_object_or_404(
                Recipe.objects.filter(title_id=self.kwargs.get('title_id')),
                pk=self.kwargs.get('review_id'))
        )
