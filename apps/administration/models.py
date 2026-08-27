from django.db import models
from django.core.exceptions import ValidationError


class AcademicYear(models.Model):
    """
    Represents a school year, e.g. "2026" or "2025/2026".

    Only one academic year may be active at a time.
    """

    name = models.CharField(
        max_length=20,
        unique=True,
        help_text='Human-readable label, e.g. "2025/2026".',
    )
    start_date = models.DateField(
        help_text='First day of the academic year.',
    )
    end_date = models.DateField(
        help_text='Last day of the academic year.',
    )
    is_current = models.BooleanField(
        default=False,
        help_text='Marks the active academic year. Only one year should be current at a time.',
    )

    class Meta:
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
        ordering = ['-start_date']

    def clean(self):
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')

    def __str__(self):
        return self.name


class Term(models.Model):
    """
    A term is a subdivision of an AcademicYear, e.g. Term 1, Term 2, Term 3.

    Term numbers must be unique within a year.
    """

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='terms',
        help_text='The academic year this term belongs to.',
    )
    name = models.CharField(
        max_length=50,
        help_text='Term label, e.g. "Term 1".',
    )
    term_number = models.PositiveSmallIntegerField(
        help_text='Ordinal position within the academic year (1, 2, 3, …).',
    )
    start_date = models.DateField(
        help_text='First day of the term.',
    )
    end_date = models.DateField(
        help_text='Last day of the term.',
    )

    class Meta:
        verbose_name = 'Term'
        verbose_name_plural = 'Terms'
        ordering = ['academic_year', 'term_number']
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'term_number'],
                name='unique_term_number_per_year',
            ),
        ]

    def clean(self):
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')

    def __str__(self):
        return f'{self.academic_year} — {self.name}'


class Class(models.Model):
    """
    Represents a grade/form level in the school, e.g. Form 1, Form 2.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text='Class/grade label, e.g. "Form 1", "Grade 8".',
    )
    level = models.PositiveSmallIntegerField(
        help_text='Numeric level to support ordering (1 = lowest, higher = more advanced).',
    )
    capacity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Maximum number of students this class can hold. Leave blank if unknown.',
    )

    class Meta:
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['level']

    def __str__(self):
        return self.name


class Stream(models.Model):
    """
    A subdivision within a Class, e.g. Form 1 East, Form 1 West.

    Stream names must be unique within a class.
    """

    school_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='streams',
        help_text='The class level this stream belongs to.',
    )
    name = models.CharField(
        max_length=50,
        help_text='Stream label, e.g. "East", "West", "A", "B".',
    )

    class Meta:
        verbose_name = 'Stream'
        verbose_name_plural = 'Streams'
        ordering = ['school_class', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['school_class', 'name'],
                name='unique_stream_name_per_class',
            ),
        ]

    def __str__(self):
        return f'{self.school_class} {self.name}'
