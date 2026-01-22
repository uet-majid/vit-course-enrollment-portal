from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from .models import Student, User, DepartmentAdmin
from academics.models import Department, DegreeProgram
import random
from datetime import timedelta
from django.urls import reverse

User = get_user_model()

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(
                Q(username__iexact=identifier) |
                Q(email__iexact=identifier)
            )
        except User.DoesNotExist:
            messages.error(request, "Invalid username/email or password")
            return redirect('login')

        # Check active status
        if not user_obj.is_active:
            messages.error(request, "Account is inactive")
            return redirect('login')

        # Check verification
        if not user_obj.is_verified:
            messages.error(request, "Account not verified")
            return redirect('login')

        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid username/email or password")
            return redirect('login')

        login(request, user)
        return redirect('dashboard')

    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Check old password
        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect")
            return redirect('change_password')

        # Check new passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match")
            return redirect('change_password')

        # Minimum password validation
        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return redirect('change_password')

        # Set new password
        user.set_password(new_password)
        user.save()

        # Keep user logged in after password change
        update_session_auth_hash(request, user)

        messages.success(request, "Password updated successfully")
        return redirect('dashboard')

    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def profile_view(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name").strip()
        user.last_name = request.POST.get("last_name").strip()

        if "image" in request.FILES:
            user.image = request.FILES["image"]

        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "accounts/profile.html")

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def student_list(request):
    students = Student.objects.select_related(
        "user", "department", "degree_program"
    ).order_by("-created_at")
    return render(request, "accounts/student_list.html", {"students": students})

