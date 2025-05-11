from rest_framework import serializers
from foodgram_backend.image_field import Base64ImageField
from profiles.models import User
from .models import (
    Recipe,
    Ingredient,
    IngredientInRecipe,
    Favorite,
    ShoppingCart
)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id', 'name',
            'measurement_unit', 'amount',
        )


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    amount = serializers.IntegerField(
        min_value=1,
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id', 'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(
        read_only=True,
    )
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image',
            'text', 'cooking_time', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
        )

    def get_author(self, obj):
        from profiles.serializers import UserSerializer
        return UserSerializer(obj.author, context=self.context).data

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj) \
            .select_related('ingredient')
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        return obj.id in self.context.get('favorited_ids', set())

    def get_is_in_shopping_cart(self, obj):
        return obj.id in self.context.get('shopping_cart_ids', set())


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer(
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'text',
            'cooking_time', 'ingredients',
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError()
        ids = [item['ingredient'].id for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError()
        return ingredients

    def create_ingredients(self, recipe, ingredients):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.get('ingredients')

        if ingredients_data is not None:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            instance.ingredient_amounts.all().delete()
            self.create_ingredients(instance, ingredients_data)
            return instance
        else:
            raise serializers.ValidationError()

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time',
        )


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and \
            obj.follower.filter(user=user).exists()

    def get_recipes(self, obj):
        limit = self.context.get('recipes_limit')

        recipes = Recipe.objects.filter(author=obj)
        if limit is not None and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
