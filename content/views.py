from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from abstract.views import (
    SimpleCreateGenericView,
    SimpleGetDetailGenericView,
    SimpleGetListGenericView,
    SimplePartialUpdateGenericView,
    SimpleUpdateGenericView,
)
from Castellum.enums import LearningTypes, Roles
from Castellum.permissions import IsOrganization

from .arch.managers import (
    AnswerQuestionManager,
    CompleteContentManager,
    ContentDetailManager,
    InitiateContentCreationManager,
)
from .models import Content
from .serializers import ContentDetailSerializer, ContentSerializer


class ContentQuerySetFilter(generics.GenericAPIView):
    queryset = Content.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        match user.role:
            case Roles.ORGANIZATION:
                queryset = self.queryset.filter(
                    Q(is_public=True) | Q(organization=user)
                )
            case Roles.EMPLOYEE:
                queryset = self.queryset.filter(
                    Q(is_public=True) | Q(organization=user.emp_profile.organization)
                )
            case _:
                queryset = self.queryset
        return queryset.all()


# @extend_schema_view(
#     get=extend_schema(
#         summary="Content List",
#         description="Get a list of all contents",
#         parameters=[
#             OpenApiParameter(
#                 name="learning_type",
#                 type=str,
#                 enum=LearningTypes.values,
#                 description="Filter by learning type",
#             )
#         ]
#     ),
# )
# class ContentView(SimpleGetListGenericView, ContentQuerySetFilter):
#     """ " Add "learning_type" query parameter to filter by learning type"""

#     pagination_class = LimitOffsetPagination
#     serializer_class = ContentSerializer
#     queryset = Content.objects.all()
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         learning_type = self.request.query_params.get("learning_type")
#         if learning_type and learning_type in LearningTypes.values:
#             queryset = queryset.filter(learning_type=learning_type)
#         return queryset.all()


@extend_schema_view(
    get=extend_schema(
        summary="Content Detail",
        description="Get the details of a content",
    ),
)
class ContentDetailView(SimpleGetDetailGenericView, ContentQuerySetFilter):
    serializer_class = ContentDetailManager
    queryset = Content.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("questions")


# class InitiateContentCreationView(SimpleCreateGenericView):
#     serializer_class = InitiateContentCreationManager
#     permission_classes = [IsOrganization]


# @extend_schema_view(
#     patch=extend_schema(
#         summary="Complete Content",
#         description="Mark content as completed",
#     ),
# )
# class CompleteContentView(SimplePartialUpdateGenericView, ContentQuerySetFilter):
#     serializer_class = CompleteContentManager
#     permission_classes = [IsAuthenticated]
#     queryset = Content.objects.all()
#     lookup_field = "id"

#     def get_queryset(self):
#         return super().get_queryset().prefetch_related("questions")


# class AnswerQuestionView(SimpleUpdateGenericView, ContentQuerySetFilter):
#     serializer_class = AnswerQuestionManager
#     permission_classes = [IsAuthenticated]
#     queryset = Content.objects.all()
#     lookup_field = "id"

#     def get_queryset(self):
#         return super().get_queryset().prefetch_related("questions")
