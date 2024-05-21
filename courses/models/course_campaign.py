from datetime import timedelta
from functools import cached_property

import pendulum
from django.conf import settings
from django.db import models
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils import timezone

from abstract.models import BaseModel
from abstract.tasks import send_email
from abstract.toolboxes import PendulumToolbox
from campaign.enums import CampaignStatus
from campaign.models import Campaign
from campaign.tasks import start_campaign
from Castellum.celery import app
from users.models import Organization, OrganizationProfile

from ..tasks import course_campaigns_reminder_email_task
from . import Course


class CourseCampaign(BaseModel):
    campaign = models.OneToOneField(
        Campaign, on_delete=models.CASCADE, related_name="course_campaign"
    )
    courses = models.ManyToManyField(Course, related_name="course_campaign", blank=True)
    employees = models.ManyToManyField(
        "users.Employee",
        related_name="course_campaign",
        blank=True,
        through="EmployeeCourseCampaign",
    )
    reminder_task_ids = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f"{self.campaign} - {self.id}"

    def cancel(self):
        if self.reminder_task_ids:
            for reminder_task_id in self.reminder_task_ids:
                app.AsyncResult(reminder_task_id).revoke()
        self.reminder_task_ids = []
        self.save()

    def notify_employees_campaign_started(self):
        """Notify employees that the campaign has started"""
        employees = self.employees.all()

        for employee in employees:
            context = {
                "campaign_name": self.campaign.name,
                "campaign_type": self.campaign.type,
                "name": employee.first_name,
                "campaign_url": f"{settings.FRONTEND_URL}employee/dashboard/campaign/{self.campaign.id}",
            }
            email_body = render_to_string(
                "emails/campaign/campaign_started.html", context=context
            )
            send_email.delay(
                email_subject=f"Campaign - {self.campaign.name} has started!",
                to_email=[employee.email],
                email_body=email_body,
            )

    # def notify_employees_campaign_enrolled(self):
    #     """Notify employees that they have been enrolled in a campaign"""
    #     employees = self.employees.all()

    #     for employee in employees:
    #         context = {
    #             "campaign_name": self.campaign.name.title(),
    #             "name": employee.first_name.title(),
    #             "campaign_type": self.campaign.type.title(),
    #             "start_date": self.campaign.start_date.strftime("%B %d, %Y, %-I:%M %p"),
    #             "end_date": self.campaign.end_date.strftime("%B %d, %Y, %-I:%M %p"),
    #             "last_name": employee.last_name,
    #         }

    #         email_body = render_to_string(
    #             "emails/campaign/employee_enrollment.html", context=context
    #         )
    #         send_email.delay(
    #             email_subject=f"You've been added to a learning campaign!",
    #             to_email=[employee.email],
    #             email_body=email_body,
    #         )

    # def notify_employee_campaign_reminder(self, employee):
    #     """Notify employee that have not completed a camaign that the deadline is approaching"""

    #     available_templates = [
    #         "emails/campaign/reminder.html",
    #         "emails/campaign/reminder1.html",
    #         "emails/campaign/reminder2.html",
    #     ]

    #     email_template = random.choice(available_templates)
    #     context = {
    #         "campaign_name": self.campaign.name.title(),
    #         "name": employee.first_name.title(),
    #         "campaign_type": self.campaign.type.title(),
    #         "start_date": self.campaign.start_date.strftime("%B %d, %Y, %-I:%M %p"),
    #         "end_date": self.campaign.end_date.strftime("%B %d, %Y, %-I:%M %p"),
    #         "last_name": employee.last_name,
    #         "campaign_url": f"{settings.FRONTEND_URL}employee/dashboard/campaign/{self.campaign.id}",
    #     }
    #     email_body = render_to_string(email_template, context=context)
    #     send_email.delay(
    #         email_subject=f"Tick Tock! You have a Campaign to Complete!",
    #         to_email=[employee.email],
    #         email_body=email_body,
    #     )

    def start(self):
        campaign = self.campaign
        campaign.status = CampaignStatus.ACTIVE
        campaign.save()
        for employee_course_campaign in self.employee_records.all():
            employee_course_campaign.notify_employee_campaign_started()

    def initiate_course_campaign(self):
        campaign: Campaign = self.campaign
        organization: Organization = campaign.organization
        org_profile: OrganizationProfile = organization.org_profile

        if org_profile.campaign_email_notification:
            for employee_course_campaign in self.employee_records.all():
                employee_course_campaign.notify_employee_campaign_enrolled()
                # course_campaign.notify_employees_campaign_enrolled()

        # set the task to start campaign in due time
        for background_task_ids in campaign.background_task_ids:
            app.AsyncResult(background_task_ids).revoke()

        campaign.background_task_ids = []
        start_course_campaign_task = start_campaign.apply_async(
            args=[campaign.id], eta=campaign.start_date
        )
        campaign.background_task_ids.append(str(start_course_campaign_task.id))
        campaign.save()

        # set up reminder tasks
        for reminder_task_id in self.reminder_task_ids:
            app.AsyncResult(reminder_task_id).revoke()

        self.reminder_task_ids = []
        if org_profile.reminder_notification:
            now = timezone.now()
            for reminder in settings.COURSE_CAMPAIGN_REMINDERS_IN_SECONDS:
                reminder_time = self.campaign.end_date - timedelta(seconds=reminder)
                if reminder_time > now:
                    reminder_task = course_campaigns_reminder_email_task.apply_async(
                        args=[self.campaign.id], eta=reminder_time
                    )
                    self.reminder_task_ids.append(str(reminder_task.id))
            self.save()

    @property
    def activity(self):
        return {
            "completed": self.employee_records.filter(is_completed=True).count(),
            "total": self.employees.count(),
        }

    @cached_property
    def duration(self):
        durations = []
        for course in self.courses.all():
            if course.duration_in_timedelta:
                durations.append(course.duration_in_timedelta)
        duration = sum(durations, timedelta())
        return PendulumToolbox.convert_timedelta_to_duration(duration, in_words=True)

    @cached_property
    def quiz_count(self):
        count = 0
        courses = self.courses.prefetch_related("contents__questions").all()
        for course in courses:
            count += course.quiz_count
        return count

    @cached_property
    def average_score(self):
        employee_course_campaigns = self.employee_records.all()
        score_percentages = []
        for employee_course_campaign in employee_course_campaigns:
            percentage = employee_course_campaign.average_score
            score_percentages.append(percentage)
        return (
            sum(score_percentages) / len(score_percentages) if score_percentages else 0
        )

    @cached_property
    def progress_rate(self):
        employee_course_campaigns = self.employee_records.all()
        progress_rates = []
        for employee_course_campaign in employee_course_campaigns:
            progress_rate = employee_course_campaign.progress_rate
            progress_rates.append(progress_rate)
        return int((sum(progress_rates) / len(progress_rates))) if progress_rates else 0


