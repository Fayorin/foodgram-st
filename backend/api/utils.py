from collections import defaultdict


def generate_cart_text(items):
    ingredients_total = defaultdict(lambda: {'amount': 0, 'unit': ''})

    for item in items:
        recipe = item.recipe
        for ingredient in recipe.ingredient_amounts \
                .select_related('ingredient'):
            key = ingredient.ingredient.name
            unit = ingredient.ingredient.measurement_unit
            ingredients_total[key]['amount'] += ingredient.amount
            ingredients_total[key]['unit'] = unit

    lines = ["Список покупок:\n"]
    for name, data in sorted(ingredients_total.items()):
        lines.append(f"- {name} ({data['unit']}): {data['amount']}")

    cart_text = '\n'.join(lines)

    return cart_text
