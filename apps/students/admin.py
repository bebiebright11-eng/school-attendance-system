from django.contrib import admin

from .models import Enrollment, Student


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('academic_year', 'school_class', 'stream', 'enrollment_date', 'status')
    readonly_fields = ('enrollment_date',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'last_name', 'first_name', 'gender', 'status')
    list_filter = ('status', 'gender')
    search_fields = ('admission_number', 'first_name', 'last_name')
    ordering = ('last_name', 'first_name')
    readonly_fields = ('admission_number',)
    inlines = [EnrollmentInline]
    fieldsets = (
        ('Identity', {'fields': ('admission_number', 'first_name', 'last_name', 'date_of_birth', 'gender')}),
        ('Status', {'fields': ('status',)}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'stream', 'academic_year', 'enrollment_date', 'status')
    list_filter = ('academic_year', 'school_class', 'status')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    raw_id_fields = ('student',)