class EmployeeCourseCampaign(BaseModel):
    employee = models.ForeignKey(
        "users.Employee",
        on_delete=models.CASCADE,
        related_name="course_campaign_records",
    )
    course_campaign = models.ForeignKey(
        "CourseCampaign", on_delete=models.CASCADE, related_name="employee_records"
    )
    started_at = models.DateTimeField(default=None, null=True, blank=True)
    completed_at = models.DateTimeField(default=None, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    is_started = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)

    def notify_employee_campaign_started(self):
        """Notify employees that the campaign has started"""
        employee = self.employee
        campaign = self.course_campaign.campaign
        context = {
            "campaign_name": campaign.name.title(),
            "campaign_type": campaign.type.title(),
            "name": employee.first_name.title(),
            "campaign_url": f"{settings.FRONTEND_URL}employee/dashboard/campaign/{campaign.id}",
        }
        email_body = render_to_string(
            "emails/campaign/campaign_started.html", context=context
        )
        send_email.delay(
            email_subject=f"Campaign - {campaign.name} has started!",
            to_email=[employee.email],
            email_body=email_body,
        )

    def notify_employee_campaign_enrolled(self):
        """Notify employees that they have been enrolled in a campaign"""
        employee = self.employee
        campaign = self.course_campaign.campaign
        context = {
            "campaign_name": campaign.name.title(),
            "name": employee.first_name.title(),
            "campaign_type": campaign.type.title(),
            "start_date": campaign.start_date.strftime("%B %d, %Y, %-I:%M %p"),
            "end_date": campaign.end_date.strftime("%B %d, %Y, %-I:%M %p"),
            "last_name": employee.last_name,
        }

        email_body = render_to_string(
            "emails/campaign/employee_enrollment.html", context=context
        )
        send_email.delay(
            email_subject=f"You've been added to a learning campaign!",
            to_email=[employee.email],
            email_body=email_body,
        )

    @property
    def courses_left(self):
        course_campaign_courses = CourseCampaignCourse.objects.filter(
            employee=self.employee, course_campaign=self.course_campaign
        )
        total_courses = course_campaign_courses.count()
        completed_courses = course_campaign_courses.filter(is_completed=True).count()
        return total_courses - completed_courses

    @property
    def questions_left(self):
        course_campaign_courses = CourseCampaignCourse.objects.filter(
            employee=self.employee, course_campaign=self.course_campaign
        )
        total_questions = 0
        answered_questions = AnsweredCourseCampaignQuestion.objects.filter(
            employee=self.employee, course_campaign=self.course_campaign
        ).count()
        for course_campaign_course in course_campaign_courses:
            total_questions += course_campaign_course.questions_count
        return total_questions - answered_questions

    def start(self):
        from users.enums import ActivityType

        self.is_started = True
        self.started_at = timezone.now()
        self.save()
        self.employee.perform_activity(ActivityType.COURSE_CAMPAIGN_STARTED)
        all_courses = self.course_campaign.courses.all()
        course_campaign_courses = []
        for course in all_courses:
            course_campaign_course = CourseCampaignCourse(
                employee=self.employee,
                course_campaign=self.course_campaign,
                # employee_course_campaign_instance=self,
                course=course,
            )
            course_campaign_courses.append(course_campaign_course)
        CourseCampaignCourse.objects.bulk_create(course_campaign_courses)

    def complete(self):
        from users.enums import ActivityType

        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
        self.employee.perform_activity(ActivityType.COURSE_CAMPAIGN_COMPLETED)
        if (
            self.course_campaign.campaign.organization.org_profile.campaign_completion_notification
        ):
            self.notify_employee_campaign_completed()

    def notify_employee_campaign_completed(self):
        """Notify employee that he has completed the campaign"""

        context = {
            "campaign_name": self.course_campaign.campaign.name.title(),
            "name": self.employee.first_name.title(),
            "campaign_type": self.course_campaign.campaign.type.title(),
        }

        email_body = render_to_string(
            "emails/campaign/employee_completed.html", context=context
        )

        send_email.delay(
            email_subject=f"Congratulations on Completing Your Campaign!",
            to_email=[self.employee.email],
            email_body=email_body,
        )

    @property
    def progress_rate(self):
        """calculate progress rate using completed contents"""
        course_campaign_courses = CourseCampaignCourse.objects.filter(
            employee=self.employee, course_campaign=self.course_campaign
        )
        course_progress_rates = []
        for course_campaign_course in course_campaign_courses:
            course_progress_rates.append(course_campaign_course.progression_rate)
        return (
            int((sum(course_progress_rates) / len(course_progress_rates)))
            if course_progress_rates
            else 0
        )

    @cached_property
    def score(self):
        return self.get_score()

    def get_score(self):
        course_campaign_courses = CourseCampaignCourse.objects.filter(
            employee=self.employee, course_campaign=self.course_campaign
        )
        score = 0
        for course_campaign_course in course_campaign_courses:
            score += course_campaign_course.score
        return (
            int(score / course_campaign_courses.count())
            if course_campaign_courses
            else 0
        )

    @cached_property
    def average_score(self):
        course_campaign_courses = CourseCampaignCourse.objects.filter(
            employee=self.employee, course_campaign=self.course_campaign
        )
        score_percentages = []
        for course_campaign_course in course_campaign_courses:
            score_percentages.append(course_campaign_course.average_score)

        return (
            sum(score_percentages) / len(score_percentages) if score_percentages else 0
        )

    @property
    def is_active(self):
        if self.is_started and not self.is_completed:
            return True
        return False


