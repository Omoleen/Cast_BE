from unittest.mock import patch
from uuid import uuid4

from faker import Faker

from abstract.base_test import BaseTestCase
from abstract.tasks import send_email
from Castellum.enums import LearningTypes, Roles
from content.tasks import update_completed_content
from courses.models import Course
from users.enums import EmployeeStatuses
from users.models import CompletedContent, Department, User, UserCourse

COURSES = "/api/courses/"
get_course_detail = lambda id: f"{COURSES}{id}/"
get_start_course_path = lambda id: f"{COURSES}{id}/start/"
get_complete_course_path = lambda id: f"{COURSES}{id}/complete/"

get_retake_course_path = lambda id: f"{COURSES}{id}/retake/"

get_course_performance_path = lambda id: f"{COURSES}{id}/performance/"

get_course_contents_path = lambda id: f"{COURSES}{id}/contents/"

get_course_content_detail_path = (
    lambda course_id, content_id: f"{COURSES}{course_id}/contents/{content_id}/"
)

get_complete_course_content_path = (
    lambda course_id, content_id: f"{COURSES}{course_id}/contents/{content_id}/complete/"
)

get_answer_course_content_question_path = (
    lambda course_id, content_id, question_id: f"{COURSES}{course_id}/contents/{content_id}/questions/{question_id}/answer/"
)


class TestCourses(BaseTestCase):
    def test_get_courses(self):
        self.client.force_authenticate(self.organization)
        response = self.client.get(COURSES)
        self.assertEqual(response.status_code, 200)

    def test_get_course_detail(self):
        self.client.force_authenticate(self.organization)
        course = Course.objects.first()
        response = self.client.get(get_course_detail(course.id))
        self.assertEqual(response.status_code, 200)

    def test_start_course(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        response = self.client.patch(get_start_course_path(course.id))
        self.assert_ok(response)
        self.assertEqual(UserCourse.objects.count(), 1)

    def test_complete_course(
        self,
    ):
        self.client.force_authenticate(user=self.employee)
        employee: User = self.employee
        course: Course = Course.objects.first()
        user_course = employee.start_course(course)
        print(user_course)

        for content in course.contents.all():
            employee.complete_content(content, course, user_course)

        response = self.client.patch(get_complete_course_path(course.id))
        self.assert_ok(response)
        user_course: UserCourse = UserCourse.objects.first()
        self.assertTrue(user_course.is_completed)

    def temt_complete_incomplete_course(self):
        self.client.force_authenticate(user=self.employee)
        course: Course = Course.objects.first()
        employee = self.employee
        employee.start_course(course)
        response = self.client.patch(get_complete_course_path(course.id))
        self.assert_bad(response)

    def test_complete_course_without_starting(self):
        self.client.force_authenticate(user=self.employee)
        course: Course = Course.objects.first()
        response = self.client.patch(get_complete_course_path(course.id))
        self.assert_bad(response)

    def test_complete_nonexistent_course(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch(get_complete_course_path(uuid4()))
        self.assertNotFound(response)

    def test_start_course_nonexistent(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch(get_start_course_path(uuid4()))
        self.assertNotFound(response)

    def test_retake_course(self):
        self.client.force_authenticate(user=self.employee)
        course: Course = Course.objects.first()
        employee = self.employee
        user_course = employee.start_course(course)
        for content in course.contents.all():
            employee.complete_content(content, course, user_course)

        response = self.client.patch(get_retake_course_path(course.id))
        self.assert_ok(response)
        user_course: UserCourse = UserCourse.objects.first()
        self.assertFalse(user_course.is_completed)

    def test_retake_nonexistent_course(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch(get_retake_course_path(uuid4()))
        self.assertNotFound(response)

    def test_get_course_performance(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        employee: User = self.employee
        user_course = employee.start_course(course)
        for content in course.contents.all():
            if content.has_questions:
                question = content.questions.first()
                answer = question.options.first()
                if answer:
                    employee.answer_course_content_question(
                        content, question, [answer], course, user_course
                    )
            else:
                employee.complete_content(content, course, user_course)
        user_course.mark_as_completed()
        response = self.client.get(get_course_performance_path(course.id))
        self.assertEqual(response.status_code, 200)

    def test_get_undone_course_performance(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        response = self.client.get(get_course_performance_path(course.id))
        self.assertEqual(response.status_code, 400)

    def test_get_course_contents(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        response = self.client.get(get_course_contents_path(course.id))
        self.assertEqual(response.status_code, 200)

    def test_get_course_content_detail(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        content = course.contents.first()
        response = self.client.get(
            get_course_content_detail_path(course.id, content.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_complete_undone_course_content(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        content = course.contents.first()
        response = self.client.patch(
            get_complete_course_content_path(course.id, content.id)
        )
        self.assert_bad(response)

    def test_complete_course_content(self):
        self.client.force_authenticate(self.employee)
        for course in Course.objects.all():
            self.employee.start_course(course)
            for content in course.contents.all():
                if not content.has_questions:
                    response = self.client.patch(
                        get_complete_course_content_path(course.id, content.id)
                    )
                    self.assert_ok(response)
                    break
            else:
                continue

    def test_complete_nonexistent_course_content(self):
        self.client.force_authenticate(self.employee)
        response = self.client.patch(get_complete_course_content_path(uuid4(), uuid4()))
        self.assertNotFound(response)

    def test_complete_nonexistent_content(self):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        response = self.client.patch(
            get_complete_course_content_path(course.id, uuid4())
        )
        self.assertNotFound(response)

    @patch.object(update_completed_content, "delay")
    def test_answer_course_content_question(self, update_completed_content_mock):
        self.client.force_authenticate(self.employee)
        course = Course.objects.first()
        employee: User = self.employee
        employee.start_course(course)
        for content in course.contents.all():
            if content.has_questions:
                question = content.questions.first()
                answer = question.options.first()
                if answer:
                    response = self.client.patch(
                        get_answer_course_content_question_path(
                            course.id, content.id, question.id
                        ),
                        {"answer_ids": [answer.id]},
                    )
                    self.assert_ok(response)
                    break
        else:
            self.fail("No content with questions found")

        self.assertTrue(update_completed_content_mock.call_count > 0)
