import pendulum
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files import File

# from abstract.toolboxes.thumbnail import ThumbnailGenerator
from content.models import Content
from courses.models import Course, CourseCampaign, EmployeeCourseCampaign
from quiz.models import Question, QuestionOption
from users.models import (
    AnsweredQuestion,
    CompletedContent,
    Employee,
    Organization,
    User,
    UserCourse,
)

# from moviepy.video.io.VideoFileClip import VideoFileClip


User = get_user_model()


@shared_task(name="Update completed content on users record")
def update_completed_content(user_id: str, content_id: str, course_id: str):
    """Check if all questions have been answered and update the user"""

    user: Employee | Organization = User.objects.filter(id=user_id).first()
    course: Course = Course.objects.filter(id=course_id).first()
    content: Content = Content.objects.filter(id=content_id).first()
    user_course = UserCourse.objects.filter(user=user, course=course).first()

    if not user:
        return
    if not content:
        return
    if not course:
        return
    if not user_course:
        return

    all_questions = content.questions.all()
    answered_questions = user.answered_questions.filter(content=content, course=course)
    if all_questions.count() == answered_questions.count():
        user.complete_content(content, course, user_course)


@shared_task(name="Update completed course campaign content on employee's record")
def update_completed_course_campaign_content(
    employee_id: str, content_id: str, course_campaign_id: str, course_id: str
):
    """Check if all questions have been answered and update the employee"""
    employee: Employee = User.objects.filter(id=employee_id).first()
    course_campaign: CourseCampaign = CourseCampaign.objects.filter(
        id=course_campaign_id
    ).first()

    course: Course = course_campaign.courses.filter(id=course_id).first()
    content: Content = course.contents.filter(id=content_id).first()
    employee_course_campaign = EmployeeCourseCampaign.objects.get(
        employee=employee, course_campaign=course_campaign
    )

    if not employee:
        return
    if not course:
        return
    if not content:
        return
    if not course_campaign:
        return
    if not employee_course_campaign:
        return

    course_campaign_course = course_campaign.campaign_courses.filter(
        employee=employee, course=course
    ).first()
    if not course_campaign_course:
        return

    all_questions = content.questions.all()
    answered_questions = employee.answered_campaign_questions.filter(
        content=content, course_campaign=course_campaign, course=course
    )
    if all_questions.count() == answered_questions.count():
        employee.complete_course_campaign_content(
            content=content,
            course=course,
            course_campaign=course_campaign,
            course_campaign_course=course_campaign_course,
        )


# @shared_task(name="update content duration and thumbnail")
# def update_duration_thumbnail(content_id, first_save=False):
#     content: Content = Content.objects.filter(id=content_id).first()
#     if not content:
#         return
#     print(content)
#     file: File = content.file
#     content.name = file.name
#     content.size = file.size / 1000000
#     content.file_type = "." + file.name.split(".")[-1]
#     content.is_uploaded = True
#     content.url = file.path
#     content.duration = pendulum.duration(seconds=VideoFileClip(content.file.path).duration)
#     thumbnail_name = f"thumbnail-{content.file.name.replace(content.file_type, '.jpg')}"
#     content.thumbnail.save(
#         name=thumbnail_name,
#         content=File(ThumbnailGenerator().generate_thumbnail(file_path=content.file.path)),
#         save=False,
#     )
#     content.save()
#     return content
