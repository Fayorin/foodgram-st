from django.contrib import admin
from django.db.models import Count

from .models import (
    Product,
    Dish,
    Component,
    Bookmark,
    Basket,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'unit',
    )
    search_fields = (
        'title',
    )


class ComponentInline(admin.TabularInline):
    model = Component
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'creator',
        'bookmarked_total',
    )
    search_fields = (
        'title',
        'creator__username',
        'creator__email',
    )
    inlines = [ComponentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(bookmark_count=Count('bookmarked_by'))

    @admin.display(description='В избранном раз')
    def bookmarked_total(self, obj):
        return obj.bookmark_count


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'dish',
    )


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'dish',
    )


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = (
        'dish',
        'product',
        'quantity',
    )
