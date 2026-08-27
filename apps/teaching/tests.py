import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Stream
from apps.teaching.models import ClassParentAssignment, Subject, Teacher, TeachingAssignment

User = get_user_model()


def make_year():
    return AcademicYear.objects.create(
        name='2026', start_date='2026-01-10', end_date='2026-11-20',
    )


def make_class(name='Form 1', level=1):
    return Class.objects.create(name=name, level=level)


def make_teacher(emp='T001'):
    return Teacher.objects.create(employee_number=emp)


def make_subject(name='Mathematics', code='MATH'):
    return Subject.objects.create(name=name, code=code)


class TeacherModelTest(TestCase):

    def test_create_teacher(self):
        t = make_teacher()
        self.assertIn('T001', str(t))

    def test_employee_number_unique(self):
        make_teacher()
        with self.assertRaises(IntegrityError):
            make_teacher()

    def test_user_link_optional(self):
        t = make_teacher()
        self.assertIsNone(t.user)

    def test_teacher_linked_to_user(self):
        user = User.objects.create_user(
            username='jmwangi', email='j@e.com', password='pass',
            role=User.Role.TEACHER, first_name='John', last_name='Mwangi',
        )
        t = make_teacher()
        t.user = user
        t.save()
        self.assertEqual(t.user, user)
        self.assertEqual(user.teacher_profile, t)

    def test_teacher_has_no_department_field(self):
        """Department removed — teacher must not have a department FK."""
        t = make_teacher()
        self.assertFalse(hasattr(t, 'department'))

    def test_teacher_has_no_first_name_field(self):
        """first_name moved to User in approved spec."""
        t = make_teacher()
        self.assertFalse(hasattr(t, 'first_name'))

    def test_teacher_has_no_last_name_field(self):
        """last_name moved to User in approved spec."""
        t = make_teacher()
        self.assertFalse(hasattr(t, 'last_name'))

    def test_get_full_name_via_user(self):
        user = User.objects.create_user(
            username='ann', email='ann@e.com', password='pass',
            first_name='Ann', last_name='Smith',
        )
        t = make_teacher(emp='T002')
        t.user = user
        t.save()
        self.assertEqual(t.get_full_name(), 'Ann Smith')

    def test_get_full_name_without_user_returns_employee_number(self):
        t = make_teacher()
        self.assertEqual(t.get_full_name(), 'T001')

    def test_qualification_field_exists(self):
        t = Teacher.objects.create(employee_number='T003', qualification='B.Ed Mathematics')
        self.assertEqual(t.qualification, 'B.Ed Mathematics')

    def test_qualification_optional(self):
        t = make_teacher()
        self.assertEqual(t.qualification, '')


class SubjectModelTest(TestCase):

    def test_create_subject(self):
        s = make_subject()
        self.assertIn('Mathematics', str(s))
        self.assertIn('MATH', str(s))

    def test_name_unique(self):
        make_subject()
        with self.assertRaises(IntegrityError):
            make_subject()

    def test_code_unique(self):
        make_subject()
        with self.assertRaises(IntegrityError):
            Subject.objects.create(name='Maths Advanced', code='MATH')

    def test_subject_has_no_department_field(self):
        """Department removed — subject must not have a department FK."""
        s = make_subject()
        self.assertFalse(hasattr(s, 'department'))

    def test_subject_has_no_is_active_field(self):
        """is_active not in approved Subject spec."""
        s = make_subject()
        self.assertFalse(hasattr(s, 'is_active'))


class TeachingAssignmentTest(TestCase):

    def setUp(self):
        self.year = make_year()
        self.teacher = make_teacher()
        self.subject = make_subject()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')

    def _assign(self, stream=None):
        return TeachingAssignment.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            school_class=self.klass,
            stream=stream,
            academic_year=self.year,
        )

    def test_create_assignment(self):
        a = self._assign(stream=self.stream)
        self.assertIn('T001', str(a))
        self.assertIn('Mathematics', str(a))
        self.assertIn('Form 1', str(a))

    def test_assignment_without_stream(self):
        a = self._assign()
        self.assertIsNone(a.stream)

    def test_duplicate_assignment_raises(self):
        self._assign(stream=self.stream)
        with self.assertRaises(IntegrityError):
            self._assign(stream=self.stream)

    def test_different_year_allows_same_assignment(self):
        year2 = AcademicYear.objects.create(
            name='2025', start_date='2025-01-01', end_date='2025-12-31',
        )
        a1 = self._assign(stream=self.stream)
        a2 = TeachingAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            school_class=self.klass, stream=self.stream, academic_year=year2,
        )
        self.assertNotEqual(a1.pk, a2.pk)

    def test_teaching_assignments_reverse_relation(self):
        self._assign()
        self.assertEqual(self.teacher.teaching_assignments.count(), 1)

    def test_teaching_assignment_has_no_is_active_field(self):
        """is_active not in approved TeachingAssignment spec."""
        a = self._assign()
        self.assertFalse(hasattr(a, 'is_active'))


