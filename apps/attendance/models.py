from django.conf import settings
from django.db import models
from django.utils import timezone


class AttendanceSession(models.Model):
    """
    Represents a single attendance-taking event.

    An AttendanceSession is linked to a Lesson (which carries all the
    context: teacher, subject, class/stream, term, year). The session
    records exactly when attendance was taken and by whom.

    AttendanceRecords belong to an AttendanceSession.
    """

    lesson = models.ForeignKey(
        'teaching.Lesson',
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        help_text='The scheduled lesson this attendance session corresponds to.',
    )
    date = models.DateField(
        help_text='Calendar date on which this attendance session occurred.',
    )
    taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='attendance_sessions_taken',
        help_text='The user who recorded this attendance session.',
    )
    taken_at = models.DateTimeField(
        default=timezone.now,
        help_text='Timestamp when attendance was first recorded.',
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Optional session-level notes.',
    )

    class Meta:
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        ordering = ['-date', 'lesson']
        constraints = [
            models.UniqueConstraint(
                fields=['lesson', 'date'],
                name='unique_attendance_session_per_lesson_date',
            ),
        ]

    def __str__(self):
        return f'{self.lesson} — {self.date}'


class AttendanceRecord(models.Model):
    """
    Records the attendance status of one student for one AttendanceSession.

    Status choices are explicit and documented. A record must exist for
    every student in the session — absence is a recorded fact, not the
    absence of a record.

    Records should not be silently overwritten; use AttendanceCorrection
    to change a record after the fact.
    """

    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        # Student attended and was on time.

        ABSENT = 'absent', 'Absent'
        # Student did not attend and no excuse was provided.

        LATE = 'late', 'Late'
        # Student attended but arrived after the session started.

        EXCUSED = 'excused', 'Excused'
        # Student was absent but with an accepted excuse.

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
    recorded_at = models.DateTimeField(
        default=timezone.now,
        help_text='Timestamp when this record was first created.',
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


class AttendanceCorrection(models.Model):
    """
    Records an authorised correction to an existing AttendanceRecord.

    Corrections preserve accountability by keeping the original record
    intact and recording who changed what and why.

    The AttendanceRecord's status is updated to the new value; this
    correction entry provides the audit trail.
    """

    record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name='corrections',
        help_text='The attendance record that was corrected.',
    )
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='attendance_corrections',
        help_text='The authorised user who made this correction.',
    )
    previous_status = models.CharField(
        max_length=10,
        choices=AttendanceRecord.Status,
        help_text='The attendance status before the correction.',
    )
    new_status = models.CharField(
        max_length=10,
        choices=AttendanceRecord.Status,
        help_text='The attendance status after the correction.',
    )
    reason = models.TextField(
        help_text='Mandatory reason/justification for this correction.',
    )
    corrected_at = models.DateTimeField(
        default=timezone.now,
        help_text='Timestamp when this correction was made.',
    )

    class Meta:
        verbose_name = 'Attendance Correction'
        verbose_name_plural = 'Attendance Corrections'
        ordering = ['-corrected_at']

    def __str__(self):
        return (
            f'Correction on {self.record} — '
            f'{self.previous_status} → {self.new_status} '
            f'by {self.corrected_by}'
        )
