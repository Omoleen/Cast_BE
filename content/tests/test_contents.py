from unittest.mock import patch

from faker import Faker

from abstract.base_test import BaseTestCase
from abstract.tasks import send_email
from Castellum.enums import LearningTypes, Roles
from users.enums import EmployeeStatuses
from users.models import Department, User

from ..models import Content
from ..tasks import update_completed_content

CONTENT_LIST = "/api/contents/"
get_filter_content_path = (
    lambda learning_type: f"/api/contents/?learning_type={learning_type}"
)
get_complete_content_path = lambda id: f"/api/contents/{id}/complete/"
get_answer_content_question_path = lambda id: f"/api/contents/{id}/answer/"


# class TestContents(BaseTestCase):
#     def test_get_default_contents_as_organization(self):
#         self.client.force_authenticate(user=self.organization)
#         response = self.client.get(CONTENT_LIST)
#         self.assert_ok(response)

#     def test_get_default_contents_as_employee(self):
#         self.client.force_authenticate(user=self.employee)
#         response = self.client.get(CONTENT_LIST)
#         self.assert_ok(response)

#     def test_content_filter_by_learning_type(self):
#         self.client.force_authenticate(user=self.organization)
#         response = self.client.get(get_filter_content_path(LearningTypes.GENERAL))
#         self.assert_ok(response)
#         data = response.json()
#         for content in data:
#             self.assertEqual(content["learning_type"], LearningTypes.GENERAL)
#         response = self.client.get(get_filter_content_path(LearningTypes.SPECIALIZED))
#         self.assert_ok(response)
#         data = response.json()
#         for content in data:
#             self.assertEqual(content["learning_type"], LearningTypes.SPECIALIZED)

#     def test_complete_content_with_questions(self):
#         self.client.force_authenticate(user=self.employee)
#         content: Content = Content.objects.first()

#         for content in Content.objects.all():
#             if content.has_questions:
#                 break
#         self.assertEqual(content.has_questions, True)
#         response = self.client.patch(get_complete_content_path(content.id))
#         self.assert_bad(response)

#     def test_complete_content_without_questions(self):
#         self.client.force_authenticate(user=self.employee)
#         content: Content = Content.objects.first()

#         for content in Content.objects.all():
#             if not content.has_questions:
#                 break
#         self.assertEqual(content.has_questions, False)
#         response = self.client.patch(get_complete_content_path(content.id))
#         self.assert_ok(response)

#     # @patch.object(update_completed_content, "delay")
#     # def test_answer_content_question(self, update_completed_content_mock):
#     #     self.client.force_authenticate(user=self.employee)
#     #     content: Content | None = None

#     #     for content in Content.objects.all():
#     #         if content.has_questions:
#     #             break
#     #     self.assertEqual(content.has_questions, True)
#     #     question = content.questions.first()
#     #     response = self.client.patch(
#     #         get_answer_content_question_path(content.id),
#     #         {"question_id": question.id, "answer_ids": [question.options.first().id]},
#     #     )
#     #     self.assert_ok(response)
#     #     update_completed_content_mock.assert_called_once()

#     # def test_answer_content_wrong_question(self):
#     #     self.client.force_authenticate(user=self.employee)
#     #     content: Content | None = None

#     #     for base_content in Content.objects.all():
#     #         if base_content.has_questions:
#     #             break

#     #     for content in Content.objects.all():
#     #         if content.has_questions and content != base_content:
#     #             break

#     #     self.assertEqual(content.has_questions, True)
#     #     question = content.questions.first()
#     #     base_question = base_content.questions.first()
#     #     response = self.client.patch(
#     #         get_answer_content_question_path(content.id),
#     #         {"question_id": base_question.id, "answer_ids": [question.options.first().id]},
#     #     )
#     #     self.assert_bad(response)

#     # def test_answer_content_wrong_answer(self):
#     #     self.client.force_authenticate(user=self.employee)
#     #     content: Content | None = None

#     #     for base_content in Content.objects.all():
#     #         if base_content.has_questions:
#     #             break

#     #     for content in Content.objects.all():
#     #         if content.has_questions and content != base_content:
#     #             break

#     #     self.assertEqual(content.has_questions, True)
#     #     question = content.questions.first()
#     #     base_question = base_content.questions.first()
#     #     response = self.client.patch(
#     #         get_answer_content_question_path(content.id),
#     #         {"question_id": question.id, "answer_ids": [base_question.options.first().id], "course_id": },
#     #     )
#     #     self.assert_bad(response)