class ClassParentAssignmentTest(TestCase):
    """
    Tests for ClassParentAssignment.

    Key rules verified:
    - A Class Parent is always a Teacher.
    - Only one active Class Parent per Class/Stream/Year.
    - Class Parent is NOT a User role.
    """

    def setUp(self):
        self.year = make_year()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')
        self.teacher = make_teacher()

    def _assign_class_parent(self, teacher=None, stream=None, year=None):
        return ClassParentAssignment.objects.create(
            teacher=teacher or self.teacher,
            school_class=self.klass,
            stream=stream,
            academic_year=year or self.year,
        )

    def test_create_class_parent_assignment(self):
        cp = self._assign_class_parent(stream=self.stream)
        self.assertIn('T001', str(cp))
        self.assertIn('Form 1', str(cp))
        self.assertIn('East', str(cp))
        self.assertTrue(cp.is_active)

    def test_class_parent_without_stream(self):
        cp = self._assign_class_parent()
        self.assertIsNone(cp.stream)

    def test_class_parent_is_still_a_teacher(self):
        cp = self._assign_class_parent(stream=self.stream)
        self.assertIsInstance(cp.teacher, Teacher)
        self.assertEqual(cp.teacher.employee_number, 'T001')

    def test_class_parent_teacher_can_also_have_teaching_assignments(self):
        subject = make_subject()
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher,
            subject=subject,
            school_class=self.klass,
            academic_year=self.year,
        )
        cp = self._assign_class_parent(stream=self.stream)
        self.assertEqual(cp.teacher, ta.teacher)
        self.assertEqual(self.teacher.teaching_assignments.count(), 1)
        self.assertEqual(self.teacher.class_parent_assignments.count(), 1)

    def test_only_one_active_class_parent_per_class_stream_year(self):
        teacher2 = make_teacher(emp='T002')
        self._assign_class_parent(stream=self.stream)
        with self.assertRaises(IntegrityError):
            ClassParentAssignment.objects.create(
                teacher=teacher2,
                school_class=self.klass,
                stream=self.stream,
                academic_year=self.year,
                is_active=True,
            )

    def test_inactive_assignment_does_not_block_new_active_one(self):
        teacher2 = make_teacher(emp='T002')
        old_cp = self._assign_class_parent(stream=self.stream)
        old_cp.is_active = False
        old_cp.save()
        new_cp = ClassParentAssignment.objects.create(
            teacher=teacher2,
            school_class=self.klass,
            stream=self.stream,
            academic_year=self.year,
            is_active=True,
        )
        self.assertTrue(new_cp.is_active)

    def test_same_teacher_can_be_class_parent_in_different_years(self):
        year2 = AcademicYear.objects.create(
            name='2025', start_date='2025-01-01', end_date='2025-12-31',
        )
        cp1 = self._assign_class_parent(stream=self.stream, year=self.year)
        cp2 = self._assign_class_parent(stream=self.stream, year=year2)
        self.assertNotEqual(cp1.pk, cp2.pk)

    def test_same_teacher_can_be_class_parent_in_different_classes(self):
        klass2 = Class.objects.create(name='Form 2', level=2)
        cp1 = self._assign_class_parent(stream=self.stream)
        cp2 = ClassParentAssignment.objects.create(
            teacher=self.teacher,
            school_class=klass2,
            stream=None,
            academic_year=self.year,
        )
        self.assertNotEqual(cp1.pk, cp2.pk)

    def test_class_parent_is_not_a_user_role(self):
        role_values = [r.value for r in User.Role]
        self.assertNotIn('class_parent', role_values)
        self.assertNotIn('parent', role_values)

    def test_reverse_relation_on_teacher(self):
        self._assign_class_parent(stream=self.stream)
        self.assertEqual(self.teacher.class_parent_assignments.count(), 1)

    def test_reverse_relation_on_class(self):
        self._assign_class_parent(stream=self.stream)
        self.assertEqual(self.klass.class_parent_assignments.count(), 1)

    def test_class_parent_assignment_has_no_notes_field(self):
        """notes field not in approved ClassParentAssignment spec."""
        cp = self._assign_class_parent(stream=self.stream)
        self.assertFalse(hasattr(cp, 'notes'))
