import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Classroom, Department, Stream, Term
from apps.teaching.models import Lesson, Subject, Teacher, TeacherAssignment

User = get_user_model()


def make_year():
    return AcademicYear.objects.create(
        name='2026', start_date='2026-01-10', end_date='2026-11-20',
    )


def make_term(year):
    return Term.objects.create(
        academic_year=year, name='Term 1', term_number=1,
        start_date='2026-01-10', end_date='2026-03-31',
    )


def make_class(name='Form 1', level=1):
    return Class.objects.create(name=name, level=level)


def make_teacher(emp='T001', first='John', last='Mwangi'):
    return Teacher.objects.create(employee_number=emp, first_name=first, last_name=last)


def make_subject(name='Mathematics', code='MATH'):
    return Subject.objects.create(name=name, code=code)


class TeacherModelTest(TestCase):

    def test_create_teacher(self):
        t = make_teacher()
        self.assertIn('John Mwangi', str(t))
        self.assertIn('T001', str(t))
        self.assertTrue(t.is_active)

    def test_employee_number_unique(self):
        make_teacher()
        with self.assertRaises(IntegrityError):
            make_teacher()

    def test_user_link_optional(self):
        t = make_teacher()
        self.assertIsNone(t.user)

    def test_teacher_linked_to_user(self):
        user = User.objects.create_user(username='jmwangi', email='j@e.com', password='pass', role=User.Role.TEACHER)
        t = make_teacher()
        t.user = user
        t.save()
        self.assertEqual(t.user, user)
        self.assertEqual(user.teacher_profile, t)

    def test_department_optional(self):
        t = make_teacher()
        self.assertIsNone(t.department)

    def test_teacher_with_department(self):
        dept = Department.objects.create(name='Sciences')
        t = Teacher.objects.create(employee_number='T003', first_name='Ann', last_name='Otieno', department=dept)
        self.assertEqual(t.department, dept)

    def test_get_full_name(self):
        t = make_teacher()
        self.assertEqual(t.get_full_name(), 'John Mwangi')


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

    def test_department_optional(self):
        s = make_subject()
        self.assertIsNone(s.department)


class TeacherAssignmentTest(TestCase):

    def setUp(self):
        self.year = make_year()
        self.teacher = make_teacher()
        self.subject = make_subject()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')

    def _assign(self, stream=None):
        return TeacherAssignment.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            school_class=self.klass,
            stream=stream,
            academic_year=self.year,
        )

    def test_create_assignment(self):
        a = self._assign(stream=self.stream)
        self.assertIn('John Mwangi', str(a))
        self.assertIn('Mathematics', str(a))
        self.assertIn('Form 1', str(a))

    def test_assignment_without_stream(self):
        a = self._assign()
        self.assertIsNone(a.stream)

    def test_duplicate_assignment_raises(self):
        self._assign(stream=self.stream)
        with self.assertRaises(IntegrityError):
            self._assign(stream=self.stream)

    def test_different_year_allows_duplicate_otherwise(self):
        year2 = AcademicYear.objects.create(
            name='2025', start_date='2025-01-01', end_date='2025-12-31',
        )
        a1 = self._assign(stream=self.stream)
        a2 = TeacherAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            school_class=self.klass, stream=self.stream, academic_year=year2,
        )
        self.assertNotEqual(a1.pk, a2.pk)

    def test_teacher_assignments_reverse_relation(self):
        self._assign()
        self.assertEqual(self.teacher.assignments.count(), 1)


class LessonModelTest(TestCase):

    def setUp(self):
        self.year = make_year()
        self.term = make_term(self.year)
        self.teacher = make_teacher()
        self.subject = make_subject()
        self.klass = make_class()
        self.assignment = TeacherAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            school_class=self.klass, academic_year=self.year,
        )
        self.classroom = Classroom.objects.create(name='Room 1')

    def test_create_lesson(self):
        lesson = Lesson.objects.create(
            assignment=self.assignment,
            classroom=self.classroom,
            term=self.term,
            day_of_week=Lesson.DayOfWeek.MONDAY,
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 0),
        )
        self.assertIn('Mathematics', str(lesson))
        self.assertIn('Monday', str(lesson))
        self.assertIn('08:00', str(lesson))

    def test_classroom_optional(self):
        lesson = Lesson.objects.create(
            assignment=self.assignment,
            term=self.term,
            day_of_week=Lesson.DayOfWeek.TUESDAY,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
        )
        self.assertIsNone(lesson.classroom)

    def test_lesson_reverse_on_assignment(self):
        Lesson.objects.create(
            assignment=self.assignment, term=self.term,
            day_of_week=Lesson.DayOfWeek.WEDNESDAY,
            start_time=datetime.time(9, 0), end_time=datetime.time(10, 0),
        )
        self.assertEqual(self.assignment.lessons.count(), 1)


