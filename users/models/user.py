import uuid
from functools import cached_property

import pendulum
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from abstract.models import BaseModel
from abstract.tasks import update_model_field
from abstract.toolboxes import UserEmailToolbox
from Castellum.celery import app
from Castellum.enums import Roles

from ..managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):

    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.ADMIN)

    last_login = models.DateTimeField(null=True, blank=True)

    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    completed_contents = models.ManyToManyField(
        "content.Content",
        related_name="completed_by",
        blank=True,
        through="CompletedContent",
    )

    token = models.CharField(max_length=256, blank=True, null=True)
    token_expiration_task_id = models.CharField(max_length=256, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    # @property
    # def full_name(self):
    #     return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.email

    def refresh(self):
        self.refresh_from_db()

    @cached_property
    def is_organization(self):
        return self.role == Roles.ORGANIZATION

    @cached_property
    def is_employee(self):
        return self.role == Roles.EMPLOYEE

    @property
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def receive_email(self, action: str):
        email_toolbox = UserEmailToolbox(self, action)
        email_toolbox.send_email()
        return

    def set_token(self):
        self.token = uuid.uuid4().hex
        self.save()
        return self.token

    def set_token(
        self,
    ):
        if self.token_expiration_task_id:
            app.control.revoke(self.token_expiration_task_id)
        self.token = str(uuid.uuid4().hex)
        token_background_task = update_model_field.apply_async(
            args=["User", self.id, "token", uuid.uuid4().hex],
            countdown=settings.USER_TOKEN_EXPIRY,
        )
        self.token_expiration_task_id = str(token_background_task.id)
        self.save()
        return self.token

    def convert_to_superuser(self):
        self.is_superuser = True
        self.is_staff = True
        self.is_admin = True
        self.is_active = True
        self.is_email_verified = True
        self.save()

    def start_course(self, course):
        from users.enums import ActivityType

        from .employee import Employee

        if self.role == Roles.EMPLOYEE:
            self.__class__ = Employee
            self.perform_activity(ActivityType.COURSE_STARTED)
        user_course, _ = UserCourse.objects.update_or_create(user=self, course=course)
        return user_course

    def complete_content(self, content, course, user_course):
        CompletedContent.objects.update_or_create(
            user=self,
            content=content,
            user_course=user_course,
            course=course,
            defaults={"completed_at": timezone.now()},
        )

    def complete_course_campaign_content(
        self, content, course, course_campaign, course_campaign_course
    ):
        from courses.models import CompletedCourseCampaignContent

        CompletedCourseCampaignContent.objects.update_or_create(
            employee=self,
            content=content,
            course=course,
            course_campaign=course_campaign,
            course_campaign_course=course_campaign_course,
            defaults={"completed_at": timezone.now()},
        )

    def answer_course_content_question(
        self, content, question, answers, course, user_course
    ):
        from content.serializers import ContentQuestionSerializer
        from content.tasks import update_completed_content
        from quiz.serializers import QuestionOptionSerializer

        answered_question, _ = AnsweredQuestion.objects.update_or_create(
            user=self,
            question=question,
            content=content,
            user_course=user_course,
            course=course,
            defaults={
                "question_options_snapshot": ContentQuestionSerializer(question).data,
                "answers_snapshot": QuestionOptionSerializer(answers, many=True).data,
            },
        )
        answered_question.answers.set(answers)
        update_completed_content.delay(self.id, content.id, course.id)
        return answered_question

    def answer_course_campaign_content_question(
        self,
        content,
        question,
        answers,
        course,
        course_campaign,
    ):
        from content.serializers import ContentQuestionSerializer
        from content.tasks import update_completed_course_campaign_content
        from courses.models import AnsweredCourseCampaignQuestion
        from quiz.serializers import QuestionOptionSerializer

        answered_question, _ = AnsweredCourseCampaignQuestion.objects.update_or_create(
            employee=self,
            question=question,
            content=content,
            course=course,
            course_campaign=course_campaign,
            defaults={
                "question_options_snapshot": ContentQuestionSerializer(question).data,
                "answers_snapshot": QuestionOptionSerializer(answers, many=True).data,
            },
        )
        answered_question.answers.set(answers)
        update_completed_course_campaign_content.delay(
            self.id, content.id, course_campaign.id, course.id
        )
        return answered_question

    def complete_course_campaign_course(
        self, course, course_campaign, employee_course_campaign
    ):
        from courses.models import CourseCampaignCourse

        CourseCampaignCourse.objects.update_or_create(
            employee=self,
            course=course,
            course_campaign=course_campaign,
            # employee_course_campaign=employee_course_campaign,
            defaults={"completed_at": timezone.now(), "is_completed": True},
        )


class Department(BaseModel):
    name = models.CharField(max_length=256)
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="departments"
    )
    security_score = models.FloatField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    @property
    def num_employees(self):
        return self.employee_profiles.count()


