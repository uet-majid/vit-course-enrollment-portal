from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Not logged in
            if not request.user.is_authenticated:
                return redirect("login")

            # Logged in but role not allowed
            if request.user.role not in allowed_roles:
                messages.error(request, "You are not authorized to access this page.")
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def guest_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def super_admin_required(view_func):
    return role_required(["SUPER_ADMIN"])(view_func)


def department_admin_required(view_func):
    return role_required(["DEPARTMENT_ADMIN"])(view_func)


def admin_required(view_func):
    return role_required(["SUPER_ADMIN", "DEPARTMENT_ADMIN"])(view_func)


def student_required(view_func):
    return role_required(["STUDENT"])(view_func)

