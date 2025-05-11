from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from profiles.serializers import (
    UserSerializer,
    UserCreateSerializer,
    AvatarUploadSerializer,
    SetPasswordSerializer,
)
from profiles.models import Follow, User
from recipes.models import (
    Recipe,
    ShoppingCart,
    Favorite,
    Ingredient,
)
from recipes.serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    RecipeShortSerializer,
    IngredientSerializer,
    FollowSerializer,
)
from .paginations import CustomPagination
from .permissions import OwnerOrReadOnly
from .filters import RecipeFilter, IngredientFilter
from .utils import generate_cart_text


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        return self.update_avatar(request) if request.method == "PUT" \
            else self.delete_avatar(request)

    def update_avatar(self, request):
        user = request.user
        serializer = AvatarUploadSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        recipes_limit = request.query_params.get('recipes_limit')

        queryset = User.objects.filter(following__user=user) \
            .annotate(recipes_count=Count('recipe'))
        page = self.paginate_queryset(queryset)

        context = self.get_serializer_context()
        context['recipes_limit'] = recipes_limit

        serializer = FollowSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        if author == user or \
                Follow.objects.filter(user=user, following=author).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(user=user, following=author)

        serializer = FollowSerializer(
            author,
            context=self._get_follow_context(request),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        follow = Follow.objects.filter(user=user, following=author)
        if not follow.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(
                    serializer.validated_data['current_password']):
                return Response(
                    {'current_password': ['Неверный пароль.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_follow_context(self, request):
        return {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        }


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = [OwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorited_ids'] = set(
                Favorite.objects.filter(user=user)
                .values_list('recipe_id', flat=True)
            )
            context['shopping_cart_ids'] = set(
                ShoppingCart.objects.filter(user=user)
                .values_list('recipe_id', flat=True)
            )
        else:
            context['favorited_ids'] = set()
            context['shopping_cart_ids'] = set()
        return context

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_id = format(recipe.id, 'x')
        short_path = reverse('api:short-link', kwargs={'short_id': short_id})
        full_url = request.build_absolute_uri(short_path)
        return Response({'short-link': full_url}, status=status.HTTP_200_OK)

    def _handle_add_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    def _handle_remove_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._handle_add_relation(request, Favorite)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self._handle_remove_relation(request, Favorite)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_add_relation(request, ShoppingCart)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._handle_remove_relation(request, ShoppingCart)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user

        items = ShoppingCart.objects.filter(user=user) \
            .select_related('recipe')

        if not items.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        content = generate_cart_text(items)
        response = HttpResponse(content, content_type='text/plain')
        filename = '"shopping_cart.txt"'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


def short_link_redirect(request, short_id):
    try:
        recipe_id = int(short_id, 16)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return HttpResponseRedirect(f'/recipes/{recipe.id}/')
    except (ValueError, Http404):
        return HttpResponseRedirect('/404')
