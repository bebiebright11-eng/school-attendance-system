import datetime

from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Stream
from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.students.models import Student
from apps.teaching.models import Teacher


def make_year():
    return AcademicYear.objects.create(
        name='2026', start_date='2026-01-10', end_date='2026-11-20',
    )


def make_class(name='Form 1', level=1):
    return Class.objects.create(name=name, level=level)


def make_teacher(emp='T001'):
    return Teacher.objects.create(employee_number=emp)


def make_student(admission='ADM001'):
    return Student.objects.create(
        admission_number=admission,
        first_name='Alice',
        last_name='Banda',
    )


def make_session(klass=None, stream=None, teacher=None, year=None,
                 date=None, session_type=AttendanceSession.SessionType.MORNING):
    return AttendanceSession.objects.create(
        school_class=klass,
        stream=stream,
        teacher=teacher,
        academic_year=year,
        date=date or datetime.date(2026, 1, 13),
        session_type=session_type,
    )


class AttendanceSessionTest(TestCase):

    def setUp(self):
        self.year = make_year()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')
        self.teacher = make_teacher()

    def test_create_session(self):
        session = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.assertIn('Form 1', str(session))
        self.assertIn('East', str(session))
        self.assertIn('2026-01-13', str(session))

    def test_create_session_without_stream(self):
        session = make_session(
            klass=self.klass, stream=None,
            teacher=self.teacher, year=self.year,
        )
        self.assertIsNone(session.stream)
        self.assertIn('Form 1', str(session))

    def test_session_type_choices(self):
        types = [
            AttendanceSession.SessionType.MORNING,
            AttendanceSession.SessionType.AFTERNOON,
            AttendanceSession.SessionType.FULL_DAY,
        ]
        for i, stype in enumerate(types):
            session = make_session(
                klass=self.klass, stream=self.stream,
                teacher=self.teacher, year=self.year,
                date=datetime.date(2026, 1, 13 + i),
                session_type=stype,
            )
            self.assertEqual(session.session_type, stype)

    def test_duplicate_session_same_class_stream_date_type_raises(self):
        make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        with self.assertRaises(IntegrityError):
            make_session(
                klass=self.klass, stream=self.stream,
                teacher=self.teacher, year=self.year,
            )

    def test_same_class_stream_different_dates_allowed(self):
        s1 = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
            date=datetime.date(2026, 1, 13),
        )
        s2 = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
            date=datetime.date(2026, 1, 20),
        )
        self.assertNotEqual(s1.pk, s2.pk)

    def test_session_has_no_lesson_field(self):
        """Lesson entity removed — AttendanceSession must not reference Lesson."""
        session = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.assertFalse(hasattr(session, 'lesson'))

    def test_session_has_no_taken_by_field(self):
        """taken_by (User FK) replaced by teacher FK in approved spec."""
        session = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.assertFalse(hasattr(session, 'taken_by'))

    def test_session_reverse_on_teacher(self):
        make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.assertEqual(self.teacher.attendance_sessions.count(), 1)

    def test_session_reverse_on_class(self):
        make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.assertEqual(self.klass.attendance_sessions.count(), 1)

    def test_session_reverse_on_academic_year(self):
        make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.assertEqual(self.year.attendance_sessions.count(), 1)


class AttendanceRecordTest(TestCase):

    def setUp(self):
        self.year = make_year()
        self.klass = make_class()
        self.stream = Stream.objects.create(school_class=self.klass, name='East')
        self.teacher = make_teacher()
        self.session = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
        )
        self.student = make_student()

    def test_create_record_present(self):
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertIn('Alice Banda', str(record))
        self.assertIn('Present', str(record))

    def test_all_status_choices(self):
        statuses = [
            AttendanceRecord.Status.PRESENT,
            AttendanceRecord.Status.ABSENT,
            AttendanceRecord.Status.LATE,
            AttendanceRecord.Status.EXCUSED,
        ]
        for i, status in enumerate(statuses):
            student = make_student(admission=f'ADM1{i:02}')
            r = AttendanceRecord.objects.create(
                session=self.session, student=student, status=status,
            )
            self.assertEqual(r.status, status)

    def test_duplicate_record_same_session_student_raises(self):
        AttendanceRecord.objects.create(
            session=self.session, student=self.student,
            status=AttendanceRecord.Status.PRESENT,
        )
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(
                session=self.session, student=self.student,
                status=AttendanceRecord.Status.ABSENT,
            )

    def test_same_student_different_sessions_allowed(self):
        session2 = make_session(
            klass=self.klass, stream=self.stream,
            teacher=self.teacher, year=self.year,
            date=datetime.date(2026, 1, 20),
        )
        r1 = AttendanceRecord.objects.create(
            session=self.session, student=self.student,
            status=AttendanceRecord.Status.PRESENT,
        )
        r2 = AttendanceRecord.objects.create(
            session=session2, student=self.student,
            status=AttendanceRecord.Status.ABSENT,
        )
        self.assertNotEqual(r1.pk, r2.pk)

    def test_records_reverse_on_session(self):
        AttendanceRecord.objects.create(
            session=self.session, student=self.student,
            status=AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(self.session.records.count(), 1)

    def test_records_reverse_on_student(self):
        AttendanceRecord.objects.create(
            session=self.session, student=self.student,
            status=AttendanceRecord.Status.LATE,
        )
        self.assertEqual(self.student.attendance_records.count(), 1)

    def test_record_has_no_recorded_at_field(self):
        """recorded_at not in approved AttendanceRecord spec."""
        record = AttendanceRecord.objects.create(
            session=self.session, student=self.student,
            status=AttendanceRecord.Status.PRESENT,
        )
        self.assertFalse(hasattr(record, 'recorded_at'))

    def test_record_has_no_corrections_field(self):
        """AttendanceCorrection removed — no corrections reverse relation."""
        record = AttendanceRecord.objects.create(
            session=self.session, student=self.student,
            status=AttendanceRecord.Status.PRESENT,
        )
        self.assertFalse(hasattr(record, 'corrections'))
