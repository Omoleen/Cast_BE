from django.db import models


class ContentTypes(models.TextChoices):
    VIDEO = "video", "Video"
    ILLUSTRATION = (
        "illustration",
        "Illustration",
    )
    SLIDESHOW = "slideshow", "Slideshow"