class ClassParentAssignmentTest(TestCase):
    """
    Tests for ClassParentAssignment.

    Key rules verified:
    - A Class Parent is always a Teacher.
    - The same teacher can still hold TeacherAssignment records (teaches).
    - Only one active Class Parent per Class/Stream/Year.
    - A teacher can be Class Parent for multiple classes/years.
    - Class Parent is NOT a User role.
    """

    def setUp(self):
        self.year = make_year()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')
        self.teacher = make_teacher()

    def _assign_class_parent(self, teacher=None, stream=None, year=None):
        from apps.teaching.models import ClassParentAssignment
        return ClassParentAssignment.objects.create(
            teacher=teacher or self.teacher,
            school_class=self.klass,
            stream=stream,
            academic_year=year or self.year,
        )

    def test_create_class_parent_assignment(self):
        from apps.teaching.models import ClassParentAssignment
        cp = self._assign_class_parent(stream=self.stream)
        self.assertIn('John Mwangi', str(cp))
        self.assertIn('Form 1', str(cp))
        self.assertIn('East', str(cp))
        self.assertTrue(cp.is_active)

    def test_class_parent_without_stream(self):
        """Class Parent can be assigned to a whole class without specifying a stream."""
        cp = self._assign_class_parent()
        self.assertIsNone(cp.stream)
        self.assertIn('John Mwangi', str(cp))

    def test_class_parent_is_still_a_teacher(self):
        """Assigning Class Parent does not remove Teacher status — same Teacher object."""
        cp = self._assign_class_parent(stream=self.stream)
        self.assertIsInstance(cp.teacher, Teacher)
        self.assertEqual(cp.teacher.employee_number, 'T001')

    def test_class_parent_teacher_can_still_have_teaching_assignments(self):
        """A Class Parent teacher can also hold normal TeacherAssignments."""
        subject = make_subject()
        ta = TeacherAssignment.objects.create(
            teacher=self.teacher,
            subject=subject,
            school_class=self.klass,
            academic_year=self.year,
        )
        cp = self._assign_class_parent(stream=self.stream)
        self.assertEqual(cp.teacher, ta.teacher)
        self.assertEqual(self.teacher.assignments.count(), 1)
        self.assertEqual(self.teacher.class_parent_assignments.count(), 1)

    def test_only_one_active_class_parent_per_class_stream_year(self):
        """The unique constraint prevents two active Class Parents for the same slot."""
        from django.db import IntegrityError
        from apps.teaching.models import ClassParentAssignment
        teacher2 = make_teacher(emp='T002', first='Mary', last='Kamau')
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
        """An inactive record does not trigger the unique constraint."""
        from apps.teaching.models import ClassParentAssignment
        teacher2 = make_teacher(emp='T002', first='Mary', last='Kamau')
        old_cp = self._assign_class_parent(stream=self.stream)
        old_cp.is_active = False
        old_cp.save()
        # Should not raise
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
        from apps.teaching.models import ClassParentAssignment
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
        """Class Parent must not appear as a User.Role value."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        role_values = [r.value for r in User.Role]
        self.assertNotIn('class_parent', role_values)
        self.assertNotIn('parent', role_values)

    def test_reverse_relation_on_teacher(self):
        cp = self._assign_class_parent(stream=self.stream)
        self.assertEqual(self.teacher.class_parent_assignments.count(), 1)

    def test_reverse_relation_on_class(self):
        cp = self._assign_class_parent(stream=self.stream)
        self.assertEqual(self.klass.class_parent_assignments.count(), 1)
