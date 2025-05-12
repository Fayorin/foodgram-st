from rest_framework import serializers
from foodgram_backend.image_field import Base64ImageField
from profiles.models import User
from .models import (
    Dish,
    Product,
    Component,
    Bookmark,
    Basket
)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ComponentReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='product.id')
    title = serializers.ReadOnlyField(source='product.title')
    unit = serializers.ReadOnlyField(source='product.unit')

    class Meta:
        model = Component
        fields = (
            'id', 'title',
            'unit', 'quantity',
        )


class ComponentWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product'
    )
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = Component
        fields = ('id', 'quantity')


class DishReadSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_in_basket = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = (
            'id', 'creator', 'title', 'picture',
            'description', 'duration', 'ingredients',
            'is_bookmarked', 'is_in_basket',
        )

    def get_creator(self, obj):
        from profiles.serializers import UserSerializer
        return UserSerializer(obj.creator, context=self.context).data

    def get_ingredients(self, obj):
        components = Component.objects.filter(dish=obj).select_related('product')
        return ComponentReadSerializer(components, many=True).data

    def get_is_bookmarked(self, obj):
        return obj.id in self.context.get('bookmarked_ids', set())

    def get_is_in_basket(self, obj):
        return obj.id in self.context.get('basket_ids', set())


class DishWriteSerializer(serializers.ModelSerializer):
    ingredients = ComponentWriteSerializer(many=True)
    picture = Base64ImageField()

    class Meta:
        model = Dish
        fields = (
            'title', 'picture', 'description',
            'duration', 'ingredients',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один компонент.")
        ids = [item['product'].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Дублирующиеся ингредиенты.")
        return value

    def create_components(self, dish, components_data):
        Component.objects.bulk_create([
            Component(
                dish=dish,
                product=item['product'],
                quantity=item['quantity']
            ) for item in components_data
        ])

    def create(self, validated_data):
        components = validated_data.pop('ingredients')
        dish = Dish.objects.create(**validated_data)
        self.create_components(dish, components)
        return dish

    def update(self, instance, validated_data):
        components = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if components is not None:
            instance.components.all().delete()
            self.create_components(instance, components)

        return instance

    def to_representation(self, instance):
        return DishReadSerializer(instance, context=self.context).data


class DishShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ('id', 'title', 'picture', 'duration')


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    dishes = serializers.SerializerMethodField()
    total_dishes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'dishes',
            'total_dishes', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.follower.filter(user=user).exists()

    def get_dishes(self, obj):
        limit = self.context.get('recipes_limit')
        queryset = Dish.objects.filter(creator=obj)
        if limit and str(limit).isdigit():
            queryset = queryset[:int(limit)]
        return DishShortSerializer(queryset, many=True, context=self.context).data

    def get_total_dishes(self, obj):
        return obj.created_dishes.count()
