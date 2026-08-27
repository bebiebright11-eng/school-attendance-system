from django.db import models


class Student(models.Model):
    """
    Represents a learner enrolled in the school.

    Students do NOT have system accounts — Student is a pure domain entity.
    Enrollment history is stored in Enrollment, not here.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        GRADUATED = 'graduated', 'Graduated'
        TRANSFERRED = 'transferred', 'Transferred'
        SUSPENDED = 'suspended', 'Suspended'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    admission_number = models.CharField(
        max_length=30,
        unique=True,
        help_text='School-assigned admission/registration number. Must be unique.',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text='Student date of birth.',
    )
    gender = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text='Gender, e.g. "Male", "Female".',
    )
    status = models.CharField(
        max_length=15,
        choices=Status,
        default=Status.ACTIVE,
        help_text='Current lifecycle status of the student.',
    )

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.admission_number})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class Enrollment(models.Model):
    """
    Records a student's enrollment in a specific class/stream for a given academic year.

    A student may have multiple enrollment records over their school career.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        TRANSFERRED = 'transferred', 'Transferred'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    school_class = models.ForeignKey(
        'administration.Class',
        on_delete=models.PROTECT,
        related_name='enrollments',
        help_text='The class/grade level the student is enrolled in.',
    )
    stream = models.ForeignKey(
        'administration.Stream',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='enrollments',
        help_text='The stream within the class, if applicable.',
    )
    academic_year = models.ForeignKey(
        'administration.AcademicYear',
        on_delete=models.PROTECT,
        related_name='enrollments',
        help_text='The academic year of this enrollment.',
    )
    enrollment_date = models.DateField(
        help_text='Date this enrollment record was created.',
    )
    status = models.CharField(
        max_length=15,
        choices=Status,
        default=Status.ACTIVE,
        help_text='Current status of this enrollment.',
    )

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering = ['-academic_year__start_date', 'student']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year', 'school_class', 'stream'],
                name='unique_enrollment_per_student_year_class_stream',
            ),
        ]

    def __str__(self):
        stream_label = f' {self.stream}' if self.stream else ''
        return f'{self.student} — {self.school_class}{stream_label} ({self.academic_year})'
