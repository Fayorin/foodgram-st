from django_filters import rest_framework as filters
from recipes.models import Dish, Product


class DishFilter(filters.FilterSet):
    bookmarked = filters.BooleanFilter(method='filter_bookmarked')
    in_basket = filters.BooleanFilter(method='filter_in_basket')

    class Meta:
        model = Dish
        fields = ['creator', 'bookmarked', 'in_basket']

    def filter_bookmarked(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_in_basket(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and value:
            return queryset.filter(in_carts__user=user)
        return queryset


class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='title',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Product
        fields = ['name']
