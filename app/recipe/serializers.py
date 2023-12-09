from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_field = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'price', 'time_minutes', 'link', 'tags']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        user = self.context.get('request').user
        for tag in tags:
            tag_obj, create = Tag.objects.get_or_create(
                user=user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', [])
        recipe = super().update(instance,validated_data)
        if tags is not None:
            recipe.tags.all().delete()
            self._get_or_create_tags(tags, recipe)
        return recipe


class DetailRecipeSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_field = ['id']