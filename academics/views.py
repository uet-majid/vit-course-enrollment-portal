from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from academics.models import Department, DegreeProgram, Course, Semester, CourseOffering
from accounts.decorators import guest_only, student_required, super_admin_required, department_admin_required, admin_required

@super_admin_required
def department_list(request):
    departments = Department.objects.all().order_by('name')
    return render(request, 'academics/department_list.html', {
        'departments': departments
    })

@super_admin_required
def department_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        is_active = request.POST.get('is_active') == '1'

        Department.objects.create(
            name=name,
            code=code,
            is_active=is_active
        )

        messages.success(request, "Department added successfully")
        return redirect('department_list')

    return render(request, 'academics/department_form.html')

@super_admin_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    dept.delete()
    messages.success(request, "Department deleted")
    return redirect('department_list')

@super_admin_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        dept.name = request.POST.get('name')
        dept.code = request.POST.get('code')
        dept.is_active = request.POST.get('is_active') == '1'
        dept.save()

        messages.success(request, "Department updated successfully")
        return redirect('department_list')

    return render(request, 'academics/department_form.html', {
        'department': dept
    })

@super_admin_required
def degree_program_list(request):
    programs = DegreeProgram.objects.select_related("department").all()
    return render(
        request,
        "academics/degree_program_list.html",
        {"programs": programs},
    )

@super_admin_required
def degree_program_add(request):
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        DegreeProgram.objects.create(
            department_id=request.POST.get("department"),
            name=request.POST.get("name"),
            level=request.POST.get("level"),
            duration_years=request.POST.get("duration_years"),
            is_active=request.POST.get("is_active") == "1",
        )
        messages.success(request, "Degree program added successfully")
        return redirect("degree_program_list")

    return render(
        request,
        "academics/degree_program_form.html",
        {"departments": departments},
    )

@super_admin_required
def degree_program_edit(request, pk):
    program = get_object_or_404(DegreeProgram, pk=pk)
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        program.department_id = request.POST.get("department")
        program.name = request.POST.get("name")
        program.level = request.POST.get("level")
        program.duration_years = request.POST.get("duration_years")
        program.is_active = request.POST.get("is_active") == "1"
        program.save()

        messages.success(request, "Degree program updated successfully")
        return redirect("degree_program_list")

    return render(
        request,
        "academics/degree_program_form.html",
        {
            "program": program,
            "departments": departments,
        },
    )

@super_admin_required
def degree_program_delete(request, pk):
    program = get_object_or_404(DegreeProgram, pk=pk)
    program.delete()
    messages.success(request, "Degree program deleted successfully")
    return redirect("degree_program_list")

@admin_required
def course_list(request):
    user = request.user

    if user.role == "SUPER_ADMIN":
        courses = Course.objects.select_related("department").order_by("-created_at")

    elif user.role == "DEPARTMENT_ADMIN":
        department = user.departmentadmin.department
        courses = Course.objects.select_related("department") \
            .filter(department=department) \
            .order_by("-created_at")

    else:
        messages.error(request, "You are not allowed to access this page.")
        return redirect("dashboard")

    return render(request, "academics/course_list.html", {
        "courses": courses
    })

@admin_required
def course_add(request):
    user = request.user

    if user.role == "SUPER_ADMIN":
        departments = Department.objects.filter(is_active=True)
        fixed_department = None

    elif user.role == "DEPARTMENT_ADMIN":
        departments = None
        fixed_department = user.departmentadmin.department

    else:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if request.method == "POST":
        if user.role == "SUPER_ADMIN":
            department_id = request.POST.get("department")
        else:
            department_id = fixed_department.id  # force department

        Course.objects.create(
            department_id=department_id,
            course_name=request.POST.get("course_name"),
            course_code=request.POST.get("course_code"),
            credit_points=request.POST.get("credit_points"),
            max_capacity=request.POST.get("max_capacity"),
            is_active=request.POST.get("is_active") == "1",
        )

        messages.success(request, "Course added successfully")
        return redirect("course_list")

    return render(request, "academics/course_form.html", {
        "departments": departments,
        "fixed_department": fixed_department,
    })

@admin_required
def course_edit(request, pk):
    user = request.user
    course = get_object_or_404(Course, pk=pk)

    # Access control
    if user.role == "DEPARTMENT_ADMIN":
        if course.department != user.departmentadmin.department:
            messages.error(request, "You are not allowed to edit this course.")
            return redirect("course_list")

    if user.role == "SUPER_ADMIN":
        departments = Department.objects.filter(is_active=True)
        fixed_department = None
    else:
        departments = None
        fixed_department = course.department

    if request.method == "POST":
        if user.role == "SUPER_ADMIN":
            course.department_id = request.POST.get("department")
        # department admin cannot change department

        course.course_name = request.POST.get("course_name")
        course.course_code = request.POST.get("course_code")
        course.credit_points = request.POST.get("credit_points")
        course.max_capacity = request.POST.get("max_capacity")
        course.is_active = request.POST.get("is_active") == "1"
        course.save()

        messages.success(request, "Course updated successfully")
        return redirect("course_list")

    return render(request, "academics/course_form.html", {
        "course": course,
        "departments": departments,
        "fixed_department": fixed_department,
    })

