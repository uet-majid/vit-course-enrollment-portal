from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path("profile/", views.profile_view, name="profile"),
    path("verify-otp/<int:user_id>/", views.verify_otp, name="verify_otp"),
    path("resend-otp/<int:user_id>/", views.resend_otp, name="resend_otp"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/<int:user_id>/", views.reset_password, name="reset_password"),


    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.student_add, name="student_add"),
    path("students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),
    path("ajax/degree-programs/", views.get_degree_programs, name="get_degree_programs"),

    path("department-admins/", views.department_admin_list, name="department_admin_list"),
    path("department-admins/add/", views.department_admin_add, name="department_admin_add"),
    path("department-admins/<int:pk>/edit/", views.department_admin_edit, name="department_admin_edit"),
    path("department-admins/<int:pk>/delete/", views.department_admin_delete, name="department_admin_delete"),
]
