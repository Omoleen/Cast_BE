# from django.db import models
# from rest_framework import serializers

# from abstract.managers import SimpleModelManager
# from courses.models import Course
# from quiz.enums import QuestionTypes
# from quiz.models import Question, QuestionOption
# from quiz.serializers import QuestionOptionSerializer, QuestionSerializer
# from users.models import AnsweredQuestion, CompletedContent, User, UserCourse

# from content.models import CampaignContentSnapshot, Content
# from content.serializers import ContentDetailSerializer, ContentSerializer, ContentQuestionSerializer
# from content.tasks import update_completed_content


# class AnswerCourseContentQuestionManager(SimpleModelManager):
#     answer_ids = serializers.ListField(
#         child=serializers.CharField(), write_only=True, required=True
#     )

#     class Meta:
#         model = Question
#         fields = ["answer_ids"]

#     def _validate_db(self, attrs):
#         course = attrs["course"] = self.context["course"]
#         question = attrs["question"] = self.context["question"]
#         content = attrs["content"] = self.context["content"]

#         answers = QuestionOption.objects.filter(id__in=attrs["answer_ids"], question=question)
#         if not answers.exists():
#             raise serializers.ValidationError("Answer not found")

#         if question.type == QuestionTypes.SINGLECHOICE and len(answers) > 1:
#             raise serializers.ValidationError("Single choice question")
#         elif (
#             question.type == QuestionTypes.MULTICHOICE
#             and len(answers) > question.options.count()
#         ):
#             raise serializers.ValidationError(
#                 "answers are morve than the available options"
#             )

#         self.question = question
#         self.answers = answers
#         self.course = course
#         self.content = content
#         return super()._validate_db(attrs)

#     def _update(self, instance, validated_data):
#         user: User = self.context["request"].user
#         content: Content = self.content
#         question: Question = self.question
#         answers: models.QuerySet[QuestionOption] = self.answers
#         course: Course = self.course
#         answered_question, _ = AnsweredQuestion.objects.update_or_create(
#             user=user,
#             question=question,
#             content=content,
#             course=course,
#             defaults={
#                 "question_options_snapshot": ContentQuestionSerializer(question).data,
#                 "answers_snapshot": QuestionOptionSerializer(answers, many=True).data,
#             },
#         )
#         answered_question.answers.set(answers)
#         self.user = user
#         self.content = content
#         return instance

#     def _misc(self, data):
#         user: User = self.user
#         content: Content = self.content
#         course: Course = self.course
#         update_completed_content.delay(user.id, content.id, course.id)
#         return

#     def _to_representation(self, instance):
#         return "Answer submitted successfully"
