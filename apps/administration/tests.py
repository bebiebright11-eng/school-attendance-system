import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Classroom, Department, Stream, Term
from apps.teaching.models import Teacher


def make_year(name='2026', start='2026-01-10', end='2026-11-20', is_current=False):
    return AcademicYear.objects.create(
        name=name,
        start_date=start,
        end_date=end,
        is_current=is_current,
    )


def make_class(name='Form 1', level=1):
    return Class.objects.create(name=name, level=level)


class AcademicYearTest(TestCase):

    def test_create_academic_year(self):
        year = make_year(is_current=True)
        self.assertEqual(str(year), '2026')
        self.assertTrue(year.is_current)

    def test_name_must_be_unique(self):
        make_year()
        with self.assertRaises(IntegrityError):
            make_year()

    def test_clean_rejects_end_before_start(self):
        year = AcademicYear(
            name='Bad',
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            year.clean()

    def test_ordering_by_start_date_descending(self):
        make_year('2024', '2024-01-01', '2024-12-31')
        make_year('2025', '2025-01-01', '2025-12-31')
        years = list(AcademicYear.objects.values_list('name', flat=True))
        self.assertEqual(years, ['2025', '2024'])


class TermTest(TestCase):

    def setUp(self):
        self.year = make_year()

    def test_create_term(self):
        term = Term.objects.create(
            academic_year=self.year,
            name='Term 1',
            term_number=1,
            start_date='2026-01-10',
            end_date='2026-03-31',
        )
        self.assertIn('2026', str(term))
        self.assertIn('Term 1', str(term))

    def test_term_number_unique_within_year(self):
        Term.objects.create(
            academic_year=self.year, name='Term 1', term_number=1,
            start_date='2026-01-10', end_date='2026-03-31',
        )
        with self.assertRaises(IntegrityError):
            Term.objects.create(
                academic_year=self.year, name='Term 1 dup', term_number=1,
                start_date='2026-04-01', end_date='2026-06-30',
            )

    def test_same_term_number_allowed_in_different_years(self):
        year2 = make_year('2025', '2025-01-01', '2025-12-31')
        t1 = Term.objects.create(
            academic_year=self.year, name='Term 1', term_number=1,
            start_date='2026-01-10', end_date='2026-03-31',
        )
        t2 = Term.objects.create(
            academic_year=year2, name='Term 1', term_number=1,
            start_date='2025-01-10', end_date='2025-03-31',
        )
        self.assertNotEqual(t1.pk, t2.pk)

    def test_clean_rejects_end_before_start(self):
        term = Term(
            academic_year=self.year, name='Bad', term_number=99,
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            term.clean()


class ClassTest(TestCase):

    def test_create_class(self):
        c = make_class()
        self.assertEqual(str(c), 'Form 1')

    def test_name_unique(self):
        make_class()
        with self.assertRaises(IntegrityError):
            make_class()

    def test_ordering_by_level(self):
        make_class('Form 3', 3)
        make_class('Form 1', 1)
        make_class('Form 2', 2)
        names = list(Class.objects.values_list('name', flat=True))
        self.assertEqual(names, ['Form 1', 'Form 2', 'Form 3'])


class StreamTest(TestCase):

    def setUp(self):
        self.klass = make_class()

    def test_create_stream(self):
        s = Stream.objects.create(school_class=self.klass, name='East')
        self.assertIn('East', str(s))
        self.assertIn('Form 1', str(s))

    def test_stream_name_unique_within_class(self):
        Stream.objects.create(school_class=self.klass, name='East')
        with self.assertRaises(IntegrityError):
            Stream.objects.create(school_class=self.klass, name='East')

    def test_same_stream_name_allowed_in_different_classes(self):
        klass2 = make_class('Form 2', 2)
        s1 = Stream.objects.create(school_class=self.klass, name='East')
        s2 = Stream.objects.create(school_class=klass2, name='East')
        self.assertNotEqual(s1.pk, s2.pk)


class ClassroomTest(TestCase):

    def test_create_classroom(self):
        room = Classroom.objects.create(name='Room 101', capacity=40)
        self.assertEqual(str(room), 'Room 101')

    def test_name_unique(self):
        Classroom.objects.create(name='Lab A')
        with self.assertRaises(IntegrityError):
            Classroom.objects.create(name='Lab A')

    def test_capacity_optional(self):
        room = Classroom.objects.create(name='Hall')
        self.assertIsNone(room.capacity)


class DepartmentTest(TestCase):

    def test_create_department_without_head(self):
        dept = Department.objects.create(name='Mathematics')
        self.assertEqual(str(dept), 'Mathematics')
        self.assertIsNone(dept.head)

    def test_name_unique(self):
        Department.objects.create(name='Sciences')
        with self.assertRaises(IntegrityError):
            Department.objects.create(name='Sciences')

    def test_department_head_is_optional(self):
        teacher = Teacher.objects.create(
            employee_number='T001', first_name='Ann', last_name='Smith',
        )
        dept = Department.objects.create(name='Languages', head=teacher)
        self.assertEqual(dept.head, teacher)

    def test_deleting_head_sets_null(self):
        teacher = Teacher.objects.create(
            employee_number='T002', first_name='Bob', last_name='Jones',
        )
        dept = Department.objects.create(name='History', head=teacher)
        teacher.delete()
        dept.refresh_from_db()
        self.assertIsNone(dept.head)
