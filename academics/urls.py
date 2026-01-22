from django.urls import path
from . import views

urlpatterns = [
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/delete/<int:pk>/', views.department_delete, name='department_delete'),
    path('departments/edit/<int:pk>/', views.department_edit, name='department_edit'),

    path("degree-programs/", views.degree_program_list, name="degree_program_list"),
    path("degree-programs/add/", views.degree_program_add, name="degree_program_add"),
    path("degree-programs/<int:pk>/edit/", views.degree_program_edit, name="degree_program_edit",),
    path("degree-programs/<int:pk>/delete/", views.degree_program_delete, name="degree_program_delete",),

    path("courses/", views.course_list, name="course_list"),
    path("courses/add/", views.course_add, name="course_add"),
    path("courses/edit/<int:pk>/", views.course_edit, name="course_edit"),
    path("courses/delete/<int:pk>/", views.course_delete, name="course_delete"),

    path("semesters/", views.semester_list, name="semester_list"),
    path("semesters/add/", views.semester_add, name="semester_add"),
    path("semesters/edit/<int:pk>/", views.semester_edit, name="semester_edit"),
    path("semesters/delete/<int:pk>/", views.semester_delete, name="semester_delete"),
]
