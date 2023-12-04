from rest_framework import serializers
from core.models import Recipe,Tag


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

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        user = self.context.get('request').user
        for tag in tags:
            tag_obj, create = Tag.objects.get_or_create(
                user=user,
                **tag,
            )
            recipe.tags.add(tag_obj)
        return recipe
        

class DetailRecipeSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
