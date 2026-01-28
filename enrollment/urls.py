from django.urls import path
from . import views

urlpatterns = [
    # Admin enrollment URLs
    path("enrollments/", views.enrollment_list, name="enrollment_list"),
    path("student/<int:student_id>/", views.student_enrollment_detail, name="student_enrollment_detail"),

    # Student enrollment URLs
    path("student/enroll/", views.student_course_enrollment, name="student_course_enrollment"),
    path("student/enrollments/", views.student_my_courses, name="student_my_courses"),
    path("student/drop-course/<int:enrollment_id>/", views.student_drop_course, name="student_drop_course"),
]
