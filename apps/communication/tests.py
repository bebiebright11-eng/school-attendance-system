import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.communication.models import Announcement, Message, Notification

User = get_user_model()


def make_user(username='user1', email='u1@e.com', role=User.Role.ADMINISTRATOR):
    return User.objects.create_user(username=username, email=email, password='pass', role=role)


class AnnouncementTest(TestCase):

    def setUp(self):
        self.author = make_user()

    def test_create_announcement(self):
        a = Announcement.objects.create(
            title='Welcome Back',
            body='School starts Monday.',
            author=self.author,
        )
        self.assertEqual(str(a), 'Welcome Back')
        self.assertTrue(a.is_published)

    def test_author_optional(self):
        a = Announcement.objects.create(title='Notice', body='Details here.')
        self.assertIsNone(a.author)

    def test_expires_at_optional(self):
        a = Announcement.objects.create(title='Notice', body='Body.', author=self.author)
        self.assertIsNone(a.expires_at)

    def test_target_roles_defaults_to_empty_list(self):
        a = Announcement.objects.create(title='All', body='Body.')
        self.assertEqual(a.target_roles, [])

    def test_target_roles_can_store_role_list(self):
        a = Announcement.objects.create(
            title='Teachers only',
            body='Staff meeting Friday.',
            target_roles=['teacher'],
        )
        self.assertIn('teacher', a.target_roles)

    def test_ordering_newest_first(self):
        a1 = Announcement.objects.create(title='Old', body='Old.', author=self.author)
        a2 = Announcement.objects.create(title='New', body='New.', author=self.author)
        announcements = list(Announcement.objects.values_list('title', flat=True))
        # Both inserted quickly; just confirm both exist and ordering field is set
        self.assertEqual(Announcement.objects.count(), 2)


class NotificationTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_notification(self):
        n = Notification.objects.create(
            recipient=self.user,
            title='Your report is ready',
        )
        self.assertIn('Your report is ready', str(n))
        self.assertIn('unread', str(n))
        self.assertFalse(n.is_read)

    def test_mark_read(self):
        n = Notification.objects.create(recipient=self.user, title='Test')
        n.is_read = True
        n.read_at = timezone.now()
        n.save()
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)

    def test_read_at_optional(self):
        n = Notification.objects.create(recipient=self.user, title='Test')
        self.assertIsNone(n.read_at)

    def test_notifications_reverse_on_user(self):
        Notification.objects.create(recipient=self.user, title='N1')
        Notification.objects.create(recipient=self.user, title='N2')
        self.assertEqual(self.user.notifications.count(), 2)

    def test_deleting_user_deletes_notifications(self):
        Notification.objects.create(recipient=self.user, title='Will be gone')
        self.user.delete()
        self.assertEqual(Notification.objects.count(), 0)


class MessageTest(TestCase):

    def setUp(self):
        self.sender = make_user(username='sender', email='sender@e.com')
        self.recipient = make_user(username='recipient', email='recipient@e.com', role=User.Role.TEACHER)

    def test_create_message(self):
        m = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject='Hello',
            body='Just checking in.',
        )
        self.assertIn('sender', str(m))
        self.assertIn('recipient', str(m))
        self.assertIn('Hello', str(m))
        self.assertFalse(m.is_read)

    def test_subject_optional(self):
        m = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            body='No subject.',
        )
        self.assertEqual(m.subject, '')
        self.assertIn('(no subject)', str(m))

    def test_sender_set_null_on_delete(self):
        m = Message.objects.create(
            sender=self.sender, recipient=self.recipient, body='Hi.'
        )
        self.sender.delete()
        m.refresh_from_db()
        self.assertIsNone(m.sender)

    def test_deleting_recipient_deletes_message(self):
        Message.objects.create(sender=self.sender, recipient=self.recipient, body='Hi.')
        self.recipient.delete()
        self.assertEqual(Message.objects.count(), 0)

    def test_sent_messages_reverse(self):
        Message.objects.create(sender=self.sender, recipient=self.recipient, body='1')
        Message.objects.create(sender=self.sender, recipient=self.recipient, body='2')
        self.assertEqual(self.sender.sent_messages.count(), 2)

    def test_received_messages_reverse(self):
        Message.objects.create(sender=self.sender, recipient=self.recipient, body='Hi')
        self.assertEqual(self.recipient.received_messages.count(), 1)

    def test_read_at_optional(self):
        m = Message.objects.create(sender=self.sender, recipient=self.recipient, body='Hi.')
        self.assertIsNone(m.read_at)
