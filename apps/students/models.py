from django.conf import settings
from django.db import models


class Guardian(models.Model):
    """
    Represents a parent or guardian of one or more students.

    A Guardian may optionally be linked to a User account
    (when the guardian uses the system directly), but this is not required.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guardian_profile',
        help_text='System account for this guardian, if they have one.',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Primary contact phone number.',
    )
    email = models.EmailField(
        blank=True,
        default='',
        help_text='Contact email address.',
    )
    relationship = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='Relationship to the student, e.g. "Father", "Mother", "Uncle".',
    )
    address = models.TextField(
        blank=True,
        default='',
        help_text='Physical or mailing address.',
    )
    is_primary_contact = models.BooleanField(
        default=False,
        help_text='Whether this guardian is the primary contact for all associated students.',
    )

    class Meta:
        verbose_name = 'Guardian'
        verbose_name_plural = 'Guardians'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class Student(models.Model):
    """
    Represents a learner enrolled in the school.

    Student is a domain entity separate from User.
    A Student may optionally have an associated User account
    (e.g. if students use the system), but this is not required.

    Enrollment history is stored in Enrollment, not here.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        # The student is currently enrolled and attending school.

        GRADUATED = 'graduated', 'Graduated'
        # The student has completed the final level and left as a graduate.

        TRANSFERRED = 'transferred', 'Transferred'
        # The student has officially left to continue at another school.

        SUSPENDED = 'suspended', 'Suspended'
        # Temporarily prohibited from attending; enrollment remains active.

        WITHDRAWN = 'withdrawn', 'Withdrawn'
        # Enrollment ended for a reason other than graduation or transfer.

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
        help_text='System account for this student, if one exists.',
    )
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
    date_of_admission = models.DateField(
        help_text='Date the student was first admitted to the school.',
    )
    status = models.CharField(
        max_length=15,
        choices=Status,
        default=Status.ACTIVE,
        help_text='Current lifecycle status of the student.',
    )
    photo = models.ImageField(
        upload_to='students/photos/',
        null=True,
        blank=True,
        help_text='Student passport photo.',
    )
    guardians = models.ManyToManyField(
        Guardian,
        through='StudentGuardian',
        related_name='students',
        blank=True,
    )

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.admission_number})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class StudentGuardian(models.Model):
    """
    Through model for the Student <-> Guardian many-to-many relationship.

    Allows a student to have multiple guardians and a guardian to be
    associated with multiple students. Stores the specific relationship
    type and whether this guardian is the primary contact for this student.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='student_guardians',
    )
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
        related_name='student_guardians',
    )
    relationship = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='Relationship of this guardian to this specific student.',
    )
    is_primary = models.BooleanField(
        default=False,
        help_text='Whether this guardian is the primary contact for this student.',
    )
    can_pickup = models.BooleanField(
        default=True,
        help_text='Whether this guardian is authorised to pick up the student.',
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Any additional notes about this student-guardian relationship.',
    )

    class Meta:
        verbose_name = 'Student Guardian'
        verbose_name_plural = 'Student Guardians'
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'guardian'],
                name='unique_student_guardian',
            ),
        ]

    def __str__(self):
        return f'{self.guardian} → {self.student}'


class Enrollment(models.Model):
    """
    Records a student's enrollment in a specific class/stream
    for a given academic year and term.

    A student may have multiple enrollment records over their school career.
    The unique constraint prevents duplicate enrollments for the same
    student/year/term/class/stream combination.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    academic_year = models.ForeignKey(
        'administration.AcademicYear',
        on_delete=models.PROTECT,
        related_name='enrollments',
        help_text='The academic year of this enrollment.',
    )
    term = models.ForeignKey(
        'administration.Term',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='enrollments',
        help_text='The term of this enrollment. Leave blank if enrollment spans the whole year.',
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
    date_enrolled = models.DateField(
        help_text='Date this enrollment record was created.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this enrollment is currently active.',
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Optional notes about this enrollment.',
    )

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering = ['-academic_year__start_date', 'student']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year', 'term', 'school_class', 'stream'],
                name='unique_enrollment_per_student_year_term_class_stream',
            ),
        ]

    def __str__(self):
        stream_label = f' {self.stream}' if self.stream else ''
        term_label = f', {self.term}' if self.term else ''
        return f'{self.student} — {self.school_class}{stream_label} ({self.academic_year}{term_label})'
