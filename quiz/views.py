from django.db.models import Q

from abstract.views import SimpleGetDetailGenericView, SimpleGetListGenericView
from Castellum.enums import Roles

from .models import Question


class ContentQuestionsView(SimpleGetDetailGenericView):
    serializer_class = None
    queryset = Question.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        id = self.kwargs.get("id")
        print(id)
        match user.role:
            case Roles.ORGANIZATION:
                return self.queryset.filter(
                    Q(organization=None)
                    | Q(organization=user)
                    | Q(content__organization=user),
                    content__id=id,
                )
            case Roles.EMPLOYEE:
                return self.queryset.filter(
                    Q(organization=None)
                    | Q(organization=user.emp_profile.organization)
                    | Q(content__organization=user.emp_profile.organization),
                    content__id=id,
                )
            case _:
                return self.queryset.filter(content__id=id)
