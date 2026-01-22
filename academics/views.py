from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from academics.models import Department, DegreeProgram, Course, Semester

@login_required(login_url='login')
def department_list(request):
    departments = Department.objects.all().order_by('name')
    return render(request, 'academics/department_list.html', {
        'departments': departments
    })

@login_required(login_url='login')
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

@login_required(login_url='login')
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    dept.delete()
    messages.success(request, "Department deleted")
    return redirect('department_list')

@login_required(login_url='login')
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

@login_required(login_url='login')
def degree_program_list(request):
    programs = DegreeProgram.objects.select_related("department").all()
    return render(
        request,
        "academics/degree_program_list.html",
        {"programs": programs},
    )

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
def degree_program_delete(request, pk):
    program = get_object_or_404(DegreeProgram, pk=pk)
    program.delete()
    messages.success(request, "Degree program deleted successfully")
    return redirect("degree_program_list")

@login_required(login_url='login')
def course_list(request):
    courses = Course.objects.select_related("department").order_by("-created_at")

    return render(request, "academics/course_list.html", {
        "courses": courses
    })

@login_required(login_url='login')
def course_add(request):
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        Course.objects.create(
            department_id=request.POST.get("department"),
            course_name=request.POST.get("course_name"),
            course_code=request.POST.get("course_code"),
            credit_points=request.POST.get("credit_points"),
            max_capacity=request.POST.get("max_capacity"),
            is_active=request.POST.get("is_active") == "1",
        )
        messages.success(request, "Course added successfully")
        return redirect("course_list")

    return render(request, "academics/course_form.html", {
        "departments": departments
    })

@login_required(login_url='login')
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        course.department_id = request.POST.get("department")
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
        "departments": departments
    })

@login_required(login_url='login')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.delete()
    messages.success(request, "Course deleted successfully")
    return redirect("course_list")

@login_required(login_url='login')  
def semester_list(request):
    semesters = Semester.objects.all().order_by("-created_at")
    return render(request, "academics/semester_list.html", {
        "semesters": semesters
    })

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
def semester_delete(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    semester.delete()
    messages.success(request, "Semester deleted successfully")
    return redirect("semester_list")