from django.contrib.auth.models import AbstractUser
from django.db import models
from academics.models import Department, DegreeProgram

class User(AbstractUser):
    ROLE_CHOICES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('DEPARTMENT_ADMIN', 'Department Admin'),
        ('STUDENT', 'Student'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    image = models.ImageField(upload_to='users/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.role in ['SUPER_ADMIN', 'DEPARTMENT_ADMIN']:
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)


class DepartmentAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.department.name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    degree_program = models.ForeignKey(DegreeProgram, on_delete=models.CASCADE)
    enrollment_year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.student_id