@login_required(login_url='login')
def student_add(request):
    departments = Department.objects.filter(is_active=True)
    programs = DegreeProgram.objects.filter(is_active=True)

    if request.method == "POST":
        try:
            with transaction.atomic():
                first_name = request.POST.get("first_name")
                last_name = request.POST.get("last_name")
                email = request.POST.get("email")
                username = request.POST.get("username")
                department_id = request.POST.get("department")
                program_id = request.POST.get("degree_program")
                enrollment_year = request.POST.get("enrollment_year")
                department = Department.objects.get(id=department_id)
                student_id = generate_student_id(department, enrollment_year)
                otp = generate_otp()

                if User.objects.filter(username=username).exists():
                    messages.error(request, "Username already exists")
                    return redirect("student_add")

                if User.objects.filter(email=email).exists():
                    messages.error(request, "Email already exists")
                    return redirect("student_add")

                password = get_random_string(10)

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role="Student",
                    otp = otp,
                    otp_expiry = timezone.now() + timedelta(minutes=30)
                )

                Student.objects.create(
                    user=user,
                    student_id=student_id,
                    department_id=department_id,
                    degree_program_id=program_id,
                    enrollment_year=enrollment_year,
                )

                verify_link = request.build_absolute_uri(
                    reverse("verify_otp", args=[user.id])
                )

                send_mail(
                    subject="Student Account Credentials and Verification OTP",
                    message=(
                        f"Hello {first_name},\n\n"
                        f"Your student account has been created successfully.\n\n"
                        f"Student ID: {student_id}\n"
                        f"Username: {username}\n"
                        f"Email: {email}\n"
                        f"Temporary Password: {password}\n"
                        f"Your OTP: {otp}\n\n"
                        f"Verify your account using the link below:\n\n"
                        f"{verify_link}\n\n"
                        f"OTP will expire in 30 minutes.\n\nAfter verfication please login and change your password.\n"
                        f"\nRegards,\nVIT - Course Enrollment Portal"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )

                messages.success(request, "Student added and email sent successfully")
                return redirect("student_list")

        except Exception:
            messages.error(request, "Failed to add student")
            return redirect("student_add")

    return render(
        request,
        "accounts/student_form.html",
        {
            "student": None,
            "departments": departments,
            "programs": programs,
        },
    )

@login_required(login_url='login')
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    departments = Department.objects.filter(is_active=True)
    programs = DegreeProgram.objects.filter(is_active=True)

    if request.method == "POST":
        student.user.first_name = request.POST.get("first_name")
        student.user.last_name = request.POST.get("last_name")
        student.user.is_active = request.POST.get("user_is_active") == "1"
        student.user.save()

        # student.student_id = request.POST.get("student_id")
        student.department_id = request.POST.get("department")
        student.degree_program_id = request.POST.get("degree_program")
        student.enrollment_year = request.POST.get("enrollment_year")
        student.is_active = request.POST.get("student_is_active") == "1"
        student.save()

        messages.success(request, "Student updated successfully")
        return redirect("student_list")

    return render(
        request,
        "accounts/student_form.html",
        {
            "student": student,
            "departments": departments,
            "programs": programs,
        },
    )

@login_required(login_url='login')
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.user.delete()
    messages.success(request, "Student deleted successfully")
    return redirect("student_list")

def generate_student_id(department, enrollment_year):
    prefix = f"{enrollment_year}-{department.code}-"

    last_student = (
        Student.objects
        .filter(student_id__startswith=prefix)
        .order_by("-student_id")
        .first()
    )

    if last_student:
        last_number = int(last_student.student_id[-4:])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{prefix}{str(next_number).zfill(4)}"

def get_degree_programs(request):
    department_id = request.GET.get("department_id")
    programs = DegreeProgram.objects.filter(
        department_id=department_id,
        is_active=True
    ).values("id", "name")

    return JsonResponse(list(programs), safe=False)

def generate_otp():
    return str(random.randint(100000, 999999))

def verify_otp(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        verify_link = request.build_absolute_uri(
            reverse("verify_otp", args=[user.id])
        )
        otp_entered = request.POST.get("otp")

        if user.is_verified:
            messages.info(request, "Your account is already verified.")
            return redirect("login")

        if not user.otp or not user.otp_expiry:
            messages.error(request, "OTP not found. Please request a new one.")
            return redirect(verify_link)

        if user.otp_expiry < timezone.now():
            messages.error(request, "OTP has expired.")
            return redirect(verify_link)

        if user.otp != otp_entered:
            messages.error(request, "Invalid OTP.")
            return redirect(verify_link)
        else:
            user.is_active = True
            user.is_verified = True
            user.otp = None
            user.otp_expiry = None
            user.save()

            messages.success(request, "Account verified successfully. You can now login.")
            return redirect("login")

    return render(request, "accounts/verify_otp.html", {"user": user})

def resend_otp(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent resending if already verified
    if user.is_verified:
        messages.info(request, "Your account is already verified.")
        return redirect("login")

    # Generate new OTP
    otp = generate_otp()

    # Update OTP and expiry
    user.otp = otp
    user.otp_expiry = timezone.now() + timedelta(minutes=30)
    user.save()

    # Verification link
    verify_link = request.build_absolute_uri(
        reverse("verify_otp", args=[user.id])
    )

    # Send email
    send_mail(
        subject="New OTP for Account Verification",
        message=(
            f"Hello {user.first_name},\n\n"
            f"You requested a new OTP for account verification.\n\n"
            f"Your new OTP: {otp}\n\n"
            f"Verify your account using the link below:\n"
            f"{verify_link}\n\n"
            f"This OTP will expire in 30 minutes.\n\n"
            f"Regards,\nVIT - Course Enrollment Portal"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify_otp", user_id=user.id)

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("forgot_password")

        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = timezone.now() + timedelta(minutes=30)
        user.save()

        reset_link = request.build_absolute_uri(
            reverse("reset_password", args=[user.id])
        )

        send_mail(
            subject="Password Reset Request",
            message=(
                f"Hello {user.first_name},\n\n"
                f"You requested to reset your password.\n\n"
                f"OTP: {otp}\n\n"
                f"Reset your password using the link below:\n"
                f"{reset_link}\n\n"
                f"OTP will expire in 30 minutes.\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"Regards,\nVIT - Course Enrollment Portal"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP has been sent to your email.")
        return redirect("reset_password", user.id)

    return render(request, "accounts/forgot_password.html")

def reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        otp = request.POST.get("otp")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if user.otp != otp:
            messages.error(request, "Invalid OTP.")
            return redirect("reset_password", user.id)

        if user.otp_expiry < timezone.now():
            messages.error(request, "OTP expired. Please request again.")
            return redirect("forgot_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password", user.id)
        
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return redirect("reset_password", user.id)

        user.set_password(password)
        user.otp = None
        user.otp_expiry = None
        user.save()

        messages.success(request, "Password reset successful. Please login.")
        return redirect("login")

    return render(request, "accounts/reset_password.html", {"user": user})

@login_required(login_url='login')
def department_admin_list(request):
    admins = (
        DepartmentAdmin.objects
        .select_related("user", "department")
        .order_by("-assigned_at")
    )

    return render(
        request,
        "accounts/department_admin_list.html",
        {"admins": admins},
    )

@login_required(login_url='login')
def department_admin_add(request):
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        department_id = request.POST.get("department")
        otp = generate_otp()

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("department_admin_add")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("department_admin_add")

        password = get_random_string(10)

        try:
            department = get_object_or_404(Department, id=department_id)
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role="DEPARTMENT_ADMIN",
                    otp_expiry = timezone.now() + timedelta(minutes=30),
                    otp = otp,
                )

                DepartmentAdmin.objects.create(
                    user=user,
                    department_id=department_id,
                )

                verify_link = request.build_absolute_uri(
                    reverse("verify_otp", args=[user.id])
                )

            send_mail(
                subject="Department Admin Account Credentials and Verification OTP",
                    message=(
                        f"Hello {first_name},\n\n"
                        f"Your department admin account has been created successfully.\n\n"
                        f"Username: {username}\n"
                        f"Email: {email}\n"
                        f"Temporary Password: {password}\n"
                        f"Assigned Department: {department.name}\n"
                        f"Your OTP: {otp}\n\n"
                        f"Verify your account using the link below:\n\n"
                        f"{verify_link}\n\n"
                        f"OTP will expire in 30 minutes.\n\nAfter verfication please login and change your password.\n"
                        f"\nRegards,\nVIT - Course Enrollment Portal"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
            )

            messages.success(request, "Department admin added successfully")
            return redirect("department_admin_list")

        except Exception:
            messages.error(request, "Something went wrong. Please try again.")

    return render(
        request,
        "accounts/department_admin_form.html",
        {"departments": departments},
    )

@login_required(login_url='login')
def department_admin_edit(request, pk):
    admin = get_object_or_404(DepartmentAdmin, pk=pk)
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        admin.user.first_name = request.POST.get("first_name")
        admin.user.last_name = request.POST.get("last_name")
        admin.user.is_active = request.POST.get("is_active") == "1"
        admin.user.save()

        admin.department_id = request.POST.get("department")
        admin.save()

        messages.success(request, "Department admin updated successfully")
        return redirect("department_admin_list")

    return render(
        request,
        "accounts/department_admin_form.html",
        {
            "admin": admin,
            "departments": departments,
        },
    )

@login_required(login_url='login')
def department_admin_delete(request, pk):
    admin = get_object_or_404(DepartmentAdmin, pk=pk)
    admin.user.delete()
    messages.success(request, "Department admin deleted successfully")
    return redirect("department_admin_list")