@admin_required
def course_delete(request, pk):
    user = request.user
    course = get_object_or_404(Course, pk=pk)

    if user.role == "DEPARTMENT_ADMIN":
        if course.department != user.departmentadmin.department:
            messages.error(request, "You are not allowed to delete this course.")
            return redirect("course_list")

    course.delete()
    messages.success(request, "Course deleted successfully")
    return redirect("course_list")

@super_admin_required
def semester_list(request):
    semesters = Semester.objects.all().order_by("-created_at")
    return render(request, "academics/semester_list.html", {
        "semesters": semesters
    })

@super_admin_required
def semester_add(request):
    if request.method == "POST":
        Semester.objects.create(
            name=request.POST.get("name"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            enrollment_open_date=request.POST.get("enrollment_open_date"),
            enrollment_close_date=request.POST.get("enrollment_close_date"),
            is_active=request.POST.get("is_active") == "1",
        )
        messages.success(request, "Semester added successfully")
        return redirect("semester_list")

    return render(request, "academics/semester_form.html")

@super_admin_required
def semester_edit(request, pk):
    semester = get_object_or_404(Semester, pk=pk)

    if request.method == "POST":
        semester.name = request.POST.get("name")
        semester.start_date = request.POST.get("start_date")
        semester.end_date = request.POST.get("end_date")
        semester.enrollment_open_date = request.POST.get("enrollment_open_date")
        semester.enrollment_close_date = request.POST.get("enrollment_close_date")
        semester.is_active = request.POST.get("is_active") == "1"
        semester.save()

        messages.success(request, "Semester updated successfully")
        return redirect("semester_list")

    return render(request, "academics/semester_form.html", {
        "semester": semester
    })

@super_admin_required
def semester_delete(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    semester.delete()
    messages.success(request, "Semester deleted successfully")
    return redirect("semester_list")

@admin_required
def course_offering_list(request):
    user = request.user

    offerings = CourseOffering.objects.select_related(
        "course", "semester", "course__department"
    )

    if user.role == "DEPARTMENT_ADMIN":
        offerings = offerings.filter(
            course__department=user.departmentadmin.department
        )

    return render(request, "academics/course_offering_list.html", {
        "offerings": offerings.order_by("-created_at")
    })

@admin_required
def course_offering_add(request):
    user = request.user

    semesters = Semester.objects.filter(is_active=True)

    if user.role == "SUPER_ADMIN":
        courses = Course.objects.filter(is_active=True)
    else:
        courses = Course.objects.filter(
            department=user.departmentadmin.department,
            is_active=True
        )

    if request.method == "POST":
        course_id = request.POST.get("course")
        semester_id = request.POST.get("semester")

        if CourseOffering.objects.filter(
            course_id=course_id,
            semester_id=semester_id
        ).exists():
            messages.error(request, "This course is already offered in this semester.")
            return redirect("course_offering_add")

        CourseOffering.objects.create(
            course_id=course_id,
            semester_id=semester_id,
            is_active=True
        )

        messages.success(request, "Course offering created successfully.")
        return redirect("course_offering_list")

    return render(request, "academics/course_offering_form.html", {
        "courses": courses,
        "semesters": semesters
    })

@admin_required
def course_offering_edit(request, pk):
    user = request.user
    offering = get_object_or_404(CourseOffering, pk=pk)

    # Restrict department admins
    if user.role == "DEPARTMENT_ADMIN" and offering.course.department != user.departmentadmin.department:
        messages.error(request, "You are not allowed to edit this course offering.")
        return redirect("course_offering_list")

    # Fetch courses & semesters
    if user.role == "SUPER_ADMIN":
        courses = Course.objects.filter(is_active=True)
    else:
        # department admin: only his department courses
        courses = Course.objects.filter(department=user.departmentadmin.department, is_active=True)

    semesters = Semester.objects.filter(is_active=True)

    if request.method == "POST":
        course_id = request.POST.get("course")
        semester_id = request.POST.get("semester")
        is_active = request.POST.get("is_active") == "1"

        # Check uniqueness before saving
        if CourseOffering.objects.exclude(pk=offering.pk).filter(course_id=course_id, semester_id=semester_id).exists():
            messages.error(request, "This course is already offered in the selected semester.")
            return redirect("course_offering_edit", pk=offering.pk)

        offering.course_id = course_id
        offering.semester_id = semester_id
        offering.is_active = is_active

        try:
            offering.save()
            messages.success(request, "Course offering updated successfully")
        except IntegrityError:
            messages.error(request, "Failed to update course offering. Duplicate entry exists.")
        return redirect("course_offering_list")

    return render(request, "academics/course_offering_form.html", {
        "offering": offering,
        "courses": courses,
        "semesters": semesters,
    })

@admin_required
def course_offering_delete(request, pk):
    user = request.user
    offering = get_object_or_404(CourseOffering, pk=pk)

    if user.role == "DEPARTMENT_ADMIN":
        if offering.course.department != user.departmentadmin.department:
            messages.error(request, "You are not allowed to delete this offering.")
            return redirect("course_offering_list")

    offering.delete()
    messages.success(request, "Course offering deleted successfully.")
    return redirect("course_offering_list")
