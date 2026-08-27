from django.db import models
from django.utils import timezone


class AttendanceSession(models.Model):
    """
    Represents a single attendance-taking event for a class/stream.

    An AttendanceSession carries all the context needed: which class,
    which stream, which teacher, which academic year, and on what date.
    AttendanceRecords belong to an AttendanceSession.
    """

    class SessionType(models.TextChoices):
        MORNING = 'morning', 'Morning'
        AFTERNOON = 'afternoon', 'Afternoon'
        FULL_DAY = 'full_day', 'Full Day'

    school_class = models.ForeignKey(
        'administration.Class',
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        help_text='The class this attendance session is for.',
    )
    stream = models.ForeignKey(
        'administration.Stream',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='attendance_sessions',
        help_text='The stream within the class, if applicable.',
    )
    teacher = models.ForeignKey(
        'teaching.Teacher',
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        help_text='The teacher who conducted this attendance session.',
    )
    academic_year = models.ForeignKey(
        'administration.AcademicYear',
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        help_text='The academic year this session belongs to.',
    )
    date = models.DateField(
        help_text='Calendar date on which this attendance session occurred.',
    )
    session_type = models.CharField(
        max_length=15,
        choices=SessionType,
        default=SessionType.MORNING,
        help_text='Type of attendance session.',
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Timestamp when this session record was created.',
    )

    class Meta:
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        ordering = ['-date', 'school_class', 'stream']
        constraints = [
            models.UniqueConstraint(
                fields=['school_class', 'stream', 'date', 'session_type'],
                name='unique_attendance_session_per_class_stream_date_type',
            ),
        ]

    def __str__(self):
        stream_label = f' {self.stream}' if self.stream else ''
        return f'{self.school_class}{stream_label} — {self.date} ({self.get_session_type_display()})'


class AttendanceRecord(models.Model):
    """
    Records the attendance status of one student for one AttendanceSession.

    A record must exist for every student in the session — absence is a
    recorded fact, not the absence of a record.
    """

    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        EXCUSED = 'excused', 'Excused'

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records',
        help_text='The attendance session this record belongs to.',
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text='The student this record is for.',
    )
    status = models.CharField(
        max_length=10,
        choices=Status,
        help_text='Attendance status for this student in this session.',
    )
    remarks = models.TextField(
        blank=True,
        default='',
        help_text='Optional remarks, e.g. reason for lateness or excuse details.',
    )

    class Meta:
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        ordering = ['session', 'student']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'student'],
                name='unique_attendance_record_per_session_student',
            ),
        ]

    def __str__(self):
        return f'{self.student} — {self.session} — {self.get_status_display()}'
