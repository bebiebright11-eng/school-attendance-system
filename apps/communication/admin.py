from django.contrib import admin

from .models import Announcement, Message, Notification


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_at', 'expires_at', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('title', 'body', 'author__username')
    readonly_fields = ('published_at',)
    raw_id_fields = ('author',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('title', 'recipient__username', 'recipient__email')
    readonly_fields = ('created_at',)
    raw_id_fields = ('recipient',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'sent_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('sender__username', 'recipient__username', 'subject')
    readonly_fields = ('sent_at',)
    raw_id_fields = ('sender', 'recipient')
