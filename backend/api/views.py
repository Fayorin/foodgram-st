from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.decorators import action
from profiles.serializers import (
    UserSerializer,
    UserCreateSerializer,
    AvatarUploadSerializer,
    SetPasswordSerializer,
)
from profiles.models import Follow, User
from recipes.models import Dish, Basket, Bookmark, Ingredient
from recipes.serializers import (
    DishSerializer,
    DishCreateSerializer,
    DishShortSerializer,
    IngredientSerializer,
    FollowSerializer,
)
from .paginations import CustomPagination
from .permissions import OwnerOrReadOnly
from .filters import DishFilter, IngredientFilter
from .utils import generate_cart_text


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path="me")
    def current_user(self, request):
        serializer = self.get_serializer(request.user, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], permission_classes=[IsAuthenticated], url_path='me/avatar')
    def manage_avatar(self, request):
        return self.put_avatar(request) if request.method == "PUT" else self.remove_avatar(request)

    def put_avatar(self, request):
        user = request.user
        serializer = AvatarUploadSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({"avatar": avatar_url}, status=200)
        return Response(serializer.errors, status=400)

    def remove_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response({}, status=204)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = User.objects.filter(following__user=user).annotate(recipes_count=Count('recipe'))
        page = self.paginate_queryset(queryset)
        context = self.build_follow_context(request)
        serializer = FollowSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        if author == user or Follow.objects.filter(user=user, following=author).exists():
            return Response({}, status=400)

        Follow.objects.create(user=user, following=author)
        serializer = FollowSerializer(author, context=self.build_follow_context(request))
        return Response(serializer.data, status=201)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()
        relation = Follow.objects.filter(user=user, following=author)

        if not relation.exists():
            return Response({}, status=400)

        relation.delete()
        return Response({}, status=204)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='set_password')
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['current_password']):
                return Response({'current_password': ['Неверный пароль.']}, status=400)

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({}, status=204)
        return Response(serializer.errors, status=400)

    def build_follow_context(self, request):
        return {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        }


class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    pagination_class = CustomPagination
    permission_classes = [OwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DishFilter

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return DishCreateSerializer
        return DishSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        favorites = Bookmark.objects.filter(user=user).values_list('recipe_id', flat=True) if user.is_authenticated else []
        shopping = Basket.objects.filter(user=user).values_list('recipe_id', flat=True) if user.is_authenticated else []
        context.update({
            'favorited_ids': set(favorites),
            'shopping_cart_ids': set(shopping),
        })
        return context

    @action(detail=True, methods=['get'], url_path='get-link')
    def shorten_link(self, request, pk=None):
        recipe = self.get_object()
        short_id = format(recipe.id, 'x')
        short_path = reverse('api:short-link', kwargs={'short_id': short_id})
        full_url = request.build_absolute_uri(short_path)
        return Response({'short-link': full_url}, status=200)

    def add_user_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        if model.objects.filter(user=user, recipe=recipe).first():
            return Response({}, status=400)
        model.objects.create(user=user, recipe=recipe)
        return Response(DishShortSerializer(recipe).data, status=201)

    def remove_user_relation(self, request, model):
        recipe = self.get_object()
        user = request.user
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response({}, status=400)
        relation.delete()
        return Response({}, status=204)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.add_user_relation(request, Bookmark)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self.remove_user_relation(request, Bookmark)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.add_user_relation(request, Basket)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self.remove_user_relation(request, Basket)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_shopping_list(self, request):
        user = request.user
        items = Basket.objects.filter(user=user).select_related('recipe')
        if not items.exists():
            return Response({}, status=400)
        content = generate_cart_text(items)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


def short_link_redirect(request, short_id):
    try:
        recipe_id = int(short_id, 16)
        recipe = get_object_or_404(Dish, id=recipe_id)
        return HttpResponseRedirect(f'/recipes/{recipe.id}/')
    except (ValueError, Http404):
        return HttpResponseRedirect('/404')
