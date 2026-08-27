from django.conf import settings
from django.db import models


class Teacher(models.Model):
    """
    Represents a teacher as a school/domain entity.

    A Teacher is always linked to a User account (the system account through
    which the teacher logs in). The User.role must be set to 'teacher'.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_profile',
        help_text='System account for this teacher.',
    )
    employee_number = models.CharField(
        max_length=30,
        unique=True,
        help_text='School-assigned employee/staff number.',
    )
    qualification = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Academic or professional qualification, e.g. "B.Ed Mathematics".',
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['employee_number']

    def __str__(self):
        if self.user:
            full_name = self.user.get_full_name()
            if full_name:
                return f'{full_name} ({self.employee_number})'
        return self.employee_number

    def get_full_name(self):
        if self.user:
            return self.user.get_full_name()
        return self.employee_number


class Subject(models.Model):
    """
    Represents an academic subject taught at the school,
    e.g. Mathematics, English, Biology.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Subject name, e.g. "Mathematics", "English Language".',
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Short subject code, e.g. "MATH", "ENG".',
    )
    description = models.TextField(
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class TeachingAssignment(models.Model):
    """
    Assigns a teacher to teach a specific subject to a specific
    class/stream in an academic year.

    This is the primary record of teaching responsibility.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
    )
    school_class = models.ForeignKey(
        'administration.Class',
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        help_text='The class level this assignment covers.',
    )
    stream = models.ForeignKey(
        'administration.Stream',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teaching_assignments',
        help_text='The specific stream, if the assignment is stream-specific.',
    )
    academic_year = models.ForeignKey(
        'administration.AcademicYear',
        on_delete=models.PROTECT,
        related_name='teaching_assignments',
    )

    class Meta:
        verbose_name = 'Teaching Assignment'
        verbose_name_plural = 'Teaching Assignments'
        ordering = ['academic_year', 'teacher', 'subject']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'subject', 'school_class', 'stream', 'academic_year'],
                name='unique_teaching_assignment',
            ),
        ]

    def __str__(self):
        stream_label = f' {self.stream}' if self.stream else ''
        return (
            f'{self.teacher} — '
            f'{self.subject} — '
            f'{self.school_class}{stream_label} '
            f'({self.academic_year})'
        )


class ClassParentAssignment(models.Model):
    """
    Records a Teacher's Class Parent responsibility for a specific
    Class/Stream in an academic year.

    A Class Parent is a Teacher who has been assigned additional pastoral
    responsibility for a particular class or stream. Class Parent is NOT
    a separate User role — it is a responsibility assigned to a Teacher.

    Only one Teacher may be the active Class Parent for a given
    Class + Stream + AcademicYear combination at any time.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='class_parent_assignments',
        help_text='The teacher assigned Class Parent responsibility.',
    )
    school_class = models.ForeignKey(
        'administration.Class',
        on_delete=models.CASCADE,
        related_name='class_parent_assignments',
        help_text='The class for which this teacher is Class Parent.',
    )
    stream = models.ForeignKey(
        'administration.Stream',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='class_parent_assignments',
        help_text=(
            'The specific stream within the class, if applicable. '
            'Leave blank if the teacher is Class Parent for the whole class.'
        ),
    )
    academic_year = models.ForeignKey(
        'administration.AcademicYear',
        on_delete=models.PROTECT,
        related_name='class_parent_assignments',
        help_text='The academic year for which this assignment is valid.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this Class Parent assignment is currently active.',
    )

    class Meta:
        verbose_name = 'Class Parent Assignment'
        verbose_name_plural = 'Class Parent Assignments'
        ordering = ['academic_year', 'school_class', 'stream']
        constraints = [
            models.UniqueConstraint(
                fields=['school_class', 'stream', 'academic_year'],
                condition=models.Q(is_active=True),
                name='unique_active_class_parent_per_class_stream_year',
            ),
        ]

    def __str__(self):
        stream_label = f' {self.stream}' if self.stream else ''
        return (
            f'{self.teacher} — '
            f'Class Parent: {self.school_class}{stream_label} '
            f'({self.academic_year})'
        )
