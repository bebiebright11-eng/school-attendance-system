from django.conf import settings
from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    """
    An official school announcement visible to one or more roles/groups.

    Announcements are authored by a user and may be targeted to specific
    audiences. They are not the same as direct messages between users.
    """

    title = models.CharField(
        max_length=255,
        help_text='Short heading for the announcement.',
    )
    body = models.TextField(
        help_text='Full announcement text.',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements',
        help_text='The user who created this announcement.',
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this announcement was published.',
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional expiry date/time after which the announcement is no longer active.',
    )
    is_published = models.BooleanField(
        default=True,
        help_text='Whether this announcement is visible to its audience.',
    )
    target_roles = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'List of role strings that should see this announcement, '
            'e.g. ["teacher", "parent"]. Empty list means all roles.'
        ),
    )

    class Meta:
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class Notification(models.Model):
    """
    A notification delivered to a specific user.

    Notifications are system-generated and directed at one user.
    They record whether the user has read them.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='The user this notification is addressed to.',
    )
    title = models.CharField(
        max_length=255,
        help_text='Short heading for the notification.',
    )
    body = models.TextField(
        blank=True,
        default='',
        help_text='Optional longer notification body.',
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the recipient has read this notification.',
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this notification was created.',
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the recipient marked this notification as read.',
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        read_label = 'read' if self.is_read else 'unread'
        return f'[{read_label}] {self.title} → {self.recipient}'


class Message(models.Model):
    """
    A direct message from one system user to another.

    Messages are separate from Notifications (system-generated) and
    Announcements (broadcast). This is a simple one-to-one user message.
    """

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
        help_text='The user who sent this message.',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text='The user this message was sent to.',
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Optional message subject.',
    )
    body = models.TextField(
        help_text='Message body.',
    )
    sent_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this message was sent.',
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the recipient has read this message.',
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the recipient read this message.',
    )

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.sender} → {self.recipient}: {self.subject or "(no subject)"}'
