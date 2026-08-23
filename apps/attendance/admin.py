from django.contrib import admin

from .models import AttendanceCorrection, AttendanceRecord, AttendanceSession


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ('student', 'status', 'remarks')
    raw_id_fields = ('student',)


class AttendanceCorrectionInline(admin.TabularInline):
    model = AttendanceCorrection
    extra = 0
    fields = ('corrected_by', 'previous_status', 'new_status', 'reason', 'corrected_at')
    readonly_fields = ('corrected_at',)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'date', 'taken_by', 'taken_at')
    list_filter = ('date', 'lesson__assignment__academic_year')
    search_fields = ('lesson__assignment__subject__name', 'taken_by__username')
    readonly_fields = ('taken_at',)
    inlines = [AttendanceRecordInline]
    raw_id_fields = ('taken_by',)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'recorded_at')
    list_filter = ('status', 'session__date')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    readonly_fields = ('recorded_at',)
    inlines = [AttendanceCorrectionInline]
    raw_id_fields = ('student', 'session')


@admin.register(AttendanceCorrection)
class AttendanceCorrectionAdmin(admin.ModelAdmin):
    list_display = ('record', 'previous_status', 'new_status', 'corrected_by', 'corrected_at')
    list_filter = ('previous_status', 'new_status')
    search_fields = ('corrected_by__username', 'record__student__last_name')
    readonly_fields = ('corrected_at',)
    raw_id_fields = ('record', 'corrected_by')
