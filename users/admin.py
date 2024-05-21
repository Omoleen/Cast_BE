from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import decorators, get_user_model
from django.utils.translation import gettext_lazy as _

from .models import (
    ActivityLog,
    AnsweredQuestion,
    AuthorizedDomain,
    DeliverabilityTest,
    Department,
    DepartmentTimeSeriesSecurityScore,
    Employee,
    EmployeeProfile,
    Organization,
    OrganizationProfile,
    User,
    UserCourse,
    UserTimeSeriesCompletedCourses,
    UserTimeSeriesSecurityScore,
)

User = get_user_model()


# @admin.register(User)
# class UserAdmin(auth_admin.UserAdmin):
#     fieldsets = (
#         (None, {"fields": ("email", "password")}),
#         # (_("Personal info"), {"fields": ("name",)}),
#         (
#             _("Permissions"),
#             {
#                 "fields": (
#                     "is_active",
#                     "is_staff",
#                     "is_superuser",
#                     "groups",
#                     "user_permissions",
#                 ),
#             },
#         ),
#         # (_("Important dates"), {"fields": ("last_login")}),
#     )
#     list_display = ["id", "email", "is_superuser"]
#     search_fields = ["email"]
#     ordering = ["id"]
#     add_fieldsets = (
#         (
#             None,
#             {
#                 "classes": ("wide",),
#                 "fields": ("email", "password1", "password2"),
#             },
#         ),
#     )


# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     model = User
#     list_display = ['email', 'is_staff', 'is_active', ]
#     list_filter = ['email', 'is_staff', 'is_active']
#     fieldsets = (
#         (None, {'fields': (
#         'email', 'password', 'first_name', 'last_name', 'phone_number', 'wallet', 'role', 'location', 'location_lat',
#         'location_long', 'date_joined')}),
#         ('Permissions', {'fields': ('is_active',)}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'first_name', 'last_name', 'role', 'phone_number', 'password1', 'password2')},
#          ),
#         ('Permissions', {'fields': ('is_active',)})
#     )
#     search_fields = ('email',)
#     ordering = ('email',)

#     # readonly_fields = ['wallet']

#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return ["email", 'date_joined', 'password', 'wallet']
#         else:
#             return ['date_joined']


admin.site.site_header = "Castellum Admin"


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    model = User
    list_display = ["id", "email", "role", "is_active", "is_admin"]
    list_filter = ["email", "is_staff", "role", "is_active", "is_admin"]
    fieldsets = (
        (None, {"fields": ("email", "password", "token", "token_expiration_task_id")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_email_verified",
                    "role",
                    "is_admin",
                    "is_staff",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password", "token", "token_expiration_task_id"),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_email_verified",
                    "role",
                    "is_admin",
                    "is_staff",
                )
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "email",
                "password",
            ]
        else:
            return []


@admin.register(Organization)
class OrganizationAdmin(UserAdmin):
    model = Organization


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    model = Employee
    list_display = UserAdmin.list_display + ["full_name"]


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    model = EmployeeProfile
    list_display = [
        "id",
        "employee",
        "organization",
        "department",
        "security_score",
        "status",
    ]


admin.site.register(Department)


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    model = OrganizationProfile
    list_display = [
        "id",
        "name",
        "security_score",
    ]


admin.site.register(AnsweredQuestion)
admin.site.register(UserCourse)
admin.site.register(DeliverabilityTest)
admin.site.register(AuthorizedDomain)
admin.site.register(ActivityLog)


@admin.register(DepartmentTimeSeriesSecurityScore)
class DepartmentTimeSeriesSecurityScoreAdmin(admin.ModelAdmin):
    model = DepartmentTimeSeriesSecurityScore
    list_display = ["id", "department", "created_at", "security_score"]

    fieldsets = ((None, {"fields": ("department", "security_score", "created_at")}),)

    readonly_fields = ["created_at"]


@admin.register(UserTimeSeriesCompletedCourses)
class UserTimeSeriesCompletedCoursesAdmin(admin.ModelAdmin):
    model = UserTimeSeriesCompletedCourses
    list_display = ["id", "user", "created_at", "courses_completed"]

    fieldsets = ((None, {"fields": ("user", "courses_completed", "created_at")}),)

    readonly_fields = ["created_at"]


@admin.register(UserTimeSeriesSecurityScore)
class UserTimeSeriesSecurityScoreAdmin(admin.ModelAdmin):
    model = UserTimeSeriesSecurityScore
    list_display = ["id", "user", "created_at", "security_score"]

    fieldsets = ((None, {"fields": ("user", "security_score", "created_at")}),)

    readonly_fields = ["created_at"]