class CourseCampaignCourse(BaseModel):
    employee = models.ForeignKey(
        "users.Employee",
        on_delete=models.CASCADE,
        related_name="campaign_courses",
    )
    course_campaign = models.ForeignKey(
        "CourseCampaign",
        on_delete=models.CASCADE,
        related_name="campaign_courses",
        null=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    employee_course_campaign_instance = (
        models.ForeignKey(
            EmployeeCourseCampaign,
            on_delete=models.CASCADE,
            related_name="employee_campaign_courses",
            null=True,
        ),
    )

    def __str__(self):
        return f"{self.employee} - {self.course}"

    @cached_property
    def questions_count(self):
        return self.course.questions_count

    @cached_property
    def score(self):
        answered_questions = AnsweredCourseCampaignQuestion.objects.filter(
            employee=self.employee,
            course=self.course,
            course_campaign=self.course_campaign,
        )
        score = 0
        for answered_question in answered_questions:
            if answered_question.is_correct:
                score += 1
        return int((score / self.questions_count) * 100) if self.questions_count else 0

    @cached_property
    def average_score(self):
        return self.score

    @cached_property
    def progression_rate(self):
        contents = self.course.contents.all()
        contents_with_questions = contents.annotate(
            num_questions=Count("questions")
        ).filter(num_questions__gt=0)
        available_questions = sum(
            [content.num_questions for content in contents_with_questions]
        )
        answered_questions = AnsweredCourseCampaignQuestion.objects.filter(
            employee=self.employee,
            course=self.course,
            course_campaign=self.course_campaign,
        ).count()
        contents_without_questions = contents.annotate(
            num_questions=Count("questions")
        ).filter(num_questions=0)
        completed_contents_without_questions = self.completed_campaign_contents.filter(
            content__in=contents_without_questions
        ).count()
        total = available_questions + contents_without_questions.count()
        answered = answered_questions + completed_contents_without_questions
        return int((answered / total) * 100) if total else 0


class CompletedCourseCampaignContent(BaseModel):
    employee = models.ForeignKey(
        "users.Employee",
        on_delete=models.CASCADE,
        related_name="completed_campaign_contents",
    )
    course_campaign = models.ForeignKey(
        "CourseCampaign",
        on_delete=models.CASCADE,
        related_name="completed_campaign_contents",
    )
    course_campaign_course = models.ForeignKey(
        "CourseCampaignCourse",
        on_delete=models.CASCADE,
        related_name="completed_campaign_contents",
        null=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="completed_campaign_contents",
    )
    content = models.ForeignKey(
        "content.Content",
        on_delete=models.CASCADE,
        related_name="completed_campaign_contents",
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.course} - {self.content}"


class AnsweredCourseCampaignQuestion(BaseModel):
    employee = models.ForeignKey(
        "users.Employee",
        on_delete=models.CASCADE,
        related_name="answered_campaign_questions",
    )
    course_campaign = models.ForeignKey(
        "CourseCampaign",
        on_delete=models.CASCADE,
        related_name="answered_campaign_questions",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="answered_campaign_questions",
    )
    content = models.ForeignKey(
        "content.Content",
        on_delete=models.CASCADE,
        related_name="answered_campaign_questions",
    )
    question = models.ForeignKey("quiz.Question", on_delete=models.CASCADE)
    answers = models.ManyToManyField("quiz.QuestionOption", blank=True)
    question_options_snapshot = models.JSONField(default=dict)
    answers_snapshot = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.employee} - {self.question}"

    @property
    def is_correct(self):
        return not self.answers.filter(is_correct=False).exists()
