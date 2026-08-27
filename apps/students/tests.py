import datetime

from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Stream
from apps.students.models import Enrollment, Student


def make_student(admission='ADM001', first='Alice', last='Banda', status=Student.Status.ACTIVE):
    return Student.objects.create(
        admission_number=admission,
        first_name=first,
        last_name=last,
        status=status,
    )


def make_year():
    return AcademicYear.objects.create(
        name='2026', start_date='2026-01-10', end_date='2026-11-20',
    )


def make_class():
    return Class.objects.create(name='Form 1', level=1)


class StudentModelTest(TestCase):

    def test_create_student(self):
        s = make_student()
        self.assertEqual(str(s), 'Alice Banda (ADM001)')
        self.assertEqual(s.status, Student.Status.ACTIVE)

    def test_admission_number_unique(self):
        make_student()
        with self.assertRaises(IntegrityError):
            make_student()

    def test_all_status_choices(self):
        statuses = [
            Student.Status.ACTIVE,
            Student.Status.GRADUATED,
            Student.Status.TRANSFERRED,
            Student.Status.SUSPENDED,
            Student.Status.WITHDRAWN,
        ]
        for i, status in enumerate(statuses):
            s = make_student(admission=f'ADM{i:03}', status=status)
            self.assertEqual(s.status, status)

    def test_default_status_is_active(self):
        s = Student.objects.create(
            admission_number='ADM999',
            first_name='Test',
            last_name='Student',
        )
        self.assertEqual(s.status, Student.Status.ACTIVE)

    def test_student_has_no_user_field(self):
        """Students do NOT have system accounts — user field must be absent."""
        s = make_student()
        self.assertFalse(hasattr(s, 'user'))

    def test_student_has_no_guardians_field(self):
        """Guardian entity removed — students have no guardians M2M."""
        s = make_student()
        self.assertFalse(hasattr(s, 'guardians'))

    def test_student_has_no_photo_field(self):
        """Photo field not in approved spec."""
        s = make_student()
        self.assertFalse(hasattr(s, 'photo'))

    def test_student_has_no_date_of_admission_field(self):
        """date_of_admission removed from approved spec."""
        s = make_student()
        self.assertFalse(hasattr(s, 'date_of_admission'))

    def test_get_full_name(self):
        s = make_student()
        self.assertEqual(s.get_full_name(), 'Alice Banda')

    def test_date_of_birth_optional(self):
        s = make_student()
        self.assertIsNone(s.date_of_birth)


class EnrollmentTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.year = make_year()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')

    def _enroll(self, stream=None, status=Enrollment.Status.ACTIVE):
        return Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            school_class=self.klass,
            stream=stream,
            enrollment_date=datetime.date(2026, 1, 10),
            status=status,
        )

    def test_create_enrollment(self):
        e = self._enroll(stream=self.stream)
        self.assertIn('Alice Banda', str(e))
        self.assertIn('Form 1', str(e))
        self.assertEqual(e.status, Enrollment.Status.ACTIVE)

    def test_enrollment_stream_optional(self):
        e = self._enroll()
        self.assertIsNone(e.stream)

    def test_enrollment_has_no_term_field(self):
        """Term removed from Enrollment per approved spec."""
        e = self._enroll(stream=self.stream)
        self.assertFalse(hasattr(e, 'term'))

    def test_enrollment_has_no_notes_field(self):
        """Notes removed from Enrollment per approved spec."""
        e = self._enroll(stream=self.stream)
        self.assertFalse(hasattr(e, 'notes'))

    def test_enrollment_uses_enrollment_date_not_date_enrolled(self):
        """Field renamed from date_enrolled to enrollment_date per approved spec."""
        e = self._enroll(stream=self.stream)
        self.assertEqual(e.enrollment_date, datetime.date(2026, 1, 10))
        self.assertFalse(hasattr(e, 'date_enrolled'))

    def test_enrollment_status_choices(self):
        statuses = [
            Enrollment.Status.ACTIVE,
            Enrollment.Status.COMPLETED,
            Enrollment.Status.WITHDRAWN,
            Enrollment.Status.TRANSFERRED,
        ]
        for i, status in enumerate(statuses):
            student = make_student(admission=f'ADM{100 + i:03}')
            e = Enrollment.objects.create(
                student=student,
                academic_year=self.year,
                school_class=self.klass,
                stream=self.stream,
                enrollment_date=datetime.date(2026, 1, 10),
                status=status,
            )
            self.assertEqual(e.status, status)

    def test_duplicate_enrollment_raises(self):
        self._enroll(stream=self.stream)
        with self.assertRaises(IntegrityError):
            self._enroll(stream=self.stream)

    def test_same_student_different_year_allowed(self):
        year2 = AcademicYear.objects.create(
            name='2025', start_date='2025-01-01', end_date='2025-12-31',
        )
        e1 = self._enroll(stream=self.stream)
        e2 = Enrollment.objects.create(
            student=self.student,
            academic_year=year2,
            school_class=self.klass,
            stream=self.stream,
            enrollment_date=datetime.date(2025, 1, 10),
        )
        self.assertNotEqual(e1.pk, e2.pk)
