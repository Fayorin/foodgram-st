from django_filters import rest_framework
from recipes.models import Recipe, Ingredient


class RecipeFilter(rest_framework.FilterSet):
    is_favorited = rest_framework.filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = rest_framework.filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(in_carts__user=user)
        return queryset


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ['name']
