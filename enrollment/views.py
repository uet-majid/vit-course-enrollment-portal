from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from enrollment.models import Enrollment
from accounts.models import Student, DepartmentAdmin
from academics.models import Semester, CourseOffering
from accounts.decorators import admin_required, student_required
from django.utils.timezone import now
from django.db import transaction
from datetime import date
from django.utils import timezone

@admin_required
def enrollment_list(request):
    user = request.user
    semester_id = request.GET.get("semester")

    semesters = Semester.objects.all().order_by("-start_date")

    enrollments = Enrollment.objects.select_related(
        "student__user",
        "student__department",
        "course_offering__course",
        "course_offering__semester",
    )

    # Department Admin restriction
    if user.role == "DEPARTMENT_ADMIN":
        department = DepartmentAdmin.objects.get(user=user).department
        enrollments = enrollments.filter(
            student__department=department
        )

    # Semester filter
    if semester_id:
        enrollments = enrollments.filter(
            course_offering__semester_id=semester_id
        )

    return render(
        request,
        "enrollment/enrollment_list.html",
        {
            "enrollments": enrollments,
            "semesters": semesters,
            "selected_semester": semester_id,
        },
    )

@admin_required
def student_enrollment_detail(request, student_id):
    user = request.user
    student = get_object_or_404(Student, id=student_id)

    # Department Admin security check
    if user.role == "DEPARTMENT_ADMIN":
        department = DepartmentAdmin.objects.get(user=user).department
        if student.department != department:
            messages.error(request, "You are not allowed to view this student.")
            return redirect("course_enrollment_list")

    enrollments = Enrollment.objects.select_related(
        "course_offering__course",
        "course_offering__semester",
    ).filter(
        student=student
    ).order_by(
        "-course_offering__semester__start_date"
    )

    return render(
        request,
        "enrollment/student_enrollment_history.html",
        {
            "student": student,
            "enrollments": enrollments,
        },
    )


@student_required
def student_my_courses(request):
    student = request.user.student

    active_semester = get_current_semester()

    current_enrollments = []
    past_enrollments = {}

    if active_semester:
        current_enrollments = Enrollment.objects.select_related(
            "course_offering__course",
            "course_offering__semester",
        ).filter(
            student=student,
            course_offering__semester=active_semester,
        ).order_by("-enrolled_at")

    past_records = Enrollment.objects.select_related(
        "course_offering__course",
        "course_offering__semester",
    ).filter(
        student=student
    ).exclude(
        course_offering__semester=active_semester
    ).order_by(
        "-course_offering__semester__start_date"
    )

    for e in past_records:
        semester = e.course_offering.semester
        past_enrollments.setdefault(semester, []).append(e)

    return render(
        request,
        "enrollment/my_enrollments.html",
        {
            "student": student,
            "active_semester": active_semester,
            "current_enrollments": current_enrollments,
            "past_enrollments": past_enrollments,
        },
    )

@student_required
def student_course_enrollment(request):
    student = request.user.student

    if not student.is_active:
        messages.error(request, "Your academic status is inactive.")
        return redirect("dashboard")

    semester = get_current_semester()
    if not semester:
        messages.error(request, "No active semester found.")
        return redirect("dashboard")

    today = timezone.now().date()
    if not (semester.enrollment_open_date <= today <= semester.enrollment_close_date):
        messages.error(request, "Enrollment window is closed.")
        return redirect("dashboard")

    # ENROLLED only (dropped should still be visible for re-enroll)
    enrolled_ids = Enrollment.objects.filter(
        student=student,
        course_offering__semester=semester,
        status="ENROLLED"
    ).values_list("course_offering_id", flat=True)

    offerings = CourseOffering.objects.select_related(
        "course", "course__department"
    ).filter(
        semester=semester,
        is_active=True,
        course__department=student.department
    )

    if request.method == "POST":
        offering_id = request.POST.get("offering_id")
        offering = get_object_or_404(CourseOffering, id=offering_id)

        # Capacity check
        if offering.current_enrollment >= offering.course.max_capacity:
            messages.error(request, "Course capacity is full.")
            return redirect("student_course_enrollment")

        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course_offering=offering,
            defaults={"status": "ENROLLED"}
        )

        if not created:
            if enrollment.status == "ENROLLED":
                messages.warning(request, "You are already enrolled in this course.")
                return redirect("student_course_enrollment")

            # Re-enroll dropped course
            enrollment.status = "ENROLLED"
            enrollment.save(update_fields=["status"])

        offering.current_enrollment += 1
        offering.save(update_fields=["current_enrollment"])

        messages.success(request, "Course enrolled successfully.")
        return redirect("student_my_courses")

    return render(
        request,
        "enrollment/enroll_course.html",
        {
            "offerings": offerings,
            "semester": semester,
            "enrolled_ids": enrolled_ids,
        },
    )


@student_required
def student_drop_course(request, enrollment_id):
    if request.method != "POST":
        return redirect("student_my_courses")

    student = request.user.student
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=student,
        status="ENROLLED"
    )

    semester = enrollment.course_offering.semester
    today = timezone.now().date()

    if not (semester.enrollment_open_date <= today <= semester.enrollment_close_date):
        messages.error(request, "You can no longer drop courses.")
        return redirect("student_my_courses")

    offering = enrollment.course_offering

    enrollment.status = "DROPPED"
    enrollment.save(update_fields=["status"])

    if offering.current_enrollment > 0:
        offering.current_enrollment -= 1
        offering.save(update_fields=["current_enrollment"])

    messages.success(
        request,
        f"{offering.course.course_code} dropped successfully."
    )

    return redirect("student_my_courses")



def get_current_semester():
    today = date.today()
    return Semester.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).first()