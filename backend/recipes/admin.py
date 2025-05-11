from django.contrib import admin
from django.db.models import Count

from .models import (
    Ingredient,
    Recipe,
    IngredientInRecipe,
    Favorite,
    ShoppingCart,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'favorites_count'
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
    )
    inlines = [IngredientInRecipeInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(fav_count=Count('favorited_by'))

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        return obj.fav_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )
