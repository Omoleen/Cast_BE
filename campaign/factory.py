import factory
import factory.fuzzy
from faker import Faker

from Castellum.enums import Roles
from courses.models import Course

from .enums import CampaignStatus, CampaignTypes

# class OrganizationFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = "users.Organization"

#     email = factory.Faker("email")
#     password = "testpassword123"

#     is_active = True
#     is_email_verified = True

#     role = Roles.ORGANIZATION

#     @classmethod
#     def _create(self, model_class, *args, **kwargs):
#         manager = self._get_manager(model_class)
#         fake = Faker()

#         kwargs["name"] = kwargs.get("name", fake.company())
#         kwargs["url"] = kwargs.get("url", fake.url())

#         user = manager.create_org(*args, **kwargs)
#         user.is_active = True
#         user.save()

#         return user


class CourseCampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.coursecampaign"

    campaign = factory.SubFactory("campaign.CampaignFactory")

    @factory.post_generation
    def add_courses(self, create, extracted, **kwargs):
        if not create:
            return

        courses = Course.objects.all()
        self.courses.add(*courses)

        # if extracted:
        #     for course in extracted:
        #         self.courses.add(course)


class CourseCampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "campaign.Campaign"

    name = factory.Faker("name")
    description = factory.Faker("text")
    type = factory.fuzzy.FuzzyChoice(CampaignTypes.values)
    status = CampaignStatus.DRAFT

    start_date = factory.Faker("date_time")
    end_date = factory.Faker("date_time")

    last_step_completed = 0

    automatically_enroll_employees = False

    background_task_ids = []

    organization = factory.SubFactory("users.OrganizationFactory")

    @factory.post_generation
    def create_course_campaign(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            CourseCampaignFactory(campaign=self)


class PhishingCampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "campaign.Campaign"

    name = factory.Faker("name")
    description = factory.Faker("text")
    type = CampaignTypes.PHISHING
    status = CampaignStatus.DRAFT

    start_date = factory.Faker("date_time")
    end_date = factory.Faker("date_time")

    last_step_completed = 0

    automatically_enroll_employees = False

    background_task_ids = []

    organization = factory.SubFactory("users.OrganizationFactory")

    @classmethod
    def _create(self, model_class, *args, **kwargs):
        manager = self._get_manager(model_class)
        fake = Faker()

        kwargs["name"] = kwargs.get("name", fake.company())
        kwargs["description"] = kwargs.get("description", fake.text())
        kwargs["type"] = kwargs.get("type", CampaignTypes.PHISHING)
        kwargs["status"] = kwargs.get("status", CampaignStatus.DRAFT)

        kwargs["start_date"] = kwargs.get("start_date", fake.date_time())
        kwargs["end_date"] = kwargs.get("end_date", fake.date_time())

        kwargs["last_step_completed"] = kwargs.get("last_step_completed", 0)

        kwargs["automatically_enroll_employees"] = kwargs.get(
            "automatically_enroll_employees", False
        )

        kwargs["background_task_ids"] = kwargs.get("background_task_ids", [])

        kwargs["organization"] = kwargs.get("organization", OrganizationFactory())

        campaign = manager.create_campaign(*args, **kwargs)
        campaign.save()

        return campaign
