from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CartViewSet, CommentViewSet, DownloadShoppingCart,
                    IngredientViewSet, RecipeViewSet, SubscriptionsViewSet,
                    TagViewSet, UserViewSet)

v1_router = DefaultRouter()
v1_router.register('users', UserViewSet, basename='users'),
v1_router.register('ingredients', IngredientViewSet,
                   basename='ingredients'),
v1_router.register('recipes', RecipeViewSet,
                   basename='recipes'),
v1_router.register('tags', TagViewSet,
                   basename='tags'),
v1_router.register(
    r'recipes/(?P<recipes_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
),

auth_urls = [
    path('', include('djoser.urls.authtoken')),
]
urlpatterns = [
    path('users/subscriptions/',
         SubscriptionsViewSet.as_view({'get': 'list'}),
         name='subscribtions'),
    # path('recipes/<int:recipe_id>/favorite/',
    #      AddToFavorite.as_view(),
    #      name='favorite'),
    # path('recipes/<int:recipe_id>/favorite/',
    #      FavouriteViewSet.as_view({'get': 'create',
    #                                'delete': 'destroy'}),
    #      name='favorite'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         CartViewSet.as_view({'get': 'create',
                              'delete': 'destroy'}),
         name='shopping_cart'),
    path('recipes/download_shopping_cart/',
         DownloadShoppingCart.as_view(),
         name='shopping_cart_list'),
    path('users/<int:author_id>/subscribe/',
         SubscriptionsViewSet.as_view({'get': 'create',
                                       'delete': 'destroy'}),
         name='subscribe'),
    path('', include(v1_router.urls)),
    path('auth/', include(auth_urls)),
]
