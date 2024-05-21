from django.urls import path

from .views import *

app_name = "courses"
urlpatterns = [
    # path("create/", CreateCourseView.as_view(), name="create-get-list"),
    path("", GetCourseListView.as_view(), name="get-list"),
    path("<uuid:course_id>/", GetCourseDetailView.as_view(), name="get-detail"),
    path("<uuid:course_id>/complete/", CompleteCourseView.as_view(), name="complete"),
    path("<uuid:course_id>/start/", StartCourseView.as_view(), name="start"),
    path("<uuid:course_id>/retake/", RetakeCourseView.as_view(), name="retake"),
    path(
        "<uuid:course_id>/performance/",
        PersonalCoursePerformanceView.as_view(),
        name="course-performance",
    ),
    path(
        "<uuid:course_id>/contents/",
        GetCourseContentListView.as_view(),
        name="get-course-contents",
    ),
    path(
        "<uuid:course_id>/contents/<uuid:content_id>/",
        GetCourseContentDetailView.as_view(),
        name="get-course-content",
    ),
    path(
        "<uuid:course_id>/contents/<uuid:content_id>/complete/",
        CompleteCourseContentView.as_view(),
        name="complete-course-content",
    ),
    path(
        "<uuid:course_id>/contents/<uuid:content_id>/questions/<uuid:question_id>/answer/",
        AnswerCourseContentQuestionView.as_view(),
        name="answer-course-content-question",
    ),
    # path("<uuid:course_id>/add-content/", AddContentView.as_view(), name="add-content"),
    # path(
    #     "<uuid:course_id>/remove-content/", RemoveContentView.as_view(), name="remove-content"
    # ),
]
