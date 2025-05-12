from django.db import models
from django.core.validators import MinValueValidator
from profiles.models import User


class Product(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name="Ингредиент",
    )
    unit = models.CharField(
        max_length=10,
        verbose_name="Мера",
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.unit})"


class Dish(models.Model):
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_dishes',
        verbose_name='Создатель',
    )
    title = models.CharField(
        max_length=256,
        verbose_name='Название блюда',
    )
    picture = models.ImageField(
        upload_to='dishes/',
        verbose_name='Картинка',
    )
    description = models.TextField(
        verbose_name="Инструкция",
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Время готовки (мин)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено"
    )

    class Meta:
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Component(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name="Блюдо",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='used_in',
        verbose_name="Продукт",
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Объём",
    )

    class Meta:
        verbose_name = "Компонент блюда"
        verbose_name_plural = "Компоненты блюд"
        unique_together = ('dish', 'product')


class Bookmark(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name="Аккаунт",
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='bookmarked_by',
        verbose_name="Блюдо",
    )

    class Meta:
        verbose_name = "Закладка"
        verbose_name_plural = "Закладки"


class Basket(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='baskets',
        verbose_name="Покупатель",
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='in_baskets',
        verbose_name="Блюдо",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
    
