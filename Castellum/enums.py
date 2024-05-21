from django.db import models


class Roles(models.TextChoices):
    ADMIN = "admin", "Admin"
    ORGANIZATION = "organization", "Organization"
    EMPLOYEE = "employee", "Employee"


class LearningTypes(models.TextChoices):
    GENERAL = "general", "General"
    SPECIALIZED = "specialized", "Specialized"
