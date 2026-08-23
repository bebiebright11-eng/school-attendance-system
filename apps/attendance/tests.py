import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.administration.models import AcademicYear, Class, Term
from apps.attendance.models import AttendanceCorrection, AttendanceRecord, AttendanceSession
from apps.students.models import Student
from apps.teaching.models import Lesson, Subject, Teacher, TeacherAssignment

User = get_user_model()


def make_user(username='teacher1', email='t1@e.com'):
    return User.objects.create_user(username=username, email=email, password='pass', role=User.Role.TEACHER)


def make_student(admission='ADM001'):
    return Student.objects.create(
        admission_number=admission,
        first_name='Alice', last_name='Banda',
        date_of_admission=datetime.date(2026, 1, 10),
    )


def make_lesson():
    year = AcademicYear.objects.create(name='2026', start_date='2026-01-10', end_date='2026-11-20')
    term = Term.objects.create(
        academic_year=year, name='Term 1', term_number=1,
        start_date='2026-01-10', end_date='2026-03-31',
    )
    klass = Class.objects.create(name='Form 1', level=1)
    teacher = Teacher.objects.create(employee_number='T001', first_name='John', last_name='Doe')
    subject = Subject.objects.create(name='Maths', code='MTH')
    assignment = TeacherAssignment.objects.create(
        teacher=teacher, subject=subject, school_class=klass, academic_year=year,
    )
    return Lesson.objects.create(
        assignment=assignment, term=term,
        day_of_week=Lesson.DayOfWeek.MONDAY,
        start_time=datetime.time(8, 0), end_time=datetime.time(9, 0),
    )


class AttendanceSessionTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.lesson = make_lesson()

    def test_create_session(self):
        session = AttendanceSession.objects.create(
            lesson=self.lesson,
            date=datetime.date(2026, 1, 13),
            taken_by=self.user,
        )
        self.assertIn('Maths', str(session))
        self.assertIn('2026-01-13', str(session))

    def test_duplicate_session_same_lesson_and_date_raises(self):
        AttendanceSession.objects.create(
            lesson=self.lesson, date=datetime.date(2026, 1, 13), taken_by=self.user,
        )
        with self.assertRaises(IntegrityError):
            AttendanceSession.objects.create(
                lesson=self.lesson, date=datetime.date(2026, 1, 13), taken_by=self.user,
            )

    def test_same_lesson_different_dates_allowed(self):
        s1 = AttendanceSession.objects.create(
            lesson=self.lesson, date=datetime.date(2026, 1, 13), taken_by=self.user,
        )
        s2 = AttendanceSession.objects.create(
            lesson=self.lesson, date=datetime.date(2026, 1, 20), taken_by=self.user,
        )
        self.assertNotEqual(s1.pk, s2.pk)


class AttendanceRecordTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.lesson = make_lesson()
        self.session = AttendanceSession.objects.create(
            lesson=self.lesson, date=datetime.date(2026, 1, 13), taken_by=self.user,
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
        # Start from ADM100 to avoid colliding with ADM001 created in setUp
        for i, status in enumerate(statuses):
            student = make_student(admission=f'ADM1{i:02}')
            r = AttendanceRecord.objects.create(
                session=self.session, student=student, status=status,
            )
            self.assertEqual(r.status, status)

    def test_duplicate_record_same_session_student_raises(self):
        AttendanceRecord.objects.create(
            session=self.session, student=self.student, status=AttendanceRecord.Status.PRESENT,
        )
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(
                session=self.session, student=self.student, status=AttendanceRecord.Status.ABSENT,
            )

    def test_same_student_different_sessions_allowed(self):
        session2 = AttendanceSession.objects.create(
            lesson=self.lesson, date=datetime.date(2026, 1, 20), taken_by=self.user,
        )
        r1 = AttendanceRecord.objects.create(
            session=self.session, student=self.student, status=AttendanceRecord.Status.PRESENT,
        )
        r2 = AttendanceRecord.objects.create(
            session=session2, student=self.student, status=AttendanceRecord.Status.ABSENT,
        )
        self.assertNotEqual(r1.pk, r2.pk)

    def test_records_reverse_on_session(self):
        AttendanceRecord.objects.create(
            session=self.session, student=self.student, status=AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(self.session.records.count(), 1)

    def test_records_reverse_on_student(self):
        AttendanceRecord.objects.create(
            session=self.session, student=self.student, status=AttendanceRecord.Status.LATE,
        )
        self.assertEqual(self.student.attendance_records.count(), 1)


class AttendanceCorrectionTest(TestCase):

    def setUp(self):
        self.user = make_user()
        admin_user = User.objects.create_user(username='admin1', email='a1@e.com', password='pass', role=User.Role.ADMINISTRATOR)
        self.admin_user = admin_user
        self.lesson = make_lesson()
        self.session = AttendanceSession.objects.create(
            lesson=self.lesson, date=datetime.date(2026, 1, 13), taken_by=self.user,
        )
        self.student = make_student()
        self.record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.ABSENT,
        )

    def test_create_correction(self):
        correction = AttendanceCorrection.objects.create(
            record=self.record,
            corrected_by=self.admin_user,
            previous_status=AttendanceRecord.Status.ABSENT,
            new_status=AttendanceRecord.Status.EXCUSED,
            reason='Student provided a medical note.',
        )
        self.assertEqual(correction.previous_status, AttendanceRecord.Status.ABSENT)
        self.assertEqual(correction.new_status, AttendanceRecord.Status.EXCUSED)
        self.assertIn('absent', str(correction))
        self.assertIn('excused', str(correction))

    def test_correction_preserves_original_record(self):
        """Correction must not silently overwrite — the record's original status stays unchanged
        until explicitly updated. The correction is the audit trail."""
        AttendanceCorrection.objects.create(
            record=self.record,
            corrected_by=self.admin_user,
            previous_status=AttendanceRecord.Status.ABSENT,
            new_status=AttendanceRecord.Status.EXCUSED,
            reason='Medical note submitted.',
        )
        # Original record unchanged by simply creating the correction
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, AttendanceRecord.Status.ABSENT)

    def test_multiple_corrections_on_same_record(self):
        """A record may be corrected more than once."""
        AttendanceCorrection.objects.create(
            record=self.record,
            corrected_by=self.admin_user,
            previous_status=AttendanceRecord.Status.ABSENT,
            new_status=AttendanceRecord.Status.EXCUSED,
            reason='First correction.',
        )
        AttendanceCorrection.objects.create(
            record=self.record,
            corrected_by=self.admin_user,
            previous_status=AttendanceRecord.Status.EXCUSED,
            new_status=AttendanceRecord.Status.PRESENT,
            reason='Second correction.',
        )
        self.assertEqual(self.record.corrections.count(), 2)

    def test_reason_blank_fails_validation(self):
        """blank=False is enforced at the Django form/model validation level via full_clean()."""
        from django.core.exceptions import ValidationError
        correction = AttendanceCorrection(
            record=self.record,
            corrected_by=self.admin_user,
            previous_status=AttendanceRecord.Status.ABSENT,
            new_status=AttendanceRecord.Status.EXCUSED,
            reason='',
        )
        with self.assertRaises(ValidationError):
            correction.full_clean()
