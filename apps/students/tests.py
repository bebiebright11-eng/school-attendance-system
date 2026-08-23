import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Stream, Term
from apps.students.models import Enrollment, Guardian, Student, StudentGuardian

User = get_user_model()


def make_student(admission='ADM001', first='Alice', last='Banda', status=Student.Status.ACTIVE):
    return Student.objects.create(
        admission_number=admission,
        first_name=first,
        last_name=last,
        date_of_admission=datetime.date(2026, 1, 10),
        status=status,
    )


def make_guardian(first='Grace', last='Banda', phone='0712345678'):
    return Guardian.objects.create(first_name=first, last_name=last, phone_number=phone)


def make_year():
    return AcademicYear.objects.create(
        name='2026', start_date='2026-01-10', end_date='2026-11-20',
    )


def make_term(year):
    return Term.objects.create(
        academic_year=year, name='Term 1', term_number=1,
        start_date='2026-01-10', end_date='2026-03-31',
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
            date_of_admission=datetime.date(2026, 1, 10),
        )
        self.assertEqual(s.status, Student.Status.ACTIVE)

    def test_student_user_link_is_optional(self):
        s = make_student()
        self.assertIsNone(s.user)

    def test_student_can_be_linked_to_user(self):
        user = User.objects.create_user(username='alice', email='alice@e.com', password='pass')
        s = make_student()
        s.user = user
        s.save()
        self.assertEqual(s.user, user)
        self.assertEqual(user.student_profile, s)

    def test_get_full_name(self):
        s = make_student()
        self.assertEqual(s.get_full_name(), 'Alice Banda')


class GuardianModelTest(TestCase):

    def test_create_guardian(self):
        g = make_guardian()
        self.assertEqual(str(g), 'Grace Banda')

    def test_guardian_user_link_is_optional(self):
        g = make_guardian()
        self.assertIsNone(g.user)

    def test_guardian_can_be_linked_to_user(self):
        user = User.objects.create_user(username='grace', email='grace@e.com', password='pass')
        g = make_guardian()
        g.user = user
        g.save()
        self.assertEqual(g.user, user)


class StudentGuardianTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.guardian = make_guardian()

    def test_create_student_guardian_relationship(self):
        sg = StudentGuardian.objects.create(
            student=self.student,
            guardian=self.guardian,
            relationship='Mother',
            is_primary=True,
        )
        self.assertEqual(sg.student, self.student)
        self.assertEqual(sg.guardian, self.guardian)
        self.assertTrue(sg.is_primary)
        self.assertIn('Grace Banda', str(sg))
        self.assertIn('Alice Banda', str(sg))

    def test_duplicate_student_guardian_raises(self):
        StudentGuardian.objects.create(student=self.student, guardian=self.guardian)
        with self.assertRaises(IntegrityError):
            StudentGuardian.objects.create(student=self.student, guardian=self.guardian)

    def test_one_guardian_multiple_students(self):
        s2 = make_student(admission='ADM002', first='Bob', last='Moyo')
        sg1 = StudentGuardian.objects.create(student=self.student, guardian=self.guardian)
        sg2 = StudentGuardian.objects.create(student=s2, guardian=self.guardian)
        self.assertEqual(self.guardian.student_guardians.count(), 2)
        self.assertNotEqual(sg1.pk, sg2.pk)

    def test_one_student_multiple_guardians(self):
        g2 = make_guardian(first='Peter', last='Banda', phone='0799')
        StudentGuardian.objects.create(student=self.student, guardian=self.guardian)
        StudentGuardian.objects.create(student=self.student, guardian=g2)
        self.assertEqual(self.student.student_guardians.count(), 2)

    def test_many_to_many_via_student_guardians(self):
        StudentGuardian.objects.create(student=self.student, guardian=self.guardian)
        self.assertIn(self.guardian, self.student.guardians.all())
        self.assertIn(self.student, self.guardian.students.all())


class EnrollmentTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.year = make_year()
        self.term = make_term(self.year)
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')

    def _enroll(self, term=None, stream=None):
        return Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            term=term,
            school_class=self.klass,
            stream=stream,
            date_enrolled=datetime.date(2026, 1, 10),
        )

    def test_create_enrollment(self):
        e = self._enroll(term=self.term, stream=self.stream)
        self.assertIn('Alice Banda', str(e))
        self.assertIn('Form 1', str(e))
        self.assertTrue(e.is_active)

    def test_enrollment_term_optional(self):
        e = self._enroll()
        self.assertIsNone(e.term)

    def test_enrollment_stream_optional(self):
        e = self._enroll(term=self.term)
        self.assertIsNone(e.stream)

    def test_duplicate_enrollment_raises(self):
        self._enroll(term=self.term, stream=self.stream)
        with self.assertRaises(IntegrityError):
            self._enroll(term=self.term, stream=self.stream)

    def test_same_student_different_term_allowed(self):
        term2 = Term.objects.create(
            academic_year=self.year, name='Term 2', term_number=2,
            start_date='2026-04-01', end_date='2026-06-30',
        )
        e1 = self._enroll(term=self.term, stream=self.stream)
        e2 = Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            term=term2,
            school_class=self.klass,
            stream=self.stream,
            date_enrolled=datetime.date(2026, 4, 1),
        )
        self.assertNotEqual(e1.pk, e2.pk)
