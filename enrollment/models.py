from django.db import models
from accounts.models import Student
from academics.models import CourseOffering
from django.db.models import Sum

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('ENROLLED', 'Enrolled'),
        ('DROPPED', 'Dropped'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course_offering')

    @staticmethod
    def get_enrolled_credits(student, semester):
        result = Enrollment.objects.filter(
            student=student,
            course_offering__semester=semester,
            status="ENROLLED",
        ).aggregate(
            total=Sum("course_offering__course__credit_points")
        )
        return result["total"] or 0

    def __str__(self):
        return f"{self.student.student_id} - {self.course_offering}"
