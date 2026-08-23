from django.conf import settings
from django.db import models


class Teacher(models.Model):
    """
    Represents a teacher as a school/domain entity.

    A Teacher may be linked to a User account, but the two are
    kept separate: not every teacher necessarily has a system account,
    and a User account is not automatically a teacher.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_profile',
        help_text='System account for this teacher, if one exists.',
    )
    employee_number = models.CharField(
        max_length=30,
        unique=True,
        help_text='School-assigned employee/staff number.',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
    )
    email = models.EmailField(
        blank=True,
        default='',
        help_text='Work email address.',
    )
    department = models.ForeignKey(
        'administration.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers',
        help_text='Department this teacher belongs to.',
    )
    date_joined = models.DateField(
        null=True,
        blank=True,
        help_text='Date the teacher joined the school.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this teacher is currently active at the school.',
    )

    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.employee_number})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class Subject(models.Model):
    """
    Represents an academic subject taught at the school,
    e.g. Mathematics, English, Biology.

    Subjects belong to a Department.
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
    department = models.ForeignKey(
        'administration.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects',
        help_text='Department responsible for this subject.',
    )
    description = models.TextField(
        blank=True,
        default='',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this subject is currently offered.',
    )

    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class TeacherAssignment(models.Model):
    """
    Assigns a teacher to teach a specific subject to a specific
    class/stream in an academic year.

    This is the primary record of teaching responsibility.
    A teacher may have multiple assignments across different subjects,
    classes, or streams.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    school_class = models.ForeignKey(
        'administration.Class',
        on_delete=models.CASCADE,
        related_name='teacher_assignments',
        help_text='The class level this assignment covers.',
    )
    stream = models.ForeignKey(
        'administration.Stream',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teacher_assignments',
        help_text='The specific stream, if the assignment is stream-specific.',
    )
    academic_year = models.ForeignKey(
        'administration.AcademicYear',
        on_delete=models.PROTECT,
        related_name='teacher_assignments',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this assignment is currently in effect.',
    )

    class Meta:
        verbose_name = 'Teacher Assignment'
        verbose_name_plural = 'Teacher Assignments'
        ordering = ['academic_year', 'teacher', 'subject']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'subject', 'school_class', 'stream', 'academic_year'],
                name='unique_teacher_assignment',
            ),
        ]

    def __str__(self):
        stream_label = f' {self.stream}' if self.stream else ''
        return (
            f'{self.teacher.get_full_name()} — '
            f'{self.subject} — '
            f'{self.school_class}{stream_label} '
            f'({self.academic_year})'
        )


class Lesson(models.Model):
    """
    Represents a scheduled teaching session.

    A Lesson is tied to a TeacherAssignment (which already encodes the
    teacher, subject, class, and year) and scheduled in a Classroom on
    a specific day/time.

    Lesson is the context in which attendance sessions are created.
    """

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, 'Monday'
        TUESDAY = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY = 4, 'Thursday'
        FRIDAY = 5, 'Friday'
        SATURDAY = 6, 'Saturday'
        SUNDAY = 7, 'Sunday'

    assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name='lessons',
        help_text='The teacher-subject-class assignment this lesson belongs to.',
    )
    classroom = models.ForeignKey(
        'administration.Classroom',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        help_text='The physical room where this lesson takes place.',
    )
    term = models.ForeignKey(
        'administration.Term',
        on_delete=models.CASCADE,
        related_name='lessons',
        help_text='The term in which this lesson is scheduled.',
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DayOfWeek,
        help_text='Day of the week this lesson occurs.',
    )
    start_time = models.TimeField(
        help_text='Scheduled start time.',
    )
    end_time = models.TimeField(
        help_text='Scheduled end time.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this lesson is currently scheduled.',
    )

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['term', 'day_of_week', 'start_time']

    def __str__(self):
        day_label = self.get_day_of_week_display()
        return (
            f'{self.assignment.subject} — '
            f'{self.assignment.school_class} — '
            f'{day_label} {self.start_time:%H:%M}–{self.end_time:%H:%M}'
        )


class ClassParentAssignment(models.Model):
    """
    Records a Teacher's Class Parent responsibility for a specific
    Class/Stream in an academic year.

    A Class Parent is a Teacher who has been assigned additional pastoral
    responsibility for a particular class or stream. They remain a Teacher
    in every other respect: they can still teach subjects and record
    attendance through the normal TeacherAssignment / Lesson / AttendanceSession
    workflow. This model only captures the additional Class Parent responsibility.

    Uniqueness rule:
        Only one Teacher may be the active Class Parent for a given
        Class + Stream + AcademicYear combination at any time.
        The constraint uses a partial approach: it covers all four fields
        so that a class without a stream (stream=NULL) is also protected.
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
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Optional notes about this assignment.',
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
            f'{self.teacher.get_full_name()} — '
            f'Class Parent: {self.school_class}{stream_label} '
            f'({self.academic_year})'
        )
