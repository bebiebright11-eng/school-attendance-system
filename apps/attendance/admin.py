from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ('student', 'status', 'remarks')
    raw_id_fields = ('student',)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'stream', 'teacher', 'date', 'session_type', 'created_at')
    list_filter = ('date', 'session_type', 'academic_year', 'school_class')
    search_fields = ('school_class__name', 'teacher__employee_number', 'teacher__user__last_name')
    readonly_fields = ('created_at',)
    inlines = [AttendanceRecordInline]
    raw_id_fields = ('teacher',)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status')
    list_filter = ('status', 'session__date')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    raw_id_fields = ('student', 'session')
