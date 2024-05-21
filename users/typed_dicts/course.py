from typing import TypedDict


class LearningResourceCourseData(TypedDict):
    name: str
    thumbnail: str
    duration: str
    button_text: str
    course_card_type: str


class LearningResourceTypesData(TypedDict):
    new: list[LearningResourceCourseData]
    ongoing: list[LearningResourceCourseData]
    completed: list[LearningResourceCourseData]
    recommended: list[LearningResourceCourseData]


class LearningResourcesData(TypedDict):
    all: LearningResourceTypesData
    general: LearningResourceTypesData
    specialized: LearningResourceTypesData