class UserCourse(BaseModel):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="attempted_courses"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="users_attempted"
    )
    started_at = models.DateTimeField(auto_now_add=True, editable=False)
    is_started = models.BooleanField(default=True, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.course} - {self.id}"

    class Meta:
        unique_together = ["user", "course"]

    @property
    def progress_rate(self):
        from django.db.models import Count

        user = self.user

        contents = self.course.contents.all()
        contents_with_questions = contents.annotate(
            num_questions=Count("questions")
        ).filter(num_questions__gt=0)
        available_questions = sum(
            [content.num_questions for content in contents_with_questions]
        )
        answered_questions = AnsweredQuestion.objects.filter(
            user=user, course=self.course
        ).count()
        contents_without_questions = contents.annotate(
            num_questions=Count("questions")
        ).filter(num_questions=0)
        completed_contents_without_questions = (
            self.course.completed_user_contents.filter(
                content__in=contents_without_questions,
                user=user,
                course=self.course,
            ).count()
        )
        total = available_questions + contents_without_questions.count()
        answered = answered_questions + completed_contents_without_questions
        return int((answered / total) * 100) if total else 0

    @property
    def completed_contents(self):
        course = self.course
        contents = course.contents.all()
        user = self.user
        completed_contents = user.completed_contents.filter(content__in=contents)
        return completed_contents

    def mark_as_completed(self):
        from ..enums import ActivityType
        from .employee import Employee

        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
        if self.user.role == Roles.EMPLOYEE:
            self.user.__class__ = Employee
            self.user.perform_activity(ActivityType.COURSE_COMPLETED)
        return

    def retake(self):
        # CompletedContent.objects.filter(user=self.user, course=self.course).delete()
        self.completed_contents.all().delete()
        self.started_at = timezone.now()
        self.is_completed = False
        self.completed_at = None
        self.save()
        AnsweredQuestion.objects.filter(user_course=self).delete()

    @cached_property
    def score(self):
        return self.get_score()

    def get_score(self):
        course = self.course
        contents = course.contents.all()
        user = self.user
        score = 0
        for content in contents:
            content_score = content.get_score(user)
            score += content_score
        return score

    @cached_property
    def contents(self):
        return self.course.contents.all()

    # @cached_property
    # def get_score(self):
    #     return self.score


class CompletedContent(BaseModel):
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
    )
    user_course = models.ForeignKey(
        "UserCourse", on_delete=models.CASCADE, related_name="completed_contents"
    )
    content = models.ForeignKey("content.Content", on_delete=models.CASCADE)
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="completed_user_contents",
        null=True,
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.course} - {self.content}"


class AnsweredQuestion(BaseModel):
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="answered_questions", null=True
    )
    user_course = models.ForeignKey(
        "UserCourse",
        on_delete=models.CASCADE,
        related_name="answered_questions",
        null=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="answered_questions",
        null=True,
    )
    content = models.ForeignKey(
        "content.Content",
        on_delete=models.CASCADE,
        related_name="answered_questions",
        default=None,
        null=True,
        blank=True,
    )
    question = models.ForeignKey("quiz.Question", on_delete=models.CASCADE)
    answers = models.ManyToManyField("quiz.QuestionOption", blank=True)
    question_options_snapshot = models.JSONField(default=dict)
    answers_snapshot = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user} - {self.question}"

    @cached_property
    def is_correct(self):
        for answer in self.answers.all():
            if not answer.is_correct:
                return False
        return True


class UserTimeSeriesSecurityScore(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="time_series_security_score"
    )
    security_score = models.FloatField()


class DepartmentTimeSeriesSecurityScore(BaseModel):
    department = models.ForeignKey(
        "Department",
        on_delete=models.CASCADE,
        related_name="time_series_security_score",
    )
    security_score = models.FloatField()


class UserTimeSeriesCompletedCourses(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="time_series_completed_courses"
    )
    courses_completed = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, editable=True)
