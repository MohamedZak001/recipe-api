from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from recipe.serializers import (
    RecipeSerializer,
    DetailRecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeImageSerializer,
)
from core.models import Recipe, Tag, Ingredient

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of IDS to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of IDS to filter'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = DetailRecipeSerializer
    authentication_classes = [TokenAuthentication]
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, st):
        return [int(ch) for ch in st.split(',')]


    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tags_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_ids)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)
        return queryset.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0,1],
                description='Filter by items assigned to recipes',
            )
        ]
    )
)
class BaseRecipeRelatedView(mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        is_assigned = bool(int(
            self.request.query_params.get('assigned_only', 0)
        ))
        queryset = self.queryset
        if is_assigned:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).order_by('-name').distinct()

class TagViewSet(BaseRecipeRelatedView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeRelatedView):

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()

    