# Create your views here.
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from abstract.views import (
    SimpleCreateGenericView,
    SimpleDeleteOneGenericView,
    SimpleGetDetailGenericView,
    SimpleGetListGenericView,
    SimplePartialUpdateGenericView,
    SimpleUpdateGenericView,
)
from Castellum.enums import Roles
from Castellum.permissions import IsOrganization
from content.arch.managers import (
    AnswerCourseContentQuestionManager,
    AnswerQuestionManager,
    CompleteContentManager,
    ContentDetailManager,
)
from content.models import Content
from content.serializers import ContentSerializer
from courses.serializers import CourseListSerializer, CourseSerializer
from quiz.models.question import Question
from users.models import UserCourse

from .arch.managers import (
    AddContentManager,
    CompleteCourseManager,
    CreateCourseManager,
    PersonalCoursePerformanceManager,
    RemoveContentSerializer,
    RetakeCourseManager,
    StartCourseManager,
)
from .models import Course

# Create your views here.
# class CreateCourseView(SimpleCreateGenericView, SimpleGetListGenericView):
#     serializer_class = CreateCourseManager
#     permission_classes = [IsOrganization]


class CourseQuerySetHelper(generics.GenericAPIView):
    queryset = Course.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "course_id"

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


class CourseContentQuerySetHelper(CourseQuerySetHelper):
    def get_queryset(self):
        obj: Course = get_object_or_404(
            super().get_queryset(), id=self.kwargs.get("course_id")
        )
        self.kwargs["course"] = obj

        return obj.contents.all()

    def get_object(self):
        obj: Content = get_object_or_404(
            self.get_queryset(), id=self.kwargs.get("content_id")
        )
        self.kwargs["content"] = obj
        return obj


@extend_schema_view(
    get=extend_schema(
        summary="Get Course List",
        description="Get a list of all courses",
        parameters=[
            OpenApiParameter(
                name="learning_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by learning type",
            )
        ],
    )
)
class GetCourseListView(generics.ListAPIView, CourseQuerySetHelper):
    serializer_class = CourseListSerializer
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]

    def filter_queryset(self, queryset):
        learning_type = self.request.query_params.get("learning_type")
        if learning_type:
            queryset = queryset.filter(learning_type=learning_type)
        return super().filter_queryset(queryset)


@extend_schema_view(
    get=extend_schema(
        summary="Get Course Detail",
        description="Get the details of a course",
    )
)
class GetCourseDetailView(
    CourseQuerySetHelper,
    SimpleGetDetailGenericView,
):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Get Course Content List",
        description="Get a list of all contents in a course",
    )
)
class GetCourseContentListView(SimpleGetListGenericView, CourseContentQuerySetHelper):
    serializer_class = ContentSerializer
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Get Course Content Detail",
        description="Get the details of a content in a course",
    )
)
class GetCourseContentDetailView(
    SimpleGetDetailGenericView, CourseContentQuerySetHelper
):
    serializer_class = ContentDetailManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    patch=extend_schema(
        summary="Start Course",
        description="Start a course",
    )
)
class StartCourseView(SimplePartialUpdateGenericView, CourseQuerySetHelper):
    serializer_class = StartCourseManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .all()
            .exclude(users_attempted__user=self.request.user)
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Complete Course",
        description="Complete a course",
    )
)
class CompleteCourseView(SimplePartialUpdateGenericView, CourseQuerySetHelper):
    serializer_class = CompleteCourseManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    patch=extend_schema(
        summary="Complete Course Content",
        description="Complete a content in a course",
    )
)
class CompleteCourseContentView(
    SimplePartialUpdateGenericView, CourseContentQuerySetHelper
):
    serializer_class = CompleteContentManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    patch=extend_schema(
        summary="Answer Course Question",
        description="Answer a question in a content",
    )
)
class AnswerCourseContentQuestionView(
    SimpleUpdateGenericView, CourseContentQuerySetHelper
):
    serializer_class = AnswerCourseContentQuestionManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]

    def get_object(self):
        content: Content = super().get_object()
        obj: Question = get_object_or_404(
            content.questions, id=self.kwargs.get("question_id")
        )
        self.kwargs["question"] = obj
        return obj


@extend_schema_view(
    patch=extend_schema(
        summary="Retake Course",
        description="Retake a course",
    )
)
class RetakeCourseView(SimplePartialUpdateGenericView, CourseQuerySetHelper):
    serializer_class = RetakeCourseManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Get Personal Course Performance",
        description="Get user performance in a course",
    )
)
class PersonalCoursePerformanceView(SimpleGetDetailGenericView, CourseQuerySetHelper):
    serializer_class = PersonalCoursePerformanceManager
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().all()


# class AddContentView(SimplePartialUpdateGenericView):
#     serializer_class = AddContentManager
#     lookup_field = "id"
#     queryset = Course.objects.all()
#     permission_classes = [IsOrganization]

#     def get_queryset(self):
#         return self.queryset.filter(organization=self.request.user)


# class RemoveContentView(SimplePartialUpdateGenericView):
#     serializer_class = RemoveContentSerializer
#     lookup_field = "id"
#     queryset = Course.objects.all()
#     permission_classes = [IsOrganization]

#     def get_queryset(self):
#         return self.queryset.filter(organization=self.request.user)
