from django.db import models


class EmployeeStatuses(models.TextChoices):
    ACTIVE = "active", "Active"
    PENDING = "pending", "Pending"
    DEACTIVATED = "deactivated", "Deactivated"


class ActivityType(models.TextChoices):
    COURSE_CAMPAIGN_STARTED = "course_campaign_started", "Course Campaign Started"
    COURSE_CAMPAIGN_COMPLETED = "course_campaign_completed", "Course Campaign Completed"
    COURSE_STARTED = "course_started", "Course Started"
    COURSE_COMPLETED = "course_completed", "Course Completed"


class LearningResourceButtonType(models.TextChoices):
    BEGIN = "begin", "Begin"
    CONTINUE = "continue", "Continue"
    RETAKE = "retake", "Retake"


class CourseCardType(models.TextChoices):
    NEW = "new", "New"
    IN_PROGRESS = "in-progress", "In-Progress"
    COMPLETED = "completed", "Completed"
    RECOMMENDED = "recommended", "Recommended"